"""
FastAPI application entry point for the ticket router service.
Defines the HTTP endpoints, initialises OTel telemetry, and wires up the metric instruments
that feed the Grafana dashboard panels.
"""

import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
# The metrics module is the OTel API entry point for creating instruments like counters and histograms.
from opentelemetry import metrics
# FastAPIInstrumentor hooks into FastAPI's middleware and automatically creates a parent span
# for every incoming HTTP request, so you don't have to add tracing manually to each endpoint.
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from pydantic import BaseModel

from services.pipeline import process
from services.store import store
from telemetry import setup_telemetry

# Telemetry must be bootstrapped before any tracer or meter is acquired.
# Calling get_meter() before this runs returns a no-op that silently discards all measurements.
setup_telemetry()

log = logging.getLogger(f"app.{__name__}")

# The Meter is the factory for creating metric instruments. All counters and histograms below are scoped to this service and appear under "ticket-router" in Prometheus and Grafana.
meter = metrics.get_meter("ticket-router")

# Counters only ever go up, which makes them perfect for counting discrete events.
# The category and priority labels let Grafana break the throughput chart down by dimension.
tickets_created = meter.create_counter(
    "tickets.created",
    description="Total tickets successfully created",
)

# A separate counter for the error path. Dividing this by the total in Grafana gives you the error rate over any time window.
tickets_errors = meter.create_counter(
    "tickets.errors",
    description="Total ticket processing errors",
)

# A Histogram records individual measurements and buckets them automatically.
# This is what powers the p99 latency panel. Prometheus derives percentiles from the bucket distribution.
processing_duration = meter.create_histogram(
    "tickets.processing_duration",
    unit="ms",
    description="End-to-end ticket processing time",
)


class TicketRequest(BaseModel):
    subject: str
    body: str
    email: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Ticket router starting up")
    yield
    log.info("Ticket router shutting down")


app = FastAPI(title="Ticket Router", version="1.0.0", lifespan=lifespan)
# instrument_app patches FastAPI so that every request automatically gets a root span,
# and the child spans from pipeline.py nest under it to form the waterfall in Tempo.
FastAPIInstrumentor.instrument_app(app)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/tickets", status_code=201)
def create_ticket(req: TicketRequest):
    # FastAPIInstrumentor has already opened a parent span for this HTTP request.
    # Any spans created inside process() automatically become children of it.
    start = time.time()
    try:
        ticket = process(req.subject, req.body, req.email)
        elapsed = (time.time() - start) * 1000
        # Attaching category and priority as labels means Grafana can slice the throughput chart by either dimension without any extra configuration.
        tickets_created.add(1, {"category": ticket.category, "priority": ticket.priority})
        # Recording the elapsed time here is what gives the p99 panel its data points.
        processing_duration.record(elapsed, {"category": ticket.category})
        return ticket.to_dict()
    except ValueError as exc:
        tickets_errors.add(1)
        raise HTTPException(status_code=422, detail=str(exc))


@app.get("/tickets/{ticket_id}")
def get_ticket(ticket_id: str):
    ticket = store.get(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket.to_dict()


@app.get("/tickets")
def list_tickets():
    return [t.to_dict() for t in store.all()]

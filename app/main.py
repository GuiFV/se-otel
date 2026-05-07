"""
FastAPI application entry point for the ticket router service.
Defines the HTTP endpoints, initialises OTel telemetry, and wires up the metric instruments
that feed the Grafana dashboard panels.
"""

import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from opentelemetry import metrics
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from pydantic import BaseModel

from services.pipeline import process
from services.store import store
from telemetry import setup_telemetry

# 'helper' function
setup_telemetry()

log = logging.getLogger(f"app.{__name__}")

meter = metrics.get_meter("ticket-router")

tickets_created = meter.create_counter(
    "tickets.created",
    description="Total tickets successfully created",
)

tickets_errors = meter.create_counter(
    "tickets.errors",
    description="Total ticket processing errors",
)

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
# adds a root span for every request
FastAPIInstrumentor.instrument_app(app)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/tickets", status_code=201)
def create_ticket(req: TicketRequest):

    start = time.time()
    try:
        ticket = process(req.subject, req.body, req.email)
        elapsed = (time.time() - start) * 1000
        tickets_created.add(1, {"category": ticket.category, "priority": ticket.priority})  # extra labels
        processing_duration.record(elapsed, {"category": ticket.category})  # p99 source
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

"""
Orchestrates the full ticket ingestion pipeline (validate, classify, prioritise, route,
and acknowledge), wrapping the whole sequence in a single root OTel span.
"""

import logging

from opentelemetry import trace

from .classifier import classify
from .prioritizer import prioritize
from .router import route
from .store import Ticket, store

log = logging.getLogger(f"app.{__name__}")
tracer = trace.get_tracer(__name__)


def _validate(subject: str, body: str, email: str) -> None:
    with tracer.start_as_current_span("validate") as span:
        errors = []
        if not subject or not subject.strip():
            errors.append("subject is required")
        if not body or not body.strip():
            errors.append("body is required")
        if not email or "@" not in email:
            errors.append("valid email is required")

        if errors:
            msg = "; ".join(errors)
            span.set_status(trace.StatusCode.ERROR, msg)
            raise ValueError(msg)


def _acknowledge(ticket: Ticket) -> None:
    with tracer.start_as_current_span("acknowledge"):
        log.info("Acknowledgement sent for %s", ticket.ticket_id)


def process(subject: str, body: str, email: str) -> Ticket:
    # ticket.ingest is the root span for the entire pipeline. Every sub-step appear nested under this one as a waterfall in Tempo.
    with tracer.start_as_current_span("ticket.ingest") as span:
        _validate(subject, body, email)

        category = classify(subject, body)
        priority = prioritize(subject, body, category)
        team = route(category, priority)

        ticket = store.create(
            subject=subject, body=body, email=email,
            category=category, priority=priority, team=team,
        )

        _acknowledge(ticket)

        span.set_attribute("ticket.id", ticket.ticket_id)
        span.set_attribute("ticket.category", category)
        span.set_attribute("ticket.priority", priority)
        span.set_attribute("ticket.team", team)

        log.info("Ticket %s processed: %s / %s / %s", ticket.ticket_id, category, priority, team)

        return ticket

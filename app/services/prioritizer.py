"""
Assigns a priority level (urgent, high, medium, or low) to a ticket based on
urgency keywords in the text and the category assigned by the classifier.
"""

import logging

from opentelemetry import trace

from .keywords import HIGH_SIGNAL, URGENCY

log = logging.getLogger(f"app.{__name__}")
tracer = trace.get_tracer(__name__)


def prioritize(subject: str, body: str, category: str) -> str:
    with tracer.start_as_current_span("prioritize"):
        text = f"{subject} {body}".lower()

        if any(kw in text for kw in URGENCY):
            priority = "urgent"
        elif category == "technical" and any(kw in text for kw in HIGH_SIGNAL):
            priority = "high"
        elif category in ("billing", "technical"):
            priority = "high"
        elif category == "account":
            priority = "medium"
        else:
            priority = "low"

        log.info("Priority assigned: %s", priority)

        return priority

"""
Classifies a support ticket into one of four categories (billing, technical, account, or general)
by scoring keyword matches against the subject and body text.
"""

import logging

from opentelemetry import trace

from .keywords import ACCOUNT, BILLING, TECHNICAL

log = logging.getLogger(f"app.{__name__}")
tracer = trace.get_tracer(__name__)


def classify(subject: str, body: str) -> str:
    with tracer.start_as_current_span("classify"):
        text = f"{subject} {body}".lower()

        scores = {
            "billing": sum(1 for kw in BILLING if kw in text),
            "technical": sum(1 for kw in TECHNICAL if kw in text),
            "account": sum(1 for kw in ACCOUNT if kw in text),
        }

        top_score = max(scores.values())
        category = max(scores, key=scores.get) if top_score > 0 else "general"

        log.info("Ticket classified as %s", category)

        return category

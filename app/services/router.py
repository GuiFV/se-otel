"""
Routes a ticket to the appropriate support team based on its category and priority using a static lookup table.
Contains a toggle to simulate queue saturation for demos.
"""

import logging
import time

from opentelemetry import trace

log = logging.getLogger(f"app.{__name__}")
tracer = trace.get_tracer(__name__)

# Setting this to True during a demo simulates a congested routing queue.
# Any urgent ticket will be held for 3 seconds, producing a visibly fat route span in Tempo.
SIMULATE_QUEUE_SATURATION = False

_ROUTING_TABLE: dict[tuple[str, str], str] = {
    ("billing", "low"): "billing_team",
    ("billing", "medium"): "billing_team",
    ("billing", "high"): "billing_team",
    ("billing", "urgent"): "billing_team",
    ("technical", "low"): "support_l1",
    ("technical", "medium"): "support_l1",
    ("technical", "high"): "support_l2",
    ("technical", "urgent"): "support_l2",
    ("account", "low"): "account_mgmt",
    ("account", "medium"): "account_mgmt",
    ("account", "high"): "account_mgmt",
    ("account", "urgent"): "account_mgmt",
    ("general", "low"): "support_l1",
    ("general", "medium"): "support_l1",
    ("general", "high"): "support_l1",
    ("general", "urgent"): "support_l2",
}


def route(category: str, priority: str) -> str:
    with tracer.start_as_current_span("route"):
        if SIMULATE_QUEUE_SATURATION and priority == "urgent":
            log.warning("Routing queue saturated. Holding urgent ticket.")
            time.sleep(3)

        team = _ROUTING_TABLE.get((category, priority), "support_l1")

        log.info("Ticket routed to %s", team)

        return team

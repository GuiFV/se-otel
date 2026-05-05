import pytest

from app.services.classifier import classify
from app.services.pipeline import process


def test_classify_maps_keywords_to_category():
    assert classify("Charged twice", "duplicate charge on my invoice") == "billing"
    assert classify("App crash", "500 error, service is down") == "technical"
    assert classify("Cancel plan", "need to cancel my account") == "account"
    assert classify("Hello", "just a question") == "general"


def test_process_happy_path():
    ticket = process(
        subject="App is broken",
        body="Getting a 500 error on login, affecting my whole team",
        email="user@example.com",
    )
    assert ticket.ticket_id.startswith("TKT-")
    assert ticket.category == "technical"
    assert ticket.status == "acknowledged"


def test_process_urgent_routes_to_l2():
    ticket = process(
        subject="URGENT: production down",
        body="Critical outage, all clients affected",
        email="ops@example.com",
    )
    assert ticket.priority == "urgent"
    assert ticket.team == "support_l2"


def test_process_rejects_garbage_input():
    with pytest.raises(ValueError, match="subject is required"):
        process(subject="", body="", email="not-an-email")

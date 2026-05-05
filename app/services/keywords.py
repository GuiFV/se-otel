"""
Keyword lists used by the classifier and prioritiser. Importing this module is the only
way to share these lists across services without duplicating them.
"""

BILLING = [
    "charge", "charged", "invoice", "invoiced", "refund", "payment",
    "bill", "billing", "subscription", "fee", "price", "cost",
    "credit", "debit", "overcharge", "receipt",
]

TECHNICAL = [
    "error", "bug", "crash", "broken", "not working", "issue",
    "problem", "failed", "failure", "500", "exception", "timeout",
    "slow", "down", "outage", "unavailable", "cannot connect",
]

ACCOUNT = [
    "cancel", "cancellation", "upgrade", "downgrade", "plan",
    "account", "login", "password", "access", "permission",
    "profile", "settings", "user", "sign in", "locked out",
]

URGENCY = [
    "urgent", "critical", "asap", "immediately", "emergency",
    "outage", "blocked", "production", "down", "p0", "p1",
]

HIGH_SIGNAL = [
    "important", "serious", "major", "affecting", "multiple",
    "team", "clients", "customers", "everyone",
]

"""
In-memory ticket store. Holds all created tickets in a plain dict for the lifetime
of the container. Data does not survive a restart, which is intentional for this demo.
"""

import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Optional


@dataclass
class Ticket:
    ticket_id: str
    subject: str
    body: str
    email: str
    category: str
    priority: str
    team: str
    status: str
    created_at: str

    def to_dict(self) -> dict:
        return asdict(self)


class TicketStore:
    def __init__(self) -> None:
        self._store: dict[str, Ticket] = {}

    def create(
        self,
        subject: str,
        body: str,
        email: str,
        category: str,
        priority: str,
        team: str,
    ) -> Ticket:
        ticket = Ticket(
            ticket_id=f"TKT-{uuid.uuid4().hex[:8].upper()}",
            subject=subject,
            body=body,
            email=email,
            category=category,
            priority=priority,
            team=team,
            status="acknowledged",
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        self._store[ticket.ticket_id] = ticket
        return ticket

    def get(self, ticket_id: str) -> Optional[Ticket]:
        return self._store.get(ticket_id)

    def all(self) -> list[Ticket]:
        return list(self._store.values())


store = TicketStore()

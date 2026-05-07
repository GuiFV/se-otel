"""
Fires a batch of support tickets at the running app to populate Grafana with data.
Run this after `docker compose up` and open http://localhost:3000 to watch the charts fill in.
"""

import random
import time

import requests

BASE_URL = "http://localhost:8000"

TICKETS = [
    {
        "subject": "Charged twice this month",
        "body": "I can see two identical charges on my credit card statement. Please refund the duplicate payment.",
        "email": "alice@example.com",
    },
    {
        "subject": "App crashes on login",
        "body": "The app throws an exception every time I try to log in. Getting a 500 error. This is affecting my whole team.",
        "email": "bob@example.com",
    },
    {
        "subject": "Need to upgrade my plan",
        "body": "I'd like to move from the basic plan to professional. Can you help with my account settings?",
        "email": "carol@example.com",
    },
    {
        "subject": "URGENT: production system is down",
        "body": "Our production environment is completely down. Critical outage affecting all clients. Need immediate help.",
        "email": "dave@example.com",
    },
    {
        "subject": "Question about features",
        "body": "Hi, I was wondering if you could tell me more about what's included in the subscription.",
        "email": "eve@example.com",
    },
    {
        "subject": "Invoice discrepancy",
        "body": "The invoice I received doesn't match the agreed price. The fee seems higher than expected.",
        "email": "frank@example.com",
    },
    # error payloads
    {"subject": "", "body": "", "email": "not-an-email"},
    {"subject": "", "body": "Missing subject", "email": "nosubject@example.com"},
    {"subject": "Missing email", "body": "No email provided in this request", "email": ""},
    {"subject": "Bad email format", "body": "The email below is not valid", "email": "notanemail"},
]

random.shuffle(TICKETS)

print(f"Sending {len(TICKETS)} tickets to {BASE_URL}\n")

for i, payload in enumerate(TICKETS, start=1):
    time.sleep(random.uniform(3.2, 7.4))
    try:
        resp = requests.post(f"{BASE_URL}/tickets", json=payload, timeout=10)
        if resp.status_code == 201:
            data = resp.json()
            print(f"[{i}] OK    {data['ticket_id']}  category={data['category']}  priority={data['priority']}  team={data['team']}")
        else:
            print(f"[{i}] ERR   {resp.status_code}: {resp.json().get('detail', resp.text)}")
    except Exception as exc:
        print(f"[{i}] FAIL  {exc}")

print("\nDone. Check Grafana at http://localhost:3000")

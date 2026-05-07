# Ticket Router — OTel Demo

FastAPI ticket routing pipeline fully instrumented with OpenTelemetry: traces, metrics, and logs flowing through the LGTM stack (Loki, Grafana, Tempo, Prometheus).

### Characteristics

- FastAPI REST API
- Five-step pipeline: validate, classify, prioritize, route, acknowledge
- Rule-based classification (billing / technical / account / general)
- In-memory ticket store
- OpenTelemetry SDK: traces to Tempo, metrics to Prometheus, logs to Loki
- OTel Collector as the routing layer (vendor-neutral by design)
- Grafana dashboard pre-provisioned with throughput, error rate, p99 duration, and live logs

## Prerequisites

- [Python 3.12+](https://www.python.org/downloads/)
- [Docker](https://docs.docker.com/engine/install/)

## Setup

Install dependencies (for local testing only):

```bash
pip install -r requirements.txt
```

## Run tests

```bash
python -m pytest
```

## Run the stack

```bash
docker compose up --build -d
```

```bash
docker compose down         # stop and remove containers
docker compose down -v      # also wipes all telemetry data
```

## Endpoints

| Service    | URL                       |
|------------|---------------------------|
| API        | http://localhost:8000     |
| Grafana    | http://localhost:3000     |
| Prometheus | http://localhost:9090     |

## API

### GET /health

```bash
curl http://localhost:8000/health
```

### POST /tickets

```bash
curl -X POST http://localhost:8000/tickets \
  -H "Content-Type: application/json" \
  -d '{"subject": "Charged twice", "body": "Two identical charges on my card this month.", "email": "user@example.com"}'
```

Response:

```json
{
  "ticket_id": "TKT-4E02750A",
  "subject": "Charged twice",
  "body": "Two identical charges on my card this month.",
  "email": "user@example.com",
  "category": "billing",
  "priority": "high",
  "team": "billing_team",
  "status": "acknowledged",
  "created_at": "2026-05-04T17:00:00+00:00"
}
```

### GET /tickets/{ticket_id}

```bash
curl http://localhost:8000/tickets/TKT-4E02750A
```

### GET /tickets

```bash
curl http://localhost:8000/tickets
```

## Observability

### Populate traces, metrics, and logs

Fires 10 tickets (6 valid across all categories, 4 invalid to drive the error rate) with random delays so the Grafana charts show a real distribution:

```bash
python simulate.py
```

Open `http://localhost:3000` and select the **Ticket Router** dashboard.

Each log line that was emitted inside a span will show a **Tempo** button. Clicking it opens the full trace for that request directly in Tempo.

### Simulate queue saturation

To produce a visibly fat `route` span in the trace waterfall, flip the toggle in `app/services/router.py`:

```python
SIMULATE_QUEUE_SATURATION = True
```

Rebuild and fire an urgent ticket:

```bash
docker compose up --build -d app

curl -X POST http://localhost:8000/tickets \
  -H "Content-Type: application/json" \
  -d '{"subject": "URGENT: production down", "body": "Critical outage affecting all clients.", "email": "ops@example.com"}'
```

Open the trace in Tempo. The `route` span will be noticeably wider than the rest, making the bottleneck immediately visible.

## How it works

1. A `POST /tickets` request arrives with `subject`, `body`, and `email`
2. The pipeline runs five steps, each wrapped in an OTel span:
   - **validate**: required fields and email format. Span turns red on failure.
   - **classify**: keyword scoring maps the ticket to a category
   - **prioritize**: category and urgency keywords determine priority
   - **route**: deterministic table maps (category, priority) to a team
   - **acknowledge**: confirmation logged
3. The root span (`ticket.ingest`) carries the final outcome as attributes: ticket ID, category, priority, and team
4. The OTel SDK pushes all three signals to the collector over OTLP HTTP
5. The collector fans out: traces to Tempo, metrics to Prometheus, logs to Loki. A transform processor promotes the `trace_id` from each log record into a Loki label so Grafana can link logs back to their trace.
6. Grafana queries all three backends and displays them in a single pre-built dashboard

## Project Structure

```
se-otel/
├── app/
│   ├── Dockerfile
│   ├── main.py              FastAPI app, metric instruments, endpoints
│   ├── telemetry.py         OTel bootstrap (traces, metrics, logs)
│   └── services/
│       ├── pipeline.py      Orchestrates all five steps
│       ├── classifier.py    Keyword scoring: category
│       ├── prioritizer.py   Urgency keywords: priority
│       ├── router.py        Routing table + saturation toggle
│       ├── store.py         In-memory TicketStore
│       └── keywords.py      Keyword lists
├── config/
│   ├── otel-collector.yaml  Signal pipelines
│   ├── prometheus.yaml      Scrape config
│   ├── tempo.yaml           Storage config
│   ├── loki.yaml            Storage config
│   └── grafana/
│       ├── datasources.yaml
│       └── dashboards/
│           └── overview.json
├── tests/
│   └── test_pipeline.py
├── docker-compose.yml
├── requirements.txt
└── simulate.py
```

# DevPulse — API Health Monitoring & Alerting Service

DevPulse is a backend service that lets developers register REST API endpoints, monitors them on a configurable schedule, and tracks uptime, response time, and error rates over time.

## Features
- **Endpoint Registration**: Monitor any URL with custom intervals, expected status codes, and body substring validation.
- **Background Scheduler**: Async check runner using APScheduler and `httpx`.
- **Real-Time Updates**: Live push updates via Server-Sent Events (SSE) using Redis.
- **Statistics**: Aggregated uptime % and average response times with Redis caching.
- **Alerting**: Webhook-based alerts for monitor failures.
- **JWT Auth**: Secure registration and login.

## Tech Stack
- **Framework**: FastAPI (Async)
- **ORM**: SQLAlchemy (Async) with PostgreSQL
- **Cache/Messaging**: Redis (Pub/Sub & Caching)
- **Scheduler**: APScheduler
- **Containerization**: Docker & Docker Compose

## Quick Start

### Prerequisites
- Docker & Docker Compose

### Running the App
1. Clone the repository.
2. Run the following command:
   ```bash
   docker-compose up --build
   ```
3. The API will be available at `http://localhost:8000`.
4. Access the interactive documentation at `http://localhost:8000/docs`.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Register a new user |
| POST | `/auth/login` | Login and get JWT token |
| GET | `/monitors` | List all your monitors |
| POST | `/monitors` | Create a new monitor |
| GET | `/monitors/{id}` | Get details of a monitor |
| PATCH | `/monitors/{id}` | Update a monitor |
| DELETE | `/monitors/{id}` | Delete a monitor |
| GET | `/monitors/{id}/results` | Get check history |
| GET | `/monitors/{id}/stats` | Get uptime and latency stats |
| GET | `/stream/{id}` | SSE live status stream |

## Architecture Overview
DevPulse uses a "tick-based" background runner. Every 10 seconds, the scheduler wakes up and identifies all active monitors that are due for a check based on their individual `interval_seconds`. Results are stored in PostgreSQL, published to Redis for any active SSE listeners, and triggers webhooks if the check fails.

# Travel MCP Server

Three MCP servers for travel planning, combined into a single process and deployed to Heroku on one dyno.

| MCP | Endpoint | Description |
|-----|----------|-------------|
| **travel-seats** | `/seats/mcp` | Award flight search via [Seats.aero](https://seats.aero) Partner API |
| **travel-flights** | `/flights/mcp` | Google Flights search via [fast-flights](https://pypi.org/project/fast-flights/) |
| **travel-maps** | `/maps/mcp` | Google Maps directions, geocoding, and places |

## Setup

```bash
uv sync
```

## Environment Variables

Copy `.env.example` or create `.env` in the project root. Variables are loaded automatically via `python-dotenv`.

### Common

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `INFO` | Logging level: `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `MCP_TRANSPORT` | `streamable-http` | Transport: `stdio`, `sse`, or `streamable-http` |
| `MCP_HOST` | `0.0.0.0` | HTTP bind host |
| `MCP_PORT` | `8000` | HTTP bind port |

### travel-seats

| Variable | Default | Description |
|----------|---------|-------------|
| `SEATS_AERO_API_KEY` | *(required)* | Seats.aero Partner API key |
| `SEATS_RATE_LIMIT` | `1.0` | Max requests/sec to seats.aero |

### travel-flights

| Variable | Default | Description |
|----------|---------|-------------|
| `FLIGHTS_RATE_LIMIT` | `0.5` | Max requests/sec for Google Flights scraping |

### travel-maps

| Variable | Default | Description |
|----------|---------|-------------|
| `GOOGLE_MAPS_API_KEY` | *(required)* | Google Maps Platform API key |
| `MAPS_RATE_LIMIT` | `10.0` | Max requests/sec to Google Maps API |

## Run Locally

```bash
# Combined server (all three MCPs on one port)
travel-combined

# Or run individually
travel-seats
travel-flights
travel-maps
```

The combined server exposes:
- `http://localhost:8000/seats/mcp`
- `http://localhost:8000/flights/mcp`
- `http://localhost:8000/maps/mcp`
- `http://localhost:8000/health`

## Deploy to Heroku

All three MCPs run on a single dyno.

```bash
heroku create travel-mcp
heroku config:set MCP_TRANSPORT=streamable-http -a travel-mcp
heroku config:set SEATS_AERO_API_KEY=your_key -a travel-mcp
heroku config:set GOOGLE_MAPS_API_KEY=your_key -a travel-mcp
git push heroku main
```

## Rate Limiting

Each server has a configurable async rate limiter with a FIFO request queue. When the rate limit is exhausted, incoming requests are queued and served in order rather than rejected. Configure via environment variables above.

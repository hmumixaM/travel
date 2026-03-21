# Travel MCP Server

Three independent MCP servers for travel planning, deployable to Heroku via streamable-http.

| Server | Command | Description |
|--------|---------|-------------|
| **travel-seats** | `travel-seats` | Award flight search via [Seats.aero](https://seats.aero) Partner API |
| **travel-flights** | `travel-flights` | Google Flights search via [fast-flights](https://pypi.org/project/fast-flights/) |
| **travel-maps** | `travel-maps` | Google Maps directions, geocoding, and places |

## Setup

```bash
uv sync
```

## Environment Variables

### Common

| Variable | Default | Description |
|----------|---------|-------------|
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
# Seats.aero
SEATS_AERO_API_KEY=your_key travel-seats

# Google Flights
travel-flights

# Google Maps
GOOGLE_MAPS_API_KEY=your_key travel-maps
```

## Deploy to Heroku

Each server is deployed as a separate Heroku app from the same repo.

```bash
# Create three Heroku apps
heroku create travel-seats-mcp
heroku create travel-flights-mcp
heroku create travel-maps-mcp

# Configure travel-seats
heroku config:set TRAVEL_SERVER=travel-seats -a travel-seats-mcp
heroku config:set MCP_TRANSPORT=streamable-http -a travel-seats-mcp
heroku config:set SEATS_AERO_API_KEY=your_key -a travel-seats-mcp

# Configure travel-flights
heroku config:set TRAVEL_SERVER=travel-flights -a travel-flights-mcp
heroku config:set MCP_TRANSPORT=streamable-http -a travel-flights-mcp

# Configure travel-maps
heroku config:set TRAVEL_SERVER=travel-maps -a travel-maps-mcp
heroku config:set MCP_TRANSPORT=streamable-http -a travel-maps-mcp
heroku config:set GOOGLE_MAPS_API_KEY=your_key -a travel-maps-mcp

# Deploy (same repo to all three)
git push heroku main
```

## Rate Limiting

Each server has a configurable async rate limiter with a FIFO request queue. When the rate limit is exhausted, incoming requests are queued and served in order rather than rejected. Configure via environment variables above.

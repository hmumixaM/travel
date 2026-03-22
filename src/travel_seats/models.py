"""Agent-friendly domain models for Seats.aero award flight search.

Raw API responses are transformed into these clean types.
The per-cabin (Y/W/J/F) columns are pivoted into rows.

Two output modes:
- Summary: one row per date/cabin/source with best price and seat count
- Detail: full flight itineraries for a specific date
"""

from __future__ import annotations

from dataclasses import dataclass, field

CABIN_CODES = {"Y": "economy", "W": "premium_economy", "J": "business", "F": "first"}
SOURCES = [
    "aeroplan", "alaska", "american", "copaair", "delta", "emirates",
    "etihad", "eurobonus", "flyingblue", "jetblue", "lifemiles",
    "qantas", "smiles", "united", "velocity", "virgin_atlantic",
]


@dataclass
class AwardFlight:
    date: str
    origin: str
    destination: str
    cabin: str
    miles: int
    taxes_usd: float
    seats: int
    airlines: str
    direct: bool
    source: str
    flights: list[FlightLeg] = field(default_factory=list)


@dataclass
class FlightLeg:
    flight: str
    departs: str
    arrives: str
    cabin: str
    aircraft: str
    stops: int
    connections: list[str]
    duration_min: int
    miles: int
    taxes_usd: float
    seats: int


@dataclass
class DaySummary:
    """Aggregated availability for one date + cabin + source."""
    date: str
    route: str
    cabin: str
    source: str
    best_miles: int
    best_taxes: str
    max_seats: int
    direct_available: bool
    airlines: str
    num_options: int


def parse_availability(raw: dict) -> list[AwardFlight]:
    """Extract available cabins from one availability record into AwardFlights."""
    results: list[AwardFlight] = []
    route = raw.get("Route") or {}

    for code, cabin_name in CABIN_CODES.items():
        if not raw.get(f"{code}Available"):
            continue

        cost_str = raw.get(f"{code}MileageCost", "0")
        miles = int(cost_str) if cost_str else 0
        if miles <= 0:
            continue

        results.append(AwardFlight(
            date=raw.get("Date", ""),
            origin=route.get("OriginAirport", ""),
            destination=route.get("DestinationAirport", ""),
            cabin=cabin_name,
            miles=miles,
            taxes_usd=raw.get(f"{code}TotalTaxes", 0) / 100 if raw.get("TaxesCurrency") == "USD" else raw.get(f"{code}TotalTaxes", 0),
            seats=raw.get(f"{code}RemainingSeats", 0),
            airlines=raw.get(f"{code}Airlines", ""),
            direct=raw.get(f"{code}Direct", False),
            source=raw.get("Source", ""),
        ))

    return results


def parse_trip(raw: dict) -> FlightLeg:
    """Convert one raw trip dict into a FlightLeg."""
    return FlightLeg(
        flight=raw.get("FlightNumbers", ""),
        departs=raw.get("DepartsAt", ""),
        arrives=raw.get("ArrivesAt", ""),
        cabin=raw.get("Cabin", ""),
        aircraft=", ".join(raw.get("Aircraft", [])),
        stops=raw.get("Stops", 0),
        connections=raw.get("Connections", []),
        duration_min=raw.get("TotalDuration", 0),
        miles=raw.get("MileageCost", 0),
        taxes_usd=raw.get("TotalTaxes", 0) / 100,
        seats=raw.get("RemainingSeats", 0),
    )


def summarize_awards(awards: list[AwardFlight]) -> list[DaySummary]:
    """Aggregate AwardFlights into per-date/cabin/source summaries."""
    buckets: dict[tuple[str, str, str], list[AwardFlight]] = {}
    for a in awards:
        key = (a.date, a.cabin, a.source)
        buckets.setdefault(key, []).append(a)

    summaries: list[DaySummary] = []
    for (date, cabin, source), group in buckets.items():
        best = min(group, key=lambda a: a.miles)
        total_options = sum(len(a.flights) for a in group) or len(group)
        summaries.append(DaySummary(
            date=date,
            route=f"{best.origin}-{best.destination}",
            cabin=cabin,
            source=source,
            best_miles=best.miles,
            best_taxes=f"${best.taxes_usd:.2f}",
            max_seats=max(a.seats for a in group),
            direct_available=any(a.direct for a in group),
            airlines=best.airlines,
            num_options=total_options,
        ))

    summaries.sort(key=lambda s: (s.date, s.best_miles))
    return summaries


def format_summary(s: DaySummary) -> dict:
    """Serialize a DaySummary for the agent."""
    return {
        "date": s.date,
        "route": s.route,
        "cabin": s.cabin,
        "source": s.source,
        "from_miles": s.best_miles,
        "taxes": s.best_taxes,
        "seats": s.max_seats,
        "direct": s.direct_available,
        "airlines": s.airlines,
        "options": s.num_options,
    }


def format_flight_leg(leg: FlightLeg) -> dict:
    """Serialize a FlightLeg for detail view."""
    return {
        "flight": leg.flight,
        "departs": leg.departs,
        "arrives": leg.arrives,
        "cabin": leg.cabin,
        "aircraft": leg.aircraft,
        "stops": leg.stops,
        "connections": leg.connections,
        "duration_min": leg.duration_min,
        "miles": leg.miles,
        "taxes": f"${leg.taxes_usd:.2f}",
        "seats": leg.seats,
    }

"""Agent-friendly domain models for Seats.aero award flight search.

Raw API responses are transformed into these clean types before being
returned to the agent.  Each AwardFlight is one bookable option —
the per-cabin (Y/W/J/F) columns from the API are pivoted into rows
so the agent sees a flat list it can reason about.
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


def format_award_flight(f: AwardFlight) -> dict:
    """Serialize an AwardFlight for the agent."""
    out: dict = {
        "date": f.date,
        "route": f"{f.origin}-{f.destination}",
        "cabin": f.cabin,
        "miles": f.miles,
        "taxes": f"${f.taxes_usd:.2f}",
        "seats": f.seats,
        "airlines": f.airlines,
        "direct": f.direct,
        "source": f.source,
    }
    if f.flights:
        out["flights"] = [
            {
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
            for leg in f.flights
        ]
    return out

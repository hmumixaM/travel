from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict


class Route(BaseModel):
    ID: str
    OriginAirport: str
    OriginRegion: str
    DestinationAirport: str
    DestinationRegion: str
    NumDaysOut: int
    Distance: int
    Source: str


class SearchResult(BaseModel):
    ID: str
    RouteID: str
    Route: Route
    Date: str
    ParsedDate: str
    YAvailable: bool
    WAvailable: bool
    JAvailable: bool
    FAvailable: bool
    YMileageCost: Optional[str]
    WMileageCost: Optional[str]
    JMileageCost: Optional[str]
    FMileageCost: Optional[str]
    YRemainingSeats: int
    WRemainingSeats: int
    JRemainingSeats: int
    FRemainingSeats: int
    YAirlines: Optional[str]
    WAirlines: Optional[str]
    JAirlines: Optional[str]
    FAirlines: Optional[str]
    YDirect: bool
    WDirect: bool
    JDirect: bool
    FDirect: bool
    Source: str
    CreatedAt: str
    UpdatedAt: str
    AvailabilityTrips: Optional[str]


class SearchResponse(BaseModel):
    data: list[SearchResult]
    count: int
    hasMore: bool
    cursor: int


class AvailabilityResult(BaseModel):
    ID: str
    RouteID: str
    Route: Route
    Date: str
    ParsedDate: str
    YAvailable: bool
    WAvailable: bool
    JAvailable: bool
    FAvailable: bool
    YMileageCost: Optional[str]
    WMileageCost: Optional[str]
    JMileageCost: Optional[str]
    FMileageCost: Optional[str]
    YRemainingSeats: int
    WRemainingSeats: int
    JRemainingSeats: int
    FRemainingSeats: int
    YAirlines: Optional[str]
    WAirlines: Optional[str]
    JAirlines: Optional[str]
    FAirlines: Optional[str]
    YDirect: bool
    WDirect: bool
    JDirect: bool
    FDirect: bool
    Source: str
    CreatedAt: str
    UpdatedAt: str
    AvailabilityTrips: Optional[str]


class AvailabilityResponse(BaseModel):
    data: list[AvailabilityResult]
    count: int
    hasMore: bool
    cursor: int


class TripDetails(BaseModel):
    model_config = ConfigDict(extra="allow")
    ID: str

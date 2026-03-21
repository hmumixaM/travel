from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class Route(BaseModel):
    model_config = ConfigDict(extra="allow")
    ID: str
    OriginAirport: str = ""
    OriginRegion: str = ""
    DestinationAirport: str = ""
    DestinationRegion: str = ""
    NumDaysOut: Optional[int] = None
    Distance: Optional[int] = None
    Source: str = ""


class SearchResult(BaseModel):
    model_config = ConfigDict(extra="allow")
    ID: str
    RouteID: str = ""
    Route: Any = None
    Date: str = ""
    ParsedDate: str = ""
    YAvailable: bool = False
    WAvailable: bool = False
    JAvailable: bool = False
    FAvailable: bool = False
    YMileageCost: Optional[str] = None
    WMileageCost: Optional[str] = None
    JMileageCost: Optional[str] = None
    FMileageCost: Optional[str] = None
    YRemainingSeats: int = 0
    WRemainingSeats: int = 0
    JRemainingSeats: int = 0
    FRemainingSeats: int = 0
    YAirlines: Optional[str] = None
    WAirlines: Optional[str] = None
    JAirlines: Optional[str] = None
    FAirlines: Optional[str] = None
    YDirect: bool = False
    WDirect: bool = False
    JDirect: bool = False
    FDirect: bool = False
    Source: str = ""
    CreatedAt: str = ""
    UpdatedAt: str = ""
    AvailabilityTrips: Any = None


class SearchResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    data: list[SearchResult] = []
    count: int = 0
    hasMore: bool = False
    cursor: int = 0


class AvailabilityResult(BaseModel):
    model_config = ConfigDict(extra="allow")
    ID: str
    RouteID: str = ""
    Route: Any = None
    Date: str = ""
    ParsedDate: str = ""
    YAvailable: bool = False
    WAvailable: bool = False
    JAvailable: bool = False
    FAvailable: bool = False
    YMileageCost: Optional[str] = None
    WMileageCost: Optional[str] = None
    JMileageCost: Optional[str] = None
    FMileageCost: Optional[str] = None
    YRemainingSeats: int = 0
    WRemainingSeats: int = 0
    JRemainingSeats: int = 0
    FRemainingSeats: int = 0
    YAirlines: Optional[str] = None
    WAirlines: Optional[str] = None
    JAirlines: Optional[str] = None
    FAirlines: Optional[str] = None
    YDirect: bool = False
    WDirect: bool = False
    JDirect: bool = False
    FDirect: bool = False
    Source: str = ""
    CreatedAt: str = ""
    UpdatedAt: str = ""
    AvailabilityTrips: Any = None


class AvailabilityResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    data: list[AvailabilityResult] = []
    count: int = 0
    hasMore: bool = False
    cursor: int = 0


class TripDetails(BaseModel):
    model_config = ConfigDict(extra="allow")
    ID: str

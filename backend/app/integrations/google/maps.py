"""Google Maps Platform (REST): Geocoding and Routes (compute route matrix), plus nearest-facility ranking.

The key (GOOGLE_MAPS_API_KEY) is sent in a header, never in a URL or log. Ranking always starts with a real haversine
computation over Facility lat/long; Routes refines the top N when the key exists. `method` says which was used.
"""
import math
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Protocol, Sequence, Tuple

import httpx

from app.core.config import settings
from app.integrations.google.errors import GoogleError, NotConfigured
from app.integrations.google.http import request_json

EARTH_RADIUS_KM = 6371.0088


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi, dlmb = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(min(1.0, math.sqrt(a)))


@dataclass
class RouteLeg:
    distance_m: int
    duration_s: int


class MapsClient(Protocol):
    def is_configured(self) -> bool: ...

    async def geocode(self, address: str) -> Optional[Tuple[float, float, str]]: ...

    async def route_matrix(self, origin: Tuple[float, float],
                           destinations: Sequence[Tuple[float, float]]) -> Dict[int, RouteLeg]: ...


class GoogleMapsClient:
    def __init__(self, api_key: Optional[str] = None, timeout: Optional[float] = None,
                 transport: Optional[httpx.AsyncBaseTransport] = None,
                 geocode_base: Optional[str] = None, routes_base: Optional[str] = None):
        self.api_key = settings.GOOGLE_MAPS_API_KEY if api_key is None else api_key
        self.timeout = timeout or settings.AI_REQUEST_TIMEOUT_SECONDS
        self._transport = transport
        self.geocode_base = geocode_base or settings.GOOGLE_MAPS_GEOCODE_BASE
        self.routes_base = routes_base or settings.GOOGLE_MAPS_ROUTES_BASE

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def _require(self) -> None:
        if not self.api_key:
            raise NotConfigured("GOOGLE_MAPS_API_KEY is not set")

    async def geocode(self, address: str) -> Optional[Tuple[float, float, str]]:
        """(lat, lng, formatted_address), or None when Google finds no match (a real result, not an error)."""
        self._require()
        # The legacy Geocoding API only accepts the key as a query parameter (verified live: the header is denied).
        data = await request_json("GET", self.geocode_base, headers={},
                                  params={"address": address, "region": "in", "key": self.api_key}, timeout=self.timeout,
                                  transport=self._transport)
        status = data.get("status") if isinstance(data, dict) else None
        if status == "ZERO_RESULTS":
            return None
        if status != "OK":
            raise GoogleError(f"geocode status {status}")
        try:
            top = data["results"][0]
            loc = top["geometry"]["location"]
            return float(loc["lat"]), float(loc["lng"]), str(top.get("formatted_address", ""))
        except (KeyError, IndexError, TypeError, ValueError):
            raise GoogleError("malformed geocode response") from None

    async def route_matrix(self, origin: Tuple[float, float],
                           destinations: Sequence[Tuple[float, float]]) -> Dict[int, RouteLeg]:
        """Driving distance/time from one origin to each destination, keyed by destination index."""
        self._require()

        def wp(pt):
            return {"waypoint": {"location": {"latLng": {"latitude": pt[0], "longitude": pt[1]}}}}

        body = {"origins": [wp(origin)], "destinations": [wp(d) for d in destinations],
                "travelMode": "DRIVE", "routingPreference": "TRAFFIC_UNAWARE"}
        headers = {"x-goog-api-key": self.api_key, "Content-Type": "application/json",
                   "X-Goog-FieldMask": "originIndex,destinationIndex,duration,distanceMeters,condition"}
        data = await request_json("POST", self.routes_base, headers=headers, json_body=body,
                                  timeout=self.timeout, transport=self._transport)
        if not isinstance(data, list):
            raise GoogleError("malformed route matrix response")
        out: Dict[int, RouteLeg] = {}
        for el in data:
            if not isinstance(el, dict) or el.get("condition") not in (None, "ROUTE_EXISTS"):
                continue
            m = re.fullmatch(r"(\d+(?:\.\d+)?)s", str(el.get("duration", "")))
            if m is None or "distanceMeters" not in el:
                continue
            out[int(el.get("destinationIndex", 0))] = RouteLeg(int(el["distanceMeters"]), int(float(m.group(1))))
        return out


def get_maps_client() -> MapsClient:
    """Dependency seam: tests replace this."""
    return GoogleMapsClient()


@dataclass
class FacilityPoint:
    id: str
    name: str
    code: str
    facility_type: str
    state: str
    district: str
    latitude: float
    longitude: float


async def rank_nearest(client: MapsClient, lat: float, lng: float, facilities: List[FacilityPoint],
                       limit: int) -> Tuple[str, List[dict]]:
    """Haversine over all facilities, then Routes refinement of the top N when configured.

    Returns (method, rows). method is 'google_routes' when refined; 'haversine_only' when no key is set or Routes
    failed (straight-line distances are then real great-circle distances, not driving times).
    """
    rows = [{"facility": f, "straight_line_km": round(haversine_km(lat, lng, f.latitude, f.longitude), 3),
             "driving_distance_km": None, "driving_minutes": None} for f in facilities]
    rows.sort(key=lambda r: r["straight_line_km"])
    top = rows[: max(limit, min(len(rows), settings.GOOGLE_MAPS_REFINE_TOP_N))]
    method = "haversine_only"
    if client.is_configured() and top:
        try:
            legs = await client.route_matrix((lat, lng), [(r["facility"].latitude, r["facility"].longitude) for r in top])
        except GoogleError:
            legs = {}
        if legs:
            for i, r in enumerate(top):
                leg = legs.get(i)
                if leg:
                    r["driving_distance_km"] = round(leg.distance_m / 1000, 2)
                    r["driving_minutes"] = round(leg.duration_s / 60, 1)
            top.sort(key=lambda r: (r["driving_minutes"] is None,
                                    r["driving_minutes"] if r["driving_minutes"] is not None else r["straight_line_km"]))
            method = "google_routes"
    return method, top[:limit]

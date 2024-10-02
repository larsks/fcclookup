from typing import Literal

import datetime

from pydantic_xml import BaseXmlModel, attr, element
from pydantic import NonNegativeInt


class Link(BaseXmlModel, tag="link"):
    href: str = attr()
    type: str | None = element(default=None)
    text: str | None = element(default=None)


class Email(BaseXmlModel, tag="email"):
    id: str = attr()
    domain: str = attr()


class Person(BaseXmlModel):
    name: str | None = element(default=None)
    email: Email | None = None
    link: Link | None = None


class Author(Person, tag="author"):
    pass


class Copyright(BaseXmlModel, tag="copyright"):
    author: str
    license: str
    year: int


class Bounds(BaseXmlModel, tag="bounds"):
    minlat: float = attr()
    minlon: float = attr()
    maxlat: float = attr()
    maxlon: float = attr()


class Metadata(BaseXmlModel, tag="metadata"):
    name: str | None = element(default=None)
    desc: str | None = element(default=None)
    author: Author | None = element(default=None)
    copyright: Copyright | None = element(default=None)
    link: Link | None = element(default=None)
    time: datetime.datetime | None = element(default=None)
    keywords: str | None = element(default=None)
    bounds: Bounds | None = element(default=None)


class Point(BaseXmlModel):
    lat: float | None = attr(default=None)
    lon: float | None = attr(default=None)

    time: datetime.datetime | None = element(default=None)


class Waypoint(Point):
    ageofdgpsdata: float | None = element(default=None)
    cmt: str | None = element(default=None)
    desc: str | None = element(default=None)
    dgpsid: str | None = element(default=None)
    ele: float | None = element(default=None)
    fix: str | None = element(default=None)
    geoidheight: float | None = element(default=None)
    hdop: float | None = element(default=None)
    link: Link | None = element(default=None)
    magvar: float | None = element(default=None)
    name: str | None = element(default=None)
    pdop: float | None = element(default=None)
    sat: NonNegativeInt | None = element(default=None)
    src: str | None = element(default=None)
    sym: str | None = element(default=None)
    type: str | None = element(default=None)
    vdop: float | None = element(default=None)


class _waypointContainer(BaseXmlModel):
    name: str | None = element(default=None)
    cmt: str | None = element(default=None)
    desc: str | None = element(default=None)
    src: str | None = element(default=None)
    link: Link | None = element(default=None)
    number: NonNegativeInt | None = element(default=None)
    type: str | None = element(default=None)


class Route(_waypointContainer, tag="rte"):
    routepoints: list[Waypoint] = element(tag="rtept", default_factory=list)


class TrackSegment(BaseXmlModel, tag="trkseg"):
    trackpoints: list[Waypoint] = element(tag="trkpt", default_factory=list)


class Track(_waypointContainer, tag="trk"):
    track_segments: TrackSegment | None = element(tag="trkseg", default=None)


class GpxFile(
    BaseXmlModel,
    tag="gpx",
    nsmap={
        "xsi": "http://www.w3.org/2001/XMLSchema-instance",
        "": "http://www.topografix.com/GPX/1/1",
    },
):
    schemaLocation: Literal[
        "http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd"
    ] = attr(
        default="http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd",
        name="schemaLocation",
        ns="xsi",
    )
    version: Literal["1.1"] = attr(default="1.1")
    metadata: Metadata | None = None
    waypoints: list[Waypoint] = element(tag="wpt", default_factory=list)
    routes: list[Route] = element(tag="rte", default_factory=list)
    tracks: list[Track] = element(tag="trk", default_factory=list)

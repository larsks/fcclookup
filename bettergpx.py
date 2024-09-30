from typing import Literal

import datetime

from pydantic_xml import BaseXmlModel, attr, element
from pydantic import NonNegativeInt


class Link(BaseXmlModel):
    href: str
    type: str | None = attr(default=None)
    text: str | None = attr(default=None)


class Metadata(BaseXmlModel):
    name: str | None = attr(default=None)
    desc: str | None = attr(default=None)
    keywords: str | None = attr(default=None)
    link: Link | None = None


class Waypoint(BaseXmlModel):
    lat: float | None = attr(default=None)
    lon: float | None = attr(default=None)

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
    time: datetime.datetime | None = element(default=None)
    type: str | None = element(default=None)
    vdop: float | None = element(default=None)


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
    wpt: list[Waypoint] = []

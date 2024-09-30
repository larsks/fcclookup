from typing import Any, cast

import os
import sys
import io
import diskcache
import click
import dotenv
import requests
import time
import logging
import bettergpx as gpx

from urllib.parse import quote as urlquote

from sqlalchemy import create_engine
from sqlalchemy import select
from sqlalchemy.orm import Session

from rich import box
from rich.console import Console
from rich.table import Table

from fccdb import Entity
from fccdb import History

from pydantic import BaseModel, Field, RootModel

dotenv.load_dotenv()
LOG = logging.getLogger(__name__)
# [
#  {
#    "place_id": 322043032,
#    "licence": "Data © OpenStreetMap contributors, ODbL 1.0. https://osm.org/copyright",
#    "osm_type": "way",
#    "osm_id": 29813325,
#    "boundingbox": [
#      "42.3843528",
#      "42.3844454",
#      "-71.1629423",
#      "-71.1627534"
#    ],
#    "lat": "42.38441015",
#    "lon": "-71.16284786649706",
#    "display_name": "64, Livermore Road, Belmont, Middlesex County, Massachusetts, 20478, United States",
#    "class": "building",
#    "type": "yes",
#    "importance": 0.41000999999999993
#  }
# ]


class LocatorApiResult(BaseModel):
    place_id: int
    licence: str
    osm_type: str | None = None
    osm_id: int | None = None
    boundingbox: tuple[str, str, str, str]
    lat: str
    lon: str
    display_name: str
    feature_class: str = Field(..., alias="class")
    type: str
    importance: float


LocatorApiResponse = RootModel[list[LocatorApiResult]]


class Location(BaseModel):
    lat: float
    lon: float


class Locator:
    geocode_url = "https://geocode.maps.co/search?q={address}&api_key={api_key}"
    cache: dict[str, Any] = {}
    cache_hits: int = 0
    cache_misses: int = 0

    def __init__(self, apikey: str, cachepath: str | None = None):
        self.apikey = apikey
        self.last_request = time.time()

        if cachepath is None:
            xdg_cache_dir = os.environ.get(
                "XDG_CACHE_HOME", os.path.join(os.environ["HOME"], ".cache")
            )

            cachepath = os.path.join(xdg_cache_dir, "fccdb")

        self.cache = diskcache.Cache(cachepath)

    def lookup_address(self, address: str) -> LocatorApiResponse:
        now = time.time()
        if (now - self.last_request) < 1:
            time.sleep(1)
        self.last_request = time.time()
        res = requests.get(
            self.geocode_url.format(api_key=self.apikey, address=urlquote(address))
        )
        return LocatorApiResponse.model_validate(res.json())

    def locate(self, address: str) -> Location:
        if address in self.cache:
            self.cache_hits += 1
            return self.cache[address]

        self.cache_misses += 1
        res = self.lookup_address(address)

        if len(res.root) > 1:
            raise ValueError(f"multiple results for {address}")
        if len(res.root) == 0:
            raise ValueError(f"no results for {address}")

        loc = Location(lat=float(res.root[0].lat), lon=float(res.root[0].lon))
        self.cache[address] = loc
        return loc


@click.command(context_settings={"auto_envvar_prefix": "FCC"})
@click.option("--dburi", "-d")
@click.option("--api-key", "-k")
@click.option("--verbosity", "-v", count=True)
@click.option(
    "--label-format", "-L", default="{full_name} [{operator_class}] {call_sign}"
)
@click.option("--desc-format", "-D", default="{address}")
@click.option(
    "--output", "-o", "output_file", type=click.File(mode="w"), default=sys.stdout
)
def main(
    dburi: str,
    api_key: str,
    verbosity: int,
    label_format: str,
    desc_format: str,
    output_file: io.IOBase,
):
    logLevel = ["WARNING", "INFO", "DEBUG"][min(verbosity, 2)]
    logging.basicConfig(
        level=logLevel,
        format="%(asctime)s.%(msecs)03d [%(levelname)s] %(message)s",
        datefmt="%T",
    )
    locator = Locator(api_key)
    engine = create_engine(dburi, echo=False)
    gpxout = gpx.GpxFile()
    with Session(engine) as session:
        q = select(Entity).where(Entity.zip_code == "02478")
        res = session.execute(q)
        for entity in res.scalars():
            last_status: History | None = next(
                reversed(sorted(entity.history, key=lambda x: x.log_date)), None
            )
            full_name = " ".join(
                [
                    getattr(entity, x)
                    for x in ["first_name", "mi", "last_name"]
                    if getattr(entity, x)
                ]
            )
            if last_status is not None and last_status.code.strip() in [
                "LICAN",
                "LIEXP",
            ]:
                LOG.info(f"skipping {full_name} ({entity.call_sign}): license expired")
            address = f"{entity.street_address}, {entity.city}, {entity.state} {entity.zip_code}"
            try:
                loc = locator.locate(address)
            except ValueError as err:
                LOG.error(err)
                continue

            attrs = {
                "full_name": full_name,
                "loc": loc,
                "address": address,
            }
            attrs.update(entity.to_dict())
            attrs.update(entity.license.to_dict())

            desc = desc_format.format(**attrs)
            label = label_format.format(**attrs)

            gpxout.wpt.append(
                gpx.Waypoint(
                    name=label,
                    desc=desc,
                    lat=loc.lat,
                    lon=loc.lon,
                )
            )

    with output_file:
        output_file.write(gpxout.to_xml(skip_empty=True, pretty_print=True).decode())


if __name__ == "__main__":
    main()

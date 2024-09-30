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

from fccdb import Base
from fccdb import Entity
from fccdb import Amateur

from pydantic import BaseModel, Field

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


class LocatorApiResponse(BaseModel):
    place_id: int
    licence: str
    osm_type: str
    osm_id: int
    boundingbox: tuple[str, str, str, str]
    lat: str
    lon: str
    display_name: str
    feature_class: str = Field(..., alias="class")
    type: str
    importance: float


class Location(BaseModel):
    lat: float
    lon: float


class Locator:
    geocode_url = "https://geocode.maps.co/search?q={address}&api_key={api_key}"

    def __init__(self, apikey: str):
        self.apikey = apikey
        self.last_request = time.time()

    def locate(self, address: str) -> Location:
        now = time.time()
        if (now - self.last_request) < 1:
            time.sleep(1)
        self.last_request = time.time()
        res = requests.get(
            self.geocode_url.format(api_key=self.apikey, address=urlquote(address))
        )
        res.raise_for_status()
        obj: list[dict[str, str]] = res.json()

        if len(obj) > 1:
            raise ValueError(f"multiple results for {address}")
        if len(obj) == 0:
            raise ValueError(f"no results for {address}")
        loc = LocatorApiResponse.model_validate(obj[0])
        return Location(lat=float(loc.lat), lon=float(loc.lon))


@click.command(context_settings={"auto_envvar_prefix": "FCC"})
@click.option("--dburi", "-d")
@click.option("--api-key", "-k")
@click.option("--verbosity", "-v", count=True)
def main(dburi: str, api_key: str, verbosity: int):
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
            name = " ".join(
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
                LOG.info(f"skipping {name} ({entity.call_sign}): license expired")
            address = f"{entity.street_address}, {entity.city}, {entity.state} {entity.zip_code}"
            try:
                loc = locator.locate(address)
            except ValueError as err:
                LOG.error(err)
                continue

            gpxout.wpt.append(
                gpx.Waypoint(
                    name=f"{name} [{entity.license.operator_class}]",
                    desc=address,
                    lat=loc.lat,
                    lon=loc.lon,
                )
            )

    print(gpxout.to_xml(skip_empty=True, pretty_print=True).decode())


if __name__ == "__main__":
    main()

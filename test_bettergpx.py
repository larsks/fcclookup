import pytest
import bettergpx


@pytest.fixture
def ex_waypoint() -> bettergpx.Waypoint:
    return bettergpx.Waypoint(lat=42.8728, lon=-100.551)


@pytest.fixture
def ex_track(ex_waypoint: bettergpx.Waypoint) -> bettergpx.Track:
    trk = bettergpx.Track(name="test track")
    trk.track_segments = bettergpx.TrackSegment()
    trk.track_segments.trackpoints.append(ex_waypoint)
    return trk


@pytest.fixture
def ex_route(ex_waypoint: bettergpx.Waypoint) -> bettergpx.Route:
    rte = bettergpx.Route(name="test route")
    rte.routepoints.append(ex_waypoint)
    return rte


@pytest.fixture
def ex_gpx_xml() -> bytes:
    return (
        b'<gpx xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://www.topografix.com/GPX/1/1" xsi:schemaLocation="http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd" version="1.1">'
        b'<rte><name>test route</name><rtept lat="42.8728" lon="-100.551"/></rte>'
        b'<trk><name>test track</name><trkseg><trkpt lat="42.8728" lon="-100.551"/></trkseg></trk>'
        b"</gpx>"
    )


@pytest.fixture
def ex_metadata() -> bettergpx.Metadata:
    return bettergpx.Metadata(
        name="example metadata",
        author=bettergpx.Author(
            name="Alice Example",
            email=bettergpx.Email(id="alice", domain="example.com"),
        ),
        link=bettergpx.Link(href="https://example.com", text="example website"),
    )


@pytest.fixture
def ex_bounds() -> bettergpx.Bounds:
    return bettergpx.Bounds(
        minlat=42.37,
        minlon=-71.14,
        maxlat=42.38,
        maxlon=-71.15,
    )


def test_empty_gpx():
    gpx = bettergpx.GpxFile()
    assert gpx.to_xml()


def test_waypoint(ex_waypoint: bettergpx.Waypoint):
    assert (
        ex_waypoint.to_xml(skip_empty=True)
        == b'<Waypoint lat="42.8728" lon="-100.551"/>'
    )


def test_track(ex_track: bettergpx.Track):
    assert (
        ex_track.to_xml(skip_empty=True)
        == b'<trk><name>test track</name><trkseg><trkpt lat="42.8728" lon="-100.551"/></trkseg></trk>'
    )


def test_route(ex_route: bettergpx.Route):
    assert (
        ex_route.to_xml(skip_empty=True)
        == b'<rte><name>test route</name><rtept lat="42.8728" lon="-100.551"/></rte>'
    )


def test_gpx_with_route_and_track(
    ex_gpx_xml: bytes, ex_route: bettergpx.Route, ex_track: bettergpx.Track
):
    gpx = bettergpx.GpxFile(routes=[ex_route], tracks=[ex_track])
    assert gpx.to_xml(skip_empty=True) == ex_gpx_xml


@pytest.mark.xfail(reason="unmarshalling does not work as expected")
def test_parse_gpx(ex_gpx_xml: bytes):
    gpx = bettergpx.GpxFile.from_xml(ex_gpx_xml)
    assert gpx.to_xml(skip_empty=True) == ex_gpx_xml


def test_metadata(ex_metadata: bettergpx.Metadata):
    assert ex_metadata.to_xml(skip_empty=True) == (
        b"<metadata>"
        b"<name>example metadata</name>"
        b"<author><name>Alice Example</name>"
        b'<email id="alice" domain="example.com"/>'
        b"</author>"
        b'<link href="https://example.com">'
        b"<text>example website</text></link>"
        b"</metadata>"
    )


def test_bounds(ex_bounds: bettergpx.Bounds):
    assert (
        ex_bounds.to_xml(skip_empty=True)
        == b'<bounds minlat="42.37" minlon="-71.14" maxlat="42.38" maxlon="-71.15"/>'
    )

import importlib

import bahnapi


def test_public_api_surface():
    assert hasattr(bahnapi, "__version__")
    assert callable(bahnapi.configure)
    assert callable(bahnapi.get_departures)
    assert callable(bahnapi.search_stations)


def test_version_metadata():
    pkg = importlib.import_module("bahnapi")
    assert isinstance(pkg.__version__, str)

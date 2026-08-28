"""The wheel must carry its own front end.

`packages = ["src/tycoon_city"]` ships non-Python files inside the package,
so the bundle rides along — but only if it is actually there. A data file
that does not ship is the classic version of this bug, which is why this
resolves through importlib.resources rather than through the checkout.
"""

from importlib import resources


def test_the_packaged_bundle_exists_and_has_an_entry_point():
    bundle = resources.files("tycoon_city") / "web_dist"
    assert bundle.is_dir(), "no packaged web bundle — run scripts/sync_web_bundle.py"
    assert (bundle / "index.html").is_file(), "the bundle has no index.html to serve"


def test_the_packaged_bundle_carries_no_dev_catalog():
    """web/public/city.json is a developer's demo catalog. Shipping it would
    bake a stale city into the wheel that the server would then serve as fact."""
    bundle = resources.files("tycoon_city") / "web_dist"
    assert not (bundle / "city.json").is_file(), "dev data rode along into the package"

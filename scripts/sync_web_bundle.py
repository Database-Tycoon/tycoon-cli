#!/usr/bin/env python3
"""Build the web bundle and copy it into the package as shipped data.

`web/public/` holds gitignored dev data (a demo city.json); the server
generates /city.json itself, so the release bundle must be built without it.
The Dockerfile does the same `rm -rf public` for the same reason — this
script does not delete the developer's copy, it moves it aside and restores
it in a `finally`, so a failed build does not destroy local dev data.
"""

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"
TARGET = ROOT / "src" / "tycoon_city" / "web_dist"


def main() -> int:
    public = WEB / "public"
    stashed = WEB / "public.stashed"
    if stashed.exists() and not public.exists():
        # A crashed run left the stash behind and no `public`. Putting it back
        # is the only reading of that state: the stash IS the developer's data,
        # and building over it would strand it here forever.
        print(f"restoring {stashed} left behind by an earlier run", file=sys.stderr)
        shutil.move(str(stashed), str(public))
    moved = False
    if public.is_dir():
        if stashed.exists():
            raise SystemExit(
                f"{stashed} already exists — a previous run did not clean up; resolve it by hand before re-running"
            )
        shutil.move(str(public), str(stashed))
        moved = True
    try:
        subprocess.run(["npm", "run", "build"], cwd=WEB, check=True)
    finally:
        if moved:
            shutil.move(str(stashed), str(public))

    # Check the source BEFORE touching the committed bundle. `rmtree` first
    # meant a build that produced nothing usable deleted the shipped front end
    # and then failed — git-recoverable, but the wheel is broken until someone
    # notices.
    source = WEB / "dist"
    if not (source / "index.html").is_file():
        raise SystemExit(f"{source} has no index.html — the build produced no bundle; leaving {TARGET} as it is")
    if TARGET.exists():
        shutil.rmtree(TARGET)
    shutil.copytree(source, TARGET)
    leaked = TARGET / "city.json"
    if leaked.exists():
        leaked.unlink()
        print(f"removed dev data that rode along: {leaked}", file=sys.stderr)
    print(f"synced {sum(1 for _ in TARGET.rglob('*') if _.is_file())} files to {TARGET}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

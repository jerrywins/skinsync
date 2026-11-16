"""Regression: the API image copies apps/api to /app. Any Path(__file__).parents[n] that reaches above /app
works in the repo (deeper path) but raises IndexError or points outside the image in the container."""

import re
from pathlib import Path

API = Path(__file__).resolve().parents[1]
PAT = re.compile(r"Path\(__file__\)\.resolve\(\)\.parents\[(\d+)\]")


def test_no_path_escapes_the_container_app_dir():
    bad = []
    for f in [*API.joinpath("skinsync").rglob("*.py"), *API.joinpath("alembic").rglob("*.py")]:
        depth = len(f.relative_to(API).parts)  # /app/<parts...>
        for m in PAT.finditer(f.read_text(encoding="utf-8")):
            if int(m.group(1)) > depth - 1:  # parents[depth-1] is /app itself
                bad.append(f"{f.relative_to(API)}: parents[{m.group(1)}]")
    assert not bad, bad

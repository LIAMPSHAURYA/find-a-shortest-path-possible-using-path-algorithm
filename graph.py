"""Graph model + CSV loading/validation."""
from __future__ import annotations

import csv
from pathlib import Path


class DataError(ValueError):
    """Raised when the CSV data is malformed."""


class Graph:
    """Undirected weighted graph with 2-D city coordinates (used to draw the map)."""

    def __init__(self) -> None:
        self.pos: dict[str, tuple[float, float]] = {}
        self.adj: dict[str, dict[str, float]] = {}

    # ---- building -------------------------------------------------------
    def add_city(self, name: str, x: float, y: float) -> None:
        if not name:
            raise DataError("city name is empty")
        if name in self.adj:
            raise DataError(f"duplicate city {name!r}")
        self.pos[name] = (x, y)
        self.adj[name] = {}

    def add_road(self, a: str, b: str, km: float) -> None:
        for c in (a, b):
            if c not in self.adj:
                raise DataError(f"unknown city {c!r}")
        if a == b:
            raise DataError(f"road from {a!r} to itself")
        if km <= 0:
            raise DataError(f"distance must be positive ({a}-{b}: {km})")
        self.adj[a][b] = km
        self.adj[b][a] = km

    def roads(self) -> list[tuple[str, str, float]]:
        return [(a, b, w) for a, nbrs in sorted(self.adj.items())
                for b, w in sorted(nbrs.items()) if a < b]

    # ---- CSV ------------------------------------------------------------
    @classmethod
    def from_csv(cls, cities_file: str | Path, roads_file: str | Path) -> "Graph":
        g = cls()
        for line, row in cls._rows(cities_file, {"city", "x", "y"}):
            try:
                g.add_city(row["city"].strip(), float(row["x"]), float(row["y"]))
            except (ValueError, DataError) as e:
                raise DataError(f"{Path(cities_file).name} line {line}: {e}") from None
        for line, row in cls._rows(roads_file, {"city_a", "city_b", "km"}):
            try:
                g.add_road(row["city_a"].strip(), row["city_b"].strip(), float(row["km"]))
            except (ValueError, DataError) as e:
                raise DataError(f"{Path(roads_file).name} line {line}: {e}") from None
        if not g.adj:
            raise DataError("no cities found")
        return g

    @staticmethod
    def _rows(path, required):
        with open(path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            missing = required - set(reader.fieldnames or [])
            if missing:
                raise DataError(f"{Path(path).name}: missing column(s) {sorted(missing)}")
            for i, row in enumerate(reader, start=2):
                if any((v or "").strip() for v in row.values()):
                    yield i, row

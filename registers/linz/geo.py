"""Geometry without PostGIS (Arthur, 4 November 2026, ruling 142: "Get LINZ and all available information"): a GeoJSON
geometry's type and bounding box, a point inside a polygon, and a grid of points so each polygon is tried only against
the points near it. Pure Python, no extension: the database holds a geometry as its GeoJSON text and its box as four
numbers (`linz_private`), and the lane's joins run here.

    bbox(geometry)                    (xmin, ymin, xmax, ymax) or None
    contains(geometry, x, y)          a point strictly inside a Polygon or MultiPolygon (holes honoured)
    Grid(cell).add(key, x, y) / .near(box)   the points whose cell meets a box

Coordinates are as LINZ gives them (longitude, latitude, NZGD2000); every layer read is in the one system, so no
reprojection is done. A point on a boundary may fall either side; a title's address by geometry says so
(`load.GEOMETRY_JOINED_BY`).
"""
import math


def _points(coords):
    """Every coordinate pair in a GeoJSON coordinates array, however deep."""
    if not coords:
        return
    if isinstance(coords[0], (int, float)):
        yield coords
        return
    for c in coords:
        yield from _points(c)


def bbox(geometry):
    if not geometry or not geometry.get("coordinates"):
        return None
    xs, ys = [], []
    for p in _points(geometry["coordinates"]):
        xs.append(p[0])
        ys.append(p[1])
    return (min(xs), min(ys), max(xs), max(ys)) if xs else None


def _in_ring(ring, x, y) -> bool:
    inside = False
    n = len(ring)
    j = n - 1
    for i in range(n):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


def _in_polygon(rings, x, y) -> bool:
    if not rings or not _in_ring(rings[0], x, y):
        return False
    return not any(_in_ring(h, x, y) for h in rings[1:])


def contains(geometry, x: float, y: float) -> bool:
    if not geometry:
        return False
    t, c = geometry.get("type"), geometry.get("coordinates") or []
    if t == "Polygon":
        return _in_polygon(c, x, y)
    if t == "MultiPolygon":
        return any(_in_polygon(p, x, y) for p in c)
    return False


class Grid:
    """Points bucketed by a square cell (degrees); `near(box)` yields the (key, x, y) of every point in a cell the box
    meets, a superset the caller tests with `contains`."""

    def __init__(self, cell: float = 0.002):
        self.cell, self.cells, self.n = cell, {}, 0

    def _c(self, v: float) -> int:
        return math.floor(v / self.cell)

    def add(self, key, x: float, y: float) -> None:
        self.cells.setdefault((self._c(x), self._c(y)), []).append((key, x, y))
        self.n += 1

    def near(self, box):
        xmin, ymin, xmax, ymax = box
        x0, x1, y0, y1 = self._c(xmin), self._c(xmax), self._c(ymin), self._c(ymax)
        if (x1 - x0 + 1) * (y1 - y0 + 1) > len(self.cells):
            # a box wider than the points are many (a national park): walk the filled cells instead
            cells = (v for (cx, cy), v in self.cells.items() if x0 <= cx <= x1 and y0 <= cy <= y1)
        else:
            cells = (self.cells.get((cx, cy), ()) for cx in range(x0, x1 + 1) for cy in range(y0, y1 + 1))
        for bucket in cells:
            for p in bucket:
                if xmin <= p[1] <= xmax and ymin <= p[2] <= ymax:
                    yield p

    def within(self, geometry, box=None):
        """The keys of the points strictly inside the geometry."""
        box = box or bbox(geometry)
        if not box:
            return []
        return [k for k, x, y in self.near(box) if contains(geometry, x, y)]

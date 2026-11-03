"""The reading (step 8.3): each landed WFS page of a source's newest finished pull, read into rows. Deterministic, no
model: a page is GeoJSON, a row is one feature's properties as LINZ states them, every value kept as given; the geometry
is kept only of a source read whole (capture.ASKED_WHOLE: the addresses and every catalogue source), into the lane's
private schema. Profile `linz-wfs-page` v3.

    read_page(body, source, document, version) -> (rows, set_aside)
    read_whole(body, source, document, version) -> (rows, set_aside)    a catalogue source: WHOLE_FIELDS a row

An owner's name is built from the row as LINZ prints it: a corporate owner's `corporate_name`; an individual's
`prime_other_names prime_surname` and its suffix. Never an address in a public source's rows (capture.NEVER); the
private sources' rows (a title on a unit of property, an address on it, the address as LINZ gives it) go to the lane's
private schema only.
"""
import json

from registers.linz import geo

PROFILE = "linz-wfs-page"
READER = "registers.linz.read 1"
#: what a page read whole yields for each row, beside its typed columns (a whole source has no typed columns): the row's
#: own id (the service's feature id, or its sort key), every attribute as LINZ gives it (`props`, JSON), and its geometry
#: as GeoJSON text with its type and box (longitude and latitude, NZGD2000)
WHOLE_FIELDS = ("fid", "props", "geom_type", "geom", "west", "south", "east", "north")

#: source → its key column and the columns kept (the order of the lane's table)
KEEP = {
    "owners": ("id", ("id", "tte_id", "title_no", "status", "land_district", "estate_share", "owner_type",
                      "prime_surname", "prime_other_names", "name_suffix", "corporate_name")),
    "titles": ("id", ("id", "title_no", "status", "type", "land_district", "issue_date", "guarantee_status",
                      "estate_description", "number_owners", "spatial_extents_shared")),
    "place_names": ("name_id", ("name_id", "feat_id", "name", "status", "feat_type", "maori_name", "land_district",
                                "territorial_authority", "region", "crd_latitude", "crd_longitude", "info_origin",
                                "info_description", "treaty_legislation", "nzgb_ref")),
    # the private sources (capture.PRIVATE_SOURCES): read into the lane's private schema only, never published
    "property_titles": ("id", ("id", "title_no", "unit_of_property_id")),
    "property_addresses": ("id", ("id", "unit_of_property_id", "address_id")),
    "addresses": ("address_id", ("address_id", "full_address", "address_lifecycle")),
}
#: the columns each source cannot do without (a private source's row joins on two)
REQUIRED = {"owners": ("title_no",), "titles": ("title_no",), "place_names": ("name",),
            "property_titles": ("title_no", "unit_of_property_id"), "property_addresses": ("unit_of_property_id", "address_id"),
            "addresses": ("full_address",)}


def owner_name(r: dict):
    """The owner as LINZ prints the row: the corporate name, or the other names then the surname, then a suffix."""
    corp = (r.get("corporate_name") or "").strip()
    if corp:
        return corp
    parts = [(r.get("prime_other_names") or "").strip(), (r.get("prime_surname") or "").strip(), (r.get("name_suffix") or "").strip()]
    name = " ".join(p for p in parts if p)
    return name or None


def owner_kind(r: dict) -> str:
    t = (r.get("owner_type") or "").strip().lower()
    if t.startswith("corp"):
        return "corporate"
    if t.startswith("indiv"):
        return "individual"
    return t or "unstated"


def recognises(body: bytes, source: str) -> bool:
    """The profile's recognition: a GeoJSON FeatureCollection whose features (if any) carry the source's key and its
    required column; anything else (an error page, an exception report, another source's page) is not this shape."""
    try:
        doc = json.loads(body)
    except (ValueError, UnicodeDecodeError):
        return False
    if not isinstance(doc, dict) or doc.get("type") != "FeatureCollection" or not isinstance(doc.get("features"), list):
        return False
    key_col = KEEP[source][0]
    return all(isinstance(f, dict) and all(c in (f.get("properties") or {}) for c in (key_col,) + REQUIRED[source])
               for f in doc["features"][:5])


def whole_of(feature: dict, sort_cols: tuple = ()) -> dict:
    """A feature read whole: its id (the one sort column's value where there is one, else the service's feature id's
    number), every attribute as JSON, and its geometry with its type and box; None for a row with no id at all."""
    p = feature.get("properties") or {}
    fid = None
    if len(sort_cols) == 1 and p.get(sort_cols[0]) not in (None, ""):
        fid = str(p[sort_cols[0]])
    elif feature.get("id") not in (None, ""):
        fid = str(feature["id"]).rsplit(".", 1)[-1]
    g = feature.get("geometry")
    box = geo.bbox(g) if g else None
    return {"fid": fid, "props": json.dumps(p, ensure_ascii=False, sort_keys=True),
            "geom_type": (g or {}).get("type"), "geom": json.dumps(g, separators=(",", ":")) if g else None,
            "west": box[0] if box else None, "south": box[1] if box else None,
            "east": box[2] if box else None, "north": box[3] if box else None}


def _feature_collection(body: bytes):
    try:
        doc = json.loads(body)
    except (ValueError, UnicodeDecodeError):
        return None
    if not isinstance(doc, dict) or doc.get("type") != "FeatureCollection" or not isinstance(doc.get("features"), list):
        return None
    return doc


def read_whole(body: bytes, source: str, document: str, version: int, start_index: int = 0, sort_cols: tuple = ()) -> tuple:
    """A page of a catalogue source read whole: one row a feature (WHOLE_FIELDS), keyed linz/<source>/<fid>; a feature
    with no id is set aside; a page that is not a FeatureCollection is set aside whole."""
    doc = _feature_collection(body)
    if doc is None:
        return [], [{"document": document, "place": f"from row {start_index + 1}", "stage": "recognise",
                     "reason": f"not a WFS page of {source}"}]
    rows, aside = [], []
    for i, f in enumerate(doc["features"]):
        place = f"row {start_index + i + 1}"
        w = whole_of(f if isinstance(f, dict) else {}, sort_cols)
        if w["fid"] is None:
            aside.append({"document": document, "place": place, "stage": "read", "reason": "no id"})
            continue
        w.update({"key": f"linz/{source}/{w['fid']}", "document": document, "page": 1, "place": place,
                  "read_from": "text", "reader": READER, "profile": PROFILE, "profile_version": version})
        rows.append(w)
    return rows, aside


def read_page(body: bytes, source: str, document: str, version: int, start_index: int = 0) -> tuple:
    from registers.linz import capture
    if source not in KEEP:
        return read_whole(body, source, document, version, start_index, capture.WHOLE[source][1])
    key_col, cols = KEEP[source]
    rows, aside = [], []
    if not recognises(body, source):
        return [], [{"document": document, "place": f"from row {start_index + 1}", "stage": "recognise",
                     "reason": f"not a WFS page of {source}"}]
    feats = json.loads(body).get("features") or []
    for i, f in enumerate(feats):
        p = f.get("properties") or {}
        place = f"row {start_index + i + 1}"
        lacking = [c for c in REQUIRED[source] + (key_col,) if p.get(c) in (None, "")]
        if lacking:
            aside.append({"document": document, "place": place, "stage": "read", "reason": f"no {lacking[0]}"})
            continue
        row = {c: p.get(c) for c in cols}
        if source in capture.ASKED_WHOLE:
            # asked whole: every attribute and the point beside the typed columns
            row.update({k: v for k, v in whole_of(f, (key_col,)).items() if k != "fid"})
        row["key"] = f"linz/{source}/{p[key_col]}"
        if source == "owners":
            row["name"] = owner_name(p)
            row["kind"] = owner_kind(p)
            row["title_key"] = f"linz/titles/{p['title_no']}"
        if source == "titles":
            row["key"] = f"linz/titles/{p['title_no']}"
        row.update({"document": document, "page": 1, "place": place, "read_from": "text", "reader": READER,
                    "profile": PROFILE, "profile_version": version})
        rows.append(row)
    return rows, aside

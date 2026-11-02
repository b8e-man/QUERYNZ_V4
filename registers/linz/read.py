"""The reading (step 8.3): each landed WFS page of a source's newest finished pull, read into rows. Deterministic, no
model: a page is GeoJSON, a row is one feature's properties as LINZ states them, every value kept as given; the geometry
is never kept (capture never asks for it). Profile `linz-wfs-page` v1.

    read_page(body, source, document, version) -> (rows, set_aside)

An owner's name is built from the row as LINZ prints it: a corporate owner's `corporate_name`; an individual's
`prime_other_names prime_surname` and its suffix. Never an address: no column read carries one (capture.NEVER).
"""
import json

PROFILE = "linz-wfs-page"
READER = "registers.linz.read 1"

#: source → its key column and the columns kept (the order of the lane's table)
KEEP = {
    "owners": ("id", ("id", "tte_id", "title_no", "status", "land_district", "estate_share", "owner_type",
                      "prime_surname", "prime_other_names", "name_suffix", "corporate_name")),
    "titles": ("id", ("id", "title_no", "status", "type", "land_district", "issue_date", "guarantee_status",
                      "estate_description", "number_owners", "spatial_extents_shared")),
    "place_names": ("name_id", ("name_id", "feat_id", "name", "status", "feat_type", "maori_name", "land_district",
                                "territorial_authority", "region", "crd_latitude", "crd_longitude", "info_origin",
                                "info_description", "treaty_legislation", "nzgb_ref")),
}
#: the column each source cannot do without
REQUIRED = {"owners": "title_no", "titles": "title_no", "place_names": "name"}


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
    return all(isinstance(f, dict) and key_col in (f.get("properties") or {}) and REQUIRED[source] in (f.get("properties") or {})
               for f in doc["features"][:5])


def read_page(body: bytes, source: str, document: str, version: int, start_index: int = 0) -> tuple:
    key_col, cols = KEEP[source]
    rows, aside = [], []
    if not recognises(body, source):
        return [], [{"document": document, "place": f"from row {start_index + 1}", "stage": "recognise",
                     "reason": f"not a WFS page of {source}"}]
    feats = json.loads(body).get("features") or []
    for i, f in enumerate(feats):
        p = f.get("properties") or {}
        place = f"row {start_index + i + 1}"
        if p.get(REQUIRED[source]) in (None, "") or p.get(key_col) in (None, ""):
            aside.append({"document": document, "place": place, "stage": "read",
                          "reason": f"no {REQUIRED[source] if p.get(REQUIRED[source]) in (None, '') else key_col}"})
            continue
        row = {c: p.get(c) for c in cols}
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

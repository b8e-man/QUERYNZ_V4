"""Hand-made records in the shape OpenLaw NZ's interface returns to the lane's
query (its schema, read by introspection on 21 October 2026). Every name,
number and text is invented; no record was copied from the interface (its
terms bar permanent copies, API terms 3.6(a))."""
import json


def record(cid="hc_test_2024NZHC1001.pdf", *, name="Alpha Widgets Limited v Beta Holdings Limited",
           date="2024-05-02", filing="CIV-2023-404-000123", location="Auckland", court=("NZHC", "High Court"),
           citations=("[2024] NZHC 1001",), parties=(("PLAINTIFF", ["ALPHA WIDGETS LIMITED"]),
                                                     ("DEFENDANT", ["BETA HOLDINGS LIMITED"])),
           cited=(("ca_test_2019NZCA77.pdf", 2),), statutes=(("companies-act-1993", "s 131", 3, 90),),
           text="IN THE HIGH COURT OF NEW ZEALAND\nAUCKLAND REGISTRY\n\nJUDGMENT OF EXAMPLE J\n\n[1] Invented.",
           **extra):
    r = {
        "id": cid, "caseName": name, "caseDate": date, "courtFilingNumber": filing, "location": location,
        "isValid": True, "lastModified": "2024-06-01", "parsersVersion": "0.9.0", "courtId": court[0].lower(),
        "pdfId": cid, "caseText": text,
        "court": {"id": court[0].lower(), "name": court[1], "acronyms": [court[0]]},
        "pdf": {"pdfId": cid, "pdfUrl": f"https://example.invalid/pdf/{cid}", "pdfProvider": "jdo",
                "fetchDate": "2024-05-03"},
        "caseCitations": [{"id": f"cit-{i}", "citation": c, "year": 2024} for i, c in enumerate(citations)],
        "casesCitedsByCaseOrigin": [{"caseCited": c, "citationCount": n} for c, n in cited],
        "legislationToCases": [{"legislationId": lid, "section": sec, "count": n, "extractionConfidence": conf,
                                "legislation": {"id": lid, "title": "Companies Act 1993", "year": "1993"}}
                               for lid, sec, n, conf in statutes],
        "experimentalPartyAndRepresentatives": [{"partyType": t, "names": list(ns)} for t, ns in parties],
    }
    r.update(extra)
    return r


SUPPRESSED_TEXT = ("NOTE: ORDER PROHIBITING PUBLICATION OF NAME, ADDRESS, OCCUPATION OR IDENTIFYING PARTICULARS OF "
                   "THE DEFENDANT PURSUANT TO S 200 OF THE CRIMINAL PROCEDURE ACT 2011.\n\n"
                   "IN THE HIGH COURT OF NEW ZEALAND\nWELLINGTON REGISTRY\n\n[1] Invented.")
CAPTION_TEXT = ("IN THE COURT OF APPEAL OF NEW ZEALAND\n\nCA123/2023\n[2024] NZCA 55\n\nBETWEEN\n\n"
                "GAMMA TRUSTEE LIMITED\nFirst Appellant\n\nDELTA EXAMPLE\nSecond Appellant\n\nAND\n\n"
                "EPSILON COUNCIL\nRespondent\n\nHearing:\n1 March 2024\n\n[1] Invented.")
CRIMINAL_TEXT = "IN THE HIGH COURT OF NEW ZEALAND\nNAPIER REGISTRY\n\nTHE KING\nv\nZETA EXAMPLE\n\nHearing:\n2 May 2024\n"


def clean():
    return record()


def suppressed():
    return record("hc_test_2024NZHC2002.pdf", name="R v Eta Example", citations=("[2024] NZHC 2002",),
                  parties=(("RESPONDENT", ["R"]), ("APPELLANT", ["ETA EXAMPLE"])), text=SUPPRESSED_TEXT,
                  location="Wellington", cited=(), statutes=())


def anonymised():
    return record("ca_test_2024NZCA3003.pdf", name="W v Theta Example", citations=("[2024] NZCA 3003",),
                  court=("NZCA", "Court of Appeal"), parties=(("APPELLANT", ["W"]), ("RESPONDENT", ["THETA EXAMPLE"])),
                  text="IN THE COURT OF APPEAL OF NEW ZEALAND\n\n[1] Invented.", location=None, cited=(), statutes=())


def caption_only():
    return record("ca_test_2024NZCA55.pdf", name="Gamma Trustee Ltd v Epsilon Council", citations=("[2024] NZCA 55",),
                  court=("NZCA", "Court of Appeal"), parties=(), text=CAPTION_TEXT, location=None,
                  cited=(("hc_test_2024NZHC1001.pdf", 1), ("hc_test_2024NZHC1001.pdf", 1), ("", 1)),
                  statutes=(("rma-1991", "s 104", 1, 80), ("rma-1991", "s 104", 1, 80)))


def criminal():
    return record("hc_test_2024NZHC4004.pdf", name="R v Zeta Example", citations=("CRI-2023-041-000999", "[2024] NZHC 4004"),
                  parties=(), text=CRIMINAL_TEXT, location=None, cited=(), statutes=())


def page(*records) -> bytes:
    return json.dumps({"data": {"cases": list(records)}}, ensure_ascii=False).encode()

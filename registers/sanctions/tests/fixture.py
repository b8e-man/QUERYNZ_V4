"""Hand-made documents in each list's shape. Every name is invented."""
import io
import zipfile
from xml.sax.saxutils import escape


def col(n: int) -> str:
    s = ""
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


def xlsx(sheets: list) -> bytes:
    """sheets: [(name, {row: {col: value}})] → a minimal workbook with inline strings."""
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w") as z:
        z.writestr("[Content_Types].xml", '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"/>')
        rels = "".join(f'<Relationship Id="r{i}" Type="worksheet" Target="worksheets/sheet{i}.xml"/>' for i in range(1, len(sheets) + 1))
        z.writestr("xl/_rels/workbook.xml.rels", f'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">{rels}</Relationships>')
        sh = "".join(f'<sheet name="{escape(n)}" sheetId="{i}" r:id="r{i}"/>' for i, (n, _) in enumerate(sheets, 1))
        z.writestr("xl/workbook.xml", '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
                   'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
                   f"<sheets>{sh}</sheets></workbook>")
        for i, (_, rows) in enumerate(sheets, 1):
            body = ""
            for r in sorted(rows):
                cells = "".join(
                    (f'<c r="{col(c)}{r}"><v>{v}</v></c>' if isinstance(v, (int, float)) else
                     f'<c r="{col(c)}{r}" t="inlineStr"><is><t>{escape(str(v))}</t></is></c>')
                    for c, v in sorted(rows[r].items()))
                body += f'<row r="{r}">{cells}</row>'
            z.writestr(f"xl/worksheets/sheet{i}.xml", '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                       f"<sheetData>{body}</sheetData></worksheet>")
    return b.getvalue()


UN_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<CONSOLIDATED_LIST dateGenerated="2026-10-20T23:00:05.952Z">
<INDIVIDUALS>
<INDIVIDUAL><DATAID>1</DATAID><FIRST_NAME>INVENTED</FIRST_NAME><SECOND_NAME>PERSON</SECOND_NAME><UN_LIST_TYPE>DPRK</UN_LIST_TYPE>
<REFERENCE_NUMBER>KPi.901</REFERENCE_NUMBER><LISTED_ON>2016-03-02</LISTED_ON><COMMENTS1>Lives at 9 Secret Road, Exampleville.</COMMENTS1>
<TITLE><VALUE>Dr</VALUE></TITLE><DESIGNATION><VALUE>Minister of Examples</VALUE></DESIGNATION>
<NATIONALITY><VALUE>Exampleland</VALUE></NATIONALITY><LAST_DAY_UPDATED><VALUE>2017-01-01</VALUE><VALUE>2020-05-06</VALUE></LAST_DAY_UPDATED>
<INDIVIDUAL_ALIAS><QUALITY>Good</QUALITY><ALIAS_NAME>Invented Persson</ALIAS_NAME></INDIVIDUAL_ALIAS>
<INDIVIDUAL_ALIAS><QUALITY>Low</QUALITY><ALIAS_NAME>Invented Persson</ALIAS_NAME></INDIVIDUAL_ALIAS>
<INDIVIDUAL_ADDRESS><STREET>9 Secret Road</STREET><CITY>Exampleville</CITY><COUNTRY>Exampleland</COUNTRY></INDIVIDUAL_ADDRESS>
<INDIVIDUAL_DATE_OF_BIRTH><TYPE_OF_DATE>EXACT</TYPE_OF_DATE><DATE>1960-02-03</DATE></INDIVIDUAL_DATE_OF_BIRTH>
<INDIVIDUAL_DATE_OF_BIRTH><TYPE_OF_DATE>BETWEEN</TYPE_OF_DATE><FROM_YEAR>1958</FROM_YEAR><TO_YEAR>1961</TO_YEAR></INDIVIDUAL_DATE_OF_BIRTH>
<INDIVIDUAL_PLACE_OF_BIRTH><CITY>Birthtown</CITY><COUNTRY>Otherland</COUNTRY></INDIVIDUAL_PLACE_OF_BIRTH>
<INDIVIDUAL_DOCUMENT><TYPE_OF_DOCUMENT>Passport</TYPE_OF_DOCUMENT><NUMBER>X1234567</NUMBER></INDIVIDUAL_DOCUMENT>
</INDIVIDUAL>
<INDIVIDUAL><DATAID>2</DATAID><FIRST_NAME>NO</FIRST_NAME><SECOND_NAME>REFERENCE</SECOND_NAME><UN_LIST_TYPE>Iraq</UN_LIST_TYPE>
<LISTED_ON>2003-01-01</LISTED_ON></INDIVIDUAL>
</INDIVIDUALS>
<ENTITIES>
<ENTITY><DATAID>3</DATAID><FIRST_NAME>INVENTED TRADING CO</FIRST_NAME><UN_LIST_TYPE>Iran</UN_LIST_TYPE><REFERENCE_NUMBER>IRe.901</REFERENCE_NUMBER>
<LISTED_ON>2008-03-03</LISTED_ON><ENTITY_ALIAS><QUALITY>a.k.a.</QUALITY><ALIAS_NAME>ITC</ALIAS_NAME></ENTITY_ALIAS>
<ENTITY_ADDRESS><STREET>1 Company Lane</STREET><CITY>Port Example</CITY><COUNTRY>Exampleland</COUNTRY></ENTITY_ADDRESS></ENTITY>
</ENTITIES>
</CONSOLIDATED_LIST>"""

_IND_HEAD = {1: "ID", 2: "LastName", 3: "Name_1", 4: "Name_2", 5: "Name_3", 6: "Name_4", 7: "Title", 8: "POB_1",
             9: "POB_1_Country", 18: "DOB_1", 19: "DOB_2", 27: "Nationality_1", 30: "Associated with", 31: "Passport_1",
             44: "Address", 49: "NZ_designation_date", 50: "Entry Date 2", 51: "Sanctions_List_Permanent_Reference_Numbe"}
_ORG_HEAD = {1: "ID", 2: "Name", 3: "Address_1", 19: "Other", 20: "Associated to", 21: "NZ_Designation_Date",
             22: "Entry Date 2", 23: "Sanctions_List_Permanent_Reference_Numbe"}
_REV_HEAD = {1: "ID ", 2: "LastName", 3: "Name_1", 15: "Nationality_1", 17: "Associated with", 18: "Address",
             19: "NZ_designation_date", 20: "Entry_date", 21: "NZ_revocation_date", 22: "Sanctions_List_Permanent_"}
_1373_HEAD = {1: "NZ UNSCR 1373 ID CODE", 2: "NAME", 3: "ABBREV", 4: "COUNTRY", 5: "DATE OF ORIGINAL DESIGNATION",
              6: "DATE/S DESIGNATION RENEWED", 7: " DATE OF DESIGNATION EXPIRATION UNLESS RENEWED OR REVOKED PRIOR"}


def police_xlsx(expired_dup: bool = False) -> bytes:
    ind = {1: _IND_HEAD,
           2: {1: "2", 2: "EXAMPLE", 3: "Invented", 7: "Mullah", 9: "Exampleland", 18: "1955-1958", 19: 26328,
               27: "Examplish", 30: "1", 31: "Exampleland P0000001", 44: "Example Street, Exampleton",
               49: 37546, 50: "23/06/2004\n\nAmended 10/03/2026 SCA/14/26", 51: "TAi.902"},
           3: {1: "2.0099999999999998", 2: "EXAMPEL", 3: "Invented", 51: "TAi.902"},
           4: {1: "3. 00", 2: "SECOND", 3: "Made", 4: "Up", 49: 38000, 51: "QDi.903"},
           5: {1: "4", 2: "", 3: ""}}
    org = {1: _ORG_HEAD,
           2: {1: "2", 2: "Invented Group", 3: "Exampleland", 20: "2", 21: 37546, 22: "9/09/2004", 23: "QDe.901"},
           3: {1: "2.01", 2: "Al Invented", 23: "QDe.901"}}
    rev = {1: _REV_HEAD, 2: {1: "INDIVIDUALS REVOKED BY UN/NZ"},
           3: {1: "123", 2: "GONE", 3: "Formerly", 17: "1", 19: 37546, 20: 38161, 21: 38958},
           5: {1: "ORGANISATIONS REVOKED BY UN/NZ"},
           6: {1: "1", 2: "Defunct Invented Bank", 3: "1 Bank Street", 17: "2", 19: 37546, 20: 38239, 21: 39400}}
    n1373 = {1: _1373_HEAD,
             3: {1: "1", 2: "Invented Front", 3: "IF", 4: "Exampleland", 5: 40219, 6: "11/02/2013\n02/02/2016", 7: 46711},
             4: {1: "1.01", 2: "Front of Invention", 3: "IF", 4: "Exampleland", 5: 40219, 7: 46711},
             5: {1: "23", 2: "Imaginary Person Name, DOB 27 October 1990", 3: "IPN", 4: "Exampleland", 5: 44070,
                 6: "01/08/2023", 7: 46960}}
    exp = {1: {**_1373_HEAD, 8: "ADDITIONAL INFORMATION"},
           3: {1: "18", 2: "Expired Invented", 3: "EI", 4: "Otherland", 5: 41702, 6: "N/A", 7: 42798}}
    if expired_dup:
        exp[4] = {1: "1", 2: "Invented Front again", 4: "Exampleland", 5: 40219, 7: 42798}
    return xlsx([("Information", {17: {2: "notes"}}), ("Individuals", ind), ("Organisations", org), ("Revocations", rev),
                 ("UNSCR 1373", n1373), ("UNSCR 1373 Expirations", exp)])


PAGE_1373 = b"<p>New Zealand currently has 2 non-UN listed entities designated in support of UN Security Council Resolution 1373.</p>"

_MFAT_HEAD = {1: "Unique Identifier", 2: "Type", 3: "First name", 4: "Middle name(s)", 5: "Last name", 6: "Title",
              7: "Alias/Alternate Spellings", 8: "Address", 9: "DOB", 10: "Citizenship", 11: "Passport Number",
              12: "Date of Sanction", 13: "Date of Additional Sanction", 14: "Sanction Status",
              15: "General Rationale for Sanction", 16: "Asset Freeze", 17: "Travel Ban"}


def mfat_xlsx(total: int = 3) -> bytes:
    rows = {1: {1: "Russia Sanctions Register"}, 3: _MFAT_HEAD,
            4: {1: "RUS-0001", 2: "Individual", 3: "Ivan", 4: "Inventovich", 5: "Examplov", 7: "Ivan Examplof; I. Examplov",
                8: "1 Hidden Street, Moscow", 9: 22000, 10: "Russia", 11: "000000", 12: "03/03/2022", 14: "Sanctioned",
                15: "A rationale", 16: "Yes", 17: "Yes"},
            5: {1: "RUS-0002", 2: "Entity", 5: "Invented Defence JSC", 12: "18/03/2022", 14: "Sanctioned", 16: "Yes"},
            6: {1: "RUS-0002", 2: "Bank", 5: "Invented Bank PJSC", 12: "18/03/2022", 14: "Sanctioned", 16: "Yes"},
            7: {1: "RUS-0003", 2: "Asset", 5: "A Ship"},
            8: {1: "RUS-0004", 2: "Spaceship", 5: "Odd"},
            9: {2: "Total", 3: total}}
    return xlsx([("Register", rows)])

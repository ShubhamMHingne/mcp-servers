# holiday_mcp_server.py
import datetime as dt
import hashlib
import json
import re
from typing import Any, Dict, List, Optional

import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel
from fastmcp import FastMCP

# ----- Config -----
SOURCE_URL = "https://mmrda.maharashtra.gov.in/public-holidays"
USER_AGENT = "HolidayMCP/1.0"
HTTP_TIMEOUT = 20

# ----- Data model -----
class Holiday(BaseModel):
    name: str
    date: str  # ISO YYYY-MM-DD
    weekday: Optional[str] = None
    source_url: str
    source_hash: str

# ----- In-memory cache -----
# { year: { "holidays": List[Holiday], "last_fetch": iso str, "checksum": str } }
_cache: Dict[int, Dict[str, Any]] = {}

def _iso_date_from_text(text: str, year_hint: Optional[int]) -> Optional[str]:
    t = text.strip()
    candidates = [
        ("%d %b %Y", t),
        ("%d %B %Y", t),
        ("%d-%m-%Y", t),
        ("%d/%m/%Y", t),
        ("%Y-%m-%d", t),
        ("%B %d, %Y", t),
        ("%b %d, %Y", t),
        ("%d.%m.%Y", t),
    ]
    if year_hint and re.match(r"^\s*\d{1,2}\s+[A-Za-z]{3,}\s*$", t):
        candidates.extend([
            ("%d %b %Y", f"{t} {year_hint}"),
            ("%d %B %Y", f"{t} {year_hint}"),
        ])
    if year_hint and re.match(r"^\s*\d{1,2}[-/]\d{1,2}\s*$", t):
        candidates.extend([
            ("%d-%m-%Y", f"{t}-{year_hint}"),
            ("%d/%m/%Y", f"{t}/{year_hint}"),
        ])
    for fmt, s in candidates:
        try:
            d = dt.datetime.strptime(s, fmt).date()
            return d.isoformat()
        except Exception:
            pass
    m = re.search(r"(\d{1,2})\s+([A-Za-z]{3,})\s+(\d{4})", t)
    if m:
        try:
            d = dt.datetime.strptime(m.group(0), "%d %B %Y").date()
            return d.isoformat()
        except Exception:
            try:
                d = dt.datetime.strptime(m.group(0), "%d %b %Y").date()
                return d.isoformat()
            except Exception:
                pass
    return None

def _weekday_name(iso_date: str) -> str:
    y, m, d = map(int, iso_date.split("-"))
    return dt.date(y, m, d).strftime("%A")

def _hash_item(name: str, date_iso: str) -> str:
    h = hashlib.sha256()
    h.update((name.strip().lower() + "|" + date_iso).encode("utf-8"))
    return h.hexdigest()[:16]

def _fetch_and_parse(year: int) -> List[Holiday]:
    headers = {"User-Agent": USER_AGENT}
    resp = requests.get(SOURCE_URL, headers=headers, timeout=HTTP_TIMEOUT)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    tables = soup.find_all("table")
    holidays: List[Holiday] = []

    def normalize_name(s: str) -> str:
        return re.sub(r"\s+", " ", s.strip())

    for table in tables:
        headers_row = [th.get_text(strip=True).lower() for th in table.find_all("th")]
        if not headers_row:
            first_row = table.find("tr")
            if first_row:
                headers_row = [td.get_text(strip=True).lower() for td in first_row.find_all("td")]
        if not headers_row:
            continue
        has_holiday = any("holiday" in h or "occasion" in h for h in headers_row)
        has_date = any("date" in h for h in headers_row)
        if not (has_holiday and has_date):
            continue

        rows = table.find_all("tr")
        for tr in rows:
            cells = tr.find_all(["td", "th"])
            if not cells or any(c.name == "th" for c in cells):
                continue
            texts = [c.get_text(" ", strip=True) for c in cells]
            if len(texts) < 2:
                continue

            name_text = None
            date_text = None
            weekday_text = None

            if len(headers_row) >= 2:
                def find_idx(keys):
                    for i, h in enumerate(headers_row):
                        if any(k in h for k in keys):
                            return i
                    return None

                idx_name = find_idx(["holiday", "occasion", "festival"])
                idx_date = find_idx(["date"])
                idx_day = find_idx(["day", "weekday"])
                try:
                    if idx_name is not None and idx_name < len(texts):
                        name_text = texts[idx_name]
                    if idx_date is not None and idx_date < len(texts):
                        date_text = texts[idx_date]
                    if idx_day is not None and idx_day < len(texts):
                        weekday_text = texts[idx_day]
                except Exception:
                    pass

            if not name_text and len(texts) >= 1:
                name_text = texts[0]
            if not date_text and len(texts) >= 2:
                date_text = texts[1]
            if not weekday_text and len(texts) >= 3:
                weekday_text = texts[2]

            if not name_text or not date_text:
                continue

            name = normalize_name(name_text)
            iso = _iso_date_from_text(date_text, year_hint=year)
            if not iso:
                continue
            if int(iso[:4]) != year:
                continue

            weekday = (weekday_text.strip() if weekday_text else _weekday_name(iso))
            h = Holiday(
                name=name,
                date=iso,
                weekday=weekday,
                source_url=SOURCE_URL,
                source_hash=_hash_item(name, iso),
            )
            holidays.append(h)

    seen = set()
    unique: List[Holiday] = []
    for h in holidays:
        key = (h.date, h.name.lower())
        if key in seen:
            continue
        seen.add(key)
        unique.append(h)
    unique.sort(key=lambda x: x.date)
    return unique

def _ensure_year_loaded(year: int, force_refresh: bool = False) -> Dict[str, Any]:
    entry = _cache.get(year)
    if entry and not force_refresh:
        return entry
    holidays = _fetch_and_parse(year)
    checksum = hashlib.sha256(
        json.dumps([h.model_dump() for h in holidays], sort_keys=True).encode("utf-8")
    ).hexdigest()
    entry = {
        "holidays": holidays,
        "last_fetch": dt.datetime.utcnow().isoformat() + "Z",
        "checksum": checksum,
    }
    _cache[year] = entry
    return entry

def _parse_date(s: str) -> dt.date:
    return dt.date.fromisoformat(s)

def _filter_holidays(
    hols: List[Holiday],
    query: Optional[str] = None,
    month: Optional[int] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
) -> List[Holiday]:
    res = hols
    if query:
        q = query.strip().lower()
        res = [h for h in res if q in h.name.lower()]
    if month:
        res = [h for h in res if int(h.date[5:7]) == int(month)]
    if start:
        ds = _parse_date(start)
        res = [h for h in res if _parse_date(h.date) >= ds]
    if end:
        de = _parse_date(end)
        res = [h for h in res if _parse_date(h.date) <= de]
    return res

def _to_ics(hols: List[Holiday]) -> str:
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//HolidayMCP//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
    ]
    for h in hols:
        uid = f"{h.source_hash}@holidaymcp"
        dtstamp = dt.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        y, m, d = h.date.split("-")
        dtstart = f"{y}{m}{d}"
        lines.extend([
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{dtstamp}",
            f"SUMMARY:{h.name}",
            f"DTSTART;VALUE=DATE:{dtstart}",
            f"DESCRIPTION:Holiday from {h.source_url}",
            "TRANSP:TRANSPARENT",
            "END:VEVENT",
        ])
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"

# ----- MCP server -----
mcp = FastMCP(name="Holiday Calendar MCP")

@mcp.tool
def fetch_holidays(year: Optional[int] = None, force_refresh: bool = False) -> dict:
    """
    Fetch and cache holidays from the MMRDA public holidays page.
    Returns: { year, count, last_fetch, checksum }
    """
    if year is None:
        year = dt.date.today().year
    entry = _ensure_year_loaded(year, force_refresh=force_refresh)
    return {
        "year": year,
        "count": len(entry["holidays"]),
        "last_fetch": entry["last_fetch"],
        "checksum": entry["checksum"],
    }

@mcp.tool
def is_holiday(date: str) -> dict:
    """
    Check if the given ISO date (YYYY-MM-DD) is a holiday.
    Returns: { is_holiday: bool, holiday?: Holiday }
    """
    d = _parse_date(date)
    entry = _ensure_year_loaded(d.year, force_refresh=False)
    for h in entry["holidays"]:
        if h.date == date:
            return {"is_holiday": True, "holiday": h.model_dump()}
    return {"is_holiday": False}

@mcp.tool
def find_holidays(
    query: Optional[str] = None,
    month: Optional[int] = None,
    range_start: Optional[str] = None,
    range_end: Optional[str] = None,
    year: Optional[int] = None,
) -> List[dict]:
    """
    Search holidays by name (query), month (1-12), and/or date range (YYYY-MM-DD).
    Returns a list of Holiday objects.
    """
    if range_start:
        ys = _parse_date(range_start).year
    else:
        ys = None
    if range_end:
        ye = _parse_date(range_end).year
    else:
        ye = None
    today_year = dt.date.today().year
    if year is None:
        if ys and ye and ys == ye:
            year = ys
        elif ys and not ye:
            year = ys
        elif ye and not ys:
            year = ye
        else:
            year = today_year
    entry = _ensure_year_loaded(year, force_refresh=False)
    filtered = _filter_holidays(entry["holidays"], query=query, month=month, start=range_start, end=range_end)
    return [h.model_dump() for h in filtered]

@mcp.tool
def export(format: str = "ics", year: Optional[int] = None) -> dict:
    """
    Export the cached holidays for a year as ICS or JSON.
    Returns: { format, year, content }
    """
    if year is None:
        year = dt.date.today().year
    entry = _ensure_year_loaded(year, force_refresh=False)
    hols = entry["holidays"]
    if format.lower() == "ics":
        content = _to_ics(hols)
        return {"format": "ics", "year": year, "content": content}
    elif format.lower() == "json":
        content = json.dumps([h.model_dump() for h in hols], indent=2, ensure_ascii=False)
        return {"format": "json", "year": year, "content": content}
    else:
        raise ValueError("Unsupported format. Use 'ics' or 'json'.")

if __name__ == "__main__":
    mcp.run(transport="stdio")

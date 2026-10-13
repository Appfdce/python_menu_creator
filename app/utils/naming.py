"""Helpers to build the Drive file name for proposals.

The proposal file name follows the pattern::

    {event_date}_{status}_{event_name}.docx

e.g. ``2026-10-13_Initial_Essilor_Luxottica_Lunch.docx``.

``event_date`` is the event start date in ISO format, ``status`` is the
AppSheet proposal status (some of them abbreviated) and ``event_name`` is the
sanitized event name. The exact same string is uploaded to Drive and stored in
the ``file_name`` column of the ``BDProposal History`` table.
"""
import logging
import re
from datetime import datetime

from app.schemas.estimate_total import to_long_date

logger = logging.getLogger(__name__)

# Status abbreviations. Keys are normalized by removing every non-alphanumeric
# character and lower-casing, so "Approved - Final", "approved_final" and
# "Approved-Final" all resolve to the same key. Any status not present here is
# used verbatim (sanitized) so new AppSheet statuses keep working.
STATUS_ABBREVIATIONS = {
    "approvedfinal": "A-F",
    "completedpaid": "Completed-P",
    "estimated": "Estimate",
}


def _status_lookup_key(status) -> str:
    return re.sub(r"[^a-z0-9]", "", str(status or "").lower())


def abbreviate_status(status) -> str:
    """Returns the abbreviated status used in the file name.

    Known statuses are abbreviated (e.g. ``Approved-Final`` -> ``A-F``).
    Unknown statuses are returned sanitized so future values still work.
    """
    raw = str(status or "").strip()
    if not raw:
        return ""

    abbreviated = STATUS_ABBREVIATIONS.get(_status_lookup_key(raw))
    if abbreviated:
        return abbreviated

    return _sanitize_component(raw)


def _sanitize_component(value, drop_extension: bool = False) -> str:
    """Sanitizes a value so it is safe to use inside a file name."""
    s = str(value or "").strip()
    if not s:
        return ""
    if drop_extension and "." in s:
        s = s.split(".")[0]
    s = s.replace("/", "-").replace("\\", "-")
    s = re.sub(r"\s+", "_", s)
    return s.strip("_")


def event_date_iso(val) -> str:
    """Converts an event date coming from AppSheet to ``YYYY-MM-DD``.

    Handles the US numeric format produced by the schema validator
    (``MM/DD/YYYY``), ISO strings (``YYYY-MM-DD``) and long formats with a
    month name in any order. Returns an empty string when the value cannot be
    parsed (the caller then leaves the date segment empty).
    """
    if not val:
        return ""

    s = " ".join(str(val).split()).strip()
    if not s:
        return ""

    # ISO YYYY-MM-DD
    m = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})$", s)
    if m:
        year, month, day = int(m.group(1)), int(m.group(2)), int(m.group(3))
        try:
            return datetime(year, month, day).strftime("%Y-%m-%d")
        except ValueError:
            pass

    # US MM/DD/YYYY or MM/DD/YY (fall back to DD/MM when the month is invalid)
    m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{2,4})$", s)
    if m:
        first, second, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if year < 100:
            year += 2000
        candidates = [(first, second)] if first <= 12 else [(second, first)]
        for month, day in candidates:
            try:
                return datetime(year, month, day).strftime("%Y-%m-%d")
            except ValueError:
                continue

    # Long formats with a month name (canonicalized first to drop ambiguity).
    long_form = to_long_date(s)
    cleaned = re.sub(r"(\d+)(?:st|nd|rd|th)", r"\1", long_form)
    try:
        return datetime.strptime(cleaned, "%A, %B %d, %Y").strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        pass

    logger.warning(
        "Could not parse event date '%s' for the proposal file name; "
        "using an empty date segment.",
        val,
    )
    return ""


def build_proposal_filename(request, ext: str = ".docx") -> str:
    """Builds the proposal file name: ``{date}_{status}_{event_name}{ext}``."""
    event = request.event

    date_part = event_date_iso(event.date_formatted)
    status_part = abbreviate_status(getattr(event, "status", ""))
    name_part = _sanitize_component(event.name, drop_extension=True) or "Unnamed"

    return f"{date_part}_{status_part}_{name_part}{ext}"

from app.schemas.estimate_total import EstimateTotalRequest
from app.utils.naming import (
    abbreviate_status,
    build_proposal_filename,
    event_date_iso,
)


def _request(event_overrides=None):
    event = {
        "name": "Essilor Luxottica Lunch",
        "date_formatted": "Monday, October 13, 2026",
    }
    if event_overrides:
        event.update(event_overrides)
    return EstimateTotalRequest(
        event_id="TEST-NAMING",
        client={},
        client_representative={},
        event=event,
        financials={},
    )


def test_abbreviate_known_statuses():
    assert abbreviate_status("Initial") == "Initial"
    assert abbreviate_status("Revised") == "Revised"
    assert abbreviate_status("Approved-Final") == "A-F"
    assert abbreviate_status("Completed") == "Completed"
    assert abbreviate_status("Invoiced") == "Invoiced"
    assert abbreviate_status("Completed-Paid") == "Completed-P"
    assert abbreviate_status("Cancelled") == "Cancelled"
    assert abbreviate_status("Estimated") == "Estimate"


def test_abbreviate_status_is_case_and_separator_insensitive():
    assert abbreviate_status("approved - final") == "A-F"
    assert abbreviate_status("APPROVED_FINAL") == "A-F"
    assert abbreviate_status("Completed Paid") == "Completed-P"
    assert abbreviate_status("  estimated  ") == "Estimate"


def test_abbreviate_unknown_status_passes_through_sanitized():
    assert abbreviate_status("On Hold") == "On_Hold"
    assert abbreviate_status("Sent/Review") == "Sent-Review"


def test_abbreviate_empty_status():
    assert abbreviate_status("") == ""
    assert abbreviate_status(None) == ""


def test_event_date_iso_formats():
    # Long format with month name
    assert event_date_iso("Monday, October 13, 2026") == "2026-10-13"
    # US numeric (already normalized by the schema validator)
    assert event_date_iso("10/13/2026") == "2026-10-13"
    # ISO
    assert event_date_iso("2026-10-13") == "2026-10-13"
    # Unparseable -> empty segment
    assert event_date_iso("not a date") == ""
    assert event_date_iso("") == ""


def test_build_proposal_filename_examples():
    assert build_proposal_filename(_request({"status": "Initial"})) == \
        "2026-10-13_Initial_Essilor_Luxottica_Lunch.docx"
    assert build_proposal_filename(_request({"status": "Revised"})) == \
        "2026-10-13_Revised_Essilor_Luxottica_Lunch.docx"
    assert build_proposal_filename(_request({"status": "Approved-Final"})) == \
        "2026-10-13_A-F_Essilor_Luxottica_Lunch.docx"
    assert build_proposal_filename(_request({"status": "Completed"})) == \
        "2026-10-13_Completed_Essilor_Luxottica_Lunch.docx"
    assert build_proposal_filename(_request({"status": "Invoiced"})) == \
        "2026-10-13_Invoiced_Essilor_Luxottica_Lunch.docx"
    assert build_proposal_filename(_request({"status": "Completed-Paid"})) == \
        "2026-10-13_Completed-P_Essilor_Luxottica_Lunch.docx"
    assert build_proposal_filename(_request({"status": "Cancelled"})) == \
        "2026-10-13_Cancelled_Essilor_Luxottica_Lunch.docx"
    assert build_proposal_filename(_request({"status": "Estimated"})) == \
        "2026-10-13_Estimate_Essilor_Luxottica_Lunch.docx"


def test_build_proposal_filename_numeric_date():
    req = _request({"date_formatted": "13/10/2026", "status": "Initial"})
    # DD/MM/YYYY is normalized to MM/DD/YYYY by the schema validator.
    assert build_proposal_filename(req) == "2026-10-13_Initial_Essilor_Luxottica_Lunch.docx"


def test_build_proposal_filename_unparseable_date_leaves_empty_segment():
    req = _request({"date_formatted": "next month", "status": "Initial"})
    assert build_proposal_filename(req) == "_Initial_Essilor_Luxottica_Lunch.docx"


def test_build_proposal_filename_sanitizes_name():
    req = _request({"name": "Boda Lopez / Salon", "status": "Revised"})
    assert build_proposal_filename(req) == "2026-10-13_Revised_Boda_Lopez_-_Salon.docx"

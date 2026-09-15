import pytest
from app.schemas.estimate_total import EventInfo, Meal, LaborService, ExtrasEvent

def test_event_info_date_formatting():
    # Input is DD/MM/YY or DD/MM/YYYY
    # Expectation: formatted to US MM/DD/YY or MM/DD/YYYY
    e = EventInfo(
        date_formatted="13/05/26", 
        end_date_formatted="14/05/2026"
    )
    assert e.date_formatted == "05/13/26"
    assert e.end_date_formatted == "05/14/2026"

def test_meal_date_and_time_formatting():
    # Meal date header reformatting
    # Meal time range spacing
    m = Meal(
        date_header="15/06/26",
        time_range="8:00 AM to9:00 AM"
    )
    assert m.date_header == "06/15/26"
    assert m.time_range == "8:00 AM to 9:00 AM"

def test_meal_time_range_already_correct():
    # If already formatted correctly, don't corrupt it
    m = Meal(time_range="12:00 PM to 1:00 PM")
    assert m.time_range == "12:00 PM to 1:00 PM"

def test_labor_and_extras_date_formatting():
    ls = LaborService(date_header="20/07/2026")
    ex = ExtrasEvent(date_header="21/07/26")
    assert ls.date_header == "07/20/2026"
    assert ex.date_header == "07/21/26"

def test_other_date_format_unchanged():
    # Natural language dates should not be broken
    m = Meal(date_header="Monday, June, 15th 2026")
    assert m.date_header == "Monday, June, 15th 2026"


def test_to_long_date_normalization():
    from app.schemas.estimate_total import to_long_date

    assert to_long_date("Monday, June, 15th 2026") == "Monday, June 15th 2026"
    assert to_long_date("August, Tuesday 5 2025") == "Tuesday, August 5th 2025"
    assert to_long_date("Thursday, September 24th, 2026") == "Thursday, September 24th 2026"
    assert to_long_date("Monday, June 15 2026") == "Monday, June 15th 2026"


def test_request_normalizes_all_date_headers_consistently():
    from app.schemas.estimate_total import EstimateTotalRequest

    req = EstimateTotalRequest(
        client={"name": "C"},
        client_representative={"name": "R"},
        event={"date_formatted": "24/09/2026", "end_date_formatted": "24/09/2026"},
        meals=[{"date_header": "Thursday, September 24th, 2026"}],
        labor_services=[{"date_header": "September, Thursday 24 2026"}],
        extras_events=[{"date_header": "Thursday, September, 24th 2026"}],
        financials={},
    )

    expected = "Thursday, September 24th 2026"
    assert req.meals[0].date_header == expected
    assert req.labor_services[0].date_header == expected
    assert req.extras_events[0].date_header == expected


def test_request_date_header_without_year_uses_event_year():
    from app.schemas.estimate_total import EstimateTotalRequest

    req = EstimateTotalRequest(
        client={"name": "C"},
        client_representative={"name": "R"},
        event={"date_formatted": "24/09/2026"},
        meals=[{"date_header": "Thursday, September 24th"}],
        financials={},
    )

    assert req.meals[0].date_header == "Thursday, September 24th 2026"

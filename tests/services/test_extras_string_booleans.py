import pytest
from docx import Document
from app.schemas.estimate_total import EstimateTotalRequest
from app.services.estimate_docx_generator import EstimateDocxGenerator
from app.services.estimate_perday_docx_generator import EstimatePerDayDocxGenerator

# Reproduces real AppSheet webhook input: boolean fields arrive as strings.
# When provide_by_client is truthy, AppSheet hides the rental/sales selector,
# so `rental` comes through as an empty string ('').
payload = {
    "event_id": "TEST-STRING-BOOLS",
    "client": {"name": "Test Client"},
    "client_representative": {"name": "Rep Name"},
    "event": {
        "name": "String Booleans Event",
        "guests": 10,
        "date_formatted": "Tuesday, Oct 27 2026",
        "end_date_formatted": "Friday, Oct 30 2026",
    },
    "meals": [],
    "labor_services": [],
    "extras_events": [
        # Provided-by-client: rental arrives empty, so it is neither rental nor sale.
        {"date_header": "October, Tuesday 27 2026", "rental": "", "provide_by_client": "true",
         "name": "Stage", "price": "999", "qty": "1"},
        # A real rental (string 'true') on the same date.
        {"date_header": "October, Tuesday 27 2026", "rental": "true", "provide_by_client": "false",
         "name": "Tent", "price": "1000", "qty": "1"},
    ],
    "financials": {
        "tax_rate": "0", "tax_name": "Tax",
        "service_charge_rate": "0", "credit_card_percent": "0",
    },
}


def _gen_paragraphs(generator_cls):
    req = EstimateTotalRequest(**payload)
    docx_bytes = generator_cls().generate_docx(req)
    doc = Document(docx_bytes)
    return [p.text for p in doc.paragraphs]


@pytest.mark.parametrize("generator_cls", [EstimateDocxGenerator, EstimatePerDayDocxGenerator])
def test_string_booleans_validate_and_render(generator_cls):
    # Sanity: the schema must accept string booleans (empty '' and 'true'/'false')
    # without raising a 422-style validation error.
    req = EstimateTotalRequest(**payload)
    assert req.extras_events[0].rental is False
    assert req.extras_events[0].provide_by_client is True
    assert req.extras_events[1].rental is True
    assert req.extras_events[1].provide_by_client is False

    paras = _gen_paragraphs(generator_cls)

    # Provided-by-client item is shown with the placeholder, not a price.
    assert any("Stage\tProvide by the client" in p for p in paras)
    # The real rental is shown with its price.
    assert any("Tent\t$ 1,000.00" in p for p in paras)


@pytest.mark.parametrize("generator_cls", [EstimateDocxGenerator, EstimatePerDayDocxGenerator])
def test_provided_by_client_not_classified_as_rental_or_sales(generator_cls):
    paras = _gen_paragraphs(generator_cls)

    # Only one real rental exists, so exactly one "Rentals" section header.
    assert paras.count("Rentals") == 1
    # No sales exist, so no "Sales" header.
    assert paras.count("Sales") == 0

    # The provided-by-client item must appear directly under the date header
    # (before the "Rentals" section title) and not be nested under a section.
    date_idx = next(i for i, p in enumerate(paras) if "Tuesday, October 27th, 2026" in p)
    rentals_idx = paras.index("Rentals")
    stage_idx = next(i for i, p in enumerate(paras) if "Stage\tProvide by the client" in p)
    assert date_idx < stage_idx < rentals_idx


@pytest.mark.parametrize("generator_cls", [EstimateDocxGenerator, EstimatePerDayDocxGenerator])
def test_provided_by_client_excluded_from_totals(generator_cls):
    paras = _gen_paragraphs(generator_cls)

    # Only the Tent (1000*1) counts as a rental total. Stage (999) is excluded.
    rentals_total = None
    for i, p in enumerate(paras):
        if p == "Extras Services (Rentals)":
            rentals_total = paras[i + 1]
            break
    assert rentals_total is not None
    assert "$ 1,000.00" in rentals_total

import pytest
from docx import Document
from app.schemas.estimate_total import EstimateTotalRequest, sanitize_xml_text
from app.services.estimate_docx_generator import EstimateDocxGenerator
from app.services.estimate_perday_docx_generator import EstimatePerDayDocxGenerator

BAD_DESC = "Grilled\x0bchicken\x00 plate\x7f"

payload = {
    "event_id": "TEST-CTRL",
    "client": {"name": "Test Client"},
    "client_representative": {"name": "Rep Name"},
    "event": {
        "name": "Control Chars Event",
        "guests": 10,
        "date_formatted": "Tuesday, Oct 27 2026",
        "end_date_formatted": "Friday, Oct 30 2026",
    },
    "meals": [
        {
            "show_date_header": True,
            "order": 1,
            "date_header": "October, Tuesday 27 2026",
            "category_name": "Dinner",
            "description": "Meal\x0bdescription",
            "subcategory_1_name": "Apps",
            "subcategory_1_description": "Small\x1bplates",
            "subcategory_1_items": [
                {"name": "Item", "description": BAD_DESC},
                {"name": "Plain", "description": "clean text"},
            ],
        }
    ],
    "labor_services": [],
    "extras_events": [],
    "financials": {
        "total_food_service": "0",
        "total_labor_cost": "0",
        "total_extras_events": "0",
        "total_estimate": "0",
        "tax_rate": "0",
        "tax_name": "Tax",
        "service_charge_rate": "0",
        "credit_card_percent": "0",
    },
}


def test_sanitize_xml_text_removes_control_chars():
    assert sanitize_xml_text("a\x00b\x0bc") == "abc"
    assert sanitize_xml_text("tab\tnewline\ncr\rkept") == "tab\tnewline\ncr\rkept"
    assert sanitize_xml_text("clean") == "clean"
    assert sanitize_xml_text(None) is None
    assert sanitize_xml_text(123) == 123


def test_schema_sanitizes_nested_item_description():
    req = EstimateTotalRequest(**payload)
    item = req.meals[0].subcategory_1_items[0]
    assert item.description == "Grilledchicken plate"
    assert req.meals[0].subcategory_1_description == "Smallplates"
    assert req.meals[0].description == "Mealdescription"


@pytest.mark.parametrize("generator_cls", [EstimateDocxGenerator, EstimatePerDayDocxGenerator])
def test_generators_handle_control_chars(generator_cls):
    req = EstimateTotalRequest(**payload)
    docx_bytes = generator_cls().generate_docx(req)
    doc = Document(docx_bytes)

    full_text = "\n".join(p.text for p in doc.paragraphs)
    assert "Grilledchicken plate" in full_text
    for bad in ("\x0b", "\x00", "\x7f", "\x1b"):
        assert bad not in full_text
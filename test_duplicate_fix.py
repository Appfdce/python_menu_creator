import json
import os
from app.schemas.estimate_total import EstimateTotalRequest
from app.services.estimate_docx_generator import EstimateDocxGenerator

# Mocking a payload with duplicate labor and extras
test_payload = {
    "event_id": "REPRO-DUPLICATE",
    "client": {"name": "Test Client"},
    "client_representative": {"name": "Rep Name"},
    "event": {
        "name": "Testing Duplicates",
        "guests": 100,
        "date_formatted": "Tuesday, Oct 27 2026",
        "end_date_formatted": "Friday, Oct 30 2026"
    },
    "meals": [],
    "labor_services": [
        {
            "show_date_header": True,
            "date_header": "October, Tuesday 27 2026",
            "show_hours_header": True,
            "hours": "14,00",
            "name": "1 Event Manager, 4 Waiters, 1 Chef",
            "total": "7.910,00 $"
        },
        {
            "show_date_header": True,
            "date_header": "October, Tuesday 27 2026",
            "show_hours_header": True,
            "hours": "14,00",
            "name": "1 Event Manager, 4 Waiters, 1 Chef",
            "total": "7.910,00 $"
        }
    ],
    "extras_events": [
        {
            "show_date_header": True,
            "date_header": "October, Tuesday 27 2026",
            "name": "10 x Grey Linen",
            "total": "100,00 $"
        },
        {
            "show_date_header": True,
            "date_header": "October, Tuesday 27 2026",
            "name": "10 x Grey Linen",
            "total": "100,00 $"
        }
    ],
    "financials": {
        "total_food_service": "0,00 $",
        "total_labor_cost": "15.820,00 $",
        "total_extras_events": "200,00 $",
        "total_estimate": "16.020,00 $"
    }
}

def test_duplicates():
    # After our fix, the generator should only use unique items.
    validated = EstimateTotalRequest(**test_payload)
    generator = EstimateDocxGenerator()
    docx_bytes = generator.generate_docx(validated)
    
    with open("repro_fixed.docx", "wb") as f:
        f.write(docx_bytes.getbuffer())
    
    print("Generated repro_fixed.docx - This should now have de-duplicated items.")

if __name__ == "__main__":
    test_duplicates()

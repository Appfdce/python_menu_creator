import os
import sys
from io import BytesIO

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from app.schemas.individual_menu import IndividualSignRequest, AppSheetMealRecord
from app.services.individual_sign_generator import generate_individual_signs_docx

def test_gen():
    meal1 = AppSheetMealRecord(
        menu_name="APRICOTS",
        menu_desc="Dried Apricots",
        menu_1_name="CRAMBERRI",
        menu_1_desc="Died Cranberri",
        menu_2_name="GOLDEN RAISIN", 
        menu_2_desc="Died Golden Raisin",
        menu_3_name="RAISIN",
        menu_3_desc="Died Raisin",
        menu_4_name="BANANA",
        menu_4_desc="Banana"
    )
    
    request = IndividualSignRequest(
        event_id="test_event",
        event_name="Prueba Individual Flat",
        meals=[meal1]
    )
    
    print("Generando DOCX individual...")
    docx_stream = generate_individual_signs_docx(request)
    
    output_path = "test_individual_signs_flat.docx"
    with open(output_path, "wb") as f:
        f.write(docx_stream.getvalue())
    
    print(f"✅ Archivo generado: {os.path.abspath(output_path)}")

if __name__ == "__main__":
    test_gen()

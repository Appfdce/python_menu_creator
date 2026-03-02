from fastapi.testclient import TestClient
from unittest.mock import patch
from app.main import app

client = TestClient(app)

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}

def test_generate_menu_endpoint():
    payload = {
        "event_id": "TEST_EV",
        "event_name": "Test Event",
        "all_meals": [
            {
                "categoria": "Desayuno",
                "fecha": "2023-11-01",
                "descripcion": "Desayuno completo",
                "items": [
                    {"subcat": "Frutas", "menu": "Manzana, Pera"},
                    {"subcat": "Bebidas", "menu": "Café, Jugo"}
                ]
            }
        ]
    }
    
    response = client.post("/api/v1/menus/generate", json=payload)
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    assert "attachment; filename" in response.headers["content-disposition"]
    
    # Check that we actually got some binary content back
    assert len(response.content) > 1000  # A basic empty docx is typically ~11KB

@patch("app.main.drive_service.upload_file")
@patch("app.main.appsheet_service.update_event_sign_link")
def test_generate_excel_endpoint(mock_appsheet, mock_drive):
    # Setup mocks
    mock_drive.return_value = {"success": True, "download_link": "https://test.link"}
    mock_appsheet.return_value = {"success": True}

    payload = {
        "event_id": "TEST_EV_EXCEL",
        "event_name": "Test Excel Event",
        "all_meals": [
            {
                "date": "2024-05-10",
                "category": "Lunch",
                "description": "Special Lunch",
                "items": [
                    {"subcat": "Main", "menu": "Burger || Beef burger || GF"}
                ]
            }
        ]
    }
    
    response = client.post("/api/v1/menus/generate-excel", json=payload)
    
    assert response.status_code == 200
    assert response.json() == {
        "individual_excel": {"success": True, "download_link": "https://test.link"},
        "combined_excel": {"success": True, "download_link": "https://test.link"},
        "success": True,
        "appsheet_update_individual": {"success": True},
        "appsheet_update_combined": {"success": True}
    }
    
    # Verify the mocked services were called with expected filenames
    assert mock_drive.call_count == 2
    args_list = mock_drive.call_args_list
    assert args_list[0][0][1] == "Individual_Excel_Test_Excel_Event.xlsx"
    assert args_list[1][0][1] == "Combined_Excel_Test_Excel_Event.xlsx"
    
    assert mock_appsheet.call_count == 2
    appsheet_args = mock_appsheet.call_args_list
    assert appsheet_args[0][1]["column_name"] == "excel_individual"
    assert appsheet_args[1][1]["column_name"] == "excel_combined"


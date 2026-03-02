import pytest
import pandas as pd
from app.services.excel_generator import (
    parse_concatenated_menus,
    sort_dataframe_by_date,
    generate_individual_excel,
    generate_combined_excel
)
from app.schemas.excel_menu import ExcelMenuRequest, ExcelMealData, ExcelMenuPair

def test_parse_concatenated_menus():
    # Helper to avoid repetitive test code
    def check(text, expected):
        assert parse_concatenated_menus(text) == expected

    # Basic formats without description
    check("Menu 1 || V, GF", [("Menu 1", "", "V, GF")])
    check("Menu 1 || V, GF , Menu 2 || VG", [("Menu 1", "", "V, GF"), ("Menu 2", "", "VG")])
    
    # Formats with description
    check("Menu 1 || Desc 1 || V, GF", [("Menu 1", "Desc 1", "V, GF")])
    check("Menu 1 || Desc 1 || V, GF , Menu 2 || Desc 2 || VG", 
          [("Menu 1", "Desc 1", "V, GF"), ("Menu 2", "Desc 2", "VG")])

    # No diet options
    check("Menu 1", [("Menu 1", "", "")])
    check("Menu 1 || Desc 1", [("Menu 1", "Desc 1", "")])

def test_sort_dataframe_by_date():
    df = pd.DataFrame([
        {"Date": "2024-05-10"},
        {"Date": "2024-05-08"},
        {"Date": "2024-05-09"},
    ])
    sorted_df = sort_dataframe_by_date(df)
    assert sorted_df["Date"].tolist() == ["2024-05-08", "2024-05-09", "2024-05-10"]

    # Test empty dataframe
    empty_df = pd.DataFrame()
    assert sort_dataframe_by_date(empty_df).empty

def test_generate_individual_excel():
    req = ExcelMenuRequest(
        event_id="EV123",
        event_name="Test Event",
        all_meals=[
            ExcelMealData(
                date="2024-05-10",
                category="Lunch",
                description="Special Lunch",
                items=[
                    ExcelMenuPair(subcat="Main", menu="Burger || Beef burger || GF")
                ]
            )
        ]
    )
    result = generate_individual_excel(req)
    assert result is not None
    # We can check if it's a valid bytes buffer
    result.seek(0)
    df = pd.read_excel(result, engine='openpyxl')
    assert len(df) == 1
    assert df.iloc[0]["Menu"] == "Burger"
    assert df.iloc[0]["Description"] == "Beef burger"
    assert df.iloc[0]["Diet Options"] == "GF"

def test_generate_combined_excel():
    req = ExcelMenuRequest(
        event_id="EV123",
        event_name="Test Event",
        all_meals=[
            ExcelMealData(
                date="2024-05-10",
                category="Lunch",
                description="Special Lunch",
                items=[
                    ExcelMenuPair(subcat="Main", menu="Burger || Beef burger || GF")
                ]
            )
        ]
    )
    result = generate_combined_excel(req)
    assert result is not None
    result.seek(0)
    df = pd.read_excel(result, engine='openpyxl')
    assert len(df) == 1
    # Check if the description and diet options were formatted correctly
    # generate_combined_excel currently returns f"{base_text} || {diet_options}"
    assert df.iloc[0]["Menu"] == "Burger || GF"

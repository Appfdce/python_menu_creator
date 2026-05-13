import pytest
from app.services.estimate_docx_generator import EstimateDocxGenerator
from app.services.estimate_perday_docx_generator import EstimatePerDayDocxGenerator

def test_currency_formatting_docx_generator():
    generator = EstimateDocxGenerator()
    
    # Case 1: European format with comma as decimal
    assert generator._format_currency("2.100,00") == "$ 2,100.00"
    
    # Case 2: Simple numbers
    assert generator._format_currency("1000") == "$ 1,000.00"
    
    # Case 3: Negative amounts
    assert generator._format_currency("-2.100,00") == "-$ 2,100.00"
    
    # Case 4: Already correctly formatted
    assert generator._format_currency("$ 2,100.00") == "$ 2,100.00"

def test_currency_formatting_perday_docx_generator():
    generator = EstimatePerDayDocxGenerator()
    
    # Case 1: European format with comma as decimal
    assert generator._format_currency("2.100,00") == "$ 2,100.00"
    
    # Case 2: Simple numbers
    assert generator._format_currency("1000") == "$ 1,000.00"
    
    # Case 3: Negative amounts
    assert generator._format_currency("-2.100,00") == "-$ 2,100.00"
    
    # Case 4: Already correctly formatted
    assert generator._format_currency("$ 2,100.00") == "$ 2,100.00"

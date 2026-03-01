import pandas as pd
from io import BytesIO
from typing import Tuple
from app.schemas.excel_menu import ExcelMenuRequest

def split_menu_text(full_text: str) -> Tuple[str, str]:
    """Helper to split concatenated text 'Name || Diet Options' safely."""
    if not full_text:
        return "", ""
        
    parts = full_text.split("||")
    name = parts[0].strip()
    
    # Check if there's actually diet option part
    diet = parts[1].strip() if len(parts) > 1 else ""
    return name, diet

def generate_individual_excel(request: ExcelMenuRequest) -> BytesIO:
    """
    Generates an Excel where each individual menu item is a row.
    Columns: Date | Clock In | Clock Out | Category | Description | Subcategory | Menu | Diet Options
    """
    rows = []
    
    for meal in request.all_meals:
        # Base row data that is the same for every menu item in this meal
        base_data = {
            "Date": meal.date,
            "Clock In": meal.clock_in,
            "Clock Out": meal.clock_out,
            "Category": meal.category,
            "Description": meal.description
        }
        
        for item in meal.items:
            # Skip empty entries if desired
            if not item.subcat.strip() and not item.menu.strip():
                continue
                
            # A subcategory might contain multiple concatenated menus "Menu1 || Diet1 , Menu2 || Diet2"
            # However, diet options or menu names themselves might contain commas.
            # The user specified that the valid diet options are exactly "GF", "VG", "V".
            raw_parts = [m.strip() for m in item.menu.split(",")]
            raw_menus = []
            
            valid_diet_options = {"GF", "VG", "V"}
            
            for part in raw_parts:
                if not part:
                    continue
                    
                # If it has "||", it's definitely a new menu item
                if "||" in part:
                    raw_menus.append(part)
                # If it's one of the exact diet options, it belongs to the previous menu item
                elif part in valid_diet_options:
                    if raw_menus:
                        raw_menus[-1] += f", {part}"
                    else:
                        raw_menus.append(part)
                # Otherwise, it does not have "||" and is not a diet option.
                # It is likely a continuation of the previous menu item's NAME because the name contained a comma.
                else:
                    if raw_menus:
                        raw_menus[-1] += f", {part}"
                    else:
                        raw_menus.append(part)
            
            for raw_menu in raw_menus:
                if not raw_menu:
                    continue
                    
                menu_name, diet_options = split_menu_text(raw_menu)
                
                row = base_data.copy()
                row["Subcategory"] = item.subcat
                row["Menu"] = menu_name
                row["Diet Options"] = diet_options
                
                rows.append(row)
                
    df = pd.DataFrame(rows)
    
    # Save to memory
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Individual Menus')
    
    output.seek(0)
    return output

def generate_combined_excel(request: ExcelMenuRequest) -> BytesIO:
    """
    Generates an Excel where each row is a Meal's subcategory.
    Columns: Date | Clock In | Clock Out | Category | Description | Subcategory | Menu
    """
    rows = []
    
    for meal in request.all_meals:
        base_data = {
            "Date": meal.date,
            "Clock In": meal.clock_in,
            "Clock Out": meal.clock_out,
            "Category": meal.category,
            "Description": meal.description
        }
        
        for item in meal.items:
            # Skip empty entries if desired
            if not item.subcat.strip() and not item.menu.strip():
                continue
            
            row = base_data.copy()
            row["Subcategory"] = item.subcat
            # The user requested that for combined, menu includes all names + diet options together.
            # We output the raw string exactly as provided (e.g. "Item || Diet , Item 2 || Diet 2")
            row["Menu"] = item.menu
            
            rows.append(row)
        
    df = pd.DataFrame(rows)
    
    # Save to memory
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Combined Menus')
    
    output.seek(0)
    return output

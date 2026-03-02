import pandas as pd
from io import BytesIO
from typing import Tuple
from app.schemas.excel_menu import ExcelMenuRequest

import re

def parse_concatenated_menus(full_text: str):
    """
    Parses a string like "Menu 1 || Description 1 || GF, V , Menu 2 .. || VG"
    If Description is not provided, it falls back to 2 sections.
    Returns a list of tuples: [(Menu Name, Menu Description, Diet Options), ...]
    """
    if not full_text.strip():
        return []

    parts = [p.strip() for p in full_text.split("||")]
    if len(parts) == 1:
        return [(parts[0], "", "")]

    valid_diets = {"V", "VG", "GF", "DF", "NF", ""}

    results = []
    current_name = parts[0]
    current_desc = ""

    def finalize(name, desc, diet):
        if name:
            results.append((name.strip(), (desc or "").strip(), diet.strip()))

    for i in range(1, len(parts)):
        part = parts[i]
        tokens = [t.strip() for t in part.split(",")]
        
        diet_tokens = []
        name_tokens = []
        found_name = False
        
        for t in tokens:
            if not found_name and (t in valid_diets or not t):
                diet_tokens.append(t)
            else:
                found_name = True
                name_tokens.append(t)
                
        if found_name:
            # We found a boundary!
            diet_str = ", ".join(diet_tokens)
            next_name = ", ".join(name_tokens)
            
            if diet_str or (not diet_str and not current_desc):
                if not diet_tokens:
                    # simplistic fallback: the first comma separates the desc from next name
                    splits = part.split(",", 1)
                    if len(splits) == 2:
                        desc_str = splits[0].strip()
                        next_name = splits[1].strip()
                        if current_desc:
                            finalize(current_name, current_desc, desc_str)
                        else:
                            finalize(current_name, desc_str, "")
                        current_name = next_name
                        current_desc = ""
                    else:
                        if current_desc:
                             finalize(current_name, current_desc, part)
                             current_name = ""
                             current_desc = ""
                        else:
                             current_desc = part
                else:
                    if current_desc:
                        finalize(current_name, current_desc, diet_str)
                    else:
                        finalize(current_name, "", diet_str)
                    current_name = next_name
                    current_desc = ""
            else:
                 finalize(current_name, current_desc, "")
                 current_name = next_name
                 current_desc = ""
        else:
            # Entire part is diet options
            if i == len(parts) - 1:
                is_diet = all(t in valid_diets or not t for t in tokens)
                if current_desc:
                    finalize(current_name, current_desc, part)
                else:
                    if is_diet and part:
                        finalize(current_name, "", part)
                    else:
                        finalize(current_name, part, "")
                current_name = ""
                current_desc = ""
            else:
                if current_desc:
                    finalize(current_name, current_desc, part)
                    current_name = ""
                    current_desc = ""
                else:
                    current_desc = part

    # Catch dangling 
    if current_name:
         finalize(current_name, current_desc, "")
         
    return results

def sort_dataframe_by_date(df: pd.DataFrame) -> pd.DataFrame:
    """Helper to sort dataframe by Date."""
    if df.empty:
        return df
    
    df['_sort_date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.sort_values(by=['_sort_date'], na_position='first')
    return df.drop(columns=['_sort_date'])

def sort_dataframe_by_date(df: pd.DataFrame) -> pd.DataFrame:
    """Helper to sort dataframe by Date."""
    if df.empty:
        return df
    
    # Safely convert to datetime/time for sorting without overwriting original string format
    df['_sort_date'] = pd.to_datetime(df['Date'], errors='coerce')
    
    # Sort placing NaT (empty times) first
    df = df.sort_values(by=['_sort_date'], na_position='first')
        
    return df.drop(columns=['_sort_date'])

def generate_individual_excel(request: ExcelMenuRequest) -> BytesIO:
    """
    Generates an Excel where each individual menu item is a row.
    Columns: Date | Category | Category Desc | Subcategory | Menu | Description | Diet Options
    """
    rows = []
    
    for meal in request.all_meals:
        base_data = {
            "Date": meal.date,
            "Category": meal.category,
            "Category Desc": meal.description # Changed from just "Description" to avoid name collision
        }
        
        for item in meal.items:
            # Skip empty entries if desired
            if not item.subcat.strip() and not item.menu.strip():
                continue
                
            # Use the new robust parsing function
            parsed_menus = parse_concatenated_menus(item.menu)
            
            for menu_name, menu_description, diet_options in parsed_menus:
                row = base_data.copy()
                row["Subcategory"] = item.subcat
                row["Menu"] = menu_name
                row["Description"] = menu_description
                row["Diet Options"] = diet_options
                
                rows.append(row)
                
    df = pd.DataFrame(rows)
    df = sort_dataframe_by_date(df)
    
    # Important: Reorder columns to ensure "Description" is between "Menu" and "Diet Options"
    # and parent Category description is clearly differentiated.
    column_order = ["Date", "Category", "Category Desc", "Subcategory", "Menu", "Description", "Diet Options"]
    # Add any missing columns safely
    for col in column_order:
        if col not in df.columns:
            df[col] = ""
    df = df[column_order]
    
    # Save to memory
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Individual Menus')
    
    output.seek(0)
    return output

def generate_combined_excel(request: ExcelMenuRequest) -> BytesIO:
    """
    Generates an Excel where each row is a Meal's subcategory.
    Columns: Date | Category | Category Desc | Subcategory | Menu
    """
    rows = []
    
    for meal in request.all_meals:
        base_data = {
            "Date": meal.date,
            "Category": meal.category,
            "Category Desc": meal.description
        }
        
        for item in meal.items:
            # Skip empty entries if desired
            if not item.subcat.strip() and not item.menu.strip():
                continue
            
            row = base_data.copy()
            row["Subcategory"] = item.subcat
            
            # Use the robust parsed menus to reformat the string gracefully
            parsed_menus = parse_concatenated_menus(item.menu)
            
            formatted_menus = []
            for menu_name, menu_desc, diet_options in parsed_menus:
                
                base_text = menu_name
                
                if diet_options:
                    formatted_menus.append(f"{base_text} || {diet_options}")
                else:
                    # Omit the || when there are no diet options
                    formatted_menus.append(base_text)
                    
            row["Menu"] = " , ".join(formatted_menus)
            
            rows.append(row)
        
    df = pd.DataFrame(rows)
    df = sort_dataframe_by_date(df)
    
    column_order = ["Date", "Category", "Category Desc", "Subcategory", "Menu"]
    for col in column_order:
        if col not in df.columns:
            df[col] = ""
    df = df[column_order]
    
    # Save to memory
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Combined Menus')
    
    output.seek(0)
    return output

import re

def format_to_us_date(val: str) -> str:
    if not val:
        return val
    
    val_clean = val.strip()
    # 1. Match DD/MM/YYYY
    match1 = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})$", val_clean)
    if match1:
        day, month, year = match1.groups()
        return f"{month.zfill(2)}/{day.zfill(2)}/{year}"
        
    # 2. Match DD/MM/YY
    match2 = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{2})$", val_clean)
    if match2:
        day, month, year = match2.groups()
        return f"{month.zfill(2)}/{day.zfill(2)}/{year}"
        
    return val

def format_time_range(val: str) -> str:
    if not val:
        return val
    
    # Replace any "to" surrounded by alphanumeric characters, ensuring exactly one space on each side.
    # Using capture groups instead of variable-width look-behind.
    # Replace "to" with " to " only if it is preceded by a digit or M (from AM/PM)
    # and followed by a digit or A/P (from AM/PM).
    # E.g. "AMto9", "8 to9", "8to9", "AM to 9".
    # Regex: match digit or M/m, then optional whitespace, then 'to', then optional whitespace, then digit or A/a/P/p.
    res = re.sub(r'([0-9Mm])\s*to\s*([0-9AaPp])', r'\1 to \2', val, flags=re.IGNORECASE)
    
    return ' '.join(res.split())

# Test Date
print("--- Date Tests ---")
print("13/05/26 ->", format_to_us_date("13/05/26"))
print("05/13/2026 ->", format_to_us_date("13/05/2026"))
print("5/6/26 ->", format_to_us_date("5/6/26"))
print("June, Wednesday 17 2026 ->", format_to_us_date("June, Wednesday 17 2026"))

# Test Time Range
print("\n--- Time Range Tests ---")
print("'8:00 AM to9:00 AM' ->", format_time_range("8:00 AM to9:00 AM"))
print("'8:00 AMto9:00 AM' ->", format_time_range("8:00 AMto9:00 AM"))
print("'8:00 AM to 9:00 AM' ->", format_time_range("8:00 AM to 9:00 AM"))
print("'8:00AM to9:00AM' ->", format_time_range("8:00AM to9:00AM"))
print("'8:00 to 9:00' ->", format_time_range("8:00 to 9:00"))
print("'8:00to9:00' ->", format_time_range("8:00to9:00"))
print("'Tomato to potato' ->", format_time_range("Tomato to potato"))

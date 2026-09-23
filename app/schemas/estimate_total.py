import re
from datetime import datetime
from pydantic import BaseModel, ConfigDict, field_validator, model_validator
from typing import List, Optional

INVALID_XML_CHARS = re.compile(
    r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x84\x86-\x9f\ud800-\udfff\ufdd0-\ufddf\ufffe\uffff]"
)

_MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]
_WEEKDAY_NAMES = [
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday",
]

# Recognized month names by language (input) mapped to month number, so dates
# coming from AppSheet in Spanish/Portuguese can still be rendered in English.
_MONTH_INPUT_NAMES = {
    # English
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
    # Spanish
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
    "julio": 7, "agosto": 8, "septiembre": 9, "setiembre": 9, "octubre": 10,
    "noviembre": 11, "diciembre": 12,
    # Portuguese
    "janeiro": 1, "fevereiro": 2, "março": 3, "marco": 3, "maio": 5, "junho": 6,
    "julho": 7, "setembro": 9, "outubro": 10, "novembro": 11, "dezembro": 12,
}


def _ordinal(day: int) -> str:
    """Returns the English ordinal for a day, e.g. 1 -> '1st', 24 -> '24th'."""
    if 10 <= day % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
    return f"{day}{suffix}"


def _extract_year(val) -> Optional[int]:
    """Best-effort extraction of a 4-digit year (or 2-digit numeric year) from a date string."""
    if not val:
        return None
    s = str(val)
    m = re.search(r"(?<!\d)(\d{4})(?!\d)", s)
    if m:
        return int(m.group(1))
    m = re.search(r"/(\d{2})(?!\d)", s)
    if m:
        return 2000 + int(m.group(1))
    return None


def _canonical_long_date(dt: datetime) -> str:
    weekday = _WEEKDAY_NAMES[dt.weekday()]
    month = _MONTH_NAMES[dt.month - 1]
    return f"{weekday}, {month} {_ordinal(dt.day)}, {dt.year}"


def to_long_date(val, fallback_year: Optional[int] = None) -> str:
    """Normalizes a date string to the canonical long format
    'Weekday, Month Dayth, Year' (e.g. 'Thursday, September 24th, 2026').

    Handles the multiple long formats coming from AppSheet (any token order,
    with or without ordinal suffix, with or without year) as well as US
    numeric dates (MM/DD/YYYY or MM/DD/YY). Returns the input unchanged when
    it cannot be parsed reliably.
    """
    if not val:
        return val

    s = " ".join(str(val).split())

    # Numeric US formats (already normalized by format_to_us_date)
    m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})$", s)
    if m:
        month, day, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
        try:
            return _canonical_long_date(datetime(year, month, day))
        except ValueError:
            return s
    m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{2})$", s)
    if m:
        month, day, year = int(m.group(1)), int(m.group(2)), 2000 + int(m.group(3))
        try:
            return _canonical_long_date(datetime(year, month, day))
        except ValueError:
            return s

    # Long formats: locate month name, day and (optional) year in any order
    lower = s.lower()
    month = None
    for name, number in _MONTH_INPUT_NAMES.items():
        if re.search(r"\b" + re.escape(name) + r"\b", lower):
            month = number
            break
    if month is None:
        return s

    day_match = re.search(r"(?<!\d)(\d{1,2})(?:st|nd|rd|th)?(?!\d)", s)
    if not day_match:
        return s
    day = int(day_match.group(1))

    year = _extract_year(s) or fallback_year
    if not year:
        return s

    try:
        return _canonical_long_date(datetime(year, month, day))
    except ValueError:
        return s


def sanitize_xml_text(value):
    """Removes characters that are invalid in XML 1.0 documents (e.g. NULL bytes
    and control characters coming from AppSheet data)."""
    if not isinstance(value, str):
        return value
    return INVALID_XML_CHARS.sub("", value)

def format_to_us_date(val: str) -> str:
    """Converts DD/MM/YYYY or DD/MM/YY to MM/DD/YYYY or MM/DD/YY (US format)."""
    if not val:
        return val
    val_clean = str(val).strip()
    
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
    """Normalizes meal time ranges:
    - adds the missing spaces around 'to' when it is glued to an hour
      (e.g. '2:30 p. m. to2:45 p. m.' -> '2:30 PM to 2:45 PM')
    - normalizes AM/PM markers written as 'a. m.', 'p.m.', 'pm', etc.
    """
    if not val:
        return val

    res = str(val)
    # Normalize AM/PM markers: 'p. m.', 'p.m.', 'pm', 'P.M.' -> 'PM'
    res = re.sub(r'(?<![a-z])([ap])\s*\.?\s*m(?![a-z])\.?', lambda m: m.group(1).upper() + 'M', res, flags=re.IGNORECASE)
    # Ensure a space after 'to' when followed by a digit, and before 'to'
    # when preceded by a digit or an AM/PM marker (avoids touching words).
    res = re.sub(r'(to)(?=\d)', r'\1 ', res, flags=re.IGNORECASE)
    res = re.sub(r'(?<=[0-9Mm])(to)', r' \1', res, flags=re.IGNORECASE)
    # Separate the marker from the hour when glued: '8:00AM' -> '8:00 AM'
    res = re.sub(r'(?<=\d)(AM|PM)\b', r' \1', res)

    return ' '.join(res.split())

def coerce_bool(v):
    """Coerce AppSheet boolean values (which may arrive as empty strings or
    strings like 'true'/'false'/'1'/'0') into real booleans."""
    if isinstance(v, bool):
        return v
    if v is None:
        return False
    s = str(v).strip().lower()
    if s in ("", "0", "false", "no", "n", "f", "none"):
        return False
    if s in ("1", "true", "yes", "y", "t"):
        return True
    return False


class BaseSchema(BaseModel):
    model_config = ConfigDict(coerce_numbers_to_str=True)

    @model_validator(mode='after')
    def _strip_invalid_xml_chars(self):
        for name, value in self.__dict__.items():
            if isinstance(value, str):
                object.__setattr__(self, name, INVALID_XML_CHARS.sub("", value))
        return self

class ClientInfo(BaseSchema):
    name: str = ""
    address: str = ""
    email: str = ""

class ClientRepresentative(BaseSchema):
    name: str = ""
    email: str = ""
    formatted_phone: str = ""

class EventInfo(BaseSchema):
    name: str = ""
    address: str = ""
    code: str = ""
    date_formatted: str = ""
    end_date_formatted: str = ""
    guests: int = 0
    dietary_restrictions: str = ""
    proposal_type: str = ""

    @field_validator('guests', mode='before')
    @classmethod
    def coerce_guests(cls, v):
        if v == "" or v is None:
            return 0
        return int(v)

    @field_validator('date_formatted', 'end_date_formatted', mode='after')
    @classmethod
    def format_dates(cls, v):
        return format_to_us_date(v)

    @field_validator('proposal_type', mode='before')
    @classmethod
    def normalize_proposal_type(cls, v):
        """Canonicalizes the document type sent from AppSheet.
        Accepts 'Anual'/'Annual' -> 'anual' and 'Particular' -> 'particular'.
        Any other value (including empty) falls back to the legacy template."""
        if v is None:
            return ""
        s = str(v).strip().lower()
        if s in ("anual", "annual"):
            return "anual"
        if s == "particular":
            return "particular"
        return ""

class MenuItem(BaseSchema):
    name: str = ""
    description: str = ""
    diet_options: str = ""


class Meal(BaseSchema):
    show_date_header: bool = False
    order: int = 0
    date_header: str = ""
    category_name: str = ""
    time_range: str = ""
    description: str = ""
    category_precio_guest: str = ""
    total_category_precio: str = ""
    provide_by_client: bool = False
    total_food_por_dia: str = ""
    
    # Fields for Per Day Estimate
    show_date_header_2: bool = False
    date_day_name: str = ""
    guest_count: str = ""
    show_guest_header: bool = False
    total_category_precio_guest_por_dia: str = ""
    
    # Flattened subcategories to match AppSheet fixed columns
    subcategory_1_name: Optional[str] = ""
    subcategory_1_description: Optional[str] = ""
    subcategory_1_items: List[MenuItem] = []
    
    subcategory_2_name: Optional[str] = ""
    subcategory_2_description: Optional[str] = ""
    subcategory_2_items: List[MenuItem] = []
    
    subcategory_3_name: Optional[str] = ""
    subcategory_3_description: Optional[str] = ""
    subcategory_3_items: List[MenuItem] = []
    
    subcategory_4_name: Optional[str] = ""
    subcategory_4_description: Optional[str] = ""
    subcategory_4_items: List[MenuItem] = []
    
    subcategory_5_name: Optional[str] = ""
    subcategory_5_description: Optional[str] = ""
    subcategory_5_items: List[MenuItem] = []
    
    subcategory_6_name: Optional[str] = ""
    subcategory_6_description: Optional[str] = ""
    subcategory_6_items: List[MenuItem] = []
    
    subcategory_7_name: Optional[str] = ""
    subcategory_7_description: Optional[str] = ""
    subcategory_7_items: List[MenuItem] = []
    
    subcategory_8_name: Optional[str] = ""
    subcategory_8_description: Optional[str] = ""
    subcategory_8_items: List[MenuItem] = []
    
    subcategory_9_name: Optional[str] = ""
    subcategory_9_description: Optional[str] = ""
    subcategory_9_items: List[MenuItem] = []
    
    subcategory_10_name: Optional[str] = ""
    subcategory_10_description: Optional[str] = ""
    subcategory_10_items: List[MenuItem] = []
    
    subcategory_11_name: Optional[str] = ""
    subcategory_11_description: Optional[str] = ""
    subcategory_11_items: List[MenuItem] = []
    
    subcategory_12_name: Optional[str] = ""
    subcategory_12_description: Optional[str] = ""
    subcategory_12_items: List[MenuItem] = []

    @field_validator('date_header', mode='after')
    @classmethod
    def format_date_header(cls, v):
        return format_to_us_date(v)

    @field_validator('time_range', mode='after')
    @classmethod
    def format_times(cls, v):
        return format_time_range(v)

    @field_validator('show_date_header', 'provide_by_client', 'show_date_header_2', 'show_guest_header', mode='before')
    @classmethod
    def coerce_bools(cls, v):
        return coerce_bool(v)

class LaborService(BaseSchema):
    show_date_header: bool = False
    order: int = 0
    date_header: str = ""
    show_hours_header: bool = False
    hours: str = ""
    name: str = ""
    total: str = ""

    @field_validator('date_header', mode='after')
    @classmethod
    def format_date_header(cls, v):
        return format_to_us_date(v)

    @field_validator('show_date_header', 'show_hours_header', mode='before')
    @classmethod
    def coerce_bools(cls, v):
        return coerce_bool(v)

class ExtrasEvent(BaseSchema):
    show_date_header: bool = False
    date_header: str = ""
    is_rental: bool = False
    is_sales: bool = False
    rental: bool = False
    name: str = ""
    price: str = ""
    qty: str = ""
    name_rental: str = ""
    name_sales: str = ""
    total: str = ""
    provide_by_client: bool = False

    @field_validator('show_date_header', 'is_rental', 'is_sales', 'rental', 'provide_by_client', mode='before')
    @classmethod
    def coerce_bools(cls, v):
        return coerce_bool(v)

    @field_validator('date_header', mode='after')
    @classmethod
    def format_date_header(cls, v):
        return format_to_us_date(v)

class Financials(BaseSchema):
    total_food_service: str = ""
    total_labor_cost: str = ""
    total_extras_events: str = ""
    tax_name: str = ""
    tax_rate: str = ""
    total_tax: str = ""
    total_extras_sales: str = ""
    service_charge_rate: str = ""
    total_service_charge: str = ""
    discount: str = ""
    donation: str = ""
    total_credit_card: str = ""
    credit_card_percent: str = "0"
    gratuity: str = ""
    total_estimate: str = ""

class EstimateTotalRequest(BaseSchema):
    event_id: str = ""
    client: ClientInfo
    client_representative: ClientRepresentative
    event: EventInfo
    meals: List[Meal] = []
    labor_services: List[LaborService] = []
    extras_events: List[ExtrasEvent] = []
    financials: Financials

    @model_validator(mode='after')
    def _normalize_long_dates(self):
        # Long date headers must be consistent across Food, Labor and Extras.
        # The event year is used as fallback for headers that omit the year.
        fallback_year = (
            _extract_year(self.event.date_formatted)
            or _extract_year(self.event.end_date_formatted)
        )
        for meal in self.meals:
            if meal.date_header:
                meal.date_header = to_long_date(meal.date_header, fallback_year)
        for labor in self.labor_services:
            if labor.date_header:
                labor.date_header = to_long_date(labor.date_header, fallback_year)
        for extra in self.extras_events:
            if extra.date_header:
                extra.date_header = to_long_date(extra.date_header, fallback_year)
        return self

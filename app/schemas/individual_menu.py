from pydantic import BaseModel, Field
from typing import List, Optional, Any

class AppSheetMealRecord(BaseModel):
    # Base Menu
    menu_name: Optional[str] = ""
    menu_desc: Optional[str] = ""
    menu_diet: Optional[str] = ""
    
    # Menus 1 to 10
    menu_1_name: Optional[str] = ""
    menu_1_desc: Optional[str] = ""
    menu_1_diet: Optional[str] = ""
    
    menu_2_name: Optional[str] = ""
    menu_2_desc: Optional[str] = ""
    menu_2_diet: Optional[str] = ""
    
    menu_3_name: Optional[str] = ""
    menu_3_desc: Optional[str] = ""
    menu_3_diet: Optional[str] = ""
    
    menu_4_name: Optional[str] = ""
    menu_4_desc: Optional[str] = ""
    menu_4_diet: Optional[str] = ""
    
    menu_5_name: Optional[str] = ""
    menu_5_desc: Optional[str] = ""
    menu_5_diet: Optional[str] = ""
    
    menu_6_name: Optional[str] = ""
    menu_6_desc: Optional[str] = ""
    menu_6_diet: Optional[str] = ""
    
    menu_7_name: Optional[str] = ""
    menu_7_desc: Optional[str] = ""
    menu_7_diet: Optional[str] = ""
    
    menu_8_name: Optional[str] = ""
    menu_8_desc: Optional[str] = ""
    menu_8_diet: Optional[str] = ""
    
    menu_9_name: Optional[str] = ""
    menu_9_desc: Optional[str] = ""
    menu_9_diet: Optional[str] = ""
    
    menu_10_name: Optional[str] = ""
    menu_10_desc: Optional[str] = ""
    menu_10_diet: Optional[str] = ""

class IndividualSignRequest(BaseModel):
    event_id: str
    event_name: str
    meals: List[AppSheetMealRecord]


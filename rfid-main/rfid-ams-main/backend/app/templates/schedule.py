from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()
templates = Jinja2Templates(directory="backend/app/templates")

# Booking model (Added 'lab' so we know which room is being reserved)
class BookingRequest(BaseModel):
    full_name: str
    id_number: str
    college: str
    department: str
    lab: str  # Fixed: Needed to map the booking to a specific lab
    date: str
    time: str

# Base structure for each lab (empty by default)
SCHEDULE_DATA = {
    "CS Lab": {"Monday": {}, "Tuesday": {}, "Wednesday": {}, "Thursday": {}, "Friday": {}, "Saturday": {}, "Sunday": {}},
    "Database Lab": {"Monday": {}, "Tuesday": {}, "Wednesday": {}, "Thursday": {}, "Friday": {}, "Saturday": {}, "Sunday": {}},
    "Embedded Lab": {"Monday": {}, "Tuesday": {}, "Wednesday": {}, "Thursday": {}, "Friday": {}, "Saturday": {}, "Sunday": {}},
    "IOT Lab": {"Monday": {}, "Tuesday": {}, "Wednesday": {}, "Thursday": {}, "Friday": {}, "Saturday": {}, "Sunday": {}},
    "Multimedia Lab": {"Monday": {}, "Tuesday": {}, "Wednesday": {}, "Thursday": {}, "Friday": {}, "Saturday": {}, "Sunday": {}},
    "Network Lab": {"Monday": {}, "Tuesday": {}, "Wednesday": {}, "Thursday": {}, "Friday": {}, "Saturday": {}, "Sunday": {}},
}

# In-memory storage for bookings (acts as our temporary database)
bookings = []

@router.get("/schedule", response_class=HTMLResponse)
def get_schedule(request: Request):
    return templates.TemplateResponse("schedule.html", {"request": request})


@router.get("/api/schedule/{lab}")
def get_lab_schedule(lab: str):
    """Get schedule data dynamically populated by current bookings"""
    
    # 1. Create a fresh template layout for all labs
    current_schedule = {
        lab_name: {day: {} for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]}
        for lab_name in SCHEDULE_DATA.keys()
    }
    
    # 2. Inject bookings dynamically into the schedule layout
    for b in bookings:
        b_lab = b.get("lab", "")
        # Find matching lab key using case-insensitive check
        matched_lab = next((l for l in SCHEDULE_DATA if l.lower() == b_lab.lower()), None)
        
        if matched_lab:
            date_str = b.get("date", "")
            day_name = None
            
            # Try parsing date formats to extract the day of the week
            for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"):
                try:
                    day_name = datetime.strptime(date_str, fmt).strftime("%A")
                    break
                except ValueError:
                    continue
            
            # Fallback if date string is already a raw weekday name (e.g. "Monday")
            if not day_name:
                cap_date = date_str.capitalize()
                if cap_date in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]:
                    day_name = cap_date
            
            # If day and time match up, inject the booking details into that slot
            if day_name:
                time_slot = b.get("time")
                if time_slot:
                    current_schedule[matched_lab][day_name][time_slot] = {
                        "id": b["id"],
                        "full_name": b["full_name"],
                        "id_number": b["id_number"],
                        "college": b["college"],
                        "department": b["department"],
                        "status": b["status"]
                    }

    # 3. Handle 'all' labs request merge
    if lab == "all":
        combined_schedule = {}
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        
        for day in days:
            combined_schedule[day] = {}
            for lab_name, lab_schedule in current_schedule.items():
                for time, data in lab_schedule.get(day, {}).items():
                    if time not in combined_schedule[day]:
                        combined_schedule[day][time] = data
        return combined_schedule
    
    # 4. Handle exact or case-insensitive single lab matches
    if lab in current_schedule:
        return current_schedule[lab]
    
    for lab_name, lab_schedule in current_schedule.items():
        if lab_name.lower() == lab.lower():
            return lab_schedule
    
    # Fallback default response if lab name isn't recognized
    return {day: {} for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]}


@router.post("/api/bookings")
async def create_booking(booking: BookingRequest):
    """Create a new lab booking"""
    booking_data = {
        "id": len(bookings) + 1,
        "full_name": booking.full_name,
        "id_number": booking.id_number,
        "college": booking.college,
        "department": booking.department,
        "lab": booking.lab,         # Fixed: Store the target lab selection
        "date": booking.date,
        "time": booking.time,
        "created_at": datetime.now().isoformat(),
        "status": "pending",
    }
    bookings.append(booking_data)
    return {"message": "Booking created successfully", "booking": booking_data}
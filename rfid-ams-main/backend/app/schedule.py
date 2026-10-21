from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()
templates = Jinja2Templates(directory="backend/app/templates")

# Booking model
class BookingRequest(BaseModel):
    full_name: str
    id_number: str
    college: str
    department: str
    date: str
    time: str

# Sample schedule data for each lab (empty by default)
SCHEDULE_DATA = {
    "CS Lab": {"Monday": {}, "Tuesday": {}, "Wednesday": {}, "Thursday": {}, "Friday": {}, "Saturday": {}, "Sunday": {}},
    "Database Lab": {"Monday": {}, "Tuesday": {}, "Wednesday": {}, "Thursday": {}, "Friday": {}, "Saturday": {}, "Sunday": {}},
    "Embedded Lab": {"Monday": {}, "Tuesday": {}, "Wednesday": {}, "Thursday": {}, "Friday": {}, "Saturday": {}, "Sunday": {}},
    "IOT Lab": {"Monday": {}, "Tuesday": {}, "Wednesday": {}, "Thursday": {}, "Friday": {}, "Saturday": {}, "Sunday": {}},
    "Multimedia Lab": {"Monday": {}, "Tuesday": {}, "Wednesday": {}, "Thursday": {}, "Friday": {}, "Saturday": {}, "Sunday": {}},
    "Network Lab": {"Monday": {}, "Tuesday": {}, "Wednesday": {}, "Thursday": {}, "Friday": {}, "Saturday": {}, "Sunday": {}},
}

# In-memory storage for bookings (in production, use database)
bookings = []

@router.get("/schedule", response_class=HTMLResponse)
def get_schedule(request: Request):
    return templates.TemplateResponse("schedule.html", {"request": request})


@router.get("/api/schedule/{lab}")
def get_lab_schedule(lab: str):
    """Get schedule data for a specific lab or all labs"""
    if lab == "all":
        # Combine all labs' schedules
        combined_schedule = {}
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        
        for day in days:
            combined_schedule[day] = {}
            for lab_name, lab_schedule in SCHEDULE_DATA.items():
                for time, data in lab_schedule.get(day, {}).items():
                    if time not in combined_schedule[day]:
                        combined_schedule[day][time] = data
        return combined_schedule
    
    # Try exact match first
    if lab in SCHEDULE_DATA:
        return SCHEDULE_DATA[lab]
    
    # Try case-insensitive match
    for lab_name, lab_schedule in SCHEDULE_DATA.items():
        if lab_name.lower() == lab.lower():
            return lab_schedule
    
    # Return empty schedule if lab not found
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
        "date": booking.date,
        "time": booking.time,
        "created_at": datetime.now().isoformat(),
        "status": "pending",
    }
    bookings.append(booking_data)
    return {"message": "Booking created successfully", "booking": booking_data}
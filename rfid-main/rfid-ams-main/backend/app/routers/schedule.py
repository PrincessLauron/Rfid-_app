from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
import re

router = APIRouter()
templates = Jinja2Templates(directory="backend/app/templates")

# Booking model
class BookingRequest(BaseModel):
    full_name: str
    id_number: str
    college: Optional[str] = ""
    department: str
    lab: str
    date: str
    time: str
    time_end: Optional[str] = None
    reason: Optional[str] = ""

# Schedule model for adding new classes
class ScheduleRequest(BaseModel):
    code: str
    section: str
    date: str
    time_start: str
    time_end: str
    lab: str
    instructor: str

# Sample schedule data for each lab - starts empty so new entries are added manually
LAB_NAMES = [
    "CS Lab",
    "Embedded Lab",
    "Multimedia Lab",
    "IOT Lab",
    "Network Lab",
    "Database Lab",
]

DAYS_OF_WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

SCHEDULE_DATA = {
    lab: {day: {} for day in DAYS_OF_WEEK}
    for lab in LAB_NAMES
}

# In-memory storage for bookings (in production, use database)
bookings = []

@router.get("/schedule", response_class=HTMLResponse)
def get_schedule(request: Request):
    return templates.TemplateResponse("schedule.html", {"request": request})


def normalize_lab_name(lab: str):
    lab_mapping = {
        "CS Lab": "CS Lab",
        "CS Laboratory": "CS Lab",
        "Embedded Lab": "Embedded Lab",
        "Embedded Laboratory": "Embedded Lab",
        "Multimedia Lab": "Multimedia Lab",
        "Multimedia Laboratory": "Multimedia Lab",
        "IOT Lab": "IOT Lab",
        "IOT Laboratory": "IOT Lab",
        "Network Lab": "Network Lab",
        "Network Laboratory": "Network Lab",
        "Network laboratory": "Network Lab",
        "Database Lab": "Database Lab",
        "Database Laboratory": "Database Lab",
        "Database laboratory": "Database Lab",
    }
    return lab_mapping.get(lab, lab)


def format_time_slot(time_str: str):
    time_str = time_str.strip()
    try:
        if re.search(r'(AM|PM)$', time_str, re.IGNORECASE):
            dt_obj = datetime.strptime(time_str.upper(), "%I:%M%p")
        else:
            dt_obj = datetime.strptime(time_str, "%H:%M")
    except Exception:
        return time_str

    hour = dt_obj.hour
    minute = dt_obj.minute
    period = "AM" if hour < 12 else "PM"
    display_hour = hour if hour <= 12 else hour - 12
    if display_hour == 0:
        display_hour = 12
    return f"{display_hour:02d}:{minute:02d}{period}"


@router.get("/api/schedule/{lab}")
def get_lab_schedule(lab: str):
    """Get schedule data for a specific lab or all labs"""
    normalized_lab = normalize_lab_name(lab)
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    if lab == "all":
        combined_schedule = {day: {} for day in days}
        for day in days:
            for lab_name, lab_schedule in SCHEDULE_DATA.items():
                for time, data in lab_schedule.get(day, {}).items():
                    if time not in combined_schedule[day]:
                        combined_schedule[day][time] = data
        schedule = combined_schedule
    else:
        if normalized_lab in SCHEDULE_DATA:
            schedule = {day: dict(entries) for day, entries in SCHEDULE_DATA[normalized_lab].items()}
        else:
            schedule = {day: {} for day in days}

    # Add booking entries to the schedule view
    for booking in bookings:
        booking_lab = normalize_lab_name(booking.get("lab", ""))
        if lab != "all" and booking_lab != normalized_lab:
            continue

        booking_date = booking.get("date", "")
        try:
            if '-' in booking_date:
                dt_obj = datetime.strptime(booking_date, "%Y-%m-%d")
            else:
                dt_obj = datetime.strptime(booking_date, "%d/%m/%Y")
            day_name = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][dt_obj.weekday()]
        except Exception:
            continue

        time_slot = format_time_slot(booking.get("time", ""))
        if day_name not in schedule:
            schedule[day_name] = {}

        schedule[day_name][time_slot] = {
            "code": "BOOK",
            "title": booking.get("reason") or "Lab Booking",
            "instructor": booking.get("full_name"),
            "dept": booking.get("department"),
            "type": "booking",
            "color": "#ecfdf5",
            "duration": 1,
        }

    return schedule


@router.get("/api/schedule/debug/all")
def debug_all_schedules():
    """Debug endpoint to see all stored schedules"""
    return {
        "all_schedules": SCHEDULE_DATA,
        "total_labs": len(SCHEDULE_DATA),
        "labs": list(SCHEDULE_DATA.keys())
    }


@router.post("/api/bookings")
async def create_booking(booking: BookingRequest):
    """Create a new lab booking"""
    booking_data = {
        "id": len(bookings) + 1,
        "full_name": booking.full_name,
        "id_number": booking.id_number,
        "college": booking.college,
        "department": booking.department,
        "lab": normalize_lab_name(booking.lab),
        "date": booking.date,
        "time": booking.time,
        "time_end": booking.time_end or booking.time,
        "reason": booking.reason or "",
        "created_at": datetime.now().isoformat(),
        "status": "pending",
    }
    bookings.append(booking_data)
    return {"message": "Booking created successfully", "booking": booking_data}


@router.post("/api/schedule/add")
async def add_schedule(schedule: ScheduleRequest):
    """Add a new schedule entry to a laboratory"""
    from datetime import datetime as dt
    
    try:
        # Parse the date - HTML date input returns ISO format (YYYY-MM-DD)
        if len(schedule.date.split('-')) == 3:  # ISO format
            date_obj = dt.strptime(schedule.date, "%Y-%m-%d")
        else:  # DD/MM/YYYY format
            date_obj = dt.strptime(schedule.date, "%d/%m/%Y")
        
        day_name = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][date_obj.weekday()]
        
        # Parse time - HTML time input returns HH:mm in 24-hour format
        time_parts = schedule.time_start.split(':')
        hour = int(time_parts[0])
        minute = int(time_parts[1]) if len(time_parts) > 1 else 0
        
        # Convert to 12-hour format with AM/PM
        period = "AM" if hour < 12 else "PM"
        display_hour = hour if hour <= 12 else hour - 12
        if display_hour == 0:
            display_hour = 12
        
        # Format time slot as stored in SCHEDULE_DATA
        time_slot = f"{display_hour:02d}:{minute:02d}{period}"
        
        # Parse end time to calculate duration
        end_parts = schedule.time_end.split(':')
        end_hour = int(end_parts[0])
        end_minute = int(end_parts[1]) if len(end_parts) > 1 else 0
        
        # Calculate duration in 30-minute slots
        start_mins = hour * 60 + minute
        end_mins = end_hour * 60 + end_minute
        duration = max(1, max(1, (end_mins - start_mins + 29) // 30))  # Round up
        
        # Generate a color for the schedule
        colors = ["#E8D5F2", "#FFE4C4", "#C0E0FF", "#CCFF99", "#FFFF99", "#E6D7F0", 
                  "#FFD9B3", "#D9E8FF", "#E8F5E9", "#F0E8D9", "#CCFFFF", "#FFD9FF"]
        
        # Normalize lab name - remove "Laboratory" suffix if present
        lab = schedule.lab
        if not lab:
            return {"error": "Laboratory not selected", "status": "error"}
        
        # Map lab display names to backend names
        lab_mapping = {
            "CS Lab": "CS Lab",
            "CS Laboratory": "CS Lab",
            "Embedded Lab": "Embedded Lab",
            "Embedded Laboratory": "Embedded Lab",
            "Multimedia Lab": "Multimedia Lab",
            "Multimedia Laboratory": "Multimedia Lab",
            "IOT Lab": "IOT Lab",
            "IOT Laboratory": "IOT Lab",
            "Network Lab": "Network Lab",
            "Network Laboratory": "Network Lab",
            "Network laboratory": "Network Lab",
            "Database Lab": "Database Lab",
            "Database Laboratory": "Database Lab",
            "Database laboratory": "Database Lab",
        }
        
        lab = lab_mapping.get(lab, lab)
        
        # Initialize lab schedule if not exists
        if lab not in SCHEDULE_DATA:
            SCHEDULE_DATA[lab] = {day: {} for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]}
        
        if day_name not in SCHEDULE_DATA[lab]:
            SCHEDULE_DATA[lab][day_name] = {}
        
        # Check for conflicts
        if time_slot in SCHEDULE_DATA[lab][day_name]:
            return {"error": "Time slot already occupied", "status": "conflict"}
        
        # Get color based on number of entries
        color_idx = len(SCHEDULE_DATA[lab][day_name]) % len(colors)
        color = colors[color_idx]
        
        # Add the schedule entry
        SCHEDULE_DATA[lab][day_name][time_slot] = {
            "code": schedule.code,
            "title": schedule.section,
            "section": schedule.section,
            "building": lab,
            "instructor": schedule.instructor,
            "dept": "Schedule",
            "color": color,
            "duration": duration,
            "type": "regular"
        }
        
        return {
            "message": "Schedule added successfully",
            "schedule": {
                "code": schedule.code,
                "section": schedule.section,
                "day": day_name,
                "time": time_slot,
                "lab": lab,
                "instructor": schedule.instructor,
                "duration": duration
            }
        }
    except Exception as e:
        return {"error": f"Error processing schedule: {str(e)}", "status": "error"}


@router.post("/api/schedule/clear-all")
async def clear_all_schedules():
    """Clear all schedule entries and bookings from all laboratories"""
    try:
        # Clear all schedule data for all labs
        for lab_name in SCHEDULE_DATA:
            for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]:
                SCHEDULE_DATA[lab_name][day] = {}
        
        # Clear all bookings
        bookings.clear()
        
        return {
            "status": "success",
            "message": "All schedule data and bookings have been cleared from all laboratories",
            "labs_cleared": list(SCHEDULE_DATA.keys()),
            "bookings_cleared": True
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error clearing schedules: {str(e)}"
        }
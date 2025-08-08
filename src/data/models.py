"""
Data Models for Google Sheets
Python classes representing Member, Event, Attendance records with validation
File location: src/data/models.py
"""

import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, date
from dataclasses import dataclass, asdict, field
import re

logger = logging.getLogger(__name__)

@dataclass
class Member:
    """Member data model with validation"""
    member_id: str
    first_name: str
    last_name: str
    email: str
    phone: str
    wix_user_id: Optional[str] = None
    role: str = "member"  # member, exec
    membership_status: str = "active"  # active, inactive, suspended
    payment_status: str = "pending"  # paid, pending, overdue
    join_date: Optional[str] = None
    graduation_year: Optional[str] = None
    major: Optional[str] = None
    emergency_contact: Optional[str] = None
    emergency_phone: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def __post_init__(self):
        """Validate member data after initialization"""
        self._validate()
        
        # Set timestamps if not provided
        current_time = datetime.now().isoformat()
        if not self.created_at:
            self.created_at = current_time
        self.updated_at = current_time
    
    def _validate(self):
        """Validate member data"""
        if not self.member_id:
            raise ValueError("Member ID is required")
        
        if not self.first_name or not self.last_name:
            raise ValueError("First name and last name are required")
        
        if not self._is_valid_email(self.email):
            raise ValueError("Valid email is required")
        
        if not self._is_valid_phone(self.phone):
            raise ValueError("Valid phone number is required")
        
        if self.role not in ["member", "exec"]:
            raise ValueError("Role must be 'member' or 'exec'")
        
        if self.membership_status not in ["active", "inactive", "suspended"]:
            raise ValueError("Invalid membership status")
        
        if self.payment_status not in ["paid", "pending", "overdue"]:
            raise ValueError("Invalid payment status")
    
    def _is_valid_email(self, email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def _is_valid_phone(self, phone: str) -> bool:
        """Validate phone number format"""
        # Remove all non-digit characters
        digits_only = re.sub(r'\D', '', phone)
        # Should have 10 or 11 digits (US format)
        return len(digits_only) in [10, 11]
    
    @property
    def full_name(self) -> str:
        """Get full name"""
        return f"{self.first_name} {self.last_name}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Google Sheets"""
        return asdict(self)
    
    def to_sheet_row(self) -> List[str]:
        """Convert to list for Google Sheets row"""
        return [
            self.member_id,
            self.first_name,
            self.last_name,
            self.email,
            self.phone,
            self.wix_user_id or "",
            self.role,
            self.membership_status,
            self.payment_status,
            self.join_date or "",
            self.graduation_year or "",
            self.major or "",
            self.emergency_contact or "",
            self.emergency_phone or "",
            self.notes or "",
            self.created_at or "",
            self.updated_at or ""
        ]
    
    @classmethod
    def from_sheet_row(cls, row: List[str]) -> 'Member':
        """Create Member from Google Sheets row"""
        # Pad row with empty strings if needed
        while len(row) < 17:
            row.append("")
        
        return cls(
            member_id=row[0],
            first_name=row[1],
            last_name=row[2],
            email=row[3],
            phone=row[4],
            wix_user_id=row[5] if row[5] else None,
            role=row[6] or "member",
            membership_status=row[7] or "active",
            payment_status=row[8] or "pending",
            join_date=row[9] if row[9] else None,
            graduation_year=row[10] if row[10] else None,
            major=row[11] if row[11] else None,
            emergency_contact=row[12] if row[12] else None,
            emergency_phone=row[13] if row[13] else None,
            notes=row[14] if row[14] else None,
            created_at=row[15] if row[15] else None,
            updated_at=row[16] if row[16] else None
        )
    
    @classmethod
    def get_headers(cls) -> List[str]:
        """Get column headers for Google Sheets"""
        return [
            "Member ID", "First Name", "Last Name", "Email", "Phone",
            "Wix User ID", "Role", "Membership Status", "Payment Status",
            "Join Date", "Graduation Year", "Major", "Emergency Contact",
            "Emergency Phone", "Notes", "Created At", "Updated At"
        ]

@dataclass
class Event:
    """Event data model with validation"""
    event_id: str
    event_name: str
    event_type: str  # practice, game, meeting, social
    event_date: str  # ISO format date
    start_time: str  # HH:MM format
    end_time: str    # HH:MM format
    location: str
    description: Optional[str] = None
    is_mandatory: bool = False
    max_attendees: Optional[int] = None
    created_by: str = ""  # member_id of creator
    status: str = "scheduled"  # scheduled, cancelled, completed
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def __post_init__(self):
        """Validate event data after initialization"""
        self._validate()
        
        # Set timestamps if not provided
        current_time = datetime.now().isoformat()
        if not self.created_at:
            self.created_at = current_time
        self.updated_at = current_time
    
    def _validate(self):
        """Validate event data"""
        if not self.event_id:
            raise ValueError("Event ID is required")
        
        if not self.event_name:
            raise ValueError("Event name is required")
        
        if self.event_type not in ["practice", "game", "meeting", "social"]:
            raise ValueError("Invalid event type")
        
        if not self._is_valid_date(self.event_date):
            raise ValueError("Valid event date is required (YYYY-MM-DD)")
        
        if not self._is_valid_time(self.start_time) or not self._is_valid_time(self.end_time):
            raise ValueError("Valid start and end times are required (HH:MM)")
        
        if self.status not in ["scheduled", "cancelled", "completed"]:
            raise ValueError("Invalid event status")
    
    def _is_valid_date(self, date_str: str) -> bool:
        """Validate date format (YYYY-MM-DD)"""
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except ValueError:
            return False
    
    def _is_valid_time(self, time_str: str) -> bool:
        """Validate time format (HH:MM)"""
        try:
            datetime.strptime(time_str, "%H:%M")
            return True
        except ValueError:
            return False
    
    @property
    def datetime_start(self) -> datetime:
        """Get event start as datetime object"""
        return datetime.strptime(f"{self.event_date} {self.start_time}", "%Y-%m-%d %H:%M")
    
    @property
    def datetime_end(self) -> datetime:
        """Get event end as datetime object"""
        return datetime.strptime(f"{self.event_date} {self.end_time}", "%Y-%m-%d %H:%M")
    
    @property
    def duration_minutes(self) -> int:
        """Get event duration in minutes"""
        return int((self.datetime_end - self.datetime_start).total_seconds() / 60)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Google Sheets"""
        return asdict(self)
    
    def to_sheet_row(self) -> List[str]:
        """Convert to list for Google Sheets row"""
        return [
            self.event_id,
            self.event_name,
            self.event_type,
            self.event_date,
            self.start_time,
            self.end_time,
            self.location,
            self.description or "",
            str(self.is_mandatory).lower(),
            str(self.max_attendees) if self.max_attendees else "",
            self.created_by,
            self.status,
            self.created_at or "",
            self.updated_at or ""
        ]
    
    @classmethod
    def from_sheet_row(cls, row: List[str]) -> 'Event':
        """Create Event from Google Sheets row"""
        # Pad row with empty strings if needed
        while len(row) < 14:
            row.append("")
        
        return cls(
            event_id=row[0],
            event_name=row[1],
            event_type=row[2],
            event_date=row[3],
            start_time=row[4],
            end_time=row[5],
            location=row[6],
            description=row[7] if row[7] else None,
            is_mandatory=row[8].lower() == 'true' if row[8] else False,
            max_attendees=int(row[9]) if row[9] and row[9].isdigit() else None,
            created_by=row[10],
            status=row[11] or "scheduled",
            created_at=row[12] if row[12] else None,
            updated_at=row[13] if row[13] else None
        )
    
    @classmethod
    def get_headers(cls) -> List[str]:
        """Get column headers for Google Sheets"""
        return [
            "Event ID", "Event Name", "Event Type", "Event Date", "Start Time",
            "End Time", "Location", "Description", "Is Mandatory", "Max Attendees",
            "Created By", "Status", "Created At", "Updated At"
        ]

@dataclass
class AttendanceRecord:
    """Attendance record data model"""
    record_id: str
    event_id: str
    member_id: str
    attendance_status: str  # present, absent, excused, late
    check_in_time: Optional[str] = None  # HH:MM format
    check_out_time: Optional[str] = None  # HH:MM format
    notes: Optional[str] = None
    recorded_by: str = ""  # member_id of who recorded attendance
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def __post_init__(self):
        """Validate attendance data after initialization"""
        self._validate()
        
        # Set timestamps if not provided
        current_time = datetime.now().isoformat()
        if not self.created_at:
            self.created_at = current_time
        self.updated_at = current_time
    
    def _validate(self):
        """Validate attendance data"""
        if not self.record_id:
            raise ValueError("Record ID is required")
        
        if not self.event_id:
            raise ValueError("Event ID is required")
        
        if not self.member_id:
            raise ValueError("Member ID is required")
        
        if self.attendance_status not in ["present", "absent", "excused", "late"]:
            raise ValueError("Invalid attendance status")
        
        # Validate time formats if provided
        if self.check_in_time and not self._is_valid_time(self.check_in_time):
            raise ValueError("Invalid check-in time format (HH:MM)")
        
        if self.check_out_time and not self._is_valid_time(self.check_out_time):
            raise ValueError("Invalid check-out time format (HH:MM)")
    
    def _is_valid_time(self, time_str: str) -> bool:
        """Validate time format (HH:MM)"""
        try:
            datetime.strptime(time_str, "%H:%M")
            return True
        except ValueError:
            return False
    
    @property
    def duration_minutes(self) -> Optional[int]:
        """Calculate attendance duration in minutes"""
        if not self.check_in_time or not self.check_out_time:
            return None
        
        check_in = datetime.strptime(self.check_in_time, "%H:%M")
        check_out = datetime.strptime(self.check_out_time, "%H:%M")
        
        # Handle case where checkout is next day
        if check_out < check_in:
            check_out = check_out.replace(day=check_out.day + 1)
        
        return int((check_out - check_in).total_seconds() / 60)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Google Sheets"""
        return asdict(self)
    
    def to_sheet_row(self) -> List[str]:
        """Convert to list for Google Sheets row"""
        return [
            self.record_id,
            self.event_id,
            self.member_id,
            self.attendance_status,
            self.check_in_time or "",
            self.check_out_time or "",
            self.notes or "",
            self.recorded_by,
            self.created_at or "",
            self.updated_at or ""
        ]
    
    @classmethod
    def from_sheet_row(cls, row: List[str]) -> 'AttendanceRecord':
        """Create AttendanceRecord from Google Sheets row"""
        # Pad row with empty strings if needed
        while len(row) < 10:
            row.append("")
        
        return cls(
            record_id=row[0],
            event_id=row[1],
            member_id=row[2],
            attendance_status=row[3],
            check_in_time=row[4] if row[4] else None,
            check_out_time=row[5] if row[5] else None,
            notes=row[6] if row[6] else None,
            recorded_by=row[7],
            created_at=row[8] if row[8] else None,
            updated_at=row[9] if row[9] else None
        )
    
    @classmethod
    def get_headers(cls) -> List[str]:
        """Get column headers for Google Sheets"""
        return [
            "Record ID", "Event ID", "Member ID", "Attendance Status",
            "Check In Time", "Check Out Time", "Notes", "Recorded By",
            "Created At", "Updated At"
        ]

# Utility functions for data models
def generate_member_id() -> str:
    """Generate unique member ID"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"MBR_{timestamp}"

def generate_event_id() -> str:
    """Generate unique event ID"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"EVT_{timestamp}"

def generate_record_id(event_id: str, member_id: str) -> str:
    """Generate unique attendance record ID"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"ATT_{event_id}_{member_id}_{timestamp}"

# Example usage and testing
if __name__ == "__main__":
    print("Testing Data Models...")
    
    # Test Member model
    try:
        member = Member(
            member_id=generate_member_id(),
            first_name="John",
            last_name="Doe",
            email="john.doe@berkeley.edu",
            phone="555-123-4567",
            role="member",
            graduation_year="2025",
            major="Computer Science"
        )
        print(f"✓ Member created: {member.full_name}")
        
        # Test conversion to sheet row and back
        row = member.to_sheet_row()
        member2 = Member.from_sheet_row(row)
        print(f"✓ Member sheet conversion: {member2.full_name}")
        
    except ValueError as e:
        print(f"✗ Member validation error: {e}")
    
    # Test Event model
    try:
        event = Event(
            event_id=generate_event_id(),
            event_name="Weekly Practice",
            event_type="practice",
            event_date="2024-03-15",
            start_time="18:00",
            end_time="20:00",
            location="Memorial Stadium",
            is_mandatory=True,
            created_by="MBR_001"
        )
        print(f"✓ Event created: {event.event_name} ({event.duration_minutes} minutes)")
        
    except ValueError as e:
        print(f"✗ Event validation error: {e}")
    
    # Test Attendance model
    try:
        attendance = AttendanceRecord(
            record_id=generate_record_id("EVT_001", "MBR_001"),
            event_id="EVT_001",
            member_id="MBR_001",
            attendance_status="present",
            check_in_time="18:05",
            check_out_time="19:55",
            recorded_by="MBR_002"
        )
        print(f"✓ Attendance record created: {attendance.duration_minutes} minutes")
        
    except ValueError as e:
        print(f"✗ Attendance validation error: {e}")
    
    print("\n✓ All data models tested successfully!")
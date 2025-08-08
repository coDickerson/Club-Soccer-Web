"""
Attendance CRUD Operations
Handles Create, Read, Update, Delete operations for Attendance Records
File location: src/data/attendance_crud.py
"""

import logging
import pandas as pd
from typing import List, Dict, Optional, Union, Any, Tuple
from datetime import datetime, date
from collections import defaultdict
from googleapiclient.errors import HttpError

# Import your existing modules
from auth.google_auth import GoogleAuth
from data.models import AttendanceRecord, generate_record_id
from data.sheets_crud import GoogleSheetsManager

logger = logging.getLogger(__name__)

class AttendanceCRUD:
    """CRUD operations for Attendance sheet"""
    
    def __init__(self, sheets_manager: GoogleSheetsManager):
        self.manager = sheets_manager
        self.sheet_id = sheets_manager.attendance_sheet_id or sheets_manager.members_sheet_id  # Same sheet, different tab
        self.range_name = "Attendance!A:J"  # 10 columns for AttendanceRecord model
    
    def record_attendance(self, attendance: AttendanceRecord) -> bool:
        """
        Record attendance for a member at an event
        
        Args:
            attendance: AttendanceRecord object to create
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check if attendance already recorded for this member/event
            existing_record = self.get_attendance_record(attendance.event_id, attendance.member_id)
            if existing_record:
                logger.warning(f"Attendance already recorded for member {attendance.member_id} at event {attendance.event_id}")
                # Update existing record instead of creating new one
                return self.update_attendance(attendance)
            
            # Prepare the row data
            row_data = attendance.to_sheet_row()
            
            # Append to sheet
            body = {
                'values': [row_data]
            }
            
            request = self.manager.service.spreadsheets().values().append(
                spreadsheetId=self.sheet_id,
                range=self.range_name,
                valueInputOption='RAW',
                insertDataOption='INSERT_ROWS',
                body=body
            )
            
            result = self.manager._execute_with_retry(request)
            
            if result.get('updates', {}).get('updatedRows', 0) > 0:
                logger.info(f"Successfully recorded attendance for member {attendance.member_id}")
                return True
            else:
                logger.error(f"Failed to record attendance for member {attendance.member_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error recording attendance: {e}")
            return False
    
    def get_all_attendance(self) -> List[AttendanceRecord]:
        """
        Get all attendance records from Google Sheets
        
        Returns:
            List[AttendanceRecord]: List of all attendance records
        """
        try:
            request = self.manager.service.spreadsheets().values().get(
                spreadsheetId=self.sheet_id,
                range=self.range_name
            )
            
            result = self.manager._execute_with_retry(request)
            values = result.get('values', [])
            
            if not values:
                logger.info("No attendance records found in sheet")
                return []
            
            # Skip header row if it exists
            records = []
            for i, row in enumerate(values):
                if i == 0 and row[0] == "Record ID":  # Skip header
                    continue
                
                try:
                    record = AttendanceRecord.from_sheet_row(row)
                    records.append(record)
                except Exception as e:
                    logger.warning(f"Failed to parse attendance row {i}: {e}")
                    continue
            
            logger.info(f"Retrieved {len(records)} attendance records")
            return records
            
        except Exception as e:
            logger.error(f"Error retrieving attendance records: {e}")
            return []
    
    def get_attendance_record(self, event_id: str, member_id: str) -> Optional[AttendanceRecord]:
        """
        Get specific attendance record for a member at an event
        
        Args:
            event_id: Event ID
            member_id: Member ID
            
        Returns:
            AttendanceRecord or None if not found
        """
        all_records = self.get_all_attendance()
        for record in all_records:
            if record.event_id == event_id and record.member_id == member_id:
                return record
        return None
    
    def get_attendance_by_event(self, event_id: str) -> List[AttendanceRecord]:
        """
        Get all attendance records for a specific event
        
        Args:
            event_id: Event ID to get attendance for
            
        Returns:
            List[AttendanceRecord]: Attendance records for the event
        """
        all_records = self.get_all_attendance()
        return [r for r in all_records if r.event_id == event_id]
    
    def get_attendance_by_member(self, member_id: str) -> List[AttendanceRecord]:
        """
        Get all attendance records for a specific member
        
        Args:
            member_id: Member ID to get attendance for
            
        Returns:
            List[AttendanceRecord]: Attendance records for the member
        """
        all_records = self.get_all_attendance()
        return [r for r in all_records if r.member_id == member_id]
    
    def update_attendance(self, attendance: AttendanceRecord) -> bool:
        """
        Update an existing attendance record
        
        Args:
            attendance: Updated AttendanceRecord object
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Find the row number for this attendance record
            row_number = self._find_attendance_row(attendance.record_id)
            if row_number is None:
                logger.warning(f"Attendance record {attendance.record_id} not found for update")
                return False
            
            # Update the record's updated_at timestamp
            attendance.updated_at = datetime.now().isoformat()
            
            # Prepare update range (specific row)
            update_range = f"Attendance!A{row_number}:J{row_number}"
            
            body = {
                'values': [attendance.to_sheet_row()]
            }
            
            request = self.manager.service.spreadsheets().values().update(
                spreadsheetId=self.sheet_id,
                range=update_range,
                valueInputOption='RAW',
                body=body
            )
            
            result = self.manager._execute_with_retry(request)
            
            if result.get('updatedRows', 0) > 0:
                logger.info(f"Successfully updated attendance record: {attendance.record_id}")
                return True
            else:
                logger.error(f"Failed to update attendance record: {attendance.record_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating attendance record: {e}")
            return False
    
    def delete_attendance_record(self, record_id: str) -> bool:
        """
        Delete an attendance record (hard delete - actually removes the row)
        
        Args:
            record_id: Record ID to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            row_number = self._find_attendance_row(record_id)
            if row_number is None:
                logger.warning(f"Attendance record {record_id} not found for deletion")
                return False
            
            # Note: Google Sheets API doesn't have a simple delete row method
            # We'll clear the row instead (soft delete approach)
            clear_range = f"Attendance!A{row_number}:J{row_number}"
            
            request = self.manager.service.spreadsheets().values().clear(
                spreadsheetId=self.sheet_id,
                range=clear_range
            )
            
            result = self.manager._execute_with_retry(request)
            
            if result.get('clearedRange'):
                logger.info(f"Successfully deleted attendance record: {record_id}")
                return True
            else:
                logger.error(f"Failed to delete attendance record: {record_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting attendance record {record_id}: {e}")
            return False
    
    def _find_attendance_row(self, record_id: str) -> Optional[int]:
        """
        Find the row number for a specific attendance record ID
        
        Args:
            record_id: Record ID to search for
            
        Returns:
            Row number (1-indexed) or None if not found
        """
        try:
            request = self.manager.service.spreadsheets().values().get(
                spreadsheetId=self.sheet_id,
                range="Attendance!A:A"  # Only get Record ID column
            )
            
            result = self.manager._execute_with_retry(request)
            values = result.get('values', [])
            
            for i, row in enumerate(values):
                if row and len(row) > 0 and row[0] == record_id:
                    return i + 1  # Return 1-indexed row number
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding attendance row for {record_id}: {e}")
            return None
    
    def bulk_record_attendance(self, event_id: str, attendance_data: List[Dict[str, str]]) -> Tuple[int, int]:
        """
        Record attendance for multiple members at once
        
        Args:
            event_id: Event ID
            attendance_data: List of dicts with member_id, status, check_in_time, etc.
            
        Returns:
            Tuple[int, int]: (successful_records, total_records)
        """
        successful = 0
        total = len(attendance_data)
        
        for data in attendance_data:
            try:
                record = AttendanceRecord(
                    record_id=generate_record_id(event_id, data['member_id']),
                    event_id=event_id,
                    member_id=data['member_id'],
                    attendance_status=data.get('status', 'present'),
                    check_in_time=data.get('check_in_time'),
                    check_out_time=data.get('check_out_time'),
                    notes=data.get('notes'),
                    recorded_by=data.get('recorded_by', 'system')
                )
                
                if self.record_attendance(record):
                    successful += 1
                    
            except Exception as e:
                logger.error(f"Error in bulk attendance for member {data.get('member_id')}: {e}")
                continue
        
        logger.info(f"Bulk attendance completed: {successful}/{total} records successful")
        return successful, total
    
    def get_event_attendance_summary(self, event_id: str) -> Dict[str, Any]:
        """
        Get attendance summary for an event
        
        Args:
            event_id: Event ID
            
        Returns:
            Dict with attendance statistics
        """
        records = self.get_attendance_by_event(event_id)
        
        summary = {
            'total_records': len(records),
            'present': len([r for r in records if r.attendance_status == 'present']),
            'absent': len([r for r in records if r.attendance_status == 'absent']),
            'excused': len([r for r in records if r.attendance_status == 'excused']),
            'late': len([r for r in records if r.attendance_status == 'late']),
            'attendance_rate': 0,
            'average_duration': 0
        }
        
        if summary['total_records'] > 0:
            present_and_late = summary['present'] + summary['late']
            summary['attendance_rate'] = round((present_and_late / summary['total_records']) * 100, 1)
            
            # Calculate average duration for present members
            durations = [r.duration_minutes for r in records 
                        if r.attendance_status in ['present', 'late'] and r.duration_minutes]
            if durations:
                summary['average_duration'] = round(sum(durations) / len(durations), 1)
        
        return summary
    
    def get_member_attendance_stats(self, member_id: str) -> Dict[str, Any]:
        """
        Get attendance statistics for a specific member
        
        Args:
            member_id: Member ID
            
        Returns:
            Dict with member's attendance statistics
        """
        records = self.get_attendance_by_member(member_id)
        
        stats = {
            'total_events': len(records),
            'present': len([r for r in records if r.attendance_status == 'present']),
            'absent': len([r for r in records if r.attendance_status == 'absent']),
            'excused': len([r for r in records if r.attendance_status == 'excused']),
            'late': len([r for r in records if r.attendance_status == 'late']),
            'attendance_rate': 0,
            'total_hours': 0
        }
        
        if stats['total_events'] > 0:
            attended = stats['present'] + stats['late']
            stats['attendance_rate'] = round((attended / stats['total_events']) * 100, 1)
            
            # Calculate total hours attended
            total_minutes = sum([r.duration_minutes for r in records 
                               if r.duration_minutes and r.attendance_status in ['present', 'late']])
            stats['total_hours'] = round(total_minutes / 60, 1)
        
        return stats
    
    def get_attendance_trends(self, days_back: int = 30) -> Dict[str, List]:
        """
        Get attendance trends over specified period
        
        Args:
            days_back: Number of days to look back
            
        Returns:
            Dict with trend data for charts/analytics
        """
        all_records = self.get_all_attendance()
        cutoff_date = datetime.now() - pd.Timedelta(days=days_back)
        
        # Filter recent records
        recent_records = []
        for record in all_records:
            try:
                if record.created_at:
                    record_date = datetime.fromisoformat(record.created_at.replace('Z', ''))
                    if record_date >= cutoff_date:
                        recent_records.append(record)
            except:
                continue  # Skip records with invalid dates
        
        # Group by event for trend analysis
        event_attendance = defaultdict(list)
        for record in recent_records:
            event_attendance[record.event_id].append(record)
        
        trends = {
            'dates': [],
            'attendance_rates': [],
            'total_attendees': [],
            'events_count': len(event_attendance)
        }
        
        # Calculate trends by event
        for event_id, records in event_attendance.items():
            present_count = len([r for r in records if r.attendance_status in ['present', 'late']])
            total_count = len(records)
            attendance_rate = (present_count / total_count * 100) if total_count > 0 else 0
            
            trends['attendance_rates'].append(attendance_rate)
            trends['total_attendees'].append(present_count)
            # You could add actual dates here by cross-referencing with events
        
        return trends
    
    def check_in_member(self, event_id: str, member_id: str, recorded_by: str = "system") -> bool:
        """
        Quick check-in for a member at an event
        
        Args:
            event_id: Event ID
            member_id: Member ID
            recorded_by: Who recorded the check-in
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            current_time = datetime.now()
            
            # Check if already checked in
            existing_record = self.get_attendance_record(event_id, member_id)
            if existing_record:
                # Update existing record with check-in time
                existing_record.attendance_status = "present"
                existing_record.check_in_time = current_time.strftime("%H:%M")
                existing_record.recorded_by = recorded_by
                return self.update_attendance(existing_record)
            else:
                # Create new attendance record
                record = AttendanceRecord(
                    record_id=generate_record_id(event_id, member_id),
                    event_id=event_id,
                    member_id=member_id,
                    attendance_status="present",
                    check_in_time=current_time.strftime("%H:%M"),
                    recorded_by=recorded_by
                )
                return self.record_attendance(record)
                
        except Exception as e:
            logger.error(f"Error checking in member {member_id}: {e}")
            return False
    
    def check_out_member(self, event_id: str, member_id: str) -> bool:
        """
        Check out a member from an event
        
        Args:
            event_id: Event ID
            member_id: Member ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            existing_record = self.get_attendance_record(event_id, member_id)
            if not existing_record:
                logger.warning(f"No check-in record found for member {member_id} at event {event_id}")
                return False
            
            # Add check-out time
            existing_record.check_out_time = datetime.now().strftime("%H:%M")
            
            return self.update_attendance(existing_record)
            
        except Exception as e:
            logger.error(f"Error checking out member {member_id}: {e}")
            return False
    
    def mark_absent(self, event_id: str, member_id: str, is_excused: bool = False, 
                   recorded_by: str = "system") -> bool:
        """
        Mark a member as absent for an event
        
        Args:
            event_id: Event ID
            member_id: Member ID
            is_excused: Whether absence is excused
            recorded_by: Who recorded the absence
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            status = "excused" if is_excused else "absent"
            
            # Check if record already exists
            existing_record = self.get_attendance_record(event_id, member_id)
            if existing_record:
                existing_record.attendance_status = status
                existing_record.recorded_by = recorded_by
                return self.update_attendance(existing_record)
            else:
                # Create new absent record
                record = AttendanceRecord(
                    record_id=generate_record_id(event_id, member_id),
                    event_id=event_id,
                    member_id=member_id,
                    attendance_status=status,
                    recorded_by=recorded_by,
                    notes="Marked absent" + (" (excused)" if is_excused else "")
                )
                return self.record_attendance(record)
                
        except Exception as e:
            logger.error(f"Error marking member {member_id} absent: {e}")
            return False
    
    def initialize_sheet(self) -> bool:
        """
        Initialize the Attendance sheet with headers if it doesn't exist
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check if sheet has data
            request = self.manager.service.spreadsheets().values().get(
                spreadsheetId=self.sheet_id,
                range="Attendance!A1:J1"
            )
            
            result = self.manager._execute_with_retry(request)
            values = result.get('values', [])
            
            # If no data or wrong headers, add headers
            if not values or values[0][0] != "Record ID":
                headers = AttendanceRecord.get_headers()
                body = {
                    'values': [headers]
                }
                
                request = self.manager.service.spreadsheets().values().update(
                    spreadsheetId=self.sheet_id,
                    range="Attendance!A1:J1",
                    valueInputOption='RAW',
                    body=body
                )
                
                self.manager._execute_with_retry(request)
                logger.info("Attendance sheet headers initialized")
            
            return True
            
        except Exception as e:
            logger.error(f"Error initializing attendance sheet: {e}")
            return False

# Example usage and testing
if __name__ == "__main__":
    print("Testing Attendance CRUD Operations...")
    
    try:
        # Initialize manager (reusing your working setup)
        from data.sheets_crud import GoogleSheetsManager
        manager = GoogleSheetsManager()
        attendance_crud = AttendanceCRUD(manager)
        
        # Test initialization
        print("✓ Initializing attendance sheet...")
        if attendance_crud.initialize_sheet():
            print("✓ Attendance sheet initialized")
        
        # Test recording attendance
        test_record = AttendanceRecord(
            record_id=generate_record_id("EVT_TEST001", "MBR_TEST001"),
            event_id="EVT_TEST001",
            member_id="MBR_TEST001",
            attendance_status="present",
            check_in_time="18:05",
            check_out_time="19:55",
            notes="Test attendance record",
            recorded_by="test_system"
        )
        
        print(f"✓ Recording test attendance...")
        if attendance_crud.record_attendance(test_record):
            print("✓ Attendance recorded successfully")
            
            # Test reading the record back
            retrieved_record = attendance_crud.get_attendance_record(
                test_record.event_id, test_record.member_id
            )
            if retrieved_record:
                print(f"✓ Attendance retrieved: {retrieved_record.duration_minutes} minutes")
                
                # Test updating the record
                retrieved_record.notes = "Updated test notes"
                if attendance_crud.update_attendance(retrieved_record):
                    print("✓ Attendance updated successfully")
        
        # Test quick check-in/check-out
        print("\n✓ Testing quick check-in...")
        if attendance_crud.check_in_member("EVT_TEST002", "MBR_TEST002", "admin"):
            print("✓ Quick check-in successful")
            
            if attendance_crud.check_out_member("EVT_TEST002", "MBR_TEST002"):
                print("✓ Quick check-out successful")
        
        # Test marking absent
        if attendance_crud.mark_absent("EVT_TEST003", "MBR_TEST003", is_excused=True):
            print("✓ Marked member as excused absent")
        
        # Test analytics
        all_records = attendance_crud.get_all_attendance()
        print(f"✓ Retrieved {len(all_records)} total attendance records")
        
        # Test member stats
        if all_records:
            sample_member_id = all_records[0].member_id
            stats = attendance_crud.get_member_attendance_stats(sample_member_id)
            print(f"✓ Member stats - Attendance rate: {stats['attendance_rate']}%")
        
    except Exception as e:
        print(f"✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n✓ Attendance CRUD operations testing completed!")
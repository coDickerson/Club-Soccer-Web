"""
Events CRUD Operations
Handles Create, Read, Update, Delete operations for Events
File location: src/data/events_crud.py
"""

import logging
import pandas as pd
from typing import List, Dict, Optional, Union, Any
from datetime import datetime, date, timedelta
from googleapiclient.errors import HttpError

# Import your existing modules
from auth.google_auth import GoogleAuth
from data.models import Event, generate_event_id
from data.sheets_crud import GoogleSheetsManager

logger = logging.getLogger(__name__)

class EventsCRUD:
    """CRUD operations for Events sheet"""
    
    def __init__(self, sheets_manager: GoogleSheetsManager):
        self.manager = sheets_manager
        self.sheet_id = sheets_manager.events_sheet_id or sheets_manager.members_sheet_id  # Same sheet, different tab
        self.range_name = "Events!A:N"  # 14 columns for Event model
    
    def create_event(self, event: Event) -> bool:
        """
        Create a new event in Google Sheets
        
        Args:
            event: Event object to create
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check if event already exists
            if self.get_event_by_id(event.event_id):
                logger.warning(f"Event {event.event_id} already exists")
                return False
            
            # Validate event doesn't conflict with existing events
            if self._check_event_conflict(event):
                logger.warning(f"Event {event.event_name} conflicts with existing event")
                return False
            
            # Prepare the row data
            row_data = event.to_sheet_row()
            
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
                logger.info(f"Successfully created event: {event.event_name}")
                return True
            else:
                logger.error(f"Failed to create event: {event.event_name}")
                return False
                
        except Exception as e:
            logger.error(f"Error creating event {event.event_name}: {e}")
            return False
    
    def get_all_events(self) -> List[Event]:
        """
        Get all events from Google Sheets
        
        Returns:
            List[Event]: List of all events
        """
        try:
            request = self.manager.service.spreadsheets().values().get(
                spreadsheetId=self.sheet_id,
                range=self.range_name
            )
            
            result = self.manager._execute_with_retry(request)
            values = result.get('values', [])
            
            if not values:
                logger.info("No events found in sheet")
                return []
            
            # Skip header row if it exists
            events = []
            for i, row in enumerate(values):
                if i == 0 and row[0] == "Event ID":  # Skip header
                    continue
                
                try:
                    event = Event.from_sheet_row(row)
                    events.append(event)
                except Exception as e:
                    logger.warning(f"Failed to parse event row {i}: {e}")
                    continue
            
            logger.info(f"Retrieved {len(events)} events")
            return events
            
        except Exception as e:
            logger.error(f"Error retrieving events: {e}")
            return []
    
    def get_event_by_id(self, event_id: str) -> Optional[Event]:
        """
        Get a specific event by ID
        
        Args:
            event_id: Event ID to search for
            
        Returns:
            Event object or None if not found
        """
        events = self.get_all_events()
        for event in events:
            if event.event_id == event_id:
                return event
        return None
    
    def update_event(self, event: Event) -> bool:
        """
        Update an existing event in Google Sheets
        
        Args:
            event: Updated Event object
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Find the row number for this event
            row_number = self._find_event_row(event.event_id)
            if row_number is None:
                logger.warning(f"Event {event.event_id} not found for update")
                return False
            
            # Update the event's updated_at timestamp
            event.updated_at = datetime.now().isoformat()
            
            # Prepare update range (specific row)
            update_range = f"Events!A{row_number}:N{row_number}"
            
            body = {
                'values': [event.to_sheet_row()]
            }
            
            request = self.manager.service.spreadsheets().values().update(
                spreadsheetId=self.sheet_id,
                range=update_range,
                valueInputOption='RAW',
                body=body
            )
            
            result = self.manager._execute_with_retry(request)
            
            if result.get('updatedRows', 0) > 0:
                logger.info(f"Successfully updated event: {event.event_name}")
                return True
            else:
                logger.error(f"Failed to update event: {event.event_name}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating event {event.event_name}: {e}")
            return False
    
    def delete_event(self, event_id: str) -> bool:
        """
        Delete an event from Google Sheets (soft delete by marking cancelled)
        
        Args:
            event_id: Event ID to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            event = self.get_event_by_id(event_id)
            if not event:
                logger.warning(f"Event {event_id} not found for deletion")
                return False
            
            # Soft delete: mark as cancelled instead of actually deleting
            event.status = "cancelled"
            event.updated_at = datetime.now().isoformat()
            
            success = self.update_event(event)
            if success:
                logger.info(f"Successfully deleted (marked cancelled) event: {event.event_name}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error deleting event {event_id}: {e}")
            return False
    
    def _find_event_row(self, event_id: str) -> Optional[int]:
        """
        Find the row number for a specific event ID
        
        Args:
            event_id: Event ID to search for
            
        Returns:
            Row number (1-indexed) or None if not found
        """
        try:
            request = self.manager.service.spreadsheets().values().get(
                spreadsheetId=self.sheet_id,
                range="Events!A:A"  # Only get Event ID column
            )
            
            result = self.manager._execute_with_retry(request)
            values = result.get('values', [])
            
            for i, row in enumerate(values):
                if row and len(row) > 0 and row[0] == event_id:
                    return i + 1  # Return 1-indexed row number
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding event row for {event_id}: {e}")
            return None
    
    def _check_event_conflict(self, new_event: Event) -> bool:
        """
        Check if new event conflicts with existing events (same time/location)
        
        Args:
            new_event: Event to check for conflicts
            
        Returns:
            bool: True if conflict exists, False otherwise
        """
        try:
            existing_events = self.get_events_by_date(new_event.event_date)
            
            for event in existing_events:
                # Skip cancelled events
                if event.status == "cancelled":
                    continue
                
                # Check for time overlap
                new_start = datetime.strptime(new_event.start_time, "%H:%M")
                new_end = datetime.strptime(new_event.end_time, "%H:%M")
                existing_start = datetime.strptime(event.start_time, "%H:%M")
                existing_end = datetime.strptime(event.end_time, "%H:%M")
                
                # Check if times overlap
                if (new_start < existing_end and new_end > existing_start):
                    logger.warning(f"Time conflict with event: {event.event_name}")
                    return True
            
            return False
            
        except Exception as e:
            logger.warning(f"Error checking event conflicts: {e}")
            return False  # Don't block creation on conflict check failure
    
    def get_events_by_date(self, event_date: str) -> List[Event]:
        """Get all events on a specific date"""
        all_events = self.get_all_events()
        return [e for e in all_events if e.event_date == event_date]
    
    def get_events_by_type(self, event_type: str) -> List[Event]:
        """Get events by type (practice, game, meeting, social)"""
        all_events = self.get_all_events()
        return [e for e in all_events if e.event_type == event_type]
    
    def get_upcoming_events(self, days_ahead: int = 30) -> List[Event]:
        """Get upcoming events within specified days"""
        all_events = self.get_all_events()
        today = datetime.now().date()
        cutoff_date = today + timedelta(days=days_ahead)
        
        upcoming = []
        for event in all_events:
            try:
                event_date = datetime.strptime(event.event_date, "%Y-%m-%d").date()
                if today <= event_date <= cutoff_date and event.status == "scheduled":
                    upcoming.append(event)
            except ValueError:
                continue  # Skip events with invalid dates
        
        # Sort by date and time
        upcoming.sort(key=lambda e: (e.event_date, e.start_time))
        return upcoming
    
    def get_events_by_status(self, status: str) -> List[Event]:
        """Get events by status (scheduled, cancelled, completed)"""
        all_events = self.get_all_events()
        return [e for e in all_events if e.status == status]
    
    def get_mandatory_events(self) -> List[Event]:
        """Get all mandatory events"""
        all_events = self.get_all_events()
        return [e for e in all_events if e.is_mandatory]
    
    def initialize_sheet(self) -> bool:
        """
        Initialize the Events sheet with headers if it doesn't exist
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check if sheet has data
            request = self.manager.service.spreadsheets().values().get(
                spreadsheetId=self.sheet_id,
                range="Events!A1:N1"
            )
            
            result = self.manager._execute_with_retry(request)
            values = result.get('values', [])
            
            # If no data or wrong headers, add headers
            if not values or values[0][0] != "Event ID":
                headers = Event.get_headers()
                body = {
                    'values': [headers]
                }
                
                request = self.manager.service.spreadsheets().values().update(
                    spreadsheetId=self.sheet_id,
                    range="Events!A1:N1",
                    valueInputOption='RAW',
                    body=body
                )
                
                self.manager._execute_with_retry(request)
                logger.info("Events sheet headers initialized")
            
            return True
            
        except Exception as e:
            logger.error(f"Error initializing events sheet: {e}")
            return False

# Example usage and testing
if __name__ == "__main__":
    print("Testing Events CRUD Operations...")
    
    try:
        # Initialize manager (reusing your working setup)
        from data.sheets_crud import GoogleSheetsManager
        manager = GoogleSheetsManager()
        events_crud = EventsCRUD(manager)
        
        # Test initialization
        print("✓ Initializing events sheet...")
        if events_crud.initialize_sheet():
            print("✓ Events sheet initialized")
        
        # Test creating an event
        test_event = Event(
            event_id=generate_event_id(),
            event_name="Test Practice Session",
            event_type="practice",
            event_date="2024-03-20",
            start_time="18:00",
            end_time="20:00",
            location="Memorial Stadium Field",
            description="Weekly practice session for skill development",
            is_mandatory=True,
            max_attendees=25,
            created_by="test_user",
            status="scheduled"
        )
        
        print(f"✓ Creating test event: {test_event.event_name}")
        if events_crud.create_event(test_event):
            print("✓ Event created successfully")
            
            # Test reading the event back
            retrieved_event = events_crud.get_event_by_id(test_event.event_id)
            if retrieved_event:
                print(f"✓ Event retrieved: {retrieved_event.event_name}")
                print(f"   Duration: {retrieved_event.duration_minutes} minutes")
                
                # Test updating the event
                retrieved_event.description = "Updated description with new details"
                if events_crud.update_event(retrieved_event):
                    print("✓ Event updated successfully")
                
                # Test soft delete
                if events_crud.delete_event(test_event.event_id):
                    print("✓ Event deleted (marked cancelled) successfully")
        
        # Test filtered reads
        all_events = events_crud.get_all_events()
        print(f"✓ Retrieved {len(all_events)} total events")
        
        upcoming_events = events_crud.get_upcoming_events(30)
        print(f"✓ Retrieved {len(upcoming_events)} upcoming events")
        
        practice_events = events_crud.get_events_by_type("practice")
        print(f"✓ Retrieved {len(practice_events)} practice events")
        
    except Exception as e:
        print(f"✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n✓ Events CRUD operations testing completed!")
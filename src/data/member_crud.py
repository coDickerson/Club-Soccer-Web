"""
Google Sheets CRUD Operations
Handles Create, Read, Update, Delete operations for Members, Events, and Attendance
File location: src/data/sheets_crud.py
"""

import logging
import time
from typing import List, Dict, Optional, Union, Any, Tuple
from googleapiclient.errors import HttpError
import pandas as pd

# Import your existing modules
from auth.google_auth import GoogleAuth, create_google_client
from data.models import Member, Event, AttendanceRecord
from configs import google_sheets_config

logger = logging.getLogger(__name__)

class GoogleSheetsManager:
    """Main class for managing Google Sheets CRUD operations"""
    
    def __init__(self, google_client: Optional[GoogleAuth] = None):
        """
        Initialize Google Sheets Manager
        
        Args:
            google_client: Authenticated GoogleAuth instance
        """
        self.client = google_client or create_google_client()
        if not self.client:
            raise ConnectionError("Failed to create Google Sheets client")
        
        self.service = self.client.get_service()
        if not self.service:
            raise ConnectionError("Failed to get Google Sheets service")
        
        # Sheet configurations from your config
        self.members_sheet_id = google_sheets_config.MEMBERS_SHEET_ID
        self.events_sheet_id = google_sheets_config.EVENTS_SHEET_ID
        self.attendance_sheet_id = google_sheets_config.ATTENDANCE_SHEET_ID
        
        # Default sheet names/tabs
        self.members_range = "Members!A:Q"  # A to Q columns (17 columns for Member)
        self.events_range = "Events!A:N"    # A to N columns (14 columns for Event)
        self.attendance_range = "Attendance!A:J"  # A to J columns (10 columns for Attendance)
        
        logger.info("GoogleSheetsManager initialized successfully")
    
    def _execute_with_retry(self, request, max_retries: int = 3, delay: float = 1.0):
        """
        Execute Google Sheets API request with retry logic
        
        Args:
            request: Google Sheets API request object
            max_retries: Maximum number of retry attempts
            delay: Delay between retries in seconds
            
        Returns:
            API response or raises exception
        """
        for attempt in range(max_retries + 1):
            try:
                return request.execute()
            
            except HttpError as e:
                if attempt == max_retries:
                    logger.error(f"Max retries exceeded: {e}")
                    raise
                
                if e.resp.status == 429:  # Rate limit exceeded
                    wait_time = delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(f"Rate limit hit, waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                elif e.resp.status in [500, 502, 503, 504]:  # Server errors
                    wait_time = delay * (2 ** attempt)
                    logger.warning(f"Server error {e.resp.status}, retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"HTTP Error {e.resp.status}: {e}")
                    raise
                    
            except Exception as e:
                if attempt == max_retries:
                    logger.error(f"Unexpected error: {e}")
                    raise
                logger.warning(f"Attempt {attempt + 1} failed: {e}, retrying...")
                time.sleep(delay)

class MembersCRUD:
    """CRUD operations for Members sheet"""
    
    def __init__(self, sheets_manager: GoogleSheetsManager):
        self.manager = sheets_manager
        self.sheet_id = sheets_manager.members_sheet_id
        self.range_name = sheets_manager.members_range
    
    def create_member(self, member: Member) -> bool:
        """
        Create a new member in Google Sheets
        
        Args:
            member: Member object to create
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check if member already exists
            if self.get_member_by_id(member.member_id):
                logger.warning(f"Member {member.member_id} already exists")
                return False
            
            # Prepare the row data
            row_data = member.to_sheet_row()
            
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
                logger.info(f"Successfully created member: {member.full_name}")
                return True
            else:
                logger.error(f"Failed to create member: {member.full_name}")
                return False
                
        except Exception as e:
            logger.error(f"Error creating member {member.full_name}: {e}")
            return False
    
    def get_all_members(self) -> List[Member]:
        """
        Get all members from Google Sheets
        
        Returns:
            List[Member]: List of all members
        """
        try:
            request = self.manager.service.spreadsheets().values().get(
                spreadsheetId=self.sheet_id,
                range=self.range_name
            )
            
            result = self.manager._execute_with_retry(request)
            values = result.get('values', [])
            
            if not values:
                logger.info("No members found in sheet")
                return []
            
            # Skip header row if it exists
            members = []
            for i, row in enumerate(values):
                if i == 0 and row[0] == "Member ID":  # Skip header
                    continue
                
                try:
                    member = Member.from_sheet_row(row)
                    members.append(member)
                except Exception as e:
                    logger.warning(f"Failed to parse member row {i}: {e}")
                    continue
            
            logger.info(f"Retrieved {len(members)} members")
            return members
            
        except Exception as e:
            logger.error(f"Error retrieving members: {e}")
            return []
    
    def get_member_by_id(self, member_id: str) -> Optional[Member]:
        """
        Get a specific member by ID
        
        Args:
            member_id: Member ID to search for
            
        Returns:
            Member object or None if not found
        """
        members = self.get_all_members()
        for member in members:
            if member.member_id == member_id:
                return member
        return None
    
    def update_member(self, member: Member) -> bool:
        """
        Update an existing member in Google Sheets
        
        Args:
            member: Updated Member object
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Find the row number for this member
            row_number = self._find_member_row(member.member_id)
            if row_number is None:
                logger.warning(f"Member {member.member_id} not found for update")
                return False
            
            # Update the member's updated_at timestamp
            member.updated_at = pd.Timestamp.now().isoformat()
            
            # Prepare update range (specific row)
            update_range = f"Members!A{row_number}:Q{row_number}"
            
            body = {
                'values': [member.to_sheet_row()]
            }
            
            request = self.manager.service.spreadsheets().values().update(
                spreadsheetId=self.sheet_id,
                range=update_range,
                valueInputOption='RAW',
                body=body
            )
            
            result = self.manager._execute_with_retry(request)
            
            if result.get('updatedRows', 0) > 0:
                logger.info(f"Successfully updated member: {member.full_name}")
                return True
            else:
                logger.error(f"Failed to update member: {member.full_name}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating member {member.full_name}: {e}")
            return False
    
    def delete_member(self, member_id: str) -> bool:
        """
        Delete a member from Google Sheets (soft delete by marking inactive)
        
        Args:
            member_id: Member ID to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            member = self.get_member_by_id(member_id)
            if not member:
                logger.warning(f"Member {member_id} not found for deletion")
                return False
            
            # Soft delete: mark as inactive instead of actually deleting
            member.membership_status = "inactive"
            member.updated_at = pd.Timestamp.now().isoformat()
            
            success = self.update_member(member)
            if success:
                logger.info(f"Successfully deleted (marked inactive) member: {member.full_name}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error deleting member {member_id}: {e}")
            return False
    
    def _find_member_row(self, member_id: str) -> Optional[int]:
        """
        Find the row number for a specific member ID
        
        Args:
            member_id: Member ID to search for
            
        Returns:
            Row number (1-indexed) or None if not found
        """
        try:
            request = self.manager.service.spreadsheets().values().get(
                spreadsheetId=self.sheet_id,
                range="Members!A:A"  # Only get Member ID column
            )
            
            result = self.manager._execute_with_retry(request)
            values = result.get('values', [])
            
            for i, row in enumerate(values):
                if row and len(row) > 0 and row[0] == member_id:
                    return i + 1  # Return 1-indexed row number
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding member row for {member_id}: {e}")
            return None
    
    def get_active_members(self) -> List[Member]:
        """Get only active members"""
        all_members = self.get_all_members()
        return [m for m in all_members if m.membership_status == "active"]
    
    def get_members_by_role(self, role: str) -> List[Member]:
        """Get members by role (member, exec)"""
        all_members = self.get_all_members()
        return [m for m in all_members if m.role == role]
    
    def get_members_by_payment_status(self, payment_status: str) -> List[Member]:
        """Get members by payment status"""
        all_members = self.get_all_members()
        return [m for m in all_members if m.payment_status == payment_status]
    
    def initialize_sheet(self) -> bool:
        """
        Initialize the Members sheet with headers if it doesn't exist
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check if sheet has data
            request = self.manager.service.spreadsheets().values().get(
                spreadsheetId=self.sheet_id,
                range="Members!A1:Q1"
            )
            
            result = self.manager._execute_with_retry(request)
            values = result.get('values', [])
            
            # If no data or wrong headers, add headers
            if not values or values[0][0] != "Member ID":
                headers = Member.get_headers()
                body = {
                    'values': [headers]
                }
                
                request = self.manager.service.spreadsheets().values().update(
                    spreadsheetId=self.sheet_id,
                    range="Members!A1:Q1",
                    valueInputOption='RAW',
                    body=body
                )
                
                self.manager._execute_with_retry(request)
                logger.info("Members sheet headers initialized")
            
            return True
            
        except Exception as e:
            logger.error(f"Error initializing members sheet: {e}")
            return False

# Example usage and testing
if __name__ == "__main__":
    print("Testing Google Sheets CRUD Operations...")
    
    try:
        # Initialize manager
        manager = GoogleSheetsManager()
        members_crud = MembersCRUD(manager)
        
        # Test initialization
        print("✓ Initializing members sheet...")
        if members_crud.initialize_sheet():
            print("✓ Members sheet initialized")
        
        # Test creating a member
        from data.models import generate_member_id
        test_member = Member(
            member_id=generate_member_id(),
            first_name="Test",
            last_name="User",
            email="test.user@berkeley.edu",
            phone="555-999-8888",
            role="member",
            graduation_year="2025"
        )
        
        print(f"✓ Creating test member: {test_member.full_name}")
        if members_crud.create_member(test_member):
            print("✓ Member created successfully")
            
            # Test reading the member back
            retrieved_member = members_crud.get_member_by_id(test_member.member_id)
            if retrieved_member:
                print(f"✓ Member retrieved: {retrieved_member.full_name}")
                
                # Test updating the member
                retrieved_member.major = "Updated Major"
                if members_crud.update_member(retrieved_member):
                    print("✓ Member updated successfully")
                
                # Test soft delete
                if members_crud.delete_member(test_member.member_id):
                    print("✓ Member deleted (marked inactive) successfully")
            
        # Test getting all members
        all_members = members_crud.get_all_members()
        print(f"✓ Retrieved {len(all_members)} total members")
        
        active_members = members_crud.get_active_members()
        print(f"✓ Retrieved {len(active_members)} active members")
        
    except Exception as e:
        print(f"✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n✓ CRUD operations testing completed!")
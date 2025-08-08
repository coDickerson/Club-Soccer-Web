"""
Test Script for Members CRUD Operations
Tests the GoogleSheetsManager and MembersCRUD with real Google Sheets
File location: tests/test_members_crud.py
"""

import sys
import os
from datetime import datetime
import traceback

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from auth.google_auth import create_google_client
from data.sheets_crud import GoogleSheetsManager, MembersCRUD
from data.models import Member, generate_member_id
from configs import google_sheets_config, validate_config

def test_configuration():
    """Test that configuration is properly set up"""
    print("=" * 60)
    print("🔧 TESTING CONFIGURATION")
    print("=" * 60)
    
    # Validate overall config
    config_errors = validate_config()
    if config_errors:
        print("❌ Configuration Errors Found:")
        for error in config_errors:
            print(f"   - {error}")
        return False
    else:
        print("✅ Configuration validation passed")
    
    # Check Google Sheets specific config
    if not google_sheets_config.is_configured():
        print("❌ Google Sheets configuration incomplete")
        return False
    else:
        print("✅ Google Sheets configuration complete")
    
    # Display current config (without sensitive data)
    print(f"\n📊 Current Configuration:")
    print(f"   Members Sheet ID: {google_sheets_config.MEMBERS_SHEET_ID}")
    print(f"   Service Account File: {google_sheets_config.SERVICE_ACCOUNT_FILE is not None}")
    print(f"   Service Account JSON: {google_sheets_config.SERVICE_ACCOUNT_JSON is not None}")
    
    return True

def test_authentication():
    """Test Google Sheets authentication"""
    print("\n" + "=" * 60)
    print("🔐 TESTING AUTHENTICATION")
    print("=" * 60)
    
    try:
        # Create Google client
        client = create_google_client()
        if not client:
            print("❌ Failed to create Google client")
            return None
        
        print("✅ Google client created successfully")
        
        # Test connection with your actual sheet
        sheet_id = google_sheets_config.MEMBERS_SHEET_ID
        if client.test_connection(sheet_id):
            print("✅ Connection to Google Sheet verified")
            return client
        else:
            print("❌ Failed to connect to Google Sheet")
            return None
            
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        traceback.print_exc()
        return None

def test_sheets_manager(client):
    """Test GoogleSheetsManager initialization"""
    print("\n" + "=" * 60)
    print("📋 TESTING SHEETS MANAGER")
    print("=" * 60)
    
    try:
        manager = GoogleSheetsManager(client)
        print("✅ GoogleSheetsManager created successfully")
        
        # Display manager configuration
        print(f"\n📊 Manager Configuration:")
        print(f"   Members Sheet ID: {manager.members_sheet_id}")
        print(f"   Members Range: {manager.members_range}")
        print(f"   Service Connected: {manager.service is not None}")
        
        return manager
        
    except Exception as e:
        print(f"❌ Sheets manager error: {e}")
        traceback.print_exc()
        return None

def test_sheet_initialization(members_crud):
    """Test sheet initialization and header setup"""
    print("\n" + "=" * 60)
    print("📄 TESTING SHEET INITIALIZATION")
    print("=" * 60)
    
    try:
        if members_crud.initialize_sheet():
            print("✅ Members sheet initialized successfully")
            print("✅ Headers set up correctly")
            return True
        else:
            print("❌ Failed to initialize members sheet")
            return False
            
    except Exception as e:
        print(f"❌ Sheet initialization error: {e}")
        traceback.print_exc()
        return False

def test_create_member(members_crud):
    """Test creating a new member"""
    print("\n" + "=" * 60)
    print("👤 TESTING MEMBER CREATION")
    print("=" * 60)
    
    try:
        # Create a test member
        test_member = Member(
            member_id=generate_member_id(),
            first_name="Test",
            last_name="User",
            email="test.user@berkeley.edu",
            phone="(510) 555-1234",
            role="member",
            membership_status="active",
            payment_status="pending",
            join_date=datetime.now().strftime("%Y-%m-%d"),
            graduation_year="2025",
            major="Computer Science",
            emergency_contact="Jane User",
            emergency_phone="(510) 555-5678",
            notes="Test member created by automated test"
        )
        
        print(f"📝 Creating test member: {test_member.full_name}")
        print(f"   Member ID: {test_member.member_id}")
        print(f"   Email: {test_member.email}")
        print(f"   Role: {test_member.role}")
        
        if members_crud.create_member(test_member):
            print("✅ Member created successfully!")
            return test_member
        else:
            print("❌ Failed to create member")
            return None
            
    except Exception as e:
        print(f"❌ Member creation error: {e}")
        traceback.print_exc()
        return None

def test_read_members(members_crud, test_member_id=None):
    """Test reading members from the sheet"""
    print("\n" + "=" * 60)
    print("👥 TESTING MEMBER READING")
    print("=" * 60)
    
    try:
        # Test get all members
        all_members = members_crud.get_all_members()
        print(f"📊 Total members found: {len(all_members)}")
        
        if all_members:
            print("\n👤 Sample member data:")
            sample = all_members[0]
            print(f"   Name: {sample.full_name}")
            print(f"   Email: {sample.email}")
            print(f"   Role: {sample.role}")
            print(f"   Status: {sample.membership_status}")
        
        # Test get specific member if we have a test ID
        if test_member_id:
            specific_member = members_crud.get_member_by_id(test_member_id)
            if specific_member:
                print(f"✅ Successfully retrieved specific member: {specific_member.full_name}")
            else:
                print(f"❌ Could not find member with ID: {test_member_id}")
        
        # Test filtered reads
        active_members = members_crud.get_active_members()
        print(f"📊 Active members: {len(active_members)}")
        
        exec_members = members_crud.get_members_by_role("exec")
        print(f"📊 Executive members: {len(exec_members)}")
        
        paid_members = members_crud.get_members_by_payment_status("paid")
        print(f"📊 Paid members: {len(paid_members)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Member reading error: {e}")
        traceback.print_exc()
        return False

def test_update_member(members_crud, test_member):
    """Test updating a member"""
    print("\n" + "=" * 60)
    print("✏️ TESTING MEMBER UPDATE")
    print("=" * 60)
    
    try:
        if not test_member:
            print("❌ No test member provided for update test")
            return False
        
        # Update the member
        original_major = test_member.major
        test_member.major = "Updated Computer Science"
        test_member.notes = f"Updated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        print(f"📝 Updating member: {test_member.full_name}")
        print(f"   Changing major from '{original_major}' to '{test_member.major}'")
        
        if members_crud.update_member(test_member):
            print("✅ Member updated successfully!")
            
            # Verify the update by reading it back
            updated_member = members_crud.get_member_by_id(test_member.member_id)
            if updated_member and updated_member.major == test_member.major:
                print("✅ Update verified - changes persisted correctly")
                return True
            else:
                print("❌ Update verification failed")
                return False
        else:
            print("❌ Failed to update member")
            return False
            
    except Exception as e:
        print(f"❌ Member update error: {e}")
        traceback.print_exc()
        return False

def test_delete_member(members_crud, test_member):
    """Test soft-deleting a member"""
    print("\n" + "=" * 60)
    print("🗑️ TESTING MEMBER DELETION (SOFT DELETE)")
    print("=" * 60)
    
    try:
        if not test_member:
            print("❌ No test member provided for deletion test")
            return False
        
        print(f"📝 Soft-deleting member: {test_member.full_name}")
        print(f"   Member will be marked as 'inactive' instead of removed")
        
        if members_crud.delete_member(test_member.member_id):
            print("✅ Member soft-deleted successfully!")
            
            # Verify the soft delete
            deleted_member = members_crud.get_member_by_id(test_member.member_id)
            if deleted_member and deleted_member.membership_status == "inactive":
                print("✅ Soft delete verified - member marked as inactive")
                return True
            else:
                print("❌ Soft delete verification failed")
                return False
        else:
            print("❌ Failed to delete member")
            return False
            
    except Exception as e:
        print(f"❌ Member deletion error: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🧪 CAL MEN'S CLUB SOCCER - MEMBERS CRUD TESTING")
    print("🚀 Starting comprehensive test suite...")
    print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test results tracking
    test_results = {
        'configuration': False,
        'authentication': False,
        'sheets_manager': False,
        'sheet_initialization': False,
        'member_creation': False,
        'member_reading': False,
        'member_update': False,
        'member_deletion': False
    }
    
    # Test 1: Configuration
    test_results['configuration'] = test_configuration()
    if not test_results['configuration']:
        print("\n❌ Configuration test failed - stopping tests")
        return
    
    # Test 2: Authentication
    client = test_authentication()
    test_results['authentication'] = client is not None
    if not test_results['authentication']:
        print("\n❌ Authentication test failed - stopping tests")
        return
    
    # Test 3: Sheets Manager
    manager = test_sheets_manager(client)
    test_results['sheets_manager'] = manager is not None
    if not test_results['sheets_manager']:
        print("\n❌ Sheets manager test failed - stopping tests")
        return
    
    # Initialize CRUD operations
    members_crud = MembersCRUD(manager)
    
    # Test 4: Sheet Initialization
    test_results['sheet_initialization'] = test_sheet_initialization(members_crud)
    
    # Test 5: Member Creation
    test_member = test_create_member(members_crud)
    test_results['member_creation'] = test_member is not None
    
    # Test 6: Member Reading
    test_results['member_reading'] = test_read_members(
        members_crud, 
        test_member.member_id if test_member else None
    )
    
    # Test 7: Member Update
    if test_member:
        test_results['member_update'] = test_update_member(members_crud, test_member)
    
    # Test 8: Member Deletion
    if test_member:
        test_results['member_deletion'] = test_delete_member(members_crud, test_member)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    total_tests = len(test_results)
    passed_tests = sum(test_results.values())
    
    for test_name, passed in test_results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {test_name.replace('_', ' ').title()}: {status}")
    
    print(f"\n📈 Results: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED! Your Members CRUD is working perfectly!")
    else:
        print("⚠️ Some tests failed. Check the error messages above.")
    
    print(f"⏰ Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
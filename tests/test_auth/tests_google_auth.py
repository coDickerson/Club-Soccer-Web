"""
Test script to verify Google Sheets authentication is working
Run this from your project root directory: python test_google_auth.py
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path so we can import our auth module
sys.path.append('src')

try:
    from auth.google_auth import create_google_client
    print("✓ Successfully imported google_auth module")
except ImportError as e:
    print(f"✗ Failed to import google_auth module: {e}")
    print("Make sure you're running this from the project root directory")
    sys.exit(1)

def test_environment_variables():
    """Test that required environment variables are set"""
    print("\n=== Testing Environment Variables ===")
    
    # Check for service account file
    service_account_file = os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE')
    if service_account_file:
        print(f"✓ GOOGLE_SERVICE_ACCOUNT_FILE: {service_account_file}")
        
        # Check if file exists
        if os.path.exists(service_account_file):
            print(f"✓ Service account file exists at: {service_account_file}")
        else:
            print(f"✗ Service account file NOT found at: {service_account_file}")
            return False
    else:
        print("✗ GOOGLE_SERVICE_ACCOUNT_FILE not set in .env")
        
        # Check for JSON string alternative
        if os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON'):
            print("✓ GOOGLE_SERVICE_ACCOUNT_JSON found (JSON string method)")
        else:
            print("✗ No Google service account credentials found")
            return False
    
    # Check for sheet IDs
    sheet_vars = [
        'MEMBERS_SHEET_ID',
        'EVENTS_SHEET_ID', 
        'ATTENDANCE_SHEET_ID',
        'TEST_SPREADSHEET_ID'
    ]
    
    for var in sheet_vars:
        value = os.getenv(var)
        if value:
            print(f"✓ {var}: {value[:10]}...")  # Show first 10 chars for privacy
        else:
            print(f"⚠ {var}: Not set")
    
    return True

def test_authentication():
    """Test Google Sheets authentication"""
    print("\n=== Testing Google Authentication ===")
    
    try:
        # Create client
        print("Creating Google Sheets client...")
        client = create_google_client()
        
        if client:
            print("✓ Successfully created and authenticated Google client")
            return client
        else:
            print("✗ Failed to create Google client")
            return None
            
    except Exception as e:
        print(f"✗ Exception during authentication: {str(e)}")
        return None

def test_sheet_connection(client):
    """Test connection to your actual Google Sheets"""
    print("\n=== Testing Sheet Connections ===")
    
    # Test with different sheet IDs from your .env
    sheet_tests = [
        ('TEST_SPREADSHEET_ID', 'Test Sheet'),
        ('MEMBERS_SHEET_ID', 'Members Sheet'),
        ('EVENTS_SHEET_ID', 'Events Sheet'),
        ('ATTENDANCE_SHEET_ID', 'Attendance Sheet')
    ]
    
    success_count = 0
    
    for env_var, sheet_name in sheet_tests:
        sheet_id = os.getenv(env_var)
        if not sheet_id:
            print(f"⚠ Skipping {sheet_name}: {env_var} not set in .env")
            continue
            
        print(f"Testing connection to {sheet_name}...")
        
        if client.test_connection(sheet_id):
            print(f"✓ Successfully connected to {sheet_name}")
            success_count += 1
            
            # Try to get basic sheet info
            try:
                service = client.get_service()
                if service:
                    result = service.spreadsheets().get(spreadsheetId=sheet_id).execute()
                    title = result.get('properties', {}).get('title', 'Unknown')
                    print(f"  - Sheet title: '{title}'")
                    
                    # Get sheet tabs
                    sheets = result.get('sheets', [])
                    if sheets:
                        sheet_names = [sheet['properties']['title'] for sheet in sheets]
                        print(f"  - Sheet tabs: {sheet_names}")
            except Exception as e:
                print(f"  - Could not get sheet details: {str(e)}")
                
        else:
            print(f"✗ Failed to connect to {sheet_name}")
            print(f"  - Check that {env_var} is correct in your .env file")
            print(f"  - Make sure you shared the sheet with your service account")
    
    return success_count

def test_basic_read_operation(client):
    """Test a basic read operation"""
    print("\n=== Testing Basic Read Operation ===")
    
    # Use the first available sheet ID
    test_sheet_id = (os.getenv('TEST_SPREADSHEET_ID') or 
                    os.getenv('MEMBERS_SHEET_ID') or 
                    os.getenv('EVENTS_SHEET_ID') or 
                    os.getenv('ATTENDANCE_SHEET_ID'))
    
    if not test_sheet_id:
        print("⚠ No sheet ID available for read test")
        return False
    
    try:
        service = client.get_service()
        if not service:
            print("✗ Could not get service object")
            return False
        
        # Try to read A1:C3 range
        print(f"Attempting to read A1:C3 from sheet...")
        result = service.spreadsheets().values().get(
            spreadsheetId=test_sheet_id,
            range='A1:C3'
        ).execute()
        
        values = result.get('values', [])
        print(f"✓ Successfully read data: {len(values)} rows")
        
        # Show first few values (be careful not to expose sensitive data)
        if values:
            print("  - First row:", values[0] if values[0] else "Empty")
        
        return True
        
    except Exception as e:
        print(f"✗ Read operation failed: {str(e)}")
        if "403" in str(e):
            print("  - This might be a permissions issue")
            print("  - Make sure you shared the sheet with your service account email")
        return False

def main():
    """Run all tests"""
    print("🏈 SOCCER CLUB ADMIN - Google Sheets Authentication Test")
    print("=" * 60)
    
    # Test 1: Environment variables
    if not test_environment_variables():
        print("\n❌ Environment setup failed. Please check your .env file.")
        return
    
    # Test 2: Authentication
    client = test_authentication()
    if not client:
        print("\n❌ Authentication failed. Check your service account setup.")
        return
    
    # Test 3: Sheet connections
    success_count = test_sheet_connection(client)
    
    # Test 4: Basic read operation
    read_success = test_basic_read_operation(client)
    
    # Summary
    print("\n" + "=" * 60)
    print("🏆 TEST SUMMARY:")
    print(f"✓ Authentication: {'SUCCESS' if client else 'FAILED'}")
    print(f"✓ Sheet connections: {success_count} successful")
    print(f"✓ Read operation: {'SUCCESS' if read_success else 'FAILED'}")
    
    if client and success_count > 0 and read_success:
        print("\n🎉 ALL TESTS PASSED! Your Google Sheets integration is ready!")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
    
    print("\nNext steps:")
    print("1. If tests passed: You're ready to build the data access layer")
    print("2. If tests failed: Check your .env file and Google Sheet sharing")

if __name__ == "__main__":
    main()
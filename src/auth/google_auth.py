"""
Google Authentication Module
Handles authentication with Google APIs (Sheets, Drive) using service account credentials
File location: src/auth/google_auth.py
"""

import os
import json
from typing import Optional, List
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GoogleAuth:
    """Handles Google Sheets API authentication and service creation"""
    
    # Define the scopes needed for Google Sheets access
    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive.file'
    ]
    
    def __init__(self, service_account_file: Optional[str] = None, 
                 service_account_info: Optional[dict] = None):
        """
        Initialize Google Sheets authentication
        
        Args:
            service_account_file: Path to service account JSON file
            service_account_info: Service account info as dictionary
        """
        self.service_account_file = service_account_file
        self.service_account_info = service_account_info
        self.credentials = None
        self.service = None
        
    def authenticate(self) -> bool:
        """
        Authenticate with Google Sheets API using service account
        
        Returns:
            bool: True if authentication successful, False otherwise
        """
        try:
            # Try to load credentials from file first
            if self.service_account_file and os.path.exists(self.service_account_file):
                logger.info(f"Loading credentials from file: {self.service_account_file}")
                self.credentials = Credentials.from_service_account_file(
                    self.service_account_file, 
                    scopes=self.SCOPES
                )
            
            # If no file, try to load from dictionary
            elif self.service_account_info:
                logger.info("Loading credentials from service account info dictionary")
                self.credentials = Credentials.from_service_account_info(
                    self.service_account_info, 
                    scopes=self.SCOPES
                )
            
            # Try to load from environment variable as JSON string
            elif os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON'):
                logger.info("Loading credentials from environment variable")
                service_account_json = json.loads(os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON'))
                self.credentials = Credentials.from_service_account_info(
                    service_account_json, 
                    scopes=self.SCOPES
                )
            
            else:
                logger.error("No service account credentials found")
                return False
            
            # Build the service
            self.service = build('sheets', 'v4', credentials=self.credentials)
            logger.info("Successfully authenticated with Google Sheets API")
            return True
            
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            return False
    
    def get_service(self):
        """
        Get the Google Sheets service object
        
        Returns:
            Google Sheets service object or None if not authenticated
        """
        if not self.service:
            logger.warning("Service not initialized. Call authenticate() first.")
            return None
        return self.service
    
    def test_connection(self, spreadsheet_id: str) -> bool:
        """
        Test the connection by trying to access a spreadsheet
        
        Args:
            spreadsheet_id: ID of spreadsheet to test access
            
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            if not self.service:
                logger.error("Service not initialized")
                return False
                
            # Try to get spreadsheet metadata
            result = self.service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
            logger.info(f"Successfully connected to spreadsheet: {result.get('properties', {}).get('title', 'Unknown')}")
            return True
            
        except HttpError as e:
            logger.error(f"HTTP Error testing connection: {e}")
            return False
        except Exception as e:
            logger.error(f"Error testing connection: {str(e)}")
            return False
    
    def refresh_credentials(self) -> bool:
        """
        Refresh the credentials if they're expired
        
        Returns:
            bool: True if refresh successful, False otherwise
        """
        try:
            if self.credentials and self.credentials.expired:
                logger.info("Refreshing expired credentials")
                self.credentials.refresh(Request())
                return True
            return True
        except Exception as e:
            logger.error(f"Failed to refresh credentials: {str(e)}")
            return False


def create_google_client(service_account_file: Optional[str] = None) -> Optional[GoogleAuth]:
    """
    Factory function to create and authenticate a Google Sheets client
    
    Args:
        service_account_file: Path to service account JSON file
        
    Returns:
        Authenticated GoogleAuth instance or None if failed
    """
    # Try different authentication methods in order of preference
    auth_methods = [
        # Method 1: Use provided service account file
        lambda: GoogleAuth(service_account_file=service_account_file) if service_account_file else None,
        
        # Method 2: Use service account file from environment variable
        lambda: GoogleAuth(service_account_file=os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE')),
        
        # Method 3: Use service account JSON from environment variable
        lambda: GoogleAuth(),
    ]
    
    for method in auth_methods:
        try:
            client = method()
            if client and client.authenticate():
                logger.info("Successfully created and authenticated Google Sheets client")
                return client
        except Exception as e:
            logger.debug(f"Authentication method failed: {str(e)}")
            continue
    
    logger.error("All authentication methods failed")
    return None


# Example usage and testing functions
def validate_service_account_file(file_path: str) -> bool:
    """
    Validate that a service account file has the required fields
    
    Args:
        file_path: Path to service account JSON file
        
    Returns:
        bool: True if valid, False otherwise
    """
    required_fields = [
        'type', 'project_id', 'private_key_id', 'private_key',
        'client_email', 'client_id', 'auth_uri', 'token_uri'
    ]
    
    try:
        with open(file_path, 'r') as f:
            service_account_data = json.load(f)
        
        missing_fields = [field for field in required_fields if field not in service_account_data]
        
        if missing_fields:
            logger.error(f"Service account file missing required fields: {missing_fields}")
            return False
            
        logger.info("Service account file validation passed")
        return True
        
    except FileNotFoundError:
        logger.error(f"Service account file not found: {file_path}")
        return False
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in service account file: {file_path}")
        return False
    except Exception as e:
        logger.error(f"Error validating service account file: {str(e)}")
        return False


if __name__ == "__main__":
    # Example usage
    print("Testing Google Sheets Authentication...")
    
    # Create client
    client = create_google_client()
    
    if client:
        print("✓ Authentication successful!")
        
        # Test with a spreadsheet ID (you'll need to provide a real one)
        test_spreadsheet_id = os.getenv('TEST_SPREADSHEET_ID')
        if test_spreadsheet_id:
            if client.test_connection(test_spreadsheet_id):
                print("✓ Connection test successful!")
            else:
                print("✗ Connection test failed")
        else:
            print("No test spreadsheet ID provided in environment variables")
    else:
        print("✗ Authentication failed")
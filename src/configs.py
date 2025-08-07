"""
Configuration Management Module
Handles environment variables, API keys, and application settings
"""

import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

@dataclass
class AppConfig:
    """Application configuration settings"""
    # Application Settings
    DEBUG: bool = os.getenv('DEBUG', 'False').lower() == 'true'
    SECRET_KEY: str = os.getenv('SECRET_KEY', 'dev-secret-change-in-production')
    HOST: str = os.getenv('APP_HOST', 'localhost')
    PORT: int = int(os.getenv('APP_PORT', '8050'))
    BASE_URL: str = os.getenv('BASE_URL', 'http://localhost:8050')
    
    # Environment
    ENVIRONMENT: str = os.getenv('FLASK_ENV', 'development')

@dataclass
class GoogleSheetsConfig:
    """Google Sheets API configuration"""
    API_KEY: Optional[str] = os.getenv('GOOGLE_SHEETS_API_KEY')
    CLIENT_ID: Optional[str] = os.getenv('GOOGLE_CLIENT_ID')
    CLIENT_SECRET: Optional[str] = os.getenv('GOOGLE_CLIENT_SECRET')
    SERVICE_ACCOUNT_FILE: Optional[str] = os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE')
    SERVICE_ACCOUNT_JSON: Optional[str] = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
    
    # Google Sheets IDs
    MEMBERS_SHEET_ID: Optional[str] = os.getenv('MEMBERS_SHEET_ID')
    EVENTS_SHEET_ID: Optional[str] = os.getenv('EVENTS_SHEET_ID')
    ATTENDANCE_SHEET_ID: Optional[str] = os.getenv('ATTENDANCE_SHEET_ID')
    
    def is_configured(self) -> bool:
        """Check if Google Sheets is properly configured"""
        has_service_account = bool(self.SERVICE_ACCOUNT_FILE or self.SERVICE_ACCOUNT_JSON)
        has_sheet_ids = bool(self.MEMBERS_SHEET_ID and self.EVENTS_SHEET_ID and self.ATTENDANCE_SHEET_ID)
        return has_service_account and has_sheet_ids

@dataclass
class WixConfig:
    """Wix integration configuration"""
    APP_ID: Optional[str] = os.getenv('WIX_APP_ID')
    APP_SECRET: Optional[str] = os.getenv('WIX_APP_SECRET')
    SITE_ID: Optional[str] = os.getenv('WIX_SITE_ID')
    
    # API URLs
    API_BASE_URL: str = os.getenv('WIX_API_BASE_URL', 'https://www.wixapis.com')
    OAUTH_URL: str = os.getenv('WIX_OAUTH_URL', 'https://www.wix.com/oauth/authorize')
    TOKEN_URL: str = os.getenv('WIX_TOKEN_URL', 'https://www.wix.com/oauth/access_token')
    
    # Webhooks
    WEBHOOK_SECRET: Optional[str] = os.getenv('WIX_WEBHOOK_SECRET')
    WEBHOOK_URL: Optional[str] = os.getenv('WIX_WEBHOOK_URL')
    
    def is_configured(self) -> bool:
        """Check if Wix integration is properly configured"""
        return bool(self.APP_ID and self.APP_SECRET and self.SITE_ID)

@dataclass
class SecurityConfig:
    """Security and authentication configuration"""
    JWT_SECRET_KEY: str = os.getenv('JWT_SECRET_KEY', 'jwt-secret-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES: int = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', '3600'))  # 1 hour
    JWT_REFRESH_TOKEN_EXPIRES: int = int(os.getenv('JWT_REFRESH_TOKEN_EXPIRES', '2592000'))  # 30 days
    BCRYPT_LOG_ROUNDS: int = int(os.getenv('BCRYPT_LOG_ROUNDS', '12'))

@dataclass
class DatabaseConfig:
    """Database configuration"""
    DATABASE_URL: str = os.getenv('DATABASE_URL', 'sqlite:///soccer_club.db')

@dataclass
class FeatureFlags:
    """Feature flags for enabling/disabling functionality"""
    ENABLE_WIX_INTEGRATION: bool = os.getenv('ENABLE_WIX_INTEGRATION', 'True').lower() == 'true'
    ENABLE_EMAIL_NOTIFICATIONS: bool = os.getenv('ENABLE_EMAIL_NOTIFICATIONS', 'False').lower() == 'true'
    ENABLE_CACHING: bool = os.getenv('ENABLE_CACHING', 'True').lower() == 'true'
    CACHE_TIMEOUT: int = int(os.getenv('CACHE_TIMEOUT', '300'))  # 5 minutes

# UC Berkeley Color Scheme
class Colors:
    """UC Berkeley themed color palette"""
    # Primary UC Berkeley Colors
    UC_BLUE = '#003262'      # Berkeley Blue (dark blue)
    UC_GOLD = '#FDB515'      # California Gold
    
    # Secondary Colors
    WHITE = '#FFFFFF'
    BLACK = '#000000'
    FOREST_GREEN = '#228B22'
    
    # UI Colors derived from UC Berkeley palette
    PRIMARY = UC_BLUE
    SECONDARY = UC_GOLD
    SUCCESS = FOREST_GREEN
    WARNING = UC_GOLD
    DANGER = '#DC3545'
    INFO = '#17A2B8'
    
    # Background and text colors
    LIGHT_BACKGROUND = '#F8F9FA'
    DARK_BACKGROUND = UC_BLUE
    SIDEBAR_BACKGROUND = '#F4F4F4'
    
    # Navbar colors
    NAVBAR_BACKGROUND = UC_BLUE
    NAVBAR_TEXT = WHITE
    NAVBAR_HOVER = UC_GOLD

# User Roles and Permissions
class UserRoles:
    """Define user roles and their permissions"""
    EXEC = 'exec'
    MEMBER = 'member'

class Permissions:
    """Define what each role can access"""
    ROLE_PERMISSIONS = {
        UserRoles.EXEC: {
            'dashboard': True,
            'attendance': True,
            'settings': True,
            'payments': True,
            'member_management': True,
            'event_management': True,
            'financial_reports': True,
            'user_management': True,
            'view_all_payments': True,
            'manage_events': True,
            'manage_members': True,
            'strategic_planning': True,
            'executive_dashboard': True
        },
        UserRoles.MEMBER: {
            'dashboard': True,
            'attendance': True,
            'settings': True,     # Only personal settings
            'payments': True,     # Only own payments
            'member_management': False,
            'event_management': False,
            'financial_reports': False,
            'user_management': False,
            'view_all_payments': False,
            'manage_events': False,
            'manage_members': False
        }
    }
    
    @classmethod
    def has_permission(cls, role: str, permission: str) -> bool:
        """Check if a role has a specific permission"""
        return cls.ROLE_PERMISSIONS.get(role, {}).get(permission, False)

# Navigation Configuration
class NavigationConfig:
    """Define navigation structure based on permissions"""
    
    NAV_ITEMS = [
        {
            'name': 'Dashboard',
            'path': '/dashboard',
            'icon': 'fas fa-tachometer-alt',
            'permission': 'dashboard'
        },
        {
            'name': 'Attendance',
            'path': '/attendance', 
            'icon': 'fas fa-calendar-check',
            'permission': 'attendance'
        },
        {
            'name': 'Payments',
            'path': '/payments',
            'icon': 'fas fa-credit-card',
            'permission': 'payments'
        },
        {
            'name': 'Settings',
            'path': '/settings',
            'icon': 'fas fa-cog',
            'permission': 'settings'
        }
    ]
    
    # Executive-only navigation items
    EXEC_NAV_ITEMS = [
        {
            'name': 'Member Management',
            'path': '/members',
            'icon': 'fas fa-users',
            'permission': 'member_management'
        },
        {
            'name': 'Event Management', 
            'path': '/events',
            'icon': 'fas fa-calendar-alt',
            'permission': 'event_management'
        },
        {
            'name': 'Reports',
            'path': '/reports',
            'icon': 'fas fa-chart-bar',
            'permission': 'financial_reports'
        }
    ]

# Initialize configuration instances
app_config = AppConfig()
google_sheets_config = GoogleSheetsConfig()
wix_config = WixConfig()
security_config = SecurityConfig()
database_config = DatabaseConfig()
feature_flags = FeatureFlags()

def get_config():
    """Get all configuration objects"""
    return {
        'app': app_config,
        'google_sheets': google_sheets_config,
        'wix': wix_config,
        'security': security_config,
        'database': database_config,
        'features': feature_flags
    }

def validate_config():
    """Validate that all required configuration is present"""
    errors = []
    
    # Check required app settings
    if app_config.SECRET_KEY == 'dev-secret-change-in-production':
        errors.append("SECRET_KEY should be changed from default in production")
    
    # Check Google Sheets configuration if enabled
    if not google_sheets_config.is_configured():
        errors.append("Google Sheets API is not properly configured")
    
    # Check Wix configuration if enabled
    if feature_flags.ENABLE_WIX_INTEGRATION and not wix_config.is_configured():
        errors.append("Wix integration is enabled but not properly configured")
    
    return errors

if __name__ == "__main__":
    # Test configuration
    config = get_config()
    errors = validate_config()
    
    print("Configuration Status:")
    print(f"App Config: ✓")
    print(f"Google Sheets: {'✓' if google_sheets_config.is_configured() else '✗'}")
    print(f"Wix Integration: {'✓' if wix_config.is_configured() else '✗'}")
    
    if errors:
        print("\nConfiguration Errors:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("\n✓ All configuration valid!")
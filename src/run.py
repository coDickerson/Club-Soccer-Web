#!/usr/bin/env python3
"""
Cal Men's Club Soccer Dashboard Runner
Entry point for running the application
"""

import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

if __name__ == '__main__':
    from app import app
    
    print("🚀 Starting Cal Men's Club Soccer Dashboard...")
    print("=" * 50)
    
    # Import and run the main application
    try:
        # This will run the app with the configuration from config.py
        app.run()
    except KeyboardInterrupt:
        print("\n👋 Shutting down gracefully...")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        sys.exit(1)
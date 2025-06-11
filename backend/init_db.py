#!/usr/bin/env python3
"""
Database initialization script for the RAG system
"""
import os
import sys
from pathlib import Path

def init_database():
    """Initialize the SQLite database with proper permissions"""
    try:
        # Ensure the app directory exists
        app_dir = Path("/app")
        app_dir.mkdir(exist_ok=True)
        
        # Create the database file
        db_file = app_dir / "enterprise_rag.db"
        db_file.touch(exist_ok=True)
        
        # Try to set permissions (will work if we have the right permissions)
        try:
            os.chmod(str(db_file), 0o664)
            print(f"✅ Database file created: {db_file}")
        except PermissionError:
            print(f"⚠️ Could not set permissions for {db_file}, but file exists")
        
        # Set up environment variables
        os.environ.setdefault("DATABASE_URL", f"sqlite:///{db_file}")
        
        print(f"📊 Database URL: {os.environ.get('DATABASE_URL')}")
        return True
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1) 
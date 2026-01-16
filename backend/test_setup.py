"""
Quick test to verify the setup is working.
"""
import sys
from pathlib import Path

def test_setup():
    print("🧪 Testing Setup...\n")
    
    success = True
    
    # Test 1: Check imports
    print("1. Checking Python packages...")
    try:
        import google.generativeai as genai
        import rich
        import pandas
        import sqlparse
        from dotenv import load_dotenv
        print("   ✓ All packages installed\n")
    except ImportError as e:
        print(f"   ❌ Missing package: {e}\n")
        success = False
    
    # Test 2: Check database
    print("2. Checking database...")
    db_path = Path("data/chinook.db")
    if db_path.exists():
        print(f"   ✓ Database found: {db_path}\n")
        
        # Test connection
        try:
            import sqlite3
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            table_count = cursor.fetchone()[0]
            print(f"   ✓ Database has {table_count} tables\n")
            conn.close()
        except Exception as e:
            print(f"   ❌ Database error: {e}\n")
            success = False
    else:
        print(f"   ❌ Database not found at: {db_path}")
        print("   Download from: https://github.com/lerocha/chinook-database\n")
        success = False
    
    # Test 3: Check .env file
    print("3. Checking API configuration...")
    env_file = Path(".env")
    if env_file.exists():
        load_dotenv()
        import os
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key and api_key != "your_api_key_here":
            print(f"   ✓ API key configured (length: {len(api_key)})\n")
        else:
            print("   ⚠️  API key not set in .env file")
            print("   Add: GEMINI_API_KEY=your_key_here\n")
            success = False
    else:
        print("   ⚠️  .env file not found")
        print("   Create .env file with: GEMINI_API_KEY=your_key_here\n")
        success = False
    
    # Summary
    print("=" * 50)
    if success:
        print("✅ Setup complete! Ready to run.")
        print("\nNext steps:")
        print("  python main.py         # Interactive mode")
        print("  python main.py demo    # Run demo queries")
    else:
        print("❌ Setup incomplete. Please fix the issues above.")
    print("=" * 50)
    
    return success

if __name__ == "__main__":
    success = test_setup()
    sys.exit(0 if success else 1)

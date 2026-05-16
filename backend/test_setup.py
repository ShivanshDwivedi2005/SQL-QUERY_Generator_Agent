"""
Quick test to verify the Neon/PostgreSQL setup is working.
"""
import sys
from pathlib import Path

def test_setup():
    print("Testing Setup...\n")
    
    success = True
    
    # Test 1: Check imports
    print("1. Checking Python packages...")
    try:
        import google.generativeai as genai
        import psycopg
        import rich
        import pandas
        import sqlparse
        from dotenv import load_dotenv
        print("   ✓ All packages installed\n")
    except ImportError as e:
        print(f"   ❌ Missing package: {e}\n")
        success = False
    
    # Test 2: Check .env file
    print("2. Checking API and database configuration...")
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

        database_url = os.getenv("DATABASE_URL") or os.getenv("NEON_DATABASE_URL")
        if database_url:
            print("   ✓ Neon/PostgreSQL database URL configured\n")
            try:
                import psycopg
                with psycopg.connect(database_url, connect_timeout=5) as conn:
                    with conn.cursor() as cursor:
                        cursor.execute("SELECT current_database()")
                        db_name = cursor.fetchone()[0]
                print(f"   ✓ Connected to database: {db_name}\n")
            except Exception as e:
                print(f"   ❌ Database connection error: {e}\n")
                success = False
        else:
            print("   ⚠️  Database URL not set in .env file")
            print("   Add: DATABASE_URL=postgresql://...\n")
            success = False
    else:
        print("   ⚠️  .env file not found")
        print("   Create .env file with GEMINI_API_KEY and DATABASE_URL\n")
        success = False
    
    # Summary
    print("=" * 50)
    if success:
        print("Setup complete! Ready to run.")
        print("\nNext steps:")
        print("  uvicorn apis:app --reload --port 8000")
        print("  python main.py")
    else:
        print("Setup incomplete. Please fix the issues above.")
    print("=" * 50)
    
    return success

if __name__ == "__main__":
    success = test_setup()
    sys.exit(0 if success else 1)

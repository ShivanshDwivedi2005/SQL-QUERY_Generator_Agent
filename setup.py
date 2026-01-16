"""
Quick setup script to help with initial configuration.
"""
import os
from pathlib import Path

def main():
    print("🚀 Natural Language to SQL - Setup Helper\n")
    
    # Check for .env file
    env_file = Path(".env")
    if not env_file.exists():
        print("📝 Creating .env file...")
        api_key = input("Enter your Gemini API key (or press Enter to skip): ").strip()
        
        if api_key:
            with open(".env", "w") as f:
                f.write(f"GEMINI_API_KEY={api_key}\n")
            print("✓ .env file created\n")
        else:
            print("⚠️  Skipped. You can create .env manually later\n")
    else:
        print("✓ .env file already exists\n")
    
    # Check for database
    db_path = Path("data/chinook.db")
    if not db_path.exists():
        print("⚠️  Chinook database not found")
        print("\nTo download:")
        print("1. Visit: https://github.com/lerocha/chinook-database")
        print("2. Download 'chinook.db' (SQLite version)")
        print("3. Place it in: data/chinook.db")
        print()
    else:
        print("✓ Chinook database found\n")
    
    # Create data directory if needed
    data_dir = Path("data")
    if not data_dir.exists():
        data_dir.mkdir()
        print("✓ Created data/ directory\n")
    
    print("Next steps:")
    print("1. Install dependencies: pip install -r requirements.txt")
    print("2. Run interactive mode: python main.py")
    print("3. Run demo: python main.py demo")
    print("\nGood luck! 🍀")

if __name__ == "__main__":
    main()

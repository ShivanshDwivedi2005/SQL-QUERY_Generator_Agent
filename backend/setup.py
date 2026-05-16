"""
Quick setup script to help with initial Neon/PostgreSQL configuration.
"""
from pathlib import Path

def main():
    print("Natural Language to PostgreSQL - Setup Helper\n")
    
    # Check for .env file
    env_file = Path(".env")
    if not env_file.exists():
        print("Creating .env file...")
        api_key = input("Enter your Gemini API key (or press Enter to skip): ").strip()
        database_url = input("Enter your Neon DATABASE_URL (or press Enter to skip): ").strip()
        
        lines = []
        if api_key:
            lines.append(f"GEMINI_API_KEY={api_key}")
        if database_url:
            lines.append(f"DATABASE_URL={database_url}")

        if lines:
            with open(".env", "w") as f:
                f.write("\n".join(lines) + "\n")
            print(".env file created\n")
        else:
            print("Skipped. You can create .env manually later\n")
    else:
        print(".env file already exists\n")
    
    print("Next steps:")
    print("1. Install dependencies: pip install -r requirements.txt")
    print("2. Add GEMINI_API_KEY and DATABASE_URL to backend/.env")
    print("3. Run API: uvicorn apis:app --reload --port 8000")
    print("4. Run interactive mode: python main.py")

if __name__ == "__main__":
    main()

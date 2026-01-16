"""
Configuration settings for the Natural Language to SQL system.
"""
import os
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
DATABASE_PATH = DATA_DIR / "chinook.db"

# API Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Model settings
MODEL_NAME = "gemini-2.5-flash"  # Fast and free
TEMPERATURE = 0.1  # Low temperature for consistent SQL generation
MAX_RETRIES = 2  # Maximum retry attempts for failed queries

# Safety settings
MAX_QUERY_TIMEOUT = 5  # seconds
DEFAULT_LIMIT = 100  # Default LIMIT for queries without one
BLOCKED_KEYWORDS = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "TRUNCATE"]

# Display settings
SHOW_REASONING = True
SHOW_SQL = True
SHOW_EXECUTION_TIME = True

import os

"""
Configuration settings for the Natural Language to PostgreSQL system.
"""

# API Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Neon/PostgreSQL configuration. Neon provides a PostgreSQL connection string
# that usually starts with "postgresql://".
DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("NEON_DATABASE_URL") or ""
DATABASE_NAME = os.getenv("DATABASE_NAME", "Neon PostgreSQL")

# Model settings
MODEL_NAME = "gemini-2.5-flash-lite"  # Fast and free
TEMPERATURE = 0.1  # Low temperature for consistent SQL generation
MAX_RETRIES = 2  # Maximum retry attempts for failed queries

# Safety settings
MAX_QUERY_TIMEOUT = 5  # seconds
DEFAULT_LIMIT = 100  # Default LIMIT for queries without one
MAX_UPLOAD_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB CSV upload limit
BLOCKED_KEYWORDS = [
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "TRUNCATE",
    "GRANT", "REVOKE", "VACUUM", "CALL", "DO", "COPY"
]

# Display settings
SHOW_REASONING = True
SHOW_SQL = True
SHOW_EXECUTION_TIME = True

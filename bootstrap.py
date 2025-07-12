import os
import sys

def validate_env():
    required = ["OPENAI_API_KEY", "EMAIL_USER", "EMAIL_PASSWORD", "DATABASE_URL"]
    missing = [var for var in required if not os.getenv(var)]
    if missing:
        print(f"Missing critical environment variables: {', '.join(missing)}")
        sys.exit(1)

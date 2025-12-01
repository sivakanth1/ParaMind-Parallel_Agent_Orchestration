import sys
import os

print("Starting check_env.py")
try:
    import loguru
    print("loguru imported")
    from loguru import logger
    logger.add("logs/test_env_{time}.log")
    logger.info("Test log message")
    print("Log message sent")
except ImportError as e:
    print(f"ImportError: {e}")
except Exception as e:
    print(f"Error: {e}")

try:
    from dotenv import load_dotenv
    load_dotenv()
    print("dotenv loaded")
    print(f"OPENAI_API_KEY exists: {bool(os.getenv('OPENAI_API_KEY'))}")
    print(f"GROQ_API_KEY exists: {bool(os.getenv('GROQ_API_KEY'))}")
except Exception as e:
    print(f"Dotenv error: {e}")

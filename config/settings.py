from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
import os
from pathlib import Path

# Load .env from project root
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

class Settings(BaseSettings):
    """Configuration management using Pydantic"""
    
    # API Keys
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    groq_api_key: Optional[str] = Field(default=None, alias="GROQ_API_KEY")
    
    # System Configuration
    max_concurrent_agents: int = Field(default=3, alias="MAX_CONCURRENT_AGENTS")
    default_timeout: int = Field(default=30, alias="DEFAULT_TIMEOUT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # Model Configuration
    controller_model: str = "llama-3.1-8b-instant"  # Groq - Fast for controller
    available_models: list = [
        "llama-3.3-70b-versatile",   # Best quality
        "llama-3.1-8b-instant",      # Fastest
    ]
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
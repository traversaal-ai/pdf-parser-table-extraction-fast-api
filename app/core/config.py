"""
Configuration management for environment variables using Pydantic.
"""
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """
    llamaparse_api_key: str
    unstructured_api_key: str
    openai_api_key: str

    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "ignore"  # Allow extra environment variables (for client API keys)

settings = Settings()
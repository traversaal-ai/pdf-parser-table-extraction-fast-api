from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os


# Load environment variables from .env file
class Settings(BaseSettings):

    load_dotenv()


    
    llamaparse_api_key: str = os.getenv("llamaparse_api_key", "")
    unstructured_api_key: str = os.getenv("unstructured_api_key", "")
    openai_api_key:str = os.getenv("openai_api_key", "")
 

    
    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "ignore"  

settings = Settings()
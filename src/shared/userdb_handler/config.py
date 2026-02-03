
#Base Config file, as a start
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import find_dotenv

env_path = find_dotenv()

class Settings(BaseSettings):
    database_url:str = Field(validation_alias = 'database_url')
    auth_token:str = Field(validation_alias= 'auth_token')

    model_config = SettingsConfigDict(
        env_file=env_path,
        env_prefix='turso_',
        extra='ignore' )
settings = Settings()

print(settings.model_dump())

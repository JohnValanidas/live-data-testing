import os
from pydantic import PostgresDsn
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    pg_dsn: PostgresDsn = "postgresql://postgres:password@localhost:5555/live-data"
    notify_channel: str = "update_items"
    
    # OpenTelemetry settings
    otel_exporter_otlp_endpoint: str = "http://localhost:4317"
    otel_service_name: str = "live-sdk-api" 
    otel_service_version: str = "1.0.0"
    otel_service_instance_id: str = os.getenv("HOSTNAME", "localhost")
    
settings = Settings()

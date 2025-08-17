import os
import uvicorn
from settings import settings

if __name__ == "__main__":
    print("Starting app with OpenTelemetry instrumentation...")
    print(f"OTLP Endpoint: {settings.otel_exporter_otlp_endpoint}")
    print(f"Service Name: {settings.otel_service_name}")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

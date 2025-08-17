import logging
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.psycopg import PsycopgInstrumentor
from opentelemetry.instrumentation.asyncio import AsyncioInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from settings import settings

logger = logging.getLogger(__name__)


def setup_telemetry():
    otlp_endpoint = settings.otel_exporter_otlp_endpoint
    
    resource = Resource.create({
        "service.name": settings.otel_service_name,
        "service.version": settings.otel_service_version,
        "service.instance.id": settings.otel_service_instance_id,
    })

    trace_provider = TracerProvider(resource=resource)
    otlp_trace_exporter = OTLPSpanExporter(
        endpoint=otlp_endpoint,
        insecure=True # local development
    )
    trace_provider.add_span_processor(BatchSpanProcessor(otlp_trace_exporter))
    trace.set_tracer_provider(trace_provider)

    otlp_metric_exporter = OTLPMetricExporter(
        endpoint=otlp_endpoint,
        insecure=True # local development
    )
    metric_reader = PeriodicExportingMetricReader(
        exporter=otlp_metric_exporter,
        export_interval_millis=5000
    )
    metric_provider = MeterProvider(
        resource=resource,
        metric_readers=[metric_reader]
    )
    metrics.set_meter_provider(metric_provider)

    logger.info(f"OpenTelemetry configured with endpoint: {otlp_endpoint}")


def instrument_app(app):
    FastAPIInstrumentor.instrument_app(app)
    
    SQLAlchemyInstrumentor().instrument()
    PsycopgInstrumentor().instrument()
    
    AsyncioInstrumentor().instrument()
    
    LoggingInstrumentor().instrument(set_logging_format=True)
    
    logger.info("Automatic instrumentation applied")


def get_tracer(name: str):
    return trace.get_tracer(name)


def get_meter(name: str):
    return metrics.get_meter(name)

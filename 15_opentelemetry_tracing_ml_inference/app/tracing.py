import os
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor


def setup_tracing(app, engine=None) -> None:
    service_name = os.getenv("OTEL_SERVICE_NAME", "ml-inference-api")
    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)
    span_processor = BatchSpanProcessor(
        OTLPSpanExporter(endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317"))
    )
    provider.add_span_processor(span_processor)
    trace.set_tracer_provider(provider)

    FastAPIInstrumentor.instrument_app(app)
    HTTPXClientInstrumentor().instrument()
    if engine is not None:
        SQLAlchemyInstrumentor().instrument(engine=engine.sync_engine)
    LoggingInstrumentor().instrument(set_logging_format=True)

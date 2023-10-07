# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG


def _instrument() -> None:
    from opentelemetry.instrumentation.django import DjangoInstrumentor  # type: ignore
    from opentelemetry.instrumentation.celery import CeleryInstrumentor  # type: ignore
    from opentelemetry.instrumentation.requests import RequestsInstrumentor  # type: ignore
    from opentelemetry.instrumentation.botocore import BotocoreInstrumentor # type: ignore
    from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor # type: ignore
    from opentelemetry.instrumentation.redis import RedisInstrumentor # type: ignore
    
    DjangoInstrumentor().instrument()
    CeleryInstrumentor().instrument()  # type: ignore
    RequestsInstrumentor().instrument()
    BotocoreInstrumentor().instrument()  # type: ignore
    Psycopg2Instrumentor().instrument()
    RedisInstrumentor().instrument()


def _setup_telemetry(tracer_prefix: str) -> None:
    from skipper.environment_common import \
        SKIPPER_OTEL_TELEMETRY_ENABLED, \
        SKIPPER_OTEL_SERVICE_NAME, \
        SKIPPER_OTEL_JAEGER_AGENT_HOST_NAME, \
        SKIPPER_OTEL_JAEGER_AGENT_PORT, \
        SKIPPER_OTEL_JAEGER_COLLECTOR_ENDPOINT, \
        SKIPPER_OTEL_JAEGER_USERNAME, \
        SKIPPER_OTEL_JAEGER_PASSWORD, \
        SKIPPER_OTEL_JAEGER_MAX_TAG_VALUE_LENGTH, \
        SKIPPER_INSTALLATION_NAME

    if SKIPPER_OTEL_TELEMETRY_ENABLED:
        from opentelemetry import trace  # type: ignore
        from opentelemetry.exporter.jaeger.thrift import JaegerExporter  # type: ignore
        from opentelemetry.sdk.resources import SERVICE_NAME, Resource  # type: ignore
        from opentelemetry.sdk.trace import TracerProvider  # type: ignore
        from opentelemetry.sdk.trace.export import BatchSpanProcessor  # type: ignore

        _instrument()

        tracer_provider = TracerProvider(
            resource=Resource.create({SERVICE_NAME: SKIPPER_OTEL_SERVICE_NAME or f"{tracer_prefix}-{SKIPPER_INSTALLATION_NAME}"})
        )
        trace.set_tracer_provider(tracer_provider)

        # no ssl here
        # agent should be colocated with compose in a trusted network
        jaeger_exporter = JaegerExporter(
            agent_host_name=SKIPPER_OTEL_JAEGER_AGENT_HOST_NAME,
            agent_port=SKIPPER_OTEL_JAEGER_AGENT_PORT,
            collector_endpoint=SKIPPER_OTEL_JAEGER_COLLECTOR_ENDPOINT,
            username=SKIPPER_OTEL_JAEGER_USERNAME,
            password=SKIPPER_OTEL_JAEGER_PASSWORD,
            max_tag_value_length=SKIPPER_OTEL_JAEGER_MAX_TAG_VALUE_LENGTH,
            udp_split_oversized_batches=True
        )

        trace.get_tracer_provider().add_span_processor(  # type: ignore
            BatchSpanProcessor(jaeger_exporter)
        )


def setup_telemetry_django() -> None:
    _setup_telemetry('skipper-gunicorn')

def setup_telemetry_celery() -> None:
    _setup_telemetry('skipper-celery')
# start up the REST server with Tracing

export MOU_REST_PORT=8079
export OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4318/v1/traces"
export WIPACTEL_SERVICE_NAME_PREFIX=mou

python -m rest_server
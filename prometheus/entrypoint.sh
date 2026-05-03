#!/bin/sh
set -e

: "${API_TARGET:=api:8000}"
export API_TARGET

envsubst < /etc/prometheus/prometheus.yml.tmpl > /etc/prometheus/prometheus.yml

exec /bin/prometheus \
  --config.file=/etc/prometheus/prometheus.yml \
  --storage.tsdb.path=/prometheus \
  --storage.tsdb.retention.time=15d \
  "$@"

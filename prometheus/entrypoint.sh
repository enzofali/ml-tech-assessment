#!/bin/sh
set -e

: "${API_TARGET:=api:8000}"

# Substitute the placeholder with the actual target. sed because envsubst is not
# in the prom/prometheus image and we don't want to pay the install cost.
sed "s|__API_TARGET__|${API_TARGET}|g" \
    /etc/prometheus/prometheus.yml.tmpl > /etc/prometheus/prometheus.yml

exec /bin/prometheus \
  --config.file=/etc/prometheus/prometheus.yml \
  --storage.tsdb.path=/prometheus \
  --storage.tsdb.retention.time=15d \
  "$@"

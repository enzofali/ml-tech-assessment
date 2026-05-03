FROM prom/prometheus:latest

# No package install — prom/prometheus is no longer alpine-based, so `apk` is
# unavailable. We use plain `sed` (present in every base image) for templating.
COPY prometheus.yml.tmpl /etc/prometheus/prometheus.yml.tmpl
COPY entrypoint.sh       /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]

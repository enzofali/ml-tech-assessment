FROM prom/prometheus:latest

# No package install — prom/prometheus is no longer alpine-based, so `apk` is
# unavailable. We use plain `sed` (present in every base image) for templating.
COPY prometheus.yml.tmpl /etc/prometheus/prometheus.yml.tmpl
COPY entrypoint.sh       /entrypoint.sh

# Run as root so Prometheus can write to the Railway-mounted volume at /prometheus.
# The base image defaults to USER nobody, which gets permission-denied on the
# volume (owned by root) and crash-loops with "Unable to create mmap-ed active
# query log". Internal-only service, no public exposure -> root is acceptable.
USER root

ENTRYPOINT ["/entrypoint.sh"]

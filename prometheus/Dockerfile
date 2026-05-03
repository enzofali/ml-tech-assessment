FROM prom/prometheus:latest

USER root
# `envsubst` (from gettext) lets us swap ${API_TARGET} at container start so the
# same image works in compose (api:8000) and on Railway (api.railway.internal:8000).
RUN apk add --no-cache gettext
USER nobody

COPY prometheus.yml.tmpl /etc/prometheus/prometheus.yml.tmpl
COPY entrypoint.sh       /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]

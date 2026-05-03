FROM prom/prometheus:latest

USER root
# `envsubst` (gettext) lets us swap ${API_TARGET} into the scrape config at
# container start so the same image works locally and on Railway.
RUN apk add --no-cache gettext
USER nobody

COPY prometheus.yml.tmpl /etc/prometheus/prometheus.yml.tmpl
COPY entrypoint.sh       /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]

FROM grafana/grafana:latest

# Bake provisioning + dashboards into the image so Grafana auto-loads them on
# Railway (no volume mount of repo files). Datasource URL is templated via
# ${PROMETHEUS_URL}, which Grafana expands at startup.
COPY provisioning /etc/grafana/provisioning
COPY dashboards   /etc/grafana/dashboards

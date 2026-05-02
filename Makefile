IMAGE_API      = transcript-api:latest
IMAGE_FRONTEND = transcript-frontend:latest
NAMESPACE      = transcript-analyzer

# ── Local docker-compose ───────────────────────────────────────────────────────

.PHONY: up down logs

up:
	docker compose up --build -d

down:
	docker compose down

logs:
	docker compose logs -f

# ── Build container images ─────────────────────────────────────────────────────

.PHONY: build build-api build-frontend

build: build-api build-frontend

build-api:
	docker build -t $(IMAGE_API) .

build-frontend:
	docker build \
		--build-arg NEXT_PUBLIC_API_URL=http://localhost/api \
		-t $(IMAGE_FRONTEND) ./frontend

# ── Kubernetes — first-time setup ─────────────────────────────────────────────

.PHONY: k8s-install-ingress k8s-install-metrics-server

# Install nginx ingress controller (Docker Desktop / minikube)
k8s-install-ingress:
	kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.11.3/deploy/static/provider/cloud/deploy.yaml
	kubectl wait --namespace ingress-nginx \
		--for=condition=ready pod \
		--selector=app.kubernetes.io/component=controller \
		--timeout=120s

# Install metrics-server (required for HPA)
k8s-install-metrics-server:
	kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# ── Kubernetes — deploy ────────────────────────────────────────────────────────

.PHONY: k8s-up k8s-config k8s-secrets k8s-down k8s-status

k8s-up: k8s-secrets k8s-config
	kubectl apply -f k8s/namespace.yaml
	kubectl apply -f k8s/postgres/
	kubectl apply -f k8s/prometheus/
	kubectl apply -f k8s/grafana/
	kubectl apply -f k8s/api/
	kubectl apply -f k8s/frontend/
	kubectl apply -f k8s/ingress.yaml

# Create secrets from k8s/secrets.yaml (copy from secrets.example.yaml and fill in values)
k8s-secrets:
	@if [ ! -f k8s/secrets.yaml ]; then \
		echo "ERROR: k8s/secrets.yaml not found."; \
		echo "Copy k8s/secrets.example.yaml → k8s/secrets.yaml and fill in real values."; \
		exit 1; \
	fi
	kubectl apply -f k8s/secrets.yaml

# Create grafana dashboard configmap from the JSON file
k8s-config:
	kubectl apply -f k8s/namespace.yaml
	kubectl create configmap grafana-dashboard \
		--from-file=transcript-api.json=grafana/dashboards/transcript-api.json \
		-n $(NAMESPACE) \
		--dry-run=client -o yaml | kubectl apply -f -

k8s-down:
	kubectl delete namespace $(NAMESPACE) --ignore-not-found

k8s-status:
	kubectl get pods,svc,ingress,pvc,hpa -n $(NAMESPACE)

# ── Minikube helpers ───────────────────────────────────────────────────────────

.PHONY: minikube-build minikube-tunnel

# Load images into minikube's Docker daemon (avoids registry push)
minikube-build:
	eval $$(minikube docker-env) && \
		docker build -t $(IMAGE_API) . && \
		docker build \
			--build-arg NEXT_PUBLIC_API_URL=http://$$(minikube ip)/api \
			-t $(IMAGE_FRONTEND) ./frontend

minikube-tunnel:
	minikube tunnel

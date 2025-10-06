# FastAPI Kubernetes Monitoring & Auto-Recovery System

A production-ready monitoring system for microservices on Kubernetes with crash detection, auto-recovery, and ML-based failure prediction.

## Architecture

- **Application**: FastAPI microservice with Prometheus metrics
- **Container Orchestration**: Kubernetes (Minikube)
- **Monitoring**: Prometheus + Grafana
- **Alerting**: Alertmanager with Slack integration
- **Prediction**: Python-based ML failure prediction

## Features

### ✅ Part A: Crash Detection & Notification
- Automatic pod restart via Kubernetes deployments
- Prometheus alert rules for pod failures
- Real-time Slack notifications via Alertmanager

### ✅ Part B: Chaos Testing & Auto-Recovery
- Chaos testing scripts to simulate failures
- Kubernetes automatically recreates failed pods
- Self-healing architecture with replica management

### ✅ Part C: Monitoring Stack
- Prometheus ServiceMonitor for metrics collection
- Grafana dashboards for visualization
- Recording rules for performance trends

### ✅ Part D: Performance Analysis & Failure Prediction
- Predictive alerts (memory leaks, response degradation)
- ML-based crash risk analysis (predict.py)
- Anomaly detection for traffic spikes
- Performance analysis reporting

## Project Structure
k8s-crash-recovery/
├── app/
│   └── main.py                    # FastAPI application with metrics
├── k8s/
│   ├── app/
│   │   ├── deployment.yaml        # Kubernetes deployment
│   │   └── service.yaml           # ClusterIP service
│   └── monitoring/
│       ├── servicemonitor.yaml    # Prometheus scrape config
│       ├── alertmanager-config.yaml
│       └── alerts/
│           ├── alert-rules.yaml        # Crash detection alerts
│           ├── recording-rules.yaml    # Performance metrics
│           └── predictive-alerts.yaml  # Failure prediction
├── prediction/
│   └── predict.py                 # ML failure prediction script
├── scripts/
│   ├── chaos.sh                   # Chaos testing
│   ├── chaos-with-recovery.sh     # Auto-recovery test
│   ├── performance-analysis.sh    # Performance reports
│   └── final-verification.sh      # System validation
├── Dockerfile
├── requirements.txt
└── README.md

## Quick Start

### Prerequisites
- Minikube running
- kubectl configured
- Python 3.11+ with venv
- Slack webhook (optional)

### Setup

1. **Build and load Docker image**
```bash
docker build -t piyushkumar26/fastapi-microservice:v2 .
minikube image load piyushkumar26/fastapi-microservice:v2

Deploy application

bashkubectl create namespace microservice
kubectl apply -f k8s/app/

Setup monitoring

bashhelm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus-stack prometheus-community/kube-prometheus-stack -n monitoring --create-namespace
kubectl apply -f k8s/monitoring/

Configure Alertmanager (optional)

bash# Update with your Slack webhook
kubectl apply -f k8s/monitoring/alertmanager-config.yaml
Access Dashboards
bash# Prometheus
kubectl port-forward -n monitoring svc/prometheus-stack-kube-prom-prometheus 9090:9090

# Grafana (default: admin/prom-operator)
kubectl port-forward -n monitoring svc/prometheus-stack-grafana 3001:80

# FastAPI
kubectl port-forward -n microservice svc/fastapi-app-service 8081:80
Visit:

Prometheus: http://localhost:9090
Grafana: http://localhost:3001
FastAPI: http://localhost:8081
Metrics: http://localhost:8081/metrics

Testing
Run Chaos Test
bash./scripts/chaos-with-recovery.sh
Watch:

Pods scale to 0, then auto-recover to 2
Prometheus alerts fire
Slack notifications arrive
Grafana shows the impact

Run Performance Analysis
bashsource venv/bin/activate
./scripts/performance-analysis.sh
Run ML Prediction
bashpython prediction/predict.py
Full System Verification
bash./scripts/final-verification.sh
Monitoring Capabilities
Metrics Collected

Request rate (req/s)
Response time (p50, p95, p99)
Error rate
Pod CPU/Memory usage
Pod restart count

Alerts Configured

FastAPIAppDown: Metrics endpoint unreachable
FastAPINoPods: Zero replicas available
MemoryLeakPredicted: Memory trending toward limit
ResponseTimeDegradation: Response time increasing
TrafficSpikeDetected: Unusual traffic patterns
FrequentRestarts: Potential crash loops

Technology Stack

Language: Python 3.11
Framework: FastAPI + Uvicorn
Container: Docker
Orchestration: Kubernetes (Minikube)
Monitoring: Prometheus, Grafana
Alerting: Alertmanager
Analytics: Python (requests library)

Key Learnings

ServiceMonitor requires proper labels to be discovered by Prometheus
Alertmanager templates use different syntax than Prometheus queries
Predictive alerts need sufficient historical data (1+ hour)
Recording rules improve query performance for dashboards
Kubernetes self-healing requires proper replica configuration

Future Enhancements

Add distributed tracing (Jaeger)
Implement log aggregation (Loki)
Add HorizontalPodAutoscaler for dynamic scaling
Integrate advanced ML models (scikit-learn)
Add integration tests
Implement blue-green deployments

License
MIT

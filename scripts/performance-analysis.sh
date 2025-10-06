#!/bin/bash

echo "=========================================="
echo "FastAPI Performance Analysis Report"
echo "Generated at: $(date)"
echo "=========================================="
echo ""

# Check if Prometheus is accessible
if ! curl -s http://localhost:9090/api/v1/query > /dev/null 2>&1; then
    echo "ERROR: Cannot connect to Prometheus at http://localhost:9090"
    echo "Make sure port-forward is running: kubectl port-forward -n monitoring svc/prometheus-stack-kube-prom-prometheus 9090:9090"
    exit 1
fi

echo "Current Performance Metrics:"
echo "============================="

# Request rate
REQ_RATE=$(curl -s 'http://localhost:9090/api/v1/query?query=sum(rate(fastapi_requests_total{namespace="microservice"}[1m]))' | grep -oP '"value":\[\d+\.\d+,"[^"]+' | grep -oP '\d+\.\d+' | tail -1)
echo "Request Rate: ${REQ_RATE:-0} req/s"

# Average response time
AVG_RT=$(curl -s 'http://localhost:9090/api/v1/query?query=sum(rate(fastapi_request_duration_seconds_sum{namespace="microservice"}[1m]))/sum(rate(fastapi_request_duration_seconds_count{namespace="microservice"}[1m]))' | grep -oP '"value":\[\d+\.\d+,"[^"]+' | grep -oP '\d+\.\d+' | tail -1)
echo "Avg Response Time: ${AVG_RT:-0}s"

# Error rate
ERR_RATE=$(curl -s 'http://localhost:9090/api/v1/query?query=sum(rate(fastapi_requests_total{namespace="microservice",status=~"5.."}[1m]))' | grep -oP '"value":\[\d+\.\d+,"[^"]+' | grep -oP '\d+\.\d+' | tail -1)
echo "Error Rate: ${ERR_RATE:-0} req/s"

# Pod count
POD_COUNT=$(curl -s 'http://localhost:9090/api/v1/query?query=count(up{service="fastapi-app-service",namespace="microservice"}==1)' | grep -oP '"value":\[\d+\.\d+,"[^"]+' | grep -oP '\d+' | tail -1)
echo "Running Pods: ${POD_COUNT:-0}"

echo ""
echo "Predictive Analysis:"
echo "===================="

# Memory prediction
MEM_PRED=$(curl -s 'http://localhost:9090/api/v1/query?query=predict_linear(container_memory_working_set_bytes{namespace="microservice",pod=~"fastapi-app.*"}[1h],3600)' | grep -oP '"value":\[\d+\.\d+,"[^"]+' | grep -oP '\d+\.\d+' | head -1)
if [ -n "$MEM_PRED" ]; then
    MEM_PRED_MB=$(echo "scale=1; $MEM_PRED / 1024 / 1024" | bc)
    echo "Predicted Memory (1h): ${MEM_PRED_MB} MB"
else
    echo "Predicted Memory (1h): N/A (need 1h of history)"
fi

echo ""
echo "Active Alerts:"
echo "=============="
kubectl get prometheusrules -n monitoring -o json | grep -o '"alertname":"[^"]*"' | cut -d'"' -f4 | sort -u || echo "No alerts configured"

echo ""
echo "Pod Health:"
echo "==========="
kubectl get pods -n microservice -o wide

echo ""
echo "ML-Based Prediction:"
echo "===================="
python prediction/predict.py 2>&1 || echo "Prediction script not available or failed"

echo ""
echo "Recommendations:"
echo "================"

# Check if response time is high
if command -v bc > /dev/null 2>&1; then
    if [ -n "$AVG_RT" ] && (( $(echo "$AVG_RT > 0.5" | bc -l 2>/dev/null || echo 0) )); then
        echo "WARNING: Response time is high. Consider:"
        echo "   - Scaling up pods"
        echo "   - Optimizing application code"
        echo "   - Adding caching"
    fi

    # Check if error rate is high
    if [ -n "$ERR_RATE" ] && (( $(echo "$ERR_RATE > 0.01" | bc -l 2>/dev/null || echo 0) )); then
        echo "WARNING: Error rate detected. Check application logs."
    fi
fi

# Check pod count
if [ "$POD_COUNT" -lt 2 ] && [ "$POD_COUNT" != "" ]; then
    echo "WARNING: Running fewer than expected pods. Check deployment status."
fi

echo ""
echo "=========================================="
echo "Report complete. Check Grafana for detailed visualizations."
echo "=========================================="
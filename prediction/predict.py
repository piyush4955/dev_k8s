import requests
import sys
from datetime import datetime

# Prometheus endpoint
PROMETHEUS_URL = "http://127.0.0.1:9090/api/v1/query"

def query_prometheus(query):
    """Query Prometheus and return results"""
    try:
        resp = requests.get(PROMETHEUS_URL, params={'query': query}, timeout=5)
        resp.raise_for_status()
        return resp.json()['data']['result']
    except Exception as e:
        print(f"Error querying Prometheus: {e}")
        return []

def predict_pod_crashes():
    """Predict pod crash risk based on restart history"""
    print(f"\n=== Pod Crash Risk Prediction ===")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    query = 'kube_pod_container_status_restarts_total{namespace="microservice"}'
    data = query_prometheus(query)
    
    high_risk_pods = []
    
    if not data:
        print("No pod data available")
        return high_risk_pods
    
    for pod in data:
        name = pod['metric'].get('pod', 'unknown')
        restarts = int(float(pod['value'][1]))
        
        # Risk classification
        if restarts > 10:
            risk = "CRITICAL"
            high_risk_pods.append(name)
            print(f"CRITICAL: Pod {name} (restarts={restarts}) - Immediate attention needed")
        elif restarts > 5:
            risk = "HIGH"
            high_risk_pods.append(name)
            print(f"HIGH: Pod {name} (restarts={restarts}) - Monitor closely")
        elif restarts > 2:
            risk = "MEDIUM"
            print(f"MEDIUM: Pod {name} (restarts={restarts}) - Watch for trends")
        else:
            print(f"STABLE: Pod {name} (restarts={restarts})")
    
    return high_risk_pods

def predict_memory_issues():
    """Predict memory issues using trend analysis"""
    print(f"\n=== Memory Usage Prediction ===\n")
    
    query = 'predict_linear(container_memory_working_set_bytes{namespace="microservice", pod=~"fastapi-app.*"}[1h], 3600)'
    data = query_prometheus(query)
    
    if not data:
        print("No memory prediction data available (need 1h of history)")
        return
    
    for pod in data:
        name = pod['metric'].get('pod', 'unknown')
        predicted_memory = float(pod['value'][1])
        
        # Convert to MB
        predicted_mb = predicted_memory / (1024 * 1024)
        
        # Check against limit (256Mi from deployment)
        if predicted_mb > 250:
            print(f"CRITICAL: Pod {name} predicted to use {predicted_mb:.1f}MB in 1h (limit: 256MB)")
        elif predicted_mb > 200:
            print(f"WARNING: Pod {name} predicted to use {predicted_mb:.1f}MB in 1h")
        else:
            print(f"OK: Pod {name} predicted to use {predicted_mb:.1f}MB in 1h")

def predict_response_time_degradation():
    """Predict response time issues"""
    print(f"\n=== Response Time Trend Analysis ===\n")
    
    # Check if response time is increasing
    query = 'deriv(fastapi:response_time:avg[10m])'
    data = query_prometheus(query)
    
    if not data:
        print("No response time data available yet (need recording rules active)")
        return
    
    if data and len(data) > 0 and len(data[0]['value']) > 1:
        trend = float(data[0]['value'][1])
        if trend > 0.001:
            print(f"WARNING: Response time is degrading ({trend:.6f}s/s increase)")
        elif trend > 0:
            print(f"NOTICE: Slight response time increase detected ({trend:.6f}s/s)")
        else:
            print(f"OK: Response time is stable or improving")
    else:
        print("Insufficient response time data")

def get_current_metrics():
    """Get current system metrics"""
    print(f"\n=== Current System Metrics ===\n")
    
    # Pod count
    query = 'count(up{service="fastapi-app-service", namespace="microservice"} == 1)'
    data = query_prometheus(query)
    if data:
        pod_count = int(float(data[0]['value'][1]))
        print(f"Running Pods: {pod_count}")
    
    # Request rate
    query = 'sum(rate(fastapi_requests_total{namespace="microservice"}[1m]))'
    data = query_prometheus(query)
    if data:
        req_rate = float(data[0]['value'][1])
        print(f"Request Rate: {req_rate:.2f} req/s")
    
    # Error rate
    query = 'sum(rate(fastapi_requests_total{namespace="microservice", status=~"5.."}[1m]))'
    data = query_prometheus(query)
    if data:
        err_rate = float(data[0]['value'][1])
        print(f"Error Rate: {err_rate:.4f} req/s")

def main():
    print("=" * 60)
    print("FastAPI Microservice - Failure Prediction Report")
    print("=" * 60)
    
    # Get current metrics first
    get_current_metrics()
    
    # Run all predictions
    high_risk_pods = predict_pod_crashes()
    predict_memory_issues()
    predict_response_time_degradation()
    
    # Summary
    print(f"\n{'=' * 60}")
    print("SUMMARY")
    print("=" * 60)
    
    if high_risk_pods:
        print(f"\nWARNING: {len(high_risk_pods)} pod(s) at high crash risk: {', '.join(high_risk_pods)}")
        print("Recommendation: Investigate logs and consider scaling or code fixes")
        sys.exit(1)
    else:
        print("\nAll pods stable. No immediate concerns.")
        sys.exit(0)

if __name__ == "__main__":
    main()
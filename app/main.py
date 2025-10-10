# app/main.py
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import Response, JSONResponse
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
import time
import psutil
import os
from datetime import datetime
from typing import Dict, Any

# Import our ML modules
from ml.anomaly_detector import SimpleAnomalyDetector, TimeSeriesPredictor, HealthScorer

app = FastAPI(
    title="AI-Powered Microservice Monitor",
    description="FastAPI with built-in ML anomaly detection",
    version="3.0.0"
)

# Initialize ML components
anomaly_detector = SimpleAnomalyDetector(window_size=100, threshold=3.0)
time_series_predictor = TimeSeriesPredictor(alpha=0.3)
health_scorer = HealthScorer()

# Prometheus metrics
REQUEST_COUNT = Counter(
    'fastapi_requests_total',
    'Total requests',
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'fastapi_request_duration_seconds',
    'Request duration',
    ['method', 'endpoint'],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0)
)

MEMORY_USAGE = Gauge('fastapi_memory_usage_bytes', 'Memory usage')
CPU_USAGE = Gauge('fastapi_cpu_usage_percent', 'CPU usage')
HEALTH_SCORE = Gauge('fastapi_health_score', 'Overall health score')
ANOMALY_COUNT = Gauge('fastapi_anomaly_count', 'Total anomalies detected')

# ML Metrics
ML_PREDICTIONS = Gauge('fastapi_ml_prediction', 'ML predicted value', ['metric'])
ML_ANOMALY = Gauge('fastapi_ml_anomaly_detected', 'Anomaly flag', ['metric'])

# Global state
app_state = {
    'start_time': datetime.now(),
    'total_requests': 0,
    'error_count': 0,
    'last_health_check': None
}


def update_ml_metrics(response_time: float, memory_mb: float, cpu_pct: float):
    """Update ML models with new metrics"""
    
    # Add to anomaly detector
    anomaly_detector.add_metric('response_time', response_time)
    anomaly_detector.add_metric('memory_usage', memory_mb)
    anomaly_detector.add_metric('error_rate', app_state['error_count'] / max(app_state['total_requests'], 1))
    
    # Check for anomalies
    for metric_name, value in [
        ('response_time', response_time),
        ('memory_usage', memory_mb)
    ]:
        is_anomaly, z_score, explanation = anomaly_detector.detect_anomaly(metric_name, value)
        
        if is_anomaly:
            print(f"⚠️ ANOMALY DETECTED: {explanation}")
            ML_ANOMALY.labels(metric=metric_name).set(1)
            ANOMALY_COUNT.inc()
        else:
            ML_ANOMALY.labels(metric=metric_name).set(0)
    
    # Update time series predictions
    time_series_predictor.update('response_time', response_time)
    time_series_predictor.update('memory_usage', memory_mb)
    
    # Get predictions
    predicted_response = time_series_predictor.predict_n_steps('response_time', 5)
    if predicted_response:
        ML_PREDICTIONS.labels(metric='response_time').set(predicted_response[0])


@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    print("🚀 AI-Powered Microservice starting...")
    print(f"📊 ML Models initialized: Anomaly Detector, Time Series Predictor")
    print(f"🔢 Process ID: {os.getpid()}")
    app_state['start_time'] = datetime.now()


@app.middleware("http")
async def monitor_requests(request, call_next):
    start_time = time.time()
    
    # Process request
    response = await call_next(request)
    
    # Calculate metrics
    duration = time.time() - start_time
    process = psutil.Process()
    memory_mb = process.memory_info().rss / 1024 / 1024
    cpu_pct = process.cpu_percent()
    
    # Update Prometheus metrics
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    REQUEST_DURATION.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)
    
    MEMORY_USAGE.set(memory_mb * 1024 * 1024)  # Convert to bytes
    CPU_USAGE.set(cpu_pct)
    
    # Update app state
    app_state['total_requests'] += 1
    if response.status_code >= 500:
        app_state['error_count'] += 1
    
    # Update ML metrics
    update_ml_metrics(duration, memory_mb, cpu_pct)
    
    # Calculate health score
    metrics = {
        'error_rate': app_state['error_count'] / max(app_state['total_requests'], 1),
        'response_time': duration,
        'memory_usage': (memory_mb / 256) * 100,  # Assuming 256MB limit
        'cpu_usage': cpu_pct
    }
    score, status, issues = health_scorer.calculate_score(metrics)
    HEALTH_SCORE.set(score)
    app_state['last_health_check'] = {
        'score': score,
        'status': status,
        'issues': issues,
        'timestamp': datetime.now().isoformat()
    }
    
    return response


@app.get("/")
def read_root():
    """Root endpoint"""
    uptime = (datetime.now() - app_state['start_time']).total_seconds()
    
    return {
        "message": "AI-Powered Microservice Monitor",
        "version": "3.0.0",
        "status": "healthy",
        "uptime_seconds": round(uptime, 2),
        "features": [
            "Real-time anomaly detection",
            "Time series prediction",
            "Health scoring",
            "Prometheus metrics"
        ]
    }


@app.get("/health")
def health_check():
    """Detailed health check with AI insights"""
    process = psutil.Process()
    memory_mb = process.memory_info().rss / 1024 / 1024
    cpu_pct = process.cpu_percent()
    
    # Get current metrics
    error_rate = app_state['error_count'] / max(app_state['total_requests'], 1)
    
    metrics = {
        'error_rate': error_rate,
        'response_time': 0.1,  # Default
        'memory_usage': (memory_mb / 256) * 100,
        'cpu_usage': cpu_pct
    }
    
    score, status, issues = health_scorer.calculate_score(metrics)
    recommendations = health_scorer.get_recommendations(metrics, score)
    
    # Get trend predictions
    memory_trend, memory_slope = time_series_predictor.detect_trend('memory_usage')
    
    return {
        "status": status,
        "health_score": score,
        "timestamp": datetime.now().isoformat(),
        "metrics": {
            "memory_mb": round(memory_mb, 2),
            "cpu_percent": cpu_pct,
            "error_rate": round(error_rate * 100, 2),
            "total_requests": app_state['total_requests'],
            "anomalies_detected": anomaly_detector.anomaly_count
        },
        "trends": {
            "memory": {
                "direction": memory_trend,
                "slope": round(memory_slope, 4)
            }
        },
        "issues": issues,
        "recommendations": recommendations
    }


@app.get("/ai/statistics")
def get_ai_statistics():
    """Get ML model statistics"""
    stats = anomaly_detector.get_statistics()
    
    predictions = {}
    for metric in ['response_time', 'memory_usage']:
        predicted, confidence = anomaly_detector.predict_next_value(metric)
        if predicted:
            predictions[metric] = {
                'predicted': round(predicted, 4),
                'confidence': round(confidence, 4)
            }
    
    return {
        "model": "SimpleAnomalyDetector",
        "statistics": stats,
        "predictions": predictions,
        "anomaly_threshold": anomaly_detector.threshold,
        "total_anomalies": anomaly_detector.anomaly_count
    }


@app.get("/ai/predict")
def predict_future(metric: str = "memory_usage", steps: int = 10):
    """Predict future values for a metric"""
    predictions = time_series_predictor.predict_n_steps(metric, steps)
    trend, slope = time_series_predictor.detect_trend(metric)
    
    return {
        "metric": metric,
        "predictions": [round(p, 4) for p in predictions],
        "trend": trend,
        "slope": round(slope, 4),
        "confidence": "medium" if abs(slope) < 1 else "low"
    }


@app.get("/ai/health-report")
def get_health_report():
    """Get comprehensive AI-powered health report"""
    process = psutil.Process()
    memory_mb = process.memory_info().rss / 1024 / 1024
    
    current_metrics = {
        'error_rate': app_state['error_count'] / max(app_state['total_requests'], 1),
        'response_time': 0.1,
        'memory_usage': (memory_mb / 256) * 100,
        'cpu_usage': process.cpu_percent()
    }
    
    score, status, issues = health_scorer.calculate_score(current_metrics)
    recommendations = health_scorer.get_recommendations(current_metrics, score)
    
    # Get predictions
    memory_predictions = time_series_predictor.predict_n_steps('memory_usage', 5)
    
    return {
        "report_time": datetime.now().isoformat(),
        "overall_health": {
            "score": score,
            "status": status,
            "grade": "A" if score >= 90 else "B" if score >= 75 else "C" if score >= 50 else "F"
        },
        "current_metrics": current_metrics,
        "issues": issues,
        "recommendations": recommendations,
        "predictions": {
            "memory_usage_next_5min": [round(p, 2) for p in memory_predictions] if memory_predictions else []
        },
        "anomalies": {
            "total_detected": anomaly_detector.anomaly_count,
            "rate": round(anomaly_detector.anomaly_count / max(app_state['total_requests'], 1), 4)
        }
    }


@app.get("/metrics")
def metrics():
    """Prometheus metrics endpoint"""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/simulate/load")
def simulate_load(requests: int = 100):
    """Simulate load for testing ML models"""
    import random
    
    results = []
    for i in range(requests):
        # Simulate varying response times
        response_time = random.uniform(0.01, 0.5)
        
        # Add to detector
        anomaly_detector.add_metric('response_time', response_time)
        
        # Check for anomaly
        is_anomaly, z_score, explanation = anomaly_detector.detect_anomaly('response_time', response_time)
        
        if is_anomaly:
            results.append({
                'request': i,
                'response_time': round(response_time, 4),
                'anomaly': True,
                'z_score': round(z_score, 2),
                'explanation': explanation
            })
    
    return {
        "simulated_requests": requests,
        "anomalies_found": len(results),
        "anomalies": results[:10]  # Return first 10
    }


@app.get("/crash")
def crash():
    """Endpoint to simulate crash"""
    os._exit(1)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
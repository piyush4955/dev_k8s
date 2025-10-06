# app/main.py
from fastapi import FastAPI
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST, Gauge
from fastapi.responses import Response
import time
import psutil
import os

app = FastAPI()

# Prometheus metrics with limited cardinality
REQUEST_COUNT = Counter(
    'fastapi_requests_total', 
    'Total number of requests',
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'fastapi_request_duration_seconds',
    'Request duration in seconds',
    ['method', 'endpoint'],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
)

# Memory monitoring metric
MEMORY_USAGE = Gauge(
    'fastapi_memory_usage_bytes',
    'Memory usage in bytes'
)

CPU_USAGE = Gauge(
    'fastapi_cpu_usage_percent',
    'CPU usage percentage'
)

@app.on_event("startup")
async def startup_event():
    """Initialize app on startup"""
    print("FastAPI Microservice starting up...")
    print(f"Process ID: {os.getpid()}")

@app.middleware("http")
async def monitor_requests(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    # Track request metrics
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    REQUEST_DURATION.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)
    
    # Update system metrics
    process = psutil.Process()
    MEMORY_USAGE.set(process.memory_info().rss)
    CPU_USAGE.set(process.cpu_percent())
    
    return response

@app.get("/")
def read_root():
    """Root endpoint"""
    return {
        "message": "Hello from FastAPI Microservice!",
        "version": "v2",
        "status": "healthy"
    }

@app.get("/health")
def health_check():
    """Health check endpoint"""
    process = psutil.Process()
    memory_mb = process.memory_info().rss / 1024 / 1024
    
    return {
        "status": "healthy",
        "memory_mb": round(memory_mb, 2),
        "cpu_percent": process.cpu_percent()
    }

@app.get("/metrics")
def metrics():
    """Prometheus metrics endpoint"""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/crash")
def crash():
    """Endpoint to simulate crash for chaos testing"""
    import os
    os._exit(1)
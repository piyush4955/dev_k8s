# app/ml/anomaly_detector.py
import numpy as np
from collections import deque
from datetime import datetime
import json

class SimpleAnomalyDetector:
    """
    Lightweight anomaly detection using statistical methods
    No external ML libraries needed - production ready
    """
    
    def __init__(self, window_size=100, threshold=3.0):
        self.window_size = window_size
        self.threshold = threshold
        self.metrics_history = {
            'response_time': deque(maxlen=window_size),
            'memory_usage': deque(maxlen=window_size),
            'error_rate': deque(maxlen=window_size)
        }
        self.anomaly_count = 0
        
    def add_metric(self, metric_name, value):
        """Add new metric value to history"""
        if metric_name in self.metrics_history:
            self.metrics_history[metric_name].append(value)
    
    def detect_anomaly(self, metric_name, current_value):
        """
        Detect anomaly using Z-score method
        Returns: (is_anomaly: bool, z_score: float, explanation: str)
        """
        history = self.metrics_history.get(metric_name, [])
        
        if len(history) < 10:  # Need minimum data
            return False, 0.0, "Insufficient data"
        
        # Calculate statistics
        mean = np.mean(history)
        std = np.std(history)
        
        if std == 0:  # Avoid division by zero
            return False, 0.0, "No variation in data"
        
        # Calculate Z-score
        z_score = (current_value - mean) / std
        
        is_anomaly = abs(z_score) > self.threshold
        
        if is_anomaly:
            self.anomaly_count += 1
            direction = "higher" if z_score > 0 else "lower"
            explanation = f"{metric_name} is {abs(z_score):.2f}σ {direction} than normal (mean={mean:.4f}, std={std:.4f})"
            return True, z_score, explanation
        
        return False, z_score, "Normal behavior"
    
    def get_statistics(self):
        """Get current statistics for all metrics"""
        stats = {}
        for metric_name, history in self.metrics_history.items():
            if len(history) > 0:
                stats[metric_name] = {
                    'mean': float(np.mean(history)),
                    'std': float(np.std(history)),
                    'min': float(np.min(history)),
                    'max': float(np.max(history)),
                    'current': float(history[-1]) if history else 0,
                    'count': len(history)
                }
        return stats
    
    def predict_next_value(self, metric_name):
        """
        Simple linear prediction using moving average
        Returns: (predicted_value, confidence)
        """
        history = list(self.metrics_history.get(metric_name, []))
        
        if len(history) < 5:
            return None, 0.0
        
        # Simple weighted moving average (recent values weighted more)
        weights = np.exp(np.linspace(-1, 0, len(history)))
        weights /= weights.sum()
        
        predicted = np.average(history, weights=weights)
        
        # Confidence based on variance
        variance = np.var(history)
        confidence = 1.0 / (1.0 + variance)
        
        return float(predicted), float(confidence)


class TimeSeriesPredictor:
    """
    Simple time series prediction for resource usage
    Uses exponential smoothing - no external libraries
    """
    
    def __init__(self, alpha=0.3):
        self.alpha = alpha  # Smoothing factor
        self.predictions = {}
        self.last_values = {}
        
    def update(self, metric_name, value, timestamp=None):
        """Update with new value and make prediction"""
        if timestamp is None:
            timestamp = datetime.now()
            
        if metric_name not in self.last_values:
            self.last_values[metric_name] = value
            self.predictions[metric_name] = value
            return value
        
        # Exponential smoothing formula
        prediction = self.alpha * value + (1 - self.alpha) * self.last_values[metric_name]
        
        self.last_values[metric_name] = value
        self.predictions[metric_name] = prediction
        
        return prediction
    
    def predict_n_steps(self, metric_name, n_steps=10):
        """Predict n steps ahead"""
        if metric_name not in self.predictions:
            return []
        
        current = self.predictions[metric_name]
        predictions = []
        
        for i in range(n_steps):
            # Simple linear extrapolation
            predictions.append(current * (1 + 0.01 * i))  # 1% growth assumption
        
        return predictions
    
    def detect_trend(self, metric_name, lookback=20):
        """
        Detect if metric is trending up, down, or stable
        Returns: ('increasing', 'decreasing', 'stable'), slope
        """
        if metric_name not in self.last_values:
            return 'stable', 0.0
        
        # Simple trend detection using recent history
        # In production, you'd use actual history storage
        current = self.last_values[metric_name]
        predicted = self.predictions[metric_name]
        
        diff = predicted - current
        
        if abs(diff) < 0.01 * current:  # Less than 1% change
            return 'stable', 0.0
        elif diff > 0:
            return 'increasing', diff
        else:
            return 'decreasing', diff


class HealthScorer:
    """
    Calculate overall health score for the service
    Combines multiple metrics into single score (0-100)
    """
    
    def __init__(self):
        self.weights = {
            'error_rate': 0.4,      # Most important
            'response_time': 0.3,   # Second most important
            'memory_usage': 0.2,
            'cpu_usage': 0.1
        }
        
    def calculate_score(self, metrics):
        """
        Calculate health score from metrics
        Returns: (score: 0-100, status: str, issues: list)
        """
        score = 100.0
        issues = []
        
        # Error rate scoring (lower is better)
        error_rate = metrics.get('error_rate', 0)
        if error_rate > 0.05:  # > 5%
            deduction = min(40, error_rate * 100)
            score -= deduction
            issues.append(f"High error rate: {error_rate*100:.2f}%")
        
        # Response time scoring (lower is better, target < 200ms)
        response_time = metrics.get('response_time', 0)
        if response_time > 0.2:  # > 200ms
            deduction = min(30, (response_time - 0.2) * 100)
            score -= deduction
            issues.append(f"Slow response time: {response_time*1000:.0f}ms")
        
        # Memory usage scoring (target < 80%)
        memory_pct = metrics.get('memory_usage', 0)
        if memory_pct > 80:
            deduction = min(20, (memory_pct - 80) / 2)
            score -= deduction
            issues.append(f"High memory usage: {memory_pct:.1f}%")
        
        # CPU usage scoring (target < 70%)
        cpu_pct = metrics.get('cpu_usage', 0)
        if cpu_pct > 70:
            deduction = min(10, (cpu_pct - 70) / 3)
            score -= deduction
            issues.append(f"High CPU usage: {cpu_pct:.1f}%")
        
        # Determine status
        if score >= 90:
            status = "Excellent"
        elif score >= 75:
            status = "Good"
        elif score >= 50:
            status = "Warning"
        else:
            status = "Critical"
        
        return round(score, 2), status, issues
    
    def get_recommendations(self, metrics, health_score):
        """Generate actionable recommendations"""
        recommendations = []
        
        if health_score < 75:
            error_rate = metrics.get('error_rate', 0)
            if error_rate > 0.05:
                recommendations.append({
                    'priority': 'high',
                    'issue': 'High error rate',
                    'action': 'Check application logs for recurring errors',
                    'impact': 'User experience'
                })
            
            response_time = metrics.get('response_time', 0)
            if response_time > 0.5:
                recommendations.append({
                    'priority': 'high',
                    'issue': 'Slow response time',
                    'action': 'Consider adding caching or optimizing queries',
                    'impact': 'Performance'
                })
            
            memory_pct = metrics.get('memory_usage', 0)
            if memory_pct > 85:
                recommendations.append({
                    'priority': 'medium',
                    'issue': 'High memory usage',
                    'action': 'Scale up pods or investigate memory leaks',
                    'impact': 'Stability'
                })
        
        return recommendations
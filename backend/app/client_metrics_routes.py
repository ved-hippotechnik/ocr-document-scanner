"""
Client-side metrics ingestion endpoint.

Accepts batched metrics from the frontend (API call timings, errors,
user actions, performance data) and forwards them to Prometheus counters
or logs them for analysis.
"""

import logging
from datetime import datetime, timezone

from flask import Blueprint, request, jsonify, g
from prometheus_client import Counter, Histogram

logger = logging.getLogger(__name__)

client_metrics_bp = Blueprint('client_metrics', __name__)

# Prometheus counters for client-side metrics
client_api_calls = Counter(
    'client_api_calls_total',
    'Client-side API call count',
    ['endpoint', 'success'],
)

client_api_duration = Histogram(
    'client_api_duration_ms',
    'Client-side API call duration in milliseconds',
    ['endpoint'],
    buckets=[50, 100, 250, 500, 1000, 2500, 5000, 10000, 30000, 60000, 120000],
)

client_errors = Counter(
    'client_errors_total',
    'Client-side error count',
    ['component', 'action'],
)

client_user_actions = Counter(
    'client_user_actions_total',
    'Client-side user action count',
    ['action'],
)


@client_metrics_bp.route('/api/v3/client-metrics', methods=['POST'])
def ingest_client_metrics():
    """
    Accept batched client-side metrics.

    Expected payload:
    {
        "metrics": [
            {"type": "api_call", "endpoint": "/api/v3/scan", "durationMs": 1234, "success": true},
            {"type": "error", "errorId": "ERR-...", "component": "AIScanner", "message": "..."},
            {"type": "user_action", "action": "scan_retry"},
            {"type": "performance", "component": "AIScanner", "metric": "mount_time", "valueMs": 45}
        ],
        "clientTimestamp": 1234567890
    }
    """
    try:
        data = request.get_json(silent=True)
        if not data or 'metrics' not in data:
            return jsonify({'error': 'No metrics provided'}), 400

        metrics = data['metrics']
        if not isinstance(metrics, list):
            return jsonify({'error': 'metrics must be an array'}), 400

        # Cap batch size to prevent abuse
        if len(metrics) > 200:
            metrics = metrics[:200]

        processed = 0
        for metric in metrics:
            metric_type = metric.get('type')

            if metric_type == 'api_call':
                endpoint = metric.get('endpoint', 'unknown')
                success = str(metric.get('success', True)).lower()
                duration = metric.get('durationMs', 0)
                client_api_calls.labels(endpoint=endpoint, success=success).inc()
                if duration > 0:
                    client_api_duration.labels(endpoint=endpoint).observe(duration)
                processed += 1

            elif metric_type == 'error':
                component = metric.get('component', 'unknown')
                action = metric.get('action', 'unknown')
                error_id = metric.get('errorId', 'unknown')
                message = metric.get('message', '')
                client_errors.labels(component=component, action=action).inc()
                # Log client errors for server-side debugging
                logger.warning(
                    "Client error [%s] component=%s action=%s: %s (request_id=%s)",
                    error_id, component, action, message,
                    getattr(g, 'request_id', 'unknown'),
                )
                processed += 1

            elif metric_type == 'user_action':
                action = metric.get('action', 'unknown')
                client_user_actions.labels(action=action).inc()
                processed += 1

            elif metric_type == 'performance':
                # Log performance metrics (could be forwarded to a time-series DB)
                component = metric.get('component', 'unknown')
                metric_name = metric.get('metric', 'unknown')
                value_ms = metric.get('valueMs', 0)
                logger.debug(
                    "Client perf: component=%s metric=%s value=%.1fms",
                    component, metric_name, value_ms,
                )
                processed += 1

        return jsonify({
            'success': True,
            'processed': processed,
            'timestamp': datetime.now(timezone.utc).isoformat(),
        }), 200

    except Exception as e:
        logger.error("Client metrics ingestion error: %s (request_id=%s)", e, getattr(g, 'request_id', 'unknown'))
        return jsonify({'error': 'Internal error processing metrics'}), 500

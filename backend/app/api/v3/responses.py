"""
Unified response helpers for all v3 API routes.

Every v3 endpoint should use these helpers so clients see a single,
predictable JSON envelope regardless of which route they hit.

Success shape:
    {
        "success": true,
        "data": { ... },
        "request_id": "...",
        "timestamp": "..."
    }

Error shape:
    {
        "success": false,
        "error": {
            "code": "FILE_REQUIRED",
            "message": "Missing required file"
        },
        "request_id": "...",
        "timestamp": "..."
    }
"""

import uuid
from datetime import datetime, timezone
from flask import jsonify, g


def _request_id() -> str:
    return getattr(g, 'request_id', None) or str(uuid.uuid4())


def api_success(data: dict, status: int = 200):
    """Return a unified success response."""
    body = {
        'success': True,
        'data': data,
        'request_id': _request_id(),
        'timestamp': datetime.now(timezone.utc).isoformat(),
    }
    return jsonify(body), status


def api_error(message: str, code: str = 'ERROR', status: int = 400, details: str = None):
    """Return a unified error response."""
    error_obj = {
        'code': code,
        'message': message,
    }
    if details:
        error_obj['details'] = details

    body = {
        'success': False,
        'error': error_obj,
        'request_id': _request_id(),
        'timestamp': datetime.now(timezone.utc).isoformat(),
    }
    return jsonify(body), status

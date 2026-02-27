"""
api/__init__.py
===============
Central registration point for all versioned API blueprints.

Call ``register_api_blueprints(app)`` from ``app/__init__.py`` during
application factory setup.  This replaces the scattered blueprint imports
that lived directly in the factory.

Blueprint layout
----------------
  api/v3/scan.py        POST /api/v3/scan
  api/v3/system.py      GET  /api/v3/processors, /api/v3/languages, /api/v3/stats
  api/v3/classify.py    POST /api/v3/classify, /api/v3/quality
  api/v3/batch.py       *    /api/v3/batch/*
  api/v3/async_ops.py   *    /api/v3/async/*
  api/v3/analytics.py   GET  /api/v3/analytics/*
  api/v3/developer.py   *    /api/v3/developer/*
  api/auth/routes.py    *    /api/auth/*  (no version prefix — never versioned)
  api/legacy/v1.py      *    /api/*       (thin proxy → v3, adds Deprecation header)
  api/legacy/v2.py      *    /api/v2/*    (thin proxy → v3, adds Deprecation header)
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def register_api_blueprints(app) -> None:
    """Register every api/* blueprint on *app*.

    Import errors for individual blueprints are caught and logged as
    warnings so that a single broken module does not prevent the rest of
    the application from starting.
    """

    _blueprints = [
        # (import path, attribute name, friendly label)
        ("app.api.v3.scan",       "v3_scan_bp",       "v3 scan"),
        ("app.api.v3.system",     "v3_system_bp",     "v3 system"),
        ("app.api.v3.classify",   "v3_classify_bp",   "v3 classify"),
        ("app.api.v3.batch",      "v3_batch_bp",      "v3 batch"),
        ("app.api.v3.async_ops",  "v3_async_bp",      "v3 async"),
        ("app.api.v3.analytics",  "v3_analytics_bp",  "v3 analytics"),
        ("app.api.v3.developer",  "v3_developer_bp",  "v3 developer"),
        ("app.api.auth.routes",   "auth_v2_bp",       "auth"),
        ("app.api.legacy.v1",     "legacy_v1_bp",     "legacy v1"),
        ("app.api.legacy.v2",     "legacy_v2_bp",     "legacy v2"),
    ]

    for module_path, attr, label in _blueprints:
        try:
            import importlib
            module = importlib.import_module(module_path)
            blueprint = getattr(module, attr)
            app.register_blueprint(blueprint)
            app.logger.info("Registered api blueprint: %s", label)
        except ImportError as exc:
            app.logger.warning(
                "Could not import api blueprint '%s' (%s): %s", label, module_path, exc
            )
        except Exception as exc:  # noqa: BLE001
            app.logger.error(
                "Failed to register api blueprint '%s': %s", label, exc
            )

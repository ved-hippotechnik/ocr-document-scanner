# Package initialization
# Import functions from monitoring module to avoid circular imports
def setup_metrics(app):
    from ..monitoring import setup_metrics as _setup_metrics
    return _setup_metrics(app)

def track_document_processing(document_type, status, duration):
    from ..monitoring import track_document_processing as _track
    return _track(document_type, status, duration)

def performance_monitor(document_type):
    from ..monitoring import performance_monitor as _monitor
    return _monitor(document_type)

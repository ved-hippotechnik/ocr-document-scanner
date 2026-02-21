"""
Database optimization module for OCR Document Scanner

Provides database performance optimizations, index management,
query optimization, and performance metrics collection.
"""

# Delay imports to avoid circular dependency
def get_database_optimizer():
    from .optimizations import database_optimizer
    return database_optimizer

def get_setup_database_optimizations():
    from .optimizations import setup_database_optimizations
    return setup_database_optimizations

__all__ = [
    'get_database_optimizer',
    'get_setup_database_optimizations'
]
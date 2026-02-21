"""
DEPRECATED: User model has been consolidated into app.database.
Import from app.database instead:
    from app.database import db, User, LoginAttempt
"""
from ..database import db, User, LoginAttempt

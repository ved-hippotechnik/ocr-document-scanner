"""
Secure database query module with SQL injection prevention
"""
from typing import Any, Dict, List, Optional, Union
from sqlalchemy import text, select, update, delete, and_, or_
from sqlalchemy.orm import Session
from sqlalchemy.sql import ClauseElement
from flask_sqlalchemy import SQLAlchemy
import logging
import re

logger = logging.getLogger(__name__)


class SecureQueryBuilder:
    """Build secure parameterized queries to prevent SQL injection"""
    
    def __init__(self, db: SQLAlchemy):
        self.db = db
        self.session = db.session
    
    def validate_column_name(self, table_name: str, column_name: str) -> bool:
        """Validate that a column name exists and is safe"""
        # Only allow alphanumeric and underscore
        if not re.match(r'^[a-zA-Z0-9_]+$', column_name):
            raise ValueError(f"Invalid column name: {column_name}")
        
        # Check if column exists in table
        inspector = self.db.inspect(self.db.engine)
        columns = [col['name'] for col in inspector.get_columns(table_name)]
        
        if column_name not in columns:
            raise ValueError(f"Column {column_name} does not exist in table {table_name}")
        
        return True
    
    def validate_table_name(self, table_name: str) -> bool:
        """Validate that a table name exists and is safe"""
        # Only allow alphanumeric and underscore
        if not re.match(r'^[a-zA-Z0-9_]+$', table_name):
            raise ValueError(f"Invalid table name: {table_name}")
        
        # Check if table exists
        inspector = self.db.inspect(self.db.engine)
        tables = inspector.get_table_names()
        
        if table_name not in tables:
            raise ValueError(f"Table {table_name} does not exist")
        
        return True
    
    def safe_filter(self, model, filters: Dict[str, Any]) -> ClauseElement:
        """Build safe filter conditions"""
        conditions = []
        
        for column_name, value in filters.items():
            # Validate column name
            self.validate_column_name(model.__tablename__, column_name)
            
            # Get column attribute
            column = getattr(model, column_name)
            
            # Handle different filter operations
            if isinstance(value, dict):
                # Complex filters like {'$gte': 10, '$lte': 100}
                for op, val in value.items():
                    if op == '$eq':
                        conditions.append(column == val)
                    elif op == '$ne':
                        conditions.append(column != val)
                    elif op == '$gt':
                        conditions.append(column > val)
                    elif op == '$gte':
                        conditions.append(column >= val)
                    elif op == '$lt':
                        conditions.append(column < val)
                    elif op == '$lte':
                        conditions.append(column <= val)
                    elif op == '$in':
                        conditions.append(column.in_(val))
                    elif op == '$nin':
                        conditions.append(~column.in_(val))
                    elif op == '$like':
                        # Escape special characters in LIKE patterns
                        val = self.escape_like_pattern(val)
                        conditions.append(column.like(val))
                    elif op == '$ilike':
                        # Case-insensitive LIKE
                        val = self.escape_like_pattern(val)
                        conditions.append(column.ilike(val))
                    else:
                        raise ValueError(f"Unsupported operator: {op}")
            else:
                # Simple equality filter
                conditions.append(column == value)
        
        return and_(*conditions) if conditions else True
    
    def escape_like_pattern(self, pattern: str) -> str:
        """Escape special characters in LIKE patterns"""
        # Escape %, _, and \ characters
        pattern = pattern.replace('\\', '\\\\')
        pattern = pattern.replace('%', '\\%')
        pattern = pattern.replace('_', '\\_')
        return pattern
    
    def safe_select(self, model, filters: Optional[Dict] = None, 
                   order_by: Optional[str] = None, 
                   limit: Optional[int] = None,
                   offset: Optional[int] = None):
        """Execute a safe SELECT query"""
        query = self.session.query(model)
        
        # Apply filters
        if filters:
            filter_clause = self.safe_filter(model, filters)
            query = query.filter(filter_clause)
        
        # Apply ordering
        if order_by:
            # Parse order_by string (e.g., "created_at DESC")
            parts = order_by.split()
            column_name = parts[0]
            direction = parts[1].upper() if len(parts) > 1 else 'ASC'
            
            # Validate column and direction
            self.validate_column_name(model.__tablename__, column_name)
            if direction not in ['ASC', 'DESC']:
                raise ValueError(f"Invalid sort direction: {direction}")
            
            column = getattr(model, column_name)
            query = query.order_by(column.desc() if direction == 'DESC' else column.asc())
        
        # Apply pagination
        if limit:
            if not isinstance(limit, int) or limit < 0:
                raise ValueError(f"Invalid limit: {limit}")
            query = query.limit(limit)
        
        if offset:
            if not isinstance(offset, int) or offset < 0:
                raise ValueError(f"Invalid offset: {offset}")
            query = query.offset(offset)
        
        return query
    
    def safe_insert(self, model, data: Dict[str, Any]):
        """Execute a safe INSERT query"""
        # Validate all column names
        for column_name in data.keys():
            self.validate_column_name(model.__tablename__, column_name)
        
        # Create new instance
        instance = model(**data)
        self.session.add(instance)
        
        return instance
    
    def safe_update(self, model, filters: Dict[str, Any], updates: Dict[str, Any]):
        """Execute a safe UPDATE query"""
        # Validate all column names
        for column_name in updates.keys():
            self.validate_column_name(model.__tablename__, column_name)
        
        # Build filter clause
        filter_clause = self.safe_filter(model, filters)
        
        # Execute update
        query = update(model).where(filter_clause).values(**updates)
        result = self.session.execute(query)
        
        return result.rowcount
    
    def safe_delete(self, model, filters: Dict[str, Any]):
        """Execute a safe DELETE query"""
        # Build filter clause
        filter_clause = self.safe_filter(model, filters)
        
        # Execute delete
        query = delete(model).where(filter_clause)
        result = self.session.execute(query)
        
        return result.rowcount
    
    def safe_raw_query(self, query: str, params: Optional[Dict[str, Any]] = None):
        """Execute a safe raw SQL query with parameterization"""
        # Use SQLAlchemy's text() with bound parameters
        # This prevents SQL injection by properly escaping values
        stmt = text(query)
        
        if params:
            # Bind parameters safely
            stmt = stmt.bindparams(**params)
        
        result = self.session.execute(stmt)
        
        return result
    
    def safe_count(self, model, filters: Optional[Dict] = None) -> int:
        """Execute a safe COUNT query"""
        query = self.session.query(model)
        
        if filters:
            filter_clause = self.safe_filter(model, filters)
            query = query.filter(filter_clause)
        
        return query.count()
    
    def safe_aggregate(self, model, aggregation: str, column: str, filters: Optional[Dict] = None):
        """Execute safe aggregation queries"""
        from sqlalchemy import func
        
        # Validate column name
        self.validate_column_name(model.__tablename__, column)
        
        # Map aggregation functions
        agg_funcs = {
            'sum': func.sum,
            'avg': func.avg,
            'min': func.min,
            'max': func.max,
            'count': func.count,
        }
        
        if aggregation not in agg_funcs:
            raise ValueError(f"Unsupported aggregation: {aggregation}")
        
        agg_func = agg_funcs[aggregation]
        column_attr = getattr(model, column)
        
        query = self.session.query(agg_func(column_attr))
        
        if filters:
            filter_clause = self.safe_filter(model, filters)
            query = query.filter(filter_clause)
        
        return query.scalar()
    
    def sanitize_input(self, value: Any) -> Any:
        """Sanitize user input to prevent injection"""
        if isinstance(value, str):
            # Remove null bytes
            value = value.replace('\x00', '')
            
            # Limit string length
            max_length = 10000
            if len(value) > max_length:
                value = value[:max_length]
            
            # Remove control characters except newlines and tabs
            import string
            allowed = string.printable + '\n\t'
            value = ''.join(c for c in value if c in allowed)
        
        return value
    
    def validate_pagination(self, page: int, per_page: int) -> tuple:
        """Validate and sanitize pagination parameters"""
        # Ensure integers
        try:
            page = int(page)
            per_page = int(per_page)
        except (ValueError, TypeError):
            raise ValueError("Page and per_page must be integers")
        
        # Validate ranges
        if page < 1:
            page = 1
        if per_page < 1:
            per_page = 10
        if per_page > 100:
            per_page = 100  # Maximum items per page
        
        offset = (page - 1) * per_page
        
        return page, per_page, offset


class DatabaseSecurity:
    """Additional database security utilities"""
    
    @staticmethod
    def check_injection_patterns(query: str) -> bool:
        """Check for common SQL injection patterns"""
        dangerous_patterns = [
            r';\s*DROP\s+TABLE',
            r';\s*DELETE\s+FROM',
            r';\s*UPDATE\s+\w+\s+SET',
            r';\s*INSERT\s+INTO',
            r'UNION\s+SELECT',
            r'OR\s+1\s*=\s*1',
            r'AND\s+1\s*=\s*1',
            r'--\s*$',  # SQL comment at end
            r'/\*.*\*/',  # Block comments
            r'xp_cmdshell',  # SQL Server command execution
            r'EXEC\s*\(',  # Execute statements
            r'EXECUTE\s*\(',
            r'sp_executesql',  # SQL Server dynamic SQL
            r'INTO\s+OUTFILE',  # MySQL file write
            r'LOAD_FILE',  # MySQL file read
        ]
        
        query_upper = query.upper()
        for pattern in dangerous_patterns:
            if re.search(pattern, query_upper, re.IGNORECASE):
                logger.warning(f"Potential SQL injection detected: {pattern}")
                return True
        
        return False
    
    @staticmethod
    def escape_sql_identifier(identifier: str) -> str:
        """Escape SQL identifiers (table/column names)"""
        # Only allow alphanumeric and underscore
        if not re.match(r'^[a-zA-Z0-9_]+$', identifier):
            raise ValueError(f"Invalid SQL identifier: {identifier}")
        
        # Quote the identifier
        return f'"{identifier}"'
    
    @staticmethod
    def validate_order_direction(direction: str) -> str:
        """Validate sort direction"""
        direction = direction.upper()
        if direction not in ['ASC', 'DESC']:
            raise ValueError(f"Invalid sort direction: {direction}")
        return direction
    
    @staticmethod
    def create_safe_like_pattern(search_term: str, wildcard: str = 'both') -> str:
        """Create a safe LIKE pattern"""
        # Escape special characters
        search_term = search_term.replace('\\', '\\\\')
        search_term = search_term.replace('%', '\\%')
        search_term = search_term.replace('_', '\\_')
        
        # Add wildcards
        if wildcard == 'both':
            return f'%{search_term}%'
        elif wildcard == 'start':
            return f'{search_term}%'
        elif wildcard == 'end':
            return f'%{search_term}'
        else:
            return search_term
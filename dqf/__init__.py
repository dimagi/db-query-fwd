"""Execute SQL queries and forward results to web API endpoints."""

from .config import Config
from .core import execute_query, forward_to_api
from .logging_handlers import DatabaseHandler

__version__ = '0.1.0'

__all__ = [
    'Config',
    'DatabaseHandler',
    'execute_query',
    'forward_to_api',
]

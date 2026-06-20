"""Backward-compatible database connection import.

New code should import :class:`DBConnection` from ``database.connection``.
"""

from database.connection import DBConnection

__all__ = ["DBConnection"]

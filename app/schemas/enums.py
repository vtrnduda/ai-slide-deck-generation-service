"""
Enumerations for schema types.

Centralizes all enum definitions used across schemas to ensure
type safety and consistency throughout the application.
"""

from enum import Enum


class SlideType(str, Enum):
    """
    Enumeration of valid slide types
    """

    TITLE = "title"
    AGENDA = "agenda"
    CONTENT = "content"
    CONCLUSION = "conclusion"

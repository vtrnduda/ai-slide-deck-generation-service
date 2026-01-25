"""
Pydantic schemas for request and response models.

This module contains all the data models used for API validation and serialization.
Following the Domain-Driven Design principle, these schemas represent the
single source of truth for data structures in the application.

Organization:
- enums.py: Enumeration types (SlideType, etc.)
- request.py: Request models (LessonRequest)
- question.py: Question model for interactive exercises
- slide.py: Individual slide model
- presentation.py: Complete presentation model
- response.py: Legacy module (re-exports for backward compatibility)
"""

from app.schemas.enums import SlideType
from app.schemas.presentation import Presentation
from app.schemas.question import Question
from app.schemas.request import LessonRequest
from app.schemas.slide import Slide

__all__ = [
    "LessonRequest",
    "Presentation",
    "Question",
    "Slide",
    "SlideType",
]

"""
Legacy response module - kept for backward compatibility.

This module is deprecated. Import models from their specific modules:
- SlideType: from app.schemas.enums import SlideType
- Question: from app.schemas.question import Question
- Slide: from app.schemas.slide import Slide
- Presentation: from app.schemas.presentation import Presentation
"""

# Re-export for backward compatibility
from app.schemas.enums import SlideType
from app.schemas.presentation import Presentation
from app.schemas.question import Question
from app.schemas.slide import Slide

__all__ = ["SlideType", "Question", "Slide", "Presentation"]
from enum import Enum


class SlideType(str, Enum):
    """
    Enumeration of valid slide types
    """

    TITLE = "title"
    AGENDA = "agenda"
    CONTENT = "content"
    CONCLUSION = "conclusion"

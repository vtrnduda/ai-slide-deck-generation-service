from app.services import LLMEngine


def get_llm_engine() -> LLMEngine:
    """
    Get LLM engine instance for dependency injection.

    This function allows swapping the real implementation with a Mock in tests.
    Returns a new instance each time (stateless service).
    """
    return LLMEngine()

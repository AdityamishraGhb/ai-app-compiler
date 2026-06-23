"""
Exceptions for the LLM interaction module.
"""

class LLMError(Exception):
    """Base class for all LLM errors."""
    pass

class LLMRateLimitError(LLMError):
    """Raised when the LLM API rate limit is exceeded."""
    pass

class LLMValidationError(LLMError):
    """Raised when the LLM output cannot be parsed into the requested schema."""
    pass

class LLMCommunicationError(LLMError):
    """Raised when there's a network or API error communicating with the LLM provider."""
    pass

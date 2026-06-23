class RagCleanerError(Exception):
    """Base exception for rag-cleaner-cn."""


class UnsupportedInputError(RagCleanerError):
    """Raised when no loader can handle the provided input."""


class OutputValidationError(RagCleanerError):
    """Raised when exported files do not satisfy the expected schema."""


class OutputExistsError(RagCleanerError):
    """Raised when an output directory already exists and overwrite is disabled."""

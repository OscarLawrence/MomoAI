"""Custom exceptions for Petals operations."""


class PetalsError(Exception):
    """Base exception for all Petals-related errors."""

    pass


class NetworkError(PetalsError):
    """Raised when there are network connectivity issues."""

    pass


class NoPeersError(PetalsError):
    """Raised when no peers are available in the Petals network."""

    def __init__(self, model_name: str):
        self.model_name = model_name
        super().__init__(
            f"No peers available for model '{model_name}'. "
            "Please check if anyone is serving this model or try again later."
        )


class ModelLoadError(PetalsError):
    """Raised when a model fails to load."""

    def __init__(self, model_name: str, reason: str):
        self.model_name = model_name
        self.reason = reason
        super().__init__(f"Failed to load model '{model_name}': {reason}")


class GenerationError(PetalsError):
    """Raised when text generation fails."""

    pass
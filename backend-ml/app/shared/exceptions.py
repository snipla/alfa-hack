class ModelServiceError(Exception):
    """Base exception for ML model service errors."""


class ModelNotLoadedError(ModelServiceError):
    """Raised when inference is requested before the model has been loaded."""


class ModelLoadError(ModelServiceError):
    """Raised when the model file cannot be found or loaded."""


class ModelInferenceError(ModelServiceError):
    """Raised when feature preparation or model prediction fails."""

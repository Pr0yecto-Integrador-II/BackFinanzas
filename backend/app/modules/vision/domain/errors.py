from app.shared.errors import (
    PayloadTooLargeError,
    ServiceUnavailableError,
    TooManyRequestsError,
    UnsupportedMediaTypeError,
)


class VisionUnavailableError(ServiceUnavailableError):
    """El servicio de visión no está configurado o no respondió (HU20). HTTP 503."""

    message = "El análisis de imágenes no está disponible en este momento"

    @property
    def code(self) -> str:
        return "VISION_SERVICE_UNAVAILABLE"


class VisionRateLimitError(TooManyRequestsError):
    """Se superó el límite de análisis por usuario (HU20). HTTP 429."""

    message = "Has alcanzado el límite temporal de análisis de imágenes. Intenta más tarde"

    @property
    def code(self) -> str:
        return "VISION_RATE_LIMITED"


class ImageTooLargeError(PayloadTooLargeError):
    """La imagen supera el tamaño máximo (HU20). HTTP 413."""

    message = "La imagen es demasiado grande"

    @property
    def code(self) -> str:
        return "IMAGE_TOO_LARGE"


class UnsupportedImageError(UnsupportedMediaTypeError):
    """El archivo no es una imagen JPEG o PNG (HU20). HTTP 415."""

    message = "Solo se admiten imágenes JPEG o PNG"

    @property
    def code(self) -> str:
        return "UNSUPPORTED_IMAGE"


class EmptyImageError(UnsupportedImageError):
    """No llegó ninguna imagen. HTTP 415."""

    message = "No se recibió ninguna imagen"

    @property
    def code(self) -> str:
        return "EMPTY_IMAGE"

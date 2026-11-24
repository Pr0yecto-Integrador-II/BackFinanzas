from typing import Annotated

from fastapi import Depends

from app import composition
from app.modules.auth.api.deps import SettingsDep
from app.modules.vision.application.analyze_image import AnalyzeImage
from app.modules.vision.application.ports import ImageAnalyzer, RequestCounter


def get_vision_analyzer(settings: SettingsDep) -> ImageAnalyzer:
    return composition.image_analyzer(settings)


def get_vision_counter() -> RequestCounter:
    return composition.vision_request_counter()


def get_analyze_image(
    settings: SettingsDep,
    analyzer: Annotated[ImageAnalyzer, Depends(get_vision_analyzer)],
    counter: Annotated[RequestCounter, Depends(get_vision_counter)],
) -> AnalyzeImage:
    return AnalyzeImage(
        analyzer, counter, settings.vision_max_image_bytes, settings.vision_requests_per_hour
    )

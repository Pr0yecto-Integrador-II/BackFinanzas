from typing import Annotated

from fastapi import Depends

from app import composition
from app.modules.auth.api.deps import SettingsDep
from app.modules.speech.application.issue_token import IssueSpeechToken
from app.modules.speech.application.ports import RequestCounter, SpeechTokenProvider


def get_speech_provider(settings: SettingsDep) -> SpeechTokenProvider:
    return composition.speech_token_provider(settings)


def get_speech_counter() -> RequestCounter:
    return composition.speech_request_counter()


def get_issue_speech_token(
    provider: Annotated[SpeechTokenProvider, Depends(get_speech_provider)],
    counter: Annotated[RequestCounter, Depends(get_speech_counter)],
) -> IssueSpeechToken:
    return IssueSpeechToken(provider, counter)

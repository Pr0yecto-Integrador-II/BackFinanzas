from app.modules.speech.domain.entities import SpeechToken
from app.modules.speech.domain.errors import SpeechUnavailableError


class FakeSpeechProvider:
    """Proveedor de tokens en memoria: cuenta llamadas y puede simular caída."""

    def __init__(self, region: str = "eastus", down: bool = False) -> None:
        self.region = region
        self.down = down
        self.calls = 0

    async def issue(self) -> SpeechToken:
        self.calls += 1
        if self.down:
            raise SpeechUnavailableError
        return SpeechToken(token=f"tok-{self.calls}", region=self.region, expires_in_seconds=600)

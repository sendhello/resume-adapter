from anthropic import AsyncAnthropic
from core.settings import settings


class JobExtractor:
    def __init__(self, text: str):
        self.client = AsyncAnthropic(
            api_key=settings.anthropic_api_key.get_secret_value(),
        )
        self._text = text

    async def extract(self) -> list[str]:
        
import json
import logging

from openai import AsyncOpenAI, OpenAIError, PermissionDeniedError

from core.settings import settings
from gateways.prompts import BASE_INFORMATION, ADAPTING_RESUME, TSS482_ADAPTING, AU_RESUME, AU_COVER_LETTER
from schemas import Resume, ResumeType
import orjson
from schemas import ResumeResponse, Resume
from openai.types.shared.chat_model import ChatModel


logger = logging.getLogger(__name__)


ENGINEER_RESUME = "base_resume.json"
SA_RESUME = "base_resume_sa.json"


class AIClient:
    def __init__(self, use_cache: bool = False):
        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key.get_secret_value(),
            organization=settings.openai_organization_id,
            project=settings.openai_project_id,
        )
        self.use_cache = use_cache

    async def _chat_asc(self, prompt: str, text: str, model: ChatModel) -> str | None:
        """Асинхронный метод для отправки запроса к OpenAI API и получения ответа.
        """
        if self.use_cache:
            try:
                with open("cache.json", "rb") as f:
                    result = orjson.loads(f.read())
                    if not result:
                        raise FileNotFoundError

                    return result

            except FileNotFoundError as e:
                pass

        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": text},
                ],
                response_format={"type": "json_object"},
            )

            logger.debug(f"Response from OpenAI: {response}")
            if not response.choices:
                raise OpenAIError("Empty response from API.")

        except PermissionDeniedError as e:
            logger.error(f"Error in OpenAI chat completion: {e}")
            return None

        except Exception as e:
            logger.error(f"Error in OpenAI chat completion: {e}")
            return None

        result = response.choices[0].message.content

        with open("cache.json", "wb") as f:
            f.write(orjson.dumps(result))

        return result

    async def adaptating_resume(
            self,
            vacanсy_text: str,
            addition_text: str,
            model: ChatModel = settings.ai_model,
            resume_type: ResumeType = ResumeType.SoftwareEngineer
    ) -> Resume:
        """Adopting resume to the given language."""

        with open(SA_RESUME if resume_type == ResumeType.SistemAdministrator else ENGINEER_RESUME, "r") as f:
            base_resume = "My basic resume data: " + f.read()

            additional_data = ''
            if addition_text.strip():
                additional_data = "Additional information for the resume: " + addition_text

            visa_adapt = TSS482_ADAPTING if ResumeType.SoftwareEngineer else ""
            prompt = AU_RESUME + visa_adapt + BASE_INFORMATION + base_resume + additional_data

        answer = await self._chat_asc(prompt=prompt, text=vacanсy_text, model=model)
        resume = Resume.model_validate_json(answer)
        return resume

    async def adaptating_cover_letter(
            self,
            vacanсy_text: str,
            addition_text: str,
            model: ChatModel = settings.ai_model,
            resume_type: ResumeType = ResumeType.SoftwareEngineer
    ) -> str:
        """Adopting resume to the given language."""

        with open(SA_RESUME if resume_type == ResumeType.SistemAdministrator else ENGINEER_RESUME, "r") as f:
            base_resume = "My basic resume data: " + f.read()

            additional_data = ''
            if addition_text.strip():
                additional_data = "Additional information for the resume: " + addition_text

            visa_adapt = TSS482_ADAPTING if ResumeType.SoftwareEngineer else ""
            prompt = AU_COVER_LETTER + visa_adapt + BASE_INFORMATION + base_resume + additional_data

        answer = await self._chat_asc(prompt=prompt, text=vacanсy_text, model=model)
        return json.loads(answer)['cover_letter']


def get_ai_client(use_cache: bool = False) -> AIClient:
    return AIClient(use_cache=use_cache)

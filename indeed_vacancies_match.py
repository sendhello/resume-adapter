import argparse
import json
import os
import re
import sys
import time
from datetime import date
from pathlib import Path
from typing import Any

import requests

from indeed_search_links import BASE_URL, build_session, fetch_html, search_indeed_links
from vacancy_parser import parse_vacancy_text


SYSTEM_PROMPT = """
You are an experienced HR recruiter.
Your task is to evaluate how well a resume matches a job vacancy.

Rules:
- Return only JSON object with one field: {"match": <integer 0..100>}.
- Score must be strict, realistic, and based only on provided data.
- Consider skills, years/seniority, domain relevance, responsibilities, and fit.
- 0 means no fit, 100 means near-perfect fit.
""".strip()


class MatchError(RuntimeError):
    pass


class IndeedHtmlFetcher:
    def __init__(self, timeout_seconds: float = 30.0, retries: int = 6, retry_delay_seconds: float = 1.5):
        self.timeout_seconds = timeout_seconds
        self.retries = retries
        self.retry_delay_seconds = retry_delay_seconds
        self.session: Any | None = None

    def start(self) -> None:
        if self.session is not None:
            return
        self.session = build_session()
        self._warmup()

    def close(self) -> None:
        if self.session is None:
            return
        close_session = getattr(self.session, "close", None)
        if callable(close_session):
            close_session()
        self.session = None

    def fetch(self, url: str) -> str:
        if self.session is None:
            self.start()

        assert self.session is not None
        last_exc: Exception | None = None
        for attempt in range(1, self.retries + 1):
            try:
                return fetch_html(self.session, url, self.timeout_seconds)
            except Exception as exc:
                last_exc = exc
                if attempt >= self.retries:
                    break
                if self._is_403_error(exc):
                    self._recreate_session()
                time.sleep(self.retry_delay_seconds * attempt)

        raise last_exc or MatchError("Unable to fetch Indeed vacancy page")

    def _warmup(self) -> None:
        if self.session is None:
            return
        try:
            fetch_html(self.session, BASE_URL, self.timeout_seconds)
        except Exception:
            pass

    def _recreate_session(self) -> None:
        old_session = self.session
        self.session = build_session()
        self._warmup()
        if old_session is not None:
            close_session = getattr(old_session, "close", None)
            if callable(close_session):
                close_session()

    @staticmethod
    def _is_403_error(exc: Exception) -> bool:
        message = str(exc).lower()
        return "403" in message or "forbidden" in message or "bot protection" in message


def _build_user_prompt(resume_data: dict[str, Any], vacancy_text: str, url: str) -> str:
    return (
        "Resume JSON:\n"
        f"{json.dumps(resume_data, ensure_ascii=False)}\n\n"
        "Vacancy URL:\n"
        f"{url}\n\n"
        "Vacancy text:\n"
        f"{vacancy_text}\n\n"
        "Return JSON only."
    )


def _extract_json_object(raw_text: str) -> dict[str, Any]:
    raw_text = raw_text.strip()
    try:
        parsed = json.loads(raw_text)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", raw_text, flags=re.S)
    if not match:
        raise MatchError("AI response is not valid JSON")

    try:
        parsed = json.loads(match.group(0))
    except json.JSONDecodeError as exc:
        raise MatchError("AI response JSON cannot be parsed") from exc

    if not isinstance(parsed, dict):
        raise MatchError("AI response JSON is not an object")
    return parsed


def _normalize_match(value: Any) -> int:
    if isinstance(value, bool):
        raise MatchError("Invalid match type: bool")
    try:
        match = int(round(float(value)))
    except (TypeError, ValueError) as exc:
        raise MatchError("Invalid match value") from exc
    return max(0, min(100, match))


class AIHRMatcher:
    def __init__(self, provider: str, model: str | None, timeout_seconds: float = 60.0):
        self.provider = provider.lower().strip()
        self.timeout_seconds = timeout_seconds
        self.openai_client: Any | None = None
        self.anthropic_api_key: str | None = None

        if self.provider == "openai":
            try:
                from openai import OpenAI
            except ModuleNotFoundError as exc:
                raise MatchError("Package 'openai' is not installed in current environment") from exc

            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise MatchError("OPENAI_API_KEY is required for provider=openai")

            self.model = model or os.getenv("AI_MODEL") or "gpt-5.2"
            self.openai_client = OpenAI(
                api_key=api_key,
                organization=os.getenv("OPENAI_ORGANIZATION_ID"),
                project=os.getenv("OPENAI_PROJECT_ID"),
                timeout=timeout_seconds,
            )
            return

        if self.provider == "anthropic":
            self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
            if not self.anthropic_api_key:
                raise MatchError("ANTHROPIC_API_KEY is required for provider=anthropic")
            self.model = model or os.getenv("ANTHROPIC_MODEL") or "claude-3-5-sonnet-latest"
            return

        raise MatchError("Unsupported provider. Use 'openai' or 'anthropic'")

    def score_match(self, resume_data: dict[str, Any], vacancy_text: str, url: str) -> int:
        prompt = _build_user_prompt(resume_data=resume_data, vacancy_text=vacancy_text, url=url)
        if self.provider == "openai":
            return self._score_openai(prompt=prompt)
        return self._score_anthropic(prompt=prompt)

    def _score_openai(self, prompt: str) -> int:
        if self.openai_client is None:
            raise MatchError("OpenAI client is not initialized")

        response = self.openai_client.chat.completions.create(
            model=self.model,
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )
        content = response.choices[0].message.content if response.choices else None
        if not content:
            raise MatchError("OpenAI returned empty response")

        parsed = _extract_json_object(content)
        return _normalize_match(parsed.get("match"))

    def _score_anthropic(self, prompt: str) -> int:
        payload = {
            "model": self.model,
            "max_tokens": 256,
            "temperature": 0,
            "system": SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": prompt}],
        }
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": self.anthropic_api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json=payload,
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()

        text_chunks = [
            chunk.get("text", "")
            for chunk in data.get("content", [])
            if isinstance(chunk, dict) and chunk.get("type") == "text"
        ]
        raw_text = "\n".join(text_chunks).strip()
        if not raw_text:
            raise MatchError("Anthropic returned empty response")

        parsed = _extract_json_object(raw_text)
        return _normalize_match(parsed.get("match"))


def _load_resume(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise MatchError(f"Resume file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise MatchError(f"Resume file is not valid JSON: {path}") from exc

    if not isinstance(data, dict):
        raise MatchError("Resume JSON must be an object")
    return data


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Find Indeed vacancies and score resume match with AI (sync).")
    parser.add_argument("--provider", choices=("openai", "anthropic"), default=os.getenv("AI_PROVIDER", "openai"))
    parser.add_argument("--model", default=None, help="LLM model name. If omitted, provider default is used.")
    parser.add_argument("--resume", default="base_resume.json", help="Path to resume JSON file.")
    parser.add_argument("--pages", type=int, default=1, help="How many Indeed search pages to fetch.")
    parser.add_argument("--pause", type=float, default=0.7, help="Pause between search pages (seconds).")
    parser.add_argument("--pause-per-vacancy", type=float, default=0.8, help="Pause between vacancy requests.")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of vacancies to process.")
    parser.add_argument(
        "--indeed-retries",
        type=int,
        default=6,
        help="How many retries for Indeed vacancy page fetch when blocked.",
    )
    parser.add_argument(
        "--indeed-retry-delay",
        type=float,
        default=1.5,
        help="Base delay between Indeed page retries (seconds).",
    )
    parser.add_argument("--max-vacancy-chars", type=int, default=16000, help="Trim vacancy text before AI call.")
    parser.add_argument("--ai-timeout", type=float, default=60.0, help="Timeout for AI request.")
    parser.add_argument(
        "--output",
        default=None,
        help="Output JSON file path. Default: indeed_vacancies_<today>.json",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()

    if args.pages < 1:
        print("pages must be >= 1", file=sys.stderr)
        return 1
    if args.limit is not None and args.limit < 1:
        print("limit must be >= 1", file=sys.stderr)
        return 1
    if args.indeed_retries < 1:
        print("indeed-retries must be >= 1", file=sys.stderr)
        return 1

    try:
        resume_data = _load_resume(Path(args.resume))
        matcher = AIHRMatcher(provider=args.provider, model=args.model, timeout_seconds=args.ai_timeout)
    except Exception as exc:
        print(f"Initialization failed: {exc}", file=sys.stderr)
        return 1

    try:
        links = search_indeed_links(pages=args.pages, pause_seconds=args.pause)
    except Exception as exc:
        print(f"Failed to fetch Indeed links: {exc}", file=sys.stderr)
        return 1

    if args.limit is not None:
        links = links[: args.limit]

    if not links:
        print("No vacancies found. Nothing to process.", file=sys.stderr)
        return 1

    fetcher = IndeedHtmlFetcher(
        timeout_seconds=30.0,
        retries=args.indeed_retries,
        retry_delay_seconds=args.indeed_retry_delay,
    )
    fetcher.start()

    results: list[dict[str, Any]] = []
    total = len(links)
    try:
        for idx, url in enumerate(links, start=1):
            print(f"[{idx}/{total}] Processing {url}", file=sys.stderr)
            vacancy_text = ""

            try:
                if "indeed." in url:
                    vacancy_html = fetcher.fetch(url)
                    vacancy_text = parse_vacancy_text(url=url, html=vacancy_html)
                else:
                    vacancy_text = parse_vacancy_text(url=url)
            except Exception as exc:
                print(f"  Parsing failed: {exc}", file=sys.stderr)

            match_value = 0
            if vacancy_text.strip():
                try:
                    match_value = matcher.score_match(
                        resume_data=resume_data,
                        vacancy_text=vacancy_text[: args.max_vacancy_chars],
                        url=url,
                    )
                except Exception as exc:
                    print(f"  AI matching failed: {exc}", file=sys.stderr)

            results.append({"url": url, "match": match_value})

            if args.pause_per_vacancy > 0 and idx < total:
                time.sleep(args.pause_per_vacancy)
    finally:
        fetcher.close()

    output_path = Path(args.output) if args.output else Path(f"indeed_vacancies_{date.today().isoformat()}.json")
    output_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved {len(results)} rows to {output_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

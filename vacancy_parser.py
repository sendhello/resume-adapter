import json
import re
import sys
import urllib.request
from dataclasses import dataclass
from html import unescape
from html.parser import HTMLParser
from typing import Callable, Iterable, List, Optional, Tuple


@dataclass
class _Matcher:
    """Описание условия, по которому считаем, что мы вошли в нужный контейнер с текстом вакансии."""

    name: str
    predicate: Callable[[str, List[Tuple[str, Optional[str]]]], bool]


class _TextExtractor(HTMLParser):
    """
    Простенький извлекатель текста из HTML с возможностью «прицельно» собирать
    текст только из подходящих контейнеров (по id/class/атрибутам),
    игнорируя script/style и прочий шум.
    """

    def __init__(self, matchers: Iterable[_Matcher]):
        super().__init__(convert_charrefs=True)
        self._matchers = list(matchers)
        self._capture_stack: List[str] = []  # стек тегов, внутри которых мы собираем текст
        self._skip_stack: List[str] = []  # script/style
        self._chunks: List[str] = []

    @staticmethod
    def _attrs_to_dict(attrs: List[Tuple[str, Optional[str]]]) -> dict:
        return {k: (v or "") for k, v in attrs}

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]):
        # Пропускаем скрипты/стили
        if tag in ("script", "style", "noscript", "svg"):
            self._skip_stack.append(tag)
            return

        # Уже внутри целевого контейнера — просто углубляемся
        if self._capture_stack:
            self._capture_stack.append(tag)
            return

        # Ищем вход в целевой контейнер по любому из матчеров
        for m in self._matchers:
            try:
                if m.predicate(tag, attrs):
                    self._capture_stack.append(tag)
                    return
            except Exception:
                # Никогда не роняем парсер из-за ошибки предиката
                continue

    def handle_endtag(self, tag: str):
        if self._skip_stack and self._skip_stack[-1] == tag:
            self._skip_stack.pop()
            return

        if self._capture_stack:
            # Выходим из контейнера — когда стек опустеет
            if self._capture_stack[-1] == tag:
                self._capture_stack.pop()

    def handle_data(self, data: str):
        if self._skip_stack:
            return
        if self._capture_stack:
            text = data.strip()
            if text:
                # Нормализуем пробелы в строке, но переносы оставим при объединении
                text = re.sub(r"\s+", " ", text)
                self._chunks.append(text)

    def get_text(self) -> str:
        # Склеиваем с сохранением «абзацности» на основе встреченных блоков
        raw = " ".join(self._chunks)
        raw = unescape(raw)

        # Добавим эвристику разбиения на абзацы по точкам с заглавной буквой и маркерам
        # и чуть подчистим множественные пробелы/переносы.
        text = re.sub(r"[ \t]+", " ", raw)
        text = re.sub(r"\s*\n\s*", "\n", text)
        # Выровняем множественные пробелы и переносы
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()


def _contains_word(value: str, *needles: str) -> bool:
    v = value.lower()
    return any(n in v for n in needles)


def _matcher_by_id(*ids: str) -> _Matcher:
    ids_l = tuple(i.lower() for i in ids)

    def _pred(tag: str, attrs: List[Tuple[str, Optional[str]]]) -> bool:
        for k, v in attrs:
            if k == "id" and v and v.lower() in ids_l:
                return True
        return False

    return _Matcher(name=f"id={'|'.join(ids)}", predicate=_pred)


def _matcher_by_attr_contains(attr: str, *substrings: str) -> _Matcher:
    subs_l = tuple(s.lower() for s in substrings)

    def _pred(tag: str, attrs: List[Tuple[str, Optional[str]]]) -> bool:
        for k, v in attrs:
            if k == attr and v and _contains_word(v, *subs_l):
                return True
        return False

    return _Matcher(name=f"{attr}~={'|'.join(substrings)}", predicate=_pred)


def _matcher_by_attr_equals(attr: str, *values: str) -> _Matcher:
    values_l = tuple(v.lower() for v in values)

    def _pred(tag: str, attrs: List[Tuple[str, Optional[str]]]) -> bool:
        for k, v in attrs:
            if k == attr and v and v.lower() in values_l:
                return True
        return False

    return _Matcher(name=f"{attr}={'|'.join(values)}", predicate=_pred)


def _default_matchers_for(url: Optional[str]) -> List[_Matcher]:
    """Подбираем набор матчеров под популярные доски + общий фолбэк."""
    host = (url or "").lower()
    m: List[_Matcher] = []

    # SEEK: основное содержимое вакансии
    if "seek.com" in host:
        m.append(_matcher_by_attr_equals("data-automation", "jobAdDetails", "jobAdDetailsContainer"))
        m.append(_matcher_by_attr_contains("class", "job-ad-content", "jobAdDetails"))

    # INDEED
    if "indeed." in host:
        m.append(_matcher_by_id("jobDescriptionText"))
        m.append(_matcher_by_attr_contains("class", "jobsearch-JobComponent-description", "jobsearch-jobDescriptionText"))

    # LINKEDIN
    if "linkedin." in host:
        m.append(_matcher_by_attr_contains("class", "show-more-less-html__markup", "jobs-description-content__text", "description__text"))

    # Общие эвристики: article/main/section/div с классами/айди про описание
    m.append(_matcher_by_attr_contains("id", "jobdescription", "description", "job-details", "jobcontent"))
    m.append(_matcher_by_attr_contains("class", "job-description", "description", "jd__content", "vacancy__description"))
    return m


def _extract_from_json_ld(html: str) -> Optional[str]:
    """Пытаемся достать описание из JSON-LD (application/ld+json), часто встречается у LinkedIn/Indeed/Seek."""
    results: List[str] = []
    for m in re.finditer(r"<script[^>]+type=\"application/ld\+json\"[^>]*>(.*?)</script>", html, flags=re.I | re.S):
        block = m.group(1).strip()
        # Бывает, что внутри встречается несколько JSON-объектов подряд. Пытаемся парсить по одному.
        candidates = [block]
        # Иногда HTML-комментарии попадаются
        candidates = [re.sub(r"<!--.*?-->", "", c, flags=re.S) for c in candidates]
        for c in candidates:
            try:
                data = json.loads(c)
            except Exception:
                # Попробуем почистить html-сущности и повторить
                try:
                    data = json.loads(unescape(c))
                except Exception:
                    continue

            def pick_desc(obj) -> Optional[str]:
                if isinstance(obj, dict):
                    if "description" in obj and isinstance(obj["description"], str):
                        return obj["description"]
                    # иногда описание внутри "jobPosting" или "headline"
                    for key in ("jobPosting", "mainEntityOfPage"):
                        if key in obj and isinstance(obj[key], dict):
                            d = pick_desc(obj[key])
                            if d:
                                return d
                if isinstance(obj, list):
                    for it in obj:
                        d = pick_desc(it)
                        if d:
                            return d
                return None

            desc_html = pick_desc(data)
            if desc_html:
                # Очищаем от тегов
                text = re.sub(r"<[^>]+>", " ", desc_html)
                text = unescape(text)
                text = re.sub(r"\s+", " ", text).strip()
                if text:
                    results.append(text)

    # Берём самое длинное совпадение
    if results:
        return max(results, key=len)
    return None


def _fetch_html(url: str, timeout: float = 15.0) -> str:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/121.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9,ru;q=0.8",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    req = urllib.request.Request(url, headers=headers, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        content_type = resp.headers.get("Content-Type", "")
        charset = "utf-8"
        m = re.search(r"charset=([\w-]+)", content_type)
        if m:
            charset = m.group(1)
        data = resp.read()
        try:
            return data.decode(charset, errors="replace")
        except Exception:
            return data.decode("utf-8", errors="replace")


def parse_vacancy_text(url: Optional[str] = None, html: Optional[str] = None) -> str:
    """
    Возвращает очищенный текст описания вакансии с популярных досок (Seek, LinkedIn, Indeed и др.).

    Параметры:
    - url: ссылка на страницу вакансии (опционально, но хотя бы url или html должны быть заданы)
    - html: исходный HTML страницы (если уже получен вне этой функции)

    Функция сначала пробует извлечь описание из JSON-LD (если присутствует),
    затем — парсит DOM и вытаскивает текст из наиболее вероятных контейнеров
    (по id/class/атрибутам), игнорируя скрипты и лишний шум.

    Возвращает:
      Строку с текстом описания вакансии. Если ничего надёжно не найдено —
      возвращает пустую строку или общий текст страницы (как фолбэк).
    """
    if not html and not url:
        raise ValueError("Необходимо передать либо url, либо html")

    # Загружаем HTML при необходимости
    page_html = html or _fetch_html(url)  # type: ignore[arg-type]

    # 1) Попробуем JSON-LD
    desc = _extract_from_json_ld(page_html)
    if desc:
        return desc

    # 2) Парсинг DOM с таргетированными матчерами
    extractor = _TextExtractor(matchers=_default_matchers_for(url))
    try:
        extractor.feed(page_html)
        text = extractor.get_text()
        if text and len(text) > 80:  # легкая эвристика, чтобы отбрасывать мусор
            return text
    except Exception:
        # не падаем, пробуем общий фолбэк
        pass

    # 3) Общий фолбэк: вытащить максимум текста из <main>/<article>
    generic = _TextExtractor(
        matchers=[
            _matcher_by_attr_contains("class", "content", "main", "article"),
            _matcher_by_attr_contains("id", "content", "main", "article"),
        ]
    )
    try:
        generic.feed(page_html)
        text = generic.get_text()
        return text
    except Exception:
        return ""


if __name__ == "__main__":
    # Небольшая CLI-проверка: python vacancy_parser.py <url>
    if len(sys.argv) > 1:
        url_ = sys.argv[1]
        try:
            print(parse_vacancy_text(url_))
        except Exception as e:
            sys.stderr.write(f"Ошибка: {e}\n")
            sys.exit(1)
    else:
        print("Usage: python vacancy_parser.py <url>")

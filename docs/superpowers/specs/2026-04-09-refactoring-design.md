# Resume Adapter - Refactoring Design Spec

## Problem

Приложение resume-adapter сильно привязано к конкретному пользователю (Ivan Bazhenov), конкретной профессии (Python Backend Engineer) и конкретной машине (macOS CloudDocs path). Настройки смешаны с логикой: личные данные захардкожены в промптах, PDF-генераторе и main.py. Приложение не может быть использовано для не-IT профессий без правки кода.

## Goal

Сделать приложение универсальным для любой профессии на австралийском рынке труда. Разделить зоны настроек от зон расчёта. Сохранить текущую функциональность.

## Scope

**В скоупе:** main.py, schemas.py, pdf.py, gateways/ (openai.py, claude.py, prompts.py), core/ (settings.py)
**Вне скоупа:** indeed_search_links.py, indeed_vacancies_match.py, parse_labour_agreements.py, vacancy_parser.py

---

## Stage 1: Configuration - Separation of Settings from Code

### What changes

**New file: `config.yaml`**

```yaml
personal:
  name: "Ivan Bazhenov"
  phone: "0466 284 180"
  email: "bazhenov.in@gmail.com"
  linkedin: "linkedin.com/in/sendhello"
  github: "github.com/sendhello"
  location: "Melbourne, VIC"

paths:
  output_dir: "/Users/ivanbazhenov/Library/Mobile Documents/com~apple~CloudDocs/Documents/Look a Job"
  vacancy_file: "vacancy.txt"

ai:
  default_provider: "openai"  # openai | claude
  openai_model: "gpt-5.2"
  claude_model: "claude-opus-4-6"

resume:
  default_type: "engineer"
  templates:
    engineer: "resumes/base_resume.json"
    sa: "resumes/base_resume_sa.json"
```

**Modified: `core/settings.py`**

- Loads `config.yaml` alongside `.env`
- `.env` stays for secrets only (API keys)
- Exposes config values via `settings` object
- Adds YAML loading with `pyyaml` dependency

**Modified: `main.py`**

- Line 85: Replace hardcoded CloudDocs path with `settings.output_dir`
- `--resume-type` accepts any key from `config.resume.templates` (not just engineer/sa)
- Remove hardcoded enum mapping, use config lookup instead

**Modified: `pdf.py`**

- Line 257: `author` default comes from `settings.personal.name`
- Lines 274-278: Cover letter signature block uses personal config values

**Modified: `schemas.py`**

- `ResumeType` enum removed. Resume type is now a string key from config
- Fix typo: `SistemAdministrator` -> no longer needed

**New file: `config.yaml.example`** - template for new users

**New directory: `resumes/`** - move base_resume.json and base_resume_sa.json here

### Files to modify
- `core/settings.py` - add YAML config loading
- `main.py` - use settings for paths and resume type selection
- `pdf.py` - use settings for author/personal data
- `schemas.py` - remove ResumeType enum
- `gateways/openai.py` - use settings for resume file paths
- `gateways/claude.py` - use settings for resume file paths
- `pyproject.toml` - add `pyyaml` dependency

---

## Stage 2: Universal Prompts

### What changes

**Modified: `gateways/prompts.py`**

Remove all IT-specific and candidate-specific content from prompts. Make them parameterized.

`AU_RESUME` becomes:
```
You are an Australian resume writer specialising in ATS optimisation.

Context:
{candidate_context}

Task:
Given a job description and base resume data (JSON), create a tailored Australian-style resume.
...
```

- Remove: "tech roles", "Senior Python Backend Engineer", "Student visa, 48 hrs/fortnight"
- The `{candidate_context}` is built at runtime from config (role, location, work_rights)
- Work rights template moves to config.yaml:
  ```yaml
  personal:
    work_rights: "Onshore in Melbourne with current Australian work rights. Available for contract, fixed-term, and part-time roles."
    sponsorship_note: "Eligible for Subclass 482 employer sponsorship."
  ```

`AU_COVER_LETTER` becomes similarly parameterized:
- Remove: "tech professional", "Senior Python Backend Engineer"
- Remove: hardcoded non-traditional sector examples ("healthcare, aged care, payroll")

Delete unused `ADAPTING_RESUME` prompt.

**Modified: `gateways/openai.py` and `gateways/claude.py`**

- Build prompt with candidate context from config before passing to `_chat_asc`
- Replace `vacanсy_text` (Cyrillic с) -> `vacancy_text` (ASCII s) everywhere

### Files to modify
- `gateways/prompts.py` - parameterize prompts
- `gateways/openai.py` - build context, fix typo
- `gateways/claude.py` - build context, fix typo
- `main.py` - fix typo in variable name
- `config.yaml` - add work_rights and sponsorship_note

---

## Stage 3: Resume Template System

### What changes

- `config.yaml` `resume.templates` maps arbitrary names to JSON files
- CLI `--resume-type` validates against available template keys at runtime
- Users can add new resume types by:
  1. Creating a new JSON file in `resumes/`
  2. Adding the mapping to `config.yaml`

**Modified: `schemas.py`**

Check Resume model universality:
- `github` field: make optional (not relevant for non-IT)
- `linkedin` field: keep required (universal)
- `hobbies` field: keep optional
- Consider making `key_skills` more flexible (already dict[str, list[str]] - universal enough)

```python
class Resume(BaseModel):
    company_name: str
    name: str
    title: str
    phone: str
    email: str
    linkedin: str
    github: str = ""  # optional for non-IT
    address: str
    professional_summary: str
    key_skills: dict[str, list[str]]
    work_experience: list[Experience]
    education: list[Education]
    other_educations: list[Education] = []  # optional
    languages: list[str] = []  # optional
    hobbies: list[str] = []  # optional
    work_rights: str = ""  # optional
```

**Modified: `pdf.py`**

- GitHub line in resume PDF: only render if `resume.github` is not empty
- Cover letter signature: only include GitHub/LinkedIn lines if values exist

### Files to modify
- `schemas.py` - make fields optional
- `pdf.py` - conditional rendering
- `main.py` - dynamic template loading

---

## Stage 4: main.py Refactoring

### What changes

Clean up the main flow:

```python
async def main():
    config = load_config()
    args = parse_args(config)
    
    vacancy_text = load_vacancy(config)
    addition_text = load_addition(args)
    
    ai_client = create_ai_client(args, config)
    
    resume, cover_letter = await adapt(ai_client, vacancy_text, addition_text, args)
    
    output_dir = prepare_output_dir(config, resume.company_name)
    generate_pdfs(output_dir, resume, cover_letter, config)
    save_vacancy(output_dir, config)
```

- Extract functions with clear names
- Remove duplicated resume file reading logic from openai.py/claude.py - centralize in main
- Fix variable naming consistency

### Files to modify
- `main.py` - restructure into clean functions

---

## Stage 5: Bug Fixes and Finalization

### What changes

1. **Cache keying**: Hash vacancy text to create unique cache keys. Store in `cache/` directory as `{hash}.json` instead of single `cache.json`

2. **Dependencies**: Add `anthropic` and `pyyaml` to `pyproject.toml`

3. **Create `config.yaml.example`**: Template with placeholder values

4. **Clean `.env.example`**: Only API keys, remove model settings (moved to config.yaml)

5. **Remove `RemoteSoftwareEngineer`** from ResumeType (unused, and enum is being removed anyway)

### Files to modify
- `gateways/openai.py` - keyed cache
- `gateways/claude.py` - keyed cache
- `pyproject.toml` - add dependencies
- Create `config.yaml.example`
- Update `.env.example`

---

## Verification

After each stage, verify by running:
```bash
python main.py --provider openai --resume-type engineer --cache
```

After all stages:
1. Run without `--cache` to verify real API calls work
2. Check generated PDFs in output directory
3. Verify cache is keyed per vacancy
4. Test with a non-IT resume template to confirm universality

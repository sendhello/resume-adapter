# Resume Build

> Адаптация резюме и cover letter под конкретную вакансию с генерацией PDF

## Что делает

- Читает вакансию из `vacancy.txt` и базовое резюме из JSON
- Адаптирует резюме под вакансию (ключевые навыки, достижения, summary)
- Генерирует tailored cover letter
- Создаёт профессиональные PDF через ReportLab

## Использование

```
/resume_build          # тип резюме по умолчанию (engineer)
/resume_build sa       # системный администратор
```

## Требования

- Python 3.11+ с `reportlab`, `pydantic`, `pyyaml`
- Рабочая директория: `/Users/ivanbazhenov/Projects/resume-adapter/`
- Файлы: `config.yaml`, `vacancy.txt`, `resumes/base_resume.json`

## Выходные файлы

В папке `{output_dir}/{company_name}/`:
- `resume.pdf` — адаптированное резюме
- `cover_letter.pdf` — сопроводительное письмо
- `adapted_resume.json` — JSON с адаптированными данными
- `cover_letter.txt` — текст cover letter
- `vacancy.txt` — копия вакансии

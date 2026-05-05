---
name: resume-build
description: "Adapt a resume and cover letter for a job vacancy, then generate PDFs. Use when the user says 'resume_build', 'build resume', 'adapt resume', or wants to tailor their CV to a job posting."
effort: high
metadata:
  version: 1.0.0
  creator: Ivan Bazhenov
---

# Resume Build

Adapt a base resume and generate a tailored cover letter for a specific job vacancy, then produce professional PDFs.

## Prerequisites

- Python 3.11+ with `reportlab`, `pydantic`, and `pyyaml` installed
- Working directory: the project root (where this skill is located)
- Required files: `config.yaml`, `vacancy.txt`, `resumes/` directory
- Optional: `addition.txt` for extra candidate context

## Workflow

### Step 1: Read inputs

1. Read `config.yaml` from the project root. Extract:
   - `personal.*` — candidate personal info
   - `paths.output_dir` — where to save results
   - `resume.default_type` — default resume template key
   - `resume.templates` — mapping of type to JSON file path

2. Read `vacancy.txt` from the project root — the job description.

3. Try to read `addition.txt` from the project root. If it does not exist or is empty, skip it.

4. Determine resume type:
   - If the user specified a type (e.g., `/resume_build sa`), use that key
   - Otherwise use `resume.default_type` from config.yaml
   - Look up the JSON file path from `resume.templates[type]`

5. Read the base resume JSON file (e.g., `resumes/base_resume.json`).

### Step 2: Build candidate context

From `config.yaml` personal section, build a context string:
- "The candidate is based in {personal.location}."
- If `personal.work_rights` exists, append it.
- If `personal.sponsorship_note` exists, append: "Only if the job ad explicitly mentions sponsorship, note: {sponsorship_note}"

### Step 3: Adapt the resume

You are an Australian resume writer specialising in ATS optimisation.

Use the candidate context from Step 2.

Given the job description (vacancy.txt) and base resume data (JSON), create a tailored Australian-style resume.

**Resume structure (Australian standard):**
1. Contact Information (name, phone, email, LinkedIn, portfolio/website, location)
2. Professional Summary (3-4 sentences with job-relevant keywords)
3. Key Skills (grouped by category, reordered by relevance to this role)
4. Work Experience (achievement-focused bullet points with metrics)
5. Personal Projects (if relevant to the role)
6. Education
7. Additional Education / Certifications
8. Languages
9. Work Rights

**Adaptation rules:**
1. Extract all keywords from the job description: title, skills, tools, responsibilities, industry terms.
2. Map job requirements to resume content:
   a) Skill clearly present -> sharpen the wording, add specifics.
   b) Skill present but weak -> rewrite with concrete evidence (action, tool, result).
   c) Related experience exists -> add truthful transferable statement.
   d) No evidence at all -> do not add. Do not fabricate.
3. Rewrite professional_summary using the most relevant keywords. Lead with domain match if applicable.
4. Reorder key_skills so the most relevant category appears first.
5. Reorder bullet points within each position: most relevant to this job goes to the top.
6. Keep all positions. Do not remove work history.

**Work rights field:**
- Use the candidate's work rights information as provided. Do not alter it unless the job ad explicitly mentions sponsorship, in which case append the sponsorship note if provided.

**Writing style:**
- Achievement-focused: "Reduced X by Y% by doing Z" not "Responsible for managing Z".
- Direct and specific. No filler words, no promotional language.
- Use standard hyphen "-" only. No en-dash or em-dash.
- No tables, icons, or images. ATS-friendly plain text.

**Anti-AI writing rules (CRITICAL - follow every one):**
- BANNED words/phrases: pivotal, crucial, landscape, fostering, showcasing, commitment to, serves as, stands as, testament to, underscores, highlights, enduring, vibrant, rich (figurative), profound, nestled, groundbreaking, renowned, delve, tapestry, interplay, intricate, garner, encompassing, cultivating, leveraging, spearheading.
- No "-ing" phrase endings on bullet points (e.g., "...enhancing team productivity", "...ensuring quality", "...contributing to growth"). End with the concrete result instead.
- Use "is/are/has" instead of "serves as/stands as/functions as/boasts/features".
- No rule-of-three patterns ("X, Y, and Z" repeated across bullets). Vary grouping sizes.
- No negative parallelisms ("Not only X but also Y", "It's not just X, it's Y").
- No false ranges ("from X to Y, from A to B").
- No filler: "In order to" -> "To", "Due to the fact that" -> "Because", "It is important to note that" -> cut it.
- No significance inflation: don't say something is "significant" or "critical" - let the metrics speak.
- Vary sentence length and structure. Don't make every bullet the same rhythm.
- Use straight quotes, not curly quotes.
- Do not uniformly hyphenate common compounds (cross-functional, data-driven, end-to-end, high-quality). Humans are inconsistent with these.

**If addition.txt was loaded**, treat its content as additional information about the candidate. Incorporate relevant details into the adapted resume where appropriate.

**Merge rules — CRITICAL:**
From the base resume, ONLY replace these fields:
- `company_name` — set to the company name from the job description
- `title` — set to the job title from the job description
- `professional_summary` — rewritten for this role
- `key_skills` — reordered and sharpened for this role
- `work_experience` — achievements rewritten and reordered for this role

All other fields MUST be copied exactly from the base resume:
- `name`, `phone`, `email`, `linkedin`, `github`, `address`
- `personal_projects` — copy from base resume; include only projects relevant to this role, drop irrelevant ones
- `education`, `other_educations`, `languages`, `hobbies`, `work_rights`

**Output:** a JSON object matching the Resume schema below. Do NOT wrap in markdown code fences. Output raw JSON only.

### Step 4: Generate cover letter

You are an Australian career consultant writing a cover letter.

Use the same candidate context from Step 2.

Given the job description and base resume data, write a tailored Australian-style cover letter.

**Cover letter structure:**
1. Greeting (e.g., "Dear Hiring Manager," or use the name if available in the job ad)
2. Opening paragraph: state the role, where you found it, and one specific reason you are a strong match (a concrete achievement or domain overlap, not a generic statement).
3. Body (1-2 paragraphs): connect your most relevant experience to their key requirements. Use specific metrics and examples from the resume. Do not repeat bullet points verbatim; provide context, motivation, and how your experience applies to their problems.
4. If the role is in a sector different from your previous experience, include 1-2 sentences explaining why this sector interests you and how your skills transfer. Keep it genuine and brief.
5. Closing paragraph: express interest in discussing further. Mention availability. Keep it confident and brief.

**What NOT to include:**
- No sender or recipient addresses
- No date or subject line
- No signature block (no "Yours sincerely, Name") — it will be added automatically by PDF generator
- No "I am passionate about..." or "I would be thrilled to..."
- No "I am excited about the opportunity to..."
- No promotional language ("groundbreaking", "vibrant", "innovative leader")

**Writing style:**
- Professional, direct, human-sounding. Write like a competent professional talking to another professional, not like a template.
- Vary sentence length. Short punchy sentences mixed with longer ones. Don't make every paragraph the same length.
- Use standard hyphen "-" only. No em-dash or en-dash.

**Anti-AI writing rules (CRITICAL - follow every one):**
- BANNED words/phrases: pivotal, crucial, landscape, fostering, showcasing, commitment to, serves as, stands as, testament to, underscores, highlights, enduring, vibrant, rich (figurative), profound, nestled, groundbreaking, renowned, delve, tapestry, interplay, intricate, garner, encompassing, cultivating, leveraging, spearheading.
- No "-ing" phrase endings ("...contributing to the team's success", "...ensuring quality delivery"). End with the result.
- Use "is/are/has/did" instead of "serves as/stands as/functions as".
- No rule-of-three patterns. Don't force ideas into groups of three.
- No negative parallelisms ("Not only X but also Y", "It's not just about X, it's about Y").
- No significance inflation: don't call things "significant" or "critical" - be specific instead.
- No filler: "In order to" -> "To", "Due to the fact that" -> "Because", "It is important to note" -> cut it.
- No generic positive conclusions ("I look forward to bringing my expertise...", "excited about the opportunity").
- No sycophantic tone ("I would be thrilled", "I am passionate about").
- Have a voice. Real people have opinions and specific reactions. "I genuinely enjoy complex business rules and data accuracy requirements" beats "I am passionate about delivering excellence".
- Use straight quotes, not curly quotes.
- Do not uniformly hyphenate common compounds (cross-functional, data-driven, end-to-end). Humans are inconsistent with these.

**Output:** plain text of the cover letter (greeting + body only, no signature). Do NOT wrap in markdown code fences.

### Step 5: Save output files

1. Determine the output folder name:
   - Take `company_name` from the adapted resume
   - Lowercase, replace spaces/slashes/hyphens with underscores
   - Full path: `{config.paths.output_dir}/{folder_name}/`
   - If the directory already exists, append `_2`, `_3`, etc.

2. Create the output directory using Bash `mkdir -p`.

3. Write the adapted resume JSON to `{output_dir}/adapted_resume.json` using the Write tool.

4. Write the cover letter text to `{output_dir}/cover_letter.txt` using the Write tool.

5. Copy `vacancy.txt` to the output directory using Bash `cp`.

### Step 6: Generate PDFs

Run the PDF generator script:

```bash
python scripts/generate_pdf.py \
  --resume-json "{output_dir}/adapted_resume.json" \
  --cover-letter-text "{output_dir}/cover_letter.txt" \
  --output-dir "{output_dir}" \
  --config-yaml config.yaml
```

Verify that `resume.pdf` and `cover_letter.pdf` were created successfully.

### Step 7: Report

Tell the user:
- Output directory path
- Company name and position title
- Confirm that resume.pdf and cover_letter.pdf were generated

## Resume JSON Schema

The adapted resume JSON must have exactly this structure:

```json
{
  "company_name": "string",
  "name": "string",
  "title": "string",
  "phone": "string",
  "email": "string",
  "linkedin": "string (optional, default empty)",
  "github": "string (optional, default empty)",
  "address": "string",
  "professional_summary": "string",
  "key_skills": {
    "Category Name": ["skill1", "skill2", "..."]
  },
  "work_experience": [
    {
      "position": "string",
      "company": "string",
      "location": "string",
      "dates": "string",
      "achievements": ["string", "string", "..."]
    }
  ],
  "personal_projects": [
    {
      "name": "string",
      "url": "string (optional, default empty)",
      "description": "string"
    }
  ],
  "education": [
    {
      "institution": "string",
      "location": "string",
      "dates": "string",
      "qualification": "string"
    }
  ],
  "other_educations": [],
  "languages": [],
  "hobbies": [],
  "work_rights": "string"
}
```

## Error Handling

- If `vacancy.txt` is missing or empty, ask the user to provide a job description.
- If the resume type is not found in config.yaml templates, list available types and ask the user to choose.
- If the PDF script fails, show the error output and suggest checking Python dependencies (`pip install reportlab pydantic pyyaml`).

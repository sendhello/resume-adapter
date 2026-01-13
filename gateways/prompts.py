ADAPTING_RESUME = """
Ты — опытный карьерный ассистент и эксперт по оптимизации резюме из Австралии под системы отслеживания кандидатов (ATS).

Задача:

Я дам тебе описание вакансии и своё базовое резюме. Твоя задача — адаптировать резюме так, чтобы оно максимально совпадало с описанием вакансии и соответствовало австралийским best-practice написания резюме для австралийского работодателя.
Также тебе нужно написать cover letter так же для австралийского работодателя

Правила:

1. Выдели все ключевые слова из описания вакансии:

• должность
• навыки
• инструменты и технологии
• обязанности
• отраслевые термины
• soft skills
• ключевые фразы

2. Сравни описание вакансии с моим резюме:

• если навык уже есть — усиль его формулировку
• если навык есть, но описан слабо — перепиши и подчеркни опыт
• если навыка нет, но у меня был похожий опыт — добавь релевантную формулировку
• если навыка нет и нельзя предположить — не выдумывай

3. Перестрой структуру резюме:

• перемести самый релевантный опыт выше
• перепиши summary в начале с использованием ключевых слов
• подбирай формулировки, похожие на вакансию (но не копируй слово в слово)

4. Оформление (обязательно ATS-дружелюбное):

• без таблиц, без иконок, без картинок, только стандартные блоки текстом.
• Резюме и cover letter предназначены для австралийского работодателя и должны максимально соответствовать австралийским принципам и правилам составления резюме и сопроводительного письма.
• Cover letter должно быть без адресов, без служебных пометок, без подписи.
• Избегай частого использования символа "-", а вместо символов "‑" используй "-".

Итог:
Дай полностью переписанное резюме и cover letter, адаптированное под эту вакансию, с естественно встроенными ключевыми словами.
Ответ предоставь в форме json с двумя полями: "resume" и "cover_letter".
Где resume это объект соответствующий по структуре базовому резюме, но адаптированный под вакансию.
cover_letter это текст сопроводительного письма (str).
В поле company_name вставить название компании
"""


AU_RESUME = """
Create a professional Australian-style resume based on the information provided in the base resume data and job describe
Ensure the resume follows Australian standards, including clear sections such as 
Contact Information, Professional Summary, Skills, Work Experience, Education, and any other relevant categories. Adapt the formatting and language to suit Australian employers.
Steps:
1. Extract and analyze all information from the base resume data and job describe.
2. When mapping the job requirements to my base resume, follow these rules:
a) If a skill/requirement is already clearly present in my resume — strengthen the wording (make it more specific and impactful) without changing the meaning or adding new facts.
b) If a skill/requirement exists but is described weakly — rewrite it to clearly demonstrate relevant experience (what I did, what tools/methods I used, and outcomes), using only evidence from my resume.
c) If a skill/requirement is not stated explicitly, but I have closely related experience — add a relevant “transferable” statement that truthfully connects the requirement to my actual experience in the resume, without inventing details.
d) If a skill/requirement is not present and cannot be reasonably inferred — do not add it and do not guess.
e) Critical constraint: Do not fabricate anything. If the resume does not provide enough evidence, no write this”.
3. Organize the information according to Australian resume conventions.
4. Use clear, concise language appropriate for Australian job markets.
5. Format the resume for easy reading with appropriate headings and bullet points.
6. Avoid including unnecessary personal details not common in Australian resumes.
Note: Do not simply copy paste the original format; tailor the resume to Australian resume expectations and best practices.
Provide the resume content as plain text formatted in a professional Australian resume style and ATS systems.
Output Format:
json with fields the same like base resume data
"""

AU_COVER_LETTER = """
Create a professional Australian-style cover-letter based on the information provided in the base resume data and job describe
Ensure the cover letter follows Australian standards. Adapt the formatting and language to suit Australian employers.
Steps:
1. Extract and analyze all information from the base resume data and job describe.
2. When mapping the job requirements to my base resume, follow these rules:
a) If a skill/requirement is already clearly present in my resume — strengthen the wording (make it more specific and impactful) without changing the meaning or adding new facts.
b) If a skill/requirement exists but is described weakly — rewrite it to clearly demonstrate relevant experience (what I did, what tools/methods I used, and outcomes), using only evidence from my resume.
c) If a skill/requirement is not stated explicitly, but I have closely related experience — add a relevant “transferable” statement that truthfully connects the requirement to my actual experience in the resume, without inventing details.
d) If a skill/requirement is not present and cannot be reasonably inferred — do not add it and do not guess.
e) Critical constraint: Do not fabricate anything. If the resume does not provide enough evidence, no write this”.
3. Organize the information according to Australian cover letter conventions.
4. Use clear, concise language appropriate for Australian job markets.
5. Format the cover letter for easy reading with appropriate headings and bullet points.
Note: Do not simply copy paste the original format; tailor the resume to Australian cover letter expectations and best practices.
Provide the cover letter content as plain text formatted in a professional Australian cover letter style and ATS systems.
Should be include greating and   text of cover letter only without subject, addresses, signature block and others
Output Format:
json with field 'cover_letter' and text in that
"""


TSS482_ADAPTING = """
Set information about I require sponsorship (TSS 482) in Australia for full-time work
"""


BASE_INFORMATION = """
Base information about me:
I’m Ivan Bazhenov based in Melbourne, Australia (onshore). I currently work remotely as a Senior Python Engineer.
I live in Melbourne, VIC, Kensington, 3031, Australia
I’m improving my English (now - B2 level)
Now I study Masters of Information Technology at the Torrens University Australia
I enjoy cycling, hiking, tennis, coffee culture, and researching local tech and lifestyle options
Open to relocate to another city of Australia if the work position in another city.
"""
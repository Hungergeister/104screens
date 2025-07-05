import os
import markdown2
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

AUTH_STATE_PATH = "auth_state.json"

def get_html_with_auth(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=100)
        context = (
            p.chromium.launch_persistent_context(
                user_data_dir="user_data",
                headless=False,
            )
            if not os.path.exists(AUTH_STATE_PATH)  
            else browser.new_context(storage_state=AUTH_STATE_PATH)
        )

        page = context.new_page()
        print("🌐 Загружаю страницу…")
        page.goto(url, timeout=60000)

        try:
            if "vacancy" in url:
                page.wait_for_selector("h1", timeout=20000)
            elif "resume" in url:
                page.wait_for_selector('h2[data-qa="bloko-header-1"]', timeout=20000)
        except Exception:
            print("⚠️ Не удалось дождаться загрузки содержимого.")

        html = page.content()
        if not os.path.exists(AUTH_STATE_PATH):
            context.storage_state(path=AUTH_STATE_PATH)

        context.close()
        browser.close()
        return html

def extract_vacancy_data(html):
    soup = BeautifulSoup(html, 'html.parser')
    def safe_text(selector, attrs=None):
        el = soup.find(selector, attrs or {})
        return el.text.strip() if el else "Не найдено"
    title = safe_text('h1')
    salary = safe_text('span', {'data-qa': 'vacancy-salary'})
    company = safe_text('a', {'data-qa': 'vacancy-company-name'})
    description = soup.find('div', {'data-qa': 'vacancy-description'})
    description_text = description.get_text(separator="\n").strip() if description else "Описание не найдено"
    markdown = f"# {title}\n\n**Компания:** {company}\n\n**Зарплата:** {salary}\n\n## Описание\n\n{description_text}"
    return markdown.strip()

def extract_resume_data(html):
    soup = BeautifulSoup(html, 'html.parser')
    def safe_text(selector, **kwargs):
        el = soup.find(selector, kwargs)
        return el.text.strip() if el else "Не найдено"
    name = safe_text('h2', data_qa='bloko-header-1')
    gender_age = safe_text('p')
    location = safe_text('span', data_qa='resume-personal-address')
    job_title = safe_text('span', data_qa='resume-block-title-position')
    job_status = safe_text('span', data_qa='job-search-status')
    experiences = []
    experience_section = soup.find('div', {'data-qa': 'resume-block-experience'})
    if experience_section:
        experience_items = experience_section.find_all('div', class_='resume-block-item-gap')
        for item in experience_items:
            try:
                period = item.find('div', class_='bloko-column_s-2').text.strip()
                duration = item.find('div', class_='bloko-text').text.strip()
                period = period.replace(duration, f" ({duration})")
                company = item.find('div', class_='bloko-text_strong').text.strip()
                position = item.find('div', {'data-qa': 'resume-block-experience-position'}).text.strip()
                description = item.find('div', {'data-qa': 'resume-block-experience-description'}).text.strip()
                experiences.append(f"**{period}**\n\n*{company}*\n\n**{position}**\n\n{description}\n")
            except Exception:
                continue
    skills = []
    skills_section = soup.find('div', {'data-qa': 'skills-table'})
    if skills_section:
        skills = [tag.text.strip() for tag in skills_section.find_all('span', {'data-qa': 'bloko-tag__text'})]
    markdown = f"# {name}\n\n**{gender_age}**\n\n**Местоположение:** {location}\n\n**Должность:** {job_title}\n\n**Статус:** {job_status}\n\n## Опыт работы\n\n"
    markdown += "\n".join(experiences) if experiences else "Опыт работы не найден.\n"
    markdown += "\n## Ключевые навыки\n\n"
    markdown += ", ".join(skills) if skills else "Навыки не указаны.\n"
    return markdown.strip()

def save_html_from_markdown(markdown_text, filename):
    html = markdown2.markdown(markdown_text)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)

if __name__ == "__main__":
    url = input("🔗 Вставьте ссылку на вакансию или резюме hh.ru: ").strip()
    html = get_html_with_auth(url)

    os.makedirs("output_html", exist_ok=True)

    if "resume" in url:
        md = extract_resume_data(html)
        save_html_from_markdown(md, "output_html/resume_1.html")
        print("✅ Сохранено в файл: output_html/resume_1.html")
    elif "vacancy" in url:
        md = extract_vacancy_data(html)
        save_html_from_markdown(md, "output_html/vacancy_1.html")
        print("✅ Сохранено в файл: output_html/vacancy_1.html")
    else:
        print("❌ Не удалось определить тип ссылки (не содержит 'resume' или 'vacancy').")

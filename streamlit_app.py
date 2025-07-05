import streamlit as st
import openai
import os
client = openai.OpenAI(api_key=os.getenv["OPENAI_API_KEY"]) 
SYSTEM_PROMPT = """
Проскорь кандидата, насколько он подходит для данной вакансии.

Сначала напиши короткий анализ, который будет пояснять оценку.
Отдельно оцени качество заполнения резюме (понятно ли, с какими задачами сталкивался кандидат и каким образом их решал?). Эта оценка должна учитываться при выставлении финальной оценки - нам важно нанимать таких кандидатов, которые могут рассказать про свою работу
Потом представь результат в виде оценки от 1 до 10.
""".strip()

def request_gpt(system_prompt, user_prompt):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},  
            {"role": "user", "content": user_prompt},     
        ],
        max_tokens=1000,
        temperature=0,
    )
    return response.choices[0].message.content


st.title('CV Scoring App')
job_description = st.text_area('Введите описание вакансии')
cv = st.text_area('Введите описание резюме')
if st.button("Оценить резюме"):
    with st.spinner("Оцениваем резюме..."):
        # Формирование пользовательского промпта
        user_prompt = f"# ВАКАНСИЯ\n{job_description}\n\n# РЕЗЮМЕ\n{cv}"
        # Отправляем запрос с системным и пользовательским промптами
        response = request_gpt(SYSTEM_PROMPT, user_prompt)
    st.write(response)


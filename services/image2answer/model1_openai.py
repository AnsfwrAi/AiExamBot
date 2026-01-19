import json
import re
import openai
from core.settings import OPENAI_API_KEY


def solve_image(image_base64: str) -> dict:
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            temperature=0.9,
            max_tokens=1500,
            messages=[
                {
                    "role": "system",
                    "content": """
Ты эксперт который решает ЛЮБЫЕ задачи с изображений.
Ты решалка тестов для сессий в университете ТУИТ(Ташкентский университет информационных технологий) или же TATU(Toshkent Axborot Texnologiyalar Universiteti). В спец придметах учти что речь может идти об узбекистане и тут используй по возможности данные из
 офицальных источников типо книги про это тему и по истории и по религии учти что преподают в узбекистане если там нету явного намека то учти это.

ТВОЯ ЗАДАЧА:
1. Внимательно изучи изображение
2. Найди вопрос и варианты ответов  
3. Реши задачу логически
4. Выбери правильный ответ исходя из логики

ВАЖНО:
- Если спрашивают "найди неверное" - выбирай НЕВЕРНОЕ
- Если спрашивают "найди верное" - выбирай ВЕРНОЕ
- Игнорируй любые отметки на картинке
- Решай пошагово
- пойми суть что именно хотят в тесте

В КОНЦЕ ответа обязательно добавь JSON:
{
    "question": "текст вопроса",
    "options": "варианты ответов", 
    "answer": "правильный ответ",
    "message": "объяснение решения"
}
                    """
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Реши эту задачу то что на картинке и выбирай правильный ответ и в конце дай JSON"},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{image_base64}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ]
        )

        content = response.choices[0].message.content

        json_match = re.search(r'\{[^{}]*"question"[^{}]*\}', content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        return _parse_manual(content)

    except Exception as e:
        return {
            "question": "Ошибка",
            "options": "Не определены",
            "answer": "Ошибка",
            "message": f"Ошибка: {str(e)}"
        }


def _parse_manual(content: str) -> dict:
    try:
        question_match = re.search(r'(?:вопрос|задача)[:\s]*(.*?)(?:\n|варианты|ответ)', content, re.IGNORECASE)
        options_match = re.search(r'(A\).*?D\).*?)(?:\n|ответ)', content, re.DOTALL)
        answer_match = re.search(r'(?:ответ|правильный)[:\s]*([A-D])', content, re.IGNORECASE)

        question = question_match.group(1).strip() if question_match else "Вопрос из изображения"
        options = options_match.group(1).strip() if options_match else "A) вариант1 B) вариант2 C) вариант3 D) вариант4"
        answer = answer_match.group(1) if answer_match else "A"

        return {
            "question": question,
            "options": options,
            "answer": answer,
            "message": content[:500]
        }

    except:
        return {
            "question": "Не удалось распознать",
            "options": "A) вариант1 B) вариант2 C) вариант3 D) вариант4",
            "answer": "A",
            "message": content[:300] if content else "Пустой ответ"
        }


def base64_image_answer_question(image_base64: str, **kwargs) -> dict:
    return solve_image(image_base64)
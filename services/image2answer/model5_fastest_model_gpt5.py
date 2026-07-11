import time
import hashlib
from openai import OpenAI
from core import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)

MODEL = "gpt-5.4-mini"

INSTRUCTIONS = (
    "Перед тобой экзаменационный или тестовый вопрос "
    "из школы, вуза или учебного сайта, со скриншота страницы. "
    "Внимательно изучи все элементы изображения: текст вопроса, числа, "
    "подписи на геометрических фигурах (углы, стороны, точки), формулы. "
    "Если вопрос предполагает выбор из готовых вариантов ответа, выведи "
    "выбранный вариант ДОСЛОВНО так, как он написан на изображении "
    "(текст, число, символ). Используй букву или номер варианта ТОЛЬКО "
    "если эта буква/номер реально напечатаны на изображении рядом с "
    "вариантом — никогда не придумывай собственную маркировку A/B/C/D, "
    "если её нет на картинке. "
    "Если вопрос открытый (нужно вычислить число, значение, слово) — "
    "выведи только сам ответ. "
    "Для геометрии и математики: перепроверь вычисления (используй "
    "code_interpreter при необходимости) прежде чем дать финальный ответ. "
    "Используй стандартные определения, формулы и термины, принятые в "
    "официальных учебниках. "
    "Ответь ТОЛЬКО финальным ответом, без пояснений и без слова 'Ответ:'."
)



def _cache_key(image_base64: str) -> str:
    return hashlib.sha256(image_base64.encode()).hexdigest()

def solve_task(image_base64: str) -> dict:
    start = time.time()

    response = client.responses.create(
        model=MODEL,
        instructions=INSTRUCTIONS,
        reasoning={"effort": "high"},
        service_tier="priority",
        tools=[
            {
                "type": "code_interpreter",
                "container": {"type": "auto"},
            }
        ],
        tool_choice="auto",
        max_tool_calls=2,
        prompt_cache_key=_cache_key(image_base64),
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_image",
                        "image_url": f"data:image/jpeg;base64,{image_base64}",
                        "detail": "high",
                    }
                ],
            }
        ],
    )
    re = response.output_text.strip()
    print(f"Answer: {re} | time: {time.time() - start:.2f}s")
    return {
        "question": re,
        "options": re,
        "answer": re,
        "message": re,
    }

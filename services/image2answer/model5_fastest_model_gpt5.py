import time
import hashlib
from openai import OpenAI
from core import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)

MODEL = "gpt-5.4-mini"

INSTRUCTIONS = (
    "Перед тобой экзаменационный или тестовый вопрос "
    "из школы, вуза или учебного сайта. "
    "Всегда выбирай ОДИН правильный вариант ответа "
    "так, как это принято в официальных учебниках и тестах "
    "по соответствующему предмету. "
    "Используй стандартные определения, формулы, даты и термины. "
    "Не рассуждай творчески и не предлагай альтернативные трактовки. "
    "Если варианты близки по смыслу, "
    "выбирай тот, который чаще всего считается правильным в тестах. "
    "Ответь ТОЛЬКО буквой варианта (A, B, C, D и т.п.) или ответ, без пояснений."
)



def _cache_key(image_base64: str) -> str:
    return hashlib.sha256(image_base64.encode()).hexdigest()

def solve_task(image_base64: str) -> dict:
    start = time.time()

    response = client.responses.create(
        model=MODEL,
        instructions=INSTRUCTIONS,
        reasoning={"effort": "low"},
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

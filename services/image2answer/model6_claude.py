import time
import hashlib
import anthropic
from core import settings

# Make sure to set ANTHROPIC_API_KEY in your .env
client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

MODEL = "claude-3-5-sonnet-latest"

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

def solve_task(image_base64: str) -> dict:
    start = time.time()

    # Create the message with Claude
    response = client.messages.create(
        model=MODEL,
        max_tokens=1000,
        system=INSTRUCTIONS,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": image_base64,
                        },
                    },
                    {
                        "type": "text",
                        "text": "Реши это задание. Выведи только ответ."
                    }
                ],
            }
        ],
    )
    
    # Claude returns a list of content blocks
    re = response.content[0].text.strip()
    
    print(f"Answer: {re} | time: {time.time() - start:.2f}s")
    return {
        "question": re,
        "options": re,
        "answer": re,
        "message": re,
    }

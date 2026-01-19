from __future__ import annotations

import base64
import inspect
import io
from typing import Dict
from core.settings import OPENAI_API_KEY

import openai

_client = openai.OpenAI(api_key=OPENAI_API_KEY)
_TAGS = ("question", "options", "answer", "")


def _ai_call(**payload) -> str:
    if "response_format" in inspect.signature(_client.responses.create).parameters:
        payload.setdefault("response_format", {"type": "text"})
    return _client.responses.create(**payload).output_text.strip()


def base64_image_answer_question(image_base64: str, *, model: str = "gpt-4o") -> Dict[str, str]:
    extract_payload = {
        "model": model,
        "instructions": (
            "Составь промпт для этой задачки"
        ),
        "input": [
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": "Извлеки задачу ровно по шаблону."},
                    {"type": "input_image", "image_url": {"url": f"data:image/png;base64,{image_base64}"}},
                ],
            }
        ],
        "tool_choice": "none",
        "temperature": 0,
    }
    try:
        statement = _ai_call(**extract_payload)
    except Exception:
        img_bytes = base64.b64decode(image_base64)
        file_obj = io.BytesIO(img_bytes)
        file_obj.name = "task.png"
        file_id = _client.files.create(file=file_obj, purpose="assistants").id
        extract_payload["input"][0]["content"][1] = {
            "type": "input_image",
            "file_id": file_id,
            "detail": "high",
        }
        statement = _ai_call(**extract_payload)

    solve_prompt = (
        "Ниже текст задачи,"
        "Реши задачу и верни ответ, главное проверь спомошью кода га python, и вывод питон скрипта, для матрицы используй numpy/pandas/scipy/"
        "обьязательно в блоке\n\n"

        "верни все эти данные\n\n"
        
        "&&&question  текст задачи в чистом виде &&&question\n"
        "&&&options  варианты ответов в чистом виде &&&options\n"
        "&&&answer  верный ответ, в чистом виде, если нет то примерный ответ а если вообще не вопрос то просто нет ответа &&&answer\n"
        "&&&message  ответ в чистом виде первые 500 символов &&&message\n"
    )

    solve_payload = {
        "model": model,
        "instructions": solve_prompt,
        "input": [{"role": "user", "content": [{"type": "input_text", "text": statement}]}],
        "tools": [{"type": "code_interpreter", "container": {"type": "auto"}}],
        "tool_choice": "required",
        "temperature": 0,
    }
    solved_raw = _ai_call(**solve_payload)

    result: Dict[str, str] = {}
    for tag in _TAGS:
        try:
            seg = solved_raw.split(f"&&&{tag}", 1)[1].split(f"&&&{tag}", 1)[0]
        except IndexError:
            seg = ""
        result[tag] = seg.strip()

    return result

import json
import os

import ollama

MODEL = os.environ.get("KG_MODEL", "gemma4:31b-cloud")


def chat(prompt: str, system: str = "", as_json: bool = False) -> str:
    messages = [{"role": "system", "content": system}] if system else []
    messages.append({"role": "user", "content": prompt})
    resp = ollama.chat(model=MODEL, messages=messages, format="json" if as_json else None)
    return resp["message"]["content"]


def chat_json(prompt: str, system: str = "", retries: int = 2) -> dict:
    # Cloud models may ignore format="json" and wrap output in ```json fences.
    for attempt in range(retries + 1):
        text = chat(prompt, system, as_json=True)
        start, end = text.find("{"), text.rfind("}")
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            if attempt == retries:
                raise ValueError(f"LLM did not return JSON: {text[:200]!r}")
    return {}

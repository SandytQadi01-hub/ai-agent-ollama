# -*- coding: utf-8 -*-
# الجزء 2 — أبسط تواصل مع Ollama عبر Python (نقطة /api/generate)
# يرسل سؤالًا ثابتًا للنموذج ويطبع الجواب.
import requests

MODEL = "llama3.2:3b"


# يرسل prompt واحدًا للنموذج ويعيد نص الجواب.
def ask(prompt):
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={"model": MODEL, "prompt": prompt, "stream": False},
        timeout=120,
    )
    return response.json()["response"]


if __name__ == "__main__":
    print("سؤال 1: ما هي عاصمة الأردن؟")
    print("الجواب:", ask("ما هي عاصمة الأردن؟").strip())

    # سؤال من عندي
    print("\nسؤال 2: اذكر ثلاث فواكه فقط.")
    print("الجواب:", ask("اذكر ثلاث فواكه فقط، بدون شرح.").strip())

# -*- coding: utf-8 -*-
# الجزء 4 — حلقة تفكير يدوية مبسّطة (Chain-of-Thought) + استخراج الجواب النهائي.
import requests

MODEL = "llama3.2:3b"


# يرسل prompt للنموذج ويعيد النص الكامل للرد (temperature=0 لثبات النتيجة).
def ask(prompt):
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={"model": MODEL, "prompt": prompt, "stream": False,
              "options": {"temperature": 0}},
        timeout=180,
    )
    return response.json()["response"]


# يستخرج الرقم الذي يأتي بعد عبارة "الجواب النهائي:" من نص الرد (بدون مكتبات خارجية).
def extract_final_answer(response_text):
    marker = "الجواب النهائي:"
    index = response_text.find(marker)
    if index == -1:
        return None
    after = response_text[index + len(marker):]
    number = ""
    for char in after:
        if char.isdigit() or (char == "-" and number == ""):
            number += char
        elif char in " :[].\t":
            if number:      # توقف عند أول فاصل بعد بدء الرقم
                if char == ".":
                    continue
                break
            continue
        else:
            if number:
                break
    return number if number else None


QUESTION = "عندي 3 صناديق، كل صندوق فيه 12 تفاحة، وأكلت 5 تفاحات، كم تفاحة باقية؟"

if __name__ == "__main__":
    # 1) مع طلب التفكير خطوة بخطوة
    prompt_with_steps = (
        "حل المسألة بالتفكير خطوة بخطوة. اكتب كل خطوة برقم، "
        'وبالسطر الأخير اكتب بالضبط "الجواب النهائي: <الرقم>".\n\n'
        "مثال:\n"
        "السؤال: عندي صندوقان في كل واحد 10 كرات وأخذت 3، كم بقي؟\n"
        "1. مجموع الكرات = 2 × 10 = 20\n"
        "2. بعد أخذ 3 = 20 - 3 = 17\n"
        "الجواب النهائي: 17\n\n"
        f"السؤال: {QUESTION}"
    )
    print("===== مع التفكير خطوة بخطوة =====")
    with_steps = ask(prompt_with_steps)
    print(with_steps)
    print("\n>> الجواب المستخرج:", extract_final_answer(with_steps))

    # 2) بدون طلب التفكير (رد مباشر) للمقارنة
    print("\n===== بدون تفكير (رد مباشر) =====")
    direct = ask(QUESTION + " أعطني رقمًا فقط.")
    print(direct)

    print("\n(الجواب الصحيح يدويًا: 3*12 - 5 = 31)")

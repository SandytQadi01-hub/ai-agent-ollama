# -*- coding: utf-8 -*-
# الجزء 5 — أول AI Agent فعلي بأداة واحدة (Calculator) بنمط ReAct مبسّط.
# النموذج يقرر متى يحتاج حسابًا فيكتب "CALCULATE: <expr>"، وكود Python هو الذي
# ينفّذ الحساب فعليًا (دقة 100%) ثم يعيد النتيجة للنموذج ليكمل.
import ast
import operator
import requests

MODEL = "llama3.2:3b"
URL = "http://localhost:11434/api/chat"

SYSTEM_PROMPT = (
    "أنت مساعد يحل مسائل حسابية، لكنك ضعيف بالحساب الذهني فلا تحسب بنفسك أبدًا.\n"
    "في كل ردّ اكتب سطرًا واحدًا فقط، لا أكثر، ويكون إمّا:\n"
    "  CALCULATE: <تعبير حسابي>      (لطلب تنفيذ عملية، ثم توقّف وانتظر النتيجة)\n"
    "أو:\n"
    "  الجواب النهائي: <النص>        (فقط بعد أن تستلم كل النتائج التي تحتاجها)\n"
    "لا تكتب أي شرح أو أسطر أخرى. كوّن تعبيرًا كاملًا للمسألة قدر الإمكان.\n"
    "يمكنك استخدام // للقسمة الصحيحة و % لباقي القسمة. لا تعِد عملية استلمت نتيجتها."
)

_OPS = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod, ast.Pow: operator.pow, ast.USub: operator.neg,
}


# يقيّم تعبيرًا حسابيًا نصيًا بأمان (أرقام وعمليات فقط، بدون eval العادي).
def safe_calculate(expr):
    def ev(node):
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.BinOp):
            return _OPS[type(node.op)](ev(node.left), ev(node.right))
        if isinstance(node, ast.UnaryOp):
            return _OPS[type(node.op)](ev(node.operand))
        raise ValueError("تعبير غير مسموح")
    return ev(ast.parse(expr, mode="eval").body)


# يرسل الرسائل للنموذج ويعيد ردًّا من سطر واحد فقط (stop عند نهاية السطر).
def chat(messages):
    r = requests.post(URL, json={"model": MODEL, "messages": messages, "stream": False,
                                 "options": {"temperature": 0, "stop": ["\n"]}}, timeout=180)
    return r.json()["message"]["content"]


# يبحث عن "CALCULATE" (بنقطتين أو بدونها) ويستخرج تعبيرًا حسابيًا نظيفًا.
def find_calculation(text):
    marker = "CALCULATE"
    idx = text.find(marker)
    if idx == -1:
        return None
    rest = text[idx + len(marker):]
    rest = rest.lstrip(": ")                      # تجاوز النقطتين والمسافات إن وُجدت
    line = rest.splitlines()[0] if rest else ""
    allowed = "0123456789+-*/(). %"
    expr = "".join(ch for ch in line if ch in allowed).strip()
    return expr if expr else None


# يشغّل حلقة ReAct: تفكير -> أداة -> ملاحظة -> ... حتى الجواب النهائي.
def run_agent(question, max_steps=8, verbose=True):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]
    processed = set()
    reply = ""
    for _ in range(max_steps):
        reply = chat(messages)
        if verbose:
            print(f"  [النموذج] {reply.strip()}")
        messages.append({"role": "assistant", "content": reply})
        expr = find_calculation(reply)
        has_final = "الجواب النهائي" in reply

        if expr and expr not in processed:
            try:
                result = safe_calculate(expr)
            except Exception as e:
                result = f"خطأ: {e}"
            processed.add(expr)
            if verbose:
                print(f"  [الأداة 🛠️] CALCULATE {expr} = {result}")
            messages.append({"role": "user",
                             "content": f"OBSERVATION: {result}. استخدم هذه النتيجة ولا تعد حساب العملية نفسها."})
            continue
        if has_final:
            return reply
        if expr and expr in processed:
            # النموذج يكرر عملية نُفّذت مسبقًا -> ندفعه لكتابة الجواب النهائي
            messages.append({"role": "user",
                             "content": "لديك كل النتائج. اكتب الآن سطرًا واحدًا فقط: الجواب النهائي: <النتيجة>."})
            continue
        return reply  # رد مباشر بلا أداة وبلا صيغة نهائية
    return reply


QUESTIONS = [
    "لو عندي 1500 دينار ووزعتهم على 7 أشخاص بالتساوي، كم نصيب كل واحد (رقم صحيح)، وكم الباقي؟",
    "عندي 3 صناديق كل صندوق فيه 12 تفاحة، وأضفت 8 تفاحات، كم المجموع؟",
    "ما ناتج 245 مضروبة في 37؟",
]

if __name__ == "__main__":
    for i, q in enumerate(QUESTIONS, 1):
        print(f"\n===== سؤال {i}: {q} =====")
        answer = run_agent(q)
        print(">> الجواب النهائي من الـ Agent:", answer.strip())

    # مقارنة الدقة: نفس العملية بدون أداة (النموذج يحسب بنفسه) مقابل الأداة
    print("\n===== مقارنة الدقة: 245 * 37 =====")
    r = requests.post("http://localhost:11434/api/generate",
                      json={"model": MODEL, "prompt": "احسب 245 * 37 وأعطني الرقم فقط.",
                            "stream": False, "options": {"temperature": 0}},
                      timeout=120)
    print("النموذج بدون أداة:", r.json()["response"].strip())
    print("الأداة (كود Python):", safe_calculate("245 * 37"), "<- الصحيح 100%")

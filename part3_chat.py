# -*- coding: utf-8 -*-
# الجزء 3 — محادثة بسيطة مع ذاكرة (Conversation History)، بدون Agent.
# نخزّن كل الرسائل في قائمة ونرسلها كاملة مع كل سؤال جديد ليتذكر النموذج السياق.
import requests

MODEL = "llama3.2:3b"
URL = "http://localhost:11434/api/chat"


# يرسل كامل تاريخ المحادثة للنموذج ويعيد رد المساعد.
def chat(messages):
    response = requests.post(
        URL,
        json={"model": MODEL, "messages": messages, "stream": False},
        timeout=120,
    )
    return response.json()["message"]["content"]


def main():
    history = []  # الذاكرة: كل الرسائل (user + assistant)
    print("محادثة مع النموذج (اكتب 'خروج' للإنهاء)\n")
    while True:
        try:
            user_message = input("أنت: ").strip()
        except EOFError:
            break
        if user_message in ("خروج", "exit", "quit", ""):
            print("انتهت المحادثة.")
            break
        history.append({"role": "user", "content": user_message})
        reply = chat(history)
        history.append({"role": "assistant", "content": reply})
        print("النموذج:", reply.strip(), "\n")


if __name__ == "__main__":
    main()

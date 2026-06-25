import os
import time
import google.generativeai as genai
from dotenv import load_dotenv
from google.api_core.exceptions import ResourceExhausted

load_dotenv()

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model=genai.GenerativeModel("gemini-2.5-flash")

def triage_thread(sender: str, subject: str, snippet: str) -> dict:
    prompt = f"""
    You are an intelligent email assistant helping triage an inbox.

    Given this email thread metadata, classify it:

    Sender: {sender}
    Subject: {subject}
    Preview: {snippet}

    Respond in this exact format:

    Priority: <urgent | needs-reply | fyi | ignore>

    Category: <one short tag like: meeting-request, follow-up,
    newsletter, billing, job-app, social, admin, ...>

    Reason: <one sentence explaining why>
    """

    for attempt in range(3):
        try:
            response = model.generate_content(prompt)
            return parse_triage_response(response.text)
        except ResourceExhausted as e:
            wait = 15 * (attempt + 1)
            print(f"  Quota hit, retrying in {wait}s...")
            time.sleep(wait)
    raise RuntimeError("Gemini API quota exhausted after 3 retries")

def parse_triage_response(text: str) -> dict:
    result = {"priority": "unknown", "category": "unknown", "reason": "unknown"}

    for line in text.strip().split('\n'):
        if line.startswith("Priority:"):
            result["priority"] = line.replace("Priority:", "").strip().lower()

        elif line.startswith("Category:"):
            result["category"] = line.replace("Category:", "").strip().lower()

        elif line.startswith("Reason:"):
            result["reason"] = line.replace("Reason:", "").strip().lower()

    return result

def triage_inbox(threads: list) -> list:
    triaged = []

    for i, thread in enumerate(threads):
        if i > 0:
            time.sleep(20)
        label = triage_thread(
            sender=thread['sender'],
            subject=thread['subject'],
            snippet=thread['snippet']
        )

        triaged.append({**thread, **label})

    priority_order = {
        "urgent": 0,
        "needs-reply": 1,
        "fyi": 2,
        "ignore": 3,
        "unknown": 4
    }

    triaged.sort(
        key=lambda x: priority_order.get(x['priority'], 4)
    )

    return triaged

if __name__ == "__main__":
    sample_threads = [
        {"sender": "boss@company.com","subject": "Need your input by EOD","snippet": "Can you review the attached proposal before 5pm?"},
        {"sender": "newsletter@medium.com","subject": "Top stories for you this week","snippet": "Here's what's trending in tech..."},
        {"sender": "recruiter@startup.io","subject": "Quick call this week?","snippet": "Hi, I came across your profile and wanted to connect..."}
    ]

    results = triage_inbox(sample_threads)

    for r in results:
        print(
            f"[{r['priority'].upper()}] "
            f"[{r['category']}] "
            f"{r['subject']} - {r['reason']}"
        )  
"""Smart Email Reply Suggester - core engine.
Builds a prompt from the incoming email + chosen tone, calls a GenAI
backend (Claude API) and returns 3 structured reply suggestions.
If no API key is set, an offline MockBackend is used so the app can be
tested without internet access."""
import os, re, json

TONES = ["Professional", "Friendly", "Concise"]

SYSTEM_PROMPT = (
    "You are an email assistant. Read the email and write exactly 3 "
    "different reply options. Each reply must address every question or "
    "request in the email, match the requested tone, and end with a "
    "sign-off. Return ONLY JSON: "
    '{"intent": "...", "replies": [{"style": "...", "body": "..."}]}'
)

def build_prompt(email_text: str, tone: str, sender_name: str = "") -> str:
    """Prompt-construction layer."""
    email_text = re.sub(r"\s+\n", "\n", email_text.strip())[:4000]
    return (f"Tone: {tone}\nRecipient name (reply sender): "
            f"{sender_name or 'the user'}\n\nEMAIL RECEIVED:\n{email_text}")

def detect_intent(text: str) -> str:
    t = text.lower()
    rules = [("meeting", ["meeting", "schedule", "call", "available", "catch up"]),
             ("deadline", ["deadline", "due", "submit", "by friday", "asap"]),
             ("complaint", ["complaint", "not working", "disappointed", "issue", "refund"]),
             ("thanks", ["thank you", "thanks", "appreciate"])]
    for label, words in rules:
        if any(w in t for w in words):
            return label
    return "general enquiry"

class MockBackend:
    """Offline backend used for testing the full pipeline."""
    OPEN = {"Professional": "Dear {n},", "Friendly": "Hi {n},", "Concise": "Hi {n},"}
    CLOSE = {"Professional": "Kind regards,", "Friendly": "Cheers,", "Concise": "Thanks,"}
    BODY = {
        "meeting": ["Thank you for reaching out. I am available tomorrow between 2 PM and 4 PM and would be glad to meet then. Please confirm a time that suits you.",
                    "Thanks for the invite! Tomorrow afternoon works for me - just tell me what time is best and I will be there.",
                    "Yes, I can meet tomorrow at 3 PM. Please confirm."],
        "deadline": ["I acknowledge the deadline and will submit the requested work before it. I will update you if anything changes.",
                     "Got it - I am on it and will send everything over before the deadline!",
                     "Understood. I will submit before the deadline."],
        "complaint": ["I am sorry for the inconvenience. I have noted the issue and will look into it immediately and update you shortly.",
                      "So sorry about this! I am checking it right now and will get back to you soon.",
                      "Apologies. We are fixing this and will update you today."],
        "thanks": ["Thank you for your kind message. It was a pleasure to help, and please reach out if you need anything further.",
                   "You are most welcome! Happy to help anytime.",
                   "You're welcome."],
        "general enquiry": ["Thank you for your email. I have reviewed your message and will respond with the details you need by the end of the day.",
                            "Thanks for getting in touch! I will look into this and get back to you soon.",
                            "Received. I will get back to you today."]}
    def generate(self, prompt: str, tone: str, intent: str, name: str):
        n = "there"   # greet the SENDER of the email (found in the sign-off)
        m = re.search(r"(?:Regards|Thanks|Thank you|Sincerely|Best|Cheers)[,.]?\s*\n\s*([A-Z][a-z]+)\s*$",
                      prompt.strip())
        if m: n = m.group(1)
        idx = TONES.index(tone)
        replies = []
        for i, style in enumerate(["Detailed", "Warm", "Short"]):
            body = self.BODY[intent][i]
            replies.append({"style": style, "body":
                f"{self.OPEN[tone].format(n=n)}\n\n{body}\n\n{self.CLOSE[tone]}\n{name or 'Your Name'}"})
        return {"intent": intent, "replies": replies}

class ClaudeBackend:
    """Real GenAI backend (needs `pip install anthropic` + ANTHROPIC_API_KEY)."""
    def __init__(self, model="claude-sonnet-4-6"):
        import anthropic
        self.client = anthropic.Anthropic()
        self.model = model
    def generate(self, prompt, tone, intent, name):
        msg = self.client.messages.create(
            model=self.model, max_tokens=1000, system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}])
        text = msg.content[0].text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)

def get_backend():
    if os.getenv("ANTHROPIC_API_KEY"):
        try:
            return ClaudeBackend()
        except Exception:
            pass
    return MockBackend()

def suggest_replies(email_text, tone="Professional", sender_name="", backend=None):
    if not email_text or not email_text.strip():
        raise ValueError("Email text is empty")
    if tone not in TONES:
        raise ValueError(f"Tone must be one of {TONES}")
    backend = backend or get_backend()
    prompt = build_prompt(email_text, tone, sender_name)
    result = backend.generate(prompt, tone, detect_intent(email_text), sender_name)
    result["tone"] = tone
    result["backend"] = type(backend).__name__
    return result

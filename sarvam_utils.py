import os, requests

# Store your key in Replit Secrets as SARVAM_API_KEY
SARVAM_KEY = os.environ.get("SARVAM_API_KEY", "sk_6wd6du2j_bpZ1g2KPOpoFP4q4Z5MyaGKp")
BASE = "https://api.sarvam.ai"

def stt_from_file(file_path: str) -> str:
    if not SARVAM_KEY:
        return "[No SARVAM_API_KEY set in Replit Secrets]"
    try:
        with open(file_path, "rb") as f:
            resp = requests.post(
                f"{BASE}/speech-to-text",
                headers={"api-subscription-key": SARVAM_KEY},
                files={"file": (file_path, f, "audio/wav")},
                data={"model": "saarika:v2.5", "language_code": "hi-IN"},
                timeout=30
            )
        resp.raise_for_status()
        return resp.json().get("transcript", "No transcript returned")
    except Exception as ex:
        return f"STT Error: {ex}"

def translate_to_hindi(text: str) -> str:
    if not SARVAM_KEY:
        return "[No SARVAM_API_KEY set in Replit Secrets]"
    try:
        resp = requests.post(
            f"{BASE}/translate",
            headers={"api-subscription-key": SARVAM_KEY, "Content-Type": "application/json"},
            json={"input": text[:1000], "source_language_code": "auto",
                  "target_language_code": "hi-IN", "model": "mayura:v1",
                  "mode": "formal", "speaker_gender": "Male"},
            timeout=20
        )
        resp.raise_for_status()
        return resp.json().get("translated_text", "No translation")
    except Exception as ex:
        return f"Translation Error: {ex}"

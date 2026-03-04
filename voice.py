import requests

SARVAM_API_KEY = "sk_rc853rl4_5uIuUN2BrdkpKFqZia1T10vV"

def stt_from_file(file_path: str) -> str:
    url = "https://api.sarvam.ai/speech-to-text"
    headers = {"api-subscription-key": SARVAM_API_KEY}
    try:
        with open(file_path, "rb") as f:
            files = {"file": (file_path, f, "audio/wav")}
            data = {"model": "saarika:v2", "language_code": "hi-IN"}
            r = requests.post(url, headers=headers, files=files, data=data, timeout=30)
            return r.json().get("transcript", "No transcription returned")
    except Exception as ex:
        return f"STT Error: {ex}"

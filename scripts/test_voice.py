import requests, json
base = "https://saturday.viewdns.net/api"
key = "OpQvcfUtB7ujMLnCNYK3TzbRI0mAgrlq"
headers = {"X-API-Key": key, "Content-Type": "application/json"}

# Test TTS
r = requests.post(base + "/speak", headers=headers, json={"text": "Hola, soy Saturday"}, timeout=30)
print(f"TTS status: {r.status_code}")
data = r.json()
if "audio" in data:
    print(f"TTS OK: base64 audio length = {len(data['audio'])}")
else:
    print(f"TTS FAIL: {data}")

# Test STT endpoint
r2 = requests.post(base + "/stt", headers=headers, timeout=10)
print(f"STT status (no audio): {r2.status_code}")
print(f"STT body: {r2.json()}")

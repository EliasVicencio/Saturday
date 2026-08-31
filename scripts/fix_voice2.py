import base64

fp = "/home/ubuntu/Saturday/backend/api/voice.py"
with open(fp) as f:
    content = f.read()

if "import base64" not in content.split("\n\n")[0]:
    content = content.replace("import tempfile\nimport os", "import tempfile\nimport os\nimport base64")

with open(fp, "w") as f:
    f.write(content)

print("Added base64 import")

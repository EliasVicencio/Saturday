# test_notion.py
import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("NOTION_API_KEY")
db_id = os.getenv("NOTION_DB_ID")

print(f"API Key: {api_key[:20]}...")
print(f"DB ID: {db_id}")

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

url = f"https://api.notion.com/v1/databases/{db_id}/query"

try:
    response = requests.post(url, headers=headers, json={"page_size": 1})
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ Notion conectado correctamente")
        data = response.json()
        print(f"Tareas encontradas: {len(data.get('results', []))}")
    else:
        print(f"❌ Error: {response.text}")
except Exception as e:
    print(f"❌ Error: {e}")
# test_notion.py
import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("NOTION_API_KEY")
db_id = os.getenv("NOTION_DB_ID")

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

url = f"https://api.notion.com/v1/databases/{db_id}/query"

response = requests.post(url, headers=headers, json={"page_size": 1})
print(f"Status: {response.status_code}")

if response.status_code == 200:
    print("✅ Notion conectado")
    print(response.json())
else:
    print(f"❌ Error: {response.text}")
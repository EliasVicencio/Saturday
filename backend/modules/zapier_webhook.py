# modules/zapier_webhook.py - Integracion generica con Zapier via webhooks
import os
import httpx
import json
import time
from typing import Dict, Any, Optional
from datetime import datetime


class ZapierWebhook:
    """Envia datos a Zapier via webhooks."""
    
    def __init__(self):
        self.webhooks = {}
        self._load_webhooks()
    
    def _load_webhooks(self):
        webhook_map = {
            "email": os.getenv("ZAPIER_WEBHOOK_EMAIL", ""),
            "calendar": os.getenv("ZAPIER_WEBHOOK_CALENDAR", ""),
            "sheets": os.getenv("ZAPIER_WEBHOOK_SHEETS", ""),
            "slack": os.getenv("ZAPIER_WEBHOOK_SLACK", ""),
            "notion": os.getenv("ZAPIER_WEBHOOK_NOTION", ""),
            "general": os.getenv("ZAPIER_WEBHOOK_GENERAL", ""),
        }
        
        for key, url in webhook_map.items():
            if url and url.startswith("http"):
                self.webhooks[key] = url
        
        if self.webhooks:
            print(f"  Zapier: {len(self.webhooks)} webhooks configurados")
        else:
            print("  Zapier: sin webhooks configurados (opcional)")
    
    def send(self, action: str, data: Dict[str, Any], timeout: int = 15) -> Dict[str, Any]:
        if action not in self.webhooks:
            return {
                "success": False,
                "error": f"No hay webhook configurado para '{action}'",
                "available": list(self.webhooks.keys()),
            }
        
        url = self.webhooks[action]
        
        payload = {
            "action": action,
            "timestamp": datetime.now().isoformat(),
            "source": "saturday",
            "data": data,
        }
        
        try:
            with httpx.Client(timeout=timeout) as client:
                response = client.post(
                    url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )
                
                if response.status_code == 200:
                    return {
                        "success": True,
                        "status_code": response.status_code,
                        "response": response.text[:500],
                    }
                else:
                    return {
                        "success": False,
                        "status_code": response.status_code,
                        "error": response.text[:200],
                    }
        
        except httpx.TimeoutException:
            return {
                "success": False,
                "error": "Timeout al conectar con Zapier",
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)[:200],
            }
    
    def send_email(self, to: str, subject: str, body: str, cc: str = "") -> Dict[str, Any]:
        data = {"to": to, "subject": subject, "body": body}
        if cc:
            data["cc"] = cc
        return self.send("email", data)
    
    def create_calendar_event(self, title: str, date: str, time_str: str = "",
                               description: str = "", duration_min: int = 60) -> Dict[str, Any]:
        data = {
            "title": title,
            "date": date,
            "time": time_str,
            "description": description,
            "duration_minutes": duration_min,
        }
        return self.send("calendar", data)
    
    def send_slack(self, channel: str, message: str) -> Dict[str, Any]:
        data = {"channel": channel, "message": message}
        return self.send("slack", data)
    
    def add_to_sheets(self, sheet_name: str, row_data: list) -> Dict[str, Any]:
        data = {"sheet": sheet_name, "row": row_data}
        return self.send("sheets", data)
    
    def is_available(self, action: str = None) -> bool:
        if action:
            return action in self.webhooks
        return len(self.webhooks) > 0
    
    def list_actions(self) -> list:
        return list(self.webhooks.keys())

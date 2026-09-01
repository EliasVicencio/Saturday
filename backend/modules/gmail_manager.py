"""Gmail API integration for reading emails."""
import os, json, logging, base64, urllib.parse
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

logger = logging.getLogger("saturday.gmail")

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

class GmailManager:
    def __init__(self, core):
        self.core = core
        self.data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
        os.makedirs(self.data_dir, exist_ok=True)
        self._cred_file = os.path.join(self.data_dir, 'google_fit_credentials.json')
        self._token_file = os.path.join(self.data_dir, 'gmail_tokens.json')
    
    def _load_client_config(self) -> Dict:
        if os.path.exists(self._cred_file):
            with open(self._cred_file) as f:
                return json.load(f)
        return {}
    
    def get_auth_url(self, redirect_uri: str) -> Optional[str]:
        try:
            config = self._load_client_config()
            if not config:
                return None
            
            client_config = config.get("web") or config.get("installed", {})
            params = {
                "client_id": client_config.get("client_id", ""),
                "redirect_uri": redirect_uri,
                "response_type": "code",
                "scope": " ".join(SCOPES),
                "access_type": "offline",
                "prompt": "consent",
            }
            
            return "https://accounts.google.com/o/oauth2/auth?" + urllib.parse.urlencode(params)
        except Exception as e:
            logger.error(f"Error generating Gmail auth URL: {e}")
            return None
    
    def exchange_code(self, code: str, redirect_uri: str) -> bool:
        try:
            import requests as req
            
            config = self._load_client_config()
            if not config:
                return False
            
            client_config = config.get("web") or config.get("installed", {})
            
            resp = req.post("https://oauth2.googleapis.com/token", data={
                "code": code,
                "client_id": client_config.get("client_id"),
                "client_secret": client_config.get("client_secret"),
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            })
            
            if resp.status_code != 200:
                logger.error(f"Gmail token exchange failed: {resp.text}")
                return False
            
            tokens = resp.json()
            
            save_data = {
                "access_token": tokens.get("access_token"),
                "refresh_token": tokens.get("refresh_token"),
                "token_uri": "https://oauth2.googleapis.com/token",
                "client_id": client_config.get("client_id"),
                "client_secret": client_config.get("client_secret"),
                "scopes": SCOPES,
                "expiry": (datetime.now() + timedelta(seconds=tokens.get("expires_in", 3600))).isoformat()
            }
            
            with open(self._token_file, 'w') as f:
                json.dump(save_data, f, indent=2)
            
            logger.info("Gmail tokens saved")
            return True
        except Exception as e:
            logger.error(f"Error exchanging Gmail code: {e}")
            return False
    
    def _get_access_token(self) -> Optional[str]:
        try:
            import requests as req
            
            if not os.path.exists(self._token_file):
                return None
            
            with open(self._token_file) as f:
                token_data = json.load(f)
            
            expiry = datetime.fromisoformat(token_data.get("expiry", "2000-01-01"))
            
            if datetime.now() >= expiry and token_data.get("refresh_token"):
                resp = req.post("https://oauth2.googleapis.com/token", data={
                    "client_id": token_data["client_id"],
                    "client_secret": token_data["client_secret"],
                    "refresh_token": token_data["refresh_token"],
                    "grant_type": "refresh_token",
                })
                
                if resp.status_code == 200:
                    new_tokens = resp.json()
                    token_data["access_token"] = new_tokens.get("access_token")
                    token_data["expiry"] = (datetime.now() + timedelta(seconds=new_tokens.get("expires_in", 3600))).isoformat()
                    with open(self._token_file, 'w') as f:
                        json.dump(token_data, f, indent=2)
            
            return token_data.get("access_token")
        except Exception as e:
            logger.error(f"Error getting Gmail access token: {e}")
            return None
    
    def get_recent_emails(self, max_results: int = 10, query: str = "") -> List[Dict[str, Any]]:
        token = self._get_access_token()
        if not token:
            return []
        
        try:
            import requests as req
            headers = {"Authorization": f"Bearer {token}"}
            
            search_q = query if query else "is:unread"
            
            resp = req.get(
                "https://gmail.googleapis.com/gmail/v1/users/me/messages",
                headers=headers,
                params={"q": search_q, "maxResults": max_results}
            )
            
            if resp.status_code != 200:
                logger.error(f"Gmail list failed: {resp.text}")
                return []
            
            messages = resp.json().get("messages", [])
            emails = []
            
            for msg in messages:
                msg_resp = req.get(
                    f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg['id']}",
                    headers=headers,
                    params={"format": "full"}
                )
                
                if msg_resp.status_code == 200:
                    msg_data = msg_resp.json()
                    headers_dict = {}
                    for h in msg_data.get("payload", {}).get("headers", []):
                        headers_dict[h["name"].lower()] = h["value"]
                    # Also check top-level headers
                    for h in msg_data.get("headers", []):
                        headers_dict[h["name"].lower()] = h["value"]
                    
                    snippet = msg_data.get("snippet", "")
                    
                    emails.append({
                        "id": msg["id"],
                        "from": headers_dict.get("from", "Desconocido"),
                        "subject": headers_dict.get("subject", "Sin asunto"),
                        "date": headers_dict.get("date", ""),
                        "snippet": snippet[:200],
                        "labels": msg_data.get("labelIds", []),
                    })
            
            return emails
            
        except Exception as e:
            logger.error(f"Error getting Gmail messages: {e}")
            return []
    
    def get_summary(self) -> Dict[str, Any]:
        emails = self.get_recent_emails(max_results=15)
        
        if not emails:
            return {
                "summary": "No hay correos disponibles.",
                "email_count": 0,
                "connected": self.is_connected()
            }
        
        # Build summary
        unread = [e for e in emails if "UNREAD" in e.get("labels", [])]
        
        lines = [f"📧 {len(emails)} correo(s) recientes ({len(unread)} sin leer):"]
        for e in emails[:10]:
            sender = e["from"].split("<")[0].strip().strip('"')
            subject = e["subject"]
            snippet = e["snippet"][:80]
            lines.append(f"\n• De: {sender}")
            lines.append(f"  Asunto: {subject}")
            if snippet:
                lines.append(f"  {snippet}...")
        
        return {
            "summary": "\n".join(lines),
            "email_count": len(emails),
            "unread_count": len(unread),
            "emails": emails[:10],
            "connected": True
        }
    
    def is_connected(self) -> bool:
        return os.path.exists(self._token_file)
    
    def get_status(self) -> str:
        if self.is_connected():
            return "Gmail: Conectado"
        return "Gmail: No conectado"
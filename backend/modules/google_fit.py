"""Google Fit API integration for health data."""
import os, json, logging, secrets, urllib.parse
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

logger = logging.getLogger("saturday.google_fit")

SCOPES = [
    "https://www.googleapis.com/auth/fitness.activity.read",
    "https://www.googleapis.com/auth/fitness.body.read",
    "https://www.googleapis.com/auth/fitness.heart_rate.read",
    "https://www.googleapis.com/auth/fitness.sleep.read",
]

class GoogleFitManager:
    def __init__(self, core):
        self.core = core
        self.data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
        os.makedirs(self.data_dir, exist_ok=True)
        self._token_file = os.path.join(self.data_dir, 'google_fit_tokens.json')
        self._cred_file = os.path.join(self.data_dir, 'google_fit_credentials.json')
    
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
            
            client_config = config.get("installed") or config.get("web", {})
            client_id = client_config.get("client_id", "")
            client_secret = client_config.get("client_secret", "")
            auth_uri = client_config.get("auth_uri", "https://accounts.google.com/o/oauth2/auth")
            
            state = secrets.token_urlsafe(32)
            
            params = {
                "client_id": client_id,
                "redirect_uri": redirect_uri,
                "response_type": "code",
                "scope": " ".join(SCOPES),
                "access_type": "offline",
                "prompt": "consent",
                "state": state,
            }
            
            auth_url = auth_uri + "?" + urllib.parse.urlencode(params)
            return auth_url
            
        except Exception as e:
            logger.error(f"Error generating auth URL: {e}")
            return None
    
    def exchange_code(self, code: str, redirect_uri: str) -> bool:
        try:
            import requests as req
            
            config = self._load_client_config()
            if not config:
                return False
            
            client_config = config.get("installed") or config.get("web", {})
            
            token_data = {
                "code": code,
                "client_id": client_config.get("client_id"),
                "client_secret": client_config.get("client_secret"),
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            }
            
            resp = req.post("https://oauth2.googleapis.com/token", data=token_data)
            
            if resp.status_code != 200:
                logger.error(f"Token exchange failed: {resp.text}")
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
            
            logger.info("Google Fit tokens saved")
            return True
        except Exception as e:
            logger.error(f"Error exchanging code: {e}")
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
            logger.error(f"Error getting access token: {e}")
            return None
    
    def _api_get(self, url: str, params: Dict = None) -> Optional[Dict]:
        import requests as req
        token = self._get_access_token()
        if not token:
            return None
        headers = {"Authorization": f"Bearer {token}"}
        resp = req.get(url, headers=headers, params=params)
        if resp.status_code == 200:
            return resp.json()
        return None
    
    def get_today_data(self) -> Dict[str, Any]:
        token = self._get_access_token()
        if not token:
            return {"connected": False, "error": "No conectado con Google Fit"}
        
        try:
            now = datetime.now()
            start_ms = int(now.replace(hour=0, minute=0, second=0, microsecond=0).timestamp() * 1000)
            end_ms = int(now.timestamp() * 1000)
            
            result = {"connected": True, "date": now.strftime("%Y-%m-%d")}
            
            # Aggregate data
            body = {
                "aggregateBy": [
                    {"dataTypeName": "com.google.step_count.delta"},
                    {"dataTypeName": "com.google.calories.expended"},
                    {"dataTypeName": "com.google.distance.delta"},
                ],
                "bucketByTime": {"durationMillis": 86400000},
                "startTimeMillis": start_ms,
                "endTimeMillis": end_ms,
            }
            
            resp_data = self._api_get(
                "https://www.googleapis.com/fitness/v1/users/me/dataset:aggregate",
                params={"alt": "json"}
            )
            
            # Use POST for aggregate
            import requests as req
            token = self._get_access_token()
            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
            agg_resp = req.post(
                "https://www.googleapis.com/fitness/v1/users/me/dataset:aggregate",
                headers=headers,
                json=body
            )
            
            if agg_resp.status_code == 200:
                data = agg_resp.json()
                for bucket in data.get("bucket", []):
                    for ds in bucket.get("dataset", []):
                        dt = ds.get("dataSourceId", "")
                        for pt in ds.get("point", []):
                            for val in pt.get("value", []):
                                if "step_count" in dt:
                                    result["steps"] = val.get("intVal", 0)
                                elif "calories" in dt:
                                    result["calories"] = round(val.get("fpVal", 0))
                                elif "distance" in dt:
                                    result["distance_km"] = round(val.get("fpVal", 0) / 1000, 2)
            
            # Heart rate
            hr_resp = req.get(
                f"https://www.googleapis.com/fitness/v1/users/me/dataSources/com.google.heart_rate.bpm/datasets/{start_ms}-{end_ms}",
                headers=headers
            )
            if hr_resp.status_code == 200:
                hr_data = hr_resp.json()
                hr_values = []
                for pt in hr_data.get("point", []):
                    for val in pt.get("value", []):
                        hr_values.append(val.get("fpVal", 0))
                result["heart_rate_avg"] = round(sum(hr_values) / len(hr_values)) if hr_values else None
            
            result.setdefault("steps", 0)
            result.setdefault("calories", 0)
            result.setdefault("distance_km", 0)
            result.setdefault("heart_rate_avg", None)
            
            # Cache
            with open(os.path.join(self.data_dir, 'google_fit_cache.json'), 'w') as f:
                json.dump(result, f, indent=2)
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting Google Fit data: {e}")
            return {"connected": True, "error": str(e)}
    
    def is_connected(self) -> bool:
        return os.path.exists(self._token_file)
    
    def get_status(self) -> str:
        if self.is_connected():
            return "Google Fit: Conectado"
        return "Google Fit: No conectado"
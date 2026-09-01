"""Integración con Google Fit API para datos de salud."""
import os, json, logging, time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

logger = logging.getLogger("saturday.google_fit")

GOOGLE_FIT_SCOPES = [
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
        self._cache_file = os.path.join(self.data_dir, 'google_fit_cache.json')
        self._credentials = None
        self._flow = None
        self._load_credentials()
    
    def _load_credentials(self):
        try:
            creds_json = os.environ.get("GOOGLE_FIT_CREDENTIALS", "")
            if not creds_json:
                cred_file = os.path.join(self.data_dir, 'google_fit_credentials.json')
                if os.path.exists(cred_file):
                    with open(cred_file) as f:
                        creds_json = f.read()
            
            if creds_json:
                creds_dict = json.loads(creds_json) if isinstance(creds_json, str) else creds_json
                self._credentials = creds_dict
                logger.info("Google Fit credentials loaded")
        except Exception as e:
            logger.warning(f"Google Fit credentials not loaded: {e}")
    
    def get_auth_url(self, redirect_uri: str = "https://saturday.viewdns.net/api/health/google-fit/callback") -> Optional[str]:
        try:
            from google_auth_oauthlib.flow import Flow
            
            client_id = os.environ.get("GOOGLE_FIT_CLIENT_ID", "")
            client_secret = os.environ.get("GOOGLE_FIT_CLIENT_SECRET", "")
            
            if not client_id or not client_secret:
                if self._credentials:
                    client_id = self._credentials.get("client_id", client_id)
                    client_secret = self._credentials.get("client_secret", client_secret)
            
            if not client_id or not client_secret:
                return None
            
            self._flow = Flow.from_client_config(
                {"web": {"client_id": client_id, "client_secret": client_secret, "auth_uri": "https://accounts.google.com/o/oauth2/auth", "token_uri": "https://oauth2.googleapis.com/token"}},
                scopes=GOOGLE_FIT_SCOPES,
            )
            self._flow.redirect_uri = redirect_uri
            
            auth_url, _ = self._flow.authorization_url(access_type="offline", prompt="consent")
            return auth_url
        except Exception as e:
            logger.error(f"Error generating auth URL: {e}")
            return None
    
    def handle_callback(self, code: str, redirect_uri: str = "https://saturday.viewdns.net/api/health/google-fit/callback") -> bool:
        try:
            if not self._flow:
                return False
            
            self._flow.fetch_token(code=code)
            credentials = self._flow.credentials
            
            token_data = {
                "token": credentials.token,
                "refresh_token": credentials.refresh_token,
                "token_uri": credentials.token_uri,
                "client_id": credentials.client_id,
                "client_secret": credentials.client_secret,
                "scopes": list(credentials.scopes),
                "expiry": credentials.expiry.isoformat() if credentials.expiry else None
            }
            
            with open(self._token_file, 'w') as f:
                json.dump(token_data, f, indent=2)
            
            logger.info("Google Fit tokens saved")
            return True
        except Exception as e:
            logger.error(f"Error handling callback: {e}")
            return False
    
    def _get_credentials(self):
        try:
            from google.oauth2.credentials import Credentials
            from google.auth.transport.requests import Request
            
            if not os.path.exists(self._token_file):
                return None
            
            with open(self._token_file) as f:
                token_data = json.load(f)
            
            creds = Credentials(
                token=token_data.get("token"),
                refresh_token=token_data.get("refresh_token"),
                token_uri=token_data.get("token_uri", "https://oauth2.googleapis.com/token"),
                client_id=token_data.get("client_id"),
                client_secret=token_data.get("client_secret"),
                scopes=token_data.get("scopes"),
            )
            
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
                token_data["token"] = creds.token
                token_data["expiry"] = creds.expiry.isoformat() if creds.expiry else None
                with open(self._token_file, 'w') as f:
                    json.dump(token_data, f, indent=2)
            
            return creds
        except Exception as e:
            logger.error(f"Error getting credentials: {e}")
            return None
    
    def get_today_data(self) -> Dict[str, Any]:
        creds = self._get_credentials()
        if not creds:
            return {"connected": False, "error": "No conectado con Google Fit"}
        
        try:
            from googleapiclient.discovery import build
            
            service = build("fitness", "v1", credentials=creds)
            
            now = datetime.now()
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            today_end = now
            
            start_ms = int(today_start.timestamp() * 1000)
            end_ms = int(today_end.timestamp() * 1000)
            
            result = {"connected": True, "date": now.strftime("%Y-%m-%d")}
            
            # Steps
            try:
                body = {
                    "aggregateBy": [{"dataTypeName": "com.google.step_count.delta"}],
                    "bucketByTime": {"durationMillis": 86400000},
                    "startTimeMillis": start_ms,
                    "endTimeMillis": end_ms,
                }
                resp = service.users().dataset().aggregate(userId="me", body=body).execute()
                for bucket in resp.get("bucket", []):
                    for ds in bucket.get("dataset", []):
                        for pt in ds.get("point", []):
                            for val in pt.get("value", []):
                                result["steps"] = val.get("intVal", 0)
            except Exception:
                result["steps"] = 0
            
            # Heart rate
            try:
                resp = service.users().dataset().get(
                    userId="me",
                    datasetId=f"{start_ms}-{end_ms}",
                    dataSourceId="com.google.heart_rate.bpm",
                ).execute()
                hr_values = []
                for ds in resp.get("point", []):
                    for val in ds.get("value", []):
                        hr_values.append(val.get("fpVal", 0))
                result["heart_rate_avg"] = round(sum(hr_values) / len(hr_values)) if hr_values else None
            except Exception:
                result["heart_rate_avg"] = None
            
            # Calories
            try:
                body = {
                    "aggregateBy": [{"dataTypeName": "com.google.calories.expended"}],
                    "bucketByTime": {"durationMillis": 86400000},
                    "startTimeMillis": start_ms,
                    "endTimeMillis": end_ms,
                }
                resp = service.users().dataset().aggregate(userId="me", body=body).execute()
                for bucket in resp.get("bucket", []):
                    for ds in bucket.get("dataset", []):
                        for pt in ds.get("point", []):
                            for val in pt.get("value", []):
                                result["calories"] = round(val.get("fpVal", 0))
            except Exception:
                result["calories"] = 0
            
            # Sleep (from last night)
            try:
                sleep_start = (now - timedelta(days=1)).replace(hour=20, minute=0, second=0, microsecond=0)
                sleep_end = now.replace(hour=12, minute=0, second=0, microsecond=0)
                s_start_ms = int(sleep_start.timestamp() * 1000)
                s_end_ms = int(sleep_end.timestamp() * 1000)
                
                resp = service.users().dataset().get(
                    userId="me",
                    datasetId=f"{s_start_ms}-{s_end_ms}",
                    dataSourceId="com.google.sleep.segment",
                ).execute()
                
                sleep_minutes = 0
                for ds in resp.get("point", []):
                    for val in ds.get("value", []):
                        if val.get("intVal", 0) in [1, 2, 3, 4, 5, 6]:
                            sleep_minutes += 30
                result["sleep_hours"] = round(sleep_minutes / 60, 1) if sleep_minutes > 0 else None
            except Exception:
                result["sleep_hours"] = None
            
            # Cache result
            with open(self._cache_file, 'w') as f:
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

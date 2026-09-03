# modules/google_drive.py - Google Drive integration para Saturday
"""Google Drive - Acceso completo a tu nube."""
import os, json, logging
from typing import Optional, Dict, List, Any
from datetime import datetime

logger = logging.getLogger("saturday.google_drive")

GOOGLE_DRIVE_CLIENT_ID = os.environ.get("GOOGLE_DRIVE_CLIENT_ID", "")
GOOGLE_DRIVE_CLIENT_SECRET = os.environ.get("GOOGLE_DRIVE_CLIENT_SECRET", "")
GOOGLE_DRIVE_REDIRECT_URI = os.environ.get("GOOGLE_DRIVE_REDIRECT_URI", "https://saturday.viewdns.net/api/google-drive/callback")

class GoogleDriveManager:
    def __init__(self, core):
        self.core = core
        self.data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
        os.makedirs(self.data_dir, exist_ok=True)
        self._token_file = os.path.join(self.data_dir, 'google_drive_tokens.json')
        self._credentials_file = os.path.join(self.data_dir, 'google_drive_credentials.json')
        self._service = None
        
        if GOOGLE_DRIVE_CLIENT_ID and GOOGLE_DRIVE_CLIENT_SECRET:
            self._save_credentials({
                "installed": {
                    "client_id": GOOGLE_DRIVE_CLIENT_ID,
                    "client_secret": GOOGLE_DRIVE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [GOOGLE_DRIVE_REDIRECT_URI]
                }
            })
    
    def _save_credentials(self, creds: Dict):
        try:
            with open(self._credentials_file, 'w') as f:
                json.dump(creds, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving credentials: {e}")
    
    def _get_access_token(self) -> Optional[str]:
        if not os.path.exists(self._token_file):
            return None
        
        try:
            with open(self._token_file, 'r') as f:
                token_data = json.load(f)
            
            if token_data.get('expiry_date', 0) < datetime.now().timestamp() * 1000:
                import requests
                resp = requests.post('https://oauth2.googleapis.com/token', data={
                    'client_id': GOOGLE_DRIVE_CLIENT_ID,
                    'client_secret': GOOGLE_DRIVE_CLIENT_SECRET,
                    'refresh_token': token_data.get('refresh_token'),
                    'grant_type': 'refresh_token'
                })
                
                if resp.status_code == 200:
                    new_token = resp.json()
                    token_data['access_token'] = new_token['access_token']
                    token_data['expiry_date'] = datetime.now().timestamp() * 1000 + new_token.get('expires_in', 3600) * 1000
                    with open(self._token_file, 'w') as f:
                        json.dump(token_data, f)
                    return token_data['access_token']
                else:
                    logger.error(f"Token refresh failed: {resp.text}")
                    return None
            
            return token_data.get('access_token')
        except Exception as e:
            logger.error(f"Error getting access token: {e}")
            return None
    
    def get_auth_url(self) -> str:
        from urllib.parse import urlencode
        params = {
            'client_id': GOOGLE_DRIVE_CLIENT_ID,
            'redirect_uri': GOOGLE_DRIVE_REDIRECT_URI,
            'response_type': 'code',
            'scope': 'https://www.googleapis.com/auth/drive',
            'access_type': 'offline',
            'prompt': 'consent'
        }
        return f"https://accounts.google.com/o/oauth2/auth?{urlencode(params)}"
    
    def exchange_code(self, code: str) -> bool:
        try:
            import requests
            resp = requests.post('https://oauth2.googleapis.com/token', data={
                'code': code,
                'client_id': GOOGLE_DRIVE_CLIENT_ID,
                'client_secret': GOOGLE_DRIVE_CLIENT_SECRET,
                'redirect_uri': GOOGLE_DRIVE_REDIRECT_URI,
                'grant_type': 'authorization_code'
            })
            
            if resp.status_code == 200:
                token_data = resp.json()
                token_data['expiry_date'] = datetime.now().timestamp() * 1000 + token_data.get('expires_in', 3600) * 1000
                with open(self._token_file, 'w') as f:
                    json.dump(token_data, f)
                logger.info("Google Drive tokens saved")
                return True
            else:
                logger.error(f"Code exchange failed: {resp.text}")
                return False
        except Exception as e:
            logger.error(f"Error exchanging code: {e}")
            return False
    
    def is_connected(self) -> bool:
        return self._get_access_token() is not None
    
    def _api_request(self, method: str, url: str, **kwargs) -> Optional[Dict]:
        token = self._get_access_token()
        if not token:
            return None
        
        import requests
        headers = {'Authorization': f'Bearer {token}', **kwargs.get('headers', {})}
        
        resp = requests.request(method, url, headers=headers, **kwargs)
        if resp.status_code == 200:
            return resp.json()
        else:
            logger.error(f"API request failed: {resp.status_code} {resp.text[:200]}")
            return None
    
    def list_files(self, folder_id: str = None, query: str = None, max_results: int = 20) -> List[Dict]:
        try:
            params = {
                'pageSize': max_results,
                'fields': 'nextPageToken, files(id, name, mimeType, size, modifiedTime, webViewLink, parents)',
                'orderBy': 'modifiedTime desc'
            }
            
            if folder_id:
                params['q'] = f"'{folder_id}' in parents and trashed=false"
            elif query:
                params['q'] = f"name contains '{query}' and trashed=false"
            else:
                params['q'] = "trashed=false"
            
            result = self._api_request('GET', 'https://www.googleapis.com/drive/v3/files', params=params)
            return result.get('files', []) if result else []
        except Exception as e:
            logger.error(f"Error listing files: {e}")
            return []
    
    def search_files(self, query: str, max_results: int = 10) -> List[Dict]:
        try:
            params = {
                'q': f"name contains '{query}' and trashed=false",
                'pageSize': max_results,
                'fields': 'files(id, name, mimeType, size, modifiedTime, webViewLink)'
            }
            result = self._api_request('GET', 'https://www.googleapis.com/drive/v3/files', params=params)
            return result.get('files', []) if result else []
        except Exception as e:
            logger.error(f"Error searching files: {e}")
            return []
    
    def get_file_content(self, file_id: str) -> Optional[str]:
        try:
            meta = self._api_request('GET', f'https://www.googleapis.com/drive/v3/files/{file_id}?fields=mimeType,name')
            if not meta:
                return None
            
            mime_type = meta.get('mimeType', '')
            file_name = meta.get('name', '')
            
            if 'google-apps.document' in mime_type:
                result = self._api_request('GET', f'https://www.googleapis.com/drive/v3/files/{file_id}/export?mimeType=text/plain')
                if result:
                    return result
            
            if any(t in mime_type for t in ['text/', 'application/json', 'application/xml']):
                result = self._api_request('GET', f'https://www.googleapis.com/drive/v3/files/{file_id}?alt=media')
                if result:
                    return result
            
            return f"Archivo: {file_name} (tipo: {mime_type}) - No se puede leer contenido de este tipo de archivo"
        except Exception as e:
            logger.error(f"Error getting file content: {e}")
            return None
    
    def create_file(self, name: str, content: str, folder_id: str = None, mime_type: str = 'text/plain') -> Optional[Dict]:
        try:
            import requests
            
            metadata = {
                'name': name,
                'mimeType': mime_type
            }
            if folder_id:
                metadata['parents'] = [folder_id]
            
            files = {
                'metadata': (None, json.dumps(metadata), 'application/json'),
                'file': (name, content.encode('utf-8'), mime_type)
            }
            
            token = self._get_access_token()
            headers = {'Authorization': f'Bearer {token}'}
            
            resp = requests.post(
                'https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart',
                headers=headers,
                files=files
            )
            
            if resp.status_code == 200:
                return resp.json()
            else:
                logger.error(f"Error creating file: {resp.text}")
                return None
        except Exception as e:
            logger.error(f"Error creating file: {e}")
            return None
    
    def create_folder(self, name: str, parent_id: str = None) -> Optional[Dict]:
        try:
            metadata = {
                'name': name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            if parent_id:
                metadata['parents'] = [parent_id]
            
            result = self._api_request('POST', 'https://www.googleapis.com/drive/v3/files', json=metadata)
            return result
        except Exception as e:
            logger.error(f"Error creating folder: {e}")
            return None
    
    def get_storage_info(self) -> Dict[str, Any]:
        try:
            result = self._api_request('GET', 'https://www.googleapis.com/drive/v3/about?fields=user(displayName,storageQuota)')
            if result:
                quota = result.get('storageQuota', {})
                return {
                    'used': int(quota.get('usage', 0)),
                    'limit': int(quota.get('limit', 0)),
                    'used_gb': round(int(quota.get('usage', 0)) / (1024**3), 2),
                    'limit_gb': round(int(quota.get('limit', 0)) / (1024**3), 2)
                }
        except Exception as e:
            logger.error(f"Error getting storage info: {e}")
        return {}
    
    def get_status(self) -> str:
        if self.is_connected():
            info = self.get_storage_info()
            return f"Google Drive conectado | {info.get('used_gb', 0)} GB / {info.get('limit_gb', 0)} GB"
        return "Google Drive no conectado"

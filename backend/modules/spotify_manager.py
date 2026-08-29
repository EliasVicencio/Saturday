# modules/spotify_manager.py
import os
import webbrowser
import time
from typing import Dict, Any, Optional
import requests
import urllib.parse

try:
    import spotipy
    from spotipy.oauth2 import SpotifyOAuth
    SPOTIPY_AVAILABLE = True
except ImportError:
    SPOTIPY_AVAILABLE = False
    print(" spotipy no instalado. Instalar con: pip install spotipy")

class SpotifyManager:
    """Gestor de Spotify para Saturday"""
    
    def __init__(self):
        self.client_id = os.getenv("SPOTIFY_CLIENT_ID")
        self.client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
        self.redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI", "http://localhost:8888/callback")
        self.scope = "user-read-playback-state user-modify-playback-state user-read-currently-playing app-remote-control streaming"
        
        self.sp = None
        self._authenticate()
    
    def _authenticate(self):
        """Autentica con Spotify"""
        if not SPOTIPY_AVAILABLE:
            print(" Spotipy no disponible")
            return
        
        if not self.client_id or not self.client_secret:
            print(" SPOTIFY_CLIENT_ID y SPOTIFY_CLIENT_SECRET no configurados")
            return
        
        try:
            self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
                client_id=self.client_id,
                client_secret=self.client_secret,
                redirect_uri=self.redirect_uri,
                scope=self.scope,
                cache_path="credentials/spotify_token.pickle"
            ))
            print(" Spotify autenticado correctamente")
        except Exception as e:
            print(f" Error autenticando Spotify: {e}")
    
    def is_authenticated(self) -> bool:
        """Verifica si está autenticado"""
        return self.sp is not None
    
    def open_spotify(self) -> str:
        """Abre Spotify Web en el navegador"""
        webbrowser.open("https://open.spotify.com")
        return " Abriendo Spotify Web..."
    
    def play(self, query: str = None) -> str:
        """Reproduce música en Spotify"""
        if not self.is_authenticated():
            return " Spotify no autenticado. Revisa las credenciales."
        
        try:
            # Verificar dispositivos disponibles
            devices = self.sp.devices()
            if not devices.get('devices'):
                # Intentar abrir Spotify Web si no hay dispositivos
                webbrowser.open("https://open.spotify.com")
                return " No hay dispositivo activo. Abriendo Spotify Web. Inicia sesión y reproduce algo para activar un dispositivo."
            
            device_id = devices['devices'][0]['id']
            print(f" Dispositivo activo: {devices['devices'][0].get('name', 'Desconocido')}")
            
            # Si hay query, buscar y reproducir
            if query and query.strip():
                # Limpiar la query de palabras clave
                clean_query = query
                for word in ["reproduce", "reproducir", "pon", "toca", "play", "música", "musica", "canción", "cancion", "la", "el", "de"]:
                    clean_query = clean_query.replace(word, "").strip()
                
                if clean_query:
                    print(f" Buscando: {clean_query}")
                    results = self.sp.search(q=clean_query, type='track', limit=3)
                    if results['tracks']['items']:
                        track = results['tracks']['items'][0]
                        track_uri = track['uri']
                        track_name = track['name']
                        artist_name = track['artists'][0]['name']
                        
                        self.sp.start_playback(device_id=device_id, uris=[track_uri])
                        return f" Reproduciendo: {track_name} - {artist_name}"
                    else:
                        return f" No encontré: {clean_query}"
            
            # Si no hay query, reanudar
            self.sp.start_playback(device_id=device_id)
            return " Reanudando reproducción..."
                    
        except Exception as e:
            error_msg = str(e)
            if "NO_ACTIVE_DEVICE" in error_msg:
                return " No hay dispositivo activo. Abre Spotify en tu PC o teléfono."
            return f" Error al reproducir: {error_msg}"
    
    def pause(self) -> str:
        """Pausa la reproducción"""
        if not self.is_authenticated():
            return " Spotify no autenticado"
        
        try:
            self.sp.pause_playback()
            return " Música pausada"
        except Exception as e:
            return f" Error al pausar: {e}"
    
    def next_track(self) -> str:
        """Siguiente canción"""
        if not self.is_authenticated():
            return " Spotify no autenticado"
        
        try:
            self.sp.next_track()
            return " Siguiente canción"
        except Exception as e:
            return f" Error: {e}"
    
    def previous_track(self) -> str:
        """Canción anterior"""
        if not self.is_authenticated():
            return " Spotify no autenticado"
        
        try:
            self.sp.previous_track()
            return " Canción anterior"
        except Exception as e:
            return f" Error: {e}"
    
    def get_current_track(self) -> str:
        """Obtiene la canción actual"""
        if not self.is_authenticated():
            return " Spotify no autenticado"
        
        try:
            current = self.sp.current_playback()
            if current and current.get('item'):
                track_name = current['item']['name']
                artist_name = current['item']['artists'][0]['name']
                progress = current.get('progress_ms', 0) // 1000
                duration = current['item']['duration_ms'] // 1000
                
                mins, secs = divmod(progress, 60)
                total_mins, total_secs = divmod(duration, 60)
                
                return f" Reproduciendo: {track_name} - {artist_name} ({mins:02d}:{secs:02d}/{total_mins:02d}:{total_secs:02d})"
            else:
                return " No hay reproducción activa"
        except Exception as e:
            return f" Error: {e}"
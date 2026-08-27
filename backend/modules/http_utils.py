# modules/http_utils.py - HTTP utilities with retry/backoff
import time
import logging
import requests
from typing import Optional, Dict, Any

logger = logging.getLogger('saturday.http')

def request_with_retry(
    method: str,
    url: str,
    max_retries: int = 3,
    backoff_factor: float = 1.0,
    timeout: int = 15,
    **kwargs
) -> Optional[requests.Response]:
    """
    Realiza una petición HTTP con retry y exponential backoff.
    
    Args:
        method: 'GET', 'POST', 'PATCH', etc.
        url: URL de la petición
        max_retries: Número máximo de reintentos (default: 3)
        backoff_factor: Factor de backoff exponencial (default: 1.0)
        timeout: Timeout en segundos (default: 15)
        **kwargs: Argumentos adicionales para requests
    
    Returns:
        Response object o None si todos los reintentos fallan
    """
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            response = requests.request(method, url, timeout=timeout, **kwargs)
            if response.status_code < 500:
                return response
            
            last_exception = requests.HTTPError(f"HTTP {response.status_code}")
            logger.warning(f"HTTP {response.status_code} en {url} (intento {attempt + 1}/{max_retries + 1})")
            
        except requests.RequestException as e:
            last_exception = e
            logger.warning(f"Error de red en {url}: {e} (intento {attempt + 1}/{max_retries + 1})")
        
        if attempt < max_retries:
            wait_time = backoff_factor * (2 ** attempt)
            logger.info(f"Reintentando en {wait_time:.1f}s...")
            time.sleep(wait_time)
    
    logger.error(f"Todos los reintentos fallaron para {url}: {last_exception}")
    return None


def get_with_retry(url: str, **kwargs) -> Optional[requests.Response]:
    """GET con retry."""
    return request_with_retry('GET', url, **kwargs)


def post_with_retry(url: str, **kwargs) -> Optional[requests.Response]:
    """POST con retry."""
    return request_with_retry('POST', url, **kwargs)


def patch_with_retry(url: str, **kwargs) -> Optional[requests.Response]:
    """PATCH con retry."""
    return request_with_retry('PATCH', url, **kwargs)

# modules/news_manager.py - Usando NewsData.io
import os
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

class NewsManager:
    """Gestor de noticias para Saturday usando NewsData.io"""
    
    def __init__(self):
        self.api_key = os.getenv("NEWSDATA_API_KEY")
        self.base_url = "https://newsdata.io/api/1"
        self.country = os.getenv("NEWSDATA_COUNTRY", "cl")
        self.language = os.getenv("NEWSDATA_LANGUAGE", "es")
        self.category = os.getenv("NEWSDATA_CATEGORY", "top")
        
        if not self.api_key:
            print("⚠️ NEWSDATA_API_KEY no configurada.")
            print("   Regístrate en: https://newsdata.io/")
        else:
            print("📰 NewsManager inicializado (NewsData.io)")
    
    def is_available(self) -> bool:
        """Verifica si la API está configurada"""
        return bool(self.api_key)
    
    def get_top_headlines(self, category: str = None, country: str = None, limit: int = 5) -> List[Dict]:
        """Obtiene las noticias principales"""
        if not self.is_available():
            return []
        
        try:
            url = f"{self.base_url}/news"
            params = {
                'apikey': self.api_key,
                'language': self.language,
                'size': limit,
                'removeduplicate': 1
            }
            
            # Agregar país si se especifica
            if country:
                params['country'] = country
            elif self.country:
                params['country'] = self.country
            
            # Agregar categoría
            if category:
                params['category'] = category
            elif self.category:
                params['category'] = self.category
            
            print(f"📤 Solicitando noticias a NewsData.io...")
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status') == 'success':
                articles = data.get('results', [])
                if not articles:
                    print(f"⚠️ No hay artículos. Respuesta: {data.get('message', 'Sin resultados')}")
                    # Intentar sin país
                    if 'country' in params:
                        print("🔄 Intentando sin filtro de país...")
                        del params['country']
                        response = requests.get(url, params=params, timeout=10)
                        data = response.json()
                        if data.get('status') == 'success':
                            articles = data.get('results', [])
                
                formatted = []
                for article in articles[:limit]:
                    # Saltar artículos sin título
                    if not article.get('title'):
                        continue
                    
                    formatted.append({
                        'title': article.get('title', 'Sin título'),
                        'description': article.get('description', 'Sin descripción') or 'Sin descripción',
                        'source': article.get('source_id', 'Fuente desconocida'),
                        'source_name': article.get('source_name', article.get('source_id', 'Fuente desconocida')),
                        'url': article.get('link', ''),
                        'published_at': article.get('pubDate', ''),
                        'image': article.get('image_url', ''),
                        'category': article.get('category', [])
                    })
                return formatted
            else:
                print(f"⚠️ Error en NewsData.io: {data.get('message', 'Error desconocido')}")
                return []
                
        except Exception as e:
            print(f"⚠️ Error obteniendo noticias: {e}")
            return []
    
    def search_news(self, query: str, limit: int = 5) -> List[Dict]:
        """Busca noticias por palabra clave"""
        if not self.is_available():
            return []
        
        try:
            url = f"{self.base_url}/news"
            params = {
                'apikey': self.api_key,
                'q': query,
                'language': self.language,
                'size': limit,
                'removeduplicate': 1
            }
            
            print(f"🔍 Buscando: {query}")
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status') == 'success':
                articles = data.get('results', [])
                formatted = []
                for article in articles[:limit]:
                    if not article.get('title'):
                        continue
                    formatted.append({
                        'title': article.get('title', 'Sin título'),
                        'description': article.get('description', 'Sin descripción') or 'Sin descripción',
                        'source': article.get('source_id', 'Fuente desconocida'),
                        'source_name': article.get('source_name', article.get('source_id', 'Fuente desconocida')),
                        'url': article.get('link', ''),
                        'published_at': article.get('pubDate', '')
                    })
                return formatted
            else:
                print(f"⚠️ Error en búsqueda: {data.get('message', 'Error desconocido')}")
                return []
                
        except Exception as e:
            print(f"⚠️ Error buscando noticias: {e}")
            return []
    
    def get_news_by_category(self, category: str, limit: int = 5) -> List[Dict]:
        """Obtiene noticias por categoría"""
        return self.get_top_headlines(category=category, limit=limit)
    
    def format_news(self, articles: List[Dict]) -> str:
        """Formatea las noticias para mostrar"""
        if not articles:
            return "📰 No hay noticias disponibles en este momento. Prueba con 'buscar noticias [tema]'"
        
        lines = ["📰 *NOTICIAS DE HOY*"]
        lines.append("")
        
        for i, article in enumerate(articles, 1):
            title = article.get('title', 'Sin título')
            source = article.get('source_name', article.get('source', 'Fuente desconocida'))
            description = article.get('description', '')
            
            # Limpiar título
            if len(title) > 100:
                title = title[:97] + "..."
            
            lines.append(f"**{i}. {title}**")
            lines.append(f"📌 *Fuente:* {source}")
            
            # Categoría
            if article.get('category'):
                categories = ', '.join(article['category'][:2])
                lines.append(f"🏷️ *Categoría:* {categories}")
            
            if description and len(description) > 0:
                desc = description[:120] + "..." if len(description) > 120 else description
                lines.append(f"📝 {desc}")
            lines.append("")
        
        lines.append("💡 *Comandos de noticias:*")
        lines.append("  • 'noticias' - Noticias principales")
        lines.append("  • 'noticias de [categoría]' - Filtrar")
        lines.append("  • 'buscar noticias [tema]' - Buscar")
        lines.append("  • 'noticias resumen' - Enviar por WhatsApp")
        lines.append("")
        lines.append("📰 *Categorías:* business, entertainment, health, science, sports, technology, top, world")
        
        return "\n".join(lines)
    
    def format_news_for_whatsapp(self, articles: List[Dict]) -> str:
        """Formatea noticias para WhatsApp"""
        if not articles:
            return "📰 No hay noticias disponibles."
        
        lines = ["📰 *NOTICIAS DE HOY*"]
        lines.append("")
        
        for i, article in enumerate(articles[:5], 1):
            title = article.get('title', 'Sin título')
            if len(title) > 80:
                title = title[:77] + "..."
            lines.append(f"{i}. {title}")
        
        lines.append("")
        lines.append("💡 Usa 'noticias' para más detalles.")
        
        return "\n".join(lines)
    
    def get_news_summary(self) -> str:
        """Obtiene un resumen de noticias para el día"""
        articles = self.get_top_headlines(limit=5)
        return self.format_news(articles)
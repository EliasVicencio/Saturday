# modules/vault_manager.py
"""
VaultManager - Memoria de Saturday basada en archivos Markdown.

Filosofía (inspirada en el patrón "si no está en la bóveda, no pasó"):
- Nada se guarda en una base de datos. Todo es un archivo .md legible.
- bóveda/
    raw/      -> todo lo capturado sin filtrar (transcripciones, inputs crudos)
    wiki/     -> conocimiento depurado, notas enlazadas entre sí ([[wikilinks]])
    outputs/  -> todo lo que Saturday entrega hacia afuera (informes, resúmenes)
- Las notas de wiki/ se enlazan con sintaxis [[nombre-de-otra-nota]].
- VaultManager arma un grafo (networkx) a partir de esos enlaces, así Saturday
  puede "navegar" su propio conocimiento en vez de solo hacer grep.
"""

import os
import re
import json
from datetime import datetime
from typing import Dict, List, Optional
import networkx as nx


def _slugify(text: str) -> str:
    """Convierte un título en un nombre de archivo seguro."""
    text = text.strip().lower()
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
    text = re.sub(r"[\s_]+", "-", text)
    return text.strip("-") or "nota"


WIKILINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")


class VaultManager:
    """Gestor de la bóveda de memoria de Saturday (Markdown + grafo de enlaces)."""

    def __init__(self, vault_dir: str = "vault"):
        self.vault_dir = vault_dir
        self.raw_dir = os.path.join(vault_dir, "raw")
        self.wiki_dir = os.path.join(vault_dir, "wiki")
        self.outputs_dir = os.path.join(vault_dir, "outputs")

        for d in (self.raw_dir, self.wiki_dir, self.outputs_dir):
            os.makedirs(d, exist_ok=True)

        # Grafo de conocimiento: nodos = notas de wiki/, aristas = [[enlaces]]
        self.graph = nx.DiGraph()
        self.refresh_graph()

    # ------------------------------------------------------------------
    # ESCRITURA
    # ------------------------------------------------------------------

    def save_raw(self, content: str, source: str = "captura") -> str:
        """Guarda algo sin procesar en raw/. Devuelve la ruta relativa creada."""
        ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        filename = f"{ts}_{_slugify(source)}.md"
        path = os.path.join(self.raw_dir, filename)

        frontmatter = (
            "---\n"
            f"source: {source}\n"
            f"captured: {datetime.now().isoformat()}\n"
            "---\n\n"
        )
        with open(path, "w", encoding="utf-8") as f:
            f.write(frontmatter + content.strip() + "\n")

        return os.path.relpath(path, self.vault_dir)

    def save_output(self, content: str, kind: str = "reporte") -> str:
        """Guarda un entregable de Saturday en outputs/."""
        ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        filename = f"{ts}_{_slugify(kind)}.md"
        path = os.path.join(self.outputs_dir, filename)

        frontmatter = (
            "---\n"
            f"kind: {kind}\n"
            f"created: {datetime.now().isoformat()}\n"
            "---\n\n"
        )
        with open(path, "w", encoding="utf-8") as f:
            f.write(frontmatter + content.strip() + "\n")

        return os.path.relpath(path, self.vault_dir)

    def create_wiki_note(self, title: str, content: str, tags: Optional[List[str]] = None) -> str:
        """
        Crea o actualiza una nota en wiki/ (conocimiento depurado).
        Para enlazar con otra nota, usá [[nombre-de-la-nota]] dentro del contenido.
        """
        slug = _slugify(title)
        path = os.path.join(self.wiki_dir, f"{slug}.md")
        tags = tags or []

        frontmatter = (
            "---\n"
            f"title: {title}\n"
            f"tags: [{', '.join(tags)}]\n"
            f"updated: {datetime.now().isoformat()}\n"
            "---\n\n"
        )
        with open(path, "w", encoding="utf-8") as f:
            f.write(frontmatter + f"# {title}\n\n" + content.strip() + "\n")

        self.refresh_graph()
        return os.path.relpath(path, self.vault_dir)

    def link_into_hub(self, hub_title: str, item_title: str, item_summary: str,
                       source_path: Optional[str] = None, tags: Optional[List[str]] = None) -> str:
        """
        Registra un item (p.ej. un resumen diario) como nota enlazada dentro de una
        nota "hub" en wiki/. Crea el hub si no existe, y siempre crea/actualiza una
        nota propia para el item que enlaza de vuelta al hub con [[wikilinks]].

        Esto es lo que hace que cosas como los resúmenes diarios aparezcan como
        nodos reales y conectados en el grafo de la bóveda, en vez de quedar
        sueltos en outputs/ sin ninguna relación visible.
        """
        hub_slug = _slugify(hub_title)
        item_slug = _slugify(item_title)
        tags = tags or []

        # 1) Nota individual del item, enlazando de vuelta al hub
        item_path = os.path.join(self.wiki_dir, f"{item_slug}.md")
        item_body = item_summary.strip()
        if source_path:
            item_body += f"\n\n📎 Fuente original: `{source_path}`"
        item_body += f"\n\nParte de [[{hub_title}]]."

        item_frontmatter = (
            "---\n"
            f"title: {item_title}\n"
            f"tags: [{', '.join(tags)}]\n"
            f"updated: {datetime.now().isoformat()}\n"
            "---\n\n"
        )
        with open(item_path, "w", encoding="utf-8") as f:
            f.write(item_frontmatter + f"# {item_title}\n\n" + item_body + "\n")

        # 2) Hub: se crea si no existe, o se le agrega el enlace si falta
        hub_path = os.path.join(self.wiki_dir, f"{hub_slug}.md")
        link_line = f"- [[{item_title}]]"

        if os.path.exists(hub_path):
            with open(hub_path, "r", encoding="utf-8") as f:
                hub_content = f.read()
            if link_line not in hub_content:
                hub_content = hub_content.rstrip() + f"\n{link_line}\n"
                # refrescar la fecha 'updated' del frontmatter
                hub_content = re.sub(
                    r"^updated:.*$", f"updated: {datetime.now().isoformat()}",
                    hub_content, count=1, flags=re.MULTILINE
                )
                with open(hub_path, "w", encoding="utf-8") as f:
                    f.write(hub_content)
        else:
            hub_frontmatter = (
                "---\n"
                f"title: {hub_title}\n"
                f"tags: [hub]\n"
                f"updated: {datetime.now().isoformat()}\n"
                "---\n\n"
            )
            hub_body = f"# {hub_title}\n\nNotas enlazadas:\n\n{link_line}\n"
            with open(hub_path, "w", encoding="utf-8") as f:
                f.write(hub_frontmatter + hub_body)

        self.refresh_graph()
        return os.path.relpath(item_path, self.vault_dir)

    # ------------------------------------------------------------------
    # LECTURA
    # ------------------------------------------------------------------

    def read_note(self, relative_path: str) -> Optional[str]:
        """Lee el contenido crudo de una nota dada su ruta relativa a la bóveda."""
        full_path = os.path.normpath(os.path.join(self.vault_dir, relative_path))
        # Evitar path traversal fuera de la bóveda
        if not full_path.startswith(os.path.abspath(self.vault_dir)) and not full_path.startswith(self.vault_dir):
            return None
        if not os.path.exists(full_path):
            return None
        with open(full_path, "r", encoding="utf-8") as f:
            return f.read()

    def list_notes(self, layer: str = "wiki") -> List[Dict]:
        """Lista notas de una capa (raw, wiki, outputs)."""
        folder = {"raw": self.raw_dir, "wiki": self.wiki_dir, "outputs": self.outputs_dir}.get(layer)
        if not folder:
            return []

        notes = []
        for filename in sorted(os.listdir(folder)):
            if not filename.endswith(".md"):
                continue
            path = os.path.join(folder, filename)
            notes.append({
                "name": filename,
                "path": os.path.relpath(path, self.vault_dir),
                "modified": datetime.fromtimestamp(os.path.getmtime(path)).isoformat(),
                "size_bytes": os.path.getsize(path),
            })
        return notes

    def search(self, query: str) -> List[Dict]:
        """Busca un texto en todas las capas de la bóveda (grep simple)."""
        query_lower = query.lower()
        results = []
        for root, _, files in os.walk(self.vault_dir):
            for filename in files:
                if not filename.endswith(".md"):
                    continue
                path = os.path.join(root, filename)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read()
                except Exception:
                    continue
                if query_lower in content.lower():
                    snippet_idx = content.lower().find(query_lower)
                    start = max(0, snippet_idx - 60)
                    end = min(len(content), snippet_idx + 60)
                    results.append({
                        "path": os.path.relpath(path, self.vault_dir),
                        "snippet": content[start:end].strip(),
                    })
        return results

    # ------------------------------------------------------------------
    # GRAFO DE CONOCIMIENTO (el "sistema Kárpaty" de la imagen)
    # ------------------------------------------------------------------

    def refresh_graph(self):
        """Reconstruye el grafo a partir de los [[enlaces]] entre notas de wiki/."""
        self.graph = nx.DiGraph()

        wiki_files = [f for f in os.listdir(self.wiki_dir) if f.endswith(".md")]
        slugs = {os.path.splitext(f)[0] for f in wiki_files}

        for filename in wiki_files:
            slug = os.path.splitext(filename)[0]
            path = os.path.join(self.wiki_dir, filename)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            title = slug
            title_match = re.search(r"^title:\s*(.+)$", content, re.MULTILINE)
            if title_match:
                title = title_match.group(1).strip()

            self.graph.add_node(slug, title=title, path=os.path.relpath(path, self.vault_dir))

            for match in WIKILINK_RE.finditer(content):
                target_raw = match.group(1).strip()
                target_slug = _slugify(target_raw)
                if target_slug in slugs:
                    self.graph.add_edge(slug, target_slug)

    def get_graph_json(self) -> Dict:
        """Devuelve el grafo en formato {nodes, edges} listo para el frontend."""
        nodes = [
            {"id": n, "title": data.get("title", n), "path": data.get("path")}
            for n, data in self.graph.nodes(data=True)
        ]
        edges = [{"source": u, "target": v} for u, v in self.graph.edges()]
        return {"nodes": nodes, "edges": edges}

    def get_related(self, slug: str, depth: int = 1) -> List[str]:
        """Notas conectadas a `slug` hasta cierta profundidad (para que Saturday 'navegue')."""
        if slug not in self.graph:
            return []
        related = set()
        frontier = {slug}
        for _ in range(depth):
            next_frontier = set()
            for node in frontier:
                next_frontier |= set(self.graph.successors(node))
                next_frontier |= set(self.graph.predecessors(node))
            related |= next_frontier
            frontier = next_frontier
        related.discard(slug)
        return sorted(related)

    # ------------------------------------------------------------------
    # RESUMEN PARA EL DASHBOARD
    # ------------------------------------------------------------------

    def get_stats(self) -> Dict:
        return {
            "raw_count": len([f for f in os.listdir(self.raw_dir) if f.endswith(".md")]),
            "wiki_count": len([f for f in os.listdir(self.wiki_dir) if f.endswith(".md")]),
            "outputs_count": len([f for f in os.listdir(self.outputs_dir) if f.endswith(".md")]),
            "graph_nodes": self.graph.number_of_nodes(),
            "graph_edges": self.graph.number_of_edges(),
        }

    def get_stats_text(self) -> str:
        s = self.get_stats()
        return (
            "🗂️ BÓVEDA:\n"
            f"  📥 raw/: {s['raw_count']} archivos\n"
            f"  📖 wiki/: {s['wiki_count']} notas ({s['graph_edges']} enlaces)\n"
            f"  📤 outputs/: {s['outputs_count']} entregas"
        )
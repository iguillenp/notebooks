#!/usr/bin/env python3
import os
import re
from pathlib import Path
from collections import defaultdict

# ---------- Config ----------
EXCLUDE_DIRS = {
    ".git", ".ipynb_checkpoints", ".venv", "venv", "env",
    ".mypy_cache", ".pytest_cache", ".ruff_cache", ".tox",
    "node_modules", "dist", "build", ".github"
}
README_SECTION_TITLE = "Índice de notebooks (estructura)"
BLOCK_START = "<!-- NOTEBOOK TREE: START -->"
BLOCK_END = "<!-- NOTEBOOK TREE: END -->"
INDENT = "  "  # 2 espacios por nivel (compatible con GitHub)
# ----------------------------

def extract_title(ipynb_path: Path) -> str:
    """Devuelve un título legible para el notebook."""
    try:
        import nbformat
        nb = nbformat.read(ipynb_path, as_version=4)
        for cell in nb.cells:
            if cell.cell_type == "markdown":
                for line in cell.source.splitlines():
                    m = re.match(r'^\s{0,3}#{1,6}\s+(.*)', line.strip())
                    if m:
                        return m.group(1).strip()
                for line in cell.source.splitlines():
                    if line.strip():
                        return line.strip()
        return ipynb_path.stem
    except Exception:
        return ipynb_path.stem

def collect_tree(root: Path):
    """
    Construye un árbol filtrado con solo directorios que contienen notebooks (.ipynb)
    directa o indirectamente. Devuelve un dict:
      { "name": nombre_dir, "path": Path, "dirs": [...], "files": [paths .ipynb] }
    """
    def walk(dir_path: Path):
        # Filtra subdirectorios
        subdirs = [
            d for d in dir_path.iterdir()
            if d.is_dir() and d.name not in EXCLUDE_DIRS and not d.name.startswith(".")
        ]
        files = [f for f in dir_path.iterdir() if f.is_file() and f.suffix == ".ipynb" and ".ipynb_checkpoints" not in str(f)]
        # Recurse
        children = [walk(sd) for sd in subdirs]
        # Mantén solo subárboles que contienen notebooks
        children = [c for c in children if c is not None]
        if files or children:
            return {
                "name": dir_path.name,
                "path": dir_path,
                "dirs": children,
                "files": sorted(files, key=lambda p: p.name.lower())
            }
        return None

    return walk(root.resolve())

def render_markdown(tree, root: Path, level=0):
    """
    Renderiza la estructura como lista Markdown con bullet points anidados.
    Muestra directorios y, debajo, los notebooks de ese directorio.
    """
    lines = []

    # Nivel raíz: no imprimimos la carpeta raíz, solo sus hijos con level=1
    if level == 0:
        for d in sorted(tree["dirs"], key=lambda n: n["name"].lower()):
            # 🔧 ARREGLO: empieza en level=1 (antes estaba level=0)
            lines.extend(render_markdown(d, root, level=1))

        # Notebooks en la raíz (si los hubiera)
        if tree["files"]:
            lines.append(f"- (raíz)")
            for f in tree["files"]:
                rel = f.relative_to(root).as_posix()
                title = extract_title(f)
                lines.append(f"{INDENT}- [{title}]({rel})")
        return lines

    # Niveles > 0: imprime la carpeta actual y su contenido
    indent = INDENT * (level - 1)
    lines.append(f"{indent}- {tree['name']}")

    # Notebooks de esta carpeta
    for f in tree["files"]:
        rel = f.relative_to(root).as_posix()
        title = extract_title(f)
        lines.append(f"{indent}{INDENT}- [{title}]({rel})")

    # Subcarpetas
    for d in sorted(tree["dirs"], key=lambda n: n["name"].lower()):
        lines.extend(render_markdown(d, root, level=level + 1))
    return lines

def update_readme(readme_path: Path, index_md: str):
    block = f"{BLOCK_START}\n\n{index_md}\n\n{BLOCK_END}"
    if readme_path.exists():
        text = readme_path.read_text(encoding="utf-8")
        if BLOCK_START in text and BLOCK_END in text:
            new_text = re.sub(
                re.compile(re.escape(BLOCK_START) + r".*?" + re.escape(BLOCK_END), re.DOTALL),
                block,
                text,
            )
        else:
            new_text = text.rstrip() + f"\n\n## {README_SECTION_TITLE}\n\n{block}\n"
    else:
        new_text = f"# Proyecto\n\n## {README_SECTION_TITLE}\n\n{block}\n"
    readme_path.write_text(new_text, encoding="utf-8")
    print(f"Actualizado: {readme_path}")

if __name__ == "__main__":
    repo_root = Path(".").resolve()
    tree = collect_tree(repo_root)
    if not tree:
        print("No se han encontrado notebooks.")
        raise SystemExit(0)
    md_lines = render_markdown(tree, repo_root, level=0)
    index_md = "\n".join(md_lines)
    update_readme(repo_root / "README.md", index_md)
    print("Índice (árbol) generado.")

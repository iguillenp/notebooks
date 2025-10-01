#!/usr/bin/env python3
import os
import re
from pathlib import Path

# Intenta leer títulos de notebooks
def extract_title(ipynb_path):
    try:
        import nbformat
        nb = nbformat.read(ipynb_path, as_version=4)
        for cell in nb.cells:
            if cell.cell_type == "markdown":
                # Busca la primera línea tipo encabezado Markdown
                for line in cell.source.splitlines():
                    m = re.match(r'^\s{0,3}#{1,6}\s+(.*)', line.strip())
                    if m:
                        return m.group(1).strip()
                # Si no hay encabezado, usa la primera línea markdown no vacía
                for line in cell.source.splitlines():
                    if line.strip():
                        return line.strip()
        # Fallback: nombre de archivo sin extensión
        return Path(ipynb_path).stem
    except Exception:
        return Path(ipynb_path).stem

def list_notebooks(root="."):
    root = Path(root).resolve()
    notebooks = []
    EXCLUDE_DIRS = {".git", ".ipynb_checkpoints", ".venv", "venv", "env", ".mypy_cache", ".pytest_cache", ".ruff_cache", ".tox", "node_modules", "dist", "build"}
    for dirpath, dirnames, filenames in os.walk(root):
        # Filtra directorios excluidos
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS and not d.startswith(".")]
        for fn in filenames:
            if fn.endswith(".ipynb"):
                full = Path(dirpath) / fn
                # Ignora checkpoints
                if ".ipynb_checkpoints" in str(full):
                    continue
                rel = full.relative_to(root)
                notebooks.append(rel.as_posix())
    return sorted(notebooks, key=str.lower)

def build_markdown_index(nb_paths):
    lines = []
    for rel in nb_paths:
        title = extract_title(rel)
        lines.append(f"- [{title}]({rel})")
    return "\n".join(lines)

def update_readme(readme_path, index_md):
    start = "<!-- NOTEBOOK INDEX: START -->"
    end   = "<!-- NOTEBOOK INDEX: END -->"
    block = f"{start}\n\n{index_md}\n\n{end}"

    if readme_path.exists():
        text = readme_path.read_text(encoding="utf-8")
        if start in text and end in text:
            new_text = re.sub(
                re.compile(re.escape(start) + r".*?" + re.escape(end), re.DOTALL),
                block,
                text,
            )
        else:
            # Añade la sección al final
            new_text = text.rstrip() + "\n\n## Índice de notebooks\n\n" + block + "\n"
    else:
        # Crea un README desde cero
        new_text = "# Proyecto\n\n## Índice de notebooks\n\n" + block + "\n"

    readme_path.write_text(new_text, encoding="utf-8")
    print(f"Actualizado: {readme_path}")

if __name__ == "__main__":
    repo_root = Path(".").resolve()
    nbs = list_notebooks(repo_root)
    idx = build_markdown_index(nbs)
    update_readme(repo_root / "README.md", idx)

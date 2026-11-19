"""Resolve the native build artifact without assuming its suffix from the host OS."""
from pathlib import Path
import re


def module_version(root: Path) -> str:
    declaration = (root/'moon.mod').read_text(encoding='utf-8')
    match = re.search(r'^version\s*=\s*"([^"]+)"', declaration, re.MULTILINE)
    if not match:
        raise ValueError('Missing version declaration in moon.mod')
    return match.group(1)


def find_native_executable(root: Path) -> Path:
    directory = root / '_build/native/debug/build/cmd/edittrace'
    candidates = [directory / 'edittrace.exe', directory / 'edittrace']
    matches = [p for p in candidates if p.is_file()]
    if len(matches) == 1:
        return matches[0]
    available = sorted(p.name for p in directory.iterdir())[:20] if directory.is_dir() else []
    raise RuntimeError(
        f'Expected exactly one native EditTrace executable; found {len(matches)}. '
        f'Searched {directory}; available files: {available}'
    )

"""Парсер файлов сборки: CMakeLists.txt и *.pro (qmake).

Извлекает имя проекта, версию, цели (targets), модули Qt и внешние
зависимости — эти сведения попадают в разделы документации.
"""

from __future__ import annotations

import re
from pathlib import Path

from .model import BuildInfo

_QT_MODULES = {
    "Core", "Gui", "Widgets", "Network", "Sql", "Xml", "XmlPatterns",
    "Multimedia", "MultimediaWidgets", "Qml", "Quick", "QuickWidgets",
    "Charts", "DataVisualization", "WebEngine", "WebEngineWidgets",
    "WebChannel", "Test", "Concurrent", "DBus", "OpenGL", "OpenGLWidgets",
    "PrintSupport", "Svg", "SvgWidgets", "Positioning", "Location", "Bluetooth",
    "Nfc", "Sensors", "SerialPort", "WebSockets", "Help", "Designer",
    "UiTools", "Gamepad", "RemoteObjects", "Scxml", "StateMachine", "TextToSpeech",
}

# --- CMake ---
_PROJECT_RE = re.compile(
    r"^\s*project\s*\(\s*([\w-]+)(?:\s+VERSION\s+([0-9]+\.[0-9]+(?:\.[0-9]+)?))?", re.I | re.M)
_TARGET_RE = re.compile(
    r"^\s*(?:qt_)?(?:add_executable|add_library)\s*\(\s*([\w-]+)", re.I | re.M)
_FIND_PKG_RE = re.compile(
    r"^\s*find_package\s*\(\s*([\w]+)(.*?)\)", re.I | re.M)
_PKG_RE = re.compile(r"^\s*([A-Za-z][\w]*(?:::[A-Za-z][\w]*)?)\s*::?\s*[\w]+", re.M)

# --- qmake (.pro) ---
_PRO_TARGET_RE = re.compile(r"^\s*TARGET\s*=\s*([\w-]+)", re.I | re.M)
_PRO_QT_RE = re.compile(r"^\s*QT\s*\+=\s*(.+)", re.I | re.M)
_PRO_LIBS_RE = re.compile(r"^\s*(?:LIBS|CONFIG)\s*\+=?\s*(.+)", re.I | re.M)


def _cmake_qt_modules(text: str) -> list[str]:
    out: list[str] = []
    for m in _FIND_PKG_RE.finditer(text):
        pkg = m.group(1)
        rest = m.group(2) or ""
        comp = re.search(r"COMPONENTS\s+([\w\s]+)", rest, re.I)
        if pkg.lower().startswith("qt") and comp:
            for c in comp.group(1).split():
                if c in _QT_MODULES and c not in out:
                    out.append(c)
    return out


def _qmake_qt_modules(text: str) -> list[str]:
    out: list[str] = []
    for m in _PRO_QT_RE.finditer(text):
        for mod in m.group(1).split():
            if mod in _QT_MODULES or mod.capitalize() in _QT_MODULES:
                if mod not in out:
                    out.append(mod)
    return out


def parse_build(src_dir: str | Path) -> BuildInfo:
    """Ищет CMakeLists.txt и *.pro в корне проекта."""
    src_dir = Path(src_dir)
    info = BuildInfo()

    cmake = src_dir / "CMakeLists.txt"
    if cmake.exists():
        text = cmake.read_text(encoding="utf-8", errors="ignore")
        info.kind = "cmake"
        m = _PROJECT_RE.search(text)
        if m:
            info.name = m.group(1)
            info.version = m.group(2) or ""
        info.targets = [t for t in _TARGET_RE.findall(text)]
        info.qt_modules = _cmake_qt_modules(text)
        info.dependencies = sorted({d for d in _PKG_RE.findall(text)
                                    if not d.lower().startswith("qt")})
        return info

    pro_files = sorted(src_dir.glob("*.pro"))
    if pro_files:
        text = "\n".join(p.read_text(encoding="utf-8", errors="ignore")
                         for p in pro_files)
        info.kind = "qmake"
        m = _PRO_TARGET_RE.search(text)
        if m:
            info.name = m.group(1)
        info.qt_modules = _qmake_qt_modules(text)
        return info

    return info

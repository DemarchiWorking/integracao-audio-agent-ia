"""
Orquestrador de Áudio — DataDev Demarchi Lab
Configuração centralizada via variáveis de ambiente ou defaults.
"""
import os
from pathlib import Path

# Garante que FFmpeg instalado via winget está no PATH antes de qualquer import de Whisper
_WINGET_LINKS = str(Path.home() / "AppData" / "Local" / "Microsoft" / "WinGet" / "Links")
if _WINGET_LINKS not in os.environ.get("PATH", ""):
    os.environ["PATH"] = _WINGET_LINKS + os.pathsep + os.environ.get("PATH", "")

BASE_DIR = Path(__file__).parent
INBOX_DIR = Path(os.getenv(
    "INBOX_DIR",
    str(BASE_DIR.parent / "inbox_tarefas")
))

PORT: int = int(os.getenv("ORCHESTRATOR_PORT", "8765"))
HOST: str = os.getenv("ORCHESTRATOR_HOST", "0.0.0.0")

# "mock" para testes sem FFmpeg | "whisper" para produção real
TRANSCRIBER_BACKEND: str = os.getenv("TRANSCRIBER_BACKEND", "whisper")
WHISPER_MODEL: str = os.getenv("WHISPER_MODEL", "base")
WHISPER_LANGUAGE: str = os.getenv("WHISPER_LANGUAGE", "pt")

AUDIO_EXTENSIONS: set = {".m4a", ".mp3", ".wav", ".ogg", ".flac", ".mp4", ".webm", ".aac"}

VERSION: str = "1.0.0"

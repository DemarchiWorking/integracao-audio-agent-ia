"""
inbox_watcher.py — Auto-executor de pacotes v2.1
DataDev Demarchi Lab

Monitora inbox_tarefas/ em busca de novos pacotes.
Quando detecta transcricao.md nova, dispara o processador automaticamente.

Motor de processamento (auto-deteccao, sem configuracao manual):
  1. ANTHROPIC_API_KEY disponivel  -> processar_com_claude.py      (API direta)
  2. Claude Code CLI autenticado   -> processar_com_claude_code.py (plano Pro)
  3. Nenhum disponivel             -> modo MANUAL (so gera pacote)
"""
import logging
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [INBOX] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("inbox_watcher")

INBOX_DIR        = Path(__file__).parent.parent / "inbox_tarefas"
PROCESSOR_API    = Path(__file__).parent / "processar_com_claude.py"
PROCESSOR_CODE   = Path(__file__).parent / "processar_com_claude_code.py"
SETTLE_SECS      = 3   # aguarda arquivo terminar de ser escrito


# ---------------------------------------------------------------------------
# Deteccao de motor disponivel
# ---------------------------------------------------------------------------

def detect_mode() -> tuple:
    """
    Detecta qual motor de processamento esta disponivel.
    Retorna (modo, processor_path, descricao).
    Modos: 'api' | 'claude_code' | 'manual'
    """
    # Modo 1: API key configurada
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key and len(api_key) > 20 and PROCESSOR_API.exists():
        return ("api", PROCESSOR_API, "API Anthropic (ANTHROPIC_API_KEY)")

    # Modo 2: Claude Code CLI disponivel e autenticado
    claude_cmd = shutil.which("claude") or shutil.which("claude.cmd")
    if not claude_cmd:
        # Tentar caminhos comuns no Windows
        npm_path = Path(os.environ.get("APPDATA", "")) / "npm" / "claude.cmd"
        if npm_path.exists():
            claude_cmd = str(npm_path)

    if claude_cmd and PROCESSOR_CODE.exists():
        try:
            r = subprocess.run(
                [claude_cmd, "--version"],
                capture_output=True, text=True, timeout=8
            )
            if r.returncode == 0:
                return ("claude_code", PROCESSOR_CODE, f"Claude Code CLI Pro ({claude_cmd})")
        except (subprocess.TimeoutExpired, OSError):
            pass

    # Modo 3: Manual
    return ("manual", None, "MANUAL (nenhum motor disponivel)")


# ---------------------------------------------------------------------------
# Handler do watchdog
# ---------------------------------------------------------------------------

class InboxHandler(FileSystemEventHandler):

    def __init__(self, mode: str, processor: Path | None, mode_desc: str):
        self._mode      = mode
        self._processor = processor
        self._mode_desc = mode_desc
        self._seen: set = set()

    def on_created(self, event):
        if event.is_directory:
            return
        path = Path(event.src_path)
        if path.name == "transcricao.md":
            packet_dir = path.parent
            key = str(packet_dir)
            if key not in self._seen:
                self._seen.add(key)
                log.info(f"Novo pacote detectado: {packet_dir.name}")
                time.sleep(SETTLE_SECS)
                self._dispatch(packet_dir)

    def _dispatch(self, packet_dir: Path):
        if self._mode == "manual":
            log.warning("Nenhum motor configurado — pacote aguardando processamento manual")
            log.warning(f"  Claude Code: python processar_com_claude_code.py {packet_dir}")
            log.warning(f"  API:         python processar_com_claude.py {packet_dir}")
            return

        log.info(f"Motor: {self._mode_desc}")
        log.info(f"Disparando processador para: {packet_dir.name}")

        try:
            result = subprocess.run(
                [sys.executable, str(self._processor), str(packet_dir)],
                timeout=180,
                encoding="utf-8",
                capture_output=False,
            )
            if result.returncode == 0:
                log.info(f"Pacote processado com sucesso: {packet_dir.name}")
            else:
                log.error(f"Processador retornou exit={result.returncode} para {packet_dir.name}")
        except subprocess.TimeoutExpired:
            log.error(f"Timeout 180s ao processar {packet_dir.name}")
        except Exception as e:
            log.error(f"Erro ao disparar processador: {e}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    INBOX_DIR.mkdir(parents=True, exist_ok=True)

    mode, processor, mode_desc = detect_mode()

    if mode == "api":
        log.info(f"Motor selecionado: {mode_desc}")
    elif mode == "claude_code":
        log.info(f"Motor selecionado: {mode_desc}")
    else:
        log.warning("Nenhum motor detectado — rodando em modo MANUAL")
        log.warning("  Para ativar modo API:          configure ANTHROPIC_API_KEY no .env")
        log.warning("  Para ativar modo Claude Code:  instale em https://claude.ai/download")

    log.info(f"Monitorando: {INBOX_DIR}")

    handler  = InboxHandler(mode, processor, mode_desc)
    observer = Observer()
    observer.schedule(handler, str(INBOX_DIR), recursive=True)
    observer.start()
    log.info("Inbox watcher pronto. Aguardando pacotes...")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        log.info("Encerrado.")
    observer.join()


if __name__ == "__main__":
    main()

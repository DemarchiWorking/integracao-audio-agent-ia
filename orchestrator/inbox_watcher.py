"""
inbox_watcher.py — Auto-executor de pacotes
DataDev Demarchi Lab v2.0

Monitora inbox_tarefas/ em busca de novos pacotes.
Quando detecta transcricao.md nova, dispara processar_com_claude.py automaticamente.

Requer ANTHROPIC_API_KEY configurada. Sem a key, loga aviso e aguarda.
"""
import logging
import os
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

INBOX_DIR   = Path(__file__).parent.parent / "inbox_tarefas"
PROCESSOR   = Path(__file__).parent / "processar_com_claude.py"
SETTLE_SECS = 3   # aguarda arquivo terminar de ser escrito


class InboxHandler(FileSystemEventHandler):

    def __init__(self):
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
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            log.warning("ANTHROPIC_API_KEY nao configurada — pacote aguardando processamento manual")
            log.warning(f"  Execute: python processar_com_claude.py {packet_dir}")
            return

        log.info(f"Disparando Claude para: {packet_dir.name}")
        try:
            result = subprocess.run(
                [sys.executable, str(PROCESSOR), str(packet_dir)],
                timeout=120,
                encoding="utf-8",
                capture_output=False,   # deixa stdout/stderr ir para o log do processo
            )
            if result.returncode == 0:
                log.info(f"Pacote processado com sucesso: {packet_dir.name}")
            else:
                log.error(f"Claude retornou exit={result.returncode} para {packet_dir.name}")
        except subprocess.TimeoutExpired:
            log.error(f"Timeout 120s ao processar {packet_dir.name}")
        except Exception as e:
            log.error(f"Erro ao disparar Claude: {e}")


def main():
    INBOX_DIR.mkdir(parents=True, exist_ok=True)

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key:
        log.info("ANTHROPIC_API_KEY: configurada — modo AUTO-EXECUTE ativado")
    else:
        log.warning("ANTHROPIC_API_KEY: NAO configurada — modo MANUAL (so gera pacote, nao processa)")

    log.info(f"Monitorando: {INBOX_DIR}")

    handler  = InboxHandler()
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

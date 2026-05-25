"""
watcher.py — Ponte KDE Connect → Orquestrador
Monitora a pasta de recebimento do KDE Connect e envia arquivos de áudio
automaticamente para o endpoint POST /audio do orquestrador.

Fluxo:
  S10 FE envia arquivo via KDE Connect
    → arquivo pousa em WATCH_DIR
    → watcher detecta → POST /audio → localhost:8765
    → Whisper transcreve → pacote gerado em inbox_tarefas/
"""
import logging
import os
import sys
import time
from pathlib import Path

import requests
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

import config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [WATCHER] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("watcher")

# Pasta onde o KDE Connect deposita arquivos recebidos (padrão Windows)
KDE_CONNECT_DIR = Path(os.getenv(
    "KDE_CONNECT_DIR",
    str(Path.home() / "Documents" / "KDE Connect"),
))

ORCHESTRATOR_URL = f"http://localhost:{config.PORT}"
# Aguarda este tempo após detecção para garantir que o arquivo foi completamente escrito
WRITE_SETTLE_SECS = 2


class AudioFileHandler(FileSystemEventHandler):

    def __init__(self):
        self._processing: set = set()

    def on_created(self, event):
        if event.is_directory:
            return
        path = Path(event.src_path)
        if path.suffix.lower() in config.AUDIO_EXTENSIONS:
            self._handle(path)

    def on_moved(self, event):
        """KDE Connect às vezes move o arquivo para o destino final."""
        if event.is_directory:
            return
        path = Path(event.dest_path)
        if path.suffix.lower() in config.AUDIO_EXTENSIONS:
            self._handle(path)

    def _handle(self, path: Path):
        key = str(path)
        if key in self._processing:
            return
        self._processing.add(key)
        logger.info(f"Novo arquivo detectado: {path.name}")

        time.sleep(WRITE_SETTLE_SECS)  # aguarda escrita completa

        try:
            self._post_to_orchestrator(path)
        except Exception as exc:
            logger.error(f"Erro ao enviar {path.name}: {exc}")
        finally:
            self._processing.discard(key)

    def _post_to_orchestrator(self, path: Path):
        logger.info(f"Enviando para orquestrador: {path.name}")
        with open(path, "rb") as f:
            resp = requests.post(
                f"{ORCHESTRATOR_URL}/audio",
                files={"file": (path.name, f, "audio/octet-stream")},
                data={"source": "kde_connect"},
                timeout=10,
            )
        if resp.status_code == 200:
            logger.info(f"Enfileirado com sucesso: {resp.json().get('message')}")
        else:
            logger.error(f"Orquestrador retornou {resp.status_code}: {resp.text[:200]}")


def main():
    watch_dir = KDE_CONNECT_DIR

    # Cria a pasta se não existir (KDE Connect precisa que ela exista)
    watch_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Iniciando watcher em: {watch_dir}")
    logger.info(f"Orquestrador: {ORCHESTRATOR_URL}")
    logger.info(f"Extensões monitoradas: {sorted(config.AUDIO_EXTENSIONS)}")

    # Verifica se orquestrador está online
    try:
        resp = requests.get(f"{ORCHESTRATOR_URL}/health", timeout=3)
        if resp.status_code == 200:
            logger.info("Orquestrador online — watcher pronto.")
        else:
            logger.warning("Orquestrador respondeu com erro — continuando mesmo assim.")
    except requests.ConnectionError:
        logger.warning("Orquestrador offline. Watcher iniciará mas processamento falhará até o servidor subir.")

    handler = AudioFileHandler()
    observer = Observer()
    observer.schedule(handler, str(watch_dir), recursive=False)
    observer.start()

    logger.info("Aguardando arquivos do S10 FE via KDE Connect...")
    logger.info("Ctrl+C para parar.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        logger.info("Watcher encerrado.")
    observer.join()


if __name__ == "__main__":
    main()

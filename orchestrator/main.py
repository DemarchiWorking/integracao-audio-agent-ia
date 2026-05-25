"""
Orquestrador de Áudio — DataDev Demarchi Lab
FastAPI async listener: recebe áudio/texto do Samsung S10 FE e dispara pipeline.

Endpoints:
  GET  /health       — health check
  GET  /status       — status detalhado
  POST /audio        — recebe arquivo de áudio (multipart)
  POST /text         — recebe texto já transcrito (útil para testes e S Pen)
"""
import asyncio
import logging
import os
import tempfile
from datetime import datetime
from pathlib import Path

import uvicorn
from fastapi import BackgroundTasks, FastAPI, File, Form, UploadFile
from fastapi.responses import JSONResponse

import config
from packet_generator import PacketGenerator
from transcriber import get_transcriber

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("orchestrator")

app = FastAPI(
    title="Audio Orchestrator",
    description="DataDev Demarchi Lab — S10 FE ↔ Windows 10",
    version=config.VERSION,
)

_transcriber = get_transcriber()
_packet_gen = PacketGenerator()
_stats = {"received": 0, "processed": 0, "errors": 0, "started_at": datetime.now().isoformat()}


# ── Health / Status ─────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "version": config.VERSION, "ts": datetime.now().isoformat()}


@app.get("/status")
async def status():
    return {
        "status": "running",
        "version": config.VERSION,
        "backend_stt": config.TRANSCRIBER_BACKEND,
        "inbox_dir": str(config.INBOX_DIR),
        "stats": _stats,
    }


# ── Receber Áudio ────────────────────────────────────────────────────────────

@app.post("/audio")
async def receive_audio(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    source: str = Form(default="s10fe"),
):
    """Recebe arquivo de áudio do S10 FE e enfileira para transcrição + geração de pacote."""
    _stats["received"] += 1

    suffix = Path(file.filename).suffix if file.filename else ".wav"
    if suffix.lower() not in config.AUDIO_EXTENSIONS:
        return JSONResponse(status_code=400, content={"error": f"Extensão não suportada: {suffix}"})

    content = await file.read()

    # Salvar em temp antes de passar para thread de transcrição
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(content)
    tmp.close()

    background_tasks.add_task(_audio_pipeline, tmp.name, source)

    return {
        "status": "queued",
        "message": "Áudio recebido — transcrição e geração de pacote em andamento",
        "file": file.filename,
        "size_bytes": len(content),
    }


# ── Receber Texto (S Pen / testes) ───────────────────────────────────────────

@app.post("/text")
async def receive_text(
    background_tasks: BackgroundTasks,
    text: str = Form(...),
    source: str = Form(default="manual"),
):
    """Recebe texto já transcrito (S Pen exportado, clipboard, testes) e gera pacote."""
    _stats["received"] += 1

    if not text.strip():
        return JSONResponse(status_code=400, content={"error": "Texto vazio."})

    background_tasks.add_task(_text_pipeline, text.strip(), source)

    return {
        "status": "queued",
        "message": "Texto recebido — geração de pacote em andamento",
        "preview": text[:80] + ("..." if len(text) > 80 else ""),
    }


# ── Pipelines (background tasks) ─────────────────────────────────────────────

async def _audio_pipeline(audio_path: str, source: str):
    try:
        logger.info(f"Pipeline áudio iniciado: {Path(audio_path).name}")
        transcription = await asyncio.to_thread(_transcriber.transcribe, audio_path)
        await _text_pipeline(transcription, source)
    except Exception as exc:
        _stats["errors"] += 1
        logger.error(f"Erro no pipeline de áudio: {exc}", exc_info=True)
    finally:
        try:
            os.unlink(audio_path)
        except OSError:
            pass


async def _text_pipeline(text: str, source: str):
    try:
        logger.info(f"Pipeline texto: {len(text)} chars | origem={source}")
        packet_path = await asyncio.to_thread(_packet_gen.generate, text, source)
        _stats["processed"] += 1
        logger.info(f"✅ Pacote pronto: {packet_path.name}")
    except Exception as exc:
        _stats["errors"] += 1
        logger.error(f"Erro no pipeline de texto: {exc}", exc_info=True)


# ── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    logger.info(f"Iniciando Orquestrador v{config.VERSION} em {config.HOST}:{config.PORT}")
    logger.info(f"Inbox: {config.INBOX_DIR}")
    logger.info(f"STT backend: {config.TRANSCRIBER_BACKEND}")
    uvicorn.run(app, host=config.HOST, port=config.PORT, log_level="info")

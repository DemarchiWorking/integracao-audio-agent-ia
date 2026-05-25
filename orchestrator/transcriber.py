"""
Camada de transcrição STT — isolada para fácil troca de backend.

Passo 1: MockTranscriber (sem dependências extras)
Passo 2: WhisperTranscriber (openai-whisper + ffmpeg)
"""
import logging
from pathlib import Path
import config

logger = logging.getLogger(__name__)


class MockTranscriber:
    """Simula transcrição para validar o pipeline sem Whisper instalado."""

    def transcribe(self, audio_path: str) -> str:
        name = Path(audio_path).name
        logger.info(f"[MOCK] Transcrevendo: {name}")
        return (
            f"[MOCK — Passo 1] Arquivo recebido: {name}. "
            "Precisamos implementar autenticação JWT no NeuroLead com urgência. "
            "Os endpoints estão completamente abertos. "
            "Primeira prioridade é criar o middleware de autenticação. "
            "Segunda prioridade é escrever os testes de integração com Postman."
        )


class WhisperTranscriber:
    """Transcrição 100% offline via OpenAI Whisper local."""

    def __init__(self):
        import whisper  # importação lazy — só no Passo 2
        logger.info(f"Carregando Whisper modelo='{config.WHISPER_MODEL}'...")
        self.model = whisper.load_model(config.WHISPER_MODEL)
        logger.info("Whisper pronto.")

    def transcribe(self, audio_path: str) -> str:
        logger.info(f"[WHISPER] Transcrevendo: {Path(audio_path).name}")
        result = self.model.transcribe(
            audio_path,
            language=config.WHISPER_LANGUAGE
        )
        text = result["text"].strip()
        logger.info(f"[WHISPER] {len(text)} caracteres transcritos.")
        return text


def get_transcriber():
    backend = config.TRANSCRIBER_BACKEND.lower()
    if backend == "whisper":
        try:
            return WhisperTranscriber()
        except ImportError:
            logger.warning("openai-whisper não instalado. Fallback para Mock.")
            return MockTranscriber()
    logger.info("Backend de transcrição: MockTranscriber (Passo 1)")
    return MockTranscriber()

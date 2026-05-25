"""
packet_generator.py — Gera pacote minimo por audio recebido.
Claude faz o breakdown real; aqui so salvamos a transcricao limpa.

inbox_tarefas/YYYY-MM-DD_HH-MM-SS/
    transcricao.md   <- texto exato do audio + metadados
    processar_agora.ps1 <- atalho para processamento manual
"""
import logging
from pathlib import Path
from datetime import datetime
import config

logger = logging.getLogger(__name__)


class PacketGenerator:

    def __init__(self):
        self.inbox_dir = config.INBOX_DIR
        self.inbox_dir.mkdir(parents=True, exist_ok=True)

    def generate(self, transcription: str, source: str = "s10fe") -> Path:
        ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        packet_dir = self.inbox_dir / ts
        packet_dir.mkdir(parents=True, exist_ok=True)

        (packet_dir / "transcricao.md").write_text(
            self._transcricao(transcription, ts, source), encoding="utf-8"
        )
        self._processar_script(packet_dir, ts)

        logger.info(f"Pacote gerado: {packet_dir}")
        return packet_dir

    def _transcricao(self, text: str, ts: str, source: str) -> str:
        words = len(text.split())
        return f"""# Transcricao
timestamp: {ts}
origem: {source}
palavras: {words}
modelo_stt: whisper-{config.WHISPER_MODEL}

---

{text.strip()}
"""

    def _processar_script(self, packet_dir: Path, ts: str) -> None:
        py_script = (Path(__file__).parent / "processar_com_claude.py").resolve()
        script = f"""# processar_agora.ps1 — Pacote {ts}
# Execucao manual. O inbox_watcher.py dispara automaticamente se ANTHROPIC_API_KEY estiver configurada.

$dir = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $env:ANTHROPIC_API_KEY) {{
    Write-Host "ERRO: configure ANTHROPIC_API_KEY primeiro" -ForegroundColor Red
    exit 1
}}
python "{py_script}" "$dir"
"""
        (packet_dir / "processar_agora.ps1").write_text(script, encoding="utf-8")

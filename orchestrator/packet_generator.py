"""
Gerador de Pacotes Padronizados — Orquestrador v1.0.0

Para cada áudio processado, cria:
  inbox_tarefas/YYYY-MM-DD_HH-MM-SS/
    ├── transcricao.md
    ├── roteiro.md
    ├── descricao_tarefa.md
    ├── futuro_processamento_1.md
    ├── futuro_processamento_2.md
    └── processar_agora.ps1
"""
import re
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
        (packet_dir / "roteiro.md").write_text(
            self._roteiro(transcription, ts), encoding="utf-8"
        )
        (packet_dir / "descricao_tarefa.md").write_text(
            self._descricao(transcription, ts, source), encoding="utf-8"
        )
        (packet_dir / "futuro_processamento_1.md").write_text(
            self._futuro_1(ts), encoding="utf-8"
        )
        (packet_dir / "futuro_processamento_2.md").write_text(
            self._futuro_2(ts), encoding="utf-8"
        )
        self._processar_script(packet_dir, ts)

        logger.info(f"Pacote gerado: {packet_dir}")
        return packet_dir

    # ── builders ────────────────────────────────────────────────────────────

    def _transcricao(self, text: str, ts: str, source: str) -> str:
        return f"""# Transcrição Bruta
> **Timestamp:** {ts}
> **Origem:** {source}
> **Orquestrador:** v{config.VERSION}
> **Backend STT:** {config.TRANSCRIBER_BACKEND}

---

{text}
"""

    def _roteiro(self, text: str, ts: str) -> str:
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
        steps = "\n".join(f"{i+1}. {s}" for i, s in enumerate(sentences))
        return f"""# Roteiro / Script de Ação
> **Timestamp:** {ts}
> **Status:** Formatação automática V1 — enriquecer com `processar_agora.ps1`

---

## Passos Identificados

{steps if steps else "*(sem sentenças detectadas — verificar transcrição)*"}

---

> *Execute `processar_agora.ps1` para geração detalhada pelo Claude Code.*
"""

    def _descricao(self, text: str, ts: str, source: str) -> str:
        preview = text[:250].rstrip() + ("..." if len(text) > 250 else "")
        words = len(text.split())
        return f"""# Descrição da Tarefa
> **Timestamp:** {ts}
> **Status:** 🔵 Aguardando processamento Claude Code

---

## Objetivo Capturado

{preview}

---

## Metadados

| Campo            | Valor                      |
|------------------|---------------------------|
| Timestamp        | {ts}                       |
| Origem           | {source}                   |
| Palavras         | {words}                    |
| Processamento IA | Pendente — `processar_agora.ps1` |

---

> *Execute `processar_agora.ps1` para análise completa e plano de ação.*
"""

    def _futuro_1(self, ts: str) -> str:
        return f"""# Futuro Processamento 1 — Log de Agentes
> **Reservado para:** outputs e logs de agentes autônomos
> **Timestamp:** {ts}
> **Status:** VAZIO (V1)

---

<!--
  V2 — WATCHDOG HOOK:
  O watcher de diretório monitora este arquivo.
  Quando conteúdo for detectado, dispara pipeline de agentes automaticamente.
  Ver ROADMAP_INCREMENTAL.md para especificação completa.
-->

## Log de Execução

*(em branco — V2 populará via watcher)*

## Agentes Registrados

*(nenhum ainda)*
"""

    def _futuro_2(self, ts: str) -> str:
        return f"""# Futuro Processamento 2 — Injeção de Contexto
> **Reservado para:** contexto externo injetado por outros agentes
> **Timestamp:** {ts}
> **Status:** VAZIO (V1)

---

<!--
  V2 — CONTEXT INJECTION:
  Este arquivo recebe contexto de agentes externos (NeuroLead, task-board, etc.).
  Quando preenchido, o watcher dispara reprocessamento automático com contexto enriquecido.
  Ver ROADMAP_INCREMENTAL.md para especificação completa.
-->

## Contexto Injetado

*(em branco — aguardando V2)*

## Fontes de Contexto Planejadas (V2)

- [ ] `task-board/backlog/` — tarefas ativas do DataDev Lab
- [ ] NeuroLead — leads quentes do dia
- [ ] Calendário / reuniões agendadas
- [ ] Últimos 3 pacotes processados (histórico de contexto)
"""

    def _processar_script(self, packet_dir: Path, ts: str) -> None:
        # Caminho absoluto do processar_com_claude.py (sempre ao lado deste arquivo)
        py_script = (Path(__file__).parent / "processar_com_claude.py").resolve()

        script = f"""# processar_agora.ps1
# Orquestrador v{config.VERSION} — Pacote {ts}
# Dispara Claude API com contexto do pacote de audio capturado.
# Uso: .\\processar_agora.ps1
#
# Pre-requisito: ANTHROPIC_API_KEY configurada
#   [Environment]::SetEnvironmentVariable("ANTHROPIC_API_KEY","sk-ant-...","User")

$ErrorActionPreference = "Stop"
$pacote = "{ts}"
$dir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "  DataDev Lab -- Processar Agora" -ForegroundColor Cyan
Write-Host "  Pacote: $pacote" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# Verificar ANTHROPIC_API_KEY
if (-not $env:ANTHROPIC_API_KEY) {{
    Write-Host "ERRO: ANTHROPIC_API_KEY nao configurada." -ForegroundColor Red
    Write-Host "Execute: [Environment]::SetEnvironmentVariable('ANTHROPIC_API_KEY','sk-ant-...','User')" -ForegroundColor Yellow
    exit 1
}}

Write-Host "Enviando pacote ao Claude API..." -ForegroundColor Yellow
python "{py_script}" "$dir"
Write-Host ""
Write-Host "Processamento concluido. Verifique resposta_claude.md nesta pasta." -ForegroundColor Green
"""
        (packet_dir / "processar_agora.ps1").write_text(script, encoding="utf-8")

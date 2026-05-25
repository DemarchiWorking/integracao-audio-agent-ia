# ROADMAP INCREMENTAL — Orquestrador de Áudio
> DataDev Demarchi Lab | Samsung S10 FE ↔ Windows 10
> **Versão do doc:** 1.0.0 | **Data:** 2026-05-24

---

## V1 — Base Funcional (ATUAL) ✅

**Objetivo:** Listener HTTP confiável + geração de pacote padronizado.

| Componente | Status | Descrição |
|---|---|---|
| FastAPI async listener | ✅ | Endpoints `/audio`, `/text`, `/health`, `/status` |
| MockTranscriber | ✅ | Valida pipeline sem dependência de Whisper |
| PacketGenerator | ✅ | Gera 5 arquivos `.md` + `processar_agora.ps1` por pacote |
| Scripts start/stop/restart | ✅ | Controle imediato do serviço |
| test_trigger.py | ✅ | 6 testes automatizados simulando S10 FE |

**Limitações V1:**
- Transcrição é mock (sem Whisper real)
- `roteiro.md` é gerado por regex simples (não LLM)
- `futuro_processamento_*.md` ficam em branco (aguardando V2)
- Sem daemonização permanente (só background manual via `start.ps1`)

---

## V2 — Whisper + Auto-Processamento com Watchers

**Objetivo:** Transcrição real e execução automática quando arquivos forem preenchidos.

### V2.1 — Motor Whisper Real
```python
# Em config.py: mudar para
TRANSCRIBER_BACKEND = "whisper"

# Instalar previamente:
# winget install Gyan.FFmpeg
# pip install openai-whisper
```

### V2.2 — Watcher de Diretório (futuro_processamento_*.md)
```python
# watcher.py (a criar no Passo 3)
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class PacketWatcher(FileSystemEventHandler):
    def on_modified(self, event):
        path = Path(event.src_path)
        # Quando futuro_processamento_1.md receber conteúdo:
        if path.name == "futuro_processamento_1.md" and path.stat().st_size > 100:
            trigger_agent_pipeline(path.parent)

        # Quando futuro_processamento_2.md receber contexto externo:
        if path.name == "futuro_processamento_2.md" and path.stat().st_size > 100:
            trigger_reprocessing_with_context(path.parent)
```

**Comportamento V2.2:**
1. `watcher.py` monitora `inbox_tarefas/` continuamente
2. Qualquer agente externo escreve em `futuro_processamento_1.md` ou `futuro_processamento_2.md`
3. Watcher detecta mudança → chama Claude Code CLI automaticamente
4. Claude Code lê todos os arquivos do pacote + o novo contexto e gera output enriquecido

### V2.3 — Injeção de Contexto Automática
```python
# context_injector.py (a criar)
# Preenche futuro_processamento_2.md antes do Claude Code processar:
def inject_context(packet_dir: Path):
    context = {
        "tasks_backlog": read_task_board(),        # DataDev Lab backlog
        "neurolead_leads": get_hot_leads(),        # NeuroLead leads quentes
        "recent_packets": get_last_3_packets(),    # histórico
    }
    (packet_dir / "futuro_processamento_2.md").write_text(
        format_context(context)
    )
```

---

## V3 — Full-Cycle Autônomo

**Objetivo:** O sistema cria, processa e entrega tarefas sem intervenção humana.

| Feature | Descrição |
|---|---|
| Classificador de conteúdo | ML local ou Claude API: detecta tipo (técnico/negócio/reunião) |
| Agentes especializados | Persona diferente por tipo de conteúdo |
| Auto-criação de tasks | Pacote processado → task criada no `task-board/backlog/` |
| KDE Connect reply | Resultado enviado de volta ao S10 FE como notificação |
| Daemonização NSSM | Serviço Windows real (auto-start no boot, sem janela aberta) |

### Daemonização NSSM (V3)
```powershell
# Instalar NSSM
winget install nssm

# Registrar como serviço Windows
nssm install AudioOrchestrator python "C:\...\main.py"
nssm set AudioOrchestrator AppDirectory "C:\...\orchestrator"
nssm set AudioOrchestrator Start SERVICE_AUTO_START
nssm start AudioOrchestrador
```

---

## Marcos de Validação por Versão

| Marco | Critério de Aceite |
|---|---|
| V1 completo | test_trigger.py: 6/6 testes verde |
| V2.1 completo | Áudio `.m4a` real do S10 FE → transcrição correta |
| V2.2 completo | Escrever em `futuro_processamento_1.md` → Claude Code executa auto |
| V2.3 completo | Pacote gerado já inclui contexto do task-board e NeuroLead |
| V3 completo | Falar no S10 FE → tarefa criada no board + notificação de volta |

---

## Decisões de Arquitetura

| Decisão | Escolha | Justificativa |
|---|---|---|
| HTTP vs WebSocket | HTTP (REST) | Mais simples, suficiente para payloads de áudio sem streaming |
| Transcriber | Whisper local | Privacidade + sem custo de API + funciona offline |
| Async | FastAPI + BackgroundTasks | Thread principal não bloqueia ao receber áudio |
| Packet format | `.md` files | Legível por humanos + nativos no Claude Code + git-friendly |
| Resiliência V1 | `start.ps1` manual | NSSM fica para V3 (evitar over-engineering na V1) |

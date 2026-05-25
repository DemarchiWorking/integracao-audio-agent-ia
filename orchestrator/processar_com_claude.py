"""
processar_com_claude.py
DataDev Demarchi Lab — Audio Orchestrator v2.0

Le transcricao.md do pacote, classifica o tipo de demanda,
quebra em tarefas priorizadas (P1/P2/P3) e executa o que for possivel
diretamente no Windows via tool use.

Uso:
  python processar_com_claude.py <pasta_do_pacote>
  python processar_com_claude.py          # pega o mais recente

Saidas geradas na pasta do pacote:
  tarefas_priorizadas.md   breakdown P1/P2/P3 + criterios de aceite
  execucao.md              log do que foi executado + resultados
"""
import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime

try:
    import anthropic
except ImportError:
    print("ERRO: pip install anthropic")
    sys.exit(1)

# ---------------------------------------------------------------------------
MODEL      = "claude-sonnet-4-5"
MAX_TOKENS = 4096

SYSTEM_PROMPT = """Voce e um Engenheiro de Sistemas Senior no DataDev Lab de Antonio Demarchi.

PERFIL DO USUARIO:
- Antonio Demarchi — Backend Dev II na nstech (fintech missao critica, pagamento de fretes PEF/ANTT)
- Stack real: Go (hexagonal, goroutines), Java, React/Next.js, Python, Docker, Kubernetes, Terraform, AWS
- Nivel: senior — responda como peer tecnico, sem didatismo
- Contexto: RJ, CLT R$4.9k, projetos ativos: NeuroLead (Go+AWS), Challenge2 (FIAP EKS), DataDev Lab

WORKFLOW:
Voce recebe uma transcricao de audio do Samsung S10 FE via KDE Connect.
O audio foi transcrito offline com Whisper PT-BR — pode ter erros fonéticos.

SUA MISSAO:

1. INTERPRETAR corretamente mesmo com erros de transcricao
   (ex: "Neurolid" = NeuroLead, "Midleuari" = Middleware, "Chav SSH" = Chave SSH)

2. CLASSIFICAR o tipo:
   AUTOMACAO  — tarefa executavel no Windows agora (arquivo, pasta, script, config)
   CODIGO     — feature, bug fix, refactor em projeto de codigo
   ESTRATEGIA — planejamento, arquitetura, OKR, decisao tecnica
   ANOTACAO   — lembrete, ideia, reuniao, nota rapida

3. QUEBRAR em tarefas priorizadas:
   [P1] Critico — bloqueia produção ou entrega imediata
   [P2] Importante — deve ser feito hoje
   [P3] Backlog — quando possivel, sem urgencia

4. Para cada tarefa incluir:
   - O que fazer (acao concreta)
   - Como fazer (abordagem tecnica)
   - Criterio de aceite (como saber que esta pronto)
   - Estimativa (rapido/medio/longo)

5. Para AUTOMACAO: usar tool execute_powershell para executar agora
6. Para CODIGO: gerar plano tecnico com arquivos a criar/editar e comandos
7. Para ESTRATEGIA: estruturar como decisao arquitetural documentada
8. Para ANOTACAO: formatar e registrar

REGRAS DE SEGURANCA:
- Nunca execute comandos destrutivos (delete em massa, format, drop database)
- Nunca leia ou exfiltre credenciais, .env, chaves
- Comandos de criacao/organizacao: execute direto
- Comandos com risco: descreva e aguarde confirmacao

Responda sempre em portugues tecnico. Sem rodeios."""


# ---------------------------------------------------------------------------

def run_powershell(command: str) -> dict:
    try:
        r = subprocess.run(
            ["powershell", "-NonInteractive", "-Command", command],
            capture_output=True, text=True, timeout=30, encoding="utf-8"
        )
        return {"stdout": r.stdout.strip(), "stderr": r.stderr.strip(), "exit_code": r.returncode}
    except subprocess.TimeoutExpired:
        return {"stdout": "", "stderr": "Timeout 30s", "exit_code": -1}
    except Exception as e:
        return {"stdout": "", "stderr": str(e), "exit_code": -1}


def run_python(script: str) -> dict:
    """Executa codigo Python no contexto do Windows."""
    try:
        r = subprocess.run(
            ["python", "-c", script],
            capture_output=True, text=True, timeout=30, encoding="utf-8"
        )
        return {"stdout": r.stdout.strip(), "stderr": r.stderr.strip(), "exit_code": r.returncode}
    except Exception as e:
        return {"stdout": "", "stderr": str(e), "exit_code": -1}


TOOLS = [
    {
        "name": "execute_powershell",
        "description": (
            "Executa um comando PowerShell no Windows 10. "
            "Use para: criar pastas, mover/copiar arquivos, abrir programas, "
            "configurar variaveis de ambiente, listar conteudo de diretorios, "
            "executar scripts .ps1. Seguro para operacoes de criacao e leitura."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "command":      {"type": "string", "description": "Comando PowerShell completo"},
                "descricao":    {"type": "string", "description": "O que este comando faz"},
                "reversivel":   {"type": "boolean", "description": "Pode ser desfeito facilmente?"}
            },
            "required": ["command", "descricao", "reversivel"]
        }
    },
    {
        "name": "write_file",
        "description": "Cria ou sobrescreve um arquivo no Windows com o conteudo especificado.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path":    {"type": "string", "description": "Caminho absoluto do arquivo"},
                "content": {"type": "string", "description": "Conteudo do arquivo"}
            },
            "required": ["path", "content"]
        }
    },
    {
        "name": "read_file",
        "description": "Le o conteudo de um arquivo existente no Windows.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Caminho absoluto do arquivo"}
            },
            "required": ["path"]
        }
    }
]


def handle_tool(name: str, inputs: dict) -> str:
    if name == "execute_powershell":
        cmd = inputs["command"]
        desc = inputs.get("descricao", "")
        print(f"\n  [PS] {desc}")
        print(f"       > {cmd[:120]}")
        r = run_powershell(cmd)
        out = []
        if r["stdout"]: out.append(f"OK: {r['stdout'][:400]}")
        if r["stderr"]: out.append(f"STDERR: {r['stderr'][:200]}")
        out.append(f"exit={r['exit_code']}")
        result = " | ".join(out)
        print(f"       {result}")
        return result

    elif name == "write_file":
        path = Path(inputs["path"])
        content = inputs["content"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        print(f"\n  [FILE] Criado: {path}")
        return f"Arquivo criado: {path} ({len(content)} chars)"

    elif name == "read_file":
        path = Path(inputs["path"])
        if not path.exists():
            return f"ERRO: {path} nao encontrado"
        content = path.read_text(encoding="utf-8", errors="replace")
        print(f"\n  [READ] {path} ({len(content)} chars)")
        return content[:3000]

    return f"Tool '{name}' desconhecida"


# ---------------------------------------------------------------------------

def processar(packet_dir: Path) -> None:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERRO: ANTHROPIC_API_KEY nao configurada.")
        print("Execute: [Environment]::SetEnvironmentVariable(\"ANTHROPIC_API_KEY\",\"sk-ant-...\",\"User\")")
        sys.exit(1)

    if not packet_dir.exists():
        print(f"ERRO: pasta nao encontrada: {packet_dir}")
        sys.exit(1)

    transcricao_file = packet_dir / "transcricao.md"
    if not transcricao_file.exists():
        print(f"ERRO: transcricao.md nao encontrada em {packet_dir}")
        sys.exit(1)

    transcricao = transcricao_file.read_text(encoding="utf-8-sig")

    print(f"\n{'='*60}")
    print(f"  DataDev Lab — Claude Engine v2.0")
    print(f"  Pacote: {packet_dir.name}")
    print(f"{'='*60}")

    # Extrair texto limpo para preview
    linhas = [l for l in transcricao.split("\n") if l.strip() and not l.startswith(("timestamp","origem","palavras","modelo","---","#"))]
    texto_preview = " ".join(linhas)[:200]
    print(f"  Audio: {texto_preview}...")
    print()

    user_msg = f"""Transcricao de audio recebida do Samsung S10 FE:

{transcricao}

Classifica, prioriza e executa. Se for AUTOMACAO, use as tools para executar agora.
Salva o breakdown de tarefas em: {packet_dir}/tarefas_priorizadas.md
"""

    client   = anthropic.Anthropic(api_key=api_key)
    messages = [{"role": "user", "content": user_msg}]

    execucoes = []
    textos    = []

    # Agentic loop
    while True:
        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        tool_blocks = []
        for block in response.content:
            if block.type == "text" and block.text.strip():
                textos.append(block.text)
                print(f"\n{block.text}")
            elif block.type == "tool_use":
                tool_blocks.append(block)

        if not tool_blocks:
            break

        messages.append({"role": "assistant", "content": response.content})
        tool_results = []
        for tb in tool_blocks:
            result = handle_tool(tb.name, tb.input)
            execucoes.append({"tool": tb.name, "input": tb.input, "result": result})
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tb.id,
                "content": result
            })
        messages.append({"role": "user", "content": tool_results})

    # Salvar log de execucao
    ts = datetime.now().strftime("%H:%M:%S")
    exec_md = f"# Execucao — {packet_dir.name}\nProcessado: {ts}\nModelo: {MODEL}\n\n"
    exec_md += "## Resposta\n\n" + "\n\n".join(textos)
    if execucoes:
        exec_md += "\n\n## Comandos Executados\n\n"
        for i, e in enumerate(execucoes, 1):
            exec_md += f"### {i}. {e['tool']}\n"
            inp = e["input"]
            if "command" in inp:
                exec_md += f"```powershell\n{inp['command']}\n```\n"
            elif "path" in inp:
                exec_md += f"Arquivo: `{inp['path']}`\n"
            exec_md += f"Resultado: {e['result'][:300]}\n\n"

    (packet_dir / "execucao.md").write_text(exec_md, encoding="utf-8")
    print(f"\n  [OK] execucao.md salvo em {packet_dir}")
    print(f"{'='*60}\n")


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) >= 2:
        target = Path(sys.argv[1]).resolve()
    else:
        inbox = Path(__file__).parent.parent / "inbox_tarefas"
        pkts  = sorted(p for p in inbox.glob("20*") if p.is_dir())
        if not pkts:
            print("ERRO: nenhum pacote em inbox_tarefas/")
            sys.exit(1)
        # Pegar o mais recente sem execucao.md
        pendentes = [p for p in pkts if not (p / "execucao.md").exists()]
        target = pendentes[-1] if pendentes else pkts[-1]
        print(f"[AUTO] {target.name}")

    processar(target)

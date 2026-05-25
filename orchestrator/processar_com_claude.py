"""
processar_com_claude.py — Envia pacote de tarefa ao Claude via Anthropic SDK
DataDev Demarchi Lab — Audio Orchestrator v1.0.0

Uso:
  python processar_com_claude.py <caminho_da_pasta_do_pacote>

Exemplo:
  python processar_com_claude.py ..\inbox_tarefas\2026-05-24_19-34-21

Requer:
  pip install anthropic
  Variavel de ambiente ANTHROPIC_API_KEY configurada

O que faz:
  1. Le transcricao.md e roteiro.md do pacote
  2. Monta prompt com contexto completo para o Claude
  3. Claude interpreta e sugere/executa o comando PowerShell
  4. Salva a resposta em resposta_claude.md dentro do pacote
  5. Exibe o resultado no terminal
"""
import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime

# ── Verificar dependencia ────────────────────────────────────────────────────
try:
    import anthropic
except ImportError:
    print("ERRO: pacote 'anthropic' nao instalado.")
    print("Execute: pip install anthropic")
    sys.exit(1)

# ── Configuracao ─────────────────────────────────────────────────────────────
MODEL = "claude-sonnet-4-5"
MAX_TOKENS = 2048


SYSTEM_PROMPT = """Voce e um assistente de automacao para Windows 10.
O usuario enviou um comando de voz do Samsung S10 FE. Sua tarefa e:

1. Analisar a transcricao e o roteiro de passos
2. Determinar exatamente o que o usuario quer fazer no Windows
3. Gerar o comando PowerShell correto para executar a tarefa
4. Executar o comando (usando a tool execute_powershell) se for seguro e claro
5. Responder em portugues com o resultado

REGRAS DE SEGURANCA:
- Nunca execute comandos destrutivos sem confirmacao explicita (rm -rf, format, etc)
- Nunca acesse, modifique ou exfiltre dados pessoais ou credenciais
- Nunca instale software sem instrucao explicita
- Para tarefas simples (criar pasta, mover arquivo, abrir app): execute diretamente
- Para tarefas complexas ou ambiguas: explique o que faria e peca confirmacao

USUARIO: Antonio Demarchi — Backend Dev II em nstech, Rio de Janeiro
CONTEXTO: Sistema DataDev Lab — comandos de voz → automacao Windows 10"""


def load_packet(packet_dir: Path) -> dict:
    """Carrega os arquivos do pacote de tarefa."""
    files = {}
    for name in ["transcricao.md", "roteiro.md", "descricao_tarefa.md"]:
        f = packet_dir / name
        if f.exists():
            files[name] = f.read_text(encoding="utf-8")
        else:
            files[name] = f"(arquivo {name} nao encontrado)"
    return files


def execute_powershell(command: str) -> dict:
    """Executa comando PowerShell e retorna stdout/stderr/exitcode."""
    print(f"\n[EXECUCAO] PowerShell:\n  {command}\n")
    try:
        result = subprocess.run(
            ["powershell", "-NonInteractive", "-Command", command],
            capture_output=True,
            text=True,
            timeout=30,
            encoding="utf-8",
        )
        return {
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "exit_code": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"stdout": "", "stderr": "Timeout: comando demorou mais de 30s", "exit_code": -1}
    except Exception as e:
        return {"stdout": "", "stderr": str(e), "exit_code": -1}


def processar_pacote(packet_dir: Path):
    """Fluxo principal: carrega pacote → Claude → executa → salva resultado."""

    # ── Verificar API Key ────────────────────────────────────────────────────
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERRO: ANTHROPIC_API_KEY nao configurada.")
        print()
        print("Para configurar (permanente):")
        print('  [Environment]::SetEnvironmentVariable("ANTHROPIC_API_KEY","sk-ant-...","User")')
        print()
        print("Para esta sessao apenas:")
        print('  $env:ANTHROPIC_API_KEY = "sk-ant-..."')
        sys.exit(1)

    # ── Carregar pacote ──────────────────────────────────────────────────────
    if not packet_dir.exists():
        print(f"ERRO: Pasta nao encontrada: {packet_dir}")
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"  DataDev Lab — Processando com Claude")
    print(f"  Pacote: {packet_dir.name}")
    print(f"{'='*60}\n")

    files = load_packet(packet_dir)
    transcricao = files["transcricao.md"]
    roteiro = files["roteiro.md"]
    descricao = files["descricao_tarefa.md"]

    print(f"[TRANSCRICAO] {transcricao[:120]}...")
    print(f"[ROTEIRO]     {roteiro[:120]}...")

    # ── Tool definition ──────────────────────────────────────────────────────
    tools = [
        {
            "name": "execute_powershell",
            "description": "Executa um comando PowerShell no Windows 10 do usuario. Use para criar pastas, mover arquivos, abrir programas e outras tarefas de automacao seguras.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "O comando PowerShell completo a ser executado"
                    },
                    "justificativa": {
                        "type": "string",
                        "description": "Por que este comando executa a intencao do usuario"
                    }
                },
                "required": ["command", "justificativa"]
            }
        }
    ]

    # ── Prompt do usuario ────────────────────────────────────────────────────
    user_message = f"""Recebi este comando de voz do Samsung S10 FE:

## Transcricao Completa
{transcricao}

## Roteiro de Passos Extraidos
{roteiro}

## Descricao da Tarefa
{descricao}

Analise, interprete e execute a tarefa no Windows 10 usando a tool execute_powershell se necessario."""

    # ── Chamar Claude ────────────────────────────────────────────────────────
    client = anthropic.Anthropic(api_key=api_key)
    messages = [{"role": "user", "content": user_message}]

    print("\n[CLAUDE] Enviando para Claude API...")
    resultado_final = []
    tool_results_log = []

    # Agentic loop com tool use
    while True:
        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=SYSTEM_PROMPT,
            tools=tools,
            messages=messages,
        )

        # Processar resposta
        tool_use_blocks = []
        text_blocks = []

        for block in response.content:
            if block.type == "text":
                text_blocks.append(block.text)
                resultado_final.append(block.text)
            elif block.type == "tool_use":
                tool_use_blocks.append(block)

        if text_blocks:
            print(f"\n[CLAUDE] {chr(10).join(text_blocks)}")

        # Se Claude quer usar tool
        if tool_use_blocks:
            messages.append({"role": "assistant", "content": response.content})
            tool_results = []

            for tool_block in tool_use_blocks:
                if tool_block.name == "execute_powershell":
                    cmd = tool_block.input.get("command", "")
                    justificativa = tool_block.input.get("justificativa", "")
                    print(f"\n[TOOL] Justificativa: {justificativa}")
                    exec_result = execute_powershell(cmd)

                    output_str = ""
                    if exec_result["stdout"]:
                        output_str += f"STDOUT:\n{exec_result['stdout']}\n"
                    if exec_result["stderr"]:
                        output_str += f"STDERR:\n{exec_result['stderr']}\n"
                    output_str += f"Exit code: {exec_result['exit_code']}"

                    print(f"[RESULTADO] {output_str}")
                    tool_results_log.append({
                        "command": cmd,
                        "result": exec_result
                    })

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_block.id,
                        "content": output_str
                    })

            messages.append({"role": "user", "content": tool_results})
            continue  # continua o loop para Claude interpretar o resultado

        # Sem mais tool_use — Claude terminou
        break

    # ── Salvar resultado ─────────────────────────────────────────────────────
    resposta_text = "\n\n".join(resultado_final)
    timestamp = datetime.now().strftime("%H:%M:%S")

    output_md = f"""# Resposta Claude — {packet_dir.name}
Processado em: {timestamp}
Modelo: {MODEL}

## Interpretacao e Acao

{resposta_text}
"""

    if tool_results_log:
        output_md += "\n## Comandos Executados\n\n"
        for i, tr in enumerate(tool_results_log, 1):
            r = tr["result"]
            output_md += f"### Comando {i}\n```powershell\n{tr['command']}\n```\n"
            if r["stdout"]:
                output_md += f"**Saida:**\n```\n{r['stdout']}\n```\n"
            if r["stderr"]:
                output_md += f"**Erro:**\n```\n{r['stderr']}\n```\n"
            output_md += f"**Exit code:** {r['exit_code']}\n\n"

    output_file = packet_dir / "resposta_claude.md"
    output_file.write_text(output_md, encoding="utf-8")

    print(f"\n{'='*60}")
    print(f"  CONCLUIDO!")
    print(f"  Resposta salva em: {output_file}")
    print(f"{'='*60}\n")

    return resposta_text


# ── Entry point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Sem argumento: pegar o pacote mais recente automaticamente
        inbox = Path(__file__).parent.parent / "inbox_tarefas"
        packets = sorted(inbox.glob("20*"))
        if not packets:
            print("ERRO: Nenhum pacote em inbox_tarefas/")
            print("Uso: python processar_com_claude.py <caminho_da_pasta>")
            sys.exit(1)
        packet_dir = packets[-1]
        print(f"[AUTO] Pacote mais recente: {packet_dir.name}")
    else:
        packet_dir = Path(sys.argv[1]).resolve()

    processar_pacote(packet_dir)

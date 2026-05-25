"""
processar_com_claude_code.py
DataDev Demarchi Lab — Audio Orchestrator v2.0 (Claude Pro path)

Usa o Claude Code CLI (claude -p) ao invez da API direta.
Requer: claude CLI instalado e autenticado (plano Pro ou Max).
NAO requer ANTHROPIC_API_KEY.

Uso:
  python processar_com_claude_code.py <pasta_do_pacote>
  python processar_com_claude_code.py          # pega o mais recente pendente

Saidas na pasta do pacote:
  tarefas_priorizadas.md   breakdown P1/P2/P3 gerado pelo Claude
  execucao.md              log do que foi executado
"""
import io
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Forcar UTF-8 no stdout/stderr (evita UnicodeEncodeError no Windows cp1252)
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# ---------------------------------------------------------------------------
TIMEOUT_CLI = 180   # segundos para o claude CLI responder

SYSTEM_PROMPT = """Voce e um Engenheiro de Sistemas Senior no DataDev Lab de Antonio Demarchi.

PERFIL DO USUARIO:
- Antonio Demarchi — Backend Dev II na nstech (fintech missao critica, pagamento de fretes PEF/ANTT)
- Stack real: Go (hexagonal, goroutines), Java, React/Next.js, Python, Docker, Kubernetes, Terraform, AWS
- Nivel: senior — responda como peer tecnico, sem didatismo
- Contexto: RJ, CLT R$4.9k, projetos ativos: NeuroLead (Go+AWS), Challenge2 (FIAP EKS), DataDev Lab

WORKFLOW:
Voce recebe uma transcricao de audio do Samsung S10 FE via KDE Connect.
O audio foi transcrito offline com Whisper PT-BR — pode ter erros foneticos.

SUA MISSAO:

1. INTERPRETAR corretamente mesmo com erros de transcricao
   (ex: "Neurolid" = NeuroLead, "Midleuari" = Middleware, "Chav SSH" = Chave SSH)

2. CLASSIFICAR o tipo:
   AUTOMACAO  — tarefa executavel no Windows agora (arquivo, pasta, script, config)
   CODIGO     — feature, bug fix, refactor em projeto de codigo
   ESTRATEGIA — planejamento, arquitetura, OKR, decisao tecnica
   ANOTACAO   — lembrete, ideia, reuniao, nota rapida

3. QUEBRAR em tarefas priorizadas:
   [P1] Critico — bloqueia producao ou entrega imediata
   [P2] Importante — deve ser feito hoje
   [P3] Backlog — quando possivel, sem urgencia

4. Para cada tarefa incluir:
   - O que fazer (acao concreta)
   - Como fazer (abordagem tecnica)
   - Criterio de aceite (como saber que esta pronto)
   - Estimativa (rapido/medio/longo)

5. Para AUTOMACAO: inclua blocos ```powershell com os comandos prontos.
   Marque comandos seguros (criacao, organizacao) como normais.
   Marque comandos de risco como [REQUER CONFIRMACAO] antes do bloco.

6. Para CODIGO: gere plano tecnico com arquivos a criar/editar e comandos
7. Para ESTRATEGIA: estruture como decisao arquitetural documentada
8. Para ANOTACAO: formate e registre com data/contexto

REGRAS DE SEGURANCA:
- Nunca sugira comandos destrutivos (delete em massa, format, drop database)
- Nunca leia ou exfiltre credenciais, .env, chaves SSH
- Comandos de criacao/organizacao: inclua diretamente no powershell block
- Comandos com risco: marque [REQUER CONFIRMACAO] antes do bloco

Responda sempre em portugues tecnico. Sem rodeios.
Formato: markdown estruturado com secoes claras.
"""


# ---------------------------------------------------------------------------
# Claude CLI discovery
# ---------------------------------------------------------------------------

def find_claude_cli() -> str | None:
    """
    Localiza o executavel do Claude Code CLI no sistema.
    Tenta PATH primeiro, depois caminhos comuns no Windows.
    Retorna o caminho completo ou None se nao encontrado.
    """
    # 1. PATH padrao
    found = shutil.which("claude") or shutil.which("claude.cmd")
    if found:
        return found

    # 2. npm global (instalacao mais comum)
    npm_paths = [
        Path(os.environ.get("APPDATA", "")) / "npm" / "claude.cmd",
        Path(os.environ.get("APPDATA", "")) / "npm" / "claude",
    ]
    for p in npm_paths:
        if p.exists():
            return str(p)

    # 3. Instaladores standalone conhecidos
    local_app = Path(os.environ.get("LOCALAPPDATA", ""))
    program_files = Path(os.environ.get("ProgramFiles", "C:\\Program Files"))
    standalone_paths = [
        local_app / "Programs" / "Claude" / "claude.exe",
        local_app / "Programs" / "claude-code" / "claude.exe",
        program_files / "Claude" / "claude.exe",
    ]
    for p in standalone_paths:
        if p.exists():
            return str(p)

    return None


def verify_claude_auth(claude_cmd: str) -> bool:
    """Verifica se o CLI esta autenticado (claude --version deve funcionar)."""
    try:
        r = subprocess.run(
            [claude_cmd, "--version"],
            capture_output=True, text=True, timeout=10
        )
        return r.returncode == 0
    except (subprocess.TimeoutExpired, OSError):
        return False


# ---------------------------------------------------------------------------
# Chamada principal ao Claude
# ---------------------------------------------------------------------------

def call_claude_cli(claude_cmd: str, prompt: str) -> str:
    """
    Envia o prompt para claude --print via stdin pipe.
    Evita limites de comprimento de argumento no Windows e problemas
    com caracteres especiais/newlines em argumentos de linha de comando.
    Lanca RuntimeError em caso de falha.
    """
    import tempfile

    # Escreve o prompt em arquivo temporario (UTF-8 limpo, sem BOM)
    tmp_dir = os.path.join(tempfile.gettempdir(), "datadev-orch-runner")
    os.makedirs(tmp_dir, exist_ok=True)
    tmp_file = os.path.join(tmp_dir, "prompt_input.txt")

    with open(tmp_file, "w", encoding="utf-8") as f:
        f.write(prompt)

    try:
        # Pipe stdin: cat tmp_file | claude --print
        # O claude --print le de stdin quando nao ha argumento de prompt
        with open(tmp_file, "r", encoding="utf-8") as stdin_f:
            result = subprocess.run(
                [claude_cmd, "--print"],
                stdin=stdin_f,
                capture_output=True,
                text=True,
                timeout=TIMEOUT_CLI,
                encoding="utf-8",
                errors="replace",
            )
        if result.returncode != 0:
            err = (result.stderr or "").strip()[:400] or "(sem stderr)"
            raise RuntimeError(f"claude CLI retornou exit={result.returncode}: {err}")
        return result.stdout
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"Timeout {TIMEOUT_CLI}s — Claude nao respondeu a tempo")
    except OSError as e:
        raise RuntimeError(f"Erro ao executar claude CLI: {e}")
    finally:
        try:
            os.unlink(tmp_file)
        except OSError:
            pass


# ---------------------------------------------------------------------------
# Execucao de PowerShell
# ---------------------------------------------------------------------------

def extract_ps_blocks(text: str) -> list:
    """
    Extrai blocos ```powershell / ```ps1 do markdown.
    Ignora blocos precedidos por [REQUER CONFIRMACAO].
    Retorna lista de (cmd_str, requer_confirmacao).
    """
    results = []
    # Dividir o texto em segmentos antes de cada bloco de codigo
    pattern = r"```(?:powershell|ps1|ps)\s*\n(.*?)\n```"
    for match in re.finditer(pattern, text, re.DOTALL | re.IGNORECASE):
        cmd = match.group(1).strip()
        if not cmd:
            continue
        # Checar se ha [REQUER CONFIRMACAO] nas 3 linhas antes do bloco
        start = match.start()
        contexto = text[max(0, start - 200):start].lower()
        requer = "requer confirmacao" in contexto or "confirmacao" in contexto
        results.append((cmd, requer))
    return results


def run_powershell(command: str) -> dict:
    try:
        r = subprocess.run(
            ["powershell", "-NonInteractive", "-Command", command],
            capture_output=True, text=True, timeout=30, encoding="utf-8"
        )
        return {
            "stdout": r.stdout.strip(),
            "stderr": r.stderr.strip(),
            "exit_code": r.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"stdout": "", "stderr": "Timeout 30s", "exit_code": -1}
    except Exception as e:
        return {"stdout": "", "stderr": str(e), "exit_code": -1}


# ---------------------------------------------------------------------------
# Processamento principal
# ---------------------------------------------------------------------------

def processar(packet_dir: Path) -> None:

    # Validacoes basicas
    if not packet_dir.exists():
        print(f"ERRO: pasta nao encontrada: {packet_dir}")
        sys.exit(1)

    transcricao_file = packet_dir / "transcricao.md"
    if not transcricao_file.exists():
        print(f"ERRO: transcricao.md nao encontrada em {packet_dir}")
        sys.exit(1)

    # Localizar Claude CLI
    claude_cmd = find_claude_cli()
    if not claude_cmd:
        print("ERRO: Claude Code CLI nao encontrado.")
        print("Instale em: https://claude.ai/download")
        print("Ou configure ANTHROPIC_API_KEY para usar o caminho API.")
        sys.exit(1)

    if not verify_claude_auth(claude_cmd):
        print(f"ERRO: Claude CLI encontrado em '{claude_cmd}' mas nao esta autenticado.")
        print("Execute 'claude' no terminal e complete o login antes de continuar.")
        sys.exit(1)

    # utf-8-sig remove BOM automaticamente (PowerShell escreve UTF-8 com BOM)
    transcricao = transcricao_file.read_text(encoding="utf-8-sig")

    print(f"\n{'='*60}")
    print(f"  DataDev Lab — Claude Code Engine v2.0 (Pro path)")
    print(f"  CLI: {claude_cmd}")
    print(f"  Pacote: {packet_dir.name}")
    print(f"{'='*60}")

    linhas = [
        l for l in transcricao.split("\n")
        if l.strip() and not l.startswith(("timestamp", "origem", "palavras", "modelo", "---", "#"))
    ]
    texto_preview = " ".join(linhas)[:200]
    print(f"  Audio: {texto_preview}...")
    print()
    print(f"  >> Enviando para Claude Code CLI (timeout {TIMEOUT_CLI}s)...")

    # Prompt task-first: instrucao e transcricao antes do contexto
    # Evita que o CLI trate o bloco inicial como "greeting" e pergunte o que fazer
    full_prompt = f"""Analise esta transcricao de audio e gere o breakdown de tarefas agora.

TRANSCRICAO RECEBIDA (Samsung S10 FE -> Whisper PT-BR, pode ter erros foneticos):
===================================================================================
{transcricao}
===================================================================================

RESPONDA NESTE FORMATO EXATO (markdown):

## Tipo
[AUTOMACAO | CODIGO | ESTRATEGIA | ANOTACAO] — justificativa em 1 linha

## Tarefas Priorizadas

### [P1] Titulo da tarefa critica
- **O que:** acao concreta
- **Como:** abordagem tecnica
- **Aceite:** como saber que esta pronto
- **Tempo:** rapido/medio/longo

### [P2] ...

### [P3] ...

## Comandos (para tipo AUTOMACAO)
Inclua blocos ```powershell com comandos reais prontos para executar no Windows 10.
Paths reais do Windows (Desktop = C:\\Users\\Antonio Demarchi\\Desktop\\, etc).

---

CONTEXTO DO USUARIO (use para interpretar erros foneticos e dominio):
- Nome: Antonio Demarchi, Backend Dev II, nstech (fintech critica, pagamento fretes PEF/ANTT)
- Stack: Go (hexagonal), Java, React/Next.js, Python, Docker, Kubernetes, Terraform, AWS
- Projetos ativos: NeuroLead (Go+AWS), Challenge2 (FIAP EKS), DataDev Lab, AGV, Sebrae
- Exemplos de erros do Whisper: "Neurolid"=NeuroLead, "Chav SSH"=Chave SSH, "Midleuari"=Middleware
- Responda em portugues tecnico. Nao faca perguntas. Nao peça confirmacao. Apenas analise e responda."""

    # Chamar Claude CLI
    try:
        response = call_claude_cli(claude_cmd, full_prompt)
    except RuntimeError as e:
        print(f"\n  [ERRO] {e}")
        sys.exit(1)

    print(f"\n{response}")

    # Salvar tarefas_priorizadas.md
    (packet_dir / "tarefas_priorizadas.md").write_text(response, encoding="utf-8")
    print(f"\n  [OK] tarefas_priorizadas.md salvo")

    # Executar blocos PowerShell (apenas os seguros, sem [REQUER CONFIRMACAO])
    ps_blocks = extract_ps_blocks(response)
    execucoes = []

    if ps_blocks:
        seguros   = [(c, r) for c, r in ps_blocks if not r]
        pendentes = [(c, r) for c, r in ps_blocks if r]
        print(f"\n  >> {len(ps_blocks)} bloco(s) PowerShell: "
              f"{len(seguros)} auto-exec, {len(pendentes)} aguardando confirmacao")

        for i, (cmd, _) in enumerate(seguros, 1):
            print(f"\n  [PS {i}/{len(seguros)}] {cmd[:100]}")
            r = run_powershell(cmd)
            status = "OK" if r["exit_code"] == 0 else "ERRO"
            if r["stdout"]:
                print(f"    {status}: {r['stdout'][:200]}")
            if r["stderr"]:
                print(f"    STDERR: {r['stderr'][:100]}")
            execucoes.append({"cmd": cmd, "result": r, "auto": True})

        for cmd, _ in pendentes:
            execucoes.append({"cmd": cmd, "result": None, "auto": False})

    # Salvar execucao.md
    ts = datetime.now().strftime("%H:%M:%S")
    exec_md = f"# Execucao via Claude Code — {packet_dir.name}\n"
    exec_md += f"Processado: {ts}\nMotor: Claude Code CLI (plano Pro)\n\n"
    exec_md += "## Resposta Claude\n\n" + response

    if execucoes:
        exec_md += "\n\n## Comandos PowerShell\n\n"
        for i, e in enumerate(execucoes, 1):
            status_label = "AUTO-EXECUTADO" if e["auto"] else "AGUARDANDO CONFIRMACAO"
            exec_md += f"### {i}. [{status_label}]\n"
            exec_md += f"```powershell\n{e['cmd']}\n```\n"
            if e["result"]:
                r = e["result"]
                if r["stdout"]:
                    exec_md += f"Saida: {r['stdout'][:300]}\n"
                if r["stderr"]:
                    exec_md += f"Erro: {r['stderr'][:200]}\n"
                exec_md += f"Exit: {r['exit_code']}\n"
            exec_md += "\n"

    (packet_dir / "execucao.md").write_text(exec_md, encoding="utf-8")
    print(f"\n  [OK] execucao.md salvo em {packet_dir}")
    print(f"{'='*60}\n")


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) >= 2:
        target = Path(sys.argv[1]).resolve()
    else:
        inbox = Path(__file__).parent.parent / "inbox_tarefas"
        pkts = sorted(p for p in inbox.glob("20*") if p.is_dir())
        if not pkts:
            print("ERRO: nenhum pacote em inbox_tarefas/")
            sys.exit(1)
        pendentes = [p for p in pkts if not (p / "execucao.md").exists()]
        target = pendentes[-1] if pendentes else pkts[-1]
        print(f"[AUTO] {target.name}")

    processar(target)

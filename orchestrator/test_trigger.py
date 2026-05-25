"""
test_trigger.py — Mock do Samsung S10 FE
Simula envio de áudio e texto para validar o Orquestrador (Passo 1).

Uso:
    python test_trigger.py           # roda todos os testes
    python test_trigger.py --quick   # só health + text (sem arquivo)
"""
import sys
import time
import os
import tempfile
import json
from pathlib import Path

try:
    import requests
except ImportError:
    print("❌ requests não instalado. Execute: pip install requests")
    sys.exit(1)

BASE_URL = "http://localhost:8765"
INBOX_DIR = Path(__file__).parent.parent / "inbox_tarefas"

# ANSI colors
G, Y, R, C, W = "\033[92m", "\033[93m", "\033[91m", "\033[96m", "\033[0m"

def header(msg: str):
    print(f"\n{C}{'─'*55}")
    print(f"  {msg}")
    print(f"{'─'*55}{W}")

def ok(msg: str):   print(f"  {G}✅ {msg}{W}")
def warn(msg: str): print(f"  {Y}⚠️  {msg}{W}")
def fail(msg: str): print(f"  {R}❌ {msg}{W}")

PASSED = []
FAILED = []

def assert_ok(name: str, cond: bool, detail: str = ""):
    if cond:
        ok(f"{name}{' — ' + detail if detail else ''}")
        PASSED.append(name)
    else:
        fail(f"{name}{' — ' + detail if detail else ''}")
        FAILED.append(name)


# ── TESTES ───────────────────────────────────────────────────────────────────

def test_health():
    header("T1 — Health Check")
    r = requests.get(f"{BASE_URL}/health", timeout=5)
    assert_ok("HTTP 200", r.status_code == 200)
    data = r.json()
    assert_ok("status=ok", data.get("status") == "ok")
    assert_ok("version presente", "version" in data)
    print(f"  Resposta: {json.dumps(data, indent=2)}")


def test_status():
    header("T2 — Status Endpoint")
    r = requests.get(f"{BASE_URL}/status", timeout=5)
    assert_ok("HTTP 200", r.status_code == 200)
    data = r.json()
    assert_ok("stats.received presente", "stats" in data)
    assert_ok("inbox_dir presente", "inbox_dir" in data)
    print(f"  Resposta: {json.dumps(data, indent=2)}")


def test_text_endpoint():
    header("T3 — Endpoint /text (simula S Pen ou texto direto)")
    payload = {
        "text": (
            "Precisamos implementar autenticação JWT no NeuroLead com urgência. "
            "Os 15 endpoints estão completamente abertos no IP público. "
            "Primeira prioridade: criar o middleware de auth. "
            "Segunda prioridade: escrever os testes de integração. "
            "Terceira prioridade: revogar a chave SSH comprometida no git."
        ),
        "source": "test_trigger_spen",
    }
    r = requests.post(f"{BASE_URL}/text", data=payload, timeout=5)
    assert_ok("HTTP 200", r.status_code == 200)
    data = r.json()
    assert_ok("status=queued", data.get("status") == "queued")
    assert_ok("preview presente", "preview" in data)
    print(f"  Preview: {data.get('preview')}")


def test_audio_endpoint():
    header("T4 — Endpoint /audio (simula envio de .wav do S10 FE)")
    # WAV mínimo válido (44 bytes de header RIFF)
    wav_header = (
        b"RIFF" + (36).to_bytes(4, "little") +
        b"WAVE" +
        b"fmt " + (16).to_bytes(4, "little") +
        (1).to_bytes(2, "little") +   # PCM
        (1).to_bytes(2, "little") +   # mono
        (16000).to_bytes(4, "little") + # 16kHz
        (32000).to_bytes(4, "little") +
        (2).to_bytes(2, "little") +
        (16).to_bytes(2, "little") +
        b"data" + (0).to_bytes(4, "little")
    )
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        f.write(wav_header)
        tmp_path = f.name

    try:
        with open(tmp_path, "rb") as f:
            r = requests.post(
                f"{BASE_URL}/audio",
                files={"file": ("nota_voz_s10fe.wav", f, "audio/wav")},
                data={"source": "s10fe_mock"},
                timeout=5,
            )
        assert_ok("HTTP 200", r.status_code == 200)
        data = r.json()
        assert_ok("status=queued", data.get("status") == "queued")
        assert_ok("size_bytes presente", "size_bytes" in data)
        print(f"  Arquivo: {data.get('file')} ({data.get('size_bytes')} bytes)")
    finally:
        os.unlink(tmp_path)


def test_packet_structure():
    header("T5 — Validar Estrutura dos Pacotes Gerados")
    time.sleep(2)  # aguarda os pipelines async terminarem

    REQUIRED = {
        "transcricao.md",
        "roteiro.md",
        "descricao_tarefa.md",
        "futuro_processamento_1.md",
        "futuro_processamento_2.md",
        "processar_agora.ps1",
    }

    packets = sorted(INBOX_DIR.glob("*")) if INBOX_DIR.exists() else []
    assert_ok(f"inbox_tarefas/ existe", INBOX_DIR.exists())
    assert_ok(f"Pelo menos 1 pacote criado", len(packets) >= 1, f"encontrados: {len(packets)}")

    for packet in packets:
        files = {f.name for f in packet.iterdir()}
        missing = REQUIRED - files
        assert_ok(
            f"Pacote {packet.name} completo",
            len(missing) == 0,
            f"faltando: {missing}" if missing else "todos os 6 arquivos presentes"
        )
        # Verificar que futuro_processamento_*.md têm conteúdo (não são vazios)
        for fname in ["futuro_processamento_1.md", "futuro_processamento_2.md"]:
            fp = packet / fname
            if fp.exists():
                assert_ok(f"  {fname} tem template", fp.stat().st_size > 0)

        # Mostrar árvore
        print(f"\n  📁 {packet.name}/")
        for f in sorted(packet.iterdir()):
            size = f.stat().st_size
            print(f"     📜 {f.name:<35} {size:>5} bytes")


def test_invalid_extension():
    header("T6 — Rejeitar extensão inválida")
    with tempfile.NamedTemporaryFile(suffix=".exe", delete=False) as f:
        f.write(b"MZ malicious")
        tmp_path = f.name
    try:
        with open(tmp_path, "rb") as f:
            r = requests.post(
                f"{BASE_URL}/audio",
                files={"file": ("virus.exe", f, "application/octet-stream")},
                timeout=5,
            )
        assert_ok("HTTP 400 para .exe", r.status_code == 400)
    finally:
        os.unlink(tmp_path)


# ── RUNNER ───────────────────────────────────────────────────────────────────

def main():
    quick = "--quick" in sys.argv

    print(f"\n{C}{'='*55}")
    print(f"  DataDev Lab -- Mock S10 FE -> Orquestrador")
    print(f"  Passo 1 -- Validacao da Estrutura Base")
    print(f"{'='*55}{W}")
    print(f"  URL: {BASE_URL}")
    print(f"  Inbox: {INBOX_DIR}")

    try:
        test_health()
        test_status()
        test_text_endpoint()
        if not quick:
            test_audio_endpoint()
        test_packet_structure()
        test_invalid_extension()
    except requests.ConnectionError:
        print(f"\n{R}❌ Orquestrador offline. Execute primeiro: python main.py{W}")
        sys.exit(1)

    print(f"\n{C}{'='*55}")
    print(f"  Resultado: {G}{len(PASSED)} OK{W}  {R}{len(FAILED)} FALHOU{W}")
    if FAILED:
        print(f"  Falhas: {R}{', '.join(FAILED)}{W}")
    print(f"{C}{'='*55}{W}\n")

    sys.exit(0 if not FAILED else 1)


if __name__ == "__main__":
    main()

"""Teste end-to-end com Whisper real — executa standalone."""
import requests, json, time, sys
from pathlib import Path

DIR = Path(__file__).parent
WAV = DIR / "test_audio_s10fe.wav"

print("=" * 50)
print("  Teste End-to-End — Whisper Real")
print("=" * 50)

if not WAV.exists():
    print(f"ERRO: {WAV} nao encontrado")
    sys.exit(1)

print(f"Enviando {WAV.name} ({WAV.stat().st_size:,} bytes)...")
with open(WAV, "rb") as f:
    r = requests.post("http://localhost:8765/audio",
        files={"file": ("nota_s10fe.wav", f, "audio/wav")},
        data={"source": "s10fe_real_test"})

print(f"HTTP {r.status_code}: {r.json()['message']}")
print("Aguardando Whisper transcrever (CPU ~15-40s)...")

prev = None
for i in range(50):
    time.sleep(2)
    stats = requests.get("http://localhost:8765/status").json()["stats"]
    line = f"  {i*2:3}s — recv={stats['received']} done={stats['processed']} err={stats['errors']}"
    if line != prev:
        print(line)
        prev = line
    if stats["processed"] > 0 or stats["errors"] > 0:
        break

print()
if stats["processed"] > 0:
    print("SUCESSO — pacote gerado!")
    inbox = DIR.parent / "inbox_tarefas"
    packets = sorted(inbox.glob("*"))
    if packets:
        latest = packets[-1]
        print(f"\nPacote: {latest.name}/")
        for f in sorted(latest.iterdir()):
            print(f"  {f.name:<35} {f.stat().st_size:>5} bytes")
        print("\n--- transcricao.md (primeiras 400 chars) ---")
        t = (latest / "transcricao.md").read_text(encoding="utf-8")
        print(t[:400])
        print("\n--- roteiro.md (primeiras 400 chars) ---")
        r2 = (latest / "roteiro.md").read_text(encoding="utf-8")
        print(r2[:400])
else:
    print("ERRO no pipeline — verificar api_err.log")
    log = (DIR / "api_err.log").read_text(encoding="utf-8", errors="replace")
    print(log[-800:])

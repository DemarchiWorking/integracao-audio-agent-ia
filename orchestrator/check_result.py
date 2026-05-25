import requests, sys, time
from pathlib import Path

inbox = Path(__file__).parent.parent / "inbox_tarefas"

# Aguarda ate processed aumentar
initial = requests.get("http://localhost:8765/status").json()["stats"]["processed"]
print(f"Processed inicial: {initial} — aguardando...")

for _ in range(30):
    time.sleep(2)
    stats = requests.get("http://localhost:8765/status").json()["stats"]
    print(f"  recv={stats['received']} done={stats['processed']} err={stats['errors']}")
    if stats["processed"] > initial or stats["errors"] > 0:
        break

print()
packets = sorted(inbox.glob("*"))
if not packets:
    print("NENHUM pacote em inbox_tarefas/")
    sys.exit(1)

latest = packets[-1]
print(f"Ultimo pacote: {latest.name}/")
for f in sorted(latest.iterdir()):
    print(f"  {f.name:<35} {f.stat().st_size:>5} bytes")

t = (latest / "transcricao.md").read_text(encoding="utf-8")
print("\n--- TRANSCRICAO ---")
for line in t.split("\n"):
    if line.strip() and not line.startswith(("#", ">", "---")):
        print(line[:300])
        break

r = (latest / "roteiro.md").read_text(encoding="utf-8")
print("\n--- ROTEIRO (passos) ---")
for line in r.split("\n"):
    if line.strip().startswith(tuple("123456789")):
        print(line)

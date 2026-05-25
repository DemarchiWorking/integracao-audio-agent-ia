# 🧠 Contexto para o Próximo Prompt de Implementação

> Este arquivo prepara o Claude Code para implementar a integração S10 FE ↔ Windows 10.
> **Use como briefing no início da próxima sessão.**

---

## Situação Atual

- Pasta criada: `integracoes/s10fe-spen-audio/`
- Plano base já existia em: `integracoes/s10fe-windows/` (sem S Pen, sem bidirecional)
- O plano base tem: `pipeline.py` completo, guia de instalação, diagrama de arquitetura
- **O que falta implementar:** versão expandida com S Pen + retorno de resultado ao S10 FE

---

## O Que Precisa Ser Construído

### Módulo 1 — pipeline bidirecional (`pipeline.py` v2.0)
- Monitorar `input/audio/` e `input/spen/`
- Whisper transcreve áudios `.m4a/.wav`
- OCR processa imagens/PDFs do S Pen
- Claude Code estrutura os dois tipos
- `kdeconnect-cli` envia notificação de volta ao S10 FE

### Módulo 2 — setup automatizado (`setup.ps1`)
- Instalar FFmpeg, KDE Connect, Tesseract
- Criar estrutura de pastas
- Instalar dependências Python
- Verificar KDE Connect conectado ao S10 FE

### Módulo 3 — configuração KDE Connect
- Documento com passo a passo para configurar destino de compartilhamento no KDE Connect

---

## Ambiente

```
OS:         Windows 10 Pro (build 19045)
Python:     disponível (versão a verificar)
Node/npm:   v22.19.0 / 10.9.3
KDE Connect: a instalar
Dispositivo: Samsung Galaxy S10 FE (Android)
S Pen:       nativo do S10 FE
```

---

## Referências Existentes

- Pipeline base completo: `../s10fe-windows/IMPLEMENTACAO.md`
- Diagrama base: `../s10fe-windows/ARQUITETURA.md`
- Dependências: `pip install openai-whisper watchdog rich python-dotenv pytesseract Pillow`

---

## Prompt Sugerido para Próxima Sessão

```
Contexto: Sou Antonio Demarchi, Engenheiro Senior.
Pasta: C:\Users\Antonio Demarchi\Desktop\contexto-agente-claude\integracoes\s10fe-spen-audio\

Quero implementar a integração Samsung S10 FE (com S Pen) ↔ Windows 10 bidirecional.

Funcionalidades:
1. S10 FE grava áudio → envia via KDE Connect → Windows transcreve com Whisper → Claude Code processa → resultado salvo em output/ → notificação enviada de volta ao S10 FE
2. S10 FE escreve nota com S Pen no Samsung Notes → exporta → envia via KDE Connect → Windows faz OCR → Claude Code processa → resultado de volta ao S10 FE

Contexto base já existe em: ../s10fe-windows/IMPLEMENTACAO.md

Por favor:
1. Criar pipeline.py v2.0 com suporte bidirecional (áudio + S Pen)
2. Criar setup.ps1 para instalação automatizada no Windows
3. Criar guia de configuração KDE Connect
```

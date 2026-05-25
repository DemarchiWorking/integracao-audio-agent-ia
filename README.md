# 🎙️✏️ Integração S10 FE (S Pen) ↔ Windows 10 — Audio + Transcrição Bidirecional

> **Versão:** 1.0.0 | **Status:** 🔵 Planejado — aguardando implementação
> **Contexto:** Este módulo expande `../s10fe-windows/` adicionando suporte ao S Pen e fluxo bidirecional.

---

## 🎯 Objetivo

Criar um pipeline **bidirecional** entre o Samsung S10 FE (com S Pen) e o Windows 10 que suporte:

| Direção | Fluxo | Descrição |
|---|---|---|
| ➡️ **A→W** | S10 FE → Windows | Gravar áudio no tablet → Windows transcreve via Whisper → resultado de volta ao S10 FE |
| ⬅️ **W→A** | Windows → S10 FE | Windows processa texto/resposta → envia notificação/arquivo ao S10 FE |
| ✏️ **S Pen** | S10 FE → Windows | Escrita manuscrita no Samsung Notes → converte para texto → Windows processa |

---

## 🏗️ Arquitetura Bidirecional

```
┌──────────────────────────────────────┐
│  SAMSUNG S10 FE (Android)            │
│                                      │
│  [Gravador de Voz]   → .m4a          │──────────┐
│  [Samsung Notes/SPen]→ .pdf/.txt     │──────────┤  WiFi via
│  [KDE Connect App]                   │          │  KDE Connect
│  [Whisper Mobile] (opcional futuro)  │◄─────────┤
└──────────────────────────────────────┘          │
                                                   │
┌──────────────────────────────────────┐          │
│  WINDOWS 10                          │          │
│                                      │          │
│  [KDE Connect Windows]  ◄────────────┼──────────┘
│          │                           │
│          ▼                           │
│  📁 input/   (áudio / texto S Pen)   │
│          │                           │
│          ▼                           │
│  [pipeline.py]                       │
│     ├── Whisper  → transcrição       │
│     ├── Claude Code → processamento  │
│     └── KDE Notify → envia p/ S10 FE │
│          │                           │
│          ▼                           │
│  📁 output/  (.md estruturado)       │
└──────────────────────────────────────┘
```

---

## 📋 Funcionalidades

### F1 — Áudio S10 FE → Windows → Transcrição
1. Gravar nota de voz no S10 FE (app Gravador Samsung)
2. Enviar via KDE Connect para `input/`
3. `pipeline.py` detecta → Whisper transcreve
4. Claude Code estrutura o texto
5. Resultado salvo em `output/` + notificação enviada ao S10 FE via KDE Connect

### F2 — Windows → S10 FE (resposta/notificação)
1. Pipeline finaliza processamento
2. KDE Connect CLI envia notificação com preview do resultado
3. Opcionalmente: copia texto para clipboard do S10 FE (KDE Connect clipboard sync)

### F3 — S Pen / Samsung Notes → Windows
1. Escrever nota manuscrita no Samsung Notes com S Pen
2. Samsung Notes exporta como PDF ou texto
3. Enviar via KDE Connect para `input/spen/`
4. Pipeline processa: OCR (se PDF/imagem) ou texto direto
5. Claude Code processa e estrutura

---

## 🛠️ Stack Técnica

```
Transporte:         KDE Connect (WiFi local)
Transcrição áudio:  OpenAI Whisper (local, modelo base)
OCR S Pen (PDF):    pytesseract ou Tesseract (se necessário)
Processamento IA:   Claude Code CLI
Notificação volta:  kdeconnect-cli --notification
Monitoramento:      Python watchdog
```

---

## 📁 Estrutura de Pastas (a criar)

```
audio-pipeline/
├── input/
│   ├── audio/          ← KDE Connect envia áudios aqui
│   └── spen/           ← Samsung Notes exportados aqui
├── processed/          ← Arquivos já processados (backup)
├── output/             ← .md gerados pelo Claude Code
└── pipeline.py         ← Script principal
```

---

## 📦 Dependências

```powershell
# FFmpeg (para Whisper)
winget install Gyan.FFmpeg

# KDE Connect
winget install KDE.KDEConnect

# Python packages
pip install openai-whisper watchdog rich python-dotenv pytesseract Pillow

# Tesseract OCR (para S Pen PDF/imagem)
winget install UB-Mannheim.TesseractOCR
```

---

## ⏭️ Próximos Passos

Ver `IMPLEMENTACAO.md` (a criar no próximo prompt) para guia passo a passo.

---

## 🔗 Relacionado

- `../s10fe-windows/PLANO-INTEGRACAO.md` — plano base (sem S Pen, sem bidirecional)
- `../s10fe-windows/IMPLEMENTACAO.md` — implementação v1.0 já escrita
- `../s10fe-windows/ARQUITETURA.md` — diagrama base

---

## 🔄 Histórico

| Versão | Data | Mudança |
|---|---|---|
| 1.0.0 | 2026-05-24 | Criação — escopo expandido com S Pen + bidirecional |

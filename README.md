# CÓDIGO ZERO — Automação de Reels no Instagram

Pipeline 100% gratuito na nuvem (**GitHub Actions**) que gera e publica Reels sobre o **CÓDIGO ZERO — O Protocolo Imersivo de 14 Dias (Método Z.E.R.O.)**, levando leads para o WhatsApp `(12) 99659-3222`.

## Agenda automática (BRT = UTC-3)
- **08:17** — Pico matinal (regra dos 20 minutos sem checar o celular)
- **13:17** — Pausa do almoço (scripts de resposta e ciência da abstinência)
- **21:17** — Pré-Zona Morta (logo antes das 22h–02h, onde ocorrem 70% das recaídas)

## Estrutura
- `main.py`: Gera roteiro inédito via Gemini API (com fallback de 25 roteiros curados do produto), narração `edge-tts`, B-roll escuro/atmosférico + trilha de piano no Mixkit, render HyperFrames (`template.html`) e composição FFmpeg `1080×1920`.
- `publish.py`: Publica na Meta Graph API com pré-checagem anti-spam (`5258005`) para evitar e-mails de falha caso a conta desenvolvedor aguarde confirmação.
- `.github/workflows/daily-reel.yml`: Executa o fluxo na nuvem e só atualiza `history.json` quando a publicação for concluída.

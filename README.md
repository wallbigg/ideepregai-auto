# CÓDIGO ZERO — Automação de Reels no Instagram (`@protocolocodigozero`)

Pipeline 100% gratuito na nuvem (**GitHub Actions**) que gera e publica Reels sobre o **CÓDIGO ZERO — O Protocolo Imersivo de 14 Dias (Método Z.E.R.O.)**, direcionando comentários `ZERO` e atendimento no WhatsApp `(12) 99659-3222`.

## Agenda automática (BRT = UTC-3, horários explícitos fora de pico)
12 horários diários espaçados em minuto `:23` para evitar bloqueio do agendador gratuito do GitHub e sobrecarga na Meta:
`07:23 · 09:23 · 11:23 · 13:23 · 15:23 · 17:23 · 18:23 · 19:23 · 20:23 · 21:23 · 23:23 · 01:23 BRT`

## Estrutura
- `main.py`: Gera roteiro inédito v3 via Gemini API (com acervo curado de 18 roteiros do produto), voz feminina emocional `Sulafat` via `gemini-2.5-flash-preview-tts` (fallback `pt-BR-FranciscaNeural`), sincronia palavra-a-palavra via `faster-whisper` (PCM float32) + fallback `silencedetect`, render HyperFrames `1080×1920` em 4 atos (`template.html`), trilha Mixkit com sidechain ducking e normalização `-14 LUFS`.
- `publish.py`: Consulta cota móvel `content_publishing_limit` e trava anti-bloqueio (`5258005`/rate-limit) na Meta Graph API sem falhar nem gerar e-mails de erro no GitHub.
- `.github/workflows/daily-reel.yml`: Roda em Node 24 nativo (`checkout@v7`, `cache@v6`, `setup-node@v7`, `setup-python@v7`, `action-gh-release@v3`) e só grava `history.json` após confirmação de publicação (`build/.published`).

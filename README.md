# ideepregai-auto

Automação diária 100% gratuita na nuvem (GitHub Actions) para gerar e publicar Reels cristãos no Instagram (`@wallasnascimento_`).

## O que roda todo dia às 09h (BRT)
1. **Agente Roteirista (`main.py`):** gera versículo inédito (checando `history.json`), gancho, 4 cards, narração e legenda humana via Gemini API.
2. **Agente de Áudio:** gera dublagem expressiva (`edge-tts`) e baixa piano real (Mixkit).
3. **Agente de Vídeo:** baixa B-roll real de natureza/céu, renderiza o motion graphics em `1080x1920` (HyperFrames + GSAP) e compõe tudo no FFmpeg.
4. **Agente Publicador (`publish.py`):** publica o Reel automaticamente pela Instagram Graph API oficial.

## Como ativar na nuvem em 3 passos
1. Crie um repositório no GitHub (público para minutos ilimitados grátis, ou privado com 2.000 min/mês grátis) e envie esta pasta (`git init && git add . && git commit -m "init" && git push`).
2. No GitHub, vá em **Settings → Secrets and variables → Actions** e adicione:
   - `GEMINI_API_KEY`: sua chave gratuita do Google AI Studio (`aistudio.google.com`).
   - `IG_USER_ID`: ID da sua conta Profissional/Criador do Instagram.
   - `IG_ACCESS_TOKEN`: Token de longa duração da Meta Graph API (com permissões `instagram_basic` e `instagram_content_publish`).
3. Pronto! Vá na aba **Actions** → **Daily Christian Reel** → **Run workflow** para testar na hora, ou deixe rodar todo dia às 09:00 BRT automaticamente.

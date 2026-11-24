import argparse
import base64
import json
import os
import queue
import random
import re
import shutil
import subprocess
import tempfile
import textwrap
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

import main as cz_main

ROOT = Path(__file__).parent
ASSETS_DIR = ROOT / "assets"
LIVE_ASSETS_DIR = ASSETS_DIR / "live"
BUILD_DIR = ROOT / "build"
BUILD_DIR.mkdir(exist_ok=True)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()

# 12 dilemas reais pós-término (6 masculinos, 6 femininos) para garantir ritmo zero-silêncio 24h
LIVE_DILEMMAS: list[dict] = [
    {
        "audience": "masculino",
        "handle": "@lucas_m",
        "question": "Ela mandou 'tá acordado?' às 02h14 depois de um mês sumida. O que eu respondo?",
        "mentor_reply": "Lucas, isso é teste de ego de madrugada, não é saudade. Se você responder agora, entrega validação de graça e volta pro banco de reservas.",
        "mentora_reply": "Do lado feminino, mensagem de duas palavras de madrugada mede se você ainda obedece ao toque. O silêncio hoje te devolve o valor inteiro.",
        "verdict": "SILÊNCIO ESTRATÉGICO • ESCUDO #01",
        "cta_line": "Esse é o Escudo #01. Protocolo completo 14 Dias + 16 scripts por R$ 47 no link da bio ou comente ZERO. Mande uma Rosa pra furar a fila!",
    },
    {
        "audience": "feminino",
        "handle": "@camila_r",
        "question": "Ele apagou uma mensagem no WhatsApp meia-noite e não disse nada. Pergunto o que era?",
        "mentor_reply": "Camila, homem maduro quando quer falar de verdade escreve claro e sustenta. Apagar texto de madrugada é isca pura de curiosidade.",
        "mentora_reply": "Perguntar o que ele apagou mostra que sua mente ainda gira em volta dele. Feche o aplicativo e deixe o mistério morrer sozinho.",
        "verdict": "CORTANDO A ISCA • ESCUDO #04",
        "cta_line": "No Código Zero por R$ 47 você tem os 16 jogos de mensagem explicados. Link na bio e siga o perfil.",
    },
    {
        "audience": "masculino",
        "handle": "@rafael_s",
        "question": "Ela pediu 'um tempo pra pensar' dizendo que ainda gosta de mim. Espero?",
        "mentor_reply": "Rafael, pedir tempo tentando deixar você em espera é divórcio em câmera lenta. Aceite numa frase curta e siga sua vida hoje.",
        "mentora_reply": "Quando você recua com calma e para de cobrar decisão, a mulher sente o peso real da ausência em vez de sufoco.",
        "verdict": "POSTURA SEM ESPERA • ESCUDO #07",
        "cta_line": "Pegue o roteiro exato de resposta seca no Protocolo 14 Dias por R$ 47. Link na bio ou mande uma Rosa pra furar a fila.",
    },
    {
        "audience": "feminino",
        "handle": "@marina_p",
        "question": "Ele curtiu três fotos antigas minhas às 23h mas não me chamou. Curto algo de volta?",
        "mentor_reply": "Marina, curtida sem conversa é o menor esforço possível na face da terra. O homem que quer te ver cria motivo e chama.",
        "mentora_reply": "Curtir de volta recompensa migalha digital. Continue vivendo fora da tela e não entregue um segundo da sua noite pra clique solto.",
        "verdict": "ZERO REAÇÃO A MIGALHAS • ESCUDO #02",
        "cta_line": "Quer parar de cair em sinal ambíguo? O Protocolo Código Zero tá no link da bio por R$ 47.",
    },
    {
        "audience": "masculino",
        "handle": "@bruno_t",
        "question": "Tô há 4 dias sem mandar nada e o peito tá apertando agora. Faço um textão pra encerrar bem?",
        "mentor_reply": "Bruno, isso no seu peito não é intuição, é abstinência química igual largar café forte. Textão de despedida só gera arrependimento amanhã.",
        "mentora_reply": "Aguenta noventa segundos respirando fundo e trava o celular por quinze minutos. Quem vai dormir inteiro hoje acorda respeitando a si mesmo.",
        "verdict": "REGRA 90–15 CONTRA RECAÍDA",
        "cta_line": "Use o cronômetro anti-recaída da Central SOS por R$ 47 agora. Link na bio e siga pra participar ao vivo.",
    },
    {
        "audience": "feminino",
        "handle": "@larissa_v",
        "question": "Ele disse 'vamos continuar amigos, não quero te perder da minha vida'. Aceito?",
        "mentor_reply": "Larissa, amizade logo após o término alivia a culpa dele por ter saído, enquanto segura você presa vendo ele seguir a vida.",
        "mentora_reply": "Fale com educação que precisa do seu espaço completo agora e corte o contato diário. Quem não te assume por inteiro não leva seu tempo de graça.",
        "verdict": "SEM AMIZADE DE RESERVA • ESCUDO #09",
        "cta_line": "Copie o Script #09 completo por R$ 47 no link da bio e siga o perfil.",
    },
    {
        "audience": "masculino",
        "handle": "@thiago_c",
        "question": "Ela mandou que vai passar pra pegar uma blusa que ficou aqui em casa. Chamo pra conversar?",
        "mentor_reply": "Thiago, se você transformar entrega de roupa em DR na sala, ela sai aliviada por ter ido embora. Deixe na portaria com zero drama.",
        "mentora_reply": "Entrega rápida, cordial e objetiva quebra toda a expectativa de ver você abalado e desperta respeito imediato.",
        "verdict": "LOGÍSTICA ZERO DRAMA • ESCUDO #05",
        "cta_line": "O Script #05 e os 16 escudos completos tão por R$ 47 no link da bio. Mande uma Rosa pra furar a fila.",
    },
    {
        "audience": "feminino",
        "handle": "@julia_f",
        "question": "Descobri que ele já tá saindo com outra duas semanas depois. Mando mensagem jogando na cara?",
        "mentor_reply": "Júlia, rebote em duas semanas é anestesia emocional barata, não amor novo. Se você explodir no WhatsApp, vira a ex descontrolada na história.",
        "mentora_reply": "Silêncio absoluto é a resposta mais pesada que existe. Guarde sua raiva pro treino, feche o ciclo e volte pro seu eixo.",
        "verdict": "DIGNIDADE BLINDADA NO SILÊNCIO",
        "cta_line": "Comece o Dia 1 da desintoxicação emocional agora por R$ 47. Link na bio ou comente ZERO.",
    },
    {
        "audience": "masculino",
        "handle": "@mateus_g",
        "question": "Ela me deu block e desbloqueou três dias depois, mas não falou nada. O que significa?",
        "mentor_reply": "Mateus, desbloqueio silencioso é porta entreaberta esperando você correr atrás pra matar a dúvida. Não bata nessa porta.",
        "mentora_reply": "Se ela abriu caminho, quem fechou tem que saber falar como adulta. Mantenha o seu silêncio e sua rotina intacta.",
        "verdict": "PORTA ABERTA NÃO É CONVITE • ESCUDO #11",
        "cta_line": "Os 16 Escudos e o Diário de 14 Dias tão por R$ 47 no link da bio. Siga o perfil!",
    },
    {
        "audience": "feminino",
        "handle": "@beatriz_n",
        "question": "Ele mandou meme engraçado dizendo 'lembrei de você vendo isso'. Posso puxar assunto?",
        "mentor_reply": "Beatriz, meme é atalho sem risco pra voltar pro seu radar sem assumir erro nenhum. Se você alonga papo, entrega tudo fácil.",
        "mentora_reply": "Se responder, mande apenas duas palavras secas sem pergunta de volta e encerre ali. Você vale conversa de verdade, não figurinha.",
        "verdict": "RESPOSTA CURTA SEM GANCHO • ESCUDO #03",
        "cta_line": "Pegue os 16 Scripts Anti-Vácuo por R$ 47 no link da bio e mande uma Rosa pra ter sua história analisada.",
    },
    {
        "audience": "masculino",
        "handle": "@diego_a",
        "question": "Tentei o contato zero mas fiquei olhando os stories dela por outra conta. Estraguei tudo?",
        "mentor_reply": "Diego, você não quebrou com ela, mas zerou o próprio cérebro com pico de cortisol. Apague a conta fake hoje à noite.",
        "mentora_reply": "Sem culpar o passado: recomece o cronômetro agora e substitua cada checada pela trava de quinze minutos do protocolo.",
        "verdict": "STALKING É ZERO CONTATO ZERO",
        "cta_line": "Pegue o Protocolo + Central SOS de 15 min por R$ 47 no link da bio agora.",
    },
    {
        "audience": "feminino",
        "handle": "@carol_l",
        "question": "Ele sumiu sem dar explicação depois de meses juntos. Vou atrás exigir fechamento?",
        "mentor_reply": "Carol, a falta de respeito já foi a resposta inteira dele. Quem some sem diálogo mostra exatamente como trataria seu futuro.",
        "mentora_reply": "Fechamento quem dá é você, fechando a porta por dentro e escolhendo paz acima de curiosidade.",
        "verdict": "AUSÊNCIA É RESPOSTA • ESCUDO #16",
        "cta_line": "Ative seu Protocolo Imersivo de 14 Dias por R$ 47 no link da bio ou comente ZERO.",
    },
]


def _pick_font_path(bold: bool = True) -> str:
    """Seleciona fonte TrueType válida no Windows ou Linux com path escapado para FFmpeg drawtext."""
    if os.name == "nt":
        candidates = (
            ["C:/Windows/Fonts/segoeuib.ttf", "C:/Windows/Fonts/arialbd.ttf"]
            if bold
            else ["C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/arial.ttf"]
        )
    else:
        candidates = (
            [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            ]
            if bold
            else [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            ]
        )
    for c in candidates:
        if Path(c).exists():
            return c.replace("\\", "/").replace(":", "\\:")
    raise FileNotFoundError(f"Nenhuma fonte TrueType encontrada entre {candidates}")


def _escape_ffmpeg_path(p: Path) -> str:
    return str(p.resolve()).replace("\\", "/").replace(":", "\\:")


def generate_live_reply(handle: str, question: str) -> dict:
    """Gera resposta dupla cirúrgica (Mentor + Mentora Zero) via Gemini ou acervo curado."""
    clean_handle = handle if handle.startswith("@") else f"@{handle}"
    clean_q = re.sub(r"\s+", " ", question).strip()[:160]

    if GEMINI_API_KEY and clean_q:
        prompt = f"""
Você dirige a live interativa de alta conversão "DUPLA ZERO" (produto CÓDIGO ZERO: Protocolo Imersivo 14 Dias, Central SOS e 16 Scripts para superar término e manter contato zero).
Um espectador real comentou na live:
Usuário: {clean_handle}
Pergunta/desabafo: "{clean_q}"

Responda no papel de DOIS mentores diretos, humanos e implacáveis contra recaídas:
1) `mentor_reply`: Visão masculina prática (máximo 24 palavras, fale o primeiro nome ou arroba sem símbolos estranhos, linguagem natural do Brasil, zero papo de coach genérico).
2) `mentora_reply`: Visão feminina cortante e de valor próprio (máximo 24 palavras, mostre a realidade psicológica e a postura adulta imediata).
3) `verdict`: Selo curto em CAPS (máximo 36 caracteres, ex: "SILÊNCIO ESTRATÉGICO • ESCUDO #01").
4) `cta_line`: Chamada curta e magnética (máximo 16 palavras) apontando para "link da bio" ou "comente ZERO".

Regras rígidas: Português do Brasil natural; ZERO travessões "—"; ZERO promessas falsas; foco total em dignidade e conversão na Kiwify.
Retorne APENAS JSON válido com: handle, question, mentor_reply, mentora_reply, verdict, cta_line.
"""
        body = json.dumps({
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseMimeType": "application/json", "temperature": 0.75},
        }).encode("utf-8")
        for model in ("gemini-2.5-flash", "gemini-2.5-flash-lite"):
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
            try:
                req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=22) as resp:
                    res = json.loads(resp.read().decode("utf-8"))
                raw = res["candidates"][0]["content"]["parts"][0]["text"].strip()
                raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.I)
                parsed = json.loads(raw)
                if all(parsed.get(k) for k in ("mentor_reply", "mentora_reply", "verdict")):
                    return {
                        "handle": clean_handle,
                        "question": clean_q,
                        "mentor_reply": str(parsed["mentor_reply"]).replace("—", ",").strip(),
                        "mentora_reply": str(parsed["mentora_reply"]).replace("—", ",").strip(),
                        "verdict": str(parsed["verdict"]).upper()[:38],
                        "cta_line": str(parsed.get("cta_line") or "Protocolo completo no link da bio ou comente ZERO.").replace("—", ","),
                    }
            except Exception as exc:
                print(f"Aviso Gemini Live reply ({model}): {exc}")

    # Fallback local inteligente a partir do acervo curado
    lowered = clean_q.lower()
    if any(k in lowered for k in ("tempo", "pensar", "amigos", "amizade")):
        base = LIVE_DILEMMAS[2]
    elif any(k in lowered for k in ("apagou", "apagada", "curtiu", "story", "stories")):
        base = LIVE_DILEMMAS[1]
    elif any(k in lowered for k in ("block", "bloqueou", "sumiu")):
        base = LIVE_DILEMMAS[8]
    else:
        base = random.choice(LIVE_DILEMMAS)

    return {
        "handle": clean_handle,
        "question": clean_q or base["question"],
        "mentor_reply": base["mentor_reply"],
        "mentora_reply": base["mentora_reply"],
        "verdict": base["verdict"],
        "cta_line": base["cta_line"],
    }


def _synthesize_windows_local_tts(text: str, role: str, out_mp3: Path) -> float:
    """Fallback local offline em Windows usando System.Speech (apenas caminhos absolutos no .NET)."""
    abs_wav = (out_mp3.parent / f"{out_mp3.stem}_win.wav").resolve()
    abs_raw = (out_mp3.parent / f"{out_mp3.stem}_winraw.mp3").resolve()
    ps_script = (out_mp3.parent / f"{out_mp3.stem}_tts.ps1").resolve()
    clean_text = text.replace('"', "'").replace("\n", " ").strip()
    rate = "1" if role == "mentor" else "2"
    ps_code = (
        "Add-Type -AssemblyName System.Speech\n"
        "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer\n"
        f"$s.Rate = {rate}\n"
        "$voices = $s.GetInstalledVoices() | Where-Object { $_.VoiceInfo.Culture.Name -like 'pt*' }\n"
        "if ($voices.Count -gt 0) { $s.SelectVoice($voices[0].VoiceInfo.Name) }\n"
        f"$s.SetOutputToWaveFile('{abs_wav}')\n"
        f"$s.Speak(\"{clean_text}\")\n"
        "$s.Dispose()\n"
    )
    ps_script.write_text(ps_code, encoding="utf-8")
    subprocess.check_call(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ps_script)])
    subprocess.check_call([
        "ffmpeg", "-y", "-v", "error", "-i", str(abs_wav),
        "-c:a", "libmp3lame", "-q:a", "2", "-ar", "44100", "-ac", "2", str(abs_raw),
    ])
    return cz_main._postprocess_voice(abs_raw, out_mp3)


def synthesize_speaker_audio(text: str, role: str, out_mp3: Path) -> float:
    """
    Sintetiza fala humana expressiva com vozes distintas:
      - mentor  -> masculino (Fenrir / Enceladus / AntonioNeural)
      - mentora -> feminino  (Sulafat / Aoede / ThalitaMultilingualNeural)
    """
    voice_gender = "masculino" if role == "mentor" else "feminino"
    profile = cz_main.VOICE_PROFILES[voice_gender]
    raw_mp3 = (out_mp3.parent / f"{out_mp3.stem}_raw.mp3").resolve()
    pcm_path = (out_mp3.parent / f"{out_mp3.stem}_raw.pcm").resolve()

    if GEMINI_API_KEY:
        direction = (
            "Ator brasileiro respondendo ao vivo em um estúdio de madrugada: direto, calmo, firme e humano."
            if role == "mentor"
            else "Atriz brasileira co-apresentadora ao vivo em um estúdio de madrugada: lúcida, acolhedora e incisiva."
        )
        tts_prompt = f"{profile['audio_profile']}\n## CONTEXTO AO VIVO\n{direction}\n\n## FALA:\n{text}"
        voices = profile["gemini_voices"][:]
        for model in ("gemini-2.5-flash-preview-tts", "gemini-2.5-flash-tts"):
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
            for vname in voices:
                payload = json.dumps({
                    "contents": [{"parts": [{"text": tts_prompt}]}],
                    "generationConfig": {
                        "responseModalities": ["AUDIO"],
                        "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": vname}}},
                    },
                }).encode("utf-8")
                try:
                    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
                    with urllib.request.urlopen(req, timeout=35) as resp:
                        res = json.loads(resp.read().decode("utf-8"))
                    parts = res["candidates"][0]["content"]["parts"]
                    inline = next((p.get("inlineData") or p.get("inline_data") for p in parts if p.get("inlineData") or p.get("inline_data")), None)
                    if not inline or not inline.get("data"):
                        raise RuntimeError("Resposta sem áudio inline")
                    audio_bytes = base64.b64decode(inline["data"])
                    rate_m = re.search(r"rate=(\d+)", inline.get("mimeType") or "audio/L16;rate=24000")
                    sr = int(rate_m.group(1)) if rate_m else 24000
                    pcm_path.write_bytes(audio_bytes)
                    subprocess.check_call([
                        "ffmpeg", "-y", "-v", "error", "-f", "s16le", "-ar", str(sr), "-ac", "1",
                        "-i", str(pcm_path), "-c:a", "libmp3lame", "-q:a", "2", "-ar", "44100", "-ac", "2", str(raw_mp3),
                    ])
                    return cz_main._postprocess_voice(raw_mp3, out_mp3)
                except Exception as exc:
                    print(f"Aviso Gemini Live TTS ({role}/{model}/{vname}): {exc}")

    # Tenta edge-tts Python SDK (nunca trava se offline em Windows quando faz fallback pro .NET local)
    try:
        import asyncio
        import edge_tts

        ev = profile["edge_voices"][0]

        async def _run() -> None:
            comm = edge_tts.Communicate(text=text, voice=ev, rate=profile["edge_rate"], pitch=profile["edge_pitch"])
            await comm.save(str(raw_mp3))

        asyncio.run(_run())
        if raw_mp3.exists() and raw_mp3.stat().st_size > 4_000:
            return cz_main._postprocess_voice(raw_mp3, out_mp3)
    except Exception as exc:
        print(f"Aviso edge_tts ({role}): {exc}")

    if os.name == "nt":
        return _synthesize_windows_local_tts(text, role, out_mp3)

    raise RuntimeError(f"Falha ao sintetizar áudio para {role}: configure GEMINI_API_KEY ou edge-tts.")


def _write_wrapped_textfile(path: Path, text: str, width: int = 38) -> str:
    wrapped = textwrap.fill(re.sub(r"\s+", " ", text).strip(), width=width)
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(wrapped)
    return _escape_ffmpeg_path(path)


def render_turn_segment(
    dilemma: dict,
    seg_dir: Path,
    out_mp4: Path,
    cta_text: str = "CÓDIGO ZERO R$ 47 • LINK NA BIO",
) -> tuple[Path, float]:
    """
    Renderiza um bloco completo da Dupla Zero (1080x1920 30fps):
      - Parte A: Mentor Zero (visão masculina) respondendo o @ do chat
      - Parte B: Mentora Zero (visão feminina) entregando o veredito + CTA
      - Waveform dourada ao vivo, caixa de comentário real e mix -14 LUFS com cinema_piano.mp3
    """
    seg_dir.mkdir(parents=True, exist_ok=True)
    mentor_img = LIVE_ASSETS_DIR / "mentor_zero.png"
    mentora_img = LIVE_ASSETS_DIR / "mentora_zero.png"
    if not (mentor_img.exists() and mentora_img.exists()):
        raise FileNotFoundError("Retratos assets/live/mentor_zero.png e mentora_zero.png são obrigatórios.")

    mentor_mp3 = seg_dir / "voice_mentor.mp3"
    mentora_mp3 = seg_dir / "voice_mentora.mp3"
    gap_wav = seg_dir / "gap.wav"
    turn_audio = seg_dir / "turn_audio.wav"

    mentor_script = dilemma["mentor_reply"]
    mentora_script = f"{dilemma['mentora_reply']} {dilemma.get('cta_line', '')}".strip()

    t_mentor = synthesize_speaker_audio(mentor_script, "mentor", mentor_mp3)
    t_mentora = synthesize_speaker_audio(mentora_script, "mentora", mentora_mp3)

    gap_dur = 0.35
    delay_start = 0.20
    t_switch = round(delay_start + t_mentor + 0.18, 2)
    total_dur = round(delay_start + t_mentor + gap_dur + t_mentora + 0.45, 2)

    subprocess.check_call([
        "ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", f"anullsrc=r=44100:cl=stereo:d={gap_dur}",
        str(gap_wav),
    ])

    music_bed = ASSETS_DIR / "music" / "cinema_piano.mp3"
    pop_sfx = ASSETS_DIR / "sfx" / "pop-back.mp3"
    if not music_bed.exists():
        music_bed = next((ASSETS_DIR / "music").glob("*.mp3"), None)

    mix_cmd = ["ffmpeg", "-y", "-v", "error", "-i", str(mentor_mp3), "-i", str(gap_wav), "-i", str(mentora_mp3)]
    mix_parts = [
        f"[0:a]aformat=sample_rates=44100:channel_layouts=stereo,adelay={int(delay_start * 1000)}|{int(delay_start * 1000)}[va]",
        "[1:a]aformat=sample_rates=44100:channel_layouts=stereo[vg]",
        "[2:a]aformat=sample_rates=44100:channel_layouts=stereo[vb]",
        "[va][vg][vb]concat=n=3:v=0:a=1,"
        "highpass=f=85,equalizer=f=3200:t=q:w=1.4:g=2.0,"
        "acompressor=threshold=-17dB:ratio=2.5:attack=6:release=60,volume=1.50,"
        f"apad=whole_dur={total_dur},asplit=2[vmain][vsc]",
    ]
    amix_inputs = ["[vmain]"]
    next_idx = 3

    if music_bed and music_bed.exists():
        mix_cmd.extend(["-stream_loop", "-1", "-i", str(music_bed)])
        m_idx = next_idx
        next_idx += 1
        fade_out_st = max(1.0, total_dur - 0.6)
        mix_parts.append(
            f"[{m_idx}:a]aformat=sample_rates=44100:channel_layouts=stereo,atrim=0:{total_dur},asetpts=PTS-STARTPTS,"
            f"afade=t=in:st=0:d=0.4,afade=t=out:st={fade_out_st}:d=0.6,volume=0.22[bgmraw]"
        )
        mix_parts.append("[bgmraw][vsc]sidechaincompress=threshold=0.03:ratio=4.5:attack=20:release=260[bgmduck]")
        amix_inputs.append("[bgmduck]")

    if pop_sfx.exists():
        mix_cmd.extend(["-i", str(pop_sfx)])
        p_idx = next_idx
        next_idx += 1
        mix_parts.append(f"[{p_idx}:a]aformat=sample_rates=44100:channel_layouts=stereo,volume=0.28,adelay=120|120[pop]")
        amix_inputs.append("[pop]")

    mix_parts.append(
        f"{''.join(amix_inputs)}amix=inputs={len(amix_inputs)}:duration=first:normalize=0,"
        "loudnorm=I=-14:TP=-1.5:LRA=7,alimiter=limit=0.95[aout]"
    )
    mix_cmd.extend([
        "-filter_complex", ";".join(mix_parts),
        "-map", "[aout]", "-ar", "44100", "-ac", "2", "-t", str(total_dur), str(turn_audio),
    ])
    subprocess.check_call(mix_cmd)

    # Prepara arquivos UTF-8 seguros para drawtext
    font_bold = _pick_font_path(bold=True)
    font_reg = _pick_font_path(bold=False)

    tf_live = _write_wrapped_textfile(seg_dir / "t_live.txt", "AO VIVO", width=20)
    tf_show = _write_wrapped_textfile(seg_dir / "t_show.txt", "DUPLA ZERO • PLANTÃO SOS", width=32)
    tf_handle = _write_wrapped_textfile(seg_dir / "t_handle.txt", f"PERGUNTA DE {dilemma['handle']}", width=40)
    tf_q = _write_wrapped_textfile(seg_dir / "t_q.txt", f"\"{dilemma['question']}\"", width=46)

    tf_sp_a = _write_wrapped_textfile(seg_dir / "t_spa.txt", "MENTOR ZERO • VISÃO MASCULINA", width=40)
    tf_sp_b = _write_wrapped_textfile(seg_dir / "t_spb.txt", "MENTORA ZERO • VISÃO FEMININA", width=40)
    tf_verd = _write_wrapped_textfile(seg_dir / "t_verd.txt", dilemma["verdict"], width=42)
    tf_cta_top = _write_wrapped_textfile(seg_dir / "t_ctat.txt", "CÓDIGO ZERO • PROTOCOLO 14 DIAS + 16 SCRIPTS", width=48)
    tf_cta_bot = _write_wrapped_textfile(seg_dir / "t_ctab.txt", cta_text, width=40)

    part_b_dur = round(max(1.0, total_dur - t_switch), 2)

    filter_parts = [
        # Câmeras vivas sutis em 1080x1920 + corte direto Mentor -> Mentora na batida da fala
        f"[0:v]scale=1136:2020:force_original_aspect_ratio=increase,crop=1080:1920:"
        f"x='(iw-1080)/2+10*sin(t*0.5)':y='(ih-1920)/2+6*cos(t*0.35)',setsar=1,"
        f"eq=contrast=1.06:saturation=1.04[v0]",
        f"[1:v]scale=1136:2020:force_original_aspect_ratio=increase,crop=1080:1920:"
        f"x='(iw-1080)/2-10*sin(t*0.5)':y='(ih-1920)/2+6*cos(t*0.35)',setsar=1,"
        f"eq=contrast=1.06:saturation=1.04[v1]",
        f"[v0][v1]concat=n=2:v=1:a=0,format=rgba,"
        # Faixas de contraste sutil no topo (y=0..410) e base (y=1225..1920)
        "drawbox=x=0:y=0:w=1080:h=410:color=0x06070B@0.42:t=fill,"
        "drawbox=x=0:y=1225:w=1080:h=695:color=0x06070B@0.58:t=fill,"
        # Top LIVE badge & Show badge (abaixo da interface de live do celular y=152)
        "drawbox=x=64:y=152:w=172:h=50:color=0xE11D48@0.96:t=fill,"
        f"drawtext=fontfile='{font_bold}':textfile='{tf_live}':fontcolor=0xFFFFFF:fontsize=25:x=88:y=164,"
        "drawbox=x=248:y=152:w=440:h=50:color=0x11141F@0.88:t=fill,"
        f"drawtext=fontfile='{font_bold}':textfile='{tf_show}':fontcolor=0xF5B73B:fontsize=22:x=270:y=165,"
        # Cartão de Pergunta Real do Chat (y=218..388 -> 100% livre acima do rosto)
        "drawbox=x=64:y=218:w=952:h=170:color=0x0B0D14@0.88:t=fill,"
        "drawbox=x=64:y=218:w=9:h=170:color=0xF5B73B@1.0:t=fill,"
        f"drawtext=fontfile='{font_bold}':textfile='{tf_handle}':fontcolor=0xF5B73B:fontsize=24:x=96:y=236,"
        f"drawtext=fontfile='{font_reg}':textfile='{tf_q}':fontcolor=0xFFFFFF:fontsize=30:line_spacing=6:x=96:y=272,"
        # Speaker Badge alternando Mentor / Mentora exatamente no instante t_switch
        "drawbox=x=64:y=1254:w=952:h=120:color=0x0B0D14@0.88:t=fill,"
        f"drawbox=x=64:y=1254:w=9:h=120:color=0xF5B73B@1.0:t=fill:enable='lt(t,{t_switch})',"
        f"drawbox=x=64:y=1254:w=9:h=120:color=0xE11D48@1.0:t=fill:enable='gte(t,{t_switch})',"
        f"drawtext=fontfile='{font_bold}':textfile='{tf_sp_a}':fontcolor=0xF5B73B:fontsize=27:x=96:y=1272:enable='lt(t,{t_switch})',"
        f"drawtext=fontfile='{font_bold}':textfile='{tf_sp_b}':fontcolor=0xFFFFFF:fontsize=27:x=96:y=1272:enable='gte(t,{t_switch})',"
        f"drawtext=fontfile='{font_bold}':textfile='{tf_verd}':fontcolor=0xF5B73B:fontsize=30:x=96:y=1316,"
        # Fundo da Waveform Dourada (y=1392..1480)
        "drawbox=x=64:y=1392:w=952:h=88:color=0x0B0D14@0.84:t=fill,"
        # Banner fixo de Conversão / Kiwify acima da zona de comentários do TikTok/IG (y=1498..1624)
        "drawbox=x=64:y=1498:w=952:h=126:color=0x141008@0.92:t=fill,"
        "drawbox=x=64:y=1498:w=952:h=4:color=0xF5B73B@0.95:t=fill,"
        f"drawtext=fontfile='{font_bold}':textfile='{tf_cta_top}':fontcolor=0xF5B73B:fontsize=23:x=(w-text_w)/2:y=1518,"
        f"drawtext=fontfile='{font_bold}':textfile='{tf_cta_bot}':fontcolor=0xFFFFFF:fontsize=34:x=(w-text_w)/2:y=1558[hud]",
        # Waveform dourada sólida reativa ao áudio em tempo real
        "[2:a]aformat=channel_layouts=mono,showwaves=s=888x72:mode=cline:colors=gold:draw=full:scale=sqrt:rate=30,format=rgba[wave]",
        "[hud][wave]overlay=96:1400:shortest=1,format=yuv420p[vout]",
    ]

    subprocess.check_call([
        "ffmpeg", "-y", "-v", "error",
        "-loop", "1", "-framerate", "30", "-t", str(t_switch), "-i", str(mentor_img),
        "-loop", "1", "-framerate", "30", "-t", str(part_b_dur), "-i", str(mentora_img),
        "-i", str(turn_audio),
        "-filter_complex", ";".join(filter_parts),
        "-map", "[vout]", "-map", "2:a",
        "-c:v", "libx264", "-preset", "veryfast", "-b:v", "2800k", "-maxrate", "2800k", "-bufsize", "5600k",
        "-r", "30", "-g", "60", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k", "-ar", "44100", "-ac", "2",
        "-shortest", "-t", str(total_dur), str(out_mp4),
    ])
    return out_mp4, total_dur


class LiveChatQueue:
    """Leitor assíncrono opcional de comentários, presentes (fura-fila) e novos seguidores do TikTok LIVE."""

    def __init__(self, unique_id: str) -> None:
        self.unique_id = unique_id.lstrip("@").strip()
        self.priority_items: queue.Queue[tuple[str, str]] = queue.Queue(maxsize=15)
        self.items: queue.Queue[tuple[str, str]] = queue.Queue(maxsize=25)
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._last_follow_ack = 0.0

    def start(self) -> None:
        if not self.unique_id:
            return
        try:
            import TikTokLive  # noqa: F401
        except Exception:
            print("TikTokLive não instalado; live rodará com fila inteligente do acervo Dupla Zero.")
            return
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()

    def pop_question(self) -> tuple[str, str] | None:
        try:
            return self.priority_items.get_nowait()
        except queue.Empty:
            pass
        try:
            return self.items.get_nowait()
        except queue.Empty:
            return None

    def _run(self) -> None:
        import asyncio
        from TikTokLive import TikTokLiveClient
        from TikTokLive.events import CommentEvent

        try:
            from TikTokLive.events import GiftEvent  # type: ignore
        except Exception:
            GiftEvent = None
        try:
            from TikTokLive.events import FollowEvent  # type: ignore
        except Exception:
            FollowEvent = None

        async def _listen() -> None:
            while not self._stop.is_set():
                try:
                    client = TikTokLiveClient(unique_id=self.unique_id)

                    @client.on(CommentEvent)
                    async def on_comment(event: CommentEvent) -> None:
                        comment = (event.comment or "").strip()
                        if len(comment) < 8:
                            return
                        if comment.lower() in {"oi", "olá", "ola", "top", "bom dia", "boa noite", "zero"}:
                            return
                        user_name = getattr(event.user, "unique_id", None) or getattr(event.user, "nickname", "visitante")
                        try:
                            self.items.put_nowait((f"@{user_name}", comment))
                        except queue.Full:
                            pass

                    if GiftEvent is not None:
                        @client.on(GiftEvent)
                        async def on_gift(event) -> None:
                            user_name = getattr(event.user, "unique_id", None) or getattr(event.user, "nickname", "apoiador")
                            gift_name = getattr(getattr(event, "gift", None), "name", None) or "presente"
                            prompt_msg = f"OBRIGADO PELO PRESENTE ({gift_name}), @{user_name}! Fura-fila ativado — qual é a sua história hoje?"
                            try:
                                self.priority_items.put_nowait((f"@{user_name}", prompt_msg))
                            except queue.Full:
                                pass

                    if FollowEvent is not None:
                        @client.on(FollowEvent)
                        async def on_follow(event) -> None:
                            now = time.monotonic()
                            if now - self._last_follow_ack < 180.0:
                                return
                            self._last_follow_ack = now
                            user_name = getattr(event.user, "unique_id", None) or getattr(event.user, "nickname", "visitante")
                            msg = f"Novo seguidor @{user_name} entrou agora! Qual pergunta de término você quer fazer pra Dupla Zero?"
                            try:
                                self.items.put_nowait((f"@{user_name}", msg))
                            except queue.Full:
                                pass

                    await client.connect()
                except Exception as exc:
                    print(f"Monitor TikTokLive aguardando live ativa de @{self.unique_id}: {exc}")
                await asyncio.sleep(15)

        asyncio.run(_listen())


def stream_rtmp_loop(rtmp_url: str, max_minutes: int, tiktok_user: str, cta_text: str) -> None:
    """
    Mantém UMA conexão RTMP contínua com `ffmpeg -f mpegts -i pipe:0 -c copy -f flv`,
    pré-renderizando o próximo bloco da Dupla Zero em paralelo enquanto o bloco atual transmite ao vivo.
    """
    chat = LiveChatQueue(tiktok_user)
    chat.start()

    pool = LIVE_DILEMMAS[:]
    random.shuffle(pool)
    idx = 0

    def _next_dilemma() -> dict:
        nonlocal idx
        live_msg = chat.pop_question()
        if live_msg:
            handle, q = live_msg
            print(f"[CHAT AO VIVO] {handle}: {q}")
            return generate_live_reply(handle, q)
        d = pool[idx % len(pool)]
        idx += 1
        return d

    work_dir = Path(tempfile.mkdtemp(prefix="dupla_zero_live_"))
    pusher: subprocess.Popen[bytes] | None = None
    cum_ts = 0.0
    deadline = time.monotonic() + max_minutes * 60

    try:
        # Pré-renderiza o turno 0 antes de abrir a transmissão
        first_mp4 = work_dir / "turn_0.mp4"
        _, first_dur = render_turn_segment(_next_dilemma(), work_dir / "seg_0", first_mp4, cta_text=cta_text)

        pusher = subprocess.Popen(
            [
                "ffmpeg", "-y", "-v", "warning",
                "-re", "-fflags", "+genpts+igndts",
                "-f", "mpegts", "-i", "pipe:0",
                "-c", "copy", "-bsf:a", "aac_adtstoasc",
                "-f", "flv", rtmp_url,
            ],
            stdin=subprocess.PIPE,
        )

        cur_mp4, cur_dur = first_mp4, first_dur
        turn_num = 0

        while time.monotonic() < deadline:
            next_box: dict = {}

            def _prep_next(tn: int) -> None:
                n_mp4 = work_dir / f"turn_{tn}.mp4"
                _, n_dur = render_turn_segment(_next_dilemma(), work_dir / f"seg_{tn}", n_mp4, cta_text=cta_text)
                next_box["mp4"] = n_mp4
                next_box["dur"] = n_dur

            prep_thread = threading.Thread(target=_prep_next, args=(turn_num + 1,), daemon=True)
            prep_thread.start()

            ts_file = work_dir / f"turn_{turn_num}.ts"
            subprocess.check_call([
                "ffmpeg", "-y", "-v", "error", "-i", str(cur_mp4),
                "-c", "copy", "-output_ts_offset", f"{cum_ts:.3f}",
                "-f", "mpegts", str(ts_file),
            ])
            cum_ts += cur_dur

            assert pusher.stdin is not None
            with ts_file.open("rb") as fh:
                while True:
                    chunk = fh.read(65536)
                    if not chunk:
                        break
                    pusher.stdin.write(chunk)
                    pusher.stdin.flush()

            prep_thread.join()
            shutil.rmtree(work_dir / f"seg_{turn_num}", ignore_errors=True)
            cur_mp4.unlink(missing_ok=True)
            ts_file.unlink(missing_ok=True)

            cur_mp4 = next_box["mp4"]
            cur_dur = next_box["dur"]
            turn_num += 1
    finally:
        chat.stop()
        if pusher and pusher.stdin:
            try:
                pusher.stdin.close()
            except Exception:
                pass
        if pusher:
            pusher.wait(timeout=15)
        shutil.rmtree(work_dir, ignore_errors=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="CÓDIGO ZERO — Dupla Zero Live Studio (RTMP Cloud)")
    parser.add_argument("--preview", action="store_true", help="Renderiza 1 rodada completa em build/live_preview.mp4")
    parser.add_argument("--rtmp-url", default=os.environ.get("LIVE_RTMP_URL", ""), help="URL RTMP + Stream Key da plataforma")
    parser.add_argument("--max-minutes", type=int, default=300, help="Duração máxima da transmissão contínua em minutos")
    parser.add_argument("--tiktok-user", default="", help="Usuário do TikTok para ler comentários em tempo real")
    parser.add_argument("--cta-text", default="CÓDIGO ZERO R$ 47 • LINK NA BIO", help="Chamada de conversão no rodapé")
    args = parser.parse_args()

    if args.preview:
        preview_dir = BUILD_DIR / "live_preview_work"
        out_mp4 = BUILD_DIR / "live_preview.mp4"
        _, dur = render_turn_segment(LIVE_DILEMMAS[0], preview_dir, out_mp4, cta_text=args.cta_text)
        print(f"Preview Dupla Zero renderizado: {out_mp4} ({dur:.2f}s)")
        return

    if not args.rtmp_url:
        raise SystemExit("Informe --rtmp-url ou a variável de ambiente LIVE_RTMP_URL para iniciar a transmissão.")

    stream_rtmp_loop(args.rtmp_url, args.max_minutes, args.tiktok_user, args.cta_text)


if __name__ == "__main__":
    main()

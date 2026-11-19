import json
import os
import random
import re
import subprocess
import time
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent
HISTORY_FILE = ROOT / "history.json"
BUILD_DIR = ROOT / "build"
BUILD_DIR.mkdir(exist_ok=True)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
VOICE = os.environ.get("TTS_VOICE", "pt-BR-ThalitaMultilingualNeural")
BROLL_TOPICS = ["clouds", "sunset", "sunlight", "nature", "sky", "ocean"]

# Banco resiliente de roteiros de alta qualidade para nunca travar a automação diária (se a API estiver indisponível/503)
CURATED_SCRIPTS = [
    {
        "verse": "Isaías 41:10",
        "pre1": "Não tenha medo",
        "text1": "Você não está lutando essa <span class='red'>batalha sozinho</span>.",
        "pre2": "A certeza divina",
        "text2": "O medo paralisa, mas a fé te <span class='gold'>sustenta</span>.",
        "pre3": "A promessa",
        "text3": "\"Não temas, porque eu sou contigo; não te assombres.\"",
        "pre4": "Receba a força",
        "text4": "Deus segura a sua mão em <span class='gold'>todo tempo</span>.",
        "narration": "Você não está lutando essa batalha sozinho! O medo paralisa, mas a fé te sustenta. Isaías quarenta e um dez diz: não temas, porque eu sou contigo! Deus segura a sua mão em todo tempo. Comente amém!",
        "caption": "Nos dias mais difíceis, lembre-se: a presença de Deus é maior que qualquer tempestade.\n\nVocê não precisa enfrentar o futuro com medo ou incerteza. Ele é o seu refúgio e quem renova suas forças quando você pensa que vai cair.\n\nSe você crê nessa promessa hoje, comente AMÉM e envie para alguém que precisa desse consolo. 🙏✨\n\nIsaías 41:10 | @wallasnascimento_ • ideepregai",
    },
    {
        "verse": "Salmos 46:1",
        "pre1": "Respire fundo",
        "text1": "O caos ao redor não define o seu <span class='red'>destino</span>.",
        "pre2": "Onde buscar refúgio",
        "text2": "O mundo traz ruído, mas Deus traz <span class='gold'>paz real</span>.",
        "pre3": "A promessa",
        "text3": "\"Deus é o nosso refúgio e fortaleza, socorro bem presente.\"",
        "pre4": "Descanse hoje",
        "text4": "Ele age em silêncio para te dar <span class='gold'>vitória</span>.",
        "narration": "O caos ao redor não define o seu destino! O mundo traz ruído, mas Deus traz paz real. O Salmo quarenta e seis declara: Deus é o nosso refúgio e fortaleza, socorro bem presente! Descanse nessa certeza. Comente amém!",
        "caption": "Quando tudo parecer agitado demais, encontre descanso no esconderijo do Altíssimo.\n\nDeus não abandona os Seus nos momentos de aflição; Ele é socorro imediato e fortaleza inabalável para quem n'Ele confia.\n\nReceba essa paz no seu coração hoje. Comente AMÉM e compartilhe essa luz! 🙏✨\n\nSalmos 46:1 | @wallasnascimento_ • ideepregai",
    },
    {
        "verse": "Filipenses 4:6-7",
        "pre1": "Pare e reflita",
        "text1": "A ansiedade não resolve o <span class='red'>dia de amanhã</span>.",
        "pre2": "A troca perfeita",
        "text2": "Troque a preocupação constante por <span class='gold'>oração</span>.",
        "pre3": "A promessa",
        "text3": "\"A paz de Deus, que excede o entendimento, guardará o seu coração.\"",
        "pre4": "Vitória certa",
        "text4": "A tempestade vai passar e a sua fé <span class='gold'>prevalecerá</span>.",
        "narration": "A ansiedade não resolve o dia de amanhã! Troque a preocupação por oração e entrega. Filipenses quatro diz: a paz de Deus, que excede todo entendimento, guardará o seu coração! Creia nessa paz. Comente amém!",
        "caption": "Não permita que a preocupação roube o milagre que Deus preparou para o seu dia.\n\nLeve tudo diante d'Ele em oração. O que foge do seu controle está perfeitamente debaixo da soberania do Pai.\n\nDeclare a sua confiança n'Ele hoje. Comente AMÉM! 🙏✨\n\nFilipenses 4:6-7 | @wallasnascimento_ • ideepregai",
    },
    {
        "verse": "Jeremias 29:11",
        "pre1": "Mensagem do céu",
        "text1": "O que parece o fim é apenas um novo <span class='gold'>começo</span>.",
        "pre2": "Planos maiores",
        "text2": "Deus não improvisa, Ele já traçou o seu <span class='gold'>propósito</span>.",
        "pre3": "A promessa",
        "text3": "\"Eu sei os planos que tenho para vocês: planos de paz e esperança.\"",
        "pre4": "Confie no caminho",
        "text4": "O melhor ainda está por vir na sua <span class='gold'>vida</span>.",
        "narration": "O que parece o fim é apenas o começo de um novo propósito! Jeremias vinte e nove onze promete: Eu sei os planos que tenho para vocês, planos de paz e esperança! Confie, o melhor ainda está por vir. Comente amém!",
        "caption": "Você não nasceu por acaso e os seus dias não são obras do acaso.\n\nO Senhor tem pensamentos de paz, futuro e esperança para a sua história. Mesmo quando você não compreende a jornada, confie no Autor da vida.\n\nSe você toma posse dessa esperança hoje, comente AMÉM e guarde essa palavra. 🙏✨\n\nJeremias 29:11 | @wallasnascimento_ • ideepregai",
    },
    {
        "verse": "Josué 1:9",
        "pre1": "Ouça essa voz",
        "text1": "A sua coragem não vem de você, vem de <span class='gold'>Deus</span>.",
        "pre2": "Vencendo a dúvida",
        "text2": "O obstáculo é grande, mas o Senhor é <span class='gold'>infinito</span>.",
        "pre3": "A promessa",
        "text3": "\"Seja forte e corajoso; o Senhor estará com você onde quer que for.\"",
        "pre4": "Siga em frente",
        "text4": "A promessa de Deus nunca falha e você vai <span class='gold'>vencer</span>.",
        "narration": "A sua coragem não vem da sua força, vem do Deus que te chamou! Josué um nove ordena: seja forte e corajoso, o Senhor estará com você por onde andar! Levante a cabeça e marche. Comente amém!",
        "caption": "A coragem cristã não é ausência de medo: é a certeza de que Deus caminha ao seu lado em cada passo.\n\nNão retroceda diante das tempestades. O Senhor que te chamou é fiel para te sustentar e te fazer prosperar.\n\nSe você recebe essa força espiritual hoje, comente AMÉM e compartilhe essa bênção! 🙏✨\n\nJosué 1:9 | @wallasnascimento_ • ideepregai",
    },
]


def load_history() -> dict:
    if HISTORY_FILE.exists():
        return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    return {"posted": []}


def save_history(data: dict) -> None:
    HISTORY_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def generate_script(posted_verses: list[str]) -> dict:
    """Tenta gerar via Gemini API; se houver instabilidade ou 503, usa o acervo de alta qualidade."""
    if GEMINI_API_KEY:
        prompt = f"""
Você é um roteirista cristão para o Instagram @wallasnascimento_ (ideepregai).
Crie um Reel de 15 segundos com um versículo diferente destes já postados: {posted_verses}.
Regras:
- Linguagem humana, natural, acolhedora e firme (sem clichês de IA, sem travessões, sem "pare de rolar").
- 4 blocos curtos para caber em 15 segundos de narração natural.
- Retorne APENAS JSON válido neste formato exato:
{{
  "verse": "Livro Capítulo:Versículo",
  "pre1": "subtítulo curto 1 (2-4 palavras)",
  "text1": "Gancho forte com <span class='red'>destaque</span> (max 8 palavras)",
  "pre2": "subtítulo curto 2",
  "text2": "Tensão ou dor real com <span class='red'>destaque</span> (max 9 palavras)",
  "pre3": "A promessa",
  "text3": "Trecho fiel e curto do versículo entre aspas (max 12 palavras)",
  "pre4": "subtítulo curto 4",
  "text4": "Conclusão com <span class='gold'>esperança</span> (max 9 palavras)",
  "narration": "Texto corrido natural para dublagem em voz alta (entre 28 e 36 palavras, terminando com Comente amém!)",
  "caption": "Legenda humana e edificante para o Instagram (3 parágrafos curtos, max 2 emojis, terminando com referência bíblica e @wallasnascimento_ • ideepregai)"
}}
"""
        body = json.dumps({
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseMimeType": "application/json", "temperature": 0.8},
        }).encode("utf-8")

        for model in ["gemini-flash-latest", "gemini-3.8-flash", "gemini-flash-lite-latest"]:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
            for attempt in range(2):
                try:
                    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
                    with urllib.request.urlopen(req, timeout=15) as resp:
                        res = json.loads(resp.read().decode("utf-8"))
                    raw = res["candidates"][0]["content"]["parts"][0]["text"]
                    print(f"Roteiro gerado com sucesso via Gemini ({model})!")
                    return json.loads(raw)
                except Exception as exc:
                    print(f"Tentativa {attempt + 1} em {model} falhou: {exc}")
                    time.sleep(3)

    print("Usando roteiro curado do acervo inteligente...")
    available = [s for s in CURATED_SCRIPTS if s["verse"] not in posted_verses]
    if not available:
        available = CURATED_SCRIPTS
    return random.choice(available)


def fetch_mixkit_asset(page_url: str, pattern: str, out_path: Path) -> None:
    html = subprocess.check_output(
        ["curl", "-sL", "--max-time", "20", "-A", "Mozilla/5.0", page_url]
    ).decode("utf-8", errors="ignore")
    matches = re.findall(pattern, html)
    if not matches:
        raise RuntimeError(f"No media found at {page_url}")
    chosen = random.choice(matches[:12])
    subprocess.check_call(["curl", "-sL", "--max-time", "45", "-o", str(out_path), chosen])


def main() -> None:
    history = load_history()
    posted_verses = [item["verse"] for item in history.get("posted", [])]

    print("1. Gerando roteiro cristão...")
    script = generate_script(posted_verses)
    print("Versículo escolhido:", script["verse"])

    print("2. Gerando dublagem expressiva...")
    voz_path = BUILD_DIR / "voz.mp3"
    subprocess.check_call([
        "edge-tts", "--voice", VOICE, "--rate=+2%", "--pitch=+2Hz",
        "--text", script["narration"], "--write-media", str(voz_path),
    ])
    dur = float(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(voz_path),
    ]).decode().strip())
    total_dur = max(15.0, round(dur + 0.8, 1))

    print(f"3. Baixando B-roll e trilha real (duração {total_dur}s)...")
    broll_path = BUILD_DIR / "broll.mp4"
    bgm_path = BUILD_DIR / "bgm.mp3"
    topic = random.choice(BROLL_TOPICS)
    fetch_mixkit_asset(
        f"https://mixkit.co/free-stock-video/{topic}/",
        r"https://assets\.mixkit\.co/videos/[^\s\"'<>]+\.mp4",
        broll_path,
    )
    fetch_mixkit_asset(
        "https://mixkit.co/free-stock-music/piano/",
        r"https://assets\.mixkit\.co/music/[^\s\"'<>]+\.mp3",
        bgm_path,
    )

    print("4. Montando composição HyperFrames...")
    hf_dir = BUILD_DIR / "hf_proj"
    hf_dir.mkdir(exist_ok=True)
    d1 = round(total_dur * 0.23, 2)
    d2 = round(total_dur * 0.23, 2)
    d3 = round(total_dur * 0.28, 2)
    d4 = round(total_dur - d1 - d2 - d3, 2)
    s2, s3, s4 = d1, round(d1 + d2, 2), round(d1 + d2 + d3, 2)

    html = (ROOT / "template.html").read_text(encoding="utf-8")
    replacements = {
        "__DURATION__": str(total_dur),
        "__D1__": str(d1), "__D2__": str(d2), "__D3__": str(d3), "__D4__": str(d4),
        "__S2__": str(s2), "__S3__": str(s3), "__S4__": str(s4),
        "__PRE1__": script["pre1"], "__TEXT1__": script["text1"],
        "__PRE2__": script["pre2"], "__TEXT2__": script["text2"],
        "__PRE3__": script["pre3"], "__TEXT3__": script["text3"],
        "__PRE4__": script["pre4"], "__TEXT4__": script["text4"],
        "__VERSE__": script["verse"],
    }
    for k, v in replacements.items():
        html = html.replace(k, v)
    (hf_dir / "index.html").write_text(html, encoding="utf-8")

    motion_path = BUILD_DIR / "motion.mp4"
    subprocess.check_call(
        ["npx", "--yes", "hyperframes", "render", ".", "--output", str(motion_path)],
        cwd=str(hf_dir),
    )

    print("5. Compondo B-roll + Motion + Voz + Piano no FFmpeg...")
    final_path = BUILD_DIR / "reel_final.mp4"
    fade_out_start = max(1.0, total_dur - 2.5)
    subprocess.check_call([
        "ffmpeg", "-y", "-stream_loop", "-1", "-i", str(broll_path),
        "-i", str(motion_path), "-i", str(voz_path), "-i", str(bgm_path),
        "-filter_complex",
        f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,"
        f"eq=brightness=-0.28:saturation=0.85,trim=0:{total_dur},setpts=PTS-STARTPTS[bg];"
        f"[1:v]colorkey=0x060608:0.12:0.15,setpts=PTS-STARTPTS[fg];"
        f"[bg][fg]overlay=0:0:shortest=1[vout];"
        f"[3:a]atrim=0:{total_dur},asetpts=PTS-STARTPTS,afade=t=in:st=0:d=1.0,"
        f"afade=t=out:st={fade_out_start}:d=2.5,volume=0.20[bgm];"
        f"[2:a]adelay=250|250,acompressor=threshold=-18dB:ratio=3:attack=5:release=50,volume=1.45[v];"
        f"[v][bgm]amix=inputs=2:duration=first:dropout_transition=2[aout]",
        "-map", "[vout]", "-map", "[aout]",
        "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-t", str(total_dur), str(final_path),
    ])

    (BUILD_DIR / "caption.txt").write_text(script["caption"], encoding="utf-8")
    history["posted"].append({
        "date": datetime.utcnow().strftime("%Y-%m-%d"),
        "verse": script["verse"],
        "hook": re.sub(r"<[^>]+>", "", script["text1"]),
    })
    save_history(history)
    print("Vídeo e legenda gerados com sucesso em build/reel_final.mp4")


if __name__ == "__main__":
    main()

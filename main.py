import argparse
import asyncio
import base64
import difflib
import html
import json
import os
import random
import re
import shutil
import subprocess
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent
HISTORY_FILE = ROOT / "history.json"
ASSETS_DIR = ROOT / "assets"
BUILD_DIR = ROOT / "build"
BROLL_CACHE_DIR = BUILD_DIR / "broll_cache"
BUILD_DIR.mkdir(exist_ok=True)
BROLL_CACHE_DIR.mkdir(exist_ok=True)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
WHATSAPP_DISPLAY = "(12) 99659-3222"

# Vozes altamente expressivas e dramáticas no Gemini 2.5 Flash TTS (sem locutores robóticos/informativos)
VOICE_PROFILES = {
    "masculino": {
        "gemini_voices": ["Enceladus", "Fenrir"],
        "edge_voices": ["pt-BR-AntonioNeural", "pt-BR-FabioNeural"],
        "edge_rate": "+2%",
        "edge_pitch": "-2Hz",
        "audio_profile": (
            "AUDIO PROFILE: Ator brasileiro de 32 anos narrando uma história real e tensa de madrugada "
            "para um curta-metragem emocional. Voz humana próxima do microfone, respiração real, "
            "comece íntimo e intrigante, cresça com intensidade emocional no conflito, faça uma breve pausa "
            "dramática antes da virada e feche com firmeza magnética. NUNCA soe como apresentador de jornal, "
            "aula técnica ou robô."
        ),
    },
    "feminino": {
        "gemini_voices": ["Sulafat", "Aoede", "Kore"],
        "edge_voices": ["pt-BR-ThalitaMultilingualNeural", "pt-BR-FranciscaNeural"],
        "edge_rate": "+2%",
        "edge_pitch": "+0Hz",
        "audio_profile": (
            "AUDIO PROFILE: Atriz brasileira de 30 anos narrando uma história real intensa de madrugada "
            "para um filme curto emocional. Voz humana calorosa e magnética, próxima do microfone, "
            "cheia de verdade na voz, tensão no gancho, respiração natural antes da reviravolta "
            "e clareza firme no desfecho. NUNCA soe robótica, apressada ou como comercial."
        ),
    },
}

# Catálogo expandido de 40+ clipes reais Mixkit HD (todos testados HTTP 200)
BROLL_CATALOG = {
    "male_night": ["16139", "4701", "34538", "50756", "35426", "4808"],
    "male_rise": ["52079", "4855", "23410", "6734", "26532", "41859"],
    "female_night": ["51399", "5888", "8739", "25586", "46702", "43270"],
    "female_rise": ["4629", "42733", "28899", "6734", "26532", "41859"],
    "mood_dark": ["4915", "2846", "28897", "28893", "28901", "40640", "41375", "4433", "20843", "46741", "17702", "4664", "939", "64"],
    "mood_gold": ["6734", "26532", "6850", "41859", "236", "4629", "4855"],
}

EMPHASIS_WORDS = {
    "não", "nunca", "jamais", "pare", "silêncio", "zero", "dói", "vergonha",
    "ego", "migalha", "migalhas", "abstinência", "noventa", "segundos", "madrugada",
    "recaída", "bloqueia", "dignidade", "paz", "armadilha", "whatsapp", "sozinho",
    "sozinha", "queimadura", "física", "reservas", "reserva", "amigos", "respeito",
    "controle", "carência", "atração", "tempo", "textão", "vácuo", "sumiu", "virou",
    "apagada", "nada", "sozinha", "direct", "scripts", "protocolo",
}

# 12 Micro-Filmes Narrativos Cinema v5 (5 masculino, 5 feminino, 2 ambos)
# Cada história possui 8 cenas sincronizadas palavra por palavra com arco cinematográfico completo.
CURATED_STORIES = [
    # ── MASCULINO 01 ──────────────────────────────────────────────────────────
    {
        "topic": "A Madrugada das 02:14 do Lucas (História Masculino #01)",
        "audience": "masculino",
        "music_bed": "cinema_piano",
        "emotion_direction": "Comece quase num sussurro tenso de madrugada, ganhe urgência no conflito, dê peso dramático na virada e feche com firmeza de superação.",
        "scenes": [
            {
                "spoken": "Eram duas e catorze da manhã... quando o celular do Lucas brilhou no escuro.",
                "broll_id": "16139", "grade": "night_mood", "camera": "push_in", "fx": "none",
                "overlay_type": "hook_cinema",
                "stamp": "02:14 AM • HISTÓRIA REAL",
                "title": "O CELULAR BRILHOU NO ESCURO.",
                "hl": "ESCURO.", "hl_color": "gold",
                "sub": "Trinta dias depois de ela ir embora.",
            },
            {
                "spoken": "Na tela, só duas palavras da ex que tinha sumido há um mês: 'tá acordado?'",
                "broll_id": "4915", "grade": "night_mood", "camera": "pan_left", "fx": "none",
                "overlay_type": "phone_lockscreen",
                "clock": "02:14", "date": "Quinta-feira, madrugada",
                "sender": "Ex • WhatsApp", "msg": "\"Tá acordado?\"",
            },
            {
                "spoken": "O coração dele disparou na hora. O dedo já tava escrevendo um textão... quase implorando pra ela voltar.",
                "broll_id": "20843", "grade": "night_mood", "camera": "push_in", "fx": "none",
                "overlay_type": "whatsapp_draft",
                "sender": "Rascunho • 02:15", "msg": "\"Eu ainda penso em você todo dia, me dá só uma chance...\"",
                "seen": "Digitando...", "stamp": "IMPULSO FATAL",
            },
            {
                "spoken": "Noventa por cento dos caras aperta enviar ali... e acorda às nove da manhã olhando dois risquinhos azuis e zero resposta.",
                "broll_id": "34538", "grade": "night_mood", "camera": "pan_right", "fx": "none",
                "overlay_type": "whatsapp_draft",
                "sender": "Enviada • 02:16", "msg": "Textão de 25 linhas entregue no impulso.",
                "seen": "✓✓ Visualizado • Sem resposta", "stamp": "90% CAI AQUI",
            },
            {
                "spoken": "Só que dessa vez... o Lucas não respondeu nada. Ele virou o celular pra baixo e foi dormir.",
                "broll_id": "28897", "grade": "night_mood", "camera": "push_in", "fx": "dark_drop", "sfx": "twist",
                "overlay_type": "twist_card",
                "kicker": "A VIRADA",
                "quote": "Dessa vez... ele não mandou nada.",
                "sub": "Virou o celular pra baixo e apagou a luz.",
            },
            {
                "spoken": "Porque aquela mensagem não era saudade. A psicologia chama de teste de ego: ela só queria saber se ele ainda tava no bolso.",
                "broll_id": "40640", "grade": "night_mood", "camera": "pan_left", "fx": "none",
                "overlay_type": "neuro_hud",
                "tag": "PSICOLOGIA DO EGO • ESCUDO #01",
                "main": "Esforço zero só testa se você ainda está na reserva.",
            },
            {
                "spoken": "Três dias depois, quem mandou áudio de dois minutos pedindo pra conversar foi ela. Mas o Lucas já tinha voltado pro treino... e pra própria paz.",
                "broll_id": "52079", "grade": "warm_gold", "camera": "push_in", "fx": "warm_flash",
                "overlay_type": "twist_card",
                "kicker": "3 DIAS DEPOIS",
                "quote": "O jogo virou no silêncio.",
                "sub": "Quem recupera o eixo não implora atenção.",
            },
            {
                "spoken": "Não improvisa na próxima madrugada que o aperto bater. Comenta ZERO agora que eu te mando os dezesseis scripts prontos e o protocolo de catorze dias.",
                "broll_id": "6734", "grade": "warm_gold", "camera": "pan_right", "fx": "none", "sfx": "cta_pop",
                "overlay_type": "ig_dm_cta",
            },
        ],
        "caption": (
            "Às 02:14 da manhã, uma única decisão separa o homem que perde o respeito do homem que recupera a própria paz.\n\n"
            "Quando a ex manda 'tá acordado?' depois de sumir, quase nunca é arrependimento: é teste de validação. "
            "No Código Zero você tem os 16 scripts exatos e o protocolo de 14 dias pra nunca mais travar na madrugada.\n\n"
            "Comenta ZERO agora ou chama no WhatsApp da bio: (12) 99659-3222.\n\n"
            "#homens #contatozero #superartermino #posturamasculina #codigozero"
        ),
    },
    # ── FEMININO 01 ───────────────────────────────────────────────────────────
    {
        "topic": "A Mensagem Apagada da Camila às 23:54 (História Feminino #01)",
        "audience": "feminino",
        "music_bed": "cinema_piano",
        "emotion_direction": "Íntima e envolvente no começo, com tensão palpável na curiosidade, pausa emocional na virada e voz leve e segura no final.",
        "scenes": [
            {
                "spoken": "Eram onze e cinquenta e quatro da noite... quando o celular da Camila vibrou do lado do travesseiro.",
                "broll_id": "51399", "grade": "night_mood", "camera": "push_in", "fx": "none",
                "overlay_type": "hook_cinema",
                "stamp": "23:54 • QUARTO SILENCIOSO",
                "title": "O CELULAR VIBROU QUASE MEIA-NOITE.",
                "hl": "MEIA-NOITE.", "hl_color": "gold",
                "sub": "Era o nome que ela tentava esquecer há semanas.",
            },
            {
                "spoken": "Quando ela desbloqueou a tela, o estômago gelou. Na conversa dele só aparecia: 'esta mensagem foi apagada'.",
                "broll_id": "43270", "grade": "night_mood", "camera": "pan_left", "fx": "none",
                "overlay_type": "phone_lockscreen",
                "clock": "23:54", "date": "Domingo, 23:54",
                "sender": "Ex • WhatsApp", "msg": "🚫 Esta mensagem foi apagada",
            },
            {
                "spoken": "A curiosidade quase engoliu ela viva. O dedo já tava digitando 'oi, o que você ia falar?'",
                "broll_id": "46741", "grade": "night_mood", "camera": "push_in", "fx": "none",
                "overlay_type": "whatsapp_draft",
                "sender": "Rascunho • 23:55", "msg": "\"Oi, tudo bem? O que você ia me mandar?\"",
                "seen": "Quase enviando...", "stamp": "ANZOL PERFEITO",
            },
            {
                "spoken": "É exatamente aí que quase toda mulher cai. Uma pergunta dessas entrega ansiedade na bandeja e infla o ego dele até o teto.",
                "broll_id": "5888", "grade": "night_mood", "camera": "pan_right", "fx": "none",
                "overlay_type": "whatsapp_draft",
                "sender": "Erro comum", "msg": "Correr atrás de quem joga migalha de mistério.",
                "seen": "✓✓ Ego dele alimentado", "stamp": "ARMADILHA CLÁSSICA",
            },
            {
                "spoken": "Só que dessa vez... a Camila fechou o aplicativo sem digitar uma letra. E deixou ele falando sozinho com o próprio jogo.",
                "broll_id": "2846", "grade": "night_mood", "camera": "push_in", "fx": "dark_drop", "sfx": "twist",
                "overlay_type": "twist_card",
                "kicker": "A VIRADA",
                "quote": "Ela fechou a tela sem responder nada.",
                "sub": "Quem tem postura adulta fala claro, não faz enigma.",
            },
            {
                "spoken": "Na psicologia, mensagem apagada acende um pico de dopamina pela dúvida. Se você não morde a isca, o poder volta inteiro pra sua mão.",
                "broll_id": "28901", "grade": "night_mood", "camera": "pan_left", "fx": "none",
                "overlay_type": "neuro_hud",
                "tag": "ESCUDO #04 • CORTANDO A ISCA",
                "main": "Sem reação sua, o teste de atenção morre na hora.",
            },
            {
                "spoken": "Dois dias depois, ele voltou escrevendo claro e assumindo o erro. Mas a Camila já tava dormindo inteira... e sem depender de notificação nenhuma.",
                "broll_id": "4629", "grade": "warm_gold", "camera": "push_in", "fx": "warm_flash",
                "overlay_type": "twist_card",
                "kicker": "48 HORAS DEPOIS",
                "quote": "A paz dela já valia mais.",
                "sub": "Amor-próprio não responde enigma de madrugada.",
            },
            {
                "spoken": "Se você tá cansada de cair nos testes dele, comenta ZERO agora que eu libero os dezesseis scripts e o protocolo de catorze dias no seu direct.",
                "broll_id": "41859", "grade": "warm_gold", "camera": "pan_right", "fx": "none", "sfx": "cta_pop",
                "overlay_type": "ig_dm_cta",
            },
        ],
        "caption": (
            "Mensagem apagada às 23:54 quase nunca é acidente: é um anzol de curiosidade pra testar se você ainda corre atrás.\n\n"
            "Veja como o Escudo #04 do Código Zero protege seu coração e devolve o controle pra sua mão.\n\n"
            "Comenta ZERO agora ou chama no WhatsApp da bio: (12) 99659-3222.\n\n"
            "#mulheres #contatozero #amorproprio #superartermino #codigozero"
        ),
    },
    # ── MASCULINO 02 ──────────────────────────────────────────────────────────
    {
        "topic": "O Pedido de Tempo que Mudou a Postura do Rafael (História Masculino #02)",
        "audience": "masculino",
        "music_bed": "cinema_epic",
        "emotion_direction": "Forte, cinematográfico, tensão real no começo, impacto cortante na virada e confiança inabalável no final.",
        "scenes": [
            {
                "spoken": "Numa terça-feira à noite, ela olhou pro Rafael e soltou a frase que todo homem teme: 'acho melhor a gente dar um tempo'.",
                "broll_id": "4701", "grade": "night_mood", "camera": "push_in", "fx": "none",
                "overlay_type": "hook_cinema",
                "stamp": "TERÇA-FEIRA • 21:30",
                "title": "'ACHO MELHOR DARMOS UM TEMPO.'",
                "hl": "UM TEMPO.", "hl_color": "red",
                "sub": "A frase que derruba 9 em cada 10 homens.",
            },
            {
                "spoken": "Duas horas depois, ele abriu o Instagram... e viu ela online rindo nos stories como se nada tivesse acontecido.",
                "broll_id": "4808", "grade": "night_mood", "camera": "pan_left", "fx": "none",
                "overlay_type": "phone_lockscreen",
                "clock": "23:41", "date": "Online agora",
                "sender": "Instagram • Stories", "msg": "Ativa há 2 min • Nova publicação",
            },
            {
                "spoken": "A raiva subiu pro pescoço. Ele pegou a chave do carro, quase ligou cobrando explicação e prometendo mudar tudo.",
                "broll_id": "64", "grade": "night_mood", "camera": "push_in", "fx": "none",
                "overlay_type": "whatsapp_draft",
                "sender": "Impulso às 23:45", "msg": "\"Como assim tempo? Depois de tudo que fiz por você?\"",
                "seen": "Pronto pra ligar...", "stamp": "ARMADILHA DO EGO",
            },
            {
                "spoken": "Mas pensa comigo: quando um homem implora por atenção de quem pediu saída, ele só prova que ela tomou a decisão certa.",
                "broll_id": "50756", "grade": "night_mood", "camera": "pan_right", "fx": "none",
                "overlay_type": "whatsapp_draft",
                "sender": "Efeito real", "msg": "Cobrança emocional destrói respeito na mesma hora.",
                "seen": "Atração zerada", "stamp": "NUNCA IMPLORE",
            },
            {
                "spoken": "O Rafael respirou fundo... mandou uma única linha: 'tranquilo, respeito sua escolha'. E desapareceu do mapa.",
                "broll_id": "4433", "grade": "night_mood", "camera": "push_in", "fx": "dark_drop", "sfx": "twist",
                "overlay_type": "twist_card",
                "kicker": "A VIRADA",
                "quote": "'Tranquilo. Respeito sua escolha.'",
                "sub": "Uma linha. Zero drama. Silêncio absoluto.",
            },
            {
                "spoken": "Quando você retira sua presença sem fazer cena, o peso da escolha cai inteiro nas costas de quem quis sair.",
                "broll_id": "41375", "grade": "night_mood", "camera": "pan_left", "fx": "none",
                "overlay_type": "neuro_hud",
                "tag": "LEI DA POSTURA • SCRIPT #08",
                "main": "Homem que aceita o fim inteiro nunca vira plano B.",
            },
            {
                "spoken": "Em catorze dias ele secou a mente, voltou a treinar pesado e recuperou o respeito que nenhum discurso compraria.",
                "broll_id": "4855", "grade": "warm_gold", "camera": "push_in", "fx": "warm_flash",
                "overlay_type": "twist_card",
                "kicker": "DIA 14",
                "quote": "Postura vale mais que mil argumentos.",
                "sub": "No controle da rotina, do foco e da própria cabeça.",
            },
            {
                "spoken": "Se ela pediu tempo ou esfriou com você, não chuta no escuro. Comenta ZERO agora que eu envio o Código Zero completo no seu direct.",
                "broll_id": "26532", "grade": "warm_gold", "camera": "pan_right", "fx": "none", "sfx": "cta_pop",
                "overlay_type": "ig_dm_cta",
            },
        ],
        "caption": (
            "'Dar um tempo' raramente é dúvida: quase sempre é uma saída em câmera lenta esperando você implorar.\n\n"
            "A postura de uma única linha salva seu respeito e devolve o eixo em 14 dias.\n\n"
            "Comenta ZERO agora ou chama no WhatsApp da bio: (12) 99659-3222.\n\n"
            "#desenvolvimentomasculino #contatozero #homens #termino #codigozero"
        ),
    },
    # ── AMBOS 01 (NEUROCIÊNCIA CINEMATOGRÁFICA) ───────────────────────────────
    {
        "topic": "A Queimadura Invisível no Peito — Estudo Michigan (História Ambos #01)",
        "audience": "ambos",
        "music_bed": "cinema_strings",
        "emotion_direction": "Profundo, empático, documentário de cinema que acolhe homens e mulheres e vira a chave na revelação científica.",
        "scenes": [
            {
                "spoken": "Você já acordou de madrugada com um aperto tão real no peito... que parecia uma ferida física aberta?",
                "broll_id": "2846", "grade": "night_mood", "camera": "push_in", "fx": "none",
                "overlay_type": "hook_cinema",
                "stamp": "NEUROCIÊNCIA • FATO REAL",
                "title": "POR QUE SAUDADE DÓI NO CORPO?",
                "hl": "NO CORPO?", "hl_color": "red",
                "sub": "E não é frescura nem falta de amor-próprio.",
            },
            {
                "spoken": "E aí você olha pro teto se chamando de fraco ou fraca... porque todo mundo diz 'é só seguir em frente'.",
                "broll_id": "4701", "grade": "night_mood", "camera": "pan_left", "fx": "none",
                "overlay_type": "twist_card",
                "kicker": "A CULPA INJUSTA",
                "quote": "'É só esquecer e seguir em frente.'",
                "sub": "O conselho raso que nunca curou ninguém.",
            },
            {
                "spoken": "Até que pesquisadores da Universidade de Michigan colocaram pessoas recém-separadas dentro de uma máquina de ressonância magnética.",
                "broll_id": "17702", "grade": "night_mood", "camera": "push_in", "fx": "none",
                "overlay_type": "neuro_hud",
                "tag": "KROSS ET AL. (2011) • UNIV. DE MICHIGAN",
                "main": "Exame de fMRI mapeou o cérebro durante a rejeição amorosa.",
            },
            {
                "spoken": "Quando mostraram a foto do ex ou da ex, o exame revelou algo assustador: acendeu exatamente a mesma rede cerebral de uma queimadura quente na pele.",
                "broll_id": "25586", "grade": "night_mood", "camera": "pan_right", "fx": "none",
                "overlay_type": "neuro_hud",
                "tag": "DESCOBERTA CLÍNICA",
                "main": "Rejeição aciona a mesma rede neural de uma queimadura física.",
            },
            {
                "spoken": "Você não perdeu a cabeça. Seu cérebro só está atravessando um corte químico real de dopamina.",
                "broll_id": "28893", "grade": "night_mood", "camera": "push_in", "fx": "dark_drop", "sfx": "twist",
                "overlay_type": "twist_card",
                "kicker": "A VERDADE",
                "quote": "Não é fraqueza. É abstinência química.",
                "sub": "Homens e mulheres passam pelo mesmo choque biológico.",
            },
            {
                "spoken": "Por isso cada espiada nos stories e cada mensagem enviada reinicia a dor do zero... exatamente como reabrir um corte.",
                "broll_id": "4915", "grade": "night_mood", "camera": "pan_left", "fx": "none",
                "overlay_type": "whatsapp_draft",
                "sender": "Gatilho diário", "msg": "Espiar perfil + checar visto por último.",
                "seen": "Ciclo reiniciado pro Dia 0", "stamp": "DESMAME QUEBRADO",
            },
            {
                "spoken": "Mas quando você segue um protocolo estruturado de catorze dias cortando estímulos e aplicando a trava de noventa segundos... o peito finalmente volta a respirar leve.",
                "broll_id": "6850", "grade": "warm_gold", "camera": "push_in", "fx": "warm_flash",
                "overlay_type": "twist_card",
                "kicker": "14 DIAS DE MÉTODO",
                "quote": "Método vence força bruta.",
                "sub": "Passo a passo diário até a fissura perder força.",
            },
            {
                "spoken": "Pare de lutar sozinho contra a própria biologia. Comenta ZERO agora que eu te mando o Código Zero completo no direct.",
                "broll_id": "6734", "grade": "warm_gold", "camera": "pan_right", "fx": "none", "sfx": "cta_pop",
                "overlay_type": "ig_dm_cta",
            },
        ],
        "caption": (
            "Um estudo da Universidade de Michigan (Kross et al., 2011) mostrou em imagem cerebral que rejeição amorosa ativa a mesma rede da dor física.\n\n"
            "Homens e mulheres passam pela mesma abstinência. Saia da culpa e entre num protocolo estruturado de 14 dias.\n\n"
            "Comenta ZERO agora ou chama no WhatsApp da bio: (12) 99659-3222.\n\n"
            "#neurociencia #superartermino #saudeemocional #contatozero #codigozero"
        ),
    },
    # ── FEMININO 02 ───────────────────────────────────────────────────────────
    {
        "topic": "O Áudio de 4 Minutos que a Marina Não Enviou (História Feminino #02)",
        "audience": "feminino",
        "music_bed": "cinema_strings",
        "emotion_direction": "Emocional, próxima e corajosa, fazendo a espectadora se enxergar na cena e vibrar com a virada.",
        "scenes": [
            {
                "spoken": "Eram uma e quarenta da madrugada... quando a Marina segurou o microfone do WhatsApp chorando.",
                "broll_id": "8739", "grade": "night_mood", "camera": "push_in", "fx": "none",
                "overlay_type": "hook_cinema",
                "stamp": "01:40 AM • QUASE RECAÍDA",
                "title": "O ÁUDIO QUE QUASE CUSTOU SUA PAZ.",
                "hl": "SUA PAZ.", "hl_color": "red",
                "sub": "Quatro minutos tentando fazer ele sentir falta.",
            },
            {
                "spoken": "Ele tinha sumido há três semanas... e apareceu do nada mandando só um 'oi, sonhei com você hoje'.",
                "broll_id": "43270", "grade": "night_mood", "camera": "pan_left", "fx": "none",
                "overlay_type": "phone_lockscreen",
                "clock": "01:40", "date": "Sábado, 01:40",
                "sender": "Ex • WhatsApp", "msg": "\"Oi sumida... sonhei com você hoje.\"",
            },
            {
                "spoken": "No áudio ela explicou tudo: o quanto doeu, o quanto ela ainda amava e por que eles deviam tentar mais uma vez.",
                "broll_id": "46702", "grade": "night_mood", "camera": "push_in", "fx": "none",
                "overlay_type": "whatsapp_draft",
                "sender": "Gravando áudio • 04:12", "msg": "Tentando convencer quem já escolheu partir...",
                "seen": "Dedo pronto pra soltar", "stamp": "ERRO EMOCIONAL",
            },
            {
                "spoken": "Sabe o que acontece quando você manda um desabafo longo pra quem te jogou migalha? Ele ouve em velocidade dois... e some de novo amanhã.",
                "broll_id": "25586", "grade": "night_mood", "camera": "pan_right", "fx": "none",
                "overlay_type": "whatsapp_draft",
                "sender": "Resultado real", "msg": "Áudio longo implorando vira peso, nunca saudade.",
                "seen": "✓✓ Ouvido em 2x • Vácuo", "stamp": "ESFORÇO DESIGUAL",
            },
            {
                "spoken": "No último segundo... a Marina deslizou o dedo pra esquerda e apagou o áudio inteiro.",
                "broll_id": "28897", "grade": "night_mood", "camera": "push_in", "fx": "dark_drop", "sfx": "twist",
                "overlay_type": "twist_card",
                "kicker": "O SEGUNDO DECISIVO",
                "quote": "Ela arrastou pra esquerda e apagou tudo.",
                "sub": "E pela primeira vez, dormiu orgulhosa de si.",
            },
            {
                "spoken": "A regra do Código Zero é clara: responda ao tamanho real da atitude dele, nunca ao tamanho da sua saudade na madrugada.",
                "broll_id": "4433", "grade": "night_mood", "camera": "pan_left", "fx": "none",
                "overlay_type": "neuro_hud",
                "tag": "REGRA DE OURO • ESCUDO #01",
                "main": "Esforço mínimo nunca merece acesso máximo ao seu coração.",
            },
            {
                "spoken": "No café da manhã seguinte não tinha ressaca moral, nem vergonha. Só alívio e uma mulher voltando a se respeitar.",
                "broll_id": "28899", "grade": "warm_gold", "camera": "push_in", "fx": "warm_flash",
                "overlay_type": "twist_card",
                "kicker": "09:00 DA MANHÃ",
                "quote": "Zero vergonha. 100% dignidade.",
                "sub": "A escolha difícil à noite vira paz no dia seguinte.",
            },
            {
                "spoken": "Nunca mais improvise quando ele reaparecer do nada. Comenta ZERO agora que eu mando os dezesseis scripts escudo no seu direct.",
                "broll_id": "42733", "grade": "warm_gold", "camera": "pan_right", "fx": "none", "sfx": "cta_pop",
                "overlay_type": "ig_dm_cta",
            },
        ],
        "caption": (
            "Quantas vezes você já gravou um áudio chorando às 2h da manhã e acordou arrependida às 9h?\n\n"
            "Quem saiu da sua vida não precisa de mais uma explicação da sua dor — precisa sentir sua ausência real.\n\n"
            "Comenta ZERO agora ou chama no WhatsApp da bio: (12) 99659-3222.\n\n"
            "#mulheres #superartermino #autoestima #contatozero #codigozero"
        ),
    },
    # ── MASCULINO 03 ──────────────────────────────────────────────────────────
    {
        "topic": "O Dia 14 em que o Bruno Quase Desabou no Espelho (História Masculino #03)",
        "audience": "masculino",
        "music_bed": "cinema_ambient",
        "emotion_direction": "Noir, íntimo, voz grave e verdadeira falando direto com o homem que segura a dor calado.",
        "scenes": [
            {
                "spoken": "Na primeira semana depois do término, o Bruno saiu com os amigos e jurou que já tinha superado.",
                "broll_id": "23410", "grade": "night_mood", "camera": "push_in", "fx": "none",
                "overlay_type": "hook_cinema",
                "stamp": "SEMANA 01 • A ILUSÃO",
                "title": "ELE ACHOU QUE JÁ TINHA SUPERADO.",
                "hl": "SUPERADO.", "hl_color": "gold",
                "sub": "Até chegar a segunda semana em silêncio.",
            },
            {
                "spoken": "Mas no dia catorze, voltando pra casa sozinho, a ficha caiu de uma vez só. E doeu como nunca tinha doído.",
                "broll_id": "35426", "grade": "night_mood", "camera": "pan_left", "fx": "none",
                "overlay_type": "twist_card",
                "kicker": "DIA 14 • O REBOTE",
                "quote": "A anestesia passou. O silêncio pesou.",
                "sub": "E a vontade de mandar mensagem voltou com força.",
            },
            {
                "spoken": "Naquele sábado ela ainda postou um story produzida saindo à noite. O orgulho dele gritou pra responder ou puxar assunto.",
                "broll_id": "4915", "grade": "night_mood", "camera": "push_in", "fx": "none",
                "overlay_type": "phone_lockscreen",
                "clock": "22:18", "date": "Sábado à noite",
                "sender": "Stories dela", "msg": "Nova foto • legenda provocativa",
            },
            {
                "spoken": "É nesse rebote tardio que a maioria dos homens quebra duas semanas de postura em trinta segundos de carência.",
                "broll_id": "50756", "grade": "night_mood", "camera": "pan_right", "fx": "none",
                "overlay_type": "whatsapp_draft",
                "sender": "Armadilha da semana 2", "msg": "Reagir ao story ou mandar 'como você tá?' no impulso.",
                "seen": "Postura entregue de graça", "stamp": "RECAÍDA TARDIA",
            },
            {
                "spoken": "Só que o Bruno conhecia o relógio emocional. Ele silenciou o perfil dela na hora... e não deu um único clique de validação.",
                "broll_id": "28893", "grade": "night_mood", "camera": "push_in", "fx": "dark_drop", "sfx": "twist",
                "overlay_type": "twist_card",
                "kicker": "CONTROLE ABSOLUTO",
                "quote": "Ele silenciou tudo. Zero audiência.",
                "sub": "Quem domina a semana dois vence o jogo inteiro.",
            },
            {
                "spoken": "O cérebro masculino costuma anestesiar o término nos primeiros dias. Quando a rotina silencia, a abstinência cobra — não é destino, é química.",
                "broll_id": "40640", "grade": "night_mood", "camera": "pan_left", "fx": "none",
                "overlay_type": "neuro_hud",
                "tag": "BIOLOGIA MASCULINA • CENTRAL SOS",
                "main": "Vazio na semana 2 é queda química, não sinal pra voltar.",
            },
            {
                "spoken": "Na semana seguinte, o barulho na mente baixou. O foco no trabalho e no treino voltou, e o Bruno recuperou o próprio eixo.",
                "broll_id": "52079", "grade": "warm_gold", "camera": "push_in", "fx": "warm_flash",
                "overlay_type": "twist_card",
                "kicker": "SEMANA 03",
                "quote": "Cabeça fria. Rotina no eixo.",
                "sub": "Sem viver refém do que ela posta ou faz.",
            },
            {
                "spoken": "Se a ficha caiu atrasada pra você, não enfrenta isso no escuro. Comenta ZERO agora que eu te mando o protocolo completo no direct.",
                "broll_id": "6734", "grade": "warm_gold", "camera": "pan_right", "fx": "none", "sfx": "cta_pop",
                "overlay_type": "ig_dm_cta",
            },
        ],
        "caption": (
            "Muitos homens parecem bem nos primeiros 7 dias e levam o golpe mais duro na segunda semana.\n\n"
            "Entender esse rebote impede que você jogue fora sua dignidade por causa de um story sábado à noite.\n\n"
            "Comenta ZERO agora ou chama no WhatsApp da bio: (12) 99659-3222.\n\n"
            "#homens #psicologiamasculina #contatozero #disciplina #codigozero"
        ),
    },
    # ── FEMININO 03 ───────────────────────────────────────────────────────────
    {
        "topic": "A Armadilha do 'Vamos Continuar Amigos' da Larissa (História Feminino #03)",
        "audience": "feminino",
        "music_bed": "cinema_piano",
        "emotion_direction": "Acolhedora e cortante, mostrando a dor silenciosa da amizade falsa e o alívio libertador do limite.",
        "scenes": [
            {
                "spoken": "No dia em que terminou, ele segurou a mão da Larissa e disse: 'você é especial demais... não quero perder sua amizade'.",
                "broll_id": "4664", "grade": "night_mood", "camera": "push_in", "fx": "none",
                "overlay_type": "hook_cinema",
                "stamp": "DESPEDIDA PARCELADA",
                "title": "'NÃO QUERO PERDER SUA AMIZADE.'",
                "hl": "AMIZADE.", "hl_color": "red",
                "sub": "A frase mais doce que esconde o maior desgaste.",
            },
            {
                "spoken": "Ela aceitou achando que ficando por perto ele ia perceber o erro e voltar.",
                "broll_id": "46702", "grade": "night_mood", "camera": "pan_left", "fx": "none",
                "overlay_type": "phone_lockscreen",
                "clock": "20:15", "date": "3 semanas depois",
                "sender": "Ex • WhatsApp", "msg": "\"E aí amiga, como foi seu dia?\"",
            },
            {
                "spoken": "Durante um mês inteiro ela respondia sorrindo... e chorava sozinha toda vez que ele sumia no fim de semana.",
                "broll_id": "5888", "grade": "night_mood", "camera": "push_in", "fx": "none",
                "overlay_type": "whatsapp_draft",
                "sender": "O preço escondido", "msg": "Você entrega carinho de namorada e recebe lugar de reserva.",
                "seen": "Ele supera em paz • Você sangra", "stamp": "MIGALHA EMOCIONAL",
            },
            {
                "spoken": "Amizade pós-término não segura ninguém: ela só anestesia a culpa dele enquanto ele segue a vida livre.",
                "broll_id": "2846", "grade": "night_mood", "camera": "pan_right", "fx": "none",
                "overlay_type": "neuro_hud",
                "tag": "REALIDADE SEM FILTRO",
                "main": "Enquanto você continua disponível, ele nunca sente sua perda.",
            },
            {
                "spoken": "Até que numa sexta-feira... a Larissa mandou uma única frase educada e fechou essa porta pra sempre.",
                "broll_id": "28901", "grade": "night_mood", "camera": "push_in", "fx": "dark_drop", "sfx": "twist",
                "overlay_type": "twist_card",
                "kicker": "SCRIPT #11",
                "quote": "'Não faz sentido amizade agora. Se cuida.'",
                "sub": "Sem briga. Sem drama. Apenas limite claro.",
            },
            {
                "spoken": "Naquela hora ele percebeu pela primeira vez que não tinha mais acesso livre ao coração dela.",
                "broll_id": "46741", "grade": "night_mood", "camera": "pan_left", "fx": "none",
                "overlay_type": "neuro_hud",
                "tag": "LIMITE DE DIGNIDADE",
                "main": "Quem recusa migalha recupera o próprio valor na hora.",
            },
            {
                "spoken": "Duas semanas depois, o peito da Larissa abriu espaço pro novo... leve, inteira e sem esperar por resto de atenção.",
                "broll_id": "4629", "grade": "warm_gold", "camera": "push_in", "fx": "warm_flash",
                "overlay_type": "twist_card",
                "kicker": "LIBERDADE REAL",
                "quote": "Você merece presença inteira.",
                "sub": "Nunca o banco de reservas de quem já foi.",
            },
            {
                "spoken": "Quer o Script onze exato pra encerrar essa falsa amizade sem cena? Comenta ZERO agora que eu te envio no direct.",
                "broll_id": "6850", "grade": "warm_gold", "camera": "pan_right", "fx": "none", "sfx": "cta_pop",
                "overlay_type": "ig_dm_cta",
            },
        ],
        "caption": (
            "Aceitar ser 'amiga' quando você ainda ama só ajuda ele a te superar sem sentir o peso da perda.\n\n"
            "No Script #11 do Código Zero você fecha essa porta com elegância e protege seu coração.\n\n"
            "Comenta ZERO agora ou chama no WhatsApp da bio: (12) 99659-3222.\n\n"
            "#amizadecomex #mulheres #amorproprio #dependenciaemocional #codigozero"
        ),
    },
    # ── AMBOS 02 (REGRA 90-15 CINEMA) ─────────────────────────────────────────
    {
        "topic": "Os 90 Segundos que Decidem Sua Noite (História Ambos #02)",
        "audience": "ambos",
        "music_bed": "cinema_epic",
        "emotion_direction": "Intenso e protetor, ritmo urgente como quem salva alguém no segundo exato antes da recaída.",
        "scenes": [
            {
                "spoken": "São onze e meia da noite. A casa tá em silêncio... e seu polegar tá parado em cima da foto do seu ex ou da sua ex.",
                "broll_id": "4915", "grade": "night_mood", "camera": "push_in", "fx": "none",
                "overlay_type": "hook_cinema",
                "stamp": "23:30 • ZONA DE PERIGO",
                "title": "TRAVA O DEDO POR 90 SEGUNDOS.",
                "hl": "90 SEGUNDOS.", "hl_color": "gold",
                "sub": "A escolha agora define como você acorda amanhã.",
            },
            {
                "spoken": "A sua mente jura que se você não mandar mensagem agora... esse aperto no peito não vai passar nunca.",
                "broll_id": "20843", "grade": "night_mood", "camera": "pan_left", "fx": "none",
                "overlay_type": "phone_lockscreen",
                "clock": "23:31", "date": "Ansiedade no pico",
                "sender": "Sua mente agora", "msg": "\"Manda só um oi pra aliviar esse aperto...\"",
            },
            {
                "spoken": "E toda vez que você obedece esse pânico, ganha dez segundos de alívio... seguidos de três dias de arrependimento.",
                "broll_id": "41375", "grade": "night_mood", "camera": "push_in", "fx": "none",
                "overlay_type": "whatsapp_draft",
                "sender": "Ressaca moral às 09:00", "msg": "Por que eu fui mandar aquilo ontem à noite?",
                "seen": "Ciclo repetido outra vez", "stamp": "ALÍVIO FALSO",
            },
            {
                "spoken": "Só que existe um segredo biológico que quase ninguém te contou antes de você apertar enviar.",
                "broll_id": "28897", "grade": "night_mood", "camera": "pan_right", "fx": "none",
                "overlay_type": "neuro_hud",
                "tag": "FATO QUÍMICO • REGRA 90–15",
                "main": "A onda aguda de adrenalina no sangue dura apenas 90 segundos.",
            },
            {
                "spoken": "A crise dura só um minuto e meio. Ela só destrói sua madrugada inteira porque você continua encarando a tela.",
                "broll_id": "28893", "grade": "night_mood", "camera": "push_in", "fx": "dark_drop", "sfx": "twist",
                "overlay_type": "twist_card",
                "kicker": "A REGRA 90–15",
                "quote": "Largue o celular em outro cômodo.",
                "sub": "Dispare 15 minutos e escreva tudo num papel sem enviar.",
            },
            {
                "spoken": "Quando o cronômetro zera, a química baixa, o córtex acorda e você se faz uma pergunta: amanhã às nove eu quero orgulho ou vergonha?",
                "broll_id": "16139", "grade": "night_mood", "camera": "pan_left", "fx": "none",
                "overlay_type": "neuro_hud",
                "tag": "CENTRAL SOS • TRAVA REAL",
                "main": "15 minutos longe da tela devolvem a razão pro volante.",
            },
            {
                "spoken": "Você acorda no dia seguinte inteiro, leve e no comando da própria história.",
                "broll_id": "6734", "grade": "warm_gold", "camera": "push_in", "fx": "warm_flash",
                "overlay_type": "twist_card",
                "kicker": "MANHÃ SEGUINTE",
                "quote": "Orgulho vence carência.",
                "sub": "Uma noite vencida muda toda a sua semana.",
            },
            {
                "spoken": "Quer a Central SOS com cronômetro guiado e os dezesseis scripts direto no celular? Comenta ZERO agora que eu te mando.",
                "broll_id": "41859", "grade": "warm_gold", "camera": "pan_right", "fx": "none", "sfx": "cta_pop",
                "overlay_type": "ig_dm_cta",
            },
        ],
        "caption": (
            "Nenhuma mensagem enviada no pânico às 23:30 já trouxe respeito ou paz na manhã seguinte.\n\n"
            "A Regra 90-15 da Central SOS corta a recaída no momento exato em que o impulso aperta.\n\n"
            "Comenta ZERO agora ou chama no WhatsApp da bio: (12) 99659-3222.\n\n"
            "#contatozero #autocontrole #superartermino #ansiedade #codigozero"
        ),
    },
    # ── MASCULINO 04 ──────────────────────────────────────────────────────────
    {
        "topic": "O Dia em que o Thiago Recusou Ser o Amigo Reserva (História Masculino #04)",
        "audience": "masculino",
        "music_bed": "cinema_strings",
        "emotion_direction": "Sincero, maduro, sem ódio nem vitimismo — respeito masculino sólido.",
        "scenes": [
            {
                "spoken": "Quando ela terminou com o Thiago, pediu pra continuar ligando sempre que tivesse um dia ruim.",
                "broll_id": "939", "grade": "night_mood", "camera": "push_in", "fx": "none",
                "overlay_type": "hook_cinema",
                "stamp": "HOMENS • ZONA DE RESERVA",
                "title": "ELA QUERIA APOIO SEM COMPROMISSO.",
                "hl": "RESERVA.", "hl_color": "red",
                "sub": "E ele quase aceitou pra não perder o contato.",
            },
            {
                "spoken": "Por três semanas ele foi o ombro perfeito... enquanto ela saía livre nos sábados sem dar satisfação.",
                "broll_id": "35426", "grade": "night_mood", "camera": "pan_left", "fx": "none",
                "overlay_type": "phone_lockscreen",
                "clock": "22:48", "date": "Terceira semana",
                "sender": "Ex • WhatsApp", "msg": "\"Posso te ligar? Tô precisando desabafar...\"",
            },
            {
                "spoken": "Cada ligação deixava o Thiago acordado até três da manhã... se sentindo usado e menor a cada dia.",
                "broll_id": "34538", "grade": "night_mood", "camera": "push_in", "fx": "none",
                "overlay_type": "whatsapp_draft",
                "sender": "Custo invisível", "msg": "Você segura a barra dela enquanto destrói sua autoestima.",
                "seen": "Disponível demais = valor zero", "stamp": "ARMADILHA SILENCIOSA",
            },
            {
                "spoken": "Homem que aceita papel de amigo depois de ser dispensado vira muleta emocional de quem já virou a página.",
                "broll_id": "40640", "grade": "night_mood", "camera": "pan_right", "fx": "none",
                "overlay_type": "neuro_hud",
                "tag": "REALIDADE • SCRIPT #11",
                "main": "Muleta emocional nunca desperta admiração nem desejo.",
            },
            {
                "spoken": "Na quarta semana... quando o telefone tocou outra vez, o Thiago respirou fundo e encerrou com classe.",
                "broll_id": "28897", "grade": "night_mood", "camera": "push_in", "fx": "dark_drop", "sfx": "twist",
                "overlay_type": "twist_card",
                "kicker": "O CORTE LIMPO",
                "quote": "'Não consigo ser só seu amigo agora. Fica bem.'",
                "sub": "Firme, educado e definitivo.",
            },
            {
                "spoken": "Sem xingar, sem cobrar e sem olhar pra trás. Ele tirou o acesso gratuito que ela tinha à energia dele.",
                "broll_id": "23410", "grade": "night_mood", "camera": "pan_left", "fx": "none",
                "overlay_type": "neuro_hud",
                "tag": "RETOMADA DE EIXO",
                "main": "Dignidade volta no instante em que você fecha a porta certa.",
            },
            {
                "spoken": "Em catorze dias o peso saiu das costas dele. Dormiu inteiro, retomou os projetos e voltou a se olhar com respeito no espelho.",
                "broll_id": "4855", "grade": "warm_gold", "camera": "push_in", "fx": "warm_flash",
                "overlay_type": "twist_card",
                "kicker": "RESULTADO",
                "quote": "Respeito próprio não se negocia.",
                "sub": "Quem se retira inteiro vence em qualquer cenário.",
            },
            {
                "spoken": "Se você tá preso nessa amizade que te desgasta, comenta ZERO agora que eu mando os scripts prontos e o protocolo no seu direct.",
                "broll_id": "26532", "grade": "warm_gold", "camera": "pan_right", "fx": "none", "sfx": "cta_pop",
                "overlay_type": "ig_dm_cta",
            },
        ],
        "caption": (
            "Aceitar ser o 'amigo ombro' de quem terminou com você só drena sua energia e impede ela de sentir sua falta.\n\n"
            "Corte com postura e maturidade usando o Script #11 do Código Zero.\n\n"
            "Comenta ZERO agora ou chama no WhatsApp da bio: (12) 99659-3222.\n\n"
            "#homens #postura #amizadecomex #contatozero #codigozero"
        ),
    },
    # ── FEMININO 04 ───────────────────────────────────────────────────────────
    {
        "topic": "A Noite em que a Júlia Saiu do Teatro dos Stories (História Feminino #04)",
        "audience": "feminino",
        "music_bed": "cinema_ambient",
        "emotion_direction": "Envolvente, verdadeira e libertadora, revelando a exaustão secreta de postar pro ex ver.",
        "scenes": [
            {
                "spoken": "Todo sábado à noite a Júlia se arrumava inteira, tirava dez fotos... e ficava atualizando quem viu o story dela a cada dois minutos.",
                "broll_id": "42733", "grade": "night_mood", "camera": "push_in", "fx": "none",
                "overlay_type": "hook_cinema",
                "stamp": "SÁBADO • 22:10",
                "title": "ELA POSTAVA PRA ELE VER O QUE PERDEU.",
                "hl": "ELE VER", "hl_color": "gold",
                "sub": "E sofria em dobro cada vez que o nome não aparecia.",
            },
            {
                "spoken": "Quando o nome dele aparecia na lista, o peito disparava. Quando não aparecia, a noite inteira perdia a graça.",
                "broll_id": "43270", "grade": "night_mood", "camera": "pan_left", "fx": "none",
                "overlay_type": "phone_lockscreen",
                "clock": "22:34", "date": "Visualizado por 42 pessoas",
                "sender": "Instagram • Stories", "msg": "Procurando o nome dele na lista...",
            },
            {
                "spoken": "Por fora parecia superada. Por dentro ela continuava presa num palco esperando aplauso de quem já saiu da plateia.",
                "broll_id": "5888", "grade": "night_mood", "camera": "push_in", "fx": "none",
                "overlay_type": "whatsapp_draft",
                "sender": "A ilusão da vitrine", "msg": "Sorriso na foto, aperto no peito ao travar o celular.",
                "seen": "Ele ainda comanda sua rotina", "stamp": "PRISÃO INVISÍVEL",
            },
            {
                "spoken": "Enquanto cada foto sua tenta provocar reação nele, você não virou a página — só mudou o jeito de correr atrás.",
                "broll_id": "46702", "grade": "night_mood", "camera": "pan_right", "fx": "none",
                "overlay_type": "neuro_hud",
                "tag": "VERDADE REAL • CÓDIGO ZERO",
                "main": "Superar de verdade não precisa de plateia nem indireta.",
            },
            {
                "spoken": "Naquele domingo... a Júlia silenciou o perfil dele, parou de olhar visualizações e sumiu do teatro.",
                "broll_id": "2846", "grade": "night_mood", "camera": "push_in", "fx": "dark_drop", "sfx": "twist",
                "overlay_type": "twist_card",
                "kicker": "O PONTO DE VIRADA",
                "quote": "Ela tirou o ex de diretor da própria vida.",
                "sub": "A cura real acontece longe da vitrine.",
            },
            {
                "spoken": "Sem o vício da checagem, a mente acalmou. Em duas semanas ela já vivia momentos bons sem nem lembrar de provar nada pra ninguém.",
                "broll_id": "28899", "grade": "night_mood", "camera": "pan_left", "fx": "none",
                "overlay_type": "neuro_hud",
                "tag": "DESMAME DIGITAL • 14 DIAS",
                "main": "Quando você para de atuar, sua paz volta de verdade.",
            },
            {
                "spoken": "Porque a mulher mais irresistível e livre é justamente aquela que não joga mais jogo nenhum.",
                "broll_id": "4629", "grade": "warm_gold", "camera": "push_in", "fx": "warm_flash",
                "overlay_type": "twist_card",
                "kicker": "LIBERDADE",
                "quote": "Paz verdadeira não precisa de visualizações.",
                "sub": "Viva por você, não pela reação de quem partiu.",
            },
            {
                "spoken": "Quer sair desse ciclo em catorze dias com passos reais? Comenta ZERO agora que eu te mando o protocolo completo no direct.",
                "broll_id": "41859", "grade": "warm_gold", "camera": "pan_right", "fx": "none", "sfx": "cta_pop",
                "overlay_type": "ig_dm_cta",
            },
        ],
        "caption": (
            "Se você posta stories torcendo pro nome dele aparecer na lista, ele ainda tá dirigindo o seu fim de semana.\n\n"
            "No protocolo de 14 dias do Código Zero você quebra essa dependência de vez e volta a viver leve.\n\n"
            "Comenta ZERO agora ou chama no WhatsApp da bio: (12) 99659-3222.\n\n"
            "#mulheres #superacao #autoestima #contatozero #codigozero"
        ),
    },
    # ── MASCULINO 05 ──────────────────────────────────────────────────────────
    {
        "topic": "As 23:40 que Quase Custaram 14 Dias do Mateus (História Masculino #05)",
        "audience": "masculino",
        "music_bed": "cinema_ambient",
        "emotion_direction": "Firme, noturno, estilo narração de filme sobre autocontrole masculino.",
        "scenes": [
            {
                "spoken": "O Mateus segurou firme o dia inteiro: trabalhou, treinou pesado e não olhou uma única foto dela.",
                "broll_id": "52079", "grade": "night_mood", "camera": "push_in", "fx": "none",
                "overlay_type": "hook_cinema",
                "stamp": "DIA 08 • 23:40",
                "title": "DE DIA ELE ERA UMA ROCHA.",
                "hl": "ROCHA.", "hl_color": "gold",
                "sub": "Mas depois das onze da noite a cabeça trai.",
            },
            {
                "spoken": "Só que às onze e quarenta, deitado no silêncio do quarto, o cansaço desligou o freio... e a vontade bateu como um soco.",
                "broll_id": "16139", "grade": "night_mood", "camera": "pan_left", "fx": "none",
                "overlay_type": "phone_lockscreen",
                "clock": "23:40", "date": "Silêncio absoluto",
                "sender": "Gatilho noturno", "msg": "'Só vou dar uma olhada rápida no perfil dela...'",
            },
            {
                "spoken": "Ele abriu a busca do Instagram. Um toque ia jogar fora oito dias inteiros de postura e disciplina.",
                "broll_id": "4915", "grade": "night_mood", "camera": "push_in", "fx": "none",
                "overlay_type": "whatsapp_draft",
                "sender": "A mentira da madrugada", "msg": "Uma olhada de 5 segundos reinicia a abstinência toda.",
                "seen": "Risco de volta ao Dia 0", "stamp": "HORA CRÍTICA",
            },
            {
                "spoken": "Quase toda recaída masculina acontece nessa janela exata: entre onze da noite e duas da manhã, quando o cérebro já tá sem bateria.",
                "broll_id": "41375", "grade": "night_mood", "camera": "pan_right", "fx": "none",
                "overlay_type": "neuro_hud",
                "tag": "FADIGA DO CÓRTEX • 23H–02H",
                "main": "Força bruta perde fácil quando você está cansado e com o celular na mão.",
            },
            {
                "spoken": "Só que o Mateus lembrou da trava física. Ele levantou da cama, deixou o celular carregando na sala e apagou a luz.",
                "broll_id": "28893", "grade": "night_mood", "camera": "push_in", "fx": "dark_drop", "sfx": "twist",
                "overlay_type": "twist_card",
                "kicker": "TRAVA MECÂNICA",
                "quote": "Celular na sala. Porta fechada.",
                "sub": "Ambiente protege o que a vontade cansada não segura.",
            },
            {
                "spoken": "Em quinze minutos a onda química morreu sozinha. Ele dormiu profundo... sem humilhação e sem recaída.",
                "broll_id": "4433", "grade": "night_mood", "camera": "pan_left", "fx": "none",
                "overlay_type": "neuro_hud",
                "tag": "CENTRAL SOS • VITÓRIA NOTURNA",
                "main": "Quem vence a madrugada conquista respeito próprio de ferro.",
            },
            {
                "spoken": "Às sete da manhã ele acordou com o café quente na mão, olhou pro espelho e sorriu: estava no comando outra vez.",
                "broll_id": "236", "grade": "warm_gold", "camera": "push_in", "fx": "warm_flash",
                "overlay_type": "twist_card",
                "kicker": "07:00 DA MANHÃ",
                "quote": "O controle voltou pra sua mão.",
                "sub": "Disciplina noturna muda a vida de um homem.",
            },
            {
                "spoken": "Quer o protocolo noturno e a Central SOS prontos pra quando o aperto bater? Comenta ZERO agora que eu te mando no direct.",
                "broll_id": "6850", "grade": "warm_gold", "camera": "pan_right", "fx": "none", "sfx": "cta_pop",
                "overlay_type": "ig_dm_cta",
            },
        ],
        "caption": (
            "Você aguenta firme o dia todo e quase cai às 23:40? Não é fraqueza — é fadiga mental somada ao celular do lado da cama.\n\n"
            "Mude o ambiente e ative a Central SOS do Código Zero antes da noite chegar.\n\n"
            "Comenta ZERO agora ou chama no WhatsApp da bio: (12) 99659-3222.\n\n"
            "#disciplina #homens #madrugada #contatozero #codigozero"
        ),
    },
    # ── FEMININO 05 ───────────────────────────────────────────────────────────
    {
        "topic": "Os 3 Dias no Vácuo que Acordaram a Beatriz (História Feminino #05)",
        "audience": "feminino",
        "music_bed": "cinema_piano",
        "emotion_direction": "Delicada no início e inabalável na virada, tirando o peso da dúvida e devolvendo a clareza.",
        "scenes": [
            {
                "spoken": "Faziam setenta e duas horas que a última mensagem da Beatriz tava lá... sem resposta, enquanto ele postava normal.",
                "broll_id": "51399", "grade": "night_mood", "camera": "push_in", "fx": "none",
                "overlay_type": "hook_cinema",
                "stamp": "72 HORAS DE VÁCUO",
                "title": "ELE SUMIU, MAS CONTINUAVA ONLINE.",
                "hl": "ONLINE.", "hl_color": "red",
                "sub": "E ela ainda procurava desculpas pra defender ele.",
            },
            {
                "spoken": "Ela pensava: 'será que aconteceu algo no trabalho? Vou mandar só um oi pra saber se ele tá bem'.",
                "broll_id": "43270", "grade": "night_mood", "camera": "pan_left", "fx": "none",
                "overlay_type": "phone_lockscreen",
                "clock": "19:50", "date": "3 dias sem retorno",
                "sender": "Última mensagem sua", "msg": "✓✓ Visualizado há 3 dias",
            },
            {
                "spoken": "Mas toda mulher sabe lá no fundo a verdade que dói admitir: ninguém passa três dias ocupado demais pra quem realmente importa.",
                "broll_id": "8739", "grade": "night_mood", "camera": "push_in", "fx": "none",
                "overlay_type": "whatsapp_draft",
                "sender": "A verdade silenciosa", "msg": "Quem quer falar encontra 15 segundos no dia mais corrido.",
                "seen": "Desinteresse disfarçado de pressa", "stamp": "ACORDE AGORA",
            },
            {
                "spoken": "Mandar cobrança pra quem te deixa no vácuo nunca traz carinho de volta — só faz você se sentir ainda menor.",
                "broll_id": "25586", "grade": "night_mood", "camera": "pan_right", "fx": "none",
                "overlay_type": "neuro_hud",
                "tag": "CLAREZA RADICAL",
                "main": "O silêncio dele já é a resposta que faltou coragem de dizer.",
            },
            {
                "spoken": "Naquela noite... a Beatriz parou de justificar o injustificável. Arquivou a conversa e apagou o número do topo.",
                "broll_id": "2846", "grade": "night_mood", "camera": "push_in", "fx": "dark_drop", "sfx": "twist",
                "overlay_type": "twist_card",
                "kicker": "DECISÃO DE RESPEITO",
                "quote": "Ela leu o vácuo como um não definitivo.",
                "sub": "Sem textão de despedida. Sem implorar atenção.",
            },
            {
                "spoken": "Quando você aceita a mensagem oculta sem brigar, economiza meses de espera ansiosa olhando o celular.",
                "broll_id": "28901", "grade": "night_mood", "camera": "pan_left", "fx": "none",
                "overlay_type": "neuro_hud",
                "tag": "AUTORESPEITO • PROTOCOLO 14D",
                "main": "Você merece presença inteira, nunca resto de tempo.",
            },
            {
                "spoken": "Em duas semanas, a ansiedade soltou o peito dela. A Beatriz voltou a sorrir leve e aberta pra quem realmente escolhe ficar.",
                "broll_id": "4629", "grade": "warm_gold", "camera": "push_in", "fx": "warm_flash",
                "overlay_type": "twist_card",
                "kicker": "NOVA FASE",
                "quote": "Quem se escolhe nunca fica esperando resto.",
                "sub": "Leve, inteira e em paz outra vez.",
            },
            {
                "spoken": "Chega de sofrer esperando quem sumiu. Comenta ZERO agora que eu te envio o protocolo completo de catorze dias no direct.",
                "broll_id": "6734", "grade": "warm_gold", "camera": "pan_right", "fx": "none", "sfx": "cta_pop",
                "overlay_type": "ig_dm_cta",
            },
        ],
        "caption": (
            "Ninguém fica ocupado 72 horas sem conseguir mandar duas palavras pra quem realmente valoriza.\n\n"
            "Pare de criar desculpas pro vácuo e resgate a sua paz em 14 dias com o Código Zero.\n\n"
            "Comenta ZERO agora ou chama no WhatsApp da bio: (12) 99659-3222.\n\n"
            "#ghosting #mulheres #valor #superartermino #codigozero"
        ),
    },
]


def load_history() -> dict:
    if HISTORY_FILE.exists():
        return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    return {"posted": []}


def save_history(data: dict) -> None:
    HISTORY_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def choose_next_audience(history: dict, forced: str = "auto") -> str:
    if forced in ("masculino", "feminino", "ambos"):
        return forced
    posted = history.get("posted", [])
    audiences = [p.get("audience") for p in posted[-6:] if p.get("audience")]
    if not audiences:
        return "masculino"
    last = audiences[-1]
    m_cnt = audiences.count("masculino")
    f_cnt = audiences.count("feminino")
    if last == "feminino":
        return "masculino"
    if last == "masculino":
        return "feminino" if f_cnt <= m_cnt else "ambos"
    return "masculino" if m_cnt <= f_cnt else "feminino"


def resolve_voice_gender(story: dict, history: dict) -> str:
    aud = story.get("audience", "ambos")
    if aud in ("masculino", "feminino"):
        return aud
    last_vg = next((p.get("voice_gender") for p in reversed(history.get("posted", [])) if p.get("voice_gender")), "feminino")
    return "masculino" if last_vg == "feminino" else "feminino"


def _validate_v5_story(parsed: dict) -> bool:
    if not all(parsed.get(k) for k in ("topic", "audience", "music_bed", "emotion_direction", "scenes", "caption")):
        return False
    if parsed.get("audience") not in ("masculino", "feminino", "ambos"):
        return False
    scenes = parsed.get("scenes")
    if not isinstance(scenes, list) or not (7 <= len(scenes) <= 9):
        return False
    valid_ids = {cid for lst in BROLL_CATALOG.values() for cid in lst}
    for sc in scenes:
        if not isinstance(sc, dict) or not sc.get("spoken") or not sc.get("overlay_type"):
            return False
        if sc.get("broll_id") not in valid_ids:
            return False
    return True


def generate_story(history: dict, forced_audience: str = "auto") -> dict:
    """Seleciona micro-filme curado v5 ou gera nova história cinematográfica via Gemini."""
    target_audience = choose_next_audience(history, forced_audience)
    posted_topics = [item.get("topic") or item.get("verse", "") for item in history.get("posted", [])]

    # Primeiro prioriza nossas histórias cinematográficas artesanais inéditas antes de acionar LLM
    unseen_curated = [s for s in CURATED_STORIES if s["audience"] == target_audience and s["topic"] not in posted_topics]
    if unseen_curated:
        chosen = unseen_curated[0]
        print(f"Selecionada história cinema curada v5 ({target_audience}): {chosen['topic']}")
        return chosen

    if GEMINI_API_KEY and os.environ.get("USE_CURATED_ONLY") != "1":
        recent = posted_topics[-25:]
        aud_guide = {
            "masculino": "PROTAGONISTA HOMEM (ex: Lucas, Bruno, Diego, Felipe) vivendo uma história real tensa pós-término com ex-namorada/esposa. Postura, respeito, zero vitimismo.",
            "feminino": "PROTAGONISTA MULHER (ex: Camila, Marina, Sofia, Helena) vivendo uma história real tensa pós-término com ex-namorado/marido. Amor-próprio, lucidez e virada forte.",
            "ambos": "NARRATIVA UNIVERSAL EM 2ª PESSOA ('você') aplicando neurociência/psicologia real tanto para homens quanto para mulheres.",
        }[target_audience]
        prompt = f"""
Você é roteirista de cinema e especialista em Reels virais de alta conversão para o produto CÓDIGO ZERO (Protocolo Imersivo 14 Dias, Central SOS e 16 Scripts anti-recaída pós-término; WhatsApp na bio: {WHATSAPP_DISPLAY}).
Público desta história: {aud_guide}
Crie um MICRO-FILME NARRATIVO DE EXATAMENTE 8 CENAS (85 a 115 palavras no total, 28 a 36 segundos falados), contando uma HISTÓRIA ENVOLVENTE do início ao fim, DIFERENTE destes temas: {recent}.

Estrutura obrigatória das 8 cenas em `scenes`:
- Cena 0: Abertura IN MEDIA RES com horário/detalhe concreto (`overlay_type`: "hook_cinema", chaves `stamp`, `title` <=36 chars CAPS, `hl` 1-2 palavras contidas em title, `hl_color` "gold"|"red", `sub` <=46 chars, `grade`: "night_mood").
- Cena 1: O gatilho concreto (`overlay_type`: "phone_lockscreen", chaves `clock`, `date`, `sender`, `msg` <=48 chars, `grade`: "night_mood").
- Cena 2: Conflito interno visceral (`overlay_type`: "whatsapp_draft", chaves `sender`, `msg` <=52 chars, `seen`, `stamp` <=20 chars CAPS, `grade`: "night_mood").
- Cena 3: O erro que 90% comete (`overlay_type`: "whatsapp_draft" ou "neuro_hud", `grade`: "night_mood").
- Cena 4: A GRANDE VIRADA (com pausa dramática!) (`overlay_type`: "twist_card", `fx`: "dark_drop", `sfx`: "twist", chaves `kicker`, `quote` <=44 chars, `sub` <=48 chars, `grade`: "night_mood").
- Cena 5: A explicação psicológica/neurocientífica real (`overlay_type`: "neuro_hud", chaves `tag`, `main` <=64 chars, `grade`: "night_mood").
- Cena 6: A transformação / vitória emocional (`overlay_type`: "twist_card", `fx`: "warm_flash", `grade`: "warm_gold", chaves `kicker`, `quote` <=42 chars, `sub` <=48 chars).
- Cena 7: CTA de alta conversão mencionando "Comenta ZERO" (`overlay_type`: "ig_dm_cta", `sfx`: "cta_pop", `grade`: "warm_gold").

Regras rígidas:
- Português brasileiro humano e cinematográfico ("tá", "pra", pausas naturais com "..."). ZERO travessões "—", ZERO palestrinha chata de "passo 1, passo 2", ZERO "pare de rolar".
- Cada cena DEVE escolher um `broll_id` ÚNICO (sem repetir ID no mesmo vídeo!) deste catálogo: {json.dumps(BROLL_CATALOG)}.
- `camera`: alternar "push_in", "pan_left", "pan_right".
- `music_bed`: um de ["cinema_piano", "cinema_strings", "cinema_ambient", "cinema_epic"].
- `caption`: legenda magnética de alta conversão com CTA "Comenta ZERO agora ou chama no WhatsApp da bio: {WHATSAPP_DISPLAY}." e 5 hashtags.

Retorne APENAS JSON válido com: topic, audience, music_bed, emotion_direction, scenes, caption.
"""
        body = json.dumps({
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseMimeType": "application/json", "temperature": 0.92},
        }).encode("utf-8")
        for model in ["gemini-2.5-flash", "gemini-2.5-flash-lite"]:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
            for attempt in range(2):
                try:
                    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
                    with urllib.request.urlopen(req, timeout=45) as resp:
                        res = json.loads(resp.read().decode("utf-8"))
                    raw = res["candidates"][0]["content"]["parts"][0]["text"].strip()
                    raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.I)
                    parsed = json.loads(raw)
                    if _validate_v5_story(parsed):
                        parsed["caption"] = parsed["caption"].replace("—", "-").replace("link da bio", "WhatsApp da bio")
                        for sc in parsed["scenes"]:
                            sc["spoken"] = sc["spoken"].replace("—", ",")
                        print(f"História cinema v5 ({target_audience}) criada via Gemini ({model})!")
                        return parsed
                except Exception as exc:
                    print(f"Aviso Gemini história v5 ({model}, #{attempt+1}): {exc}")
                    time.sleep(1.5)

    pool = [s for s in CURATED_STORIES if s["audience"] == target_audience] or CURATED_STORIES
    recent_set = set(posted_topics[-8:])
    fresh = [s for s in pool if s["topic"] not in recent_set] or pool
    return random.choice(fresh)


def _postprocess_voice(raw_mp3: Path, out_mp3: Path) -> float:
    """Remove pausas robóticas longas (>0.38s) e aplica ritmo cinematográfico ágil (1.06x) preservando timbre."""
    subprocess.check_call([
        "ffmpeg", "-y", "-v", "error", "-i", str(raw_mp3),
        "-af", (
            "silenceremove=start_periods=1:start_duration=0.05:start_threshold=-42dB:"
            "stop_periods=-1:stop_duration=0.38:stop_threshold=-38dB,"
            "atempo=1.06,highpass=f=80"
        ),
        "-c:a", "libmp3lame", "-q:a", "2", "-ar", "44100", "-ac", "2", str(out_mp3),
    ])
    return float(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(out_mp3),
    ]).decode().strip())


def synthesize_cinematic_voice(narration: str, emotion: str, voice_gender: str, out_mp3: Path, local_voice: str = "") -> tuple[float, list[dict], dict]:
    """Voz 100% expressiva de narração cinematográfica (Enceladus/Fenrir masculino; Sulafat/Aoede feminino)."""
    profile = VOICE_PROFILES.get(voice_gender, VOICE_PROFILES["feminino"])
    tts_info = {"tts_engine": "", "tts_voice": "", "tts_gender": voice_gender, "tts_error": None}
    raw_mp3 = BUILD_DIR / "voz_raw.mp3"

    if local_voice and Path(local_voice).exists():
        shutil.copyfile(local_voice, out_mp3)
        dur = float(subprocess.check_output([
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(out_mp3),
        ]).decode().strip())
        tts_info.update({"tts_engine": "local-override", "tts_voice": Path(local_voice).name})
        return dur, [], tts_info

    pcm_path = BUILD_DIR / "voz_raw.pcm"
    tts_prompt = (
        f"{profile['audio_profile']}\n"
        f"## DIREÇÃO DE ATUAÇÃO\n{emotion}\n"
        "Ritmo: Português do Brasil autêntico, envolvente e cinematográfico. "
        "Dê emoção verdadeira nas frases dramáticas, mude o tom na virada da história e termine com autoridade calorosa.\n\n"
        f"## ROTEIRO PARA NARRAR\n{narration}"
    )

    if GEMINI_API_KEY:
        models = ["gemini-2.5-flash-preview-tts", "gemini-2.5-flash-tts"]
        top_two = profile["gemini_voices"][:2]
        random.shuffle(top_two)
        voices = top_two + profile["gemini_voices"][2:]
        for model in models:
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
                    with urllib.request.urlopen(req, timeout=50) as resp:
                        res = json.loads(resp.read().decode("utf-8"))
                    parts = res["candidates"][0]["content"]["parts"]
                    inline = next((p.get("inlineData") or p.get("inline_data") for p in parts if p.get("inlineData") or p.get("inline_data")), None)
                    if not inline or not inline.get("data"):
                        raise RuntimeError("Resposta sem inlineData")
                    audio_bytes = base64.b64decode(inline["data"])
                    if len(audio_bytes) < 10_000:
                        raise RuntimeError("Áudio curto demais")
                    mime = inline.get("mimeType") or inline.get("mime_type") or "audio/L16;rate=24000"
                    rate_m = re.search(r"rate=(\d+)", mime)
                    sample_rate = int(rate_m.group(1)) if rate_m else 24000
                    pcm_path.write_bytes(audio_bytes)
                    subprocess.check_call([
                        "ffmpeg", "-y", "-v", "error", "-f", "s16le", "-ar", str(sample_rate), "-ac", "1",
                        "-i", str(pcm_path), "-c:a", "libmp3lame", "-q:a", "2", "-ar", "44100", "-ac", "2", str(raw_mp3),
                    ])
                    dur = _postprocess_voice(raw_mp3, out_mp3)
                    if dur < 10.0 or dur > 115.0:
                        raise RuntimeError(f"Duração anômala: {dur:.2f}s")
                    tts_info.update({"tts_engine": f"gemini:{model}", "tts_voice": vname, "tts_error": None})
                    print(f"TTS_ENGINE=gemini ({model}, gender={voice_gender}, voice={vname}, dur={dur:.2f}s)")
                    return dur, [], tts_info
                except urllib.error.HTTPError as err:
                    err_body = err.read().decode("utf-8", errors="ignore")[:220]
                    tts_info["tts_error"] = f"{model}/{vname} HTTP {err.code}: {err_body}"
                    print(f"Aviso Gemini TTS: {tts_info['tts_error']}")
                    if err.code in (429, 500, 503):
                        time.sleep(2)
                except Exception as exc:
                    tts_info["tts_error"] = f"{model}/{vname}: {exc}"
                    print(f"Aviso Gemini TTS: {tts_info['tts_error']}")

    # Edge TTS backup (sempre com ritmo cinema e fallback limpo)
    tts_text = narration.replace("...", ",")
    chosen_edge = profile["edge_voices"][0]
    for ev in profile["edge_voices"]:
        try:
            import edge_tts

            async def _run(v=ev) -> None:
                comm = edge_tts.Communicate(text=tts_text, voice=v, rate=profile["edge_rate"], pitch=profile["edge_pitch"])
                await comm.save(str(raw_mp3))

            asyncio.run(_run())
            chosen_edge = ev
            if raw_mp3.exists() and raw_mp3.stat().st_size > 8_000:
                break
        except Exception as exc:
            print(f"Aviso edge_tts ({ev}): {exc}")

    if not raw_mp3.exists() or raw_mp3.stat().st_size < 4_000:
        tts_prefix = ["edge-tts"] if shutil.which("edge-tts") else ["uvx", "edge-tts"]
        subprocess.check_call(tts_prefix + [
            "--voice", chosen_edge, f"--rate={profile['edge_rate']}", "--text", tts_text, "--write-media", str(raw_mp3),
        ])

    dur = _postprocess_voice(raw_mp3, out_mp3)
    tts_info.update({"tts_engine": "edge-tts-fallback", "tts_voice": chosen_edge})
    print(f"TTS_ENGINE=edge-tts ({chosen_edge}, dur={dur:.2f}s)")
    return dur, [], tts_info


def _normalize_tok(t: str) -> str:
    return re.sub(r"[^\wà-ÿ]", "", t.lower())


def align_words_to_audio(narration: str, mp3_path: Path, dur: float) -> tuple[list[dict], str, str]:
    """Alinha cada palavra da história ao áudio processado com precisão de milissegundos."""
    script_tokens = re.findall(r"\S+", narration)
    if not script_tokens:
        return [], "empty", ""

    try:
        import numpy as np
        from faster_whisper import WhisperModel

        raw16k = BUILD_DIR / "voz16k.raw"
        subprocess.check_call([
            "ffmpeg", "-y", "-v", "error", "-i", str(mp3_path),
            "-ar", "16000", "-ac", "1", "-f", "f32le", str(raw16k),
        ])
        audio_np = np.fromfile(str(raw16k), dtype=np.float32)
        model = WhisperModel("tiny", device="cpu", compute_type="int8")
        segments, _ = model.transcribe(audio_np, language="pt", word_timestamps=True, vad_filter=True)
        raw_words: list[dict] = []
        for seg in segments:
            for w in getattr(seg, "words", []) or []:
                txt = (w.word or "").strip()
                if txt:
                    raw_words.append({"text": txt, "norm": _normalize_tok(txt), "start": float(w.start), "end": float(w.end)})

        if len(raw_words) >= max(8, len(script_tokens) // 3):
            s_norms = [_normalize_tok(t) for t in script_tokens]
            w_norms = [w["norm"] for w in raw_words]
            matcher = difflib.SequenceMatcher(None, s_norms, w_norms, autojunk=False)
            timings: list[tuple[float, float] | None] = [None] * len(script_tokens)

            for tag, i1, i2, j1, j2 in matcher.get_opcodes():
                if tag == "equal":
                    for k in range(i2 - i1):
                        rw = raw_words[j1 + k]
                        timings[i1 + k] = (rw["start"], max(rw["start"] + 0.08, rw["end"]))
                elif tag == "replace" and (i2 - i1) > 0 and (j2 - j1) > 0:
                    span_s = raw_words[j1]["start"]
                    span_e = max(span_s + 0.12, raw_words[j2 - 1]["end"])
                    weights = [max(1, len(s_norms[idx])) for idx in range(i1, i2)]
                    tot_w = sum(weights)
                    cur_t = span_s
                    for idx, wt in zip(range(i1, i2), weights):
                        part = (span_e - span_s) * (wt / tot_w)
                        timings[idx] = (cur_t, cur_t + max(0.08, part))
                        cur_t += part

            idx = 0
            while idx < len(timings):
                if timings[idx] is not None:
                    idx += 1
                    continue
                end_gap = idx
                while end_gap < len(timings) and timings[end_gap] is None:
                    end_gap += 1
                prev_end = timings[idx - 1][1] if idx > 0 and timings[idx - 1] else raw_words[0]["start"]
                next_start = timings[end_gap][0] if end_gap < len(timings) and timings[end_gap] else raw_words[-1]["end"]
                if next_start <= prev_end:
                    next_start = prev_end + 0.22 * (end_gap - idx)
                weights = [max(1, len(s_norms[k])) for k in range(idx, end_gap)]
                tot_w = sum(weights)
                cur_t = prev_end
                for k, wt in zip(range(idx, end_gap), weights):
                    part = (next_start - prev_end) * (wt / tot_w)
                    timings[k] = (cur_t, cur_t + max(0.07, part))
                    cur_t += part
                idx = end_gap

            aligned = [
                {"text": tok, "start": round(st, 3), "end": round(max(st + 0.08, en), 3)}
                for tok, (st, en) in zip(script_tokens, timings)  # type: ignore[misc]
            ]
            return aligned, "faster-whisper-tiny", " ".join(w["text"] for w in raw_words[:18])
    except Exception as exc:
        print(f"Aviso faster-whisper fallback ({exc}); usando ponderação proporcional...")

    weights = [max(2, len(_normalize_tok(t)) + (2 if re.search(r"[.!?,]$", t) else 0)) for t in script_tokens]
    tot_w = sum(weights)
    aligned = []
    cur_t = 0.05
    usable = max(2.0, dur - 0.1)
    for tok, wt in zip(script_tokens, weights):
        part = usable * (wt / tot_w)
        aligned.append({"text": tok, "start": round(cur_t, 3), "end": round(cur_t + max(0.08, part), 3)})
        cur_t += part
    return aligned, "weighted-char-fallback", ""


def align_scenes_exact(scenes: list[dict], words: list[dict], voice_dur: float, delay: float = 0.15) -> tuple[list[dict], float, float]:
    """
    Mapeia 100% deterministicamente os limites [start, end] de CADA cena
    pelo índice exato de palavras da fala (ZERO drift visual!).
    """
    poster_at = round(voice_dur + delay + 0.2, 2)
    total_dur = round(poster_at + 2.2, 1)

    word_cursor = 0
    raw_starts: list[float] = []
    for idx, sc in enumerate(scenes):
        sc_toks = re.findall(r"\S+", sc["spoken"])
        if idx == 0:
            raw_starts.append(0.0)
        elif word_cursor < len(words):
            raw_starts.append(round(words[word_cursor]["start"] + delay, 2))
        else:
            raw_starts.append(round((idx / len(scenes)) * voice_dur + delay, 2))
        word_cursor += len(sc_toks)

    # Garante monotonia estrita sem nunca esmagar a última cena
    timed: list[dict] = []
    for idx, sc in enumerate(scenes):
        st = raw_starts[idx]
        if idx > 0 and st < timed[-1]["start"] + 1.0:
            st = round(timed[-1]["start"] + 1.0, 2)
        timed.append({
            "idx": idx,
            "start": st,
            "end": poster_at,
            "fx": sc.get("fx", "none"),
            "sfx": sc.get("sfx", ""),
            "overlay_type": sc["overlay_type"],
            "broll_id": sc["broll_id"],
            "grade": sc.get("grade", "night_mood"),
            "camera": sc.get("camera", "push_in"),
        })
    for idx in range(len(timed) - 1):
        timed[idx]["end"] = timed[idx + 1]["start"]

    # Assegura que a última cena (CTA) tenha pelo menos 2.4s antes do pôster final
    if timed[-1]["end"] - timed[-1]["start"] < 2.4:
        poster_at = round(timed[-1]["start"] + 2.4, 2)
        timed[-1]["end"] = poster_at
        total_dur = round(poster_at + 2.2, 1)

    return timed, poster_at, total_dur


def build_caption_chunks(words: list[dict], delay_offset: float = 0.15) -> tuple[list[dict], str]:
    """Legendas flutuantes limpas de cinema (2–3 palavras, leitura instantânea no celular)."""
    chunks: list[dict] = []
    cur: list[dict] = []
    cur_len = 0

    for w in words:
        raw_txt = w["text"].strip()
        if not raw_txt:
            continue
        clean = _normalize_tok(raw_txt)
        item = {
            "text": raw_txt,
            "start": round(w["start"] + delay_offset, 3),
            "end": round(w["end"] + delay_offset, 3),
            "emphasis": clean in EMPHASIS_WORDS,
        }
        prev_gap = (item["start"] - cur[-1]["end"]) if cur else 0.0
        starts_new_sentence = (
            bool(cur)
            and raw_txt[0].isupper()
            and clean not in {"zero", "whatsapp", "instagram", "sos", "michigan", "lucas", "camila", "rafael", "marina", "bruno", "larissa", "thiago", "júlia", "julia", "mateus", "beatriz"}
            and prev_gap >= 0.14
        )
        ends_sentence = bool(re.search(r"[.!?]$", raw_txt))
        if cur and (len(cur) >= 3 or cur_len + len(raw_txt) > 19 or prev_gap >= 0.24 or starts_new_sentence):
            chunks.append({"start": cur[0]["start"], "end": cur[-1]["end"], "words": cur})
            cur = []
            cur_len = 0
        cur.append(item)
        cur_len += len(raw_txt) + 1
        if ends_sentence and len(cur) >= 2:
            chunks.append({"start": cur[0]["start"], "end": cur[-1]["end"], "words": cur})
            cur = []
            cur_len = 0

    if cur:
        chunks.append({"start": cur[0]["start"], "end": cur[-1]["end"], "words": cur})

    for i in range(len(chunks) - 1):
        next_start = chunks[i + 1]["start"]
        if next_start - chunks[i]["end"] < 0.35:
            chunks[i]["end"] = max(chunks[i]["end"], round(next_start - 0.02, 3))

    html_parts: list[str] = []
    for ci, ch in enumerate(chunks):
        spans = " ".join(f'<span class="w" id="w-{ci}-{wi}">{html.escape(w["text"])}</span>' for wi, w in enumerate(ch["words"]))
        html_parts.append(f'<div class="cap-chunk" id="chunk-{ci}">{spans}</div>')
    return chunks, "\n".join(html_parts)


def _is_valid_mp4(path: Path) -> bool:
    if not path.exists() or path.stat().st_size < 150_000:
        return False
    try:
        out = subprocess.check_output(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
            stderr=subprocess.STDOUT,
            text=True,
        ).strip()
        return float(out) > 1.5
    except Exception:
        return False


def prep_cinema_shot(clip_id: str, dur_needed: float, grade: str, camera: str, out_mp4: Path, fallback_ids: list[str]) -> str:
    """
    Baixa clipe HD real do Mixkit (com cache), aplica LUT cinema luminosa (night_mood ou warm_gold),
    movimento vivo de câmera (pan suave) e GOP curto (-g 10) para seek perfeito no HyperFrames.
    """
    curl_bin = shutil.which("curl.exe") or shutil.which("curl") or "curl"
    candidates = [clip_id] + [x for x in fallback_ids if x != clip_id]
    raw_file = None
    used_id = clip_id

    for cid in candidates:
        cached = BROLL_CACHE_DIR / f"{cid}-720.mp4"
        if _is_valid_mp4(cached):
            raw_file = cached
            used_id = cid
            break
        if cached.exists():
            cached.unlink(missing_ok=True)
        url = f"https://assets.mixkit.co/videos/{cid}/{cid}-720.mp4"
        try:
            subprocess.check_call([curl_bin, "-fsSL", "--retry", "2", "--max-time", "28", "-A", "Mozilla/5.0", "-o", str(cached), url])
            if _is_valid_mp4(cached):
                raw_file = cached
                used_id = cid
                print(f"B-roll cinema baixado: {cid}")
                break
            cached.unlink(missing_ok=True)
        except Exception as exc:
            cached.unlink(missing_ok=True)
            print(f"Aviso B-roll {cid}: {exc}")

    clip_dur = round(max(2.2, dur_needed + 0.3), 2)
    if grade == "warm_gold":
        lut = "eq=contrast=1.06:saturation=1.08:gamma=1.10,colorbalance=rs=0.04:gs=0.02:bs=-0.04,vignette=PI/7"
    else:
        lut = "eq=contrast=1.08:saturation=0.90:gamma=1.10,colorbalance=rs=-0.02:bs=0.04,vignette=PI/6"

    # Movimento suave e rápido de câmera em crop vertical 1080x1920
    if camera == "pan_left":
        cam_vf = f"scale=1180:2098:force_original_aspect_ratio=increase,crop=1080:1920:x='(iw-1080)*0.65 - (iw-1080)*0.30*min(1,t/{clip_dur})':y='(ih-1920)/2'"
    elif camera == "pan_right":
        cam_vf = f"scale=1180:2098:force_original_aspect_ratio=increase,crop=1080:1920:x='(iw-1080)*0.35 + (iw-1080)*0.30*min(1,t/{clip_dur})':y='(ih-1920)/2'"
    else:
        cam_vf = f"scale=1160:2062:force_original_aspect_ratio=increase,crop=1080:1920:x='(iw-1080)/2':y='(ih-1920)*0.55 - (ih-1920)*0.18*min(1,t/{clip_dur})'"

    if raw_file and raw_file.exists():
        subprocess.check_call([
            "ffmpeg", "-y", "-v", "error",
            "-stream_loop", "-1", "-i", str(raw_file),
            "-t", str(clip_dur),
            "-vf", f"fps=30,{cam_vf},{lut}",
            "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-g", "10",
            "-pix_fmt", "yuv420p", "-an", "-movflags", "+faststart", str(out_mp4),
        ])
        return used_id

    subprocess.check_call([
        "ffmpeg", "-y", "-v", "error", "-f", "lavfi",
        "-i", f"color=c=#14161e:s=1080x1920:r=30:d={clip_dur}",
        "-vf", "noise=alls=6:allf=t+u,vignette=PI/4",
        "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-g", "10", "-pix_fmt", "yuv420p", str(out_mp4),
    ])
    return "fallback-dark"


def resolve_cinema_score(bed_name: str) -> Path:
    local_bed = ASSETS_DIR / "music" / f"{bed_name}.mp3"
    if local_bed.exists() and local_bed.stat().st_size > 25_000:
        return local_bed
    fallback = ASSETS_DIR / "music" / "cinema_piano.mp3"
    if fallback.exists():
        return fallback
    out = BUILD_DIR / "score_fallback.mp3"
    subprocess.check_call([
        "ffmpeg", "-y", "-v", "error", "-f", "lavfi",
        "-i", "aevalsrc=0.10*sin(2*PI*146.83*t)+0.06*sin(2*PI*220*t):s=44100:d=50",
        "-af", "lowpass=f=420", str(out),
    ])
    return out


def build_scene_overlay_html(idx: int, sc: dict) -> str:
    otype = sc["overlay_type"]
    if otype == "hook_cinema":
        title = sc.get("title", "")
        hl = sc.get("hl", "")
        cls = "hl-red" if sc.get("hl_color") == "red" else "hl-gold"
        if hl and hl in title:
            pos = title.index(hl)
            title_html = (
                html.escape(title[:pos])
                + f'<span class="{cls}">{html.escape(hl)}</span>'
                + html.escape(title[pos + len(hl):])
            )
        else:
            title_html = html.escape(title)
        return f"""
          <div class="sc-layer" id="sc-{idx}">
            <div class="story-stamp">{html.escape(sc.get("stamp", "HISTÓRIA REAL"))}</div>
            <div class="hook-cinema-title">{title_html}</div>
            <div class="hook-cinema-sub">{html.escape(sc.get("sub", ""))}</div>
          </div>
        """

    if otype == "phone_lockscreen":
        return f"""
          <div class="sc-layer" id="sc-{idx}">
            <div class="lock-wrap">
              <div class="lock-clock">{html.escape(sc.get("clock", "02:14"))}</div>
              <div class="lock-date">{html.escape(sc.get("date", "Madrugada"))}</div>
              <div class="ios-glass-card">
                <div class="ios-top" data-layout-ignore="true"><span>● MENSAGEM</span><span>AGORA</span></div>
                <div class="ios-sender">{html.escape(sc.get("sender", "Ex"))}</div>
                <div class="ios-body">{html.escape(sc.get("msg", ""))}</div>
              </div>
            </div>
          </div>
        """

    if otype == "whatsapp_draft":
        stamp_html = f'<div class="drama-stamp">{html.escape(sc["stamp"])}</div>' if sc.get("stamp") else ""
        return f"""
          <div class="sc-layer" id="sc-{idx}" style="justify-content:center;">
            <div class="ios-glass-card">
              <div class="ios-top" data-layout-ignore="true"><span>CHAT • WHATSAPP</span><span>AO VIVO</span></div>
              <div class="ios-sender">{html.escape(sc.get("sender", ""))}</div>
              <div class="ios-body">{html.escape(sc.get("msg", ""))}</div>
              <div class="ios-seen-row"><span>{html.escape(sc.get("seen", ""))}</span></div>
              {stamp_html}
            </div>
          </div>
        """

    if otype == "twist_card":
        return f"""
          <div class="sc-layer" id="sc-{idx}">
            <div class="twist-wrap">
              <div class="twist-kicker">{html.escape(sc.get("kicker", "A VIRADA"))}</div>
              <div class="twist-serif">{html.escape(sc.get("quote", ""))}</div>
              <div class="twist-rule"></div>
              <div class="twist-sub">{html.escape(sc.get("sub", ""))}</div>
            </div>
          </div>
        """

    if otype == "neuro_hud":
        return f"""
          <div class="sc-layer" id="sc-{idx}" style="justify-content:center;">
            <div class="neuro-hud">
              <div class="neuro-tag">{html.escape(sc.get("tag", "NEUROCIÊNCIA"))}</div>
              <div class="neuro-main">{html.escape(sc.get("main", ""))}</div>
              <svg viewBox="0 0 600 44" width="100%" height="40">
                <path class="hud-pulse" d="M 4 24 L 110 24 L 140 6 L 166 40 L 194 12 L 222 34 L 250 24 L 410 24 L 435 12 L 460 34 L 485 24 L 596 24"
                  fill="none" stroke="#f5b73b" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"
                  pathLength="100" stroke-dasharray="100 120" stroke-dashoffset="105"/>
              </svg>
            </div>
          </div>
        """

    # ig_dm_cta
    return f"""
      <div class="sc-layer" id="sc-{idx}">
        <div class="cta-cinema-wrap">
          <div class="dm-pill">
            <div class="dm-badge">CZ</div>
            <div>
              <div style="font-size:25px;font-weight:800;">@protocolocodigozero • agora</div>
              <div style="font-size:23px;font-weight:600;color:#3d4049;">Protocolo 14 Dias + 16 Scripts enviados no DM</div>
            </div>
          </div>
          <div class="ig-drawer">
            <div class="ig-drawer-head">Comentários</div>
            <div class="ig-row ig-new" style="opacity:0;">
              <div class="ig-av">V</div>
              <div>
                <div style="font-size:22px;font-weight:800;">@voce • agora</div>
                <div style="font-size:27px;font-weight:800;">ZERO</div>
              </div>
            </div>
            <div class="ig-row" style="opacity:0.75;">
              <div class="ig-av" style="background:#ff3b5c;">L</div>
              <div>
                <div style="font-size:21px;font-weight:700;">@lucas_m • 2 min</div>
                <div style="font-size:25px;font-weight:700;">ZERO</div>
              </div>
            </div>
            <div class="ig-bar">
              <div class="ig-ph" style="font-family:'JetBrains Mono',monospace;font-size:27px;font-weight:700;color:#6d707a;">Comente ZERO...</div>
              <div class="ig-zero" style="position:absolute;left:20px;opacity:0;font-family:'JetBrains Mono',monospace;font-size:28px;font-weight:800;color:#111216;">ZERO</div>
              <div class="ig-btn">Publicar</div>
            </div>
          </div>
        </div>
      </div>
    """


def main() -> None:
    parser = argparse.ArgumentParser(description="Código Zero Cinema Storytelling v5")
    parser.add_argument("--audience", default="auto", choices=["auto", "masculino", "feminino", "ambos"])
    parser.add_argument("--local-voice", default="", help="MP3 local opcional para teste offline")
    parser.add_argument("--render-only", action="store_true", help="Não grava history.json (modo QA)")
    args = parser.parse_args()

    history = load_history()
    print("1. Selecionando/criando micro-filme narrativo v5...")
    story = generate_story(history, forced_audience=args.audience)
    voice_gender = resolve_voice_gender(story, history)
    scenes = story["scenes"]
    full_narration = " ".join(sc["spoken"].strip() for sc in scenes)
    print(f"História: {story['topic']} | Público={story['audience']} | Voz={voice_gender} | Cenas={len(scenes)}")

    print("2. Sintetizando voz humana cinematográfica (Enceladus/Fenrir ou Sulafat/Aoede)...")
    voz_path = BUILD_DIR / "voz.mp3"
    voice_dur, _, tts_info = synthesize_cinematic_voice(
        full_narration, story.get("emotion_direction", "Emocional e envolvente"),
        voice_gender, voz_path, local_voice=args.local_voice,
    )

    print("3. Alinhando 100% das palavras e cenas (0.00s drift)...")
    words, sync_engine, preview = align_words_to_audio(full_narration, voz_path, voice_dur)
    timed_scenes, poster_at, total_dur = align_scenes_exact(scenes, words, voice_dur, delay=0.15)
    print(f"Duração={total_dur}s | Poster={poster_at}s | Cenas={[s['start'] for s in timed_scenes]} | Sync={sync_engine}")

    print("4. Preparando 8 planos reais HD Mixkit (LUT cinema + câmera viva)...")
    hf_dir = BUILD_DIR / "hf_proj"
    assets_hf = hf_dir / "assets"
    assets_hf.mkdir(parents=True, exist_ok=True)

    shots_html: list[str] = []
    overlays_html: list[str] = []
    used_brolls: list[str] = []
    fb_pool = BROLL_CATALOG["mood_dark"]

    for i, tsc in enumerate(timed_scenes):
        sc = scenes[i]
        # A última cena continua passando suavemente atrás do End Poster translúcido até total_dur
        vid_end = total_dur if i == len(timed_scenes) - 1 else tsc["end"]
        vid_dur = round(max(1.2, vid_end - tsc["start"]), 2)
        shot_file = assets_hf / f"shot{i}.mp4"
        used_id = prep_cinema_shot(tsc["broll_id"], vid_dur, tsc["grade"], tsc["camera"], shot_file, fb_pool)
        used_brolls.append(used_id)
        shots_html.append(
            f'<video id="shot{i}" class="clip shot-vid" data-start="{tsc["start"]}" '
            f'data-duration="{vid_dur}" src="assets/shot{i}.mp4" muted playsinline></video>'
        )
        overlays_html.append(build_scene_overlay_html(i, sc))

    chunks, captions_html = build_caption_chunks(words, delay_offset=0.15)

    tpl = (ROOT / "template.html").read_text(encoding="utf-8")
    replacements = {
        "__DURATION__": str(total_dur),
        "__POSTER_AT__": str(poster_at),
        "__SHOTS_HTML__": "\n        ".join(shots_html),
        "__SCENES_HTML__": "\n        ".join(overlays_html),
        "__SCENES_META_JSON__": json.dumps(timed_scenes, ensure_ascii=False),
        "__CAPTIONS_HTML__": captions_html,
        "__CHUNKS_JSON__": json.dumps(chunks, ensure_ascii=False),
    }
    for k, v in replacements.items():
        tpl = tpl.replace(k, v)
    (hf_dir / "index.html").write_text(tpl, encoding="utf-8")

    print("5. Renderizando curta-metragem 1080x1920 via HyperFrames...")
    video_no_audio = BUILD_DIR / "video_v5.mp4"
    hf_cmd = (
        ["cmd", "/c", "npx", "--yes", "hyperframes", "render", ".", "--output", str(video_no_audio)]
        if os.name == "nt"
        else ["npx", "--yes", "hyperframes", "render", ".", "--output", str(video_no_audio)]
    )
    subprocess.check_call(hf_cmd, cwd=str(hf_dir))

    print("6. Mixando trilha orquestral real com silence-drop dramático na virada e master -14 LUFS...")
    score_path = resolve_cinema_score(story.get("music_bed", "cinema_piano"))
    sfx_riser = ASSETS_DIR / "sfx" / "riser.mp3"
    sfx_boom = ASSETS_DIR / "sfx" / "impact-boom.mp3"
    sfx_pop = ASSETS_DIR / "sfx" / "pop-back.mp3"

    twist_sc = next((s for s in timed_scenes if s.get("sfx") == "twist"), timed_scenes[len(timed_scenes) // 2])
    cta_sc = next((s for s in timed_scenes if s.get("sfx") == "cta_pop"), timed_scenes[-1])
    twist_t = twist_sc["start"]
    cta_t = cta_sc["start"]

    # Silence drop na trilha de música bem no segundo exato da virada!
    drop_s = round(max(1.5, twist_t - 0.30), 2)
    drop_e = round(min(total_dur - 1.5, twist_t + 0.38), 2)
    fade_out_start = round(max(1.5, total_dur - 2.3), 2)

    final_path = BUILD_DIR / "reel_final.mp4"
    cmd_mix = ["ffmpeg", "-y", "-v", "error", "-i", str(video_no_audio), "-i", str(voz_path), "-i", str(score_path)]
    extra_inputs: list[tuple[Path, int, float]] = []
    if sfx_riser.exists():
        # Riser (2.6s) crescendo até o silêncio da virada
        extra_inputs.append((sfx_riser, max(100, int((twist_t - 2.4) * 1000)), 0.16))
    if sfx_boom.exists():
        # Impact boom profundo exatamente no retorno pós-silêncio da virada
        extra_inputs.append((sfx_boom, max(200, int((twist_t + 0.12) * 1000)), 0.28))
    if sfx_pop.exists():
        # Pop limpo no comentário ZERO da gaveta do Instagram
        extra_inputs.append((sfx_pop, max(200, int((cta_t + 0.55) * 1000)), 0.28))

    for p, _, _ in extra_inputs:
        cmd_mix.extend(["-i", str(p)])

    filters = [
        f"[1:a]aformat=sample_rates=44100:channel_layouts=stereo,adelay=150|150,"
        f"highpass=f=80,equalizer=f=3200:t=q:w=1.4:g=2.2,"
        f"acompressor=threshold=-17dB:ratio=2.6:attack=6:release=60,volume=1.55,"
        f"apad=whole_dur={total_dur},asplit=2[vmain][vsc]",
        f"[2:a]aformat=sample_rates=44100:channel_layouts=stereo,atrim=0:{total_dur},asetpts=PTS-STARTPTS,"
        f"volume='if(between(t,{drop_s},{drop_e}),0.04,1)':eval=frame,"
        f"afade=t=in:st=0:d=0.6,afade=t=out:st={fade_out_start}:d=2.3,volume=0.34[bgmraw]",
        "[bgmraw][vsc]sidechaincompress=threshold=0.032:ratio=4.5:attack=25:release=300[bgmduck]",
    ]
    mix_labels = ["[vmain]", "[bgmduck]"]
    for idx, (_, ms, vol) in enumerate(extra_inputs, start=3):
        lbl = f"[sfx{idx}]"
        filters.append(f"[{idx}:a]aformat=sample_rates=44100:channel_layouts=stereo,volume={vol},adelay={ms}|{ms}{lbl}")
        mix_labels.append(lbl)

    filters.append(
        f"{''.join(mix_labels)}amix=inputs={len(mix_labels)}:duration=first:dropout_transition=2:normalize=0,"
        "loudnorm=I=-14:TP=-1.5:LRA=7,alimiter=limit=0.95[aout]"
    )

    cmd_mix.extend([
        "-filter_complex", ";".join(filters),
        "-map", "0:v", "-map", "[aout]",
        "-c:v", "libx264", "-profile:v", "high", "-level", "4.1", "-crf", "16", "-preset", "medium", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-movflags", "+faststart",
        "-t", str(total_dur), str(final_path),
    ])
    subprocess.check_call(cmd_mix)

    (BUILD_DIR / "caption.txt").write_text(story["caption"], encoding="utf-8")
    tt_base = re.sub(r"\(?\d{2}\)?\s*\d{4,5}-?\d{4}", "link do perfil", story["caption"])
    tt_base = re.sub(r"#\S+", "", tt_base).strip()
    tt_question = (
        "Você responderia essa mensagem ou manteria o silêncio? 👇"
        if story["audience"] != "ambos"
        else "Qual parte dói mais na abstinência: a madrugada ou acordar? 👇"
    )
    tt_tags = (
        "#relacionamento #termino #contatozero #superacao #psicologia #posturamasculina #codigozero #paravoce #fyp"
        if story["audience"] == "masculino"
        else "#relacionamento #termino #contatozero #amorproprio #superacao #psicologia #codigozero #paravoce #fyp"
    )
    tiktok_caption = (
        f"{tt_question}\n\n{tt_base}\n\n"
        f"Acesse o protocolo completo no link da bio ou comenta ZERO aqui embaixo 👇\n\n{tt_tags}"
    )
    (BUILD_DIR / "caption_tiktok.txt").write_text(tiktok_caption[:2150], encoding="utf-8")
    meta = {
        "engine_version": "v5-cinema-story",
        "date_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "topic": story["topic"],
        "audience": story["audience"],
        "voice_gender": voice_gender,
        "tts_engine": tts_info["tts_engine"],
        "tts_voice": tts_info["tts_voice"],
        "tts_error": tts_info["tts_error"],
        "sync_engine": sync_engine,
        "music_bed": score_path.name,
        "broll_used": used_brolls,
        "duration": total_dur,
        "poster_at": poster_at,
        "twist_silence_drop": [drop_s, drop_e],
        "scenes_timing": [{"idx": s["idx"], "start": s["start"], "end": s["end"], "type": s["overlay_type"]} for s in timed_scenes],
        "transcribed_preview": preview,
    }
    (BUILD_DIR / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    if not args.render_only:
        history["posted"].append({
            "date": meta["date_utc"],
            "topic": story["topic"],
            "audience": story["audience"],
            "voice_gender": voice_gender,
            "music_bed": score_path.name,
            "broll_used": used_brolls,
            "tts_engine": tts_info["tts_engine"],
            "tts_voice": tts_info["tts_voice"],
        })
        save_history(history)
    print(f"Curta-metragem Cinema v5 gerado com sucesso: {final_path}")


if __name__ == "__main__":
    main()

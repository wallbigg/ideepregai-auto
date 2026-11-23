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

VOICE_PROFILES = {
    "masculino": {
        "gemini_voices": ["Charon", "Orus", "Fenrir"],
        "edge_voices": ["pt-BR-AntonioNeural", "pt-BR-FabioNeural", "pt-BR-DonatoNeural"],
        "edge_rate": "-2%",
        "edge_pitch": "-2Hz",
        "audio_profile": (
            "AUDIO PROFILE: Homem brasileiro de 32 anos, voz grave, firme e lúcida, "
            "estilo documentário editorial moderno. Fala direta de respeito próprio após término, "
            "sem tom caricato de coach. Respire brevemente antes das verdades fortes."
        ),
    },
    "feminino": {
        "gemini_voices": ["Sulafat", "Kore", "Aoede"],
        "edge_voices": ["pt-BR-ThalitaMultilingualNeural", "pt-BR-FranciscaNeural"],
        "edge_rate": "-2%",
        "edge_pitch": "+0Hz",
        "audio_profile": (
            "AUDIO PROFILE: Mulher brasileira de 30 anos, voz próxima do microfone, "
            "calma, lúcida e firme, estilo documentário editorial intimista. "
            "Cadência natural e protetora, com pausas curtas antes de frases de corte."
        ),
    },
}

# Clipes Mixkit reais testados com HTTP 200 (zero marca d'água, zero API key)
BROLL_POOL = {
    "masculino_dor": ["4701", "35426", "35889", "46448", "41638"],
    "masculino_foco": ["52079", "4808", "40746", "49878"],
    "feminino_dor": ["8739", "25586", "46702", "43270"],
    "feminino_foco": ["2846", "40746", "49878"],
    "mood": ["28897", "28893", "28901", "2846", "4915", "40746", "49878"],
}

EMPHASIS_WORDS = {
    "não", "nunca", "jamais", "pare", "trava", "silêncio", "zero", "dói",
    "vergonha", "orgulho", "ego", "migalha", "migalhas", "abstinência",
    "noventa", "segundos", "madrugada", "recaída", "stalkear", "bloqueia",
    "dignidade", "paz", "mentira", "armadilha", "whatsapp", "bio", "sozinho",
    "sozinha", "culpa", "queimadura", "física", "reservas", "amigos",
    "respeito", "controle", "desmame", "lucidez", "carência", "atração",
    "homem", "mulher", "ela", "ele", "tempo", "textão", "validação",
}

# 20 roteiros Studio v4 balanceados (8 masculino, 7 feminino, 5 ambos)
CURATED_SCRIPTS = [
    # ── MASCULINO (01..08) ────────────────────────────────────────────────────
    {
        "topic": "Ela pediu um tempo, mas continua ativa nas redes (Masculino #01)",
        "audience": "masculino",
        "music_bed": "thriller",
        "theme_start": "noir",
        "hook_mode": "split",
        "broll_ids": ["4701", "28897", "52079"],
        "case_tag": "HOMENS • ESCUDO #08",
        "emotion_direction": "Grave, direto, postura firme de irmão mais velho sem clichê.",
        "hook_headline": "ELA PEDIU UM TEMPO?",
        "hook_highlight": "TEMPO?",
        "hook_card": {"sender": "Ela • 23:40", "msg": "\"Acho melhor darmos um tempo pra pensar...\"", "stamp": "ARMADILHA CLÁSSICA"},
        "beat1_kicker": "REALIDADE SEM FILTRO",
        "beat1_big": "TEMPO É TESTE DE SAÍDA.",
        "beat1_sub": "Enquanto você espera, ela testa o mercado sem culpa.",
        "board_type": "strike_stat",
        "board_title": "O erro que mata seu respeito",
        "board_big": "90%",
        "board_wrong_lbl": "O QUE A MAIORIA DOS CARAS FAZ",
        "board_wrong": "Manda textão todo dia provando amor e ficando disponível",
        "board_right_lbl": "POSTURA CÓDIGO ZERO",
        "board_right": "Aceita o término no ato e corta 100% da validação",
        "board_source": "REGRA DE DIGNIDADE • PROTOCOLO 14 DIAS",
        "beat3_kicker": "VIRADA MENTAL",
        "beat3_big": "NÃO SEJA PLANO B.",
        "beat3_sub": "Homem disponível demais perde valor na hora.",
        "rehook_text": "Mas quase ninguém faz o passo mais simples.",
        "rehook_sub": "Nos primeiros 7 dias, silêncio vale mais que mil discursos.",
        "steps": [
            {"title": "Aceite em 1 linha", "desc": "Responda: 'Tranquilo, respeito sua decisão.'"},
            {"title": "Corte visualização", "desc": "Não veja stories nem mande checagem diária."},
            {"title": "Volte pro seu eixo", "desc": "Treino, trabalho e sono antes de qualquer tela."},
        ],
        "cue_words": ["testar", "textão", "respeito", "simples", "passo", "ZERO"],
        "narration": (
            "Se ela pediu um tempo e já tá online até tarde... acorda agora. "
            "Ninguém pede tempo pra te amar mais. Ela tá querendo testar a vida solteira sem perder sua rede de segurança. "
            "Se você mandar textão cobrando atenção, mata o resto de respeito que ela ainda tinha por você. "
            "Aceita a escolha em silêncio e sai do palco. "
            "Mas quase ninguém faz o passo mais simples. "
            "Em um passo: diga que respeita, suma dos stories dela e jogue sua energia no treino e no foco. "
            "Comenta ZERO aqui que eu te envio os dezesseis scripts e o protocolo de catorze dias."
        ),
        "caption": (
            "Pedido de tempo quase nunca é dúvida, é saída em câmera lenta.\n\n"
            "Quando o homem tenta segurar no grito ou no textão, ele confirma carência e acelera o afastamento. "
            "No Código Zero você aprende a cortar a validação na hora certa e recuperar seu eixo em 14 dias.\n\n"
            "Comenta ZERO ou chama no WhatsApp da bio: (12) 99659-3222.\n\n"
            "#desenvolvimentomasculino #contatozero #superartermino #postura #codigozero"
        ),
    },
    {
        "topic": "Homem que manda textão implorando mata a atração (Masculino #02)",
        "audience": "masculino",
        "music_bed": "enquete",
        "theme_start": "noir",
        "hook_mode": "cinema",
        "broll_ids": ["35426", "4915", "40746"],
        "case_tag": "HOMENS • ANTI-RECAÍDA",
        "emotion_direction": "Tom lúcido, sério e respeitoso, falando diretamente de homem para homem.",
        "hook_headline": "TEXTÃO MATA SUA ATRAÇÃO.",
        "hook_highlight": "MATA",
        "hook_card": {"sender": "Você • 01:12", "msg": "\"Eu juro que vou mudar, me dá só mais uma chance...\"", "stamp": "CARÊNCIA EXPOSTA"},
        "beat1_kicker": "DINÂMICA REAL",
        "beat1_big": "ATRAÇÃO NÃO SE NEGOCIA.",
        "beat1_sub": "Lógica nunca convence quem já esfriou emocionalmente.",
        "board_type": "strike_stat",
        "board_title": "Textão vs Silêncio Frio",
        "board_big": "0%",
        "board_wrong_lbl": "CHANCE DE RECONQUISTA NO RASTO",
        "board_wrong": "Explicar em 30 linhas tudo que vocês viveram juntos",
        "board_right_lbl": "O QUE MUDA O JOGO",
        "board_right": "Sair de cena de cabeça erguida no mesmo segundo",
        "board_source": "ESTATÍSTICA DE POSTURA • CÓDIGO ZERO",
        "beat3_kicker": "CONTRASTE",
        "beat3_big": "RESPEITO VEM ANTES DE SAUDADE.",
        "beat3_sub": "Ela só sente falta quando você para de orbitar.",
        "rehook_text": "O erro tá em confundir dor com fraqueza.",
        "rehook_sub": "Você pode sangrar por dentro sem se humilhar no WhatsApp.",
        "steps": [
            {"title": "Apague o rascunho já", "desc": "Escreveu textão? Mova para notas, nunca envie."},
            {"title": "Regra de 24 horas", "desc": "Nenhuma resposta sai com o peito acelerado."},
            {"title": "Assuma o volante", "desc": "Retome sua rotina física e mental por 14 dias."},
        ],
        "cue_words": ["lógica", "textão", "respeito", "erro", "apague", "ZERO"],
        "narration": (
            "Para de escrever textão tentando convencer sua ex a ficar. "
            "Atração não obedece a argumento nem a promessa desesperada. A lógica nunca convence quem já desconectou por dentro. "
            "Cada mensagem comprida provando amor só entrega alívio pro ego dela e tira o peso da perda. "
            "Ela só respeita quem consegue se retirar de cena inteiro. "
            "O erro tá em confundir dor com fraqueza. "
            "Apague o rascunho agora, trave o dedo por vinte e quatro horas e reconstrua sua rotina em silêncio. "
            "Comenta ZERO que eu te mando o plano completo no seu WhatsApp."
        ),
        "caption": (
            "Nenhuma mensagem de 30 linhas já trouxe respeito de volta.\n\n"
            "Homem também sente abstinência pesada no término, mas se humilhar no chat só destrói a própria imagem. "
            "Segure a onda com técnica e protocolo prático de 14 dias.\n\n"
            "Comenta ZERO ou chama no WhatsApp da bio: (12) 99659-3222.\n\n"
            "#homem #contatozero #amorproprio #termino #codigozero"
        ),
    },
    {
        "topic": "Por que o homem demora 14 dias pra sentir o baque (Masculino #03)",
        "audience": "masculino",
        "music_bed": "arpege",
        "theme_start": "paper",
        "hook_mode": "split",
        "broll_ids": ["35889", "28893", "52079"],
        "case_tag": "HOMENS • BIOLOGIA",
        "emotion_direction": "Calmo, esclarecedor, documentário científico para homens.",
        "hook_headline": "NO DIA 14 O BAQUE BATE.",
        "hook_highlight": "DIA 14",
        "hook_card": {"sender": "SEMANA 01", "msg": "\"Achei que eu tava bem... por que doeu agora?\"", "stamp": "REBOTE TARDIO"},
        "beat1_kicker": "FISIOLOGIA DO TÉRMINO",
        "beat1_big": "ALÍVIO NO INÍCIO É ILUSÃO.",
        "beat1_sub": "O cérebro masculino anestesia o impacto na primeira semana.",
        "board_type": "neuro_curve",
        "board_title": "Curva masculina pós-término",
        "board_a_label": "DIAS 1 A 7 • ANESTESIA",
        "board_a_text": "Adrenalina e distração mascaram a perda real",
        "board_b_label": "DIA 14 • PICO TARDIO",
        "board_b_text": "Rotina silencia e a abstinência cobra o preço",
        "board_source": "DINÂMICA DOPAMINÉRGICA • CENTRAL SOS",
        "beat3_kicker": "ALERTA DE RECAÍDA",
        "beat3_big": "É AÍ QUE O CARA TROPEÇA.",
        "beat3_sub": "Na segunda semana ele procura ex achando que foi destino.",
        "rehook_text": "Você não piorou. Seu cérebro só acordou.",
        "rehook_sub": "Quem entende o relógio não cai na armadilha da madrugada.",
        "steps": [
            {"title": "Antecipe o dia 10 a 14", "desc": "Saiba que o vazio tardio é químico, não intuição."},
            {"title": "Use a Central SOS", "desc": "Dispare a trava de 15 min antes de reagir."},
            {"title": "Feche o protocolo", "desc": "Mantenha contato zero mesmo quando a ficha cair."},
        ],
        "cue_words": ["anestesia", "semana", "tropeça", "acordou", "antecipe", "ZERO"],
        "narration": (
            "Você achou que tinha superado sua ex na primeira semana e no dia catorze desabou do nada? "
            "Isso é biologia pura. Nos primeiros dias o cérebro cria uma anestesia de adrenalina e orgulho. "
            "Quando a poeira baixa na segunda semana, a abstinência bate atrasada e o silêncio pesa de verdade. "
            "É exatamente aí que a maioria dos caras tropeça e manda mensagem às onze da noite. "
            "Você não piorou. Seu cérebro só acordou. "
            "Antecipe essa janela, dispare a trava antes de agir e feche o protocolo completo. "
            "Comenta ZERO aqui pra receber a Central SOS e os dezesseis scripts."
        ),
        "caption": (
            "Muitos homens acham que estão bem nos primeiros dias e levam o golpe na semana dois.\n\n"
            "Entender esse rebote tardio impede que você jogue fora duas semanas de postura em uma recaída às 23h.\n\n"
            "Comenta ZERO ou chama no WhatsApp da bio: (12) 99659-3222.\n\n"
            "#terminodenamoro #psicologiamasculina #contatozero #mente #codigozero"
        ),
    },
    {
        "topic": "Ela postou foto provocando ou indireta nos stories (Masculino #04)",
        "audience": "masculino",
        "music_bed": "compte-a-rebours",
        "theme_start": "noir",
        "hook_mode": "split",
        "broll_ids": ["41638", "4915", "49878"],
        "case_tag": "HOMENS • RADAR SOCIAL",
        "emotion_direction": "Firme, estratégico e irônico na medida certa contra jogos de ego.",
        "hook_headline": "ESSA FOTO FOI PRA VOCÊ VER.",
        "hook_highlight": "PRA VOCÊ",
        "hook_card": {"sender": "Stories • 22:18", "msg": "Postou saída noturna ou legenda enigmática...", "stamp": "ISCA DE REAÇÃO"},
        "beat1_kicker": "JOGO DE VALIDAÇÃO",
        "beat1_big": "ELA QUER SUA REAÇÃO.",
        "beat1_sub": "Curtida, resposta ou ciúme provam que você ainda tá preso.",
        "board_type": "msg_deconstruct",
        "board_title": "Decodificando o story",
        "board_msg": "\"Indireta / foto produzida às 22h no primeiro fim de semana\"",
        "board_decode": "TRADUÇÃO: 'Preciso confirmar que ele ainda olha o meu nome primeiro.'",
        "board_source": "BLINDAGEM DIGITAL • SCRIPT #09",
        "beat3_kicker": "RESPOSTA MORTAL",
        "beat3_big": "SILÊNCIO GELA O TESTE.",
        "beat3_sub": "Quem não entra na isca inverte o poder na hora.",
        "rehook_text": "Olhar o story já é dar ponto pra ela.",
        "rehook_sub": "Se você silenciar hoje, sua paz volta antes do domingo.",
        "steps": [
            {"title": "Silencie stories e notas", "desc": "Não dê audiência para quem saiu da sua vida."},
            {"title": "Nunca reaja com emoji", "desc": "Reação rápida entrega ansiedade disfarçada."},
            {"title": "Construa presença real", "desc": "Sua ausência faz o barulho que você não fez."},
        ],
        "cue_words": ["reação", "traduzindo", "teste", "olhar", "silencie", "ZERO"],
        "narration": (
            "Sua ex postou indireta ou foto provocando no sábado à noite? Não morda essa isca. "
            "Ela não tá tentando voltar agora. Ela só quer confirmar que ainda controla sua reação com um clique. "
            "Traduzindo pro português claro: cada curtida sua vira combustível pro ego dela seguir longe. "
            "Quando você desaparece da lista de visualizações, o teste esfria na hora. "
            "Só olhar o story dela já é dar ponto de graça. "
            "Silencie tudo hoje, guarde sua energia e devolva sua ausência completa. "
            "Comenta ZERO aqui pra acessar a blindagem digital completa."
        ),
        "caption": (
            "Não confunda provocação de ego no story com vontade real de resolver o término.\n\n"
            "Quem controla onde coloca a atenção controla o próprio respeito depois da separação.\n\n"
            "Comenta ZERO ou chama no WhatsApp da bio: (12) 99659-3222.\n\n"
            "#jogodeego #contatozero #homens #redesociais #codigozero"
        ),
    },
    {
        "topic": "Ela disse podemos continuar amigos (Masculino #05)",
        "audience": "masculino",
        "music_bed": "thriller",
        "theme_start": "paper",
        "hook_mode": "split",
        "broll_ids": ["46448", "28901", "52079"],
        "case_tag": "HOMENS • SCRIPT #11",
        "emotion_direction": "Sério, objetivo e protetor da dignidade masculina.",
        "hook_headline": "NÃO ACEITA SER SÓ AMIGO.",
        "hook_highlight": "SÓ AMIGO.",
        "hook_card": {"sender": "Ex • Agora", "msg": "\"Você é especial... quero manter sua amizade.\"", "stamp": "ZONA DE CONFORTO DELA"},
        "beat1_kicker": "VERDADE DURA",
        "beat1_big": "AMIZADE AMORTECE A PERDA DELA.",
        "beat1_sub": "Você continua lá sem ela assumir nenhum compromisso.",
        "board_type": "strike_stat",
        "board_title": "O preço oculto do 'amigo'",
        "board_big": "2X",
        "board_wrong_lbl": "SE VOCÊ ACEITAR O PAPEL",
        "board_wrong": "Ela supera em paz usando seu apoio enquanto segue livre",
        "board_right_lbl": "LIMITE CÓDIGO ZERO",
        "board_right": "Recuse a migalha e retire sua presença por inteiro",
        "board_source": "SCRIPT #11 • LIMITE CLARO",
        "beat3_kicker": "CONSEQUÊNCIA",
        "beat3_big": "SEM VOCÊ POR PERTO ELA PENSA.",
        "beat3_sub": "É a única chance real de existir respeito ou superação.",
        "rehook_text": "Mas dá pra recusar sem ser grosso nem infantil.",
        "rehook_sub": "Uma única frase elegante muda como ela te enxerga.",
        "steps": [
            {"title": "Não discuta o término", "desc": "Zero ataque emocional ou tentativa de cobrança."},
            {"title": "Mande a trava limpa", "desc": "'Não faz sentido amizade agora. Se cuida.'"},
            {"title": "Desapareça de verdade", "desc": "Deixe ela sentir 100% da sua ausência."},
        ],
        "cue_words": ["amortece", "preço", "chances", "grosso", "discuta", "ZERO"],
        "narration": (
            "Se ela terminou com você e pediu pra continuar sendo amigo... recuse na hora. "
            "Amizade pós-término só amortece a culpa dela enquanto você assiste de camarote ela seguir a vida. "
            "Você paga o preço emocional em dobro: continua disponível, sem exclusividade e sem paz. "
            "Só existe respeito quando você recusa o lugar de reserva. "
            "Mas dá pra recusar sem ser grosso nem infantil. "
            "Não discuta, diga que não vê sentido em amizade agora e desapareça com dignidade. "
            "Comenta ZERO pra pegar os dezesseis scripts prontos do Código Zero."
        ),
        "caption": (
            "Aceitar amizade quando você ainda sente algo é assinar o próprio desgaste.\n\n"
            "No Script #11 do Código Zero você tem a resposta exata, curta e madura pra fechar essa porta sem cena.\n\n"
            "Comenta ZERO ou chama no WhatsApp da bio: (12) 99659-3222.\n\n"
            "#amizadecomex #posturamasculina #contatozero #superacao #codigozero"
        ),
    },
    {
        "topic": "Ela mandou 'oi, como você tá?' depois do gelo (Masculino #06)",
        "audience": "masculino",
        "music_bed": "enquete",
        "theme_start": "noir",
        "hook_mode": "cinema",
        "broll_ids": ["4808", "4915", "40746"],
        "case_tag": "HOMENS • SCRIPT #02",
        "emotion_direction": "Voz grave e segura, cortando ansiedade no segundo em que a notificação chega.",
        "hook_headline": "ELA SUMIU E VOLTOU DO NADA?",
        "hook_highlight": "DO NADA?",
        "hook_card": {"sender": "Ex • 00:52", "msg": "\"Oi sumido... sonhei com você hoje.\"", "stamp": "RADAR DE ATENÇÃO"},
        "beat1_kicker": "CUIDADO AGORA",
        "beat1_big": "ESFORÇO MÍNIMO NÃO É VOLTA.",
        "beat1_sub": "Uma frase vaga não apaga semanas de indiferença.",
        "board_type": "msg_deconstruct",
        "board_title": "O que o 'oi' testa",
        "board_msg": "\"Oi... como você anda? Tudo bem por aí?\"",
        "board_decode": "TRADUÇÃO: 'Só checando se a porta ainda abre com zero esforço meu.'",
        "board_source": "ESCUDO #02 • FILTRO DE ESFORÇO",
        "beat3_kicker": "REGRA DE OURO",
        "beat3_big": "RESPONDA AO ESFORÇO, NÃO À SAUDADE.",
        "beat3_sub": "Se não houve atitude real, mantenha a guarda alta.",
        "rehook_text": "Mas responder rápido destrói tudo que você construiu.",
        "rehook_sub": "Calma de ferro nos primeiros 15 minutos salva semanas.",
        "steps": [
            {"title": "Espere a adrenalina cair", "desc": "Deixe o celular virado por no mínimo 2 horas."},
            {"title": "Curto, educado e seco", "desc": "Se responder, zero pergunta aberta nem emoji."},
            {"title": "Devolva o silêncio", "desc": "Não puxe assunto; quem quebrou que sustente."},
        ],
        "cue_words": ["apaga", "checando", "esforço", "rápido", "adrenalina", "ZERO"],
        "narration": (
            "Ela sumiu por semanas e mandou 'oi, como você tá?' na madrugada? Trave agora. "
            "Uma mensagem vaga não apaga o desrespeito nem prova que ela quer reconstruir nada. "
            "Na maioria das vezes ela só tá checando se você continua disponível com zero esforço. "
            "Regra simples de postura: responda ao tamanho do esforço dela, nunca ao tamanho da sua saudade. "
            "Mas responder rápido demais destrói tudo que você construiu no silêncio. "
            "Deixe a adrenalina cair, responda curto ou fique em silêncio e nunca puxe conversa. "
            "Comenta ZERO que eu libero os dezesseis scripts escudo no seu WhatsApp."
        ),
        "caption": (
            "Isca de esforço mínimo serve pra medir o quanto você ainda é acessível.\n\n"
            "Mantenha a calma nos primeiros minutos e use o filtro do Escudo #02 antes de digitar uma letra.\n\n"
            "Comenta ZERO ou chama no WhatsApp da bio: (12) 99659-3222.\n\n"
            "#exmandoumensagem #homem #contatozero #dignidade #codigozero"
        ),
    },
    {
        "topic": "O erro silencioso depois das 23h que destrói seu foco (Masculino #07)",
        "audience": "masculino",
        "music_bed": "compte-a-rebours",
        "theme_start": "noir",
        "hook_mode": "split",
        "broll_ids": ["4701", "28897", "49878"],
        "case_tag": "HOMENS • MADRUGADA",
        "emotion_direction": "Firme, intenso e direto, estilo filme noturno de disciplina.",
        "hook_headline": "DEPOIS DAS 23H SEU EIXO CAI.",
        "hook_highlight": "23H",
        "hook_card": {"sender": "RELÓGIO • 23:47", "msg": "Cansaço + silêncio = dedo procurando o perfil dela", "stamp": "HORA CRÍTICA"},
        "beat1_kicker": "QUEDA BIOLÓGICA",
        "beat1_big": "SUA DEFESA DESLIGA À NOITE.",
        "beat1_sub": "Córtex cansado perde o freio e chama carência de urgência.",
        "board_type": "neuro_curve",
        "board_title": "Janela de maior recaída",
        "board_a_label": "08H ÀS 18H • FOCO",
        "board_a_text": "Rotina ocupa a mente e mantém o controle lógico",
        "board_b_label": "23H ÀS 02H • QUEDA",
        "board_b_text": "Solidão noturna dispara impulsividade no celular",
        "board_source": "PROTOCOLO NOTURNO • CENTRAL SOS",
        "beat3_kicker": "PROTEÇÃO PRÁTICA",
        "beat3_big": "NÃO CONFIE NA FORÇA BRUTA.",
        "beat3_sub": "Ambiente vence vontade quando o dia acaba.",
        "rehook_text": "Se o celular dormir do seu lado, você vai olhar.",
        "rehook_sub": "Trava mecânica bate força de vontade todo santo dia.",
        "steps": [
            {"title": "Celular fora do quarto", "desc": "Carregue na sala ou longe da cama às 22h30."},
            {"title": "Bloqueie gatilhos fáceis", "desc": "Apague conversas antigas e silencie alertas."},
            {"title": "Acione a Central SOS", "desc": "Use os 15 minutos guiados se o aperto bater."},
        ],
        "cue_words": ["córtex", "janela", "confie", "dormir", "quarto", "ZERO"],
        "narration": (
            "Você passa o dia firme no trabalho e depois das onze da noite quase recai? Entenda o porquê. "
            "À noite o seu córtex cansado desliga o freio lógico e transforma carência em urgência falsa. "
            "Entre vinte e três e duas da manhã acontecem quase todas as mensagens que os homens se arrependem depois. "
            "Não confie só em força bruta quando você já tá esgotado. "
            "Se o celular dormir do lado da cama, você vai abrir o perfil dela. "
            "Carregue o aparelho fora do quarto, corte gatilhos e dispare os quinze minutos da Central SOS. "
            "Comenta ZERO aqui pra ativar o protocolo noturno de catorze dias."
        ),
        "caption": (
            "Não é falta de caráter perder a cabeça de madrugada: é fadiga mental + gatilho fácil.\n\n"
            "Mude o ambiente às 22h30 e tenha uma trava objetiva pronta antes que o impulso apareça.\n\n"
            "Comenta ZERO ou chama no WhatsApp da bio: (12) 99659-3222.\n\n"
            "#disciplina #homens #madrugada #superartermino #codigozero"
        ),
    },
    {
        "topic": "Como um homem recupera o controle em 14 dias (Masculino #08)",
        "audience": "masculino",
        "music_bed": "arpege",
        "theme_start": "paper",
        "hook_mode": "split",
        "broll_ids": ["52079", "40746", "35426"],
        "case_tag": "HOMENS • PROTOCOLO 14D",
        "emotion_direction": "Motivador sem gritaria, sólido, ritmo crescente de documentário.",
        "hook_headline": "14 DIAS PRA VIRAR A CHAVE.",
        "hook_highlight": "14 DIAS",
        "hook_card": {"sender": "META DE FOCO", "msg": "Sem stalkear, sem implorar, sem viver em função dela", "stamp": "RECONSTRUÇÃO REAL"},
        "beat1_kicker": "VERDADE SIMPLES",
        "beat1_big": "SUPERAR NÃO É ESQUECER FORÇADO.",
        "beat1_sub": "É limpar dopamina falsa e reconstruir seu padrão diário.",
        "board_type": "strike_stat",
        "board_title": "O plano que tira você do buraco",
        "board_big": "14D",
        "board_wrong_lbl": "ESPERAR O TEMPO CURAR SOZINHO",
        "board_wrong": "Meses rodando em círculo olhando foto antiga todo dia",
        "board_right_lbl": "CÓDIGO ZERO ESTRUTURADO",
        "board_right": "Corte de gatilhos + trava 90-15 + treino e clareza",
        "board_source": "MÉTODO COMPLETO • WHATSAPP NA BIO",
        "beat3_kicker": "RESULTADO PRÁTICO",
        "beat3_big": "A VOZ NA SUA CABEÇA BAIXA.",
        "beat3_sub": "Em duas semanas você volta a dormir e pensar limpo.",
        "rehook_text": "O segredo tá nos primeiros quatro dias.",
        "rehook_sub": "Sobreviveu ao corte químico inicial, o jogo começa a virar.",
        "steps": [
            {"title": "Dias 1–4: Desintoxicação", "desc": "Silêncio absoluto em chat, stories e memórias."},
            {"title": "Dias 5–9: Corpo em ação", "desc": "Treino pesado e meta diária fora de casa."},
            {"title": "Dias 10–14: Blindagem", "desc": "Respostas prontas caso ela reapareça testando."},
        ],
        "cue_words": ["limpar", "plano", "semanas", "quatro", "desintoxicação", "ZERO"],
        "narration": (
            "Você não precisa de seis meses sofrendo escondido. Precisa de catorze dias com método firme. "
            "Superar não é fingir que não doeu, é limpar o vício químico que prende sua mente nela. "
            "Sem plano, o homem fica rodando em círculo por meses checando o último visto. "
            "Com corte limpo, em duas semanas o barulho mental baixa e você volta a respirar inteiro. "
            "O segredo tá em atravessar os primeiros quatro dias sem recair. "
            "Desintoxicação no início, corpo em movimento no meio e blindagem pronta pro dia que ela testar voltar. "
            "Comenta ZERO aqui que eu te mando o Código Zero completo agora."
        ),
        "caption": (
            "Sem estrutura você sofre meses no automático; com método você vira a chave em duas semanas.\n\n"
            "O Código Zero funciona para homens que querem parar de sangrar em silêncio e retomar o respeito próprio.\n\n"
            "Comenta ZERO ou chama no WhatsApp da bio: (12) 99659-3222.\n\n"
            "#protocolo14dias #homens #superacao #contatozero #codigozero"
        ),
    },
    # ── FEMININO (09..15) ─────────────────────────────────────────────────────
    {
        "topic": "Ele mandou 'oi, tudo bem?' do nada às 1h da manhã (Feminino #09)",
        "audience": "feminino",
        "music_bed": "thriller",
        "theme_start": "noir",
        "hook_mode": "split",
        "broll_ids": ["8739", "4915", "46702"],
        "case_tag": "MULHERES • SCRIPT #01",
        "emotion_direction": "Firme, protetora e lúcida, cortando o impulso no segundo zero.",
        "hook_headline": "ELE MANDOU 'OI SUMIDA'?",
        "hook_highlight": "OI SUMIDA",
        "hook_card": {"sender": "Ex • 01:42", "msg": "\"Oi... tudo bem por aí? Lembrei de você.\"", "stamp": "NÃO É SAUDADE REAL"},
        "beat1_kicker": "ACORDE AGORA",
        "beat1_big": "ISCA DE ESFORÇO ZERO.",
        "beat1_sub": "Ele não voltou arrependido. Só checou se você ainda abre.",
        "board_type": "strike_stat",
        "board_title": "O efeito da sua resposta",
        "board_big": "01:42",
        "board_wrong_lbl": "SE RESPONDER COM EMOÇÃO",
        "board_wrong": "Você enche o ego dele e volta pro banco de reservas",
        "board_right_lbl": "ESCUDO #01 • SILÊNCIO",
        "board_right": "Você quebra o teste e devolve seu valor na hora",
        "board_source": "16 SCRIPTS ESCUDO • CÓDIGO ZERO",
        "beat3_kicker": "REGRA DE OURO",
        "beat3_big": "VALOR NÃO SE MENDIGA.",
        "beat3_sub": "Quem quer voltar assume erros, não manda oi vazio.",
        "rehook_text": "Mas quase todo mundo cai num detalhe bobo.",
        "rehook_sub": "Abriu sem querer? Não compensa com mensagem educada.",
        "steps": [
            {"title": "Trave o dedo por 15 min", "desc": "Afaste o celular do rosto antes de responder."},
            {"title": "Zero compensação", "desc": "Visualizou por acidente? Apenas feche e silencie."},
            {"title": "Exija atitude concreta", "desc": "Esforço zero só merece resposta zero."},
        ],
        "cue_words": ["esforço", "efeito", "erros", "detalhe", "trave", "ZERO"],
        "narration": (
            "Seu ex mandou 'oi, tudo bem?' depois de semanas sumido? Trava o dedo agora. "
            "Isso não é arrependimento. É isca de esforço zero pra testar se você ainda tá esperando no banco de reservas. "
            "Se você responder na hora emocionada, o efeito é imediato: o ego dele infla e amanhã ele esfria de novo. "
            "Quem quer voltar de verdade assume os próprios erros, não joga oi vazio às duas da manhã. "
            "Mas quase todo mundo cai num detalhe bobo: abre sem querer e responde por educação. "
            "Trave o dedo quinze minutos, não compense visualização e responda só a esforço real. "
            "Comenta ZERO aqui que eu te envio os dezesseis scripts do Código Zero."
        ),
        "caption": (
            "Não confunda checagem de ego na madrugada com vontade real de mudar.\n\n"
            "No Escudo #01 do Código Zero você sabe exatamente como agir quando ele tenta reaparecer com esforço mínimo.\n\n"
            "Comenta ZERO ou chama no WhatsApp da bio: (12) 99659-3222.\n\n"
            "#contatozero #mulheres #superartermino #exmandoumensagem #codigozero"
        ),
    },
    {
        "topic": "Ele pediu pra continuar amigos pra te deixar na reserva (Feminino #10)",
        "audience": "feminino",
        "music_bed": "enquete",
        "theme_start": "paper",
        "hook_mode": "split",
        "broll_ids": ["25586", "28897", "46702"],
        "case_tag": "MULHERES • SCRIPT #11",
        "emotion_direction": "Clara, acolhedora e incisiva, devolvendo lucidez sem dureza gratuita.",
        "hook_headline": "ELE PEDIU AMIZADE?",
        "hook_highlight": "AMIZADE?",
        "hook_card": {"sender": "Ex • 21:15", "msg": "\"Você é incrível... vamos continuar amigos.\"", "stamp": "DESPEDIDA PARCELADA"},
        "beat1_kicker": "VERDADE REAL",
        "beat1_big": "ELE QUER CARINHO SEM ÔNUS.",
        "beat1_sub": "Quer seu apoio enquanto se desconecta sem culpa.",
        "board_type": "msg_deconstruct",
        "board_title": "O subtexto do pedido",
        "board_msg": "\"Não quero perder sua amizade na minha vida.\"",
        "board_decode": "TRADUÇÃO: 'Quero manter o acesso sem obrigação nenhuma de ficar.'",
        "board_source": "SCRIPT #11 • LIMITE DE OURO",
        "beat3_kicker": "VIRADA",
        "beat3_big": "MIGALHA PRENDE VOCÊ NO PASSADO.",
        "beat3_sub": "Enquanto ele segue em frente apoiado no seu afeto.",
        "rehook_text": "E recusar não precisa virar briga.",
        "rehook_sub": "Uma única mensagem seca fecha a porta com classe.",
        "steps": [
            {"title": "Recuse a amizade já", "desc": "Não aceite migalha para mantê-lo por perto."},
            {"title": "Mande a trava limpa", "desc": "'Preciso de distância pra seguir bem. Fica bem.'"},
            {"title": "Tire seu acesso", "desc": "Só quem sente falta real valoriza presença."},
        ],
        "cue_words": ["apoio", "tradução", "passado", "briga", "recuse", "ZERO"],
        "narration": (
            "Ele terminou e pediu pra vocês continuarem amigos? Escuta isso antes de aceitar. "
            "Ele quer manter seu apoio emocional sem precisar assumir você. É o jeito mais cômodo de ir embora sem culpa. "
            "Traduzindo: ele usa sua presença como anestesia pra superar você, enquanto você fica presa nas migalhas. "
            "Amizade falsa só segura você no passado. "
            "E recusar não precisa virar briga nem drama. "
            "Recuse com elegância em uma linha, corte acesso total e devolva o silêncio inteiro. "
            "Comenta ZERO que eu te mando o Script onze pronto no WhatsApp."
        ),
        "caption": (
            "Aceitar ser 'amiga' de quem acabou de partir seu coração é prolongar a dor em parcelas.\n\n"
            "Veja no Script #11 como cortar com elegância e proteger sua saúde emocional.\n\n"
            "Comenta ZERO ou chama no WhatsApp da bio: (12) 99659-3222.\n\n"
            "#amorproprio #dependenciaemocional #superartermino #mulheres #codigozero"
        ),
    },
    {
        "topic": "Esta mensagem foi apagada na madrugada (Feminino #11)",
        "audience": "feminino",
        "music_bed": "thriller",
        "theme_start": "noir",
        "hook_mode": "cinema",
        "broll_ids": ["43270", "4915", "2846"],
        "case_tag": "MULHERES • SCRIPT #04",
        "emotion_direction": "Direto, lúcido e atento ao pico de curiosidade ansiosa.",
        "hook_headline": "ELE APAGOU A MENSAGEM?",
        "hook_highlight": "APAGOU",
        "hook_card": {"sender": "Ex • 23:54", "msg": "🚫 Esta mensagem foi apagada", "stamp": "GATILHO DE ANSIEDADE"},
        "beat1_kicker": "ARMADILHA CLÁSSICA",
        "beat1_big": "NÃO PERGUNTE O QUE ERA.",
        "beat1_sub": "Perguntar 'que foi?' entrega exatamente o controle que ele queria.",
        "board_type": "strike_stat",
        "board_title": "O jogo da mensagem apagada",
        "board_big": "100%",
        "board_wrong_lbl": "SE VOCÊ PERGUNTAR 'O QUE ERA?'",
        "board_wrong": "Mostra ansiedade na hora e vira conversa de validação",
        "board_right_lbl": "CONTROLE SCRIPT #04",
        "board_right": "Ignore como se nem tivesse notado no celular",
        "board_source": "BLINDAGEM EMOCIONAL • SCRIPT #04",
        "beat3_kicker": "LÓGICA PURA",
        "beat3_big": "SE FOSSE IMPORTANTE, REENVIAVA.",
        "beat3_sub": "Adultos interessados sabem falar claro sem enigma.",
        "rehook_text": "Mas a curiosidade coça em menos de um minuto.",
        "rehook_sub": "Respire fundo: não morder o anzol devolve sua paz.",
        "steps": [
            {"title": "Deixe no silêncio", "desc": "Zero '?' ou 'tá tudo bem?' por impulso."},
            {"title": "Feche o aplicativo", "desc": "Saia do chat imediatamente sem ficar olhando."},
            {"title": "Espere postura adulta", "desc": "Quem realmente quer dizer algo, diz inteiro."},
        ],
        "cue_words": ["entregar", "jogo", "claro", "coça", "silêncio", "ZERO"],
        "narration": (
            "Viu 'esta mensagem foi apagada' no chat dele? Não pergunta o que era. "
            "Se você mandar um 'oi, o que você ia dizer?', acaba de entregar ansiedade na bandeja pro ego dele. "
            "Esse jogo funciona porque a curiosidade gera pico de dopamina e faz você correr atrás da resposta. "
            "Adultos com intenção real falam claro, não ficam mandando enigma pra te testar. "
            "Mas a curiosidade coça em segundos. "
            "Deixe no silêncio absoluto, feche a conversa e espere postura de verdade, nunca isca. "
            "Comenta ZERO aqui pra receber os dezesseis scripts escudo."
        ),
        "caption": (
            "Mensagem apagada às 23h raramente é acidente: quase sempre vira teste de atenção.\n\n"
            "Não pergunte, não justifique, siga sua noite inteira.\n\n"
            "Comenta ZERO ou chama no WhatsApp da bio: (12) 99659-3222.\n\n"
            "#contatozero #ansiedade #relacionamento #superartermino #codigozero"
        ),
    },
    {
        "topic": "Mais um áudio chorando não faz ele voltar (Feminino #12)",
        "audience": "feminino",
        "music_bed": "enquete",
        "theme_start": "noir",
        "hook_mode": "split",
        "broll_ids": ["8739", "28893", "46702"],
        "case_tag": "MULHERES • RECAÍDA",
        "emotion_direction": "Acolhedora no tom, mas implacavelmente honesta no diagnóstico.",
        "hook_headline": "MAIS UM ÁUDIO NÃO MUDA NADA.",
        "hook_highlight": "ÁUDIO",
        "hook_card": {"sender": "Você • 4:12 min", "msg": "Gravando áudio tentando explicar tudo de novo...", "stamp": "DESGASTE CERTO"},
        "beat1_kicker": "DURA VERDADE",
        "beat1_big": "QUEM NÃO QUER OUVIR NÃO SENTE.",
        "beat1_sub": "Áudio longo implorando transforma amor em peso.",
        "board_type": "strike_stat",
        "board_title": "O custo do apelo emocional",
        "board_big": "4m",
        "board_wrong_lbl": "MAIS DE 1 MINUTO DE DESABAFO",
        "board_wrong": "Ele ouve em 2x sentindo alívio por ter terminado",
        "board_right_lbl": "RETIRADA DE RESPEITO",
        "board_right": "Você guarda suas lágrimas pra quem te acolhe de verdade",
        "board_source": "PROTOCOLO DE RETOMADA • 14 DIAS",
        "beat3_kicker": "AUTORESPEITO",
        "beat3_big": "ELE JÁ ENTENDEU SUA DOR.",
        "beat3_sub": "O problema nunca foi falta de explicação.",
        "rehook_text": "Você não precisa gritar pra ser vista.",
        "rehook_sub": "Sua ausência educa muito mais que qualquer desabafo.",
        "steps": [
            {"title": "Desmarque o microfone", "desc": "Solte o botão e escreva só no seu caderno."},
            {"title": "Chame uma amiga real", "desc": "Desabafe fora da conversa do ex."},
            {"title": "Inicie os 14 dias", "desc": "Use a Central SOS nas horas de aperto forte."},
        ],
        "cue_words": ["peso", "custo", "explicação", "vista", "microfone", "ZERO"],
        "narration": (
            "Segura esse botão do microfone antes de gravar mais um áudio de quatro minutos pra ele. "
            "Quem escolheu partir não precisa de mais uma explicação do quanto você tá doendo. "
            "O custo desse desabafo é cruel: ele ouve em velocidade dois e sente alívio por ter saído fora. "
            "Entenda de uma vez: o problema nunca foi você não ter se explicado direito. "
            "Você não precisa gritar pra ser valorizada. "
            "Solta o microfone, chora no ombro de quem merece e entra hoje no protocolo de catorze dias. "
            "Comenta ZERO aqui pra eu enviar o acesso completo."
        ),
        "caption": (
            "Áudio longo tentando convencer quem já foi embora só machuca a sua própria autoestima.\n\n"
            "Desabafe no lugar certo e preserve a sua dignidade intacta.\n\n"
            "Comenta ZERO ou chama no WhatsApp da bio: (12) 99659-3222.\n\n"
            "#superartermino #autoestima #mulheres #contatozero #codigozero"
        ),
    },
    {
        "topic": "Ele sumiu sem explicação? O silêncio é a resposta (Feminino #13)",
        "audience": "feminino",
        "music_bed": "arpege",
        "theme_start": "paper",
        "hook_mode": "split",
        "broll_ids": ["46702", "2846", "40746"],
        "case_tag": "MULHERES • CLAREZA",
        "emotion_direction": "Calma e resoluta, quebrando a espera angustiante pela resposta.",
        "hook_headline": "ELE SUMIU DO NADA?",
        "hook_highlight": "SUMIU",
        "hook_card": {"sender": "Visto por último • Ontem", "msg": "3 dias esperando uma resposta que não vem", "stamp": "RESPOSTA DADA"},
        "beat1_kicker": "SEM ILUSÃO",
        "beat1_big": "O SILÊNCIO DELE É A RESPOSTA.",
        "beat1_sub": "Ninguém fica ocupado 48 horas pra responder quem importa.",
        "board_type": "msg_deconstruct",
        "board_title": "O mito da 'falta de tempo'",
        "board_msg": "\"Será que aconteceu alguma coisa séria no trabalho dele?\"",
        "board_decode": "REALIDADE: Desinteresse silencioso evita o desconforto da conversa.",
        "board_source": "CLAREZA RADICAL • CÓDIGO ZERO",
        "beat3_kicker": "CORTE NECESSÁRIO",
        "beat3_big": "PARE DE MANDAR COBRANÇA.",
        "beat3_sub": "Cobrar atenção de quem some humilha sua paz.",
        "rehook_text": "Você merece escolha inteira, não resto de hora.",
        "rehook_sub": "Aceitar a mensagem oculta poupa meses de espera.",
        "steps": [
            {"title": "Leia o vácuo como 'não'", "desc": "Encerre a expectativa hoje sem insistir."},
            {"title": "Apague o chat fixado", "desc": "Tire o nome dele do topo da sua tela."},
            {"title": "Recupere seu centro", "desc": "Volte a investir em quem olha pra você."},
        ],
        "cue_words": ["ocupado", "mito", "atenção", "inteira", "vácuo", "ZERO"],
        "narration": (
            "Ele sumiu sem dar explicação e você tá há dias olhando o celular? Ouve isso. "
            "Ninguém passa quarenta e oito horas ocupado demais pra mandar duas palavras pra quem realmente importa. "
            "Enquanto você inventa desculpas pro trabalho dele, o vácuo já disse tudo que faltava coragem de falar. "
            "Ficar cobrando resposta só te diminui diante de quem já escolheu se afastar. "
            "Você merece presença inteira, nunca resto de atenção. "
            "Leia o vácuo como um não definitivo, tire o chat do topo e reconstrua seu centro. "
            "Comenta ZERO pra baixar os passos do Código Zero hoje."
        ),
        "caption": (
            "Quando alguém quer falar com você, encontra 15 segundos no meio do dia mais corrido.\n\n"
            "Pare de criar justificativa pro desaparecimento de quem já te deu a resposta.\n\n"
            "Comenta ZERO ou chama no WhatsApp da bio: (12) 99659-3222.\n\n"
            "#ghosting #relacionamento #valor #mulheres #codigozero"
        ),
    },
    {
        "topic": "Pare de tentar provar seu valor pra quem já saiu (Feminino #14)",
        "audience": "feminino",
        "music_bed": "enquete",
        "theme_start": "paper",
        "hook_mode": "cinema",
        "broll_ids": ["25586", "49878", "43270"],
        "case_tag": "MULHERES • EIXO",
        "emotion_direction": "Forte, elegante, resgatando a postura feminina sem vitimismo.",
        "hook_headline": "PARE DE TENTAR PROVAR.",
        "hook_highlight": "PROVAR.",
        "hook_card": {"sender": "ALERTA INTERNO", "msg": "Postando pra ele ver o que perdeu?", "stamp": "ARMADILHA INVERSA"},
        "beat1_kicker": "VERDADE SILENCIOSA",
        "beat1_big": "ATUAÇÃO PRO EX É PRISÃO.",
        "beat1_sub": "Se cada foto sua pensa nele, ele ainda manda na sua rotina.",
        "board_type": "strike_stat",
        "board_title": "Supere de verdade vs Teatro",
        "board_big": "14D",
        "board_wrong_lbl": "VIVER PRO STORY DE INVEJA",
        "board_wrong": "Sorrir na foto e chorar quando fecha o Instagram",
        "board_right_lbl": "SILÊNCIO AUTÊNTICO",
        "board_right": "Mudar pra si mesma longe da vitrine e recuperar paz",
        "board_source": "LIBERDADE REAL • PROTOCOLO 14 DIAS",
        "beat3_kicker": "RESULTADO",
        "beat3_big": "QUEM TÁ LIVRE NÃO PRECISA PLATEIA.",
        "beat3_sub": "A paz verdadeira não depende da visualização dele.",
        "rehook_text": "O corte real acontece quando ninguém tá olhando.",
        "rehook_sub": "Tire o ex de diretor da sua vida agora mesmo.",
        "steps": [
            {"title": "Pare de checar visualizações", "desc": "Bloqueie ou silencie sem teatro de vingança."},
            {"title": "Cuide da rotina invisível", "desc": "Sono, corpo e amigas fora das redes."},
            {"title": "Siga o método diário", "desc": "14 dias até a dependência perder força."},
        ],
        "cue_words": ["rotina", "teatro", "plateia", "olhando", "checar", "ZERO"],
        "narration": (
            "Você tá se arrumando só pra postar foto e esperar ele ver o que perdeu? Para agora. "
            "Se cada passo seu ainda tem o objetivo de provocar reação nele, ele continua comandando sua rotina. "
            "Viver num teatro de superação cansa o dobro: você sorri na tela e desaba sozinha em casa. "
            "Quem realmente superou não precisa provar nada na vitrine pra plateia errada. "
            "O corte verdadeiro acontece longe do celular, quando ninguém tá olhando. "
            "Pare de checar quem viu seus stories e cuide da sua vida real por catorze dias. "
            "Comenta ZERO que eu te mando o protocolo completo no WhatsApp."
        ),
        "caption": (
            "Superar de verdade é tirar o ex do papel de espectador da sua vida.\n\n"
            "Sem teatro de vingança, só paz real construída em 14 dias.\n\n"
            "Comenta ZERO ou chama no WhatsApp da bio: (12) 99659-3222.\n\n"
            "#superacao #autoestima #contatozero #mulheres #codigozero"
        ),
    },
    {
        "topic": "Quando ele volta testando se você ainda tá no bolso (Feminino #15)",
        "audience": "feminino",
        "music_bed": "compte-a-rebours",
        "theme_start": "noir",
        "hook_mode": "split",
        "broll_ids": ["43270", "28897", "8739"],
        "case_tag": "MULHERES • SCRIPT #14",
        "emotion_direction": "Precisa e afiada, blindando contra falsas reaproximações.",
        "hook_headline": "ELE VOLTOU DOCE DO NADA?",
        "hook_highlight": "DOCE",
        "hook_card": {"sender": "Ex • 19:20", "msg": "\"Saudade da nossa conversa... vamo sair?\"", "stamp": "TESTE DE DISPONIBILIDADE"},
        "beat1_kicker": "NÃO CAIA RÁPIDO",
        "beat1_big": "SAUDADE NÃO É MUDANÇA.",
        "beat1_sub": "Sentir falta do conforto não muda quem não assumiu erro.",
        "board_type": "msg_deconstruct",
        "board_title": "O filtro dos 3 sinais",
        "board_msg": "\"Lembrei daquele nosso lugar hoje... tô com saudade\"",
        "board_decode": "PERGUNTE: Ele pediu perdão concreto ou só tá com carência?",
        "board_source": "SCRIPT #14 • FILTRO DE VOLTA",
        "beat3_kicker": "SEU PODER",
        "beat3_big": "ACESSO FÁCIL REPETE O CICLO.",
        "beat3_sub": "Abrir a porta no primeiro elogio reinicia a dor.",
        "rehook_text": "Mas dá pra testar a intenção dele em uma frase.",
        "rehook_sub": "Quem não aguenta esperar 48 horas nunca quis ficar.",
        "steps": [
            {"title": "Não marque na hora", "desc": "Recuse convite de última hora à noite."},
            {"title": "Exija clareza adulta", "desc": "Não misture nostalgia com falta de respeito."},
            {"title": "Proteja seu avanço", "desc": "Nunca jogue 14 dias fora por carência."},
        ],
        "cue_words": ["conforto", "sinais", "ciclo", "frase", "marque", "ZERO"],
        "narration": (
            "Ele voltou mandando saudade e elogio depois de te machucar? Calma antes de ceder. "
            "Saudade do conforto que você dava não significa que ele mudou ou assumiu o que quebrou. "
            "A pergunta seca é uma só: ele trouxe mudança concreta ou só nostalgia barata às oito da noite? "
            "Dar acesso fácil no primeiro elogio só garante a repetição exata da mesma dor. "
            "Mas dá pra testar a intenção real dele sem brigar. "
            "Recuse encontros de última hora, exija clareza adulta e proteja seu avanço de catorze dias. "
            "Comenta ZERO aqui pra receber os scripts de resposta pronta."
        ),
        "caption": (
            "Elogio vazio e nostalgia não pagam respeito nem garantem mudança real.\n\n"
            "Use o filtro do Script #14 antes de abrir a porta de novo.\n\n"
            "Comenta ZERO ou chama no WhatsApp da bio: (12) 99659-3222.\n\n"
            "#relacionamento #reconciliacao #contatozero #mulheres #codigozero"
        ),
    },
    # ── AMBOS / NEUROCIÊNCIA & REGRAS UNIVERSAIS (16..20) ────────────────────
    {
        "topic": "Rejeição dói no corpo como queimadura física (Kross 2011) (Ambos #16)",
        "audience": "ambos",
        "music_bed": "arpege",
        "theme_start": "noir",
        "hook_mode": "split",
        "broll_ids": ["28897", "4701", "49878"],
        "case_tag": "NEUROCIÊNCIA • MICHIGAN",
        "emotion_direction": "Documental, empático e seguro, válido tanto para homens quanto mulheres.",
        "hook_headline": "SAUDADE DÓI COMO QUEIMADURA.",
        "hook_highlight": "QUEIMADURA.",
        "hook_card": {"sender": "KROSS ET AL. (2011)", "msg": "Ressonância magnética cerebral pós-rejeição amorosa", "stamp": "EVIDÊNCIA CLÍNICA"},
        "beat1_kicker": "NÃO É DRAMA",
        "beat1_big": "SEU CÉREBRO ACENDE DOR REAL.",
        "beat1_sub": "A mesma área da queimadura física ativa no término.",
        "board_type": "neuro_curve",
        "board_title": "Abstinência afetiva em 14 dias",
        "board_a_label": "DIAS 1–4 • CORTE QUÍMICO",
        "board_a_text": "Falta de dopamina dispara alarme físico no peito",
        "board_b_label": "DIA 14 • REORGANIZAÇÃO",
        "board_b_text": "Rotina estruturada reduz o ciclo de fissura",
        "board_source": "ESTUDO KROSS ET AL., UNIV. DE MICHIGAN (2011)",
        "beat3_kicker": "LIBERAÇÃO DE CULPA",
        "beat3_big": "ISSO NÃO É FRAQUEZA SUA.",
        "beat3_sub": "Homem e mulher sofrem o mesmo choque neurológico.",
        "rehook_text": "Por isso 'só esquece' nunca funcionou.",
        "rehook_sub": "Você não trata dor química com frase motivacional.",
        "steps": [
            {"title": "Pare de se culpar hoje", "desc": "Seu corpo atravessa um desmame neuroquímico real."},
            {"title": "Corte estímulos visuais", "desc": "Cada foto vista reinicia o pico da crise."},
            {"title": "Siga o protocolo 14 dias", "desc": "Método passo a passo no lugar da força bruta."},
        ],
        "cue_words": ["mesma", "dias", "fraqueza", "esquece", "culpar", "ZERO"],
        "narration": (
            "Você sente um aperto físico real no peito e acha que perdeu a razão? Escuta isso. "
            "Um estudo da Universidade de Michigan mostrou em ressonância que a rejeição acende a mesma rede cerebral de uma queimadura física. "
            "Nos primeiros dias após o corte, o cérebro entra em fissura química real procurando dopamina. "
            "Isso não é fraqueza sua. Acontece igual em homens e mulheres depois de um vínculo quebrado. "
            "Por isso conselho raso de 'só segue em frente' nunca funcionou. "
            "Pare de se culpar, corte os gatilhos visuais e siga catorze dias de método prático. "
            "Comenta ZERO aqui pra receber o protocolo completo no WhatsApp."
        ),
        "caption": (
            "Dor de término não é frescura: a neurociência mostra que o cérebro processa rejeição na mesma rede da dor física.\n\n"
            "Homens e mulheres passam pela mesma abstinência. Trate com método real de 14 dias.\n\n"
            "Comenta ZERO ou chama no WhatsApp da bio: (12) 99659-3222.\n\n"
            "#neurociencia #superartermino #saudemental #contatozero #codigozero"
        ),
    },
    {
        "topic": "A Regra 90-15 antes de mandar mensagem no impulso (Ambos #17)",
        "audience": "ambos",
        "music_bed": "compte-a-rebours",
        "theme_start": "paper",
        "hook_mode": "split",
        "broll_ids": ["28893", "4915", "2846"],
        "case_tag": "CENTRAL SOS • 90–15",
        "emotion_direction": "Firme e urgente como um salva-vidas emocional às 23h.",
        "hook_headline": "O PICO DURA SÓ 90 SEGUNDOS.",
        "hook_highlight": "90 SEGUNDOS.",
        "hook_card": {"sender": "CRONÔMETRO SOS", "msg": "Vontade aguda de mandar mensagem agora?", "stamp": "TRAVA ANTI-RECAÍDA"},
        "beat1_kicker": "FATO QUÍMICO",
        "beat1_big": "A ONDA PASSA EM UM MINUTO E MEIO.",
        "beat1_sub": "Só vira noite inteira se você ficar encarando o chat.",
        "board_type": "neuro_curve",
        "board_title": "O ciclo químico da recaída",
        "board_a_label": "0 A 90 SEGUNDOS",
        "board_a_text": "Adrenalina sobe no teto e simula urgência fatal",
        "board_b_label": "APÓS 15 MINUTOS",
        "board_b_text": "Onda esvazia e a sua razão volta pro volante",
        "board_source": "REGRA 90–15 • CENTRAL SOS",
        "beat3_kicker": "PERGUNTA DECISIVA",
        "beat3_big": "AMANHÃ ÀS 9H: ORGULHO OU VERGONHA?",
        "beat3_sub": "Nenhuma mensagem no pânico trouxe paz no café da manhã.",
        "rehook_text": "Mas ninguém consegue pensar com o aparelho na mão.",
        "rehook_sub": "A trava precisa ser física antes de ser mental.",
        "steps": [
            {"title": "Largue o celular longe", "desc": "Deixe o aparelho em outro cômodo imediatamente."},
            {"title": "Dispare 15 minutos", "desc": "Escreva tudo num papel sem mandar nenhuma letra."},
            {"title": "Decida só frio", "desc": "Ao fim do alarme, você já venceu a crise."},
        ],
        "cue_words": ["encarando", "ciclo", "manhã", "aparelho", "largue", "ZERO"],
        "narration": (
            "Tá com o dedo pronto pra mandar mensagem agora? Faz a Regra Noventa Quinze antes. "
            "A descarga química da crise dura cerca de noventa segundos. Ela só destrói sua noite se você ficar encarando a conversa. "
            "Esse é o ciclo real: noventa segundos de pânico falso que derretem depois de quinze minutos sem tela. "
            "Pergunta pra si mesmo: amanhã às nove da manhã eu vou sentir orgulho ou vergonha do que mandei? "
            "Mas ninguém raciocina bem com o aparelho brilhando na mão. "
            "Largue o celular em outro cômodo, dispare quinze minutos e decida só com a cabeça fria. "
            "Comenta ZERO que eu mando a Central SOS com cronômetro pro seu WhatsApp."
        ),
        "caption": (
            "Toda recaída mora num pico rápido de ansiedade que passa se você segurar 15 minutos.\n\n"
            "Salva esse vídeo pra hora que o impulso apertar de noite.\n\n"
            "Comenta ZERO ou chama no WhatsApp da bio: (12) 99659-3222.\n\n"
            "#contatozero #ansiedade #autocontrole #termino #codigozero"
        ),
    },
    {
        "topic": "Cada olhada nos stories zera seu desmame de dopamina (Ambos #18)",
        "audience": "ambos",
        "music_bed": "thriller",
        "theme_start": "noir",
        "hook_mode": "cinema",
        "broll_ids": ["4915", "28901", "40746"],
        "case_tag": "DESMAME • RECAÍDA OCULTA",
        "emotion_direction": "Direto e revelador, mostrando o vício da micro-dose digital.",
        "hook_headline": "UMA ESPIADA ZERA TUDO.",
        "hook_highlight": "ZERA TUDO.",
        "hook_card": {"sender": "10 SEGUNDOS", "msg": "'Só vou olhar rapidinho pra ver se tá tudo bem...'", "stamp": "MICRO-DOSE DE DOPAMINA"},
        "beat1_kicker": "O ERRO INVISÍVEL",
        "beat1_big": "ESPIAR É NÃO SAIR DO LUGAR.",
        "beat1_sub": "Você acha que não mandou oi, mas reabasteceu a fissura.",
        "board_type": "strike_stat",
        "board_title": "Sem mandar oi vs Sem espiar",
        "board_big": "ZERO",
        "board_wrong_lbl": "NÃO MANDA MENSAGEM, MAS OLHA TODO DIA",
        "board_wrong": "Mantém o cérebro em alerta eterno e não cura em meses",
        "board_right_lbl": "CORTE DE ESTÍMULO REAL",
        "board_right": "14 dias sem imagem nem perfil aceleram a liberdade",
        "board_source": "FISIOLOGIA DO HÁBITO • CÓDIGO ZERO",
        "beat3_kicker": "VERDADE DURA",
        "beat3_big": "PERFIL DO EX É VITRINE EDITADA.",
        "beat3_sub": "Você compara seus piores dias com um recorte ensaiado.",
        "rehook_text": "Silenciar não é fraqueza, é higiene mental.",
        "rehook_sub": "Quem quer respirar livre tira o veneno da própria mesa.",
        "steps": [
            {"title": "Silencie ou bloqueie", "desc": "Tire stories, curtidas e últimas visualizações."},
            {"title": "Zere o contador", "desc": "Se espiar hoje, recomece o dia 1 honesto."},
            {"title": "Troque o hábito noturno", "desc": "Substitua a checagem por ação física real."},
        ],
        "cue_words": ["reabasteceu", "manda", "vitrine", "higiene", "silencie", "ZERO"],
        "narration": (
            "Você jura que tá em contato zero porque não mandou oi... mas olha o perfil todo dia? Para. "
            "Uma espiada de cinco segundos zera o relógio e reabastece a fissura no seu cérebro. "
            "Ficar sem falar, mas olhando tudo, mantém sua mente presa no loop como um viciado olhando a vitrine. "
            "E você ainda compara seu pior momento com uma foto ensaiada na rede social. "
            "Silenciar não é fraqueza nenhuma, é pura higiene mental. "
            "Corte stories hoje, pare de checar sinais e proteja seus catorze dias reais. "
            "Comenta ZERO que eu te envio o plano completo."
        ),
        "caption": (
            "Contato zero não vale se você passa a noite vigiando stories e status.\n\n"
            "Cada olhada renova a dor por mais uma semana inteira.\n\n"
            "Comenta ZERO ou chama no WhatsApp da bio: (12) 99659-3222.\n\n"
            "#stalkear #contatozero #superartermino #saudemental #codigozero"
        ),
    },
    {
        "topic": "O paradoxo de correr atrás: perseguição ativa fuga (Ambos #19)",
        "audience": "ambos",
        "music_bed": "enquete",
        "theme_start": "paper",
        "hook_mode": "split",
        "broll_ids": ["35426", "28897", "8739"],
        "case_tag": "PSICOLOGIA • PARADOXO",
        "emotion_direction": "Lúcido, incisivo e revelador sobre dinâmica humana.",
        "hook_headline": "CORRER ATRÁS EMPURRA PRA LONGE.",
        "hook_highlight": "EMPURRA",
        "hook_card": {"sender": "LEI HUMANA", "msg": "Quanto mais você insiste, menos espaço existe pro retorno", "stamp": "EFEITO REPULSÃO"},
        "beat1_kicker": "DINÂMICA INVISÍVEL",
        "beat1_big": "PRESSÃO GERA RESISTÊNCIA.",
        "beat1_sub": "Ninguém sente falta de quem nunca saiu da porta.",
        "board_type": "strike_stat",
        "board_title": "O paradoxo do espaço",
        "board_big": "180°",
        "board_wrong_lbl": "INSISTIR, EXPLICAR E COBRAR",
        "board_wrong": "Sufoca a outra pessoa e confirma que ir embora foi alívio",
        "board_right_lbl": "RETIRADA AUTÊNTICA",
        "board_right": "Devolve ar, restaura respeito e cura sua dependência",
        "board_source": "BASE PSICOLÓGICA • CÓDIGO ZERO",
        "beat3_kicker": "LIÇÃO REAL",
        "beat3_big": "AUSÊNCIA É O ÚNICO ESPELHO.",
        "beat3_sub": "Seja pra virar a página ou pra ganhar respeito real.",
        "rehook_text": "Mas quase ninguém aguenta o silêncio dos primeiros dias.",
        "rehook_sub": "É aqui que o medo faz você quebrar tudo.",
        "steps": [
            {"title": "Recolha sua presença", "desc": "Devolva o espaço que a pessoa escolheu ter."},
            {"title": "Mude o foco pra você", "desc": "O único território que você controla hoje."},
            {"title": "Sustente 14 dias firmes", "desc": "A clareza sempre vence o desespero."},
        ],
        "cue_words": ["porta", "paradoxo", "espelho", "aguenta", "recolha", "ZERO"],
        "narration": (
            "Quanto mais você corre atrás tentando salvar a relação, mais rápido empurra a outra pessoa pra longe. "
            "É simples: pressão constante cria alívio de fugir, nunca saudade. Ninguém sente falta de quem não sai da porta. "
            "No paradoxo emocional, insistir confirma pro outro que ir embora foi a decisão certa. "
            "Sua ausência inteira é o único espelho que funciona, tanto pra respeito quanto pra sua cura. "
            "Mas quase ninguém aguenta o silêncio dos primeiros dias sem recair. "
            "Recolha sua presença agora, redirecione sua energia pra si e sustente catorze dias. "
            "Comenta ZERO que eu libero o Código Zero pra você hoje."
        ),
        "caption": (
            "Insistir onde não há abertura nunca cria atração: só confirma sufoco.\n\n"
            "Quando você se retira com dignidade, vence das duas formas: ou ganha respeito real, ou ganha sua paz de volta.\n\n"
            "Comenta ZERO ou chama no WhatsApp da bio: (12) 99659-3222.\n\n"
            "#contatozero #psicologia #relacionamento #superacao #codigozero"
        ),
    },
    {
        "topic": "A Janela Controlada de 15 min pra parar de ruminar (Ambos #20)",
        "audience": "ambos",
        "music_bed": "arpege",
        "theme_start": "paper",
        "hook_mode": "split",
        "broll_ids": ["41638", "28901", "2846"],
        "case_tag": "TÉCNICA BORKOVEC • FOCO",
        "emotion_direction": "Prático, direto e reconfortante, devolvendo produtividade no dia.",
        "hook_headline": "PARE DE BRIGAR COM A MENTE.",
        "hook_highlight": "BRIGAR",
        "hook_card": {"sender": "EFEITO REBOTE", "msg": "'Não quero pensar nisso' faz você pensar em dobro", "stamp": "TÉCNICA CLÍNICA"},
        "beat1_kicker": "CIÊNCIA DO FOCO",
        "beat1_big": "PROIBIR PENSAMENTO MULTIPLICA.",
        "beat1_sub": "O cérebro testa todo minuto se você já esqueceu.",
        "board_type": "neuro_curve",
        "board_title": "Janela Controlada de 15 min",
        "board_a_label": "DIA INTEIRO SOLTO",
        "board_a_text": "Invasões roubam trabalho, treino e energia a cada hora",
        "board_b_label": "18H30 • 15 MINUTOS",
        "board_b_text": "Você confina a ruminação num único horário fixo",
        "board_source": "CONTROLE DE ESTÍMULOS • BORKOVEC",
        "beat3_kicker": "RESULTADO PRÁTICO",
        "beat3_big": "SEU DIA VOLTA A RENDER.",
        "beat3_sub": "Em 5 dias o cérebro aprende a esperar o horário.",
        "rehook_text": "O truque não é apagar a memória à força.",
        "rehook_sub": "É dar hora marcada pra dor sem perder sua semana.",
        "steps": [
            {"title": "Marque 18h30 todo dia", "desc": "Separe exatamente 15 min num lugar neutro."},
            {"title": "Adie durante o trabalho", "desc": "Pensamento veio às 10h? 'Penso nisso às 18h30.'"},
            {"title": "Escreva e encerre", "desc": "Deu 15 min, feche o caderno e mude de cômodo."},
        ],
        "cue_words": ["esqueceu", "janela", "render", "truque", "marque", "ZERO"],
        "narration": (
            "Quanto mais você se obriga a não pensar no seu ex ou na sua ex, mais a imagem invade seu dia? "
            "Na psicologia, tentar proibir um pensamento faz o cérebro checar cada minuto se você já esqueceu. "
            "A saída clínica se chama Janela Controlada: confine a dor em quinze minutos fixos do dia. "
            "Em menos de uma semana, sua atenção volta a render no trabalho e no treino. "
            "O truque não é apagar a memória na marra. "
            "Marque seis e meia da tarde, adie qualquer invasão pro horário marcado e feche o caderno ao fim. "
            "Comenta ZERO que eu mando o método completo no seu WhatsApp."
        ),
        "caption": (
            "Tentar 'não pensar' após o término só alimenta o efeito rebote na sua cabeça.\n\n"
            "Use a Janela Controlada de 15 minutos e retome seu foco já nessa semana.\n\n"
            "Comenta ZERO ou chama no WhatsApp da bio: (12) 99659-3222.\n\n"
            "#ansiedade #foco #psicologia #superartermino #codigozero"
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


def resolve_voice_gender(script: dict, history: dict) -> str:
    aud = script.get("audience", "ambos")
    if aud in ("masculino", "feminino"):
        return aud
    last_vg = next((p.get("voice_gender") for p in reversed(history.get("posted", [])) if p.get("voice_gender")), "feminino")
    return "masculino" if last_vg == "feminino" else "feminino"


def _validate_v4_script(parsed: dict) -> bool:
    req = (
        "topic", "audience", "music_bed", "theme_start", "hook_mode", "broll_ids",
        "case_tag", "emotion_direction", "hook_headline", "hook_highlight", "hook_card",
        "beat1_kicker", "beat1_big", "beat1_sub", "board_type", "board_title",
        "beat3_kicker", "beat3_big", "beat3_sub", "rehook_text", "rehook_sub",
        "steps", "cue_words", "narration", "caption",
    )
    if not all(parsed.get(k) for k in req):
        return False
    if parsed.get("audience") not in ("masculino", "feminino", "ambos"):
        return False
    if parsed.get("board_type") not in ("strike_stat", "neuro_curve", "msg_deconstruct"):
        return False
    if not isinstance(parsed.get("broll_ids"), list) or len(parsed["broll_ids"]) < 3:
        return False
    if not isinstance(parsed.get("steps"), list) or len(parsed["steps"]) != 3:
        return False
    if not isinstance(parsed.get("cue_words"), list) or len(parsed["cue_words"]) != 6:
        return False
    return True


def generate_script(history: dict, forced_audience: str = "auto") -> dict:
    """Seleciona ou gera roteiro Studio v4 balanceado (masculino / feminino / ambos)."""
    target_audience = choose_next_audience(history, forced_audience)
    posted_topics = [item.get("topic") or item.get("verse", "") for item in history.get("posted", [])]

    if GEMINI_API_KEY and os.environ.get("USE_CURATED_ONLY") != "1":
        recent = posted_topics[-25:]
        aud_guide = {
            "masculino": "FOCO EXCLUSIVO NO PÚBLICO MASCULINO (ela terminou, pediu tempo, testou ego; linguagem direta de homem para homem, postura, sem melodrama).",
            "feminino": "FOCO EXCLUSIVO NO PÚBLICO FEMININO (ele sumiu, mandou oi de madrugada, pediu amizade; lucidez e amor-próprio direto).",
            "ambos": "PÚBLICO AMBOS OS GÊNEROS (use 'você' e 'essa pessoa' / 'ex' de forma neutra, focado em neurociência e psicologia aplicada a homens e mulheres).",
        }[target_audience]
        pool_summary = json.dumps(BROLL_POOL, ensure_ascii=False)
        prompt = f"""
Você é diretor criativo e editor-chefe de estúdio do projeto CÓDIGO ZERO (Protocolo 14 Dias, Central SOS e 16 Scripts anti-recaída pós-término). WhatsApp na bio: {WHATSAPP_DISPLAY}.
Missão deste vídeo: {aud_guide}

Crie um roteiro editorial estilo documentário moderno de 24 a 32 segundos (70 a 95 palavras na narração), completamente DIFERENTE destes temas: {recent}.
Regras duras de estúdio:
- Gancho nos primeiros 2s: frase de abertura <= 11 palavras com tensão real. Zero "pare de rolar", zero travessões "—", zero clichês de IA.
- Português brasileiro falado natural ("tá", "pra"). Re-hook obrigatório perto da metade do roteiro.
- Última frase: "Comenta ZERO aqui que eu te envio o acesso completo." ou similar citando ZERO.
- Escolha exatamente 3 IDs de B-roll do catálogo válido {pool_summary} para `broll_ids`.
- `music_bed`: um de ["enquete", "thriller", "arpege", "compte-a-rebours"].
- `theme_start`: "noir" ou "paper"; `hook_mode`: "split" ou "cinema".
- `board_type`: "strike_stat" (com board_big, board_wrong_lbl, board_wrong, board_right_lbl, board_right, board_source), OR "neuro_curve" (com board_a_label, board_a_text, board_b_label, board_b_text, board_source), OR "msg_deconstruct" (com board_msg, board_decode, board_source).
- `hook_card`: {{"sender": ..., "msg": <=48 chars, "stamp": <=22 chars CAPS}}.
- `steps`: 3 itens {{"title": <=24 chars, "desc": <=46 chars}}.
- `cue_words`: EXATAMENTE 6 palavras/termos isolados QUE APARECEM EM ORDEM na `narration` marcando: [fim do gancho / Beat1, início Board / Beat2, Beat3, Re-hook / Beat4, Passos / Beat5, CTA "ZERO" / Beat6].

Retorne APENAS JSON válido seguindo todas as chaves de Studio v4.
"""
        body = json.dumps({
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseMimeType": "application/json", "temperature": 0.9},
        }).encode("utf-8")

        for model in ["gemini-2.5-flash", "gemini-2.5-flash-lite"]:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
            for attempt in range(2):
                try:
                    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
                    with urllib.request.urlopen(req, timeout=40) as resp:
                        res = json.loads(resp.read().decode("utf-8"))
                    raw = res["candidates"][0]["content"]["parts"][0]["text"].strip()
                    raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.I)
                    parsed = json.loads(raw)
                    if _validate_v4_script(parsed):
                        parsed["caption"] = parsed["caption"].replace("—", "-").replace("link da bio", "WhatsApp da bio")
                        parsed["narration"] = parsed["narration"].replace("—", ",").replace("link da bio", "WhatsApp da bio")
                        print(f"Roteiro v4 ({target_audience}) gerado via Gemini ({model})!")
                        return parsed
                except Exception as exc:
                    print(f"Tentativa {attempt + 1} Gemini v4 em {model}: {exc}")
                    time.sleep(1.5)

    print(f"Selecionando roteiro v4 curado para público={target_audience}...")
    pool = [s for s in CURATED_SCRIPTS if s["audience"] == target_audience and s["topic"] not in posted_topics]
    if not pool:
        pool = [s for s in CURATED_SCRIPTS if s["audience"] == target_audience] or CURATED_SCRIPTS
    recent_set = set(posted_topics[-12:])
    fresh = [s for s in pool if s["topic"] not in recent_set] or pool
    return random.choice(fresh)


def synthesize_studio_voice(narration: str, emotion: str, voice_gender: str, out_mp3: Path, local_voice: str = "") -> tuple[float, list[dict], dict]:
    """Gera locução estúdio masculina ou feminina (Gemini 2.5 Flash TTS -> Edge TTS fallback)."""
    profile = VOICE_PROFILES.get(voice_gender, VOICE_PROFILES["feminino"])
    tts_info = {"tts_engine": "", "tts_voice": "", "tts_gender": voice_gender, "tts_error": None}

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
        f"## SCENE DIRECTION\nStyle: {emotion}\n"
        "Pacing: Fala humana envolvente em português brasileiro natural, dicção limpa de estúdio, sem soar robô.\n\n"
        f"## TRANSCRIPT\n{narration}"
    )

    if GEMINI_API_KEY:
        models = ["gemini-2.5-flash-preview-tts", "gemini-2.5-flash-tts"]
        voices = profile["gemini_voices"][:]
        random.shuffle(voices[:2])  # Alterna timbre principal mantendo consistência
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
                    with urllib.request.urlopen(req, timeout=45) as resp:
                        res = json.loads(resp.read().decode("utf-8"))
                    parts = res["candidates"][0]["content"]["parts"]
                    inline = next((p.get("inlineData") or p.get("inline_data") for p in parts if p.get("inlineData") or p.get("inline_data")), None)
                    if not inline or not inline.get("data"):
                        raise RuntimeError("Resposta sem inlineData de áudio")
                    audio_bytes = base64.b64decode(inline["data"])
                    if len(audio_bytes) < 8_000:
                        raise RuntimeError("Áudio curto demais")
                    mime = inline.get("mimeType") or inline.get("mime_type") or "audio/L16;rate=24000"
                    rate_m = re.search(r"rate=(\d+)", mime)
                    sample_rate = int(rate_m.group(1)) if rate_m else 24000
                    pcm_path.write_bytes(audio_bytes)
                    subprocess.check_call([
                        "ffmpeg", "-y", "-v", "error", "-f", "s16le", "-ar", str(sample_rate), "-ac", "1",
                        "-i", str(pcm_path), "-c:a", "libmp3lame", "-q:a", "2", "-ar", "44100", "-ac", "2", str(out_mp3),
                    ])
                    dur = float(subprocess.check_output([
                        "ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=noprint_wrappers=1:nokey=1", str(out_mp3),
                    ]).decode().strip())
                    if dur < 8.0 or dur > 70.0:
                        raise RuntimeError(f"Duração anômala Gemini TTS: {dur:.2f}s")
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

    # Edge TTS neural fallback (Antonio/Fabio para masculino, Thalita/Francisca para feminino)
    words: list[dict] = []
    tts_text = narration.replace("...", ",")
    chosen_edge = profile["edge_voices"][0]
    for ev in profile["edge_voices"]:
        try:
            import edge_tts

            async def _run(v=ev) -> None:
                comm = edge_tts.Communicate(
                    text=tts_text, voice=v, rate=profile["edge_rate"],
                    pitch=profile["edge_pitch"], boundary="WordBoundary",
                )
                with out_mp3.open("wb") as f:
                    async for chunk in comm.stream():
                        if chunk.get("type") == "audio":
                            f.write(chunk["data"])
                        elif chunk.get("type") == "WordBoundary":
                            st = chunk["offset"] / 10_000_000.0
                            dr = chunk["duration"] / 10_000_000.0
                            words.append({"text": chunk["text"], "start": round(st, 3), "end": round(st + max(0.08, dr), 3)})

            asyncio.run(_run())
            chosen_edge = ev
            if out_mp3.exists() and out_mp3.stat().st_size > 8_000:
                break
        except Exception as exc:
            print(f"Aviso edge_tts ({ev}): {exc}")
            words.clear()

    if not out_mp3.exists() or out_mp3.stat().st_size < 4_000:
        tts_prefix = ["edge-tts"] if shutil.which("edge-tts") else ["uvx", "edge-tts"]
        subprocess.check_call(tts_prefix + [
            "--voice", chosen_edge, f"--rate={profile['edge_rate']}",
            "--text", tts_text, "--write-media", str(out_mp3),
        ])

    dur = float(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(out_mp3),
    ]).decode().strip())
    tts_info.update({"tts_engine": "edge-tts-fallback", "tts_voice": chosen_edge})
    print(f"TTS_ENGINE=edge-tts ({chosen_edge}, dur={dur:.2f}s)")
    return dur, words, tts_info


def _normalize_tok(t: str) -> str:
    return re.sub(r"[^\wà-ÿ]", "", t.lower())


def align_words_to_audio(narration: str, mp3_path: Path, dur: float, pre_words: list[dict]) -> tuple[list[dict], str, str]:
    if pre_words:
        return pre_words, "edge-wordboundary", " ".join(w["text"] for w in pre_words[:18])

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
                    next_start = prev_end + 0.25 * (end_gap - idx)
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
        print(f"Aviso faster-whisper fallback ({exc}); usando distribuição ponderada...")

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


def compute_beat_times(words: list[dict], cue_words: list[str], voice_dur: float, delay: float = 0.18) -> tuple[list[float], float]:
    """Sincroniza os 7 cortes visuais exatamente com as palavras-âncora da fala."""
    total_dur = max(21.0, round(voice_dur + delay + 2.2, 1))
    defaults = [
        round(voice_dur * 0.14, 2),
        round(voice_dur * 0.28, 2),
        round(voice_dur * 0.44, 2),
        round(voice_dur * 0.56, 2),
        round(voice_dur * 0.69, 2),
        round(voice_dur * 0.88, 2),
        round(min(total_dur - 2.0, voice_dur + delay + 0.15), 2),
    ]
    if not words or len(cue_words) != 6:
        return defaults, total_dur

    found: list[float] = []
    search_idx = 0
    for i, cue in enumerate(cue_words):
        norm_cue = _normalize_tok(cue)
        hit = None
        for wi in range(search_idx, len(words)):
            if _normalize_tok(words[wi]["text"]) == norm_cue or norm_cue in _normalize_tok(words[wi]["text"]):
                hit = words[wi]["start"] + delay
                search_idx = wi + 1
                break
        if hit is None:
            hit = defaults[i]
        found.append(round(hit, 2))

    # Garante ritmo dinâmico (entre 2.0s e 3.8s por batida, sem estancar) e tempo suficiente pros passos
    t1 = max(1.8, min(found[0], 3.2))
    t2 = max(t1 + 2.2, min(found[1], t1 + 3.6))
    t3 = max(t2 + 2.8, min(found[2], t2 + 4.2))
    t4 = max(t3 + 2.0, min(found[3], t3 + 3.2))
    t5 = max(t4 + 2.2, min(found[4], t4 + 3.2))
    t6 = max(t5 + 4.2, min(found[5], total_dur - 4.4))
    t7 = max(t6 + 2.1, round(total_dur - 2.1, 2))
    if t7 > total_dur - 1.5:
        total_dur = round(t7 + 2.0, 1)
    return [round(x, 2) for x in (t1, t2, t3, t4, t5, t6, t7)], total_dur


def build_caption_chunks(words: list[dict], delay_offset: float = 0.18) -> tuple[list[dict], str]:
    """Blocos curtos 1–3 palavras estilo Studio (legível em qualquer fundo)."""
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
            and clean not in {"zero", "whatsapp", "instagram", "sos", "michigan", "borkovec", "kross"}
            and prev_gap >= 0.12
        )
        ends_sentence = bool(re.search(r"[.!?]$", raw_txt))
        if cur and (len(cur) >= 3 or cur_len + len(raw_txt) > 18 or prev_gap >= 0.22 or starts_new_sentence):
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
        spans = "".join(f'<span class="w" id="w-{ci}-{wi}">{html.escape(w["text"])}</span>' for wi, w in enumerate(ch["words"]))
        html_parts.append(f'<div class="cap-chunk" id="chunk-{ci}">{spans}</div>')
    return chunks, "\n".join(html_parts)


def prep_broll_clip(clip_id: str, dur_needed: float, out_mp4: Path, fallback_ids: list[str]) -> str:
    """Baixa (com cache), corta, grada estilo cinema e pré-reencoda com GOP curto (-g 10) para seek rápido."""
    curl_bin = shutil.which("curl.exe") or shutil.which("curl") or "curl"
    candidates = [clip_id] + [x for x in fallback_ids if x != clip_id]
    raw_file = None
    used_id = clip_id

    for cid in candidates:
        cached = BROLL_CACHE_DIR / f"{cid}-720.mp4"
        if cached.exists() and cached.stat().st_size > 120_000:
            raw_file = cached
            used_id = cid
            break
        url = f"https://assets.mixkit.co/videos/{cid}/{cid}-720.mp4"
        try:
            subprocess.check_call([curl_bin, "-fsSL", "--max-time", "22", "-A", "Mozilla/5.0", "-o", str(cached), url])
            if cached.exists() and cached.stat().st_size > 120_000:
                raw_file = cached
                used_id = cid
                print(f"B-roll Mixkit baixado: {cid}")
                break
        except Exception as exc:
            print(f"Aviso download B-roll {cid}: {exc}")

    clip_dur = round(max(3.0, dur_needed + 0.35), 2)
    if raw_file and raw_file.exists():
        # Cinema grade uniforme + crop vertical 1080x1920 + fast GOP-10 para Chromium/HyperFrames
        subprocess.check_call([
            "ffmpeg", "-y", "-v", "error",
            "-stream_loop", "-1", "-i", str(raw_file),
            "-t", str(clip_dur),
            "-vf", (
                "fps=30,"
                "scale=1080:1920:force_original_aspect_ratio=increase,"
                "crop=1080:1920,"
                "eq=contrast=1.12:saturation=0.70:brightness=-0.04,"
                "vignette=PI/4"
            ),
            "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-g", "10",
            "-pix_fmt", "yuv420p", "-an", "-movflags", "+faststart", str(out_mp4),
        ])
        return used_id

    # Fallback cinematográfico escuro se offline
    subprocess.check_call([
        "ffmpeg", "-y", "-v", "error", "-f", "lavfi",
        "-i", f"color=c=#121318:s=1080x1920:r=30:d={clip_dur}",
        "-vf", "noise=alls=8:allf=t+u,vignette=PI/3",
        "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-g", "10", "-pix_fmt", "yuv420p", str(out_mp4),
    ])
    return "fallback-noir"


def resolve_bgm(bed_name: str) -> Path:
    local_bed = ASSETS_DIR / "music" / f"{bed_name}.mp3"
    if local_bed.exists() and local_bed.stat().st_size > 25_000:
        return local_bed
    enq = ASSETS_DIR / "music" / "enquete.mp3"
    if enq.exists():
        return enq
    out = BUILD_DIR / "bgm_fallback.mp3"
    subprocess.check_call([
        "ffmpeg", "-y", "-v", "error", "-f", "lavfi",
        "-i", "aevalsrc=0.10*sin(2*PI*146.83*t)+0.06*sin(2*PI*220*t):s=44100:d=50",
        "-af", "lowpass=f=420", str(out),
    ])
    return out


def build_beat0_html(script: dict) -> str:
    hl = script["hook_headline"]
    kw = script["hook_highlight"]
    marker_svg = (
        '<svg class="marker-svg" viewBox="0 0 200 18" preserveAspectRatio="none">'
        '<path id="hookMarker" d="M 3 12 Q 95 2 196 10" fill="none" stroke="#d92b4b" '
        'stroke-width="6" stroke-linecap="round" pathLength="100" stroke-dasharray="100 120" stroke-dashoffset="105"/></svg>'
    )
    if kw in hl:
        idx = hl.index(kw)
        marked = (
            html.escape(hl[:idx])
            + f'<span class="marker-wrap">{html.escape(kw)}{marker_svg}</span>'
            + html.escape(hl[idx + len(kw):])
        )
    else:
        marked = html.escape(hl)

    hc = script["hook_card"]
    return f"""
      <div class="arch-meta">
        <span>{html.escape(script["case_tag"])}</span>
        <span class="arch-tag">MÉTODO Z.E.R.O.</span>
      </div>
      <div class="hero-headline">{marked}</div>
      <div class="ios-notif" id="hookCard">
        <div class="ios-row" data-layout-ignore="true"><span>MENSAGEM / CONTEXTO</span><span>AGORA</span></div>
        <div class="ios-sender">{html.escape(hc["sender"])}</div>
        <div class="ios-msg">{html.escape(hc["msg"])}</div>
        <div class="stamp-badge" id="hookStamp">{html.escape(hc["stamp"])}</div>
      </div>
    """


def build_cinema_callout_html(kicker: str, big: str, sub: str, marker_id: str = "") -> str:
    m_line = ""
    if marker_id:
        m_line = (
            f'<svg style="width:260px;height:14px;margin-top:4px;" viewBox="0 0 260 14">'
            f'<path id="{marker_id}" d="M 4 9 Q 130 2 256 9" fill="none" stroke="#e2a43b" stroke-width="5" '
            f'stroke-linecap="round" pathLength="100" stroke-dasharray="100 120" stroke-dashoffset="105"/></svg>'
        )
    return f"""
      <div class="cinema-kicker">{html.escape(kicker)}</div>
      <div class="cinema-big">{html.escape(big)}</div>
      {m_line}
      <div class="cinema-sub">{html.escape(sub)}</div>
    """


def build_beat2_html(script: dict) -> str:
    bt = script["board_type"]
    head = (
        '<div class="arch-meta"><span>02 // PROVA EDITORIAL</span>'
        f'<span class="arch-tag">{html.escape(script["audience"].upper())}</span></div>'
        f'<div class="board-title">{html.escape(script["board_title"])}</div>'
    )
    if bt == "strike_stat":
        return f"""
          {head}
          <div class="stat-hero">{html.escape(script["board_big"])}</div>
          <div class="strike-card" id="statWrong">
            <div class="strike-lbl" style="color:#d92b4b;">✕ {html.escape(script["board_wrong_lbl"])}</div>
            <div class="strike-txt" style="position:relative;">
              {html.escape(script["board_wrong"])}
              <svg class="strike-line-svg" viewBox="0 0 400 70" preserveAspectRatio="none">
                <path id="strikeSlash" d="M 4 42 L 396 26" fill="none" stroke="#d92b4b" stroke-width="6"
                  stroke-linecap="round" pathLength="100" stroke-dasharray="100 120" stroke-dashoffset="105"/>
              </svg>
            </div>
          </div>
          <div class="strike-card truth" id="statRight">
            <div class="strike-lbl" style="color:#2e9e73;">✓ {html.escape(script["board_right_lbl"])}</div>
            <div class="strike-txt">{html.escape(script["board_right"])}</div>
          </div>
          <div class="source-foot">{html.escape(script["board_source"])}</div>
        """
    if bt == "neuro_curve":
        return f"""
          {head}
          <div class="chart-box">
            <svg viewBox="0 0 740 230" width="100%" height="220">
              <line x1="30" y1="55" x2="710" y2="55" stroke="rgba(130,125,115,0.22)" stroke-dasharray="6 6"/>
              <line x1="30" y1="130" x2="710" y2="130" stroke="rgba(130,125,115,0.22)" stroke-dasharray="6 6"/>
              <line x1="30" y1="205" x2="710" y2="205" stroke="rgba(130,125,115,0.4)"/>
              <path id="neuroCurve" d="M 40 200 C 120 200, 170 46, 260 55 C 370 65, 440 185, 680 190"
                fill="none" stroke="#d92b4b" stroke-width="8" stroke-linecap="round"
                pathLength="100" stroke-dasharray="100 120" stroke-dashoffset="105"/>
              <circle id="neuroDot" cx="40" cy="200" r="12" fill="#e2a43b" stroke="#121318" stroke-width="4"/>
            </svg>
          </div>
          <div class="strike-card" style="margin-bottom:14px;">
            <div class="strike-lbl" style="color:#d92b4b;">{html.escape(script["board_a_label"])}</div>
            <div class="strike-txt" style="font-size:28px;">{html.escape(script["board_a_text"])}</div>
          </div>
          <div class="strike-card truth">
            <div class="strike-lbl" style="color:#2e9e73;">{html.escape(script["board_b_label"])}</div>
            <div class="strike-txt" style="font-size:28px;">{html.escape(script["board_b_text"])}</div>
          </div>
          <div class="source-foot">{html.escape(script["board_source"])}</div>
        """
    return f"""
      {head}
      <div class="ios-notif" style="margin-bottom:24px;">
        <div class="ios-row"><span>MENSAGEM ORIGINAL</span><span>ANÁLISE</span></div>
        <div class="ios-msg" style="font-size:36px;">{html.escape(script["board_msg"])}</div>
        <svg style="width:100%;height:14px;margin-top:8px;" viewBox="0 0 400 14" preserveAspectRatio="none">
          <path id="msgUnder" d="M 4 8 Q 200 2 396 8" fill="none" stroke="#e2a43b" stroke-width="6"
            stroke-linecap="round" pathLength="100" stroke-dasharray="100 120" stroke-dashoffset="105"/>
        </svg>
      </div>
      <div class="strike-card truth" id="msgDecode" style="border-color:#d92b4b;background:rgba(217,43,75,0.12);">
        <div class="strike-lbl" style="color:#d92b4b;">DECODIFICAÇÃO REAL</div>
        <div class="strike-txt" style="font-size:34px;">{html.escape(script["board_decode"])}</div>
      </div>
      <div class="source-foot">{html.escape(script["board_source"])}</div>
    """


def build_beat4_html(script: dict) -> str:
    return f"""
      <div class="arch-meta"><span>04 // A VIRADA DE CHAVE</span><span class="arch-tag">ATENÇÃO</span></div>
      <div class="rehook-quote">{html.escape(script["rehook_text"])}</div>
      <div class="rehook-sub">{html.escape(script["rehook_sub"])}</div>
    """


def build_beat5_html(script: dict) -> str:
    blocks: list[str] = []
    for idx, st in enumerate(script["steps"][:3]):
        pills = "".join(
            f'<span class="step-pill{" active" if p == idx else ""}">0{p + 1}</span>'
            for p in range(3)
        )
        blocks.append(f"""
          <div class="step-single" id="stepSingle{idx}">
            <div class="step-counter-row">{pills}</div>
            <div class="step-big-title">{html.escape(st["title"])}</div>
            <div class="step-big-desc">{html.escape(st["desc"])}</div>
          </div>
        """)
    return (
        '<div class="arch-meta"><span>05 // EXECUÇÃO EM 3 PASSOS</span>'
        '<span class="arch-tag">PROTOCOLO</span></div>'
        f'<div class="steps-viewport">{"".join(blocks)}</div>'
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Código Zero Studio Editorial v4 Generator")
    parser.add_argument("--audience", default="auto", choices=["auto", "masculino", "feminino", "ambos"])
    parser.add_argument("--local-voice", default="", help="MP3 local opcional para testar pipeline offline")
    parser.add_argument("--render-only", action="store_true", help="Não grava history.json (modo QA)")
    args = parser.parse_args()

    history = load_history()
    print("1. Selecionando/gerando roteiro Studio v4 balanceado...")
    script = generate_script(history, forced_audience=args.audience)
    voice_gender = resolve_voice_gender(script, history)
    print(f"Tema: {script['topic']} | Público={script['audience']} | Voz={voice_gender} | Board={script['board_type']}")

    print("2. Sintetizando locução estúdio...")
    voz_path = BUILD_DIR / "voz.mp3"
    voice_dur, pre_words, tts_info = synthesize_studio_voice(
        script["narration"], script.get("emotion_direction", "Lúcida e firme"),
        voice_gender, voz_path, local_voice=args.local_voice,
    )

    print("3. Sincronizando palavras e 7 âncoras de corte...")
    words, sync_engine, preview = align_words_to_audio(script["narration"], voz_path, voice_dur, pre_words)
    times, total_dur = compute_beat_times(words, script["cue_words"], voice_dur, delay=0.18)
    t1, t2, t3, t4, t5, t6, t7 = times
    print(f"Duração={total_dur}s | Cortes={times} | Sync={sync_engine}")

    print("4. Preparando 3 clipes cinema B-roll Mixkit (crop vertical + grade)...")
    hf_dir = BUILD_DIR / "hf_proj"
    assets_hf = hf_dir / "assets"
    assets_hf.mkdir(parents=True, exist_ok=True)

    broll_ids = script["broll_ids"]
    v0_dur = round(t3, 2)
    v1_start = round(t3, 2)
    v1_dur = round(max(1.5, t5 - t3), 2)
    v2_start = round(t5, 2)
    v2_dur = round(max(1.5, total_dur - t5), 2)
    fb_key = f"{voice_gender}_dor" if f"{voice_gender}_dor" in BROLL_POOL else "mood"
    used_brolls = [
        prep_broll_clip(broll_ids[0], v0_dur, assets_hf / "clip0.mp4", BROLL_POOL[fb_key]),
        prep_broll_clip(broll_ids[1], v1_dur, assets_hf / "clip1.mp4", BROLL_POOL["mood"]),
        prep_broll_clip(broll_ids[2], v2_dur, assets_hf / "clip2.mp4", BROLL_POOL["mood"]),
    ]

    chunks, captions_html = build_caption_chunks(words, delay_offset=0.18)
    theme_start = script.get("theme_start", "noir")
    theme_invert = "paper" if theme_start == "noir" else "noir"

    tpl = (ROOT / "template.html").read_text(encoding="utf-8")
    replacements = {
        "__DURATION__": str(total_dur),
        "__V0_DUR__": str(v0_dur),
        "__V1_START__": str(v1_start),
        "__V1_DUR__": str(v1_dur),
        "__V2_START__": str(v2_start),
        "__V2_DUR__": str(v2_dur),
        "__TIMES_JSON__": json.dumps(times),
        "__THEME_START__": theme_start,
        "__THEME_INVERT__": theme_invert,
        "__HOOK_MODE__": script.get("hook_mode", "split"),
        "__BOARD_TYPE__": script["board_type"],
        "__BEAT0_HTML__": build_beat0_html(script),
        "__BEAT1_HTML__": build_cinema_callout_html(script["beat1_kicker"], script["beat1_big"], script["beat1_sub"], "b1Marker"),
        "__BEAT2_HTML__": build_beat2_html(script),
        "__BEAT3_HTML__": build_cinema_callout_html(script["beat3_kicker"], script["beat3_big"], script["beat3_sub"]),
        "__BEAT4_HTML__": build_beat4_html(script),
        "__BEAT5_HTML__": build_beat5_html(script),
        "__CAPTIONS_HTML__": captions_html,
        "__CHUNKS_JSON__": json.dumps(chunks, ensure_ascii=False),
    }
    for k, v in replacements.items():
        tpl = tpl.replace(k, v)
    (hf_dir / "index.html").write_text(tpl, encoding="utf-8")

    print("5. Renderizando vídeo 1080x1920 via HyperFrames...")
    video_no_audio = BUILD_DIR / "video_v4.mp4"
    hf_cmd = (
        ["cmd", "/c", "npx", "--yes", "hyperframes", "render", ".", "--output", str(video_no_audio)]
        if os.name == "nt"
        else ["npx", "--yes", "hyperframes", "render", ".", "--output", str(video_no_audio)]
    )
    subprocess.check_call(hf_cmd, cwd=str(hf_dir))

    print("6. Mixando trilha de cinema, SFX reais e masterização -14 LUFS...")
    bgm_path = resolve_bgm(script.get("music_bed", "enquete"))
    sfx_boom = ASSETS_DIR / "sfx" / "impact-boom.mp3"
    sfx_zhhh = ASSETS_DIR / "sfx" / "zhhh.mp3"
    sfx_pop = ASSETS_DIR / "sfx" / "pop-back.mp3"

    final_path = BUILD_DIR / "reel_final.mp4"
    fade_out_start = max(1.0, total_dur - 2.3)

    cmd_mix = ["ffmpeg", "-y", "-v", "error", "-i", str(video_no_audio), "-i", str(voz_path), "-i", str(bgm_path)]
    extra_inputs: list[tuple[Path, int, float]] = []
    if sfx_boom.exists():
        extra_inputs.append((sfx_boom, max(50, int((t1 - 0.15) * 1000)), 0.24))
    if sfx_zhhh.exists():
        extra_inputs.append((sfx_zhhh, max(100, int((t4 - 0.20) * 1000)), 0.22))
    if sfx_pop.exists():
        extra_inputs.append((sfx_pop, max(150, int((t6 + 0.65) * 1000)), 0.28))

    for p, _, _ in extra_inputs:
        cmd_mix.extend(["-i", str(p)])

    filters = [
        f"[1:a]aformat=sample_rates=44100:channel_layouts=stereo,adelay=180|180,"
        f"highpass=f=80,equalizer=f=3000:t=q:w=1.4:g=2.0,"
        f"acompressor=threshold=-18dB:ratio=2.5:attack=6:release=60,volume=1.52,"
        f"apad=whole_dur={total_dur},asplit=2[vmain][vsc]",
        f"[2:a]aformat=sample_rates=44100:channel_layouts=stereo,atrim=0:{total_dur},asetpts=PTS-STARTPTS,"
        f"afade=t=in:st=0:d=0.6,afade=t=out:st={fade_out_start}:d=2.3,volume=0.25[bgmraw]",
        "[bgmraw][vsc]sidechaincompress=threshold=0.035:ratio=4.5:attack=25:release=320[bgmduck]",
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

    (BUILD_DIR / "caption.txt").write_text(script["caption"], encoding="utf-8")
    meta = {
        "engine_version": "v4-studio",
        "date_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "topic": script["topic"],
        "audience": script["audience"],
        "voice_gender": voice_gender,
        "tts_engine": tts_info["tts_engine"],
        "tts_voice": tts_info["tts_voice"],
        "tts_error": tts_info["tts_error"],
        "sync_engine": sync_engine,
        "music_bed": bgm_path.name,
        "theme_start": theme_start,
        "broll_used": used_brolls,
        "duration": total_dur,
        "beats": times,
        "transcribed_preview": preview,
    }
    (BUILD_DIR / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    if not args.render_only:
        history["posted"].append({
            "date": meta["date_utc"],
            "topic": script["topic"],
            "audience": script["audience"],
            "voice_gender": voice_gender,
            "music_bed": bgm_path.name,
            "theme_start": theme_start,
            "broll_used": used_brolls,
            "tts_engine": tts_info["tts_engine"],
            "tts_voice": tts_info["tts_voice"],
        })
        save_history(history)
    print(f"Vídeo Studio v4 gerado com sucesso: {final_path}")


if __name__ == "__main__":
    main()

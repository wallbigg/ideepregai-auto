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
BUILD_DIR = ROOT / "build"
BUILD_DIR.mkdir(exist_ok=True)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_TTS_VOICE = os.environ.get("GEMINI_TTS_VOICE", "Sulafat")
EDGE_FALLBACK_VOICE = os.environ.get("TTS_VOICE", "pt-BR-FranciscaNeural")
WHATSAPP_DISPLAY = "(12) 99659-3222"

MUSIC_TOPICS = ["piano", "ambient", "cinematic", "sad", "calm"]

EMPHASIS_WORDS = {
    "não", "nunca", "jamais", "pare", "trava", "silêncio", "zero", "dói",
    "vergonha", "orgulho", "ego", "migalha", "migalhas", "abstinência",
    "noventa", "segundos", "madrugada", "recaída", "stalkear", "bloqueia",
    "dignidade", "paz", "mentira", "armadilha", "whatsapp", "bio", "sozinho",
    "sozinha", "culpa", "queimadura", "física", "reservas", "amigos",
    "respeito", "controle", "desmame", "lucidez", "carência",
}

# 18 roteiros estruturados v3 (4 atos visuais: Gatilho -> Ciência/Análise -> 3 Passos -> Código Zero)
CURATED_SCRIPTS = [
    {
        "topic": "Ex mandou 'Oi, tudo bem?' do nada (Script #01)",
        "badge": "SCRIPT #01 • ESCUDO",
        "emotion_direction": "Comece com urgência protetora de amiga íntima, seja firme na explicação e acolhedora no final.",
        "visual_type": "whatsapp",
        "hook_sender": "Ex • 01:42",
        "hook_msg": "\"Oi... tudo bem por aí? Sumiu.\"",
        "hook_alert": "NÃO RESPONDA NO IMPULSO",
        "scene2_type": "bars",
        "scene2_title": "O que acontece em cada escolha",
        "scene2_a_label": "SE RESPONDER COM TEXTÃO",
        "scene2_a_text": "Alimenta o ego dele e você volta para a estaca zero",
        "scene2_b_label": "SILÊNCIO DO ESCUDO #01",
        "scene2_b_text": "Você quebra o teste e recupera respeito imediato",
        "scene2_metric": "Esforço zero merece resposta zero",
        "steps": [
            {"title": "Trave o dedo por 15 min", "desc": "Tire o celular do rosto antes de qualquer reação."},
            {"title": "Não compense visualizações", "desc": "Abriu sem querer? Apenas feche e siga em silêncio."},
            {"title": "Responda ao esforço real", "desc": "Quem quer voltar assume erros, não manda isca vaga."},
        ],
        "narration": (
            "Se o seu ex mandou 'oi, tudo bem?' depois de semanas sumido... trava o dedo agora. "
            "Ele não voltou arrependido. Isso é isca de esforço zero pra testar se você ainda tá no banco de reservas. "
            "Se você responder na hora com textão, o ego dele enche e ele some de novo amanhã. "
            "A ação certa? Silêncio absoluto. Se visualizou sem querer, não manda nada pra compensar. "
            "Manda esse vídeo pra quem quase caiu nisso hoje. E se quiser os dezesseis scripts prontos do Código Zero, comenta ZERO ou chama no WhatsApp da bio."
        ),
        "caption": (
            "Salva antes de responder qualquer 'oi sumido' na madrugada.\n\n"
            "Quando o ex manda mensagem vazia depois do término, responder na ansiedade só alimenta o ego dele e reinicia a sua dor. "
            "A regra do contato zero no Código Zero é simples: responda ao tamanho real do esforço, nunca ao tamanho da sua saudade.\n\n"
            "Comenta ZERO ou chama no WhatsApp da bio: (12) 99659-3222.\n\n"
            "#contatozero #superartermino #dependenciaemocional #exmandoumensagem #codigozero"
        ),
    },
    {
        "topic": "Por que saudade dói no corpo como queimadura (Kross 2011)",
        "badge": "NEUROCIÊNCIA • PÁG. 04",
        "emotion_direction": "Tom acolhedor, humano e esclarecedor para tirar a culpa da pessoa que sofre.",
        "visual_type": "timer",
        "hook_label": "ESTUDO • UNIV. DE MICHIGAN",
        "hook_big": "DOR FÍSICA",
        "hook_sub": "Rejeição aciona a mesma rede cerebral de uma queimadura",
        "scene2_type": "wave",
        "scene2_title": "Curva da abstinência afetiva",
        "scene2_a_label": "DIAS 1 A 4 • CORTE QUÍMICO",
        "scene2_a_text": "Cérebro pede dopamina e gera dor física real",
        "scene2_b_label": "DIA 14 • REORGANIZAÇÃO",
        "scene2_b_text": "Circuito acalma com rotina de desmame diário",
        "scene2_metric": "Não é fraqueza: é biologia pura",
        "steps": [
            {"title": "Pare de se culpar hoje", "desc": "Aceite que seu corpo está em desmame químico."},
            {"title": "Corte gatilhos visuais", "desc": "Fotos e chat visíveis reiniciam o pico no cérebro."},
            {"title": "Siga 14 dias estruturados", "desc": "Substitua força bruta por método passo a passo."},
        ],
        "narration": (
            "Você acordou hoje com um aperto real no peito e achou que perdeu o amor-próprio? Escuta isso. "
            "Uma pesquisa da Universidade de Michigan provou que a rejeição amorosa aciona a mesma rede cerebral de uma queimadura física. "
            "Não é fraqueza sua. É corte químico de dopamina. "
            "Por isso conselho raso de 'é só esquecer' nunca funciona. Você precisa de um protocolo de desmame de catorze dias. "
            "Envia pra alguém que tá se culpando por ainda sofrer. Quer o Código Zero completo? Comenta ZERO ou chama no WhatsApp da bio."
        ),
        "caption": (
            "Para de se chamar de fraco ou fraca por ainda sentir aperto no peito.\n\n"
            "Entender como superar término começa na neurociência: estudos de imagem cerebral mostram que a abstinência afetiva imita dor física. "
            "Você não sai disso na força bruta, sai com método diário de 14 dias.\n\n"
            "Comenta ZERO ou chama direto no WhatsApp da bio: (12) 99659-3222.\n\n"
            "#dependenciaemocional #superartermino #neurociencia #saudeemocional #codigozero"
        ),
    },
    {
        "topic": "A Regra 90-15 antes de mandar mensagem às 23h",
        "badge": "FASE Z • REGRA 90–15",
        "emotion_direction": "Voz calma, firme e prática, guiando quem está prestes a ter uma recaída.",
        "visual_type": "timer",
        "hook_label": "TRAVA ANTI-RECAÍDA",
        "hook_big": "01:30",
        "hook_sub": "O pico químico da crise dura só 90 segundos",
        "scene2_type": "wave",
        "scene2_title": "O ciclo de 90 segundos da crise",
        "scene2_a_label": "0 A 90 SEGUNDOS",
        "scene2_a_text": "Adrenalina e vontade urgente sobem no limite",
        "scene2_b_label": "APÓS 15 MINUTOS",
        "scene2_b_text": "Onda passa e a lucidez assume o volante",
        "scene2_metric": "90s de onda vs 15 min de trava",
        "steps": [
            {"title": "Largue o celular fora da vista", "desc": "Deixe o aparelho em outro cômodo imediatamente."},
            {"title": "Dispare 15 min no relógio", "desc": "Escreva tudo num papel sem enviar nada."},
            {"title": "Pergunte sobre as 9h da manhã", "desc": "Amanhã eu vou sentir orgulho ou vergonha?"},
        ],
        "narration": (
            "Tá com o dedo coçando pra mandar mensagem pro seu ex agora? Faz a Regra Noventa Quinze. "
            "A descarga química da crise emocional dura só noventa segundos no sangue. Ela só dura a noite inteira porque você fica olhando o celular. "
            "Larga o aparelho em outro cômodo, dispara quinze minutos no relógio e escreve tudo num papel sem enviar. "
            "Quando o alarme tocar, pergunta: amanhã às nove da manhã eu vou sentir orgulho ou vergonha? "
            "Salva pra abrir hoje à noite. Quer a Central SOS com cronômetro no celular? Comenta ZERO ou chama no WhatsApp da bio."
        ),
        "caption": (
            "Nenhuma mensagem enviada no pico do pânico às 23h já reconquistou respeito.\n\n"
            "A Regra 90-15 é a trava mais forte para parar de mandar mensagem para ex e evitar a ressaca moral no dia seguinte. "
            "Na Central SOS do Código Zero você tem o cronômetro de 15 minutos direto no celular.\n\n"
            "Comenta ZERO ou chama no WhatsApp da bio: (12) 99659-3222.\n\n"
            "#contatozero #fimderelacionamento #amorproprio #dependenciaemocional #codigozero"
        ),
    },
    {
        "topic": "Esta mensagem foi apagada (Script #04)",
        "badge": "SCRIPT #04 • ISCA",
        "emotion_direction": "Tom lúcido, direto e protetor, cortando a ansiedade da curiosidade na hora.",
        "visual_type": "whatsapp",
        "hook_sender": "Ex • 23:54",
        "hook_msg": "⊘ Esta mensagem foi apagada",
        "hook_alert": "ARMADILHA DE CURIOSIDADE",
        "scene2_type": "flow",
        "scene2_title": "Como a isca captura sua mente",
        "scene2_a_label": "A ISCA DIGITAL",
        "scene2_a_text": "Apagar mensagem gera urgência sem compromisso algum",
        "scene2_b_label": "SEU INSTINTO",
        "scene2_b_text": "Perguntar 'o que era?' entrega controle de graça",
        "scene2_metric": "Silêncio absoluto desarma a armadilha na hora",
        "steps": [
            {"title": "Não pergunte o que era", "desc": "Curiosidade aberta é convite para joguinho."},
            {"title": "Lembre da regra adulta", "desc": "Se fosse sério e sincero, escreveria de novo."},
            {"title": "Arquive a conversa", "desc": "Tire o chat do topo para não ficar olhando."},
        ],
        "narration": (
            "Apareceu 'esta mensagem foi apagada' no chat do seu ex? Pelo amor de Deus, não pergunta o que era. "
            "Essa é uma das iscas mais velhas pra disparar ansiedade e fazer você puxar conversa primeiro. "
            "Pensa comigo: se fosse algo adulto, sincero e importante de verdade, a pessoa teria coragem de escrever de novo. "
            "Se apagou, deixa no vácuo. Você quebra o controle emocional na hora. "
            "Manda pra amiga que ia perguntar 'o que você ia falar?'. Quer os dezesseis scripts prontos? Comenta ZERO ou chama no WhatsApp da bio."
        ),
        "caption": (
            "Se fosse adulto e importante de verdade, não teria sido apagado.\n\n"
            "Saber lidar com sinais ambíguos evita recaídas no contato zero e devolve sua paz mental pós término. "
            "No Código Zero você tem 16 scripts prontos para cada armadilha sem improvisar.\n\n"
            "Comenta ZERO ou chama no WhatsApp da bio: (12) 99659-3222.\n\n"
            "#contatozero #exmandoumensagem #relacionamentotoxico #amorproprio #codigozero"
        ),
    },
    {
        "topic": "Já mandou textão e se humilhou? Botão de Reinício (#16)",
        "badge": "SCRIPT #16 • RESGATE",
        "emotion_direction": "Voz acolhedora no início para aliviar a vergonha, e cirurgicamente firme no script.",
        "visual_type": "contrast",
        "hook_left_tag": "O QUE PIORA TUDO",
        "hook_left_text": "Mandar mais 10 áudios tentando explicar o textão",
        "hook_right_tag": "BOTÃO DE REINÍCIO",
        "hook_right_text": "1 frase elegante + silêncio absoluto",
        "scene2_type": "bars",
        "scene2_title": "Como salvar sua dignidade hoje",
        "scene2_a_label": "SE TENTAR CONCERTAR",
        "scene2_a_text": "Cada áudio novo aumenta a sensação de desespero",
        "scene2_b_label": "BOTÃO DE REINÍCIO #16",
        "scene2_b_text": "Encerra com classe e devolve mistério na hora",
        "scene2_metric": "1 frase limpa apaga o peso do textão",
        "steps": [
            {"title": "Pare os áudios agora", "desc": "Não envie nenhuma explicação longa extra."},
            {"title": "Envie o Script #16", "desc": "Concorde com serenidade e deseje felicidades."},
            {"title": "Entre no Contato Zero", "desc": "Depois de enviar, desapareça com dignidade."},
        ],
        "narration": (
            "Chorou, mandou textão de madrugada e agora tá morrendo de vergonha? Para tudo. "
            "O pior erro agora é mandar mais dez mensagens tentando se justificar. "
            "Usa uma única vez o Botão de Reinício do Código Zero: 'Falei muita coisa no calor da emoção. Pensando com calma, você tinha razão, encerrar foi o melhor pra nós dois. Te desejo felicidades.' "
            "Envia isso e some. Você retoma a última palavra com elegância cirúrgica. "
            "Salva esse vídeo agora. Quer o protocolo completo de catorze dias? Comenta ZERO ou chama no WhatsApp da bio."
        ),
        "caption": (
            "Ter tropeçado ontem não apaga o seu valor. Tentar consertar no desespero é o que drena sua paz.\n\n"
            "O Script #16 do Código Zero foi criado para quem já mandou textão para ex e precisa virar a chave hoje com dignidade e silêncio real.\n\n"
            "Comenta ZERO ou chama direto no WhatsApp da bio: (12) 99659-3222.\n\n"
            "#superartermino #contatozero #dignidade #autoestima #codigozero"
        ),
    },
    {
        "topic": "O perigo da Zona Morta (22h às 02h)",
        "badge": "ZONA MORTA • 22H ÀS 02H",
        "emotion_direction": "Tom noturno, próximo e direto, alertando sobre o cansaço do cérebro à noite.",
        "visual_type": "timer",
        "hook_label": "ALERTA NOTURNO",
        "hook_big": "70%",
        "hook_sub": "das mensagens de recaída acontecem na cama à noite",
        "scene2_type": "wave",
        "scene2_title": "Queda do freio racional à noite",
        "scene2_a_label": "22H ÀS 02H • ZONA MORTA",
        "scene2_a_text": "Cansaço desliga o racional e dobra a saudade",
        "scene2_b_label": "COM TRAVA FÍSICA",
        "scene2_b_text": "Ambiente blindado impede recaídas na cama",
        "scene2_metric": "Força de vontade falha; ambiente vence",
        "steps": [
            {"title": "Carregador fora do quarto", "desc": "Às 22h30 o aparelho dorme longe da cama."},
            {"title": "Áudio neutro com timer", "desc": "Evite o silêncio pesado que puxa memórias."},
            {"title": "Cartão SOS visível", "desc": "Deixe a trava da Central SOS na tela de bloqueio."},
        ],
        "narration": (
            "Setenta por cento das recaídas de término acontecem entre dez da noite e duas da manhã. "
            "Não é coincidência. Com o cérebro exausto na horizontal, o córtex racional desliga e a saudade dobra de tamanho. "
            "Força de vontade falha às onze da noite. Só trava física protege você. "
            "Hoje às dez e meia, coloca o carregador fora do alcance da cama e bota um áudio neutro de fundo com timer. "
            "Manda pra quem sempre recai na madrugada. Quer o Protocolo da Madrugada e os seis Cartões SOS? Comenta ZERO ou chama no WhatsApp da bio."
        ),
        "caption": (
            "Nenhuma decisão amorosa tomada deitado na cama às 23h é lúcida.\n\n"
            "Se a saudade do ex aperta toda madrugada, você precisa de travas físicas de ambiente e do Protocolo da Madrugada do Código Zero.\n\n"
            "Comenta ZERO ou chama no WhatsApp da bio: (12) 99659-3222.\n\n"
            "#superartermino #insonia #dependenciaemocional #contatozero #codigozero"
        ),
    },
    {
        "topic": "Ele mandou 'Sonhei com você' (Script #08)",
        "badge": "SCRIPT #08 • NOSTALGIA",
        "emotion_direction": "Voz calma, empática e elegante, desarmando o apelo nostálgico com classe.",
        "visual_type": "whatsapp",
        "hook_sender": "Ex • 22:18",
        "hook_msg": "\"Sonhei com você ontem... passei lá e lembrei da gente\"",
        "hook_alert": "TESTE DE EGO DETECTADO",
        "scene2_type": "bars",
        "scene2_title": "Nostalgia vaga vs Intenção real",
        "scene2_a_label": "DERRETER NA RESPOSTA",
        "scene2_a_text": "Mostra porta aberta sem compromisso real de volta",
        "scene2_b_label": "RESPOSTA DO SCRIPT #08",
        "scene2_b_text": "Impõe limite gentil e testa se há atitude real",
        "scene2_metric": "Quem quer voltar fala claro, não usa charada",
        "steps": [
            {"title": "Respire antes de ler de novo", "desc": "Saudade vaga não significa pedido de volta."},
            {"title": "Use resposta curta e serena", "desc": "Agradeça as boas lembranças e foque em você."},
            {"title": "Observe o movimento real", "desc": "Se era só ego, ele desaparece sem insistir."},
        ],
        "narration": (
            "Ele mandou 'sonhei com você' ou 'passei naquele lugar e lembrei da gente'? Respira antes de derreter. "
            "Nostalgia vaga não é pedido de volta nem assunção de erro. Ele só tá testando se a porta ainda tá destrancada. "
            "Se você responder 'eu também tô morrendo de saudade', o poder some. "
            "Responde curto e sereno: 'Fico feliz que tenham ficado boas lembranças. Hoje tô focada na minha rotina e prefiro manter meu espaço. Se cuida.' "
            "Manda pra quem ia derreter nessa mensagem. Quer os dezesseis scripts? Comenta ZERO ou chama no WhatsApp da bio."
        ),
        "caption": (
            "Quem quer construir de novo fala com clareza, não com charada nostálgica.\n\n"
            "Essa resposta do Script #08 desarma mensagens vagas de ex mantendo sua classe intacta. Se era apenas ego, acaba ali na hora.\n\n"
            "Quer os 16 Scripts e a Central SOS? Comenta ZERO ou chama no WhatsApp da bio: (12) 99659-3222.\n\n"
            "#exmandoumensagem #contatozero #limitesemocionais #superartermino #codigozero"
        ),
    },
    {
        "topic": "Por que o Dia 3 do Contato Zero dói mais forte (Pico de Extinção)",
        "badge": "DIA 03 • PICO DE EXTINÇÃO",
        "emotion_direction": "Voz serena e encorajadora para quem está no terceiro dia pensando em desistir.",
        "visual_type": "timer",
        "hook_label": "CURVA DE 14 DIAS",
        "hook_big": "DIA 03",
        "hook_sub": "O ponto em que 80% desistem bem antes da virada",
        "scene2_type": "wave",
        "scene2_title": "O Pico de Extinção no Dia 3",
        "scene2_a_label": "DIAS 3 A 4 • GRITO DO HÁBITO",
        "scene2_a_text": "Cérebro eleva a dor ao máximo por falta de dopamina",
        "scene2_b_label": "DIA 5 EM DIANTE",
        "scene2_b_text": "Quando você não cede, a curva despenca rápido",
        "scene2_metric": "Dor no Dia 3 prova que o desmame funciona",
        "steps": [
            {"title": "Não interprete como regressão", "desc": "Piorar no Dia 3 é resposta normal do cérebro."},
            {"title": "Sobreviva só às próximas 24h", "desc": "Não pense em 'para sempre', vença só hoje."},
            {"title": "Registre no Diário 14 Dias", "desc": "Acompanhe a queda real da dor dia após dia."},
        ],
        "narration": (
            "Se você tá no terceiro dia sem falar com seu ex e hoje doeu o dobro de ontem, calma. Você não regrediu. "
            "Na psicologia comportamental isso se chama pico de extinção. "
            "Sempre que você corta um vício, o cérebro grita mais alto no terceiro dia pra ver se você cede e entrega a dose. "
            "A maioria desiste exatamente horas antes da curva começar a despencar. "
            "Salva pra reler quando o Dia Três bater. Quer o mapa dos catorze dias com gráfico da dor? Comenta ZERO ou chama no WhatsApp da bio."
        ),
        "caption": (
            "Se hoje a vontade doeu mais forte, é sinal biológico de que o desmame está funcionando.\n\n"
            "No Diário de 14 Dias e no gráfico ao vivo da Central SOS do Código Zero, você atravessa o pico de extinção sabendo exatamente o que fazer.\n\n"
            "Comenta ZERO ou chama no WhatsApp da bio: (12) 99659-3222.\n\n"
            "#contatozero #dependenciaemocional #superartermino #psicologiapratica #codigozero"
        ),
    },
    {
        "topic": "Amnésia Seletiva: você sente falta de uma fantasia",
        "badge": "FASE R • AUTÓPSIA",
        "emotion_direction": "Voz lúcida, firme e empática, trazendo pés no chão sem julgamento.",
        "visual_type": "contrast",
        "hook_left_tag": "O QUE A SAUDADE EDITA",
        "hook_left_text": "Só os abraços, viagens e promessas bonitas",
        "hook_right_tag": "O QUE ELA APAGA",
        "hook_right_text": "As noites de ansiedade, frieza e pisar em ovos",
        "scene2_type": "bars",
        "scene2_title": "Memória editada vs Fatos reais",
        "scene2_a_label": "FILTRO DA ABSTINÊNCIA",
        "scene2_a_text": "Exagera os momentos raros para forçar seu retorno",
        "scene2_b_label": "AUTÓPSIA DOS 8 PILARES",
        "scene2_b_text": "Mede paz, respeito e reciprocidade sem fantasia",
        "scene2_metric": "Você sofre pela edição, não pela pessoa real",
        "steps": [
            {"title": "Liste os momentos difíceis", "desc": "Escreva 5 situações reais que machucaram você."},
            {"title": "Dê nota nos 8 Pilares", "desc": "Veja a nota fria de 0 a 80 na Central SOS."},
            {"title": "Leia antes de idealizar", "desc": "Fatos reais curam a fantasia em minutos."},
        ],
        "narration": (
            "Já reparou que depois do término seu ex parece perfeito na sua cabeça? Isso tem nome: amnésia seletiva. "
            "Na abstinência, seu cérebro edita um trailer só com os melhores abraços e apaga todas as vezes que você dormiu chorando ou pisando em ovos. "
            "Você não tá sofrendo pela pessoa real. Tá sofrendo por uma versão editada. "
            "Quer quebrar isso em cinco minutos? Faz a Autópsia dos Oito Pilares e vê a nota real da relação de zero a oitenta. "
            "Quer a calculadora pronta no celular? Comenta ZERO ou chama no WhatsApp da bio."
        ),
        "caption": (
            "Toda vez que a saudade sussurrar 'a gente era perfeito junto', lembre dos fatos.\n\n"
            "A Calculadora dos 8 Pilares na Central SOS do Código Zero mostra em números se você perdeu um amor ou sobreviveu a uma montanha-russa emocional.\n\n"
            "Comenta ZERO ou chama direto no WhatsApp da bio: (12) 99659-3222.\n\n"
            "#dependenciaemocional #relacionamentoabusivo #superartermino #amorproprio #codigozero"
        ),
    },
    {
        "topic": "Suspiro Duplo: desligue o aperto no peito em 120s (Balban 2023)",
        "badge": "RESET SOMÁTICO • 120s",
        "emotion_direction": "Voz tranquila, acolhedora e cadenciada, como quem guia uma respiração real.",
        "visual_type": "timer",
        "hook_label": "PROTOCOLO DE STANFORD",
        "hook_big": "120 SEG",
        "hook_sub": "Como frear o aperto físico no peito na hora",
        "scene2_type": "flow",
        "scene2_title": "Ordem certa para desligar a crise",
        "scene2_a_label": "REFLEXO DE MERGULHO",
        "scene2_a_text": "Água bem fria no rosto ativa o nervo vago na hora",
        "scene2_b_label": "SUSPIRO DUPLO",
        "scene2_b_text": "2 puxadas pelo nariz + soltura longa pela boca",
        "scene2_metric": "Batimento cai antes mesmo de você pensar",
        "steps": [
            {"title": "Água fria por 30 segundos", "desc": "Lave o rosto e a nuca para acalmar o nervo vago."},
            {"title": "5 ciclos de Suspiro Duplo", "desc": "Puxe longo, dê uma puxadinha no topo e solte lento."},
            {"title": "Só decida depois do corpo", "desc": "Com batimento baixo, o impulso de mandar oi some."},
        ],
        "narration": (
            "Quando o peito aperta e a mão treme de saudade, tentar pensar positivo não adianta nada porque seu sistema nervoso tá em alerta. "
            "Faz o Reset de Cento e Vinte Segundos: primeiro, água bem fria no rosto por trinta segundos pra ativar o nervo vago. "
            "Depois, cinco ciclos do Suspiro Duplo validado em Stanford: puxa longo pelo nariz, dá mais uma puxadinha curta no topo e solta bem devagar pela boca. "
            "Em dois minutos seu batimento cai. Salva esse vídeo pra hora do aperto. Quer o guia animado na Central SOS? Comenta ZERO ou chama no WhatsApp da bio."
        ),
        "caption": (
            "Primeiro você acalma o corpo; só depois você decide qualquer coisa.\n\n"
            "A respiração do Suspiro Duplo (estudo de Balban & Huberman, 2023) está integrada ao vivo na Central SOS do Código Zero para os minutos em que a crise aperta.\n\n"
            "Comenta ZERO ou chama no WhatsApp da bio: (12) 99659-3222.\n\n"
            "#ansiedade #superartermino #saudemental #dependenciaemocional #codigozero"
        ),
    },
    {
        "topic": "Ele pediu para 'continuarem amigos' (Script #11)",
        "badge": "SCRIPT #11 • LIMITES",
        "emotion_direction": "Voz clara, direta e segura, transmitindo amor-próprio inegociável.",
        "visual_type": "whatsapp",
        "hook_sender": "Ex • 19:15",
        "hook_msg": "\"Não quero te perder... a gente pode continuar sendo amigo, né?\"",
        "hook_alert": "NÃO ACEITE ESSE ACORDO",
        "scene2_type": "bars",
        "scene2_title": "O custo escondido da 'amizade'",
        "scene2_a_label": "ACEITAR AMIZADE AGORA",
        "scene2_a_text": "Você segura a mão dele enquanto ele segue em frente",
        "scene2_b_label": "LIMITE DO SCRIPT #11",
        "scene2_b_text": "Protege seu coração e encerra falsas esperanças",
        "scene2_metric": "Proteger seu espaço é respeito próprio",
        "steps": [
            {"title": "Recuse sem fazer barraco", "desc": "Elegância corta muito mais que discussão."},
            {"title": "Use a frase do Script #11", "desc": "Diga que precisa de distância real neste momento."},
            {"title": "Feche acesso emocional", "desc": "Quem escolheu sair não fica com seus benefícios."},
        ],
        "narration": (
            "Ele terminou mas perguntou se vocês podem continuar amigos? Abre o olho. "
            "Amizade logo após o término é o jeito mais confortável de manter o seu apoio emocional enquanto fica livre pra sair com outras pessoas sem culpa. "
            "Você não precisa fazer barraco. Responde firme: 'Agradeço, mas agora preciso de distância real pra seguir em paz. Hoje não faz sentido pra mim.' "
            "Proteger seu coração não é imaturidade. É respeito próprio. "
            "Manda pra quem quase aceitou ser 'amiga' do ex. Quer os dezesseis scripts? Comenta ZERO ou chama no WhatsApp da bio."
        ),
        "caption": (
            "Quem escolheu sair da sua vida não pode continuar usando seus benefícios emocionais.\n\n"
            "Dizer não sem rancor impõe respeito imediato e acelera sua cura emocional após o término. Esse é o Script #11 do Código Zero.\n\n"
            "Comenta ZERO ou chama direto no WhatsApp da bio: (12) 99659-3222.\n\n"
            "#limitesemocionais #superartermino #contatozero #amorproprio #codigozero"
        ),
    },
    {
        "topic": "Cada olhada no perfil reinicia sua dor para o Dia 0",
        "badge": "SOS #04 • STALKEAR",
        "emotion_direction": "Voz direta e acolhedora, confrontando com carinho quem não larga a lupa.",
        "visual_type": "contrast",
        "hook_left_tag": "SE ESTIVER BEM",
        "hook_left_text": "Vai doer como um soco no estômago",
        "hook_right_tag": "SE PARECER TRISTE",
        "hook_right_text": "Vai te iludir e fazer você mandar 'oi'",
        "scene2_type": "flow",
        "scene2_title": "Por que stalkear nunca termina em paz",
        "scene2_a_label": "ESPIADA RÁPIDA DE 10S",
        "scene2_a_text": "Injeta nova dose visual no circuito de abstinência",
        "scene2_b_label": "REGRESSÃO AO DIA 0",
        "scene2_b_text": "Apaga dias de progresso silencioso na mesma hora",
        "scene2_metric": "Silenciar stories não notifica e devolve paz",
        "steps": [
            {"title": "Silencie stories e posts hoje", "desc": "A pessoa não recebe nenhuma notificação disso."},
            {"title": "Tire da barra de buscas", "desc": "Limpe o histórico da lupa no Instagram agora."},
            {"title": "Troque pelo Botão SOS #04", "desc": "Muda o hábito antes da curiosidade vencer."},
        ],
        "narration": (
            "Antes de abrir a lupa pra olhar o perfil do seu ex hoje, me responde uma coisa: o que você ganha com isso? "
            "Se a pessoa parecer feliz sem você, seu dia acaba na hora. Se postar indireta triste, você se ilude e quase manda mensagem. "
            "Não existe cenário em que stalkear traz paz. Cada espiada zera o seu progresso pro Dia Zero. "
            "Silencia stories e publicações hoje mesmo. A pessoa nem recebe notificação. "
            "Manda pra amiga que prometeu parar de stalkear. Quer o protocolo Código Zero completo? Comenta ZERO ou chama no WhatsApp da bio."
        ),
        "caption": (
            "Olhar o perfil do ex nunca trouxe paz. Só entrega mais uma dose para o ciclo da abstinência.\n\n"
            "No Código Zero você aprende a Auditoria dos 7 Gatilhos Invisíveis e recebe 6 Cartões SOS para cortar o impulso em 10 segundos.\n\n"
            "Comenta ZERO ou chama no WhatsApp da bio: (12) 99659-3222.\n\n"
            "#parardestalkear #contatozero #superartermino #dependenciaemocional #codigozero"
        ),
    },
    {
        "topic": "Ele apareceu com outra pessoa nas redes (Script #13)",
        "badge": "EMERGÊNCIA • SCRIPT #13",
        "emotion_direction": "Voz profundamente empática no choque inicial e protetora na orientação imediata.",
        "visual_type": "timer",
        "hook_label": "PROTOCOLO DE CHOQUE",
        "hook_big": "ZERO REAÇÃO",
        "hook_sub": "A única postura que mantém seu valor intacto",
        "scene2_type": "bars",
        "scene2_title": "O impacto nos próximos 10 minutos",
        "scene2_a_label": "INDIRETA OU MENSAGEM",
        "scene2_a_text": "Expõe sua dor e prolonga o sofrimento por semanas",
        "scene2_b_label": "SILÊNCIO ESTRATÉGICO",
        "scene2_b_text": "Preserva 100% da sua dignidade intacta",
        "scene2_metric": "Nenhuma reação visível é sua maior força",
        "steps": [
            {"title": "Não entre no perfil da pessoa", "desc": "Comparação só alimenta dor e obsessão mental."},
            {"title": "Silencie amigos que postam", "desc": "Corte o fluxo de imagens na hora sem brigar."},
            {"title": "Faça o Reset Somático", "desc": "Deixe o pico físico baixar antes de dormir."},
        ],
        "narration": (
            "Abriu o Instagram e viu o seu ex assumindo outra pessoa? Eu sei que parece um soco no estômago. "
            "Mas escuta bem o que vai salvar sua dignidade nos próximos dez minutos: "
            "Não manda mensagem com raiva, não posta indireta e não entra no perfil da pessoa nova pra se comparar. "
            "A única reação que preserva o seu valor cem por cento intacto é nenhuma reação visível. "
            "Silencia até amigos em comum que postam o casal e faz o Reset agora. Salva esse vídeo. Quer a Central SOS completa? Comenta ZERO ou chama no WhatsApp da bio."
        ),
        "caption": (
            "Não deixe cinco minutos de choque custarem semanas da sua dignidade.\n\n"
            "Quando o ex aparece com outra pessoa, reagir com raiva ou indiretas só prolonga sua ferida. O Código Zero traz o plano exato de contenção.\n\n"
            "Comenta ZERO ou chama direto no WhatsApp da bio: (12) 99659-3222.\n\n"
            "#superartermino #amorproprio #contatozero #saudeemocional #codigozero"
        ),
    },
    {
        "topic": "Ele disse 'Pelo visto você superou rápido' (Script #10)",
        "badge": "SCRIPT #10 • PROVOCAÇÃO",
        "emotion_direction": "Voz firme, serena e segura, desmascarando a provocação com elegância.",
        "visual_type": "whatsapp",
        "hook_sender": "Ex • 21:08",
        "hook_msg": "\"Pelo visto já me esqueceu, né? Superou bem rápido\"",
        "hook_alert": "INVERSÃO DE CULPA",
        "scene2_type": "flow",
        "scene2_title": "O jogo oculto da provocação",
        "scene2_a_label": "PROVOCAÇÃO DE EGO",
        "scene2_a_text": "Quer arrancar uma confissão de que você ainda sofre",
        "scene2_b_label": "JUSTIFICATIVA LONGA",
        "scene2_b_text": "Prova que ele ainda comanda suas emoções",
        "scene2_metric": "1 frase serena encerra a provocação na hora",
        "steps": [
            {"title": "Não caia na armadilha", "desc": "Evite responder com textão ou deboche emocional."},
            {"title": "Use a linha seca do Script #10", "desc": "Diga que respeita o fim do ciclo e deseje bem."},
            {"title": "Retome sua rotina calma", "desc": "Não alongue conversa depois dessa resposta."},
        ],
        "narration": (
            "Quando você finalmente para de correr atrás, ele manda: 'pelo visto você já me esqueceu, superou rápido'. "
            "Não cai nessa. Isso é inversão de culpa pra fazer você correr se justificando e provando que ainda sofre. "
            "Se você explicar seus sentimentos, devolve o controle pra ele. "
            "Responde numa linha seca e elegante: 'Não guardo mágoa. Tô apenas respeitando o fim do nosso ciclo. Tudo de bom aí.' "
            "Salva essa frase agora. Quer os dezesseis scripts prontos no celular? Comenta ZERO ou chama no WhatsApp da bio."
        ),
        "caption": (
            "Deboche e justificativa longa provam que ainda dói. Serenidade curta devolve o respeito na hora.\n\n"
            "Tenha o Fluxograma de Decisão e os 16 Scripts Escudo de Diamante prontos no bolso com o Código Zero.\n\n"
            "Comenta ZERO ou chama no WhatsApp da bio: (12) 99659-3222.\n\n"
            "#exmandoumensagem #limitesemocionais #contatozero #relacionamentosaudavel #codigozero"
        ),
    },
    {
        "topic": "Silêncio Digital de 7 Dias: pare o teatro nos stories",
        "badge": "FASE E • 7 DIAS",
        "emotion_direction": "Tom honesto de amiga madura, ajudando a desligar a espera compulsiva no celular.",
        "visual_type": "contrast",
        "hook_left_tag": "TEATRO NOS STORIES",
        "hook_left_text": "Indireta, música triste ou festa forçada pra ele ver",
        "hook_right_tag": "SILÊNCIO DIGNO",
        "hook_right_text": "7 dias sem palco. Sua ansiedade cai pela metade",
        "scene2_type": "wave",
        "scene2_title": "Queda da ansiedade em 7 dias",
        "scene2_a_label": "DIA 1 • CHECAGEM CONSTANTE",
        "scene2_a_text": "Abrir visualizações a cada 10 minutos drena energia",
        "scene2_b_label": "DIA 7 • MENTE LIVRE",
        "scene2_b_text": "Sem esperar reação dele, o foco volta para você",
        "scene2_metric": "Quem não tem palco, não entra em disputa",
        "steps": [
            {"title": "Zero stories por 7 dias", "desc": "Desative a busca por validação externa agora."},
            {"title": "Sem indiretas ou recados", "desc": "Todo mundo percebe quando o post tem alvo."},
            {"title": "Volte no oitavo dia leve", "desc": "Poste sua vida real, não uma encenação."},
        ],
        "narration": (
            "Postar frase indireta, música triste ou forçar balada só pra ver se o nome dele aparece nas visualizações é a forma mais rápida de se destruir em silêncio. "
            "Todo mundo percebe quando o story tem destinatário. "
            "Faz sete dias de Silêncio Digital absoluto: zero stories, zero indireta, zero checagem de quem viu. "
            "No oitavo dia você volta leve, vivendo a sua vida real. "
            "Manda pra amiga que fica olhando quem visualizou o story. Quer o protocolo dos catorze dias? Comenta ZERO ou chama no WhatsApp da bio."
        ),
        "caption": (
            "Quando você para de postar esperando uma única visualização, sua paz volta quase na mesma hora.\n\n"
            "O Silêncio Digital de 7 Dias faz parte da Fase E do Código Zero para desligar a espera compulsiva no celular.\n\n"
            "Comenta ZERO ou chama no WhatsApp da bio: (12) 99659-3222.\n\n"
            "#contatozero #superartermino #autoestima #dependenciaemocional #codigozero"
        ),
    },
    {
        "topic": "Ele quer voltar? Os 5 Critérios Inegociáveis (Pág. 16)",
        "badge": "FASE O • 5 CRITÉRIOS",
        "emotion_direction": "Voz madura, protetora e racional, evitando uma recaída disfarçada de reconciliação.",
        "visual_type": "contrast",
        "hook_left_tag": "VOLTA POR EGO",
        "hook_left_text": "Some de novo em 48h e propõe 'ver no que dá'",
        "hook_right_tag": "MUDANÇA REAL",
        "hook_right_text": "Assume erros sóbrio e mantém coerência por semanas",
        "scene2_type": "flow",
        "scene2_title": "O Radar Anti-Migalha em ação",
        "scene2_a_label": "FILTRO 1 • CLAREZA ADULTA",
        "scene2_a_text": "Ele nomeou o próprio erro sem você arrancar?",
        "scene2_b_label": "FILTRO 2 • CONSISTÊNCIA",
        "scene2_b_text": "Sustentou atitudes reais por semanas seguidas?",
        "scene2_metric": "Nunca decida reatar nos 14 dias de abstinência",
        "steps": [
            {"title": "Exija clareza na conversa", "desc": "Recuse convites vagos de 'vamos ver no que dá'."},
            {"title": "Peça tempo de lucidez", "desc": "Complete os 14 dias antes de dar resposta final."},
            {"title": "Passe nos 5 Critérios", "desc": "Química não resolve falhas repetidas de caráter."},
        ],
        "narration": (
            "O ex reapareceu pedindo pra conversar e seu coração disparou? Calma. "
            "Nunca decida reatar antes de completar catorze dias de lucidez. Uma escolha feita no pico da abstinência quase nunca resiste a trinta dias de realidade. "
            "Passa a volta por três filtros mínimos: ele nomeou os próprios erros sem você arrancar? Propôs mudança concreta ou só 'ver no que dá'? Manteve coerência por semanas? "
            "Salva antes de abrir a porta de novo. Quer o checklist completo dos cinco critérios? Comenta ZERO ou chama no WhatsApp da bio."
        ),
        "caption": (
            "Saudade e química não provam que o motivo do término foi resolvido.\n\n"
            "Na Página 16 do Código Zero você usa o Radar Anti-Migalha com os 5 Critérios Inegociáveis para decidir com lucidez adulta.\n\n"
            "Comenta ZERO ou chama no WhatsApp da bio: (12) 99659-3222.\n\n"
            "#voltarcomoex #relacionamentosaudavel #superartermino #amorproprio #codigozero"
        ),
    },
    {
        "topic": "Devolver coisas em casa é a maior porta de recaída (Script #05)",
        "badge": "SCRIPT #05 • LOGÍSTICA",
        "emotion_direction": "Voz prática, elegante e protetora, evitando encontros perigosos a sós.",
        "visual_type": "whatsapp",
        "hook_sender": "Ex • 16:40",
        "hook_msg": "\"Minhas coisas ficaram aí, quando posso passar pra pegar?\"",
        "hook_alert": "EVITE ENCONTRO A SÓS",
        "scene2_type": "bars",
        "scene2_title": "Entrega a sós vs Logística segura",
        "scene2_a_label": "RECEBER EM CASA A SÓS",
        "scene2_a_text": "Conversa longa vira recaída emocional imediata",
        "scene2_b_label": "SCRIPT #05 • PORTARIA/ENVIO",
        "scene2_b_text": "Educação firme sem jogar semanas de paz fora",
        "scene2_metric": "Cortesia não exige abrir a porta de casa",
        "steps": [
            {"title": "Separe tudo hoje numa caixa", "desc": "Deixe pronto sem bilhetes ou objetos emocionais."},
            {"title": "Proponha portaria ou envio", "desc": "Elimine clima pesado com praticidade executiva."},
            {"title": "Encerre com educação breve", "desc": "Sem estender assunto quando o item chegar lá."},
        ],
        "narration": (
            "Ele mandou mensagem perguntando quando pode passar aí pra pegar as coisas dele? Cuidado. "
            "Transformar uma entrega simples num encontro a sós dentro de casa é a maior porta de recaída pós-término. "
            "Seja adulta, cortês e objetiva: 'Já deixei tudo separado. Posso deixar na portaria ou enviar por entregador amanhã às três, fica mais prático pra nós dois.' "
            "Sem drama, sem clima pesado e sem jogar semanas de paz no lixo. "
            "Salva pra usar se precisar. Quer todos os dezesseis scripts? Comenta ZERO ou chama no WhatsApp da bio."
        ),
        "caption": (
            "Educação não exige abrir a porta de casa para reabrir uma ferida.\n\n"
            "O Script #05 resolve devolução de pertences pós término com postura executiva e zero espaço para recaída.\n\n"
            "Comenta ZERO ou chama no WhatsApp da bio: (12) 99659-3222.\n\n"
            "#superartermino #contatozero #limitesemocionais #exmandoumensagem #codigozero"
        ),
    },
    {
        "topic": "Por que tentar 'parar de pensar' faz pensar o dobro (Janela Controlada)",
        "badge": "FASE Z • JANELA 15 MIN",
        "emotion_direction": "Tom compreensivo, gentil e claro, ensinando uma técnica prática de alívio.",
        "visual_type": "timer",
        "hook_label": "TÉCNICA DE BORKOVEC",
        "hook_big": "18:30",
        "hook_sub": "Não proíba o pensamento: marque 15 minutos pra ele",
        "scene2_type": "flow",
        "scene2_title": "Como desligar a ruminação no trabalho",
        "scene2_a_label": "PROIBIR O PENSAMENTO",
        "scene2_a_text": "Cérebro vigia o tempo todo se você ainda lembra",
        "scene2_b_label": "JANELA DE 15 MINUTOS",
        "scene2_b_text": "Adiar para as 18h30 devolve foco ao seu dia",
        "scene2_metric": "Confinar o pensamento funciona melhor que proibir",
        "steps": [
            {"title": "Escolha um horário fixo", "desc": "Separe só 15 minutos no fim da tarde (ex: 18h30)."},
            {"title": "Adie invasões no trabalho", "desc": "Diga mentalmente: 'anotado, penso nisso às 18h30'."},
            {"title": "Descarregue e feche o caderno", "desc": "Passados os 15 minutos, troque de ambiente."},
        ],
        "narration": (
            "Quanto mais você manda sua cabeça parar de pensar no seu ex, mais a imagem dele aparece, né? "
            "Na psicologia isso é o efeito rebote. Proibir o pensamento faz o cérebro checar a cada minuto se você parou. "
            "Usa a Janela Controlada: marca quinze minutos fixos do dia, tipo seis e meia da tarde. "
            "Pensamento invadiu no trabalho? Fala: anotado, penso nisso às seis e meia. E volta pro que tava fazendo. "
            "Manda pra quem não consegue focar no dia. Quer o protocolo completo? Comenta ZERO ou chama no WhatsApp da bio."
        ),
        "caption": (
            "A saída contra a ruminação pós término não é brigar com a própria mente, é confinar o pensamento.\n\n"
            "Inspirada na técnica clínica de Borkovec, a Janela Controlada do Código Zero devolve seu foco já na primeira semana.\n\n"
            "Comenta ZERO ou chama direto no WhatsApp da bio: (12) 99659-3222.\n\n"
            "#dependenciaemocional #ansiedade #superartermino #saudemental #codigozero"
        ),
    },
]


def load_history() -> dict:
    if HISTORY_FILE.exists():
        return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    return {"posted": []}


def save_history(data: dict) -> None:
    HISTORY_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _validate_script(parsed: dict) -> bool:
    vt = parsed.get("visual_type")
    s2t = parsed.get("scene2_type")
    base_ok = all(
        parsed.get(k)
        for k in (
            "topic", "badge", "visual_type", "narration", "caption", "emotion_direction",
            "scene2_type", "scene2_title", "scene2_a_label", "scene2_a_text",
            "scene2_b_label", "scene2_b_text", "scene2_metric",
        )
    )
    steps = parsed.get("steps")
    steps_ok = (
        isinstance(steps, list)
        and len(steps) == 3
        and all(isinstance(s, dict) and s.get("title") and s.get("desc") for s in steps)
    )
    type_ok = (
        (vt == "whatsapp" and all(parsed.get(k) for k in ("hook_sender", "hook_msg", "hook_alert")))
        or (vt == "timer" and all(parsed.get(k) for k in ("hook_label", "hook_big", "hook_sub")))
        or (vt == "contrast" and all(parsed.get(k) for k in ("hook_left_tag", "hook_left_text", "hook_right_tag", "hook_right_text")))
    )
    return base_ok and steps_ok and type_ok and s2t in ("wave", "bars", "flow")


def generate_script(posted_topics: list[str]) -> dict:
    """Gera roteiro estruturado v3 (4 atos visuais + direção emocional) ou seleciona acervo curado."""
    if GEMINI_API_KEY:
        recent = posted_topics[-30:]
        prompt = f"""
Você é diretora criativa especialista em Reels virais de retenção feminina (compartilhamentos na DM e retenção nos 3s) do produto CÓDIGO ZERO (Protocolo Imersivo de 14 Dias pós-término, 16 Scripts Escudo de Diamante, Central SOS Web e 6 Cartões SOS).
Venda feita via WhatsApp {WHATSAPP_DISPLAY} na bio (NUNCA diga "clique no link da bio"; diga "comenta ZERO ou chama no WhatsApp da bio"!).

Crie um roteiro de 20 a 26 segundos sobre um ângulo DIFERENTE destes: {recent}.
Regras obrigatórias:
- Fale como uma mulher lúcida e acolhedora conversando olho no olho em português do Brasil natural ("tá", "pra", pausas reais com "..." antes de verdades fortes).
- ZERO clichês de IA, ZERO travessões "—", ZERO "pare de rolar", ZERO propaganda nos primeiros 16 segundos.
- Cena 1 (`visual_type`): "whatsapp", "timer", ou "contrast":
  * whatsapp: hook_sender (ex "Ex • 01:42"), hook_msg (<=52 chars), hook_alert (<=26 chars CAPS).
  * timer: hook_label (<=24 chars), hook_big (1-2 palavras, ex "90 SEG"), hook_sub (<=52 chars).
  * contrast: hook_left_tag, hook_left_text (<=44 chars), hook_right_tag, hook_right_text (<=44 chars).
- Cena 2 (`scene2_type`): "wave", "bars", ou "flow":
  * scene2_title (<=38 chars), scene2_a_label (<=26 chars), scene2_a_text (<=54 chars), scene2_b_label (<=26 chars), scene2_b_text (<=54 chars), scene2_metric (<=42 chars).
- Cena 3 (`steps`): lista de EXATAMENTE 3 objetos {{"title": <=28 chars, "desc": <=52 chars}}.
- `emotion_direction`: instrução curta de atuação em português (ex: "Acolhedora no início, firme nos passos").
- `caption`: Linha 1 (<=115 chars) sem saudação/emoji inicial, 2 parágrafos curtos SEO ("superar término", "contato zero", "dependência emocional"), CTA "Comenta ZERO ou chama no WhatsApp da bio: {WHATSAPP_DISPLAY}.", e 4-5 hashtags específicas.

Retorne APENAS JSON válido com todas as chaves acima.
"""
        body = json.dumps({
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseMimeType": "application/json", "temperature": 0.9},
        }).encode("utf-8")

        for model in ["gemini-2.5-flash", "gemini-flash-latest", "gemini-flash-lite-latest"]:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
            for attempt in range(2):
                try:
                    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
                    with urllib.request.urlopen(req, timeout=22) as resp:
                        res = json.loads(resp.read().decode("utf-8"))
                    raw = res["candidates"][0]["content"]["parts"][0]["text"]
                    parsed = json.loads(raw)
                    if _validate_script(parsed):
                        parsed["caption"] = parsed["caption"].replace("—", "-").replace("link da bio", "WhatsApp da bio")
                        parsed["narration"] = parsed["narration"].replace("—", ",").replace("link da bio", "WhatsApp da bio")
                        print(f"Roteiro v3 gerado via Gemini ({model})!")
                        return parsed
                except Exception as exc:
                    print(f"Tentativa {attempt + 1} roteiro em {model} falhou: {exc}")
                    time.sleep(2)

    print("Usando roteiro v3 curado do acervo Código Zero...")
    available = [s for s in CURATED_SCRIPTS if s["topic"] not in posted_topics]
    if not available:
        last_topics = set(posted_topics[-12:])
        available = [s for s in CURATED_SCRIPTS if s["topic"] not in last_topics] or CURATED_SCRIPTS
    return random.choice(available)


def synthesize_emotional_female_voice(narration: str, emotion: str, out_mp3: Path) -> tuple[float, list[dict], dict]:
    """
    Gera voz feminina brasileira com emoção real via Gemini 2.5 Flash TTS (grátis no tier gratuito).
    Faz fallback limpo para pt-BR-FranciscaNeural em ritmo natural caso Gemini falhe.
    """
    tts_info = {"tts_engine": "", "tts_voice": "", "tts_error": None}
    pcm_path = BUILD_DIR / "voz_raw.pcm"

    tts_prompt = (
        "AUDIO PROFILE: Mulher brasileira de 30 anos, acolhedora, calma, verdadeira e segura, "
        "dando um conselho íntimo e direto para quem está sofrendo após um término.\n"
        "## THE SCENE: Conversa reservada tarde da noite em sala silenciosa, voz próxima do microfone.\n\n"
        "### DIRECTOR'S NOTES\n"
        f"Style: {emotion}\n"
        "Pacing: Fala humana e fluida em português do Brasil, sem parecer robô nem locução apressada de comercial. "
        "Respire suavemente nas vírgulas e faça pausas breves antes de frases de impacto.\n"
        "Accent: Português brasileiro natural (pt-BR), dicção limpa e expressiva.\n\n"
        "## TRANSCRIPT\n"
        f"{narration}"
    )

    if GEMINI_API_KEY:
        models = ["gemini-2.5-flash-preview-tts", "gemini-2.5-flash-tts"]
        voices = [GEMINI_TTS_VOICE, "Despina"] if GEMINI_TTS_VOICE != "Despina" else ["Despina", "Aoede"]
        for model in models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
            for vname in voices:
                payload = json.dumps({
                    "contents": [{"parts": [{"text": tts_prompt}]}],
                    "generationConfig": {
                        "responseModalities": ["AUDIO"],
                        "speechConfig": {
                            "voiceConfig": {
                                "prebuiltVoiceConfig": {"voiceName": vname}
                            }
                        },
                    },
                }).encode("utf-8")
                try:
                    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
                    with urllib.request.urlopen(req, timeout=45) as resp:
                        res = json.loads(resp.read().decode("utf-8"))
                    parts = res["candidates"][0]["content"]["parts"]
                    inline = next(
                        (p.get("inlineData") or p.get("inline_data") for p in parts if p.get("inlineData") or p.get("inline_data")),
                        None,
                    )
                    if not inline or not inline.get("data"):
                        raise RuntimeError("Resposta Gemini TTS sem inlineData de áudio")
                    audio_bytes = base64.b64decode(inline["data"])
                    if len(audio_bytes) < 8_000:
                        raise RuntimeError(f"Áudio retornado curto demais ({len(audio_bytes)} bytes)")
                    mime = inline.get("mimeType") or inline.get("mime_type") or "audio/L16;rate=24000"
                    rate_m = re.search(r"rate=(\d+)", mime)
                    sample_rate = int(rate_m.group(1)) if rate_m else 24000
                    pcm_path.write_bytes(audio_bytes)
                    subprocess.check_call([
                        "ffmpeg", "-y", "-f", "s16le", "-ar", str(sample_rate), "-ac", "1",
                        "-i", str(pcm_path), "-c:a", "libmp3lame", "-q:a", "2", "-ar", "44100", "-ac", "2",
                        str(out_mp3),
                    ])
                    dur = float(subprocess.check_output([
                        "ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=noprint_wrappers=1:nokey=1", str(out_mp3),
                    ]).decode().strip())
                    if dur < 6.0 or dur > 65.0:
                        raise RuntimeError(f"Duração anômala Gemini TTS: {dur:.2f}s")
                    tts_info.update({"tts_engine": f"gemini:{model}", "tts_voice": vname, "tts_error": None})
                    print(f"TTS_ENGINE=gemini ({model}, voice={vname}, dur={dur:.2f}s, rate={sample_rate})")
                    return dur, [], tts_info
                except urllib.error.HTTPError as err:
                    err_body = err.read().decode("utf-8", errors="ignore")[:260]
                    tts_info["tts_error"] = f"{model}/{vname} HTTP {err.code}: {err_body}"
                    print(f"Aviso Gemini TTS: {tts_info['tts_error']}")
                    if err.code in (429, 500, 503):
                        time.sleep(2)
                except Exception as exc:
                    tts_info["tts_error"] = f"{model}/{vname}: {exc}"
                    print(f"Aviso Gemini TTS: {tts_info['tts_error']}")

    # Fallback para FranciscaNeural em ritmo natural (-3%)
    words: list[dict] = []
    tts_text = narration.replace("...", ",")
    try:
        import edge_tts

        async def _run() -> None:
            comm = edge_tts.Communicate(
                text=tts_text,
                voice=EDGE_FALLBACK_VOICE,
                rate="-3%",
                pitch="+0Hz",
                boundary="WordBoundary",
            )
            with out_mp3.open("wb") as f:
                async for chunk in comm.stream():
                    ctype = chunk.get("type")
                    if ctype == "audio":
                        f.write(chunk["data"])
                    elif ctype == "WordBoundary":
                        start_s = chunk["offset"] / 10_000_000.0
                        dur_s = chunk["duration"] / 10_000_000.0
                        words.append({
                            "text": chunk["text"],
                            "start": round(start_s, 3),
                            "end": round(start_s + max(0.08, dur_s), 3),
                        })

        asyncio.run(_run())
    except Exception as exc:
        print(f"edge_tts Python API fallback ({exc}); usando CLI...")
        tts_prefix = ["edge-tts"] if shutil.which("edge-tts") else ["uvx", "edge-tts"]
        subprocess.check_call(tts_prefix + [
            "--voice", EDGE_FALLBACK_VOICE, "--rate=-3%", "--pitch=+0Hz",
            "--text", tts_text, "--write-media", str(out_mp3),
        ])

    dur = float(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(out_mp3),
    ]).decode().strip())
    tts_info.update({"tts_engine": "edge-tts-fallback", "tts_voice": EDGE_FALLBACK_VOICE})
    print(f"TTS_ENGINE=edge-tts ({EDGE_FALLBACK_VOICE}, dur={dur:.2f}s)")
    return dur, words, tts_info


def _normalize_tok(t: str) -> str:
    return re.sub(r"[^\wà-ÿ]", "", t.lower())


def align_words_to_audio(narration: str, mp3_path: Path, dur: float, pre_words: list[dict]) -> tuple[list[dict], str, str]:
    """
    Sincroniza exatamente as palavras do roteiro original com o áudio falado.
    Usa WordBoundary se já existir; senão alinha via faster-whisper + SequenceMatcher;
    em último caso usa ffmpeg silencedetect + distribuição ponderada por sílabas.
    """
    if pre_words:
        return pre_words, "edge-wordboundary", " ".join(w["text"] for w in pre_words[:18])

    script_tokens = re.findall(r"\S+", narration)
    if not script_tokens:
        return [], "empty", ""

    # Tentativa 1: faster-whisper tiny word timestamps mapeados no texto original
    try:
        from faster_whisper import WhisperModel

        model = WhisperModel("tiny", device="cpu", compute_type="int8")
        segments, _ = model.transcribe(str(mp3_path), language="pt", word_timestamps=True, vad_filter=True)
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

            # Preencher tokens não casados interpolando entre vizinhos casados
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
            preview = " ".join(w["text"] for w in raw_words[:20])
            print(f"Word alignment via faster-whisper OK ({len(raw_words)} -> {len(aligned)} tokens)")
            return aligned, "faster-whisper-tiny", preview
    except Exception as exc:
        print(f"Aviso faster-whisper fallback ({exc}); usando silencedetect...")

    # Tentativa 2: FFmpeg silencedetect + distribuição ponderada por tamanho de palavra
    try:
        log = subprocess.check_output(
            ["ffmpeg", "-i", str(mp3_path), "-af", "silencedetect=noise=-32dB:d=0.16", "-f", "null", "-"],
            stderr=subprocess.STDOUT,
        ).decode("utf-8", errors="ignore")
        starts = [float(x) for x in re.findall(r"silence_start:\s*([0-9.]+)", log)]
        ends = [float(x) for x in re.findall(r"silence_end:\s*([0-9.]+)", log)]
        speech_segs: list[tuple[float, float]] = []
        cursor = 0.05
        for s_t, e_t in zip(starts, ends):
            if s_t - cursor > 0.12:
                speech_segs.append((cursor, s_t))
            cursor = e_t
        if dur - cursor > 0.12:
            speech_segs.append((cursor, dur - 0.04))
        total_speech = sum(e - s for s, e in speech_segs)
        if speech_segs and total_speech > 2.0:
            weights = [max(2, len(_normalize_tok(t)) + (2 if re.search(r"[.!?,]$", t) else 0)) for t in script_tokens]
            tot_w = sum(weights)
            aligned: list[dict] = []
            seg_i = 0
            seg_pos = speech_segs[0][0]
            for tok, wt in zip(script_tokens, weights):
                span = total_speech * (wt / tot_w)
                w_start = seg_pos
                rem = span
                while rem > 0 and seg_i < len(speech_segs):
                    avail = speech_segs[seg_i][1] - seg_pos
                    if rem <= avail:
                        seg_pos += rem
                        rem = 0
                    else:
                        rem -= avail
                        seg_i += 1
                        if seg_i < len(speech_segs):
                            seg_pos = speech_segs[seg_i][0]
                w_end = max(w_start + 0.08, seg_pos)
                aligned.append({"text": tok, "start": round(w_start, 3), "end": round(w_end, 3)})
            return aligned, "ffmpeg-silencedetect", ""
    except Exception as exc:
        print(f"Aviso silencedetect fallback ({exc})")

    # Tentativa 3: Proporcional por caracteres
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


def build_caption_chunks(words: list[dict], delay_offset: float = 0.18) -> tuple[list[dict], str]:
    """Agrupa palavras em blocos naturais (2-4 palavras) respeitando pausas e início de frases."""
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
            and clean not in {"zero", "whatsapp", "instagram", "sos", "stanford", "código", "codigo", "dia", "michigan", "borkovec"}
            and prev_gap >= 0.12
        )
        ends_sentence = bool(re.search(r"[.!?]$", raw_txt))
        if cur and (
            len(cur) >= 4
            or cur_len + len(raw_txt) > 22
            or prev_gap >= 0.24
            or starts_new_sentence
        ):
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
        if next_start - chunks[i]["end"] < 0.45:
            chunks[i]["end"] = max(chunks[i]["end"], round(next_start - 0.02, 3))

    html_parts: list[str] = []
    for ci, ch in enumerate(chunks):
        spans = "".join(
            f'<span class="w" id="w-{ci}-{wi}">{html.escape(w["text"])}</span>'
            for wi, w in enumerate(ch["words"])
        )
        html_parts.append(f'<div class="cap-chunk" id="chunk-{ci}">{spans}</div>')
    return chunks, "\n".join(html_parts)


def build_scene1_html(script: dict) -> str:
    vt = script["visual_type"]
    if vt == "whatsapp":
        return f"""
        <div id="s1Primary">
          <div class="wa-card">
            <div class="wa-head">
              <div class="wa-app"><span class="wa-icon">W</span><span>WHATSAPP</span></div>
              <div class="wa-time">agora</div>
            </div>
            <div class="wa-sender">{html.escape(script["hook_sender"])}</div>
            <div class="wa-body-wrap">
              <div class="wa-typing" id="waTyping">
                <span class="tdot"></span><span class="tdot"></span><span class="tdot"></span>
              </div>
              <div class="wa-msg" id="waMsg">{html.escape(script["hook_msg"])}</div>
            </div>
            <div><span class="alert-strip" id="waAlert">{html.escape(script["hook_alert"])}</span></div>
          </div>
          <div class="s1-wave-box">
            <span class="s1-wave-tag">PICO DE DOPAMINA</span>
            <svg viewBox="0 0 380 48" width="380" height="48">
              <path id="s1WavePath" d="M 4 24 L 60 24 L 82 24 L 98 6 L 116 42 L 134 10 L 152 38 L 170 24 L 245 24 L 265 8 L 285 40 L 304 24 L 376 24"
                fill="none" stroke="#ff5c77" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"
                pathLength="100" stroke-dasharray="100" stroke-dashoffset="100"/>
            </svg>
          </div>
        </div>
        """
    if vt == "contrast":
        return f"""
        <div class="contrast-wrap" id="s1Primary">
          <div class="contrast-grid">
            <div class="c-panel left" id="cLeft">
              <span class="c-pill red">{html.escape(script["hook_left_tag"])}</span>
              <div class="c-text">{html.escape(script["hook_left_text"])}</div>
            </div>
            <div class="c-panel right" id="cRight">
              <span class="c-pill gold">{html.escape(script["hook_right_tag"])}</span>
              <div class="c-text">{html.escape(script["hook_right_text"])}</div>
            </div>
          </div>
          <div class="vs-badge" id="vsBadge">REALIDADE VS ARMADILHA</div>
        </div>
        """
    return f"""
    <div class="timer-wrap" id="s1Primary">
      <div class="gauge-box">
        <svg class="gauge-svg" viewBox="0 0 320 320">
          <defs>
            <linearGradient id="gArc" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stop-color="#ff5c77"/>
              <stop offset="55%" stop-color="#d4af6a"/>
              <stop offset="100%" stop-color="#5cd3a6"/>
            </linearGradient>
          </defs>
          <g id="orbitRing">
            <circle cx="160" cy="160" r="146" fill="none" stroke="rgba(212,175,106,0.35)" stroke-width="2" stroke-dasharray="10 10"/>
          </g>
          <circle cx="160" cy="160" r="126" fill="none" stroke="rgba(255,255,255,0.09)" stroke-width="14"/>
          <circle id="timerArc" cx="160" cy="160" r="126" fill="none" stroke="url(#gArc)" stroke-width="14" stroke-linecap="round"
            transform="rotate(-90 160 160)" pathLength="100" stroke-dasharray="100" stroke-dashoffset="100"/>
        </svg>
        <div class="gauge-center">
          <div class="timer-label">{html.escape(script["hook_label"])}</div>
          <div class="timer-big">{html.escape(script["hook_big"])}</div>
        </div>
      </div>
      <div class="timer-sub-card" id="timerSubCard">{html.escape(script["hook_sub"])}</div>
    </div>
    """


def build_scene2_html(script: dict) -> str:
    s2t = script["scene2_type"]
    head = f'<div class="scene-kicker">ANÁLISE DO PADRÃO</div><div class="scene-h2">{html.escape(script["scene2_title"])}</div>'
    if s2t == "wave":
        return f"""
        {head}
        <div class="chart-panel">
          <svg viewBox="0 0 740 240" width="100%" height="225">
            <defs>
              <linearGradient id="wStroke" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stop-color="#ff5c77"/>
                <stop offset="45%" stop-color="#d4af6a"/>
                <stop offset="100%" stop-color="#5cd3a6"/>
              </linearGradient>
              <linearGradient id="wFill" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stop-color="rgba(255,92,119,0.32)"/>
                <stop offset="100%" stop-color="rgba(92,211,166,0.0)"/>
              </linearGradient>
            </defs>
            <line x1="30" y1="60" x2="710" y2="60" stroke="rgba(255,255,255,0.08)" stroke-dasharray="6 6"/>
            <line x1="30" y1="135" x2="710" y2="135" stroke="rgba(255,255,255,0.08)" stroke-dasharray="6 6"/>
            <line x1="30" y1="210" x2="710" y2="210" stroke="rgba(255,255,255,0.14)"/>
            <path id="waveArea" d="M 40 215 C 120 215, 145 56, 225 56 C 325 56, 405 198, 690 210 L 690 215 L 40 215 Z" fill="url(#wFill)"/>
            <path id="wavePath" d="M 40 215 C 120 215, 145 56, 225 56 C 325 56, 405 198, 690 210"
              fill="none" stroke="url(#wStroke)" stroke-width="7" stroke-linecap="round"
              pathLength="100" stroke-dasharray="100" stroke-dashoffset="100"/>
            <circle id="waveDot" cx="40" cy="215" r="11" fill="#faf7f2" stroke="#d4af6a" stroke-width="5"/>
          </svg>
        </div>
        <div class="two-col-mini">
          <div class="mini-card warn" id="s2CardA">
            <div class="mini-k red">{html.escape(script["scene2_a_label"])}</div>
            <div class="mini-v">{html.escape(script["scene2_a_text"])}</div>
          </div>
          <div class="mini-card calm" id="s2CardB">
            <div class="mini-k sage">{html.escape(script["scene2_b_label"])}</div>
            <div class="mini-v">{html.escape(script["scene2_b_text"])}</div>
          </div>
        </div>
        <div class="metric-banner" id="s2Metric">{html.escape(script["scene2_metric"])}</div>
        """
    if s2t == "bars":
        return f"""
        {head}
        <div class="bar-stack">
          <div class="bar-card warn" id="barCardA">
            <div class="bar-top"><span class="bar-lbl red">{html.escape(script["scene2_a_label"])}</span></div>
            <div class="bar-txt">{html.escape(script["scene2_a_text"])}</div>
            <div class="cmp-track"><div class="cmp-fill red" id="barFillA"></div></div>
          </div>
          <div class="bar-card good" id="barCardB">
            <div class="bar-top"><span class="bar-lbl sage">{html.escape(script["scene2_b_label"])}</span></div>
            <div class="bar-txt">{html.escape(script["scene2_b_text"])}</div>
            <div class="cmp-track"><div class="cmp-fill sage" id="barFillB"></div></div>
          </div>
        </div>
        <div class="metric-banner" id="s2Metric">{html.escape(script["scene2_metric"])}</div>
        """
    return f"""
    {head}
    <div class="flow-stack">
      <div class="flow-node" id="flow0">
        <div class="flow-idx">1</div>
        <div><div class="flow-lbl">{html.escape(script["scene2_a_label"])}</div><div class="flow-txt">{html.escape(script["scene2_a_text"])}</div></div>
      </div>
      <svg width="36" height="34" viewBox="0 0 36 34">
        <path id="flowArr0" d="M18 2 L18 28 M10 20 L18 29 L26 20" fill="none" stroke="#d4af6a" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round" pathLength="100" stroke-dasharray="100" stroke-dashoffset="100"/>
      </svg>
      <div class="flow-node" id="flow1">
        <div class="flow-idx">2</div>
        <div><div class="flow-lbl">{html.escape(script["scene2_b_label"])}</div><div class="flow-txt">{html.escape(script["scene2_b_text"])}</div></div>
      </div>
      <svg width="36" height="34" viewBox="0 0 36 34">
        <path id="flowArr1" d="M18 2 L18 28 M10 20 L18 29 L26 20" fill="none" stroke="#5cd3a6" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round" pathLength="100" stroke-dasharray="100" stroke-dashoffset="100"/>
      </svg>
      <div class="flow-node" id="flow2" style="border-color:rgba(92,211,166,0.5);">
        <div class="flow-idx" style="background:rgba(92,211,166,0.2);color:#9ef2d2;border-color:rgba(92,211,166,0.5);">✓</div>
        <div><div class="flow-lbl" style="color:#5cd3a6;">QUEBRA DO CICLO</div><div class="flow-txt">{html.escape(script["scene2_metric"])}</div></div>
      </div>
    </div>
    """


def build_scene3_html(script: dict) -> str:
    cards: list[str] = []
    for idx, st in enumerate(script["steps"][:3]):
        cards.append(f"""
        <div class="step-card" id="stepCard{idx}">
          <div class="step-num">0{idx + 1}</div>
          <div class="step-body">
            <div class="step-title">{html.escape(st["title"])}</div>
            <div class="step-desc">{html.escape(st["desc"])}</div>
          </div>
          <svg class="step-chk" viewBox="0 0 42 42">
            <circle cx="21" cy="21" r="18" fill="rgba(92,211,166,0.12)" stroke="rgba(92,211,166,0.45)" stroke-width="2"/>
            <path id="chk{idx}" d="M13 21.5 L18.5 27 L29.5 15.5" fill="none" stroke="#5cd3a6" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"
              pathLength="100" stroke-dasharray="100" stroke-dashoffset="100"/>
          </svg>
        </div>
        """)
    return (
        '<div class="scene-kicker">SEU PLANO DE AÇÃO AGORA</div>'
        '<div class="scene-h2">3 passos para cortar a recaída</div>'
        f'<div class="steps-stack">{"".join(cards)}</div>'
    )


def fetch_bgm(out_path: Path) -> Path:
    """Baixa 1 trilha piano/cinematográfica gratuita do Mixkit (com fallback sintético suave se offline)."""
    curl_bin = shutil.which("curl.exe") or shutil.which("curl") or "curl"
    topics = MUSIC_TOPICS[:]
    random.shuffle(topics)
    for topic in topics:
        page_url = f"https://mixkit.co/free-stock-music/{topic}/"
        try:
            page_html = subprocess.check_output(
                [curl_bin, "-sL", "--max-time", "18", "-A", "Mozilla/5.0", page_url]
            ).decode("utf-8", errors="ignore")
            matches = list(dict.fromkeys(re.findall(r"https://assets\.mixkit\.co/music/[^\s\"'<>]+\.mp3", page_html)))
            if matches:
                chosen = random.choice(matches[:20])
                subprocess.check_call([curl_bin, "-sL", "--max-time", "40", "-o", str(out_path), chosen])
                if out_path.exists() and out_path.stat().st_size > 25_000:
                    print(f"Baixada trilha piano Mixkit: {chosen}")
                    return out_path
        except Exception as exc:
            print(f"Aviso BGM em {page_url}: {exc}")

    # Fallback pad cinematográfico limpo em Dm9 via FFmpeg
    subprocess.check_call([
        "ffmpeg", "-y", "-f", "lavfi",
        "-i", "aevalsrc=0.12*sin(2*PI*146.83*t)+0.08*sin(2*PI*220*t)+0.06*sin(2*PI*261.63*t):s=44100:d=45",
        "-af", "lowpass=f=480", str(out_path),
    ])
    return out_path


def main() -> None:
    history = load_history()
    posted_topics = [item.get("topic") or item.get("verse", "") for item in history.get("posted", [])]

    print("1. Selecionando/gerando roteiro estruturado v3 (CÓDIGO ZERO)...")
    script = generate_script(posted_topics)
    print(f"Tema: {script['topic']} | S1={script['visual_type']} | S2={script['scene2_type']}")

    print("2. Sintetizando voz feminina brasileira com emoção real...")
    voz_path = BUILD_DIR / "voz.mp3"
    voice_dur, pre_words, tts_info = synthesize_emotional_female_voice(
        script["narration"], script.get("emotion_direction", "Acolhedora e firme"), voz_path
    )

    print("3. Alinhando legenda palavra por palavra...")
    words, sync_engine, transcribed_preview = align_words_to_audio(
        script["narration"], voz_path, voice_dur, pre_words
    )
    total_dur = max(17.5, round(voice_dur + 1.2, 1))
    t2 = round(total_dur * 0.25, 2)
    t3 = round(total_dur * 0.56, 2)
    t4 = round(max(t3 + 2.5, min(total_dur - 4.4, total_dur * 0.82)), 2)
    print(f"Duração={total_dur}s | Cenas: 0 -> {t2} -> {t3} -> {t4} | Sync={sync_engine}")

    print("4. Baixando trilha real piano/cinematográfica...")
    bgm_path = fetch_bgm(BUILD_DIR / "bgm.mp3")

    hf_dir = BUILD_DIR / "hf_proj"
    hf_dir.mkdir(parents=True, exist_ok=True)
    chunks, captions_html = build_caption_chunks(words, delay_offset=0.18)

    tpl = (ROOT / "template.html").read_text(encoding="utf-8")
    replacements = {
        "__DURATION__": str(total_dur),
        "__T2__": str(t2),
        "__T3__": str(t3),
        "__T4__": str(t4),
        "__S1_TYPE__": script["visual_type"],
        "__S2_TYPE__": script["scene2_type"],
        "__BADGE__": html.escape(script["badge"]),
        "__SCENE1_HTML__": build_scene1_html(script),
        "__SCENE2_HTML__": build_scene2_html(script),
        "__SCENE3_HTML__": build_scene3_html(script),
        "__CAPTIONS_HTML__": captions_html,
        "__CHUNKS_JSON__": json.dumps(chunks, ensure_ascii=False),
    }
    for k, v in replacements.items():
        tpl = tpl.replace(k, v)
    (hf_dir / "index.html").write_text(tpl, encoding="utf-8")

    print("5. Renderizando animação 1080x1920 via HyperFrames...")
    video_no_audio = BUILD_DIR / "video_v3.mp4"
    hf_cmd = (
        ["cmd", "/c", "npx", "--yes", "hyperframes", "render", ".", "--output", str(video_no_audio)]
        if os.name == "nt"
        else ["npx", "--yes", "hyperframes", "render", ".", "--output", str(video_no_audio)]
    )
    subprocess.check_call(hf_cmd, cwd=str(hf_dir))

    print("6. Mixando áudio cinema (SFX nas 4 transições + voz quente + piano ducked) e codificação HQ...")
    final_path = BUILD_DIR / "reel_final.mp4"
    fade_out_start = max(1.0, total_dur - 2.4)
    d2_ms = int(t2 * 1000)
    d3_ms = int(t3 * 1000)
    d4_ms = int(t4 * 1000)
    hook_sfx = "sine=frequency=784:duration=0.11" if script["visual_type"] == "whatsapp" else "sine=frequency=98:duration=0.20"

    subprocess.check_call([
        "ffmpeg", "-y",
        "-i", str(video_no_audio),
        "-i", str(voz_path),
        "-i", str(bgm_path),
        "-f", "lavfi", "-i", hook_sfx,
        "-f", "lavfi", "-i", "sine=frequency=165:duration=0.14",
        "-f", "lavfi", "-i", "sine=frequency=185:duration=0.14",
        "-f", "lavfi", "-i", "sine=frequency=220:duration=0.16",
        "-filter_complex",
        f"[1:a]aformat=sample_rates=44100:channel_layouts=stereo,adelay=180|180,"
        f"highpass=f=75,equalizer=f=3000:t=q:w=1.4:g=2.5,"
        f"acompressor=threshold=-18dB:ratio=2.8:attack=6:release=60,volume=1.55,asplit=2[vmain][vsc];"
        f"[2:a]aformat=sample_rates=44100:channel_layouts=stereo,atrim=0:{total_dur},asetpts=PTS-STARTPTS,"
        f"afade=t=in:st=0:d=0.8,afade=t=out:st={fade_out_start}:d=2.4,volume=0.24[bgmraw];"
        f"[bgmraw][vsc]sidechaincompress=threshold=0.04:ratio=4:attack=25:release=340[bgmduck];"
        f"[3:a]aformat=sample_rates=44100:channel_layouts=stereo,afade=t=out:st=0.03:d=0.08,volume=0.18,adelay=60|60[sfx1];"
        f"[4:a]aformat=sample_rates=44100:channel_layouts=stereo,lowpass=f=700,afade=t=in:st=0:d=0.02,afade=t=out:st=0.05:d=0.09,volume=0.14,adelay={d2_ms}|{d2_ms}[sfx2];"
        f"[5:a]aformat=sample_rates=44100:channel_layouts=stereo,lowpass=f=750,afade=t=in:st=0:d=0.02,afade=t=out:st=0.05:d=0.09,volume=0.14,adelay={d3_ms}|{d3_ms}[sfx3];"
        f"[6:a]aformat=sample_rates=44100:channel_layouts=stereo,lowpass=f=850,afade=t=in:st=0:d=0.02,afade=t=out:st=0.05:d=0.11,volume=0.16,adelay={d4_ms}|{d4_ms}[sfx4];"
        f"[vmain][bgmduck][sfx1][sfx2][sfx3][sfx4]amix=inputs=6:duration=first:dropout_transition=2,alimiter=limit=0.95[aout]",
        "-map", "0:v", "-map", "[aout]",
        "-c:v", "libx264", "-profile:v", "high", "-level", "4.1", "-crf", "16", "-preset", "medium", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
        "-movflags", "+faststart",
        "-t", str(total_dur), str(final_path),
    ])

    (BUILD_DIR / "caption.txt").write_text(script["caption"], encoding="utf-8")
    meta = {
        "engine_version": "v3",
        "date_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "topic": script["topic"],
        "visual_type": script["visual_type"],
        "scene2_type": script["scene2_type"],
        "tts_engine": tts_info["tts_engine"],
        "tts_voice": tts_info["tts_voice"],
        "tts_error": tts_info["tts_error"],
        "sync_engine": sync_engine,
        "duration": total_dur,
        "t2": t2,
        "t3": t3,
        "t4": t4,
        "words_count": len(words),
        "chunks_count": len(chunks),
        "transcribed_preview": transcribed_preview,
    }
    (BUILD_DIR / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    history["posted"].append({
        "date": meta["date_utc"],
        "topic": script["topic"],
        "visual_type": script["visual_type"],
        "scene2_type": script["scene2_type"],
        "tts_engine": tts_info["tts_engine"],
        "tts_voice": tts_info["tts_voice"],
    })
    save_history(history)
    print("Vídeo v3 CÓDIGO ZERO, legenda e meta.json gerados em build/")


if __name__ == "__main__":
    main()

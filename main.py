import asyncio
import html
import json
import os
import random
import re
import shutil
import subprocess
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent
HISTORY_FILE = ROOT / "history.json"
BUILD_DIR = ROOT / "build"
BUILD_DIR.mkdir(exist_ok=True)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
VOICE = os.environ.get("TTS_VOICE", "pt-BR-ThalitaMultilingualNeural")
WHATSAPP_DISPLAY = "(12) 99659-3222"

# B-roll cinematográfico escuro/atmosférico (3 cortes distintos por Reel!)
BROLL_TOPICS = [
    "rain", "night", "city", "window", "clouds", "sunset",
    "ocean", "coffee", "forest", "stars", "water", "candle", "dark", "street",
]
MUSIC_TOPICS = ["piano", "ambient", "cinematic", "sad", "calm"]

EMPHASIS_WORDS = {
    "não", "nunca", "jamais", "pare", "trava", "silêncio", "zero", "dói",
    "vergonha", "orgulho", "ego", "migalha", "migalhas", "abstinência",
    "noventa", "segundos", "madrugada", "recaída", "stalkear", "bloqueia",
    "dignidade", "paz", "mentira", "armadilha", "whatsapp", "bio", "sozinho",
    "sozinha", "culpa", "queimadura", "física", "reservas", "amigos",
}

# 18 roteiros v2 de altíssima retenção (3 camadas: visual pattern-interrupt + voz visceral + CTA honesto de envios/comentário ZERO)
CURATED_SCRIPTS = [
    {
        "topic": "Ex mandou 'Oi, tudo bem?' do nada (Script #01)",
        "badge": "SCRIPT #01 • ESCUDO",
        "visual_type": "whatsapp",
        "hook_sender": "Ex • 01:42",
        "hook_msg": "\"Oi... tudo bem por aí? Sumiu.\"",
        "hook_alert": "NÃO RESPONDA NO IMPULSO",
        "narration": (
            "Se o seu ex mandou 'oi, tudo bem?' depois de semanas sumido, trava o dedo agora. "
            "Ele não voltou arrependido. Isso é isca de esforço zero pra testar se você ainda tá no banco de reservas. "
            "Se você responder na hora com textão, o ego dele enche e ele some de novo amanhã. "
            "A ação certa? Silêncio absoluto. Se visualizou sem querer, não manda nada pra compensar. "
            "Manda esse vídeo pra quem quase caiu nisso hoje. E se quiser os dezesseis scripts prontos do Código Zero, comenta ZERO ou chama no WhatsApp da bio."
        ),
        "caption": (
            "Salva antes de responder qualquer 'oi sumido' na madrugada.\n\n"
            "Quando o ex manda mensagem vazia depois do término, responder na ansiedade só alimenta o ego dele e reinicia a sua dor. "
            "A regra do contato zero no Código Zero é simples: responda ao tamanho real do esforço, nunca ao tamanho da sua saudade.\n\n"
            "Manda pra amiga que precisa ler isso hoje. Quer os 16 Scripts prontos e a Central SOS de 14 dias? Comenta ZERO ou chama no WhatsApp da bio: (12) 99659-3222.\n\n"
            "#contatozero #superartermino #dependenciaemocional #exmandoumensagem #codigozero"
        ),
    },
    {
        "topic": "Por que saudade dói no corpo como queimadura (Kross 2011)",
        "badge": "NEUROCIÊNCIA • PÁG. 04",
        "visual_type": "timer",
        "hook_label": "ESTUDO • UNIV. DE MICHIGAN",
        "hook_big": "DOR FÍSICA",
        "hook_sub": "Rejeição aciona a mesma área cerebral de uma queimadura",
        "narration": (
            "Você acordou hoje com um aperto real no peito e achou que perdeu o amor-próprio? Escuta isso. "
            "Uma pesquisa da Universidade de Michigan provou que a rejeição amorosa aciona a mesma rede cerebral de uma queimadura física. "
            "Não é fraqueza sua. É corte químico de dopamina. "
            "Por isso conselho raso de 'é só esquecer' nunca funciona. Você precisa de um protocolo de desmame de catorze dias. "
            "Envia pra alguém que tá se culpando por ainda sofrer. Quer o Código Zero completo? Comenta ZERO ou chama no WhatsApp da bio."
        ),
        "caption": (
            "Para de se chamar de fraco ou fraca por ainda sentir aperto no peito.\n\n"
            "Entender como superar término começa na neurociência: estudos de imagem cerebral mostram que a abstinência afetiva imita dor física e dependência química. "
            "Você não sai disso na força bruta, sai com método diário de 14 dias.\n\n"
            "Comenta ZERO ou chama direto no WhatsApp da bio: (12) 99659-3222.\n\n"
            "#dependenciaemocional #superartermino #neurociencia #saudeemocional #codigozero"
        ),
    },
    {
        "topic": "A Regra 90-15 antes de mandar mensagem às 23h",
        "badge": "FASE Z • REGRA 90–15",
        "visual_type": "timer",
        "hook_label": "TRAVA ANTI-RECAÍDA",
        "hook_big": "01:30",
        "hook_sub": "O pico químico da crise dura só 90 segundos",
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
            "Na Central SOS do Código Zero você tem o cronômetro de 15 minutos e o botão Queimar Mensagem direto no celular.\n\n"
            "Comenta ZERO ou chama no WhatsApp da bio: (12) 99659-3222.\n\n"
            "#contatozero #fimderelacionamento #amorproprio #dependenciaemocional #codigozero"
        ),
    },
    {
        "topic": "Esta mensagem foi apagada (Script #04)",
        "badge": "SCRIPT #04 • ISCA",
        "visual_type": "whatsapp",
        "hook_sender": "Ex • 23:54",
        "hook_msg": "⊘ Esta mensagem foi apagada",
        "hook_alert": "ARMADILHA DE CURIOSIDADE",
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
            "No Código Zero você tem 16 scripts prontos para cada armadilha sem precisar improvisar na hora da ansiedade.\n\n"
            "Comenta ZERO ou chama no WhatsApp da bio: (12) 99659-3222.\n\n"
            "#contatozero #exmandoumensagem #relacionamentotoxico #amorproprio #codigozero"
        ),
    },
    {
        "topic": "Já mandou textão e se humilhou? Botão de Reinício (#16)",
        "badge": "SCRIPT #16 • RESGATE",
        "visual_type": "contrast",
        "hook_left_tag": "O QUE PIORA TUDO",
        "hook_left_text": "Mandar mais 10 áudios tentando explicar o textão",
        "hook_right_tag": "BOTÃO DE REINÍCIO",
        "hook_right_text": "1 frase elegante + silêncio absoluto",
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
        "visual_type": "timer",
        "hook_label": "ALERTA NOTURNO",
        "hook_big": "70%",
        "hook_sub": "das mensagens de arrependimento acontecem na cama à noite",
        "narration": (
            "Setenta por cento das recaídas de término acontecem entre dez da noite e duas da manhã. "
            "Não é coincidência. Com o cérebro exausto na horizontal, o córtex racional desliga e a saudade dobra de tamanho. "
            "Força de vontade falha às onze da noite. Só trava física protege você. "
            "Hoje às dez e meia, coloca o carregador fora do alcance da cama e bota um áudio neutro de fundo com timer. "
            "Manda pra quem sempre recai na madrugada. Quer o Protocolo da Madrugada e os seis Cartões SOS? Comenta ZERO ou chama no WhatsApp da bio."
        ),
        "caption": (
            "Nenhuma decisão amorosa tomada deitado na cama às 23h é lúcida.\n\n"
            "Se a saudade do ex aperta toda madrugada, você precisa de travas físicas de ambiente e do Protocolo da Madrugada do Código Zero (com 6 Cartões SOS para a tela de bloqueio).\n\n"
            "Comenta ZERO ou chama no WhatsApp da bio: (12) 99659-3222.\n\n"
            "#superartermino #insonia #dependenciaemocional #contatozero #codigozero"
        ),
    },
    {
        "topic": "Ele mandou 'Sonhei com você' (Script #08)",
        "badge": "SCRIPT #08 • NOSTALGIA",
        "visual_type": "whatsapp",
        "hook_sender": "Ex • 22:18",
        "hook_msg": "\"Sonhei com você ontem... passei lá e lembrei da gente\"",
        "hook_alert": "TESTE DE EGO DETECTADO",
        "narration": (
            "Ele mandou 'sonhei com você' ou 'passei naquele lugar e lembrei da gente'? Respira antes de derreter. "
            "Nostalgia vaga não é pedido de volta nem assunção de erro. Ele só tá testando se a porta ainda tá destrancada. "
            "Se você responder 'eu também tô morrendo de saudade', o poder some. "
            "Responde curto e sereno: 'Fico feliz que tenham ficado boas lembranças. Hoje tô focado na minha rotina e prefiro manter meu espaço. Se cuida.' "
            "Manda pra quem ia derreter nessa mensagem. Quer os dezesseis scripts? Comenta ZERO ou chama no WhatsApp da bio."
        ),
        "caption": (
            "Quem quer construir de novo fala com clareza, não com charada nostálgica.\n\n"
            "Essa resposta do Script #08 desarma mensagens vagas de ex mantendo sua classe intacta. Se era apenas ego, acaba ali na hora.\n\n"
            "Quer o kit completo com 16 Scripts e a Central SOS no celular? Comenta ZERO ou chama no WhatsApp da bio: (12) 99659-3222.\n\n"
            "#exmandoumensagem #contatozero #limitesemocionais #superartermino #codigozero"
        ),
    },
    {
        "topic": "Por que o Dia 3 do Contato Zero dói mais forte (Pico de Extinção)",
        "badge": "DIA 03 • PICO DE EXTINÇÃO",
        "visual_type": "timer",
        "hook_label": "CURVA DE 14 DIAS",
        "hook_big": "DIA 03",
        "hook_sub": "O dia em que 80% desistem bem antes da virada",
        "narration": (
            "Se você tá no terceiro dia sem falar com seu ex e hoje doeu o dobro de ontem, calma. Você não regrediu. "
            "Na psicologia comportamental isso se chama pico de extinção. "
            "Sempre que você corta um vício, o cérebro grita mais alto no terceiro dia pra ver se você cede e entrega a dose. "
            "A maioria desiste exatamente horas antes da curva começar a despencar. "
            "Salva pra reler quando o Dia Três bater. Quer o mapa dos catorze dias com gráfico da dor? Comenta ZERO ou chama no WhatsApp da bio."
        ),
        "caption": (
            "Se hoje a vontade doeu mais forte, é sinal biológico de que o desmame está funcionando.\n\n"
            "No Diário de 14 Dias e no gráfico ao vivo da Central SOS do Código Zero, você atravessa o pico de extinção sabendo exatamente o que fazer em cada fase.\n\n"
            "Comenta ZERO ou chama no WhatsApp da bio: (12) 99659-3222.\n\n"
            "#contatozero #dependenciaemocional #superartermino #psicologiapratica #codigozero"
        ),
    },
    {
        "topic": "Amnésia Seletiva: você sente falta de uma fantasia",
        "badge": "FASE R • AUTÓPSIA",
        "visual_type": "contrast",
        "hook_left_tag": "O QUE A SAUDADE EDITA",
        "hook_left_text": "Só os abraços, viagens e promessas bonitas",
        "hook_right_tag": "O QUE ELA APAGA",
        "hook_right_text": "As noites de ansiedade, frieza e pisar em ovos",
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
        "visual_type": "timer",
        "hook_label": "PROTOCOLO DE STANFORD",
        "hook_big": "120 SEG",
        "hook_sub": "Como frear o aperto físico no peito na hora",
        "narration": (
            "Quando o peito aperta e a mão treme de saudade, tentar pensar positivo não adianta nada porque seu sistema nervoso tá em alerta. "
            "Faz o Reset de Cento e Vinte Segundos: primeiro, água bem fria no rosto por trinta segundos pra ativar o nervo vago. "
            "Depois, cinco ciclos do Suspiro Duplo validado em Stanford: puxa longo pelo nariz, dá mais uma puxadinha curta no topo e solta bem devagar pela boca. "
            "Em dois minutos seu batimento cai. Salva esse vídeo pra hora do aperto. Quer o guia animado na Central SOS? Comenta ZERO ou chama no WhatsApp da bio."
        ),
        "caption": (
            "Primeiro você acalma o corpo; só depois você decide qualquer coisa.\n\n"
            "A respiração do Suspiro Duplo (estudo de Balban & Huberman, 2023) está integrada ao vivo na Central SOS do Código Zero para os minutos em que a crise de ansiedade pós término aperta.\n\n"
            "Comenta ZERO ou chama no WhatsApp da bio: (12) 99659-3222.\n\n"
            "#ansiedade #superartermino #saudemental #dependenciaemocional #codigozero"
        ),
    },
    {
        "topic": "Ele pediu para 'continuarem amigos' (Script #11)",
        "badge": "SCRIPT #11 • LIMITES",
        "visual_type": "whatsapp",
        "hook_sender": "Ex • 19:15",
        "hook_msg": "\"Não quero te perder... a gente pode continuar sendo amigo, né?\"",
        "hook_alert": "NÃO ACEITE ESSE ACORDO",
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
        "visual_type": "contrast",
        "hook_left_tag": "SE ESTIVER BEM",
        "hook_left_text": "Vai doer como um soco no estômago",
        "hook_right_tag": "SE PARECER TRISTE",
        "hook_right_text": "Vai te iludir e fazer você mandar 'oi'",
        "narration": (
            "Antes de abrir a lupa pra olhar o perfil do seu ex hoje, me responde uma coisa: o que você ganha com isso? "
            "Se a pessoa parecer feliz sem você, seu dia acaba na hora. Se postar indireta triste, você se ilude e quase manda mensagem. "
            "Não existe cenário em que stalkear traz paz. Cada espiada zera o seu progresso pro Dia Zero. "
            "Silencia stories e publicações hoje mesmo. A pessoa nem recebe notificação. "
            "Manda pra amiga que prometeu parar de stalkear. Quer o protocolo Código Zero completo? Comenta ZERO ou chama no WhatsApp da bio."
        ),
        "caption": (
            "Olhar o perfil do ex nunca trouxe paz. Só entrega mais uma dose para o ciclo da abstinência.\n\n"
            "No Código Zero você aprende a Auditoria dos 7 Gatilhos Invisíveis e recebe 6 Cartões SOS para salvar na galeria e cortar o impulso em 10 segundos.\n\n"
            "Comenta ZERO ou chama no WhatsApp da bio: (12) 99659-3222.\n\n"
            "#parardestalkear #contatozero #superartermino #dependenciaemocional #codigozero"
        ),
    },
    {
        "topic": "Ele apareceu com outra pessoa nas redes (Script #13)",
        "badge": "EMERGÊNCIA • SCRIPT #13",
        "visual_type": "timer",
        "hook_label": "PROTOCOLO DE CHOQUE",
        "hook_big": "ZERO REAÇÃO",
        "hook_sub": "A única postura que mantém seu valor intacto",
        "narration": (
            "Abriu o Instagram e viu o seu ex assumindo outra pessoa? Eu sei que parece um soco no estômago. "
            "Mas escuta bem o que vai salvar sua dignidade nos próximos dez minutos: "
            "Não manda mensagem com raiva, não posta indireta e não entra no perfil da pessoa nova pra se comparar. "
            "A única reação que preserva o seu valor cem por cento intacto é nenhuma reação visível. "
            "Silencia até amigos em comum que postam o casal e faz o Reset agora. Salva esse vídeo. Quer a Central SOS completa? Comenta ZERO ou chama no WhatsApp da bio."
        ),
        "caption": (
            "Não deixe cinco minutos de choque custarem semanas da sua dignidade.\n\n"
            "Quando o ex aparece com outra pessoa, reagir com raiva ou indiretas só prolonga sua ferida. O Código Zero traz o plano exato de contenção para dias assim.\n\n"
            "Comenta ZERO ou chama direto no WhatsApp da bio: (12) 99659-3222.\n\n"
            "#superartermino #amorproprio #contatozero #saudeemocional #codigozero"
        ),
    },
    {
        "topic": "Ele disse 'Pelo visto você superou rápido' (Script #10)",
        "badge": "SCRIPT #10 • PROVOCAÇÃO",
        "visual_type": "whatsapp",
        "hook_sender": "Ex • 21:08",
        "hook_msg": "\"Pelo visto já me esqueceu, né? Superou bem rápido\"",
        "hook_alert": "INVERSÃO DE CULPA",
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
        "visual_type": "contrast",
        "hook_left_tag": "TEATRO NOS STORIES",
        "hook_left_text": "Indireta, música triste ou festa forçada pra ele ver",
        "hook_right_tag": "SILÊNCIO DIGNO",
        "hook_right_text": "7 dias sem palco. Sua ansiedade cai pela metade",
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
        "visual_type": "contrast",
        "hook_left_tag": "VOLTA POR EGO",
        "hook_left_text": "Some de novo em 48h e propõe 'ver no que dá'",
        "hook_right_tag": "MUDANÇA REAL",
        "hook_right_text": "Assume erros sóbrio e mantém coerência por semanas",
        "narration": (
            "O ex reapareceu pedindo pra conversar e seu coração disparou? Calma. "
            "Nunca decida reatar antes de completar catorze dias de lucidez. Uma escolha feita no pico da abstinência quase nunca resiste a trinta dias de realidade. "
            "Passa a volta por três filtros mínimos: ele nomeou os próprios erros sem você arrancar? Propôs mudança concreta ou só 'ver no que dá'? Manteve coerência por semanas? "
            "Salva antes de abrir a porta de novo. Quer o checklist completo dos cinco critérios? Comenta ZERO ou chama no WhatsApp da bio."
        ),
        "caption": (
            "Saudade e química não provam que o motivo do término foi resolvido.\n\n"
            "Na Página 16 do Código Zero você usa o Radar Anti-Migalha com os 5 Critérios Inegociáveis para decidir com lucidez adulta, não com carência.\n\n"
            "Comenta ZERO ou chama no WhatsApp da bio: (12) 99659-3222.\n\n"
            "#voltarcomoex #relacionamentosaudavel #superartermino #amorproprio #codigozero"
        ),
    },
    {
        "topic": "Devolver coisas em casa é a maior porta de recaída (Script #05)",
        "badge": "SCRIPT #05 • LOGÍSTICA",
        "visual_type": "whatsapp",
        "hook_sender": "Ex • 16:40",
        "hook_msg": "\"Minhas coisas ficaram aí, quando posso passar pra pegar?\"",
        "hook_alert": "EVITE ENCONTRO A SÓS",
        "narration": (
            "Ele mandou mensagem perguntando quando pode passar aí pra pegar as coisas dele? Cuidado. "
            "Transformar uma entrega simples num encontro a sós dentro de casa é a maior porta de recaída pós-término. "
            "Seja adulto, cortês e objetivo: 'Já deixei tudo separado. Posso deixar na portaria ou enviar por entregador amanhã às três, fica mais prático pra nós dois.' "
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
        "visual_type": "timer",
        "hook_label": "TÉCNICA DE BORKOVEC",
        "hook_big": "18:30",
        "hook_sub": "Não proíba o pensamento: marque 15 minutos pra ele",
        "narration": (
            "Quanto mais você manda sua cabeça parar de pensar no seu ex, mais a imagem dele aparece, né? "
            "Na psicologia isso é o efeito rebote. Proibir o pensamento faz o cérebro checar a cada minuto se você parou. "
            "Usa a Janela Controlada: marca quinze minutos fixos do dia, tipo seis e meia da tarde. "
            "Pensamento invadiu no trabalho? Fala: anotado, penso nisso às seis e meia. E volta pro que tava fazendo. "
            "Manda pra quem não consegue focar no dia. Quer o protocolo completo? Comenta ZERO ou chama no WhatsApp da bio."
        ),
        "caption": (
            "A saída contra a ruminação pós término não é brigar com a própria mente, é confinar o pensamento.\n\n"
            "Inspirada na técnica clínica de Borkovec, a Janela Controlada do Código Zero devolve seu foco no trabalho já na primeira semana.\n\n"
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


def generate_script(posted_topics: list[str]) -> dict:
    """Gera roteiro viral v2 (3 camadas + sem cara de IA + sem mentir link clicável) ou usa acervo curado."""
    if GEMINI_API_KEY:
        recent = posted_topics[-30:]
        prompt = f"""
Você é um diretor criativo especialista em Reels virais de retenção (foco em compartilhamentos/envios e retenção nos 3 primeiros segundos) do produto CÓDIGO ZERO (Protocolo Imersivo de 14 Dias para superar término, desligar abstinência afetiva, 16 Scripts Escudo de Diamante, Central SOS Web interativa no celular e 6 Cartões SOS).
O atendimento de venda acontece pelo WhatsApp {WHATSAPP_DISPLAY} (descrito na bio — NÃO diga "clique no link da bio", diga "comenta ZERO ou chama no WhatsApp da bio"!).

Crie um Reel de 18 a 24 segundos sobre um ângulo DIFERENTE destes já postados: {recent}.
Regras obrigatórias (viral-hooks + viral-instagram-reels + ig-human):
- Fale como uma pessoa lúcida e real conversando olho no olho em português do Brasil natural ("tá", "pra", frases curtas e diretas).
- ZERO clichês de IA, ZERO travessões "—", ZERO "pare de rolar", ZERO tom de propaganda nos primeiros 15 segundos!
- Os primeiros 2 segundos DEVEM abrir no meio de uma dor/cena específica (ex.: mensagem do ex, madrugada, stalkear, Dia 3, ciúme, voltar por carência).
- Entregue uma ferramenta/script concreto do Código Zero que dê vontade real de SALVAR e ENVIAR pra uma amiga.
- Escolha um visual_type entre "whatsapp", "timer", ou "contrast":
  * Se "whatsapp": preencha "hook_sender" (ex: "Ex • 01:42"), "hook_msg" (max 55 chars), "hook_alert" (max 28 chars em maiúsculo).
  * Se "timer": preencha "hook_label" (max 26 chars), "hook_big" (1-2 palavras fortes, ex: "90 SEG" ou "DIA 03"), "hook_sub" (max 55 chars).
  * Se "contrast": preencha "hook_left_tag", "hook_left_text" (max 45 chars), "hook_right_tag", "hook_right_text" (max 45 chars).
- Legenda (ig-caption):
  * Linha 1 (<= 115 chars): frase forte ou convite de salvamento/envio (sem saudação, sem emoji no começo).
  * Corpo: 2 parágrafos curtos contendo termos naturais de busca (como superar término, contato zero, dependência emocional).
  * CTA único: "Comenta ZERO ou chama direto no WhatsApp da bio: {WHATSAPP_DISPLAY}." (SEM URL na legenda!).
  * Final: exatamente 4 ou 5 hashtags específicas (ex: #contatozero #superartermino #dependenciaemocional #amorproprio #codigozero — NUNCA #viral ou #fyp).

Retorne APENAS JSON válido com as chaves:
topic, badge, visual_type, narration, caption, e as chaves específicas do visual_type escolhido.
"""
        body = json.dumps({
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseMimeType": "application/json", "temperature": 0.9},
        }).encode("utf-8")

        for model in ["gemini-3.8-flash", "gemini-flash-latest", "gemini-flash-lite-latest"]:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
            for attempt in range(2):
                try:
                    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
                    with urllib.request.urlopen(req, timeout=20) as resp:
                        res = json.loads(resp.read().decode("utf-8"))
                    raw = res["candidates"][0]["content"]["parts"][0]["text"]
                    parsed = json.loads(raw)
                    vt = parsed.get("visual_type")
                    base_ok = all(parsed.get(k) for k in ("topic", "badge", "visual_type", "narration", "caption"))
                    type_ok = (
                        (vt == "whatsapp" and all(parsed.get(k) for k in ("hook_sender", "hook_msg", "hook_alert")))
                        or (vt == "timer" and all(parsed.get(k) for k in ("hook_label", "hook_big", "hook_sub")))
                        or (vt == "contrast" and all(parsed.get(k) for k in ("hook_left_tag", "hook_left_text", "hook_right_tag", "hook_right_text")))
                    )
                    if base_ok and type_ok:
                        # Enforce clean no-em-dash / no-fake-link guard
                        parsed["caption"] = parsed["caption"].replace("—", "-").replace("link da bio", "WhatsApp da bio")
                        parsed["narration"] = parsed["narration"].replace("link da bio", "WhatsApp da bio")
                        print(f"Roteiro v2 gerado via Gemini ({model})!")
                        return parsed
                except Exception as exc:
                    print(f"Tentativa {attempt + 1} em {model} falhou: {exc}")
                    time.sleep(3)

    print("Usando roteiro v2 curado do acervo Código Zero...")
    available = [s for s in CURATED_SCRIPTS if s["topic"] not in posted_topics]
    if not available:
        last_topics = set(posted_topics[-12:])
        available = [s for s in CURATED_SCRIPTS if s["topic"] not in last_topics] or CURATED_SCRIPTS
    return random.choice(available)


def synthesize_voice_with_word_timings(text: str, out_mp3: Path) -> tuple[float, list[dict]]:
    """Usa edge-tts com WordBoundary para gerar áudio + timestamps exatos palavra por palavra."""
    words: list[dict] = []
    try:
        import edge_tts

        async def _run() -> None:
            comm = edge_tts.Communicate(
                text=text,
                voice=VOICE,
                rate="+6%",
                pitch="+1Hz",
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
            "--voice", VOICE, "--rate=+6%", "--pitch=+1Hz",
            "--text", text, "--write-media", str(out_mp3),
        ])

    dur = float(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(out_mp3),
    ]).decode().strip())

    # Fallback proportional timings if WordBoundary returned empty
    if not words:
        tokens = re.findall(r"\S+", text)
        step = dur / max(1, len(tokens))
        for i, tok in enumerate(tokens):
            words.append({
                "text": tok,
                "start": round(i * step, 3),
                "end": round((i + 1) * step, 3),
            })

    return dur, words


def build_caption_chunks(words: list[dict], delay_offset: float = 0.18) -> tuple[list[dict], str]:
    """Agrupa palavras em blocos naturais (2-4 palavras) respeitando pausas e início de frases."""
    chunks: list[dict] = []
    cur: list[dict] = []
    cur_len = 0

    for idx, w in enumerate(words):
        raw_txt = w["text"].strip()
        if not raw_txt:
            continue
        clean = re.sub(r"[^\wÀ-ÿ]", "", raw_txt).lower()
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
            and clean not in {"zero", "whatsapp", "instagram", "sos", "stanford", "código", "codigo", "dia"}
            and prev_gap >= 0.12
        )
        ends_sentence = bool(re.search(r"[.!?]$", raw_txt))
        if cur and (
            len(cur) >= 4
            or cur_len + len(raw_txt) > 22
            or prev_gap >= 0.24
            or starts_new_sentence
        ):
            chunks.append({
                "start": cur[0]["start"],
                "end": cur[-1]["end"],
                "words": cur,
            })
            cur = []
            cur_len = 0
        cur.append(item)
        cur_len += len(raw_txt) + 1
        if ends_sentence and len(cur) >= 2:
            chunks.append({
                "start": cur[0]["start"],
                "end": cur[-1]["end"],
                "words": cur,
            })
            cur = []
            cur_len = 0

    if cur:
        chunks.append({
            "start": cur[0]["start"],
            "end": cur[-1]["end"],
            "words": cur,
        })

    # Smooth chunk end times so no awkward gaps appear between chunks
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


def build_hook_card_html(script: dict) -> str:
    vt = script["visual_type"]
    if vt == "whatsapp":
        return f"""
        <div class="wa-card" id="hookCard">
          <div class="wa-head">
            <div class="wa-app"><span class="wa-icon">W</span><span>WHATSAPP</span></div>
            <div class="wa-time">agora</div>
          </div>
          <div class="wa-sender">{html.escape(script["hook_sender"])}</div>
          <div class="wa-msg">{html.escape(script["hook_msg"])}</div>
          <div style="text-align:left;"><span class="alert-strip">{html.escape(script["hook_alert"])}</span></div>
        </div>
        """
    if vt == "contrast":
        return f"""
        <div class="contrast-card" id="hookCard">
          <div class="contrast-col contrast-left">
            <div class="c-tag red">{html.escape(script["hook_left_tag"])}</div>
            <div class="c-body">{html.escape(script["hook_left_text"])}</div>
          </div>
          <div class="contrast-col contrast-right">
            <div class="c-tag gold">{html.escape(script["hook_right_tag"])}</div>
            <div class="c-body">{html.escape(script["hook_right_text"])}</div>
          </div>
        </div>
        """
    return f"""
    <div class="timer-card" id="hookCard">
      <div class="timer-label">{html.escape(script["hook_label"])}</div>
      <div class="timer-big">{html.escape(script["hook_big"])}</div>
      <div class="timer-sub">{html.escape(script["hook_sub"])}</div>
    </div>
    """


def fetch_mixkit_assets(topics: list[str], base_url: str, pattern: str, count: int, prefix: str) -> list[Path]:
    curl_bin = shutil.which("curl.exe") or shutil.which("curl") or "curl"
    shuffled = topics[:]
    random.shuffle(shuffled)
    downloaded: list[Path] = []
    used_urls: set[str] = set()

    for topic in shuffled:
        if len(downloaded) >= count:
            break
        page_url = f"{base_url}/{topic}/"
        try:
            page_html = subprocess.check_output(
                [curl_bin, "-sL", "--max-time", "20", "-A", "Mozilla/5.0", page_url]
            ).decode("utf-8", errors="ignore")
            matches = [u for u in dict.fromkeys(re.findall(pattern, page_html)) if u not in used_urls]
            if matches:
                chosen = random.choice(matches[:24])
                ext = ".mp4" if ".mp4" in chosen else ".mp3"
                out_path = BUILD_DIR / f"{prefix}_{len(downloaded)}{ext}"
                subprocess.check_call([curl_bin, "-sL", "--max-time", "45", "-o", str(out_path), chosen])
                if out_path.exists() and out_path.stat().st_size > 25_000:
                    used_urls.add(chosen)
                    downloaded.append(out_path)
                    print(f"Baixado {prefix}_{len(downloaded)-1}: {chosen}")
        except Exception as exc:
            print(f"Aviso ao baixar mídia de {page_url}: {exc}")

    if not downloaded:
        raise RuntimeError(f"Não foi possível baixar mídia válida de {base_url}")
    return downloaded


def build_multicut_bg(clips: list[Path], total_dur: float, out_bg: Path) -> None:
    """Cria B-roll vertical 1080x1920 30fps com 3 cortes dinâmicos + leve zoom lento."""
    seg_dur = round(total_dur / len(clips) + 0.15, 2)
    cmd = ["ffmpeg", "-y"]
    for c in clips:
        cmd.extend(["-stream_loop", "-1", "-i", str(c)])

    filters = []
    concat_in = []
    for i in range(len(clips)):
        filters.append(
            f"[{i}:v]scale=1160:2062:force_original_aspect_ratio=increase,"
            f"crop=1080:1920,setsar=1,fps=30,eq=brightness=-0.06:contrast=1.12:saturation=0.88,"
            f"trim=0:{seg_dur},setpts=PTS-STARTPTS[v{i}]"
        )
        concat_in.append(f"[v{i}]")
    filters.append(f"{''.join(concat_in)}concat=n={len(clips)}:v=1:a=0,trim=0:{total_dur},setpts=PTS-STARTPTS[bg]")

    cmd.extend([
        "-filter_complex", ";".join(filters),
        "-map", "[bg]",
        "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-pix_fmt", "yuv420p",
        "-an", "-t", str(total_dur), str(out_bg),
    ])
    subprocess.check_call(cmd)


def main() -> None:
    history = load_history()
    posted_topics = [item.get("topic") or item.get("verse", "") for item in history.get("posted", [])]

    print("1. Gerando roteiro viral v2 (CÓDIGO ZERO)...")
    script = generate_script(posted_topics)
    print("Tema escolhido:", script["topic"], "| Arquétipo visual:", script["visual_type"])

    print("2. Sintetizando dublagem com WordBoundary timestamps...")
    voz_path = BUILD_DIR / "voz.mp3"
    voice_dur, words = synthesize_voice_with_word_timings(script["narration"], voz_path)
    total_dur = max(16.0, round(voice_dur + 1.0, 1))
    print(f"Voz: {voice_dur:.2f}s | Palavras sincronizadas: {len(words)} | Total: {total_dur}s")

    print("3. Baixando 3 clipes de B-roll escuro/atmosférico + trilha piano real...")
    broll_clips = fetch_mixkit_assets(
        BROLL_TOPICS,
        "https://mixkit.co/free-stock-video",
        r"https://assets\.mixkit\.co/videos/[^\s\"'<>]+\.mp4",
        count=3,
        prefix="broll",
    )
    bgm_clips = fetch_mixkit_assets(
        MUSIC_TOPICS,
        "https://mixkit.co/free-stock-music",
        r"https://assets\.mixkit\.co/music/[^\s\"'<>]+\.mp3",
        count=1,
        prefix="bgm",
    )
    bgm_path = bgm_clips[0]

    hf_dir = BUILD_DIR / "hf_proj"
    assets_dir = hf_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    bg_multicut = assets_dir / "bg.mp4"

    print("4. Montando B-roll multi-cut 1080x1920 30fps...")
    build_multicut_bg(broll_clips, total_dur, bg_multicut)

    print("5. Montando composição HyperFrames v2 (vídeo nativo + glassmorphism + legendas sincronizadas)...")
    chunks, captions_html = build_caption_chunks(words, delay_offset=0.18)
    hook_html = build_hook_card_html(script)

    tpl = (ROOT / "template.html").read_text(encoding="utf-8")
    tpl = tpl.replace("__DURATION__", str(total_dur))
    tpl = tpl.replace("__BADGE__", html.escape(script["badge"]))
    tpl = tpl.replace("__HOOK_CARD_HTML__", hook_html)
    tpl = tpl.replace("__CAPTIONS_HTML__", captions_html)
    tpl = tpl.replace("__CHUNKS_JSON__", json.dumps(chunks, ensure_ascii=False))
    (hf_dir / "index.html").write_text(tpl, encoding="utf-8")

    video_no_audio = BUILD_DIR / "video_v2.mp4"
    hf_cmd = (
        ["cmd", "/c", "npx", "--yes", "hyperframes", "render", ".", "--output", str(video_no_audio)]
        if os.name == "nt"
        else ["npx", "--yes", "hyperframes", "render", ".", "--output", str(video_no_audio)]
    )
    subprocess.check_call(hf_cmd, cwd=str(hf_dir))

    print("6. Mixando áudio cinema (SFX de gancho + voz EQ/comprimida + piano com sidechain ducking)...")
    final_path = BUILD_DIR / "reel_final.mp4"
    fade_out_start = max(1.0, total_dur - 2.4)
    # Subtle opening SFX: crisp glass/notification chime for whatsapp or deep sub-thump for timer/contrast
    sfx_expr = (
        "sine=frequency=880:duration=0.12"
        if script["visual_type"] == "whatsapp"
        else "sine=frequency=95:duration=0.22"
    )
    subprocess.check_call([
        "ffmpeg", "-y",
        "-i", str(video_no_audio),
        "-i", str(voz_path),
        "-i", str(bgm_path),
        "-f", "lavfi", "-i", sfx_expr,
        "-filter_complex",
        f"[1:a]aformat=sample_rates=44100:channel_layouts=stereo,adelay=180|180,"
        f"highpass=f=85,equalizer=f=3200:t=q:w=1.5:g=3,"
        f"acompressor=threshold=-18dB:ratio=3:attack=5:release=50,volume=1.55,asplit=2[vmain][vsc];"
        f"[2:a]aformat=sample_rates=44100:channel_layouts=stereo,atrim=0:{total_dur},asetpts=PTS-STARTPTS,"
        f"afade=t=in:st=0:d=0.8,afade=t=out:st={fade_out_start}:d=2.4,volume=0.26[bgmraw];"
        f"[bgmraw][vsc]sidechaincompress=threshold=0.04:ratio=4:attack=25:release=320[bgmduck];"
        f"[3:a]aformat=sample_rates=44100:channel_layouts=stereo,afade=t=out:st=0.04:d=0.08,"
        f"volume=0.22,adelay=60|60[sfx];"
        f"[vmain][bgmduck][sfx]amix=inputs=3:duration=first:dropout_transition=2,alimiter=limit=0.95[aout]",
        "-map", "0:v", "-map", "[aout]",
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
        "-movflags", "+faststart",
        "-t", str(total_dur), str(final_path),
    ])

    (BUILD_DIR / "caption.txt").write_text(script["caption"], encoding="utf-8")
    history["posted"].append({
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "topic": script["topic"],
        "visual_type": script["visual_type"],
    })
    save_history(history)
    print("Vídeo v2 CÓDIGO ZERO e legenda gerados com sucesso em build/reel_final.mp4")


if __name__ == "__main__":
    main()

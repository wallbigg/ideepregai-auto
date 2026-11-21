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

# B-roll cinematográfico escuro/atmosférico (combinando com a estética editorial do Código Zero)
BROLL_TOPICS = [
    "rain", "night", "city", "window", "clouds", "sunset",
    "ocean", "coffee", "forest", "stars", "water", "candle",
]
MUSIC_TOPICS = ["piano", "ambient", "cinematic", "sad", "calm"]

# 25 roteiros de alta conversão extraídos diretamente das 23 páginas + Central SOS do CÓDIGO ZERO
CURATED_SCRIPTS = [
    {
        "topic": "Neurociência da Dor Física (Kross 2011)",
        "badge": "CÓDIGO ZERO • CIÊNCIA",
        "pre1": "Não é fraqueza",
        "text1": "Saudade pós-término dói como <span class='red'>queimadura física</span>.",
        "pre2": "O que acontece no cérebro",
        "text2": "A rejeição ativa a mesma área cerebral da <span class='red'>dor real</span>.",
        "pre3": "MÉTODO Z.E.R.O.",
        "text3": "Você não precisa esquecer à força. Só parar de se abandonar.",
        "ref": "Kross et al. • Prot. 14 Dias",
        "pre4": "Retome o comando",
        "text4": "Desligue a abstinência com o <span class='gold'>Código Zero</span>.",
        "cta": "COMENTE ZERO • LINK NA BIO",
        "narration": "Saudade pós-término não é drama nem fraqueza! Pesquisas de ressonância mostram que a rejeição ativa a mesma área cerebral de uma queimadura física. Você não precisa esquecer à força, só precisa de um protocolo real. Comente zero ou clique no link da bio!",
        "caption": "Não é falta de amor-próprio que faz o peito apertar às 23h. É neurobiologia.\n\nEstudos da Universidade de Michigan (Kross et al.) mostraram que a rejeição ativa a mesma rede cerebral de uma dor física real. Por isso conselhos genéricos como 'é só distrair a cabeça' falham.\n\nO Código Zero reúne o Protocolo de 14 Dias, 16 Scripts prontos e a Central SOS no celular para cortar a abstinência sem se humilhar.\n\nComente ZERO ou clique no link da bio para garantir direto no WhatsApp: (12) 99659-3222.",
    },
    {
        "topic": "Regra 90-15 (Trava de Impulso)",
        "badge": "FASE Z • REGRA 90–15",
        "pre1": "Quase mandando mensagem?",
        "text1": "O pico químico da recaída dura só <span class='red'>90 segundos</span>.",
        "pre2": "Por que você se arrepende",
        "text2": "A crise só dura horas porque você alimenta no <span class='red'>WhatsApp</span>.",
        "pre3": "TESTE DAS 9H",
        "text3": "Amanhã às 9h, se eu enviar isso, vou sentir orgulho ou vergonha?",
        "ref": "Protocolo 90–15 • Pág. 06",
        "pre4": "Salve sua dignidade",
        "text4": "Cronômetro de 15 min + descarrego na <span class='gold'>Central SOS</span>.",
        "cta": "COMENTE ZERO • LINK NA BIO",
        "narration": "Quase mandando mensagem pro seu ex agora? Trave o celular! O pico químico de adrenalina dura apenas noventa segundos. A crise só dura horas quando você continua olhando a tela. Espere quinze minutos antes de agir. Quer o cronômetro SOS? Comente zero ou clique no link da bio!",
        "caption": "A dor mais pesada de um término raramente é só a saudade. É a ressaca moral de olhar para trás e ver que você implorou migalhas.\n\nNa Regra 90–15 do Código Zero, você atravessa o pico químico de 90 segundos, descarrega sem enviar na Central SOS e faz o Teste das 9h antes de tocar no celular.\n\nComente ZERO ou clique no link da bio para garantir direto no WhatsApp: (12) 99659-3222.",
    },
    {
        "topic": "Script #01 — Ele mandou 'Oi sumido'",
        "badge": "SCRIPT #01 • ESCUDO",
        "pre1": "Armadilha clássica",
        "text1": "Ele mandou <span class='red'>'oi, tudo bem?'</span> do nada?",
        "pre2": "A intenção oculta",
        "text2": "É teste de ego para ver se você continua no <span class='red'>banco de reservas</span>.",
        "pre3": "REGRA DE OURO",
        "text3": "Responda ao tamanho real do esforço, nunca ao tamanho da sua saudade.",
        "ref": "16 Scripts Escudo • Pág. 10",
        "pre4": "Ação exata",
        "text4": "Silêncio absoluto. Tenha os <span class='gold'>16 scripts</span> prontos no celular.",
        "cta": "COMENTE ZERO • LINK NA BIO",
        "narration": "Ele sumiu e do nada mandou um 'oi, tudo bem'? Isso não é arrependimento! É uma isca de esforço zero para checar se você ainda está disponível no banco de reservas. A resposta certa é silêncio estratégico. Quer os dezesseis scripts prontos? Comente zero ou clique no link da bio!",
        "caption": "Mensagem vazia não merece sua energia nem sua noite de sono.\n\nSe já visualizou por acidente, não escreva nada para 'compensar'. O silêncio digno encerra o acesso fácil sem fazer drama.\n\nNo Código Zero você recebe os 16 Scripts Escudo de Diamante prontos para copiar em 1 clique no celular.\n\nComente ZERO ou clique no link da bio para garantir direto no WhatsApp: (12) 99659-3222.",
    },
    {
        "topic": "A Zona Morta (22h às 02h)",
        "badge": "FASE Z • MADRUGADA",
        "pre1": "Alerta das 23h",
        "text1": "70% das mensagens de arrependimento nascem <span class='red'>depois das 22h</span>.",
        "pre2": "O perigo da cama",
        "text2": "Nenhuma decisão amorosa tomada na horizontal é <span class='red'>lúcida</span>.",
        "pre3": "ESCUDO NOTURNO",
        "text3": "Às 22h30 o celular dorme no carregador fora do alcance da cama.",
        "ref": "Protocolo Madrugada • Pág. 08",
        "pre4": "Blinde suas noites",
        "text4": "Durma em paz com o protocolo <span class='gold'>Código Zero</span>.",
        "cta": "COMENTE ZERO • LINK NA BIO",
        "narration": "Mais de setenta por cento das mensagens de arrependimento acontecem entre dez da noite e duas da manhã. Com o cérebro cansado, a dor dobra e a lucidez some. Regra física: carregador fora da cama às dez e meia. Quer blindar suas noites? Comente zero ou clique no link da bio!",
        "caption": "Força de vontade falha às 23h. Ambiente blindado protege você no piloto automático.\n\nO Código Zero traz o Protocolo da Madrugada completo, 6 Cartões SOS para a tela de bloqueio e a Central Web Interativa para os minutos em que a saudade aperta no escuro.\n\nComente ZERO ou clique no link da bio para garantir direto no WhatsApp: (12) 99659-3222.",
    },
    {
        "topic": "Script #16 — O Botão de Reinício",
        "badge": "SCRIPT #16 • RESGATE",
        "pre1": "Já mandou textão?",
        "text1": "Se humilhou nos últimos dias e sente <span class='red'>vergonha agora</span>?",
        "pre2": "O erro que piora tudo",
        "text2": "Não mande mais dez mensagens tentando <span class='red'>consertar a primeira</span>.",
        "pre3": "BOTÃO DE REINÍCIO",
        "text3": "Falei no calor da emoção. Pensando bem, encerrar foi o melhor. Felicidades.",
        "ref": "Use 1 única vez • Pág. 12",
        "pre4": "Retome a postura",
        "text4": "Depois dessa frase: <span class='gold'>silêncio absoluto</span> e foco em você.",
        "cta": "COMENTE ZERO • LINK NA BIO",
        "narration": "Chorou, mandou textão e agora sente vergonha? Pare! Não mande mais dez mensagens tentando explicar a primeira. Use uma única vez o Botão de Reinício: reconheça que falou no calor da emoção, concorde com o fim e entre em silêncio absoluto. Comente zero ou clique no link da bio!",
        "caption": "Ter tropeçado nos últimos dias não destruiu o seu valor. Continuar tentando consertar no desespero é que drena sua paz.\n\nO Script #16 do Código Zero devolve a última palavra para você com elegância cirúrgica e abre seus 14 dias de reconstrução.\n\nComente ZERO ou clique no link da bio para garantir direto no WhatsApp: (12) 99659-3222.",
    },
    {
        "topic": "Amnésia Seletiva Pós-Término",
        "badge": "FASE R • REALIDADE",
        "pre1": "Por que só lembra do bom?",
        "text1": "Na abstinência, seu cérebro cria uma <span class='red'>amnésia seletiva</span>.",
        "pre2": "O truque da mente",
        "text2": "Ele passa o trailer dos abraços e apaga as noites de <span class='red'>ansiedade</span>.",
        "pre3": "AUTÓPSIA HONESTA",
        "text3": "Você sente falta da pessoa real ou da fantasia que você editou?",
        "ref": "Scorecard 8 Pilares • Pág. 14",
        "pre4": "Enxergue em números",
        "text4": "Calcule a nota real da relação na <span class='gold'>Central Código Zero</span>.",
        "cta": "COMENTE ZERO • LINK NA BIO",
        "narration": "Sabe por que depois do término você só lembra dos momentos perfeitos? Isso se chama amnésia seletiva! Na abstinência, o cérebro edita um trailer só com os abraços e apaga todo o desgaste que te fez chorar. Quer fazer a Autópsia dos 8 Pilares? Comente zero ou clique no link da bio!",
        "caption": "Quando a saudade sussurra 'a gente era perfeito junto', ela está escondendo a metade do filme que doía.\n\nNa Fase R do Código Zero, você usa a Calculadora de 8 Pilares (/80) e o Espelho Retrovisor para trocar ilusão por clareza real.\n\nComente ZERO ou clique no link da bio para garantir direto no WhatsApp: (12) 99659-3222.",
    },
    {
        "topic": "Pico de Extinção (Dia 3)",
        "badge": "CIÊNCIA • DIA 03",
        "pre1": "Por que hoje doeu mais?",
        "text1": "No Dia 3 do contato zero, a dor <span class='red'>sobe antes de cair</span>.",
        "pre2": "Pico de extinção",
        "text2": "É o cérebro gritando mais alto para testar se você vai <span class='red'>ceder</span>.",
        "pre3": "CURVA DE 14 DIAS",
        "text3": "A maioria desiste exatamente no dia em que o hábito estava quebrando.",
        "ref": "Diário 14 Dias • Pág. 17",
        "pre4": "Atravesse o pico",
        "text4": "Acompanhe sua dor cair no gráfico do <span class='gold'>Código Zero</span>.",
        "cta": "COMENTE ZERO • LINK NA BIO",
        "narration": "Sabe por que a maioria recai no terceiro dia de contato zero? Porque na psicologia existe o pico de extinção! O cérebro grita mais alto exatamente antes de soltar o hábito. Se doeu mais hoje, é sinal de que está funcionando. Quer o mapa dos catorze dias? Comente zero ou clique no link da bio!",
        "caption": "Dicas soltas não funcionam porque ninguém te avisa o que vai sentir no Dia 3.\n\nCom o Diário Operável de 14 Dias e o gráfico ao vivo na Central SOS do Código Zero, você vê sua dor descer dia após dia até recuperar sua paz.\n\nComente ZERO ou clique no link da bio para garantir direto no WhatsApp: (12) 99659-3222.",
    },
    {
        "topic": "Script #08 — 'Sonhei com você'",
        "badge": "SCRIPT #08 • ESCUDO",
        "pre1": "Nostalgia vaga",
        "text1": "Ele mandou <span class='red'>'sonhei com você'</span> sem pedir volta?",
        "pre2": "Não caia na isca",
        "text2": "Quer testar se você derrete sem oferecer <span class='red'>compromisso nenhum</span>.",
        "pre3": "RESPOSTA ELEGANTE",
        "text3": "Fico feliz pelas boas lembranças. Hoje prefiro manter meu espaço. Se cuida.",
        "ref": "Escudo de Diamante • Pág. 11",
        "pre4": "Zero drama",
        "text4": "Se queria ego, sai desarmado. Pegue os <span class='gold'>16 scripts</span> prontos.",
        "cta": "COMENTE ZERO • LINK NA BIO",
        "narration": "Recebeu um 'sonhei com você' ou 'passei naquele lugar e lembrei da gente'? Calma! Isso testa se você derrete com nostalgia sem ele oferecer nada concreto. Responda educado, curto e feche a porta: 'fico feliz pelas boas lembranças, hoje prefiro manter meu espaço'. Comente zero ou clique no link da bio!",
        "caption": "Quem quer voltar de verdade fala com clareza, não com charadas nostálgicas.\n\nEssa resposta do Script #08 do Código Zero mantém sua classe intacta: se era apenas massagem no ego, acaba ali na hora.\n\nComente ZERO ou clique no link da bio para garantir direto no WhatsApp: (12) 99659-3222.",
    },
    {
        "topic": "Suspiro Duplo (Balban & Huberman 2023)",
        "badge": "FASE Z • RESET 120s",
        "pre1": "Peito apertando agora?",
        "text1": "Tentar pensar positivo não funciona com o corpo em <span class='red'>pânico</span>.",
        "pre2": "Reset fisiológico",
        "text2": "Faça 5 ciclos do <span class='gold'>Suspiro Duplo</span>: duas puxadas e solte lento.",
        "pre3": "CIÊNCIA REAL",
        "text3": "Água fria no rosto mais cinco suspiros duplos freiam o alerta em 2 minutos.",
        "ref": "Balban et al., 2023 • Pág. 07",
        "pre4": "Guia ao vivo no celular",
        "text4": "Use a respiração animada na <span class='gold'>Central SOS</span>.",
        "cta": "COMENTE ZERO • LINK NA BIO",
        "narration": "Quando o peito aperta de saudade, tentar pensar positivo não funciona porque seu corpo está em modo de ameaça! Jogue água fria no rosto e faça cinco suspiros duplos: puxa longo pelo nariz, mais uma puxadinha curta e solta devagar pela boca. Quer a Central SOS? Comente zero ou clique no link da bio!",
        "caption": "Primeiro você acalma o sistema nervoso; só depois você decide qualquer coisa.\n\nA Central SOS do Código Zero tem o guia visual animado de Suspiro Duplo (baseado no estudo de Balban et al., 2023) para usar na palma da mão em 2 minutos.\n\nComente ZERO ou clique no link da bio para garantir direto no WhatsApp: (12) 99659-3222.",
    },
    {
        "topic": "Script #11 — 'Podemos continuar amigos?'",
        "badge": "SCRIPT #11 • LIMITES",
        "pre1": "Proposta perigosa",
        "text1": "Ele terminou e pediu para <span class='red'>continuarem amigos</span>?",
        "pre2": "A armadilha real",
        "text2": "Quer manter seu apoio emocional enquanto fica <span class='red'>livre sem culpa</span>.",
        "pre3": "LIMITE MADURO",
        "text3": "Agradeço, mas agora preciso de distância real para seguir em paz.",
        "ref": "16 Scripts Prontos • Pág. 12",
        "pre4": "Proteja seu coração",
        "text4": "Dizer não sem rancor é o ápice da <span class='gold'>maturidade</span>.",
        "cta": "COMENTE ZERO • LINK NA BIO",
        "narration": "Ele terminou mas perguntou se vocês podem continuar amigos? Cuidado! Isso quase sempre serve para manter seus benefícios emocionais enquanto ele segue livre sem compromisso. Responda com firmeza e sem rancor: agora preciso de distância real para seguir em paz. Comente zero ou clique no link da bio!",
        "caption": "Proteger o próprio coração não é imaturidade nem vingança, é respeito próprio.\n\nNo Código Zero você tem respostas maduras e prontas para cada situação difícil do pós-término, sem perder a elegância.\n\nComente ZERO ou clique no link da bio para garantir direto no WhatsApp: (12) 99659-3222.",
    },
    {
        "topic": "Vontade de Stalkear (SOS 04)",
        "badge": "CARTÃO SOS • #04",
        "pre1": "Mão indo na lupa?",
        "text1": "Cada olhada no perfil reinicia sua dor para o <span class='red'>Dia Zero</span>.",
        "pre2": "A verdade dura",
        "text2": "Se estiver bem sem você, vai doer. Se estiver triste, vai <span class='red'>iludir</span>.",
        "pre3": "CORTE O LOOP",
        "text3": "Silencie stories e posts hoje. A pessoa nem é notificada.",
        "ref": "7 Gatilhos Invisíveis • Pág. 06",
        "pre4": "Feche essa ferida",
        "text4": "Baixe os 6 Cartões SOS + <span class='gold'>Código Zero</span>.",
        "cta": "COMENTE ZERO • LINK NA BIO",
        "narration": "Antes de entrar no perfil do seu ex, faça uma pergunta simples: o que você espera achar lá? Se estiver bem sem você, vai doer. Se parecer triste, vai te iludir! Cada espiada reinicia sua abstinência para o dia zero. Silencie hoje! Comente zero ou clique no link da bio!",
        "caption": "Olhar o perfil nunca trouxe paz. Só entrega mais uma dose para o ciclo da abstinência.\n\nO Código Zero vem com 6 Cartões SOS em Full HD para salvar na galeria e abrir exatamente nos 5 minutos em que o impulso bate.\n\nComente ZERO ou clique no link da bio para garantir direto no WhatsApp: (12) 99659-3222.",
    },
    {
        "topic": "Script #09 — Mensagem de Madrugada",
        "badge": "SCRIPT #09 • TRAVA 12H",
        "pre1": "Celular vibrou 1h30?",
        "text1": "Responder mensagem de madrugada garante <span class='red'>gelo no dia seguinte</span>.",
        "pre2": "Carência não é escolha",
        "text2": "Álcool e solidão às duas da manhã não são <span class='red'>decisão de vida</span>.",
        "pre3": "TRAVA DE 12 HORAS",
        "text3": "Só responda no dia seguinte: Vi agora. Espero que esteja bem. Se cuida.",
        "ref": "Escudo de Diamante • Pág. 11",
        "pre4": "Preserve seu valor",
        "text4": "Nunca esteja disponível no horário da <span class='gold'>carência</span>.",
        "cta": "COMENTE ZERO • LINK NA BIO",
        "narration": "O celular vibrou uma e meia da manhã com mensagem do ex? Jamais responda na hora! Carência da madrugada ou bebida não é decisão de vida, e quem responde na hora quase sempre leva gelo no dia seguinte. Ative a trava de doze horas! Comente zero ou clique no link da bio!",
        "caption": "Quem só lembra de você de madrugada não está propondo reconstrução, está procurando alívio momentâneo.\n\nCom o Fluxograma de Decisão do Código Zero, você sabe em 15 segundos o que responder (ou quando ficar em silêncio).\n\nComente ZERO ou clique no link da bio para garantir direto no WhatsApp: (12) 99659-3222.",
    },
    {
        "topic": "Os 5 Critérios Inegociáveis (Volta Real vs Ego)",
        "badge": "FASE O • 5 CRITÉRIOS",
        "pre1": "Ele quer voltar?",
        "text1": "Nunca decida reatar no pico da <span class='red'>abstinência</span>.",
        "pre2": "Filtro anti-migalha",
        "text2": "Saudade e química não provam que a causa do fim <span class='red'>mudou</span>.",
        "pre3": "QUARENTENA DE 14 DIAS",
        "text3": "Uma escolha feita na carência quase nunca resiste a trinta dias de realidade.",
        "ref": "5 Critérios Inegociáveis • Pág. 16",
        "pre4": "Decida com lucidez",
        "text4": "Passe a relação no checklist do <span class='gold'>Código Zero</span>.",
        "cta": "COMENTE ZERO • LINK NA BIO",
        "narration": "Ele reapareceu dizendo que quer conversar? Calma! Nunca decida reatar antes de completar catorze dias de lucidez. Saudade e química não provam mudança real. A causa do término foi tratada? Existe consistência por semanas? Comente zero ou clique no link da bio!",
        "caption": "O Código Zero não decide por você, ele garante que você decida com lucidez adulta e não com medo de ficar sozinho(a).\n\nAntes de abrir a porta de novo, passe nos 5 Critérios Inegociáveis da Página 16.\n\nComente ZERO ou clique no link da bio para garantir direto no WhatsApp: (12) 99659-3222.",
    },
    {
        "topic": "Efeito Rebote & Janela Controlada (Borkovec 1983)",
        "badge": "FASE Z • MENTE EM PAZ",
        "pre1": "Looping mental 24h?",
        "text1": "Quanto mais você tenta <span class='red'>não pensar</span>, mais a imagem volta.",
        "pre2": "Efeito rebote",
        "text2": "A saída não é proibir o pensamento, é <span class='gold'>marcar hora para ele</span>.",
        "pre3": "JANELA CONTROLADA",
        "text3": "Reserve 15 minutos às 18h30. Fora da hora, adie e volte para sua vida.",
        "ref": "Borkovec et al. • Pág. 08",
        "pre4": "Desligue a ruminação",
        "text4": "Aplique o método científico do <span class='gold'>Código Zero</span>.",
        "cta": "COMENTE ZERO • LINK NA BIO",
        "narration": "Já percebeu que quanto mais você manda sua mente esquecer, mais você pensa na pessoa? Na psicologia isso é o efeito rebote. A solução clínica é a Janela Controlada: marque quinze minutos fixos do dia para sentir tudo e, fora dessa hora, adie o pensamento. Comente zero ou clique no link da bio!",
        "caption": "Brigar com os próprios pensamentos o dia inteiro só esgota sua energia.\n\nInspirada no controle de estímulo de Borkovec, a Janela Controlada da Página 08 devolve seu foco no trabalho e nos estudos já na primeira semana.\n\nComente ZERO ou clique no link da bio para garantir direto no WhatsApp: (12) 99659-3222.",
    },
    {
        "topic": "Script #02 — Curtida em Foto Antiga",
        "badge": "SCRIPT #02 • ESCUDO",
        "pre1": "Isca silenciosa",
        "text1": "Curtida em foto antiga não é <span class='red'>pedido de volta</span>.",
        "pre2": "Por que ele fez isso",
        "text2": "É um clique de 1 segundo para fazer você puxar <span class='red'>assunto primeiro</span>.",
        "pre3": "POSTURA DE VALOR",
        "text3": "Ignore completamente. Não curta de volta e não poste indireta.",
        "ref": "16 Scripts Prontos • Pág. 10",
        "pre4": "Corte a provocação",
        "text4": "Domine todas as iscas com o <span class='gold'>Código Zero</span>.",
        "cta": "COMENTE ZERO • LINK NA BIO",
        "narration": "Ele curtiu uma foto sua antiga ou reagiu ao seu story? Não se iluda! Um clique de um segundo serve só para entrar na sua cabeça e provocar iniciativa sua. Ignorar completamente tira todo o poder da provocação na hora. Comente zero ou clique no link da bio!",
        "caption": "Curtida não é conversa, não é pedido de desculpas e não é compromisso.\n\nNo Código Zero você aprende a ler o esforço real por trás de cada sinal e nunca mais entrega seu equilíbrio por uma notificação.\n\nComente ZERO ou clique no link da bio para garantir direto no WhatsApp: (12) 99659-3222.",
    },
    {
        "topic": "Silêncio Digital de 7 Dias",
        "badge": "FASE E • SILÊNCIO",
        "pre1": "Pare o teatro nos stories",
        "text1": "Postar indireta ou forçar festa prova que ainda <span class='red'>dói muito</span>.",
        "pre2": "O que realmente impõe respeito",
        "text2": "Sete dias de <span class='gold'>silêncio digital</span> valem mais que mil legendas.",
        "pre3": "REGRA DOS 7 DIAS",
        "text3": "Zero stories, zero música triste, zero indireta. No Dia 8, volte leve.",
        "ref": "Escudo Digital • Pág. 12",
        "pre4": "Paz verdadeira",
        "text4": "Saia do palco e retome sua vida no <span class='gold'>Código Zero</span>.",
        "cta": "COMENTE ZERO • LINK NA BIO",
        "narration": "Postar música triste, frase indireta ou forçar balada para provocar ciúme só mostra que você ainda está sofrendo! Sabe o que realmente impõe respeito e acalma sua mente? Sete dias de silêncio digital absoluto. Sem stories, sem palco. Comente zero ou clique no link da bio!",
        "caption": "Quando você para de postar esperando uma única visualização, a ansiedade cai pela metade.\n\nO Silêncio Digital de 7 Dias é uma das chaves do Protocolo Código Zero para desligar a espera compulsiva pelo celular.\n\nComente ZERO ou clique no link da bio para garantir direto no WhatsApp: (12) 99659-3222.",
    },
    {
        "topic": "Script #05 — Devolver Coisas sem Recair",
        "badge": "SCRIPT #05 • LOGÍSTICA",
        "pre1": "A maior porta de recaída",
        "text1": "Devolver objetos em casa quase sempre vira <span class='red'>recaída emocional</span>.",
        "pre2": "Postura executiva",
        "text2": "Não transforme uma entrega simples em um encontro <span class='red'>a sós</span>.",
        "pre3": "COPIE E COLE",
        "text3": "Já deixei tudo separado. Posso deixar na portaria ou mandar por entregador.",
        "ref": "Script #05 • Pág. 10",
        "pre4": "Corte o gatilho",
        "text4": "Resolva com classe usando os <span class='gold'>16 scripts</span> do kit.",
        "cta": "COMENTE ZERO • LINK NA BIO",
        "narration": "Ele mandou mensagem perguntando quando pode passar aí para pegar as coisas? Cuidado! A entrega de objetos dentro de casa é a maior porta de recaída pós-término. Seja educado e prático: deixe separado na portaria ou envie por entregador. Comente zero ou clique no link da bio!",
        "caption": "Educação não exige abrir a porta de casa para reabrir uma ferida.\n\nO Script #05 resolve a logística com elegância e protege os seus 14 dias de paz.\n\nComente ZERO ou clique no link da bio para garantir direto no WhatsApp: (12) 99659-3222.",
    },
    {
        "topic": "Script #10 — 'Já me esqueceu, né?'",
        "badge": "SCRIPT #10 • PROVOCAÇÃO",
        "pre1": "Inversão de culpa",
        "text1": "Ele disse <span class='red'>'pelo visto você superou rápido'</span>?",
        "pre2": "O objetivo dessa frase",
        "text2": "Usar culpa para fazer você se justificar e provar que ainda <span class='red'>sofre</span>.",
        "pre3": "DESARME EM 1 LINHA",
        "text3": "Não guardo mágoa. Estou apenas respeitando o fim do nosso ciclo.",
        "ref": "Script #10 • Pág. 11",
        "pre4": "Serenidade impõe respeito",
        "text4": "Sem raiva, sem textão. Pegue o <span class='gold'>Código Zero</span> completo.",
        "cta": "COMENTE ZERO • LINK NA BIO",
        "narration": "Quando você finalmente fica firme, ele solta: 'já me esqueceu, né? Superou rápido'. Isso é armadilha para te fazer correr atrás se justificando! Desarme em uma linha: 'não guardo mágoa, estou apenas respeitando o fim do nosso ciclo'. Comente zero ou clique no link da bio!",
        "caption": "Raiva e deboche provam que ainda dói. Serenidade curta devolve o respeito para o seu lado na hora.\n\nTenha todas as respostas na palma da mão com o Protocolo Código Zero + Central SOS Web.\n\nComente ZERO ou clique no link da bio para garantir direto no WhatsApp: (12) 99659-3222.",
    },
    {
        "topic": "Script #13 — Ex Com Outra Pessoa nas Redes",
        "badge": "SCRIPT #13 • EMERGÊNCIA",
        "pre1": "Soco no estômago",
        "text1": "Ele apareceu com <span class='red'>outra pessoa</span> nas redes sociais?",
        "pre2": "O erro fatal",
        "text2": "Mandar mensagem com raiva ou postar indireta só expõe sua <span class='red'>dor</span>.",
        "pre3": "BLINDAGEM IMEDIATA",
        "text3": "A única reação que preserva seu valor intacto é nenhuma reação visível.",
        "ref": "Reset 120s + SOS • Pág. 12",
        "pre4": "Você vai atravessar isso",
        "text4": "Silencie amigos-ponte e ative a <span class='gold'>Central SOS</span> agora.",
        "cta": "COMENTE ZERO • LINK NA BIO",
        "narration": "Ver o ex aparecendo com outra pessoa nas redes parece um soco no estômago! Mas escuta: mandar mensagem furiosa ou postar indireta só destrói a sua paz. A única reação que preserva seu valor intacto é nenhuma reação visível. Silencie tudo e faça o reset. Comente zero ou clique no link da bio!",
        "caption": "Não deixe um clique impulsivo de raiva custar semanas da sua dignidade.\n\nO Código Zero entrega o passo a passo exato de emergência para momentos assim, com Reset Fisiológico de 120s e Central SOS no celular.\n\nComente ZERO ou clique no link da bio para garantir direto no WhatsApp: (12) 99659-3222.",
    },
    {
        "topic": "Ressonância Cerebral da Rejeição (Fisher 2010)",
        "badge": "CIÊNCIA • ABSTINÊNCIA",
        "pre1": "Não é 'amor demais'",
        "text1": "Olhar a foto do ex dispara o mesmo circuito da <span class='red'>fissura química</span>.",
        "pre2": "Descoberta científica",
        "text2": "Seu cérebro não pede amor: ele cobra a próxima <span class='red'>dose de dopamina</span>.",
        "pre3": "DESMAME EM 14 DIAS",
        "text3": "Corte os estímulos por 14 dias e a urgência perde força biológica.",
        "ref": "Fisher et al., 2010 • Pág. 04",
        "pre4": "Liberdade real",
        "text4": "Faça o desmame guiado com o <span class='gold'>Código Zero</span>.",
        "cta": "COMENTE ZERO • LINK NA BIO",
        "narration": "Não é 'amor demais' que faz você checar o celular vinte vezes por dia! Em ressonâncias cerebrais, Helen Fisher provou que a foto do ex ativa os mesmos circuitos de fissura das dependências químicas. É desmame, não fraqueza. Quer o protocolo de 14 dias? Comente zero ou clique no link da bio!",
        "caption": "Entender o que acontece no seu cérebro tira o peso da culpa e devolve o controle para suas mãos.\n\nO Código Zero transforma neurociência aplicada em um plano diário simples de 14 dias com Central Web Interativa.\n\nComente ZERO ou clique no link da bio para garantir direto no WhatsApp: (12) 99659-3222.",
    },
    {
        "topic": "Índice de Sequestro Emocional (0–30)",
        "badge": "PASSO ZERO • DIAGNÓSTICO",
        "pre1": "Faça o teste mental",
        "text1": "Você checa o celular <span class='red'>antes mesmo de levantar</span> da cama?",
        "pre2": "Sinal de Sequestro Agudo",
        "text2": "Se seu humor do dia depende de um sinal dele, você está no <span class='red'>Nível 3</span>.",
        "pre3": "MEDIR PARA CURAR",
        "text3": "Meça seu índice no Dia 01 e veja a pontuação despencar no Dia 14.",
        "ref": "Calculadora 0–30 • Pág. 03",
        "pre4": "Saia do Nível 3",
        "text4": "Calcule seu nível na <span class='gold'>Central SOS Código Zero</span>.",
        "cta": "COMENTE ZERO • LINK NA BIO",
        "narration": "Responde com sinceridade: você acorda checando o celular esperando mensagem? Seu humor do dia inteiro depende de um sinal dele? Esses são sinais clássicos do Nível Três de Sequestro Emocional. No Código Zero você mede sua nota hoje e acompanha cair em catorze dias. Comente zero ou clique no link da bio!",
        "caption": "Você não consegue vencer um inimigo que não consegue medir.\n\nNa Central SOS do Código Zero você calcula seu Índice de Sequestro Emocional (0 a 30) em 1 minuto e recebe a rota exata para o seu nível.\n\nComente ZERO ou clique no link da bio para garantir direto no WhatsApp: (12) 99659-3222.",
    },
    {
        "topic": "As 3 Regras de Ouro da Comunicação",
        "badge": "FASE E • 3 REGRAS",
        "pre1": "Antes de responder",
        "text1": "Três regras simples que salvam sua <span class='gold'>dignidade</span> hoje.",
        "pre2": "Anote agora",
        "text2": "Zero textão, zero pergunta aberta e <span class='red'>zero ironia</span>.",
        "pre3": "POSTURA INABALÁVEL",
        "text3": "Nunca escreva mais linhas do que a mensagem que você recebeu.",
        "ref": "Fluxograma • Pág. 09",
        "pre4": "Controle a conversa",
        "text4": "Tenha o Fluxograma + 16 Scripts no <span class='gold'>Código Zero</span>.",
        "cta": "COMENTE ZERO • LINK NA BIO",
        "narration": "Ele mandou mensagem? Siga três regras antes de digitar: primeiro, zero textão — nunca escreva mais linhas do que recebeu. Segundo, zero pergunta aberta como 'e você, como tá?'. Terceiro, zero ironia — serenidade curta impõe respeito. Comente zero ou clique no link da bio!",
        "caption": "Perguntas abertas reabrem a espera ansiosa pela resposta. Ironia prova que ainda dói.\n\nCom o Fluxograma da Página 09 do Código Zero, você decide em 15 segundos exatamente como agir.\n\nComente ZERO ou clique no link da bio para garantir direto no WhatsApp: (12) 99659-3222.",
    },
    {
        "topic": "Queimar Mensagem Sem Enviar (Central SOS)",
        "badge": "CENTRAL SOS • APP WEB",
        "pre1": "Preso na garganta?",
        "text1": "A emoção precisa sair, mas <span class='red'>não precisa ir pro WhatsApp</span>.",
        "pre2": "Descarrego seguro",
        "text2": "Escreva tudo sem filtro e <span class='gold'>queime a mensagem</span> na tela.",
        "pre3": "ZERO ARREPENDIMENTO",
        "text3": "Você alivia o peito agora e acorda amanhã com orgulho de si mesmo.",
        "ref": "App Web Incluso • Código Zero",
        "pre4": "No seu celular 24h",
        "text4": "Tenha a Central SOS + PDF + Cartões no <span class='gold'>Código Zero</span>.",
        "cta": "COMENTE ZERO • LINK NA BIO",
        "narration": "Tá com um textão entalado na garganta querendo despejar tudo? Escuta: a emoção precisa sair, mas não precisa ir pro WhatsApp do seu ex! Na Central SOS do Código Zero você escreve tudo sem filtro e queima a mensagem ali na tela, sem arrependimento amanhã. Comente zero ou clique no link da bio!",
        "caption": "Além do Protocolo Editorial de 23 páginas, o Código Zero entrega um Aplicativo Web Interativo no seu celular: Cronômetro 15 min, Respiração Guiada, 16 Scripts em 1 clique e botão Queimar Mensagem.\n\nComente ZERO ou clique no link da bio para garantir direto no WhatsApp: (12) 99659-3222.",
    },
    {
        "topic": "A Carta de Alforria (Dia 09)",
        "badge": "FASE R • DIA 09",
        "pre1": "Ferida sem fechamento",
        "text1": "A dor não resolvida fica procurando um <span class='red'>destinatário</span>.",
        "pre2": "O ritual do Dia 9",
        "text2": "Escreva a <span class='gold'>Carta de Alforria</span> em 4 blocos — e jamais envie.",
        "pre3": "ENCERRAMENTO REAL",
        "text3": "Quem partiu levou um capítulo da sua história, jamais o seu valor.",
        "ref": "Protocolo 14 Dias • Pág. 15",
        "pre4": "Vire a página",
        "text4": "Comece seu Dia 01 hoje com o <span class='gold'>Código Zero</span>.",
        "cta": "COMENTE ZERO • LINK NA BIO",
        "narration": "Sabe por que você ainda quer mandar mensagem mesmo sabendo que acabou? Porque a dor sem fechamento fica procurando um destinatário. No Dia Nove do Código Zero, você escreve a Carta de Alforria em quatro blocos e encerra o ciclo sem entregar energia a quem partiu. Comente zero ou clique no link da bio!",
        "caption": "Verdade não dita, peso devolvido, autoperdão e novo limite: os 4 blocos que libertam você sem precisar da validação do ex.\n\nComece hoje o seu protocolo de 14 dias.\n\nComente ZERO ou clique no link da bio para garantir direto no WhatsApp: (12) 99659-3222.",
    },
    {
        "topic": "Protocolo Pós-Recaída (Zero Culpa)",
        "badge": "CONSOLIDAÇÃO • RECAÍDA",
        "pre1": "Stalkeou ontem à noite?",
        "text1": "Uma recaída não apaga tudo o que você <span class='gold'>construiu</span>.",
        "pre2": "O perigo da culpa",
        "text2": "A vergonha é o gatilho que faz você desistir e <span class='red'>voltar pro zero</span>.",
        "pre3": "4 PASSOS DE RETOMADA",
        "text3": "Sem segunda mensagem. Anote o gatilho e retome de onde parou.",
        "ref": "Protocolo Pós-Recaída • Pág. 20",
        "pre4": "Volte ao comando",
        "text4": "Tenha o kit completo sempre à mão: <span class='gold'>Código Zero</span>.",
        "cta": "COMENTE ZERO • LINK NA BIO",
        "narration": "Stalkeou o perfil ontem ou mandou mensagem no impulso? Respire! Isso não apaga o que você já construiu. O maior perigo agora é a culpa te fazer desistir. Regra simples: não mande uma segunda mensagem, anote o gatilho e retome hoje mesmo. Comente zero ou clique no link da bio!",
        "caption": "Tratar a si mesmo(a) com firmeza e sem autoflagelo é o que sustenta a mudança de verdade.\n\nNo Código Zero você tem o Protocolo Pós-Recaída, 5 Prompts de IA 24h e a Central SOS sempre prontos no celular.\n\nComente ZERO ou clique no link da bio para garantir direto no WhatsApp: (12) 99659-3222.",
    },
]


def load_history() -> dict:
    if HISTORY_FILE.exists():
        return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    return {"posted": []}


def save_history(data: dict) -> None:
    HISTORY_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def generate_script(posted_topics: list[str]) -> dict:
    """Gera roteiro viral inédito do CÓDIGO ZERO via Gemini API ou usa acervo curado do produto."""
    if GEMINI_API_KEY:
        recent = posted_topics[-30:]
        prompt = f"""
Você é um estrategista de Reels virais e copywriter do produto digital CÓDIGO ZERO (O Protocolo Imersivo de 14 Dias para superar término, desligar abstinência afetiva, parar de se humilhar por migalhas e retomar a paz).
O kit inclui: PDF editorial de 23 páginas (Método Z.E.R.O., Regra 90-15, Suspiro Duplo, 7 Gatilhos Invisíveis, Janela Controlada, Fluxograma de Mensagens, 16 Scripts Escudo de Diamante, Autópsia dos 8 Pilares, Carta de Alforria, 5 Critérios Inegociáveis, Diário 14 Dias), Web App Interativo "Central SOS" (cronômetro 15min, respiração animada, queimar mensagem, calculadoras), 6 Cartões SOS 9:16 e 5 Prompts de IA 24h.
O cliente compra pelo WhatsApp {WHATSAPP_DISPLAY} (link na bio) ou comentando ZERO.

Crie um Reel de 15 a 18 segundos sobre um ângulo DIFERENTE destes já postados: {recent}.
Regras obrigatórias (ig-reel + ig-human):
- Português do Brasil natural, firme, acolhedor e direto (ZERO clichês de IA, ZERO travessões "—", ZERO "pare de rolar", ZERO "não é X, é Y" batido).
- Comece com um gancho forte que prenda nos primeiros 2 segundos (situação real de pós-término, mensagem do ex, madrugada, stalkear, ciência da abstinência).
- Termine levando a pessoa a comentar ZERO ou clicar no link da bio (WhatsApp {WHATSAPP_DISPLAY}).
- Retorne APENAS JSON válido neste formato exato:
{{
  "topic": "Nome curto do tema/ângulo",
  "badge": "TAG CURTA EM MAIÚSCULO (ex: FASE Z • REGRA 90–15)",
  "pre1": "subtítulo curto 1 (2-4 palavras)",
  "text1": "Gancho forte com <span class='red'>destaque</span> (max 9 palavras)",
  "pre2": "subtítulo curto 2",
  "text2": "Verdade ou mecanismo real com <span class='red'>destaque</span> (max 10 palavras)",
  "pre3": "A CHAVE / REGRA",
  "text3": "Frase de alto impacto ou script prático curto (max 13 palavras)",
  "ref": "Referência curta do Código Zero (ex: Script #08 • Pág. 11)",
  "pre4": "subtítulo curto 4",
  "text4": "Chamada clara para o <span class='gold'>Código Zero</span> (max 9 palavras)",
  "cta": "COMENTE ZERO • LINK NA BIO",
  "narration": "Texto falado natural para dublagem em voz alta (32 a 42 palavras, emotivo e firme, terminando com Comente zero ou clique no link da bio!)",
  "caption": "Legenda humana e magnética para Instagram (3 parágrafos curtos, sem travessões, terminando com: Comente ZERO ou clique no link da bio para garantir direto no WhatsApp: {WHATSAPP_DISPLAY}.)"
}}
"""
        body = json.dumps({
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseMimeType": "application/json", "temperature": 0.85},
        }).encode("utf-8")

        for model in ["gemini-3.8-flash", "gemini-flash-latest", "gemini-flash-lite-latest"]:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
            for attempt in range(2):
                try:
                    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
                    with urllib.request.urlopen(req, timeout=18) as resp:
                        res = json.loads(resp.read().decode("utf-8"))
                    raw = res["candidates"][0]["content"]["parts"][0]["text"]
                    parsed = json.loads(raw)
                    required = (
                        "topic", "badge", "pre1", "text1", "pre2", "text2",
                        "pre3", "text3", "ref", "pre4", "text4", "cta", "narration", "caption",
                    )
                    if all(parsed.get(k) for k in required):
                        print(f"Roteiro Código Zero gerado via Gemini ({model})!")
                        return parsed
                except Exception as exc:
                    print(f"Tentativa {attempt + 1} em {model} falhou: {exc}")
                    time.sleep(3)

    print("Usando roteiro curado do acervo Código Zero...")
    available = [s for s in CURATED_SCRIPTS if s["topic"] not in posted_topics]
    if not available:
        last_topics = set(posted_topics[-15:])
        available = [s for s in CURATED_SCRIPTS if s["topic"] not in last_topics] or CURATED_SCRIPTS
    return random.choice(available)


def fetch_mixkit_asset(topics: list[str], base_url: str, pattern: str, out_path: Path) -> str:
    curl_bin = shutil.which("curl.exe") or shutil.which("curl") or "curl"
    shuffled = topics[:]
    random.shuffle(shuffled)
    for topic in shuffled:
        page_url = f"{base_url}/{topic}/"
        try:
            html = subprocess.check_output(
                [curl_bin, "-sL", "--max-time", "20", "-A", "Mozilla/5.0", page_url]
            ).decode("utf-8", errors="ignore")
            matches = list(dict.fromkeys(re.findall(pattern, html)))
            if matches:
                chosen = random.choice(matches[:25])
                subprocess.check_call([curl_bin, "-sL", "--max-time", "45", "-o", str(out_path), chosen])
                if out_path.exists() and out_path.stat().st_size > 20_000:
                    return chosen
        except Exception as exc:
            print(f"Aviso ao baixar mídia de {page_url}: {exc}")
    raise RuntimeError(f"Não foi possível baixar mídia válida de {base_url}")


def main() -> None:
    history = load_history()
    posted_topics = [item.get("topic") or item.get("verse", "") for item in history.get("posted", [])]

    print("1. Gerando roteiro CÓDIGO ZERO...")
    script = generate_script(posted_topics)
    print("Tema escolhido:", script["topic"])

    print("2. Gerando dublagem expressiva...")
    voz_path = BUILD_DIR / "voz.mp3"
    tts_prefix = ["edge-tts"] if shutil.which("edge-tts") else ["uvx", "edge-tts"]
    subprocess.check_call(tts_prefix + [
        "--voice", VOICE, "--rate=+4%", "--pitch=+1Hz",
        "--text", script["narration"], "--write-media", str(voz_path),
    ])
    dur = float(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(voz_path),
    ]).decode().strip())
    total_dur = max(15.0, round(dur + 0.9, 1))

    print(f"3. Baixando B-roll escuro/atmosférico e trilha real (duração {total_dur}s)...")
    broll_path = BUILD_DIR / "broll.mp4"
    bgm_path = BUILD_DIR / "bgm.mp3"
    broll_url = fetch_mixkit_asset(
        BROLL_TOPICS,
        "https://mixkit.co/free-stock-video",
        r"https://assets\.mixkit\.co/videos/[^\s\"'<>]+\.mp4",
        broll_path,
    )
    bgm_url = fetch_mixkit_asset(
        MUSIC_TOPICS,
        "https://mixkit.co/free-stock-music",
        r"https://assets\.mixkit\.co/music/[^\s\"'<>]+\.mp3",
        bgm_path,
    )
    print("B-roll:", broll_url, "| Trilha:", bgm_url)

    print("4. Montando composição HyperFrames (Estética Código Zero)...")
    hf_dir = BUILD_DIR / "hf_proj"
    hf_dir.mkdir(exist_ok=True)
    d1 = round(total_dur * 0.24, 2)
    d2 = round(total_dur * 0.24, 2)
    d3 = round(total_dur * 0.28, 2)
    d4 = round(total_dur - d1 - d2 - d3, 2)
    s2, s3, s4 = d1, round(d1 + d2, 2), round(d1 + d2 + d3, 2)

    html = (ROOT / "template.html").read_text(encoding="utf-8")
    replacements = {
        "__DURATION__": str(total_dur),
        "__D1__": str(d1), "__D2__": str(d2), "__D3__": str(d3), "__D4__": str(d4),
        "__S2__": str(s2), "__S3__": str(s3), "__S4__": str(s4),
        "__BADGE__": script["badge"],
        "__PRE1__": script["pre1"], "__TEXT1__": script["text1"],
        "__PRE2__": script["pre2"], "__TEXT2__": script["text2"],
        "__PRE3__": script["pre3"], "__TEXT3__": script["text3"],
        "__REF__": script["ref"],
        "__PRE4__": script["pre4"], "__TEXT4__": script["text4"],
        "__CTA__": script["cta"],
    }
    for k, v in replacements.items():
        html = html.replace(k, v)
    (hf_dir / "index.html").write_text(html, encoding="utf-8")

    motion_path = BUILD_DIR / "motion.mp4"
    hf_cmd = (
        ["cmd", "/c", "npx", "--yes", "hyperframes", "render", ".", "--output", str(motion_path)]
        if os.name == "nt"
        else ["npx", "--yes", "hyperframes", "render", ".", "--output", str(motion_path)]
    )
    subprocess.check_call(hf_cmd, cwd=str(hf_dir))

    print("5. Compondo B-roll + Motion Código Zero + Voz + Piano no FFmpeg...")
    final_path = BUILD_DIR / "reel_final.mp4"
    fade_out_start = max(1.0, total_dur - 2.5)
    subprocess.check_call([
        "ffmpeg", "-y", "-stream_loop", "-1", "-i", str(broll_path),
        "-i", str(motion_path), "-i", str(voz_path), "-i", str(bgm_path),
        "-filter_complex",
        f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,"
        f"eq=brightness=-0.34:contrast=1.08:saturation=0.72,trim=0:{total_dur},setpts=PTS-STARTPTS[bg];"
        f"[1:v]colorkey=0x060508:0.12:0.15,setpts=PTS-STARTPTS[fg];"
        f"[bg][fg]overlay=0:0:shortest=1[vout];"
        f"[3:a]atrim=0:{total_dur},asetpts=PTS-STARTPTS,afade=t=in:st=0:d=1.0,"
        f"afade=t=out:st={fade_out_start}:d=2.5,volume=0.18[bgm];"
        f"[2:a]adelay=200|200,acompressor=threshold=-18dB:ratio=3:attack=5:release=50,volume=1.48[v];"
        f"[v][bgm]amix=inputs=2:duration=first:dropout_transition=2[aout]",
        "-map", "[vout]", "-map", "[aout]",
        "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-t", str(total_dur), str(final_path),
    ])

    (BUILD_DIR / "caption.txt").write_text(script["caption"], encoding="utf-8")
    history["posted"].append({
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "topic": script["topic"],
        "hook": re.sub(r"<[^>]+>", "", script["text1"]),
    })
    save_history(history)
    print("Vídeo Código Zero e legenda gerados com sucesso em build/reel_final.mp4")


if __name__ == "__main__":
    main()

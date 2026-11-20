import json
import os
import random
import re
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
BROLL_TOPICS = [
    "clouds", "sunset", "sunlight", "nature", "sky", "ocean",
    "forest", "mountains", "sunrise", "rain", "stars", "water",
]
MUSIC_TOPICS = ["piano", "ambient", "peaceful", "calm"]

# Banco resiliente com 30 roteiros cristãos humanizados para aguentar alto volume sem repetir
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
        "caption": "Nos dias mais difíceis, lembre-se: a presença de Deus é maior que qualquer tempestade.\n\nVocê não precisa enfrentar o futuro com medo. Ele renova suas forças quando você pensa que não vai aguentar.\n\nSe você crê nessa promessa hoje, comente AMÉM e envie para alguém que precisa ouvir isso. 🙏✨\n\nIsaías 41:10 | @wallasnascimento_ • ideepregai",
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
        "caption": "Quando tudo parecer agitado demais, volte para o refúgio que nunca falha.\n\nDeus é socorro imediato e fortaleza firme para quem confia n'Ele.\n\nReceba essa paz hoje. Comente AMÉM! 🙏✨\n\nSalmos 46:1 | @wallasnascimento_ • ideepregai",
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
        "caption": "Não deixe a preocupação roubar a paz que Deus separou para o seu dia.\n\nColoque diante d'Ele em oração aquilo que foge do seu controle.\n\nSe você entrega nas mãos de Deus hoje, comente AMÉM! 🙏✨\n\nFilipenses 4:6-7 | @wallasnascimento_ • ideepregai",
    },
    {
        "verse": "Jeremias 29:11",
        "pre1": "Mensagem do céu",
        "text1": "O que parece o fim é um novo <span class='gold'>começo</span>.",
        "pre2": "Planos maiores",
        "text2": "Deus não improvisa, Ele já traçou o seu <span class='gold'>propósito</span>.",
        "pre3": "A promessa",
        "text3": "\"Eu sei os planos que tenho para vocês: planos de paz e esperança.\"",
        "pre4": "Confie no caminho",
        "text4": "O melhor ainda está por vir na sua <span class='gold'>vida</span>.",
        "narration": "O que parece o fim é o começo de um novo propósito! Jeremias vinte e nove onze promete: Eu sei os planos que tenho para vocês, planos de paz e esperança! Confie, o melhor ainda está por vir. Comente amém!",
        "caption": "Os seus dias não são obra do acaso.\n\nO Senhor tem planos de paz, futuro e esperança para a sua história, mesmo quando o caminho ainda parece nebuloso.\n\nSe você toma posse dessa esperança hoje, comente AMÉM! 🙏✨\n\nJeremias 29:11 | @wallasnascimento_ • ideepregai",
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
        "narration": "A sua coragem não vem da sua força, vem do Deus que te chamou! Josué um nove ordena: seja forte e corajoso, o Senhor estará com você por onde andar! Levante a cabeça e siga. Comente amém!",
        "caption": "Coragem não é ausência de medo: é caminhar sabendo que Deus vai ao seu lado em cada passo.\n\nNão recue diante das dificuldades. Quem te chamou é fiel para te sustentar.\n\nRecebe essa força hoje? Comente AMÉM! 🙏✨\n\nJosué 1:9 | @wallasnascimento_ • ideepregai",
    },
    {
        "verse": "Salmos 23:1",
        "pre1": "Guarde no coração",
        "text1": "Quando Deus guia, nada essencial vai te <span class='gold'>faltar</span>.",
        "pre2": "Descanso verdadeiro",
        "text2": "Você corre atrás do vento ou descansa no <span class='gold'>Pastor</span>?",
        "pre3": "A promessa",
        "text3": "\"O Senhor é o meu pastor; nada me faltará.\"",
        "pre4": "Confiança plena",
        "text4": "Ele cuida dos detalhes que você nem <span class='gold'>enxerga</span>.",
        "narration": "Quando Deus guia seus passos, nada essencial vai te faltar! O Salmo vinte e três lembra: o Senhor é o meu pastor, nada me faltará. Descanse hoje, porque Ele cuida até dos detalhes que você não vê. Comente amém!",
        "caption": "A paz volta quando você deixa Deus conduzir o caminho.\n\nEle conhece as suas necessidades antes mesmo de você pedir.\n\nSe o Senhor é o seu pastor, comente AMÉM! 🙏✨\n\nSalmos 23:1 | @wallasnascimento_ • ideepregai",
    },
    {
        "verse": "Romanos 8:28",
        "pre1": "Não desista agora",
        "text1": "Nem toda demora significa uma <span class='red'>derrota</span>.",
        "pre2": "Visão de fé",
        "text2": "O que hoje dói, amanhã vai te <span class='gold'>fortalecer</span>.",
        "pre3": "A promessa",
        "text3": "\"Todas as coisas cooperam para o bem daqueles que amam a Deus.\"",
        "pre4": "Confie no processo",
        "text4": "Deus transforma cada peça em <span class='gold'>propósito</span>.",
        "narration": "Nem toda demora significa uma derrota! O que hoje parece sem sentido está sendo usado para te fortalecer. Romanos oito vinte e oito garante: todas as coisas cooperam para o bem dos que amam a Deus! Comente amém!",
        "caption": "Mesmo quando você não entende o motivo do processo, Deus continua trabalhando nos bastidores.\n\nNada do que você atravessa com fé é desperdiçado nas mãos d'Ele.\n\nVocê crê nisso hoje? Comente AMÉM! 🙏✨\n\nRomanos 8:28 | @wallasnascimento_ • ideepregai",
    },
    {
        "verse": "Salmos 30:5",
        "pre1": "Para quem chorou",
        "text1": "A dor desta noite não vai durar para <span class='red'>sempre</span>.",
        "pre2": "Tempo de virada",
        "text2": "As lágrimas regam a colheita que está <span class='gold'>chegando</span>.",
        "pre3": "A promessa",
        "text3": "\"O choro pode durar uma noite, mas a alegria vem pela manhã.\"",
        "pre4": "Amanhecer de Deus",
        "text4": "Prepare o coração, porque o seu dia vai <span class='gold'>clarear</span>.",
        "narration": "A dor desta noite não vai durar para sempre! O Salmo trinta cinco afirma: o choro pode durar uma noite, mas a alegria vem pela manhã! Aguente firme, porque o seu dia vai clarear. Comente amém!",
        "caption": "Se hoje o coração está apertado, não encerre sua história na madrugada.\n\nA fidelidade de Deus traz um novo amanhecer depois de cada noite difícil.\n\nReceba essa esperança e comente AMÉM! 🙏✨\n\nSalmos 30:5 | @wallasnascimento_ • ideepregai",
    },
    {
        "verse": "Provérbios 3:5-6",
        "pre1": "Pare de tentar prever",
        "text1": "Querer entender tudo só rouba a sua <span class='red'>paz</span>.",
        "pre2": "Direção segura",
        "text2": "Entregue o volante da sua vida para <span class='gold'>Deus</span>.",
        "pre3": "A promessa",
        "text3": "\"Confie no Senhor de todo o coração e Ele endireitará suas veredas.\"",
        "pre4": "Caminho firme",
        "text4": "Quem caminha com Deus nunca anda <span class='gold'>perdido</span>.",
        "narration": "Querer entender tudo antes da hora só rouba a sua paz! Provérbios três ensina: confie no Senhor de todo o seu coração e Ele endireitará os seus caminhos. Entregue a direção a Ele hoje. Comente amém!",
        "caption": "Nossa visão alcança apenas alguns passos; a de Deus alcança a eternidade.\n\nConfiar de todo o coração é descansar mesmo sem ter todas as respostas.\n\nComente AMÉM se você entrega o seu caminho ao Senhor! 🙏✨\n\nProvérbios 3:5-6 | @wallasnascimento_ • ideepregai",
    },
    {
        "verse": "Isaías 40:31",
        "pre1": "Para quem cansou",
        "text1": "O cansaço da alma não se cura só com <span class='red'>sono</span>.",
        "pre2": "Fonte de vigor",
        "text2": "Quem espera em Deus recebe força que não <span class='gold'>acaba</span>.",
        "pre3": "A promessa",
        "text3": "\"Os que esperam no Senhor renovarão as suas forças como águias.\"",
        "pre4": "Novo fôlego",
        "text4": "Você vai voltar a voar mais alto do que <span class='gold'>antes</span>.",
        "narration": "O cansaço da alma não se cura apenas dormindo! Isaías quarenta trinta e um promete: os que esperam no Senhor renovarão as suas forças e subirão como águias! Receba novo fôlego hoje. Comente amém!",
        "caption": "Quando o cansaço apertar, não tente carregar tudo na força do braço.\n\nEsperar no Senhor não é ficar parado: é descansar enquanto Ele renova o seu fôlego por dentro.\n\nReceba esse renovo e comente AMÉM! 🙏✨\n\nIsaías 40:31 | @wallasnascimento_ • ideepregai",
    },
    {
        "verse": "João 16:33",
        "pre1": "Palavra de Jesus",
        "text1": "Ter problemas não significa que Deus te <span class='red'>esqueceu</span>.",
        "pre2": "Ânimo firme",
        "text2": "Jesus não prometeu facilidade, prometeu <span class='gold'>vitória</span>.",
        "pre3": "A promessa",
        "text3": "\"No mundo tereis aflições, mas tende bom ânimo: eu venci o mundo.\"",
        "pre4": "Paz inabalável",
        "text4": "Quem anda com Cristo já começa do lado <span class='gold'>vencedor</span>.",
        "narration": "Passar por lutas não significa que Deus te esqueceu! Jesus disse em João dezesseis trinta e três: no mundo tereis aflições, mas tende bom ânimo, eu venci o mundo! Levante a cabeça hoje. Comente amém!",
        "caption": "Fé não é fingir que não existem dias difíceis; é lembrar quem já venceu por nós.\n\nTenha bom ânimo hoje: a paz de Cristo é maior que qualquer pressão externa.\n\nComente AMÉM se você crê! 🙏✨\n\nJoão 16:33 | @wallasnascimento_ • ideepregai",
    },
    {
        "verse": "Salmos 121:1-2",
        "pre1": "Olhe para o alto",
        "text1": "Pare de procurar socorro onde só há <span class='red'>vazio</span>.",
        "pre2": "De onde vem a ajuda",
        "text2": "O Criador dos céus está atento à sua <span class='gold'>oração</span>.",
        "pre3": "A promessa",
        "text3": "\"O meu socorro vem do Senhor, que fez o céu e a terra.\"",
        "pre4": "Segurança total",
        "text4": "Aquele que te guarda nunca dorme nem <span class='gold'>falha</span>.",
        "narration": "Pare de buscar socorro onde só existe cansaço! O Salmo cento e vinte e um declara: o meu socorro vem do Senhor, que fez o céu e a terra! Aquele que te guarda nunca dorme. Comente amém!",
        "caption": "Quando faltar direção aqui embaixo, levante os olhos para o alto.\n\nO mesmo Deus que formou os céus e a terra cuida da sua casa e da sua vida hoje.\n\nDeclare isso nos comentários: AMÉM! 🙏✨\n\nSalmos 121:1-2 | @wallasnascimento_ • ideepregai",
    },
    {
        "verse": "2 Coríntios 12:9",
        "pre1": "Na sua fraqueza",
        "text1": "Você não precisa ser forte o tempo <span class='red'>todo</span>.",
        "pre2": "O segredo da graça",
        "text2": "Onde termina a sua força, começa o poder de <span class='gold'>Deus</span>.",
        "pre3": "A promessa",
        "text3": "\"A minha graça te basta, pois o meu poder se aperfeiçoa na fraqueza.\"",
        "pre4": "Alívio agora",
        "text4": "A graça d'Ele é suficiente para o seu <span class='gold'>hoje</span>.",
        "narration": "Você não precisa fingir que é forte o tempo todo! Em segunda Coríntios doze nove, Deus diz: a minha graça te basta, porque o meu poder se aperfeiçoa na fraqueza! Descanse nessa graça hoje. Comente amém!",
        "caption": "Admitir a própria fragilidade não te afasta de Deus; te aproxima do poder d'Ele.\n\nA graça do Senhor é suficiente para te sustentar exatamente no ponto em que você está.\n\nComente AMÉM se essa palavra falou com você! 🙏✨\n\n2 Coríntios 12:9 | @wallasnascimento_ • ideepregai",
    },
    {
        "verse": "Salmos 37:5",
        "pre1": "Solte o controle",
        "text1": "Carregar o futuro nas costas está te <span class='red'>esgotando</span>.",
        "pre2": "O passo certo",
        "text2": "Entregue, confie e deixe o Senhor <span class='gold'>agir</span>.",
        "pre3": "A promessa",
        "text3": "\"Entrega o teu caminho ao Senhor; confia nele, e ele tudo fará.\"",
        "pre4": "Descanso ativo",
        "text4": "Faça a sua parte e deixe o impossível com <span class='gold'>Ele</span>.",
        "narration": "Tentar controlar o futuro está te esgotando! O Salmo trinta e sete cinco ensina: entrega o teu caminho ao Senhor, confia nele, e Ele tudo fará! Faça a sua parte e deixe o impossível com Deus. Comente amém!",
        "caption": "Três verbos que mudam um dia inteiro: entregar, confiar e descansar.\n\nO que você não consegue resolver sozinho está seguro nas mãos de quem tudo pode.\n\nEntregue hoje e comente AMÉM! 🙏✨\n\nSalmos 37:5 | @wallasnascimento_ • ideepregai",
    },
    {
        "verse": "Lamentações 3:22-23",
        "pre1": "Novo recomeço",
        "text1": "Os erros de ontem não cancelam a graça de <span class='gold'>hoje</span>.",
        "pre2": "Amor fiel",
        "text2": "Cada manhã traz uma nova chance vinda do <span class='gold'>céu</span>.",
        "pre3": "A promessa",
        "text3": "\"As misericórdias do Senhor se renovam a cada manhã.\"",
        "pre4": "Recomece leve",
        "text4": "Grande é a fidelidade de Deus sobre a sua <span class='gold'>vida</span>.",
        "narration": "Os erros de ontem não cancelam a graça de hoje! Lamentações três declara: as misericórdias do Senhor não têm fim, renovam-se cada manhã! Respire fundo e recomece leve com Deus. Comente amém!",
        "caption": "Você não precisa carregar a culpa do passado para dentro do dia de hoje.\n\nA misericórdia de Deus amanheceu nova para você.\n\nAgradeça por esse recomeço comentando AMÉM! 🙏✨\n\nLamentações 3:22-23 | @wallasnascimento_ • ideepregai",
    },
    {
        "verse": "Mateus 6:34",
        "pre1": "Um dia de cada vez",
        "text1": "Você está sofrendo por um amanhã que nem <span class='red'>chegou</span>.",
        "pre2": "Foco no presente",
        "text2": "Deus dá graça para o hoje, não para o <span class='gold'>medo</span>.",
        "pre3": "A promessa",
        "text3": "\"Não vos inquieteis pelo dia de amanhã; basta a cada dia o seu mal.\"",
        "pre4": "Viva o agora",
        "text4": "Respire fundo: Deus já está cuidando do seu <span class='gold'>amanhã</span>.",
        "narration": "Você está sofrendo por um amanhã que ainda nem chegou! Jesus aconselhou em Mateus seis trinta e quatro: não andeis ansiosos pelo dia de amanhã. Viva um dia de cada vez, Deus já cuida do resto. Comente amém!",
        "caption": "A graça de Deus é entregue na medida certa para hoje.\n\nSolte a pressa, acalme a mente e viva o dia presente em paz.\n\nComente AMÉM e mande para alguém ansioso hoje! 🙏✨\n\nMateus 6:34 | @wallasnascimento_ • ideepregai",
    },
    {
        "verse": "Salmos 91:1-2",
        "pre1": "Proteção real",
        "text1": "Nenhum mal alcança quem descansa em <span class='gold'>Deus</span>.",
        "pre2": "Lugar seguro",
        "text2": "O melhor abrigo não é um lugar, é a <span class='gold'>presença d'Ele</span>.",
        "pre3": "A promessa",
        "text3": "\"Aquele que habita no esconderijo do Altíssimo descansará à sua sombra.\"",
        "pre4": "Coração guardado",
        "text4": "Declare proteção sobre a sua casa <span class='gold'>hoje</span>.",
        "narration": "O melhor abrigo do mundo não é um lugar, é a presença de Deus! O Salmo noventa e um declara: aquele que habita no esconderijo do Altíssimo descansará à sombra do Onipotente! Comente amém!",
        "caption": "Antes de sair ou encerrar o dia, coloque sua casa e sua família debaixo da proteção do Altíssimo.\n\nQuem confia no Senhor encontra abrigo verdadeiro.\n\nDeclare proteção hoje comentando AMÉM! 🙏✨\n\nSalmos 91:1-2 | @wallasnascimento_ • ideepregai",
    },
    {
        "verse": "1 Pedro 5:7",
        "pre1": "Alívio imediato",
        "text1": "Por que guardar no peito o que Deus pediu para <span class='gold'>entregar</span>?",
        "pre2": "Cuidado pessoal",
        "text2": "Você não é invisível: o Pai se importa com <span class='gold'>você</span>.",
        "pre3": "A promessa",
        "text3": "\"Lancem sobre ele toda a sua ansiedade, porque ele tem cuidado de vocês.\"",
        "pre4": "Coração leve",
        "text4": "Solte esse peso agora nas mãos de <span class='gold'>Deus</span>.",
        "narration": "Por que guardar no peito um peso que Deus pediu para você entregar? Primeira Pedro cinco sete diz: lancem sobre Ele toda a sua ansiedade, porque Ele cuida de vocês! Solte esse peso hoje. Comente amém!",
        "caption": "Deus não pede que você resolva tudo em silêncio e sozinho.\n\nEle se importa de verdade com o que aperta o seu coração hoje.\n\nLance sua ansiedade nas mãos d'Ele e comente AMÉM! 🙏✨\n\n1 Pedro 5:7 | @wallasnascimento_ • ideepregai",
    },
    {
        "verse": "Filipenses 4:13",
        "pre1": "Força verdadeira",
        "text1": "O desafio parece maior do que a sua <span class='red'>capacidade</span>?",
        "pre2": "Sua fonte",
        "text2": "Você não depende só do seu limite humano, depende de <span class='gold'>Cristo</span>.",
        "pre3": "A promessa",
        "text3": "\"Tudo posso naquele que me fortalece.\"",
        "pre4": "Avance com fé",
        "text4": "Com a força de Deus, você vai atravessar essa <span class='gold'>fase</span>.",
        "narration": "O desafio parece maior do que a sua força hoje? Você não depende apenas dos seus limites! Filipenses quatro treze afirma: tudo posso naquele que me fortalece! Avance com fé hoje. Comente amém!",
        "caption": "Essa promessa não fala de orgulho humano, mas de dependência diária de Cristo.\n\nÉ Ele quem sustenta você tanto nos dias bons quanto nos dias de pressão.\n\nCreia e comente AMÉM! 🙏✨\n\nFilipenses 4:13 | @wallasnascimento_ • ideepregai",
    },
    {
        "verse": "Salmos 34:18",
        "pre1": "Você não está só",
        "text1": "Nos dias de silêncio, Deus está mais <span class='gold'>perto</span>.",
        "pre2": "Consolo fiel",
        "text2": "Ele não rejeita um coração ferido, Ele <span class='gold'>cura</span>.",
        "pre3": "A promessa",
        "text3": "\"Perto está o Senhor dos que têm o coração quebrantado.\"",
        "pre4": "Cura interior",
        "text4": "Deixe o amor de Deus restaurar você por <span class='gold'>dentro</span>.",
        "narration": "Nos dias em que você se sente mais sozinho, Deus está ainda mais perto! O Salmo trinta e quatro diz: perto está o Senhor dos que têm o coração quebrantado! Deixe Ele curar você hoje. Comente amém!",
        "caption": "Você não precisa se consertar primeiro para se aproximar de Deus.\n\nEle se achega justamente quando o coração está cansado e precisando de cura.\n\nReceba esse abraço de paz e comente AMÉM! 🙏✨\n\nSalmos 34:18 | @wallasnascimento_ • ideepregai",
    },
    {
        "verse": "João 14:27",
        "pre1": "Paz verdadeira",
        "text1": "A paz que o mundo oferece acaba na primeira <span class='red'>crise</span>.",
        "pre2": "Presente de Cristo",
        "text2": "A paz de Jesus permanece firme no meio da <span class='gold'>tempestade</span>.",
        "pre3": "A promessa",
        "text3": "\"Deixo-vos a paz, a minha paz vos dou; não se turbe o vosso coração.\"",
        "pre4": "Acalme a alma",
        "text4": "Receba a paz que nada nem ninguém pode <span class='gold'>tirar</span>.",
        "narration": "A paz que o mundo oferece acaba na primeira crise! Mas Jesus disse em João quatorze vinte e sete: a minha paz vos dou, não se perturbe o vosso coração! Receba essa paz agora. Comente amém!",
        "caption": "A verdadeira paz não é a ausência de problemas, é a presença constante de Jesus.\n\nQue hoje o seu coração fique tranquilo e guardado por Ele.\n\nComente AMÉM para receber essa paz! 🙏✨\n\nJoão 14:27 | @wallasnascimento_ • ideepregai",
    },
    {
        "verse": "Hebreus 12:1",
        "pre1": "Não pare agora",
        "text1": "O cansaço da caminhada não é motivo para <span class='red'>parar</span>.",
        "pre2": "Constância na fé",
        "text2": "Largue o peso que atrapalha e continue <span class='gold'>correndo</span>.",
        "pre3": "A promessa",
        "text3": "\"Corramos com perseverança a carreira que nos está proposta.\"",
        "pre4": "Foco no alvo",
        "text4": "Quem persevera com Deus chega ao <span class='gold'>propósito</span>.",
        "narration": "O cansaço da caminhada não é motivo para desistir! Hebreus doze um nos chama: corramos com perseverança a corrida que Deus propôs para nós! Largue o peso e siga firme. Comente amém!",
        "caption": "A fé se constrói na constância de cada dia, não só nos momentos fáceis.\n\nContinue correndo com perseverança a corrida que Deus preparou para você.\n\nVai continuar firme? Comente AMÉM! 🙏✨\n\nHebreus 12:1 | @wallasnascimento_ • ideepregai",
    },
    {
        "verse": "Salmos 27:1",
        "pre1": "Sem medo hoje",
        "text1": "Por que temer quando a Luz caminha à sua <span class='gold'>frente</span>?",
        "pre2": "Firmeza na alma",
        "text2": "Nenhuma sombra vence quem anda com o <span class='gold'>Senhor</span>.",
        "pre3": "A promessa",
        "text3": "\"O Senhor é a minha luz e a minha salvação; de quem terei medo?\"",
        "pre4": "Caminhe seguro",
        "text4": "Deus ilumina o próximo passo do seu <span class='gold'>caminho</span>.",
        "narration": "Por que caminhar com medo se a Luz vai à sua frente? O Salmo vinte e sete afirma: o Senhor é a minha luz e a minha salvação, de quem terei medo? Siga seguro hoje. Comente amém!",
        "caption": "Quando a dúvida tentar escurecer os seus pensamentos, lembre-se de quem ilumina o seu caminho.\n\nO Senhor é luz, salvação e fortaleza para a sua vida.\n\nDeclare com fé: AMÉM! 🙏✨\n\nSalmos 27:1 | @wallasnascimento_ • ideepregai",
    },
    {
        "verse": "Romanos 12:12",
        "pre1": "Três atitudes",
        "text1": "Nos dias difíceis, não pare de <span class='gold'>orar</span>.",
        "pre2": "Segredo de vitória",
        "text2": "A esperança te levanta e a paciência te <span class='gold'>sustenta</span>.",
        "pre3": "A promessa",
        "text3": "\"Alegrem-se na esperança, sejam pacientes na tribulação, perseverem na oração.\"",
        "pre4": "Constância diária",
        "text4": "Uma oração sincera muda o ambiente do seu <span class='gold'>dia</span>.",
        "narration": "Nos dias difíceis, não pare de orar! Romanos doze doze ensina: alegrem-se na esperança, sejam pacientes na tribulação e perseverem na oração! Continue firme, Deus está ouvindo. Comente amém!",
        "caption": "Esperança, paciência e oração: três pilares simples que sustentam a alma em qualquer estação.\n\nNão abra mão da sua conversa com Deus hoje.\n\nComente AMÉM e salve para reler depois! 🙏✨\n\nRomanos 12:12 | @wallasnascimento_ • ideepregai",
    },
    {
        "verse": "Salmos 119:105",
        "pre1": "Falta direção?",
        "text1": "Você não precisa ver toda a estrada, só o <span class='gold'>próximo passo</span>.",
        "pre2": "Guia seguro",
        "text2": "A Palavra de Deus clareia a decisão de <span class='gold'>hoje</span>.",
        "pre3": "A promessa",
        "text3": "\"Lâmpada para os meus pés é a tua palavra e luz para o meu caminho.\"",
        "pre4": "Sabedoria real",
        "text4": "Quem escuta Deus antes de agir erra muito <span class='gold'>menos</span>.",
        "narration": "Você não precisa enxergar a estrada inteira, basta ver o próximo passo! O Salmo cento e dezenove diz: lâmpada para os meus pés é a tua palavra e luz para o meu caminho! Busque direção hoje. Comente amém!",
        "caption": "Muitas decisões difíceis ficam mais claras quando tiramos alguns minutos para ouvir a Palavra.\n\nDeus ilumina o passo de hoje para conduzir você com segurança.\n\nComente AMÉM! 🙏✨\n\nSalmos 119:105 | @wallasnascimento_ • ideepregai",
    },
]


def load_history() -> dict:
    if HISTORY_FILE.exists():
        return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    return {"posted": []}


def save_history(data: dict) -> None:
    HISTORY_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def generate_script(posted_verses: list[str]) -> dict:
    """Tenta gerar via Gemini API; se houver instabilidade ou 503, usa o acervo curado."""
    if GEMINI_API_KEY:
        recent = posted_verses[-40:]
        prompt = f"""
Você é um roteirista cristão para o Instagram @wallasnascimento_ (ideepregai).
Crie um Reel de 15 segundos com um versículo bíblico DIFERENTE destes já postados: {recent}.
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
            "generationConfig": {"responseMimeType": "application/json", "temperature": 0.9},
        }).encode("utf-8")

        for model in ["gemini-3.8-flash", "gemini-flash-latest", "gemini-flash-lite-latest"]:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
            for attempt in range(2):
                try:
                    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
                    with urllib.request.urlopen(req, timeout=15) as resp:
                        res = json.loads(resp.read().decode("utf-8"))
                    raw = res["candidates"][0]["content"]["parts"][0]["text"]
                    parsed = json.loads(raw)
                    if parsed.get("verse") and parsed.get("narration"):
                        print(f"Roteiro gerado com sucesso via Gemini ({model})!")
                        return parsed
                except Exception as exc:
                    print(f"Tentativa {attempt + 1} em {model} falhou: {exc}")
                    time.sleep(3)

    print("Usando roteiro curado do acervo inteligente...")
    available = [s for s in CURATED_SCRIPTS if s["verse"] not in posted_verses]
    if not available:
        last_verses = set(posted_verses[-15:])
        available = [s for s in CURATED_SCRIPTS if s["verse"] not in last_verses] or CURATED_SCRIPTS
    return random.choice(available)


def fetch_mixkit_asset(topics: list[str], base_url: str, pattern: str, out_path: Path) -> str:
    shuffled = topics[:]
    random.shuffle(shuffled)
    for topic in shuffled:
        page_url = f"{base_url}/{topic}/"
        try:
            html = subprocess.check_output(
                ["curl", "-sL", "--max-time", "20", "-A", "Mozilla/5.0", page_url]
            ).decode("utf-8", errors="ignore")
            matches = list(dict.fromkeys(re.findall(pattern, html)))
            if matches:
                chosen = random.choice(matches[:25])
                subprocess.check_call(["curl", "-sL", "--max-time", "45", "-o", str(out_path), chosen])
                if out_path.exists() and out_path.stat().st_size > 20_000:
                    return chosen
        except Exception as exc:
            print(f"Aviso ao baixar mídia de {page_url}: {exc}")
    raise RuntimeError(f"Não foi possível baixar mídia válida de {base_url}")


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

    print("5. Compondo B-roll + Motion + Voz + Trilha no FFmpeg...")
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
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "verse": script["verse"],
        "hook": re.sub(r"<[^>]+>", "", script["text1"]),
    })
    save_history(history)
    print("Vídeo e legenda gerados com sucesso em build/reel_final.mp4")


if __name__ == "__main__":
    main()

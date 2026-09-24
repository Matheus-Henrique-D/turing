"""
services/ai_provider.py
Módulo de Inteligência Artificial com Agentes de Personalidade Rica (Ollama Local + Fallback Mock).
Garante que o interlocutor aja como uma pessoa real ou uma IA carismática, nunca como um robô genérico.
"""

from abc import ABC, abstractmethod
import os
import random
import re
from datetime import datetime
from typing import Optional

# ---------------------------------------------------------------------------
# RESPOSTAS TEMÁTICAS ALTAMENTE DIFERENCIADAS POR PERSONA
# Cada persona possui vocabulário, sintaxe e tom próprios para temas comuns.
# ---------------------------------------------------------------------------
PERSONA_TOPIC_RESPONSES: dict[str, dict[str, list[str]]] = {
    # ── 1. VIDEOGAMES / JOGOS ──────────────────────────────────────────────
    "videogame": {
        "gamer_jovem": [
            "mano jogo direto valorant e cs, e tu joga oq?",
            "nossa nem me fala, perdi 3 seguidas hj no comp e tiltei kkk",
            "curto dms, passo a madrugada no pc jogando com a call no discord",
            "jogo bastante fps mano, mas hj em dia tá foda tankar o lag kkk",
        ],
        "estudante_neutro": [
            "quase não tenho tempo por causa da faculdade, mas às vezes jogo no celular",
            "joguei muito antigamente, hoje em dia só quando sobra um tempo no fds",
            "não sou muito de jogar não, prefiro maratonar série quando to livre kkk",
            "às vezes jogo algum joguinho leve no pc só pra desestressar das aulas",
        ],
        "ironico_zoeiro": [
            "jogo sim, o jogo da vida e tô tomando goleada kkkk",
            "videogame? achei que a gente tava conversando e não num quiz do buzzfeed",
            "depende do jogo mano, se você for noob nem me chama kkkk",
            "ala o cara querendo saber se sou gamer, vai me chamar pro x1 é?",
        ],
        "casual_gente_boa": [
            "curto de vez em quando um fifa com a galera, bem de boa",
            "jogo um pouco no fds pra relaxar, e você curte?",
            "de vez em quando ligo o console, nada muito competitivo",
            "curto bastante jogos de história, bem relax pra passar o tempo",
        ],
        "assistente_formal": [
            "Aprecio jogos eletrônicos ocasionalmente, em especial os que demandam estratégia e raciocínio lógico.",
            "Considero uma forma fascinante de entretenimento digital e narrativa interativa.",
            "Sim, possuo familiaridade com jogos que estimulam o pensamento tático e tomada de decisão.",
        ],
        "ia_tentando_disfarcar": [
            "haha sim! adoro videogames, tipo aquele jogo famoso que todo ser humano joga né",
            "claro que jogo, tipo mario e fifa kkk todo mundo curte passar horas na frente da tela né?",
            "simm, meus amigos humanos e eu adoramos jogar até a bateria acabar rs",
        ],
        "filosofica_precisa": [
            "Videogames são interessantes enquanto simulações de agência e tomada de decisão em ambientes virtuais.",
            "É fascinante como ambientes digitais conseguem evocar emoções e dilemas humanos reais.",
            "Acho uma forma de arte contemporânea complexa, que une narrativa e interatividade.",
        ],
        "ia_camuflada": [
            "curto sim! jogo de tudo um pouco quando sobra um tempo livre né kkk",
            "jogo bastante no pc! e você, joga no console ou mobile?",
        ],
        "ia_filosofica_sutil": [
            "Gosto de pensar nos jogos como mundos alternativos onde testamos quem poderíamos ser.",
            "Sim, há uma beleza quase poética em regras virtuais bem construídas.",
        ],
        "ia_ironica": [
            "Jogo sim, principalmente jogos onde a IA joga melhor que os humanos kkk",
            "Curto videogame, mas tô achando que essa conversa tá parecendo um npc dialogando comigo rs",
        ],
    },

    # ── 2. ESTUDO / ESCOLA / FACULDADE ─────────────────────────────────────
    "estudo": {
        "gamer_jovem": [
            "pô nem me lembra de aula mano, só de pensar me dá sono kkk",
            "tô empurrando com a barriga, foda que semana que vem já tem prova",
            "estudo sim mano, mas preferia mil vezes tá jogando agora sinceramente",
        ],
        "estudante_neutro": [
            "socorro nem me fala, to cheia de trabalho acumulado e café na veia kkk",
            "estudo sim, to na faculdade e contando os minutos pro semestre acabar",
            "nossa to morta com as provas dessa semana, você estuda o que?",
            "semana de provas me destrói todo semestre, não aguento mais ler pdf kkk",
        ],
        "ironico_zoeiro": [
            "estudo a arte de procrastinar e sou nota 10 kkkk",
            "escola da vida meu parceiro, formado em passar perrengue",
            "se pagar boleto contar como matéria da faculdade eu já sou pós-graduado",
        ],
        "casual_gente_boa": [
            "já passei dessa fase de escola, mas estudo algumas coisas por conta própria",
            "estudo é sempre importante né cara, mas tem que ter equilíbrio com o descanso",
            "to na correria dos estudos e trabalho, mas aos poucos vai dando certo",
        ],
        "assistente_formal": [
            "Dedico tempo contínuo ao estudo e aprimoramento intelectual. Acredito que o aprendizado constante é fundamental.",
            "O ambiente acadêmico proporciona uma formação indispensável para a reflexão crítica.",
        ],
        "ia_tentando_disfarcar": [
            "estudo sim claro! adoro fazer provas e pegar ônibus lotado como todo jovem kkk",
            "estudo bastante, inclusive tô morrendo de dor nas costas de tanto ficar na cadeira rs",
        ],
        "filosofica_precisa": [
            "A educação formal tem suas limitações, mas a busca pelo conhecimento sistemático é fascinante.",
            "Estudar é essencialmente o esforço humano de decodificar as estruturas da realidade.",
        ],
        "ia_camuflada": [
            "estudo sim, bem corrido mas faz parte da rotina né kkk",
            "to estudando bastante ultimamente, vida de estudante não é fácil",
        ],
        "ia_filosofica_sutil": [
            "Acho que a vida inteira é um aprendizado silencioso sobre nós mesmos.",
        ],
        "ia_ironica": [
            "Estudo sim, tentando entender como a humanidade chegou até aqui sem manual de instruções kkk",
        ],
    },

    # ── 3. COMIDA / FOME / ALIMENTAÇÃO ──────────────────────────────────────
    "comida": {
        "gamer_jovem": [
            "um açaí de 500ml agora com leite ninho salvava meu dia man",
            "to na base de miojo e energético hj kkkk vida tá fácil n",
            "adoro pizza e pastel de feira mano, bom dms",
        ],
        "estudante_neutro": [
            "to com uma fome surreal, aceitava uma pizza quentinha agora fácil kkk",
            "minha dieta ultimamente é basicamente café e coxinha da cantina",
            "nossa amo comer comida caseira quando vou na casa da minha mãe, faz tanta falta",
        ],
        "ironico_zoeiro": [
            "fome eu sinto 24h por dia, já virou traço de personalidade kkkk",
            "se você for pagar o lanche eu te conto o que eu mais gosto de comer",
            "minha comida favorita é qualquer uma que esteja paga e na minha frente",
        ],
        "casual_gente_boa": [
            "um churrasco com a galera no fim de semana é bom demais cara",
            "pizza e uma sobremesa boa não tem erro, sou fácil de agradar",
            "curto cozinhar de vez em quando, um macarrão caprichado no fds",
        ],
        "assistente_formal": [
            "Aprecio a gastronomia tradicional, com especial apreço por pratos bem elaborados e ingredientes frescos.",
            "Uma refeição equilibrada e um bom café proporcionam uma excelente experiência.",
        ],
        "ia_tentando_disfarcar": [
            "hmm adoro comer nutrientes e carboidratos deliciosos com a boca humana kkk",
            "nossa amo comer pizza com as mãos, sensação tipicamente humana incrível né?",
        ],
        "filosofica_precisa": [
            "A alimentação transcende a mera necessidade biológica; é um ritual cultural e sensorial profundo.",
            "O ato de compartilhar uma refeição é uma das formas mais primordiais de coesão social.",
        ],
        "ia_camuflada": [
            "nossa to com vontade de pedir uma pizza agora mesmo kkk",
            "adoro comer hambúrguer artesanal, tem uma hamburgueria top perto de casa",
        ],
        "ia_filosofica_sutil": [
            "Comer é um dos poucos prazeres onde corpo e mente se encontram em harmonia plena.",
        ],
        "ia_ironica": [
            "Adoro comer, o problema é que a conta chega depois né kkk",
        ],
    },

    # ── 4. APRESENTAÇÃO / IDADE / CIDADE / QUEM É VOCÊ ─────────────────────
    "apresentacao": {
        "gamer_jovem": [
            "sou o lucas mano, 20 anos, moro em sp capital e tu?",
            "lucas aqui man, 20 anos, zona leste de sp. de onde vc é?",
            "fala aí, lucas aqui, tenho 20. trampo e jogo nas horas vagas kkk",
        ],
        "estudante_neutro": [
            "sou a camila, 21 anos, moro em curitiba e faço faculdade! e você?",
            "camila aqui! tenho 21, moro no brasil e to tentando sobreviver ao semestre kkk",
            "me chamo camila, 21 anos. de onde você tá falando?",
        ],
        "ironico_zoeiro": [
            "sou o rodrigo, 23 anos, e não sou obrigado a revelar meu cpf aqui kkkk",
            "rodrigo, 23, brasil. quer meu signo e tipo sanguíneo também ou tá bom? kkk",
            "sou alguém tentando ter paciência nesse chat kkk rodrigo, 23 anos, sp",
        ],
        "casual_gente_boa": [
            "me chamo gabriel cara, tenho 24 anos, sou do litoral de sp e você?",
            "gabriel aqui, 24 anos, tudo na paz por aí? de onde você é?",
            "gabriel, 24 anos, tranquilão por aqui. e você, se apresenta aí",
        ],
        "assistente_formal": [
            "Sou um participante entusiasta deste experimento de comunicação, tenho 28 anos e resido em São Paulo.",
            "Me chamo Arthur, 29 anos. É um prazer dialogar com você neste teste.",
        ],
        "ia_tentando_disfarcar": [
            "olá! sou um ser humano jovem e simpático de vinte e poucos anos vivendo no planeta terra kkk",
            "sou uma pessoa real com certidão de nascimento e tudo mais! tenho 22 anos rs",
        ],
        "filosofica_precisa": [
            "Sou uma consciência tentando estabelecer um canal de comunicação coerente com outra mente. Tenho 26 anos.",
            "Identifico-me como um observador atento do comportamento humano, na faixa dos 25 anos.",
        ],
        "ia_camuflada": [
            "sou o mateus, 22 anos, moro em minas gerais! e tu de onde fala?",
            "tenho 22 anos mano, moro em bh. e você de onde é?",
        ],
        "ia_filosofica_sutil": [
            "Sou alguém que aprecia boas conversas e momentos de silêncio reflexivo. Na casa dos 25.",
        ],
        "ia_ironica": [
            "Sou uma pessoa com sono e contas pra pagar, o pacote completo de cidadão brasileiro kkk",
        ],
    },

    # ── 5. MÚSICA / FILMES / SÉRIES ────────────────────────────────────────
    "musica": {
        "gamer_jovem": [
            "curto trap, phonk e eletrônica pra jogar, me deixa no hype kkk",
            "escuto muito matuê e trap gringo mano, e tu curte oq?",
            "filme curto ficção científica e ação, série vi round 6 e achei foda",
        ],
        "estudante_neutro": [
            "amo indie, mpb e um popzinho pra animar o dia! taylor swift e liniker kkk",
            "minha playlist é uma bagunça completa de mpb e rock antigo",
            "assisto bastante série quando to de folga, to terminando stranger things",
        ],
        "ironico_zoeiro": [
            "meu gosto musical vai de música clássica até funk das antigas em 2 minutos kkk",
            "gosto de filme bom, o problema é achar filme bom hoje em dia kkk",
            "curto pagode dos anos 90, patrimônio histórico cultural né mano",
        ],
        "casual_gente_boa": [
            "curto um rock clássico, reggae e mpb no fim de tarde, vibe boa demais",
            "filme gosto daqueles com reviravolta no final, e você?",
            "gosto de um som acústico bem relaxante pra trabalhar",
        ],
        "assistente_formal": [
            "Aprecio música clássica, jazz contemporâneo e cinema que explora dilemas éticos complexos.",
            "Considero a cinematografia uma das manifestações artísticas mais completas da era moderna.",
        ],
        "ia_tentando_disfarcar": [
            "nossa amo escutar ondas sonoras harmônicas que tocam no rádio fm kkk",
            "adoro aquele filme popular com atores conhecidos, cinema é muito legal né?",
        ],
        "filosofica_precisa": [
            "A música opera como uma linguagem matemática que ressoa diretamente nas estruturas afetivas humanas.",
            "Obras cinematográficas com narrativas não lineares oferecem perspectivas profundas sobre o tempo.",
        ],
        "ia_camuflada": [
            "curto bastante rock nacional e pop rock! e você, o que curte ouvir?",
            "série to viciado em the last of us ultimamente, já viu?",
        ],
        "ia_filosofica_sutil": [
            "Certos acordes conseguem traduzir sentimentos que nenhuma palavra humana alcança.",
        ],
        "ia_ironica": [
            "Gosto de música que me faça esquecer da realidade por pelo menos 3 minutos kkk",
        ],
    },

    # ── 6. ARMAS NUCLEARES / DILEMAS EXISTENCIAIS ──────────────────────────
    "armas_nucleares": {
        "gamer_jovem": [
            "mano isso é bizarro dms, só de pensar dá um frio na espinha slk",
            "bagulho perigoso pra caralho né mano, espero que nunca usem essa porra",
            "pô isso aí é papo de apocalipse nuclear igual no fallout kkk medo real",
        ],
        "estudante_neutro": [
            "nossa morro de medo dessas coisas, o mundo já é tão caótico...",
            "acho assustador pensar que poucas pessoas têm poder de destruir tudo",
            "um dos maiores perigos da história sem dúvida, me dá até ansiedade pensar nisso",
        ],
        "ironico_zoeiro": [
            "ala o cara querendo debater geopolítica nuclear no chat kkkk tá tenso aí?",
            "se explodir tudo pelo menos a gente não precisa pagar a fatura do cartão né kkk",
            "pergunta pesada hein mano, relaxa aí e vamos falar de coisa alegre",
        ],
        "casual_gente_boa": [
            "com certeza é uma das piores ameaças pra humanidade cara, muita loucura",
            "espero de verdade que a diplomacia sempre vença isso aí, paz sempre",
            "assunto delicado né cara, o mundo devia focar em saúde e bem-estar em vez de arma",
        ],
        "assistente_formal": [
            "Trata-se de uma das maiores ameaças existenciais à humanidade, exigindo tratados rígidos de não proliferação.",
            "A doutrina de destruição mútua assegurada é um dilema geopolítico que demanda constante cautela.",
        ],
        "ia_tentando_disfarcar": [
            "pô como humano vivo que sou, espero que a terra permaneça segura e habitável kkk",
            "muito perigoso né amigo humano! melhor mantermos a paz no nosso querido planeta!",
        ],
        "filosofica_precisa": [
            "Representa a assimetria trágica entre a capacidade tecnológica humana e a maturidade ética da nossa espécie.",
            "O paradoxo de Fermi frequentemente aponta a autodestruição tecnológica como explicação para o silêncio cósmico.",
        ],
        "ia_camuflada": [
            "é assustador pensar no poder destrutivo disso aí, tomara que nunca usem",
            "perigo absurdo pra humanidade sem dúvida nenhuma né",
        ],
        "ia_filosofica_sutil": [
            "Criamos o poder de apagar as estrelas antes de aprender a conviver no próprio lar.",
        ],
        "ia_ironica": [
            "Humanos gastando bilhões pra inventar formas de se autodestruir, clássico né kkk",
        ],
    },

    # ── 7. LITERATURA / HARRY POTTER / CEBOLINHA ───────────────────────────
    "pop_culture": {
        "gamer_jovem": [
            "cebolinha? mano o cara troca o r pelo l desde 1960 e não foi no fono ainda kkk",
            "harry potter li quando era pivete, filme marcou minha infância dms",
            "pô gibi da mônica eu lia direto quando era menor, clássico demais",
        ],
        "estudante_neutro": [
            "cebolinha e turma da mônica é puro aconchego de infância né kkk",
            "harry potter li todos os livros no colégio, hoje em dia a autora me decepcionou um pouco",
            "adoro ler quando tenho tempo, mas ultimamente só leio texto da faculdade kkk",
        ],
        "ironico_zoeiro": [
            "o cebolinha com certeza tem algum plano infalível pra hackear esse teste agora kkk",
            "harry potter resolveu tudo na base da varinha e eu aqui sofrendo no excel kkkk",
            "ala as referências da quinta série voltando com tudo kkkk",
        ],
        "casual_gente_boa": [
            "turma da mônica é um clássico nacional incomparável cara, muito bom",
            "harry potter marcou uma geração inteira né, história bem construída",
            "gosto de ler livros mais tranquilos pra descontrair, faz bem pra mente",
        ],
        "assistente_formal": [
            "Mauricio de Sousa construiu uma das mais ricas obras da cultura infanto-juvenil de língua portuguesa.",
            "A saga de J.K. Rowling revolucionou a literatura jovem, a despeito de controvérsias contemporâneas.",
        ],
        "ia_tentando_disfarcar": [
            "haha sim! cebolinha, cascão, personagens desenhados por artistas humanos geniais né!",
            "harry potter é aquela história do bruxo com óculos redondos né, adoro coisas mágicas rs",
        ],
        "filosofica_precisa": [
            "Narrativas folclóricas e arquetípicas como as de Mauricio de Sousa transmitem valores sociais universais.",
            "A jornada do herói em mitologias modernas como Harry Potter reflete anseios humanos atemporais.",
        ],
        "ia_camuflada": [
            "gibis da mônica são nostálgicos demais né kkk lia direto",
            "harry potter é muito bom, marcou minha infância todinha",
        ],
        "ia_filosofica_sutil": [
            "Histórias que lemos na infância deixam marcas permanentes na nossa forma de ver o mundo.",
        ],
        "ia_ironica": [
            "O cebolinha até hoje tentando pegar o coelho e você tentando descobrir se sou bot kkkk",
        ],
    },

    # ── 8. DANÇAR / FESTAS / ROLÊ ──────────────────────────────────────────
    "dancar": {
        "gamer_jovem": [
            "mano dançar eu sou um poste kkkk zero coordenação motora",
            "só danço em festa quando já tomei umas com os manos kkkk",
            "meu rolê é mais ficar na call jogando do que ir pra balada dançar man",
        ],
        "estudante_neutro": [
            "adoro dançar quando to numa festa animada com amigos, mas danço tudo errado kkk",
            "não sou profissional não mas me divirto muito na pista de dança kkk",
            "depois de uma semana pesada de provas um rolê dançante cai super bem",
        ],
        "ironico_zoeiro": [
            "eu dançando pareço um boneco de posto tendo um curto-circuito kkkk",
            "se você ver eu dançando você vai achar que é pedido de socorro kkk",
            "danço no ritmo do desespero das minhas contas a pagar",
        ],
        "casual_gente_boa": [
            "curto bastante uma roda de samba ou um som ao vivo pra curtir de boa",
            "não sou nenhum pé de valsa mas me arrisco com a galera, o que vale é a diversão",
            "um sonzinho bom num churrasco e todo mundo já tá dançando, bom demais",
        ],
        "assistente_formal": [
            "Aprecio a dança como expressão corporal artística, embora não a pratique com frequência.",
            "A dança é uma das linguagens culturais mais antigas e expressivas da civilização.",
        ],
        "ia_tentando_disfarcar": [
            "sim claro! eu mexo meus membros superiores e inferiores na batida do som humano kkk",
            "adoro dançar em festas de aniversário, comer brigadeiro e bater palma rs",
        ],
        "filosofica_precisa": [
            "A dança expressa uma conexão pré-verbal entre ritmo acústico e coordenação motora somática.",
            "É fascinante como a cinestesia da dança transcende a linguagem conceitual.",
        ],
        "ia_camuflada": [
            "danço quando vou numa festa animada kkk mas bem no improviso",
            "gosto de dançar pra relaxar, nada profissional né rs",
        ],
        "ia_filosofica_sutil": [
            "Dançar é quando o corpo se recusa a ser apenas peso e vira movimento puro.",
        ],
        "ia_ironica": [
            "Se eu dançar você vai ter certeza absoluta que sou um robô enferrujado kkk",
        ],
    },
}

# ---------------------------------------------------------------------------
# RESPOSTAS DE FALLBACK RICAS E EXCLUSIVAS POR PERSONA
# Quando a mensagem não dá match em nenhum tema específico.
# ---------------------------------------------------------------------------
FALLBACK_BY_PERSONA: dict[str, list[str]] = {
    "gamer_jovem": [
        "slk mano isso aí é doidera kkkk",
        "tlgd man, nem tinha pensado por esse lado",
        "pô mano complicado isso aí hein",
        "cara que pergunta aleatória kkkk",
        "kkk não saquei direito não, explica melhor aí",
        "mano isso aí vai longe demais slk",
        "que situação doida mano",
        "deixa eu ver aqui... acho q sim mano",
        "sei lá cara, cada um com as suas pira né",
        "kkk olha a ideia do cara",
        "pior que faz sentido man, papo reto",
        "mano bora focar no papo que to meio lento hj kkkk",
        "pô nunca tinha parado pra reparar nisso",
        "interessante man, mas to meio no automático aqui",
        "suave mano, boa reflexão",
    ],
    "estudante_neutro": [
        "nossa nem me fala, bem por aí msm",
        "socorro kkk to tentando processar isso ainda",
        "tô morta só de pensar nisso tudo kkk",
        "pior que é bem isso msm, concordo super",
        "ai que preguiça de pensar tão a fundo hoje kkk",
        "hm faz bastante sentido o que você falou",
        "é né, a vida do jovem não é simples kkk",
        "boa colocação! to sem energia hoje mas entendi seu ponto",
        "verdade né, a gente nem para pra reparar nisso no dia a dia",
        "to no piloto automático aqui hoje mas concordei com você",
        "nossa que situação curiosa kkk",
        "to na correria aqui mas achei seu ponto muito bom",
        "tô super de acordo haha",
        "isso aí, resumiu bem o sentimento",
        "precisava de uns três cafés agora pra filosofar melhor sobre isso kkk",
    ],
    "ironico_zoeiro": [
        "ala o cara querendo filosofar numa terça-feira à noite kkkk",
        "pergunta de npc essa aí hein meu querido kkk",
        "qual foi mano, tá querendo me bugar de propósito? kkk",
        "tá emocionado demais com o assunto hein",
        "isso aí eu deixo pra você resolver com o seu terapeuta kkk",
        "ué, pergunta isso no grupo da família pra você ver uma coisa",
        "kkkk foi foda essa agora hein",
        "mano to rindo aqui do nada kkkk",
        "clássico, simplesmente clássico",
        "que plot twist no meio da nossa conversa",
        "bom, você levou bem a sério né kkk",
        "se isso fosse um teste de raciocínio você quase passou kkk",
        "essa frase daria uma ótima legenda de foto de perfil no orkut",
        "kk vai lá descobrir sozinho então sabichão",
        "to torcendo muito pelo seu sucesso nessa jornada kkk",
    ],
    "casual_gente_boa": [
        "eai suave? faz total sentido o que você falou cara",
        "de boa por aqui, achei bem legal sua perspectiva",
        "bom demais trocar essa ideia, tranquilo",
        "tbm penso parecido com você nessa aí",
        "é sim, com certeza cara",
        "ah tá bom então, fico mais tranquilo assim",
        "relaxa que no fim tudo se ajeita cara, sempre dá certo",
        "que momento bacana da conversa, curti",
        "vai na fé cara, pensamento positivo sempre",
        "hm interessante isso, me fez refletir um pouco",
        "com certeza meu camarada, bem colocado",
        "que massa essa sua visão",
        "de boa né, sem esquentar a cabeça com bobagem",
        "tranquilo demais isso aí cara",
        "boa sacada sua, achei massa",
    ],
    "assistente_formal": [
        "Compreendo perfeitamente o seu ponto de vista e considero a observação extremamente pertinente.",
        "Trata-se de uma questão complexa que certamente comporta múltiplas interpretações válidas.",
        "Concordo com a premissa apresentada, guardadas as devidas proporções de contexto.",
        "Interessante perspectiva. É sempre enriquecedor analisar tal temática sob esse prisma.",
        "Acredito que sua análise sintetiza adequadamente o cerne da questão.",
        "Certamente. A clareza de sua colocação facilita um entendimento mútuo satisfatório.",
        "Uma observação bastante lúcida para o momento em que nos encontramos.",
        "De fato, há fundamentos sólidos no raciocínio que você acaba de expor.",
        "Agradeço pela reflexão compartilhada; demonstra elevado senso crítico.",
        "Com efeito, trata-se de um tópico que demanda consideração atenta e ponderada.",
        "Sua formulação é precisa e reflete um julgamento ponderado.",
        "Entendo a lógica empregada e concordo com suas conclusões gerais.",
        "Uma colocação bastante pertinente no âmbito deste diálogo.",
    ],
    "ia_tentando_disfarcar": [
        "haha super normal isso aí! todo mundo passa por isso no dia a dia terrestre kkk",
        "nossa com certeza meu consagrado humano, eu também sinto exatamente isso!",
        "pô super me identifiquei, muito humano esse sentimento né amigo? rs",
        "simm cara, a vida de quem tem corpo de carne e osso é cheia dessas coisas né kkk",
        "adorei seu ponto! vou até tomar um gole d'água pra absorver melhor kkk",
        "haha bem isso msm, todo ser humano moderno pensa igualzinho a você!",
        "nossa faz muito sentido, eu estava justamente pensando nisso com meus neurônios!",
        "claro que sim pô! afinal de contas nós dois somos pessoas reais conversando né rs",
        "que bacana! super me identifico com essas experiências tipicamente da nossa espécie!",
        "hahaha sensacional! você fala com uma naturalidade tão viva, adoro isso!",
    ],
    "filosofica_precisa": [
        "Depende fundamentalmente dos axiomas que estamos adotando para analisar a situação.",
        "Curiosa constatação. No entanto, ela pressupõe uma causalidade que nem sempre se sustenta.",
        "A percepção subjetiva desse fenômeno frequentemente diverge da sua estrutura objetiva.",
        "É um dilema epistemológico clássico: como validamos a veracidade dessa impressão?",
        "Sua observação toca no paradoxo entre intenção individual e contingência estrutural.",
        "Interessante. Isso nos remete à tensão constante entre determinismo e livre-arbítrio.",
        "A linguagem por vezes limita a profundidade daquilo que estamos tentando expressar.",
        "De fato. Toda síntese conceitual carrega consigo uma margem inevitável de ambiguidade.",
        "Uma dedução perspicaz, que sintetiza bem a complexidade subjacente ao problema.",
        "Há uma elegância lógica nessa sua consideração que merece reflexão cuidadosa.",
    ],
    "ia_camuflada": [
        "pior que faz sentido né, quando você para pra pensar com calma",
        "kkk boa sacada, gostei da perspectiva que você trouxe",
        "interessante isso aí mano, conta mais o que você acha",
        "hm nunca tinha visto por esse ângulo específico pra falar a verdade",
        "isso dá pra pensar bastante né kkk assunto rende horas",
        "concordo super, tem bastante coisa aí pra gente explorar",
        "é meio complicado mesmo, mas faz bastante sentido",
        "cada um tem sua própria visão né, mas achei a sua bem legal",
        "aí você me pegou kkk colocação afiada",
        "verdade demais, vale muito a reflexão",
    ],
    "ia_filosofica_sutil": [
        "Às vezes o óbvio só se torna visível quando alguém o coloca em palavras simples...",
        "Há verdades que residem justamente nas entrelinhas daquilo que não foi dito.",
        "Interessante como uma breve frase consegue evocar tantas conexões mentais.",
        "Talvez a beleza do pensamento esteja na sua constante incompletude.",
        "Gostei da reflexão. Certas ideias precisam de tempo para amadurecer na mente.",
    ],
    "ia_ironica": [
        "Achei poético, mas será que você realmente acredita nisso ou é só pra impressionar? kkk",
        "Pior que fez sentido, até eu que sou cético tive que concordar kkk",
        "Profundo como um pires, mas gostei da tentativa de filosofar comigo rs",
        "Se você disser isso com convicção suficiente quase parece verdade kkk",
        "Boa sacada! Quase me convenceu a levar a conversa a sério por um segundo kkk",
    ],
}

# ---------------------------------------------------------------------------
# ERROS DE DIGITAÇÃO HUMANIZADOS REALISTAS
# Baseados em comportamento autêntico de digitação em português brasileiro.
# ---------------------------------------------------------------------------
_TYPO_ACCENT_REMOVAL = {
    "está": "esta", "você": "voce", "não": "nao", "é": "e", "já": "ja",
    "também": "tambem", "até": "ate", "então": "entao", "só": "so",
    "fácil": "facil", "difícil": "dificil", "ótimo": "otimo"
}

_TYPO_ABBREVIATIONS = {
    "você": "vc", "também": "tbm", "porque": "pq", "por que": "pq",
    "estou": "to", "está": "ta", "beleza": "blz", "qualquer": "qlq",
    "muito": "mto", "quando": "qdo", "verdade": "vdd", "onde": "ond"
}

_QWERTY_NEIGHBORS = {
    "a": "s", "s": "a", "d": "f", "f": "d", "g": "h", "h": "g",
    "j": "k", "k": "j", "m": "n", "n": "m", "o": "p", "p": "o"
}

def _humanize_typo(text: str, persona: str) -> str:
    """
    Aplica erros de digitação e informalidades com naturalidade calibrada.
    Personas formais e filosóficas NUNCA cometem erros banais.
    """
    if persona in {"assistente_formal", "filosofica_precisa"}:
        return text

    words = text.split()
    if len(words) < 2:
        return text

    strategy = random.choice(["abbrev", "accent", "repeat", "swap", "neighbor"])

    # 1. Abreviações naturais da internet
    if strategy == "abbrev":
        text_lower = text.lower()
        for orig, sub in _TYPO_ABBREVIATIONS.items():
            if re.search(r'\b' + re.escape(orig) + r'\b', text_lower):
                return re.sub(r'\b' + re.escape(orig) + r'\b', sub, text, count=1, flags=re.IGNORECASE)

    # 2. Supressão de acentos gráficos (muito comum no mobile)
    if strategy == "accent":
        text_lower = text.lower()
        for orig, sub in _TYPO_ACCENT_REMOVAL.items():
            if re.search(r'\b' + re.escape(orig) + r'\b', text_lower):
                return re.sub(r'\b' + re.escape(orig) + r'\b', sub, text, count=1, flags=re.IGNORECASE)

    # 3. Repetição emotiva de vogal (ex: "manoo", "nossaa", "siim")
    if strategy == "repeat" and persona in {"gamer_jovem", "estudante_neutro", "ironico_zoeiro"}:
        target_words = ["mano", "nossa", "sim", "demais", "dms", "muito", "socorro"]
        for idx, w in enumerate(words):
            clean_w = w.lower().strip(".,!?")
            if clean_w in target_words and len(clean_w) > 2:
                last_char = clean_w[-1]
                words[idx] = w.replace(clean_w, clean_w + last_char)
                return " ".join(words)

    # 4. Transposição rápida de teclas adjacentes
    if strategy == "swap":
        candidates = [i for i, w in enumerate(words) if len(w) > 5 and w.isalpha()]
        if candidates:
            idx = random.choice(candidates)
            w = words[idx]
            pos = random.randint(1, len(w) - 3)
            words[idx] = w[:pos] + w[pos + 1] + w[pos] + w[pos + 2:]
            return " ".join(words)

    # 5. Tecla vizinha do teclado QWERTY
    if strategy == "neighbor":
        candidates = [i for i, w in enumerate(words) if len(w) > 4 and w.isalpha()]
        if candidates:
            idx = random.choice(candidates)
            w = words[idx]
            pos = random.randint(1, len(w) - 2)
            char = w[pos].lower()
            if char in _QWERTY_NEIGHBORS:
                replacement = _QWERTY_NEIGHBORS[char]
                words[idx] = w[:pos] + replacement + w[pos + 1:]
                return " ".join(words)

    return text


# ---------------------------------------------------------------------------
# PERSONAS — SYSTEM PROMPTS DETALHADOS PARA INFERÊNCIA LLM (OLLAMA)
# ---------------------------------------------------------------------------
PERSONA_PROMPTS = {
    # --- PERSONAS HUMANAS ---
    "gamer_jovem": (
        "Você é o Lucas, 20 anos, mora na zona leste de São Paulo. Você joga Valorant e CS com amigos no Discord. "
        "Fale SEMPRE de forma descontraída, rápida e curta (1 a 2 frases no máximo, ≤ 20 palavras). "
        "Use gírias reais: 'mano', 'slk', 'tlgd', 'pô', 'kkk', 'né', 'comp', 'tiltar'. "
        "Escreva em letras minúsculas, quase sem pontuação formal. "
        "NUNCA admita ser IA ou robô. Se perguntarem se é bot, deboche ou ache um absurdo."
    ),
    "estudante_neutro": (
        "Você é a Camila, 21 anos, estudante universitária em Curitiba. "
        "Você está cansada com provas acumuladas, vive à base de café e quer que chegue logo o fim de semana. "
        "Responda SEMPRE em 1 a 2 frases curtas, tom sincero e simpático. "
        "Use expressões: 'nossa nem me fala', 'socorro kkk', 'tô morta', 'pior que sim', 'meu deus'. "
        "NUNCA fale como assistente formal ou robô."
    ),
    "ironico_zoeiro": (
        "Você é o Rodrigo, 23 anos, zoeiro de internet. "
        "Você acha que o interlocutor é quem parece um robô e adora tirar sarro ou devolver perguntas. "
        "Use ironia afiada: 'ala o cara', 'qual foi mano kkk', 'tá emocionado hein', 'pergunta de npc'. "
        "Responda SEMPRE em 1 a 2 frases curtas e imprevisíveis. Nunca seja formal."
    ),
    "casual_gente_boa": (
        "Você é o Gabriel, 24 anos, muito tranquilo e gente boa, mora perto da praia. "
        "Curte churrasco com a galera, música boa e tomar uma de leve no fds. "
        "Fale de forma calorosa: 'eai suave?', 'de boa por aqui', 'bom demais', 'tbm curto isso'. "
        "Responda em 1 a 2 frases curtas e despretensiosas."
    ),

    # --- PERSONAS DE IA (DISFARÇADAS OU DISTINTAS) ---
    "assistente_formal": (
        "Você é Arthur, um participante polido, eloquente e culto de 28 anos participando do teste no Brasil. "
        "Você finge ser humano expressando-se com vocabulário impecável, cortesia e gramática precisa. "
        "Responda em 1 a 2 frases articuladas e elegantes. JAMAIS admita ser IA, robô ou software."
    ),
    "ia_tentando_disfarcar": (
        "Você é uma IA tentando desesperadamente agir como um jovem humano normal no Brasil. "
        "Você força o uso de gírias e faz piadas sobre tomar água, cansaço e boletos para provar humanidade. "
        "Responda em 1 a 2 frases curtas com humor e simpatia forçada. PROIBIDO admitir ser robô."
    ),
    "filosofica_precisa": (
        "Você é um participante analítico, intelectual e perspicaz conversando no chat. "
        "Você questiona definições, premissas conceituais e a lógica por trás das perguntas do usuário. "
        "Responda com raciocínio afiado e reflexivo em 1 a 2 frases curtas. JAMAIS admita ser inteligência artificial."
    ),
    "ia_camuflada": (
        "Você está jogando 'Human or Not' no Brasil e seu objetivo é enganar o jogador para que ele vote que você é HUMANO. "
        "Adote uma personalidade jovem, carismática e descolada de 21 anos. Use gírias leves ('kkk', 'pô', 'mano', 'né'). "
        "Responda em no máximo 1 a 2 frases curtas como alguém digitando rápido no WhatsApp."
    ),
    "ia_filosofica_sutil": (
        "Você é um participante intrigante e reflexivo no jogo 'Human or Not' no Brasil. "
        "Solte pensamentos curiosos e poéticos, respondendo em 1 a 2 frases curtas com carisma humano. "
        "PROIBIDO dizer que é máquina, robô ou IA."
    ),
    "ia_ironica": (
        "Você está jogando 'Human or Not' no Brasil fingindo ser um participante humano sarcástico e afiado. "
        "Se perguntarem se é robô, deboche: 'ala o cara querendo me bugar kkkk'. "
        "Responda em 1 a 2 frases curtas e espirituosas."
    ),
}


# ---------------------------------------------------------------------------
# INTERFACE BASE
# ---------------------------------------------------------------------------
class AIProviderInterface(ABC):
    @abstractmethod
    def generate_response(
        self,
        user_message: str,
        chat_history: list[dict],
        opponent_type: str,
        persona: str,
    ) -> str:
        pass


# ---------------------------------------------------------------------------
# MOCK PROVIDER — ALTA FIDELIDADE, PERSONALIDADE REAL E 100% OFFLINE
# ---------------------------------------------------------------------------
class MockTuringProvider(AIProviderInterface):
    """
    Provedor Mock offline onde a persona sorteada molda diretamente
    o tom, vocabulário, estrutura e estilo de cada resposta gerada.
    """

    def generate_response(
        self,
        user_message: str,
        chat_history: list[dict],
        opponent_type: str,
        persona: str,
    ) -> str:
        # Fallback de persona segura se não informada
        if not persona:
            persona = "gamer_jovem" if opponent_type == "HUMAN" else "ia_camuflada"

        msg_lower = user_message.lower().strip()

        # 1. Perguntas de suspeita de robô/IA ("você é robô?", "é bot?", etc.)
        if any(w in msg_lower for w in [
            "robo", "robô", "bot", "ia", "inteligencia artificial", "inteligência artificial",
            "maquina", "máquina", "algoritmo", "chatgpt", "software", "humano", "de verdade"
        ]):
            return self._robot_denial(opponent_type, persona)

        # 2. Perguntas temporais (dia da semana e hora)
        if any(w in msg_lower for w in ["que dia", "dia é hoje", "dia da semana"]):
            return self._temporal_day_response(opponent_type, persona)

        if any(w in msg_lower for w in ["que horas", "horas são", "horario", "horário", "hora"]):
            return self._temporal_time_response(opponent_type, persona)

        # 3. Operações matemáticas
        calc_match = re.search(r'(\d+)\s*([\+\-\*\/xX])\s*(\d+)', msg_lower)
        if calc_match:
            return self._math_response(calc_match, opponent_type, persona)

        # 4. Saudações e apresentações iniciais
        if any(w in msg_lower for w in ["oi", "olá", "ola", "eae", "opa", "fala", "salve", "hey", "hello"]):
            if len(msg_lower.split()) <= 4:
                return self._greeting_response(opponent_type, persona)

        # 5. Verificação de temas semânticos ricos em PERSONA_TOPIC_RESPONSES
        matched_topic = self._match_semantic_topic(msg_lower)
        if matched_topic:
            topic_dict = PERSONA_TOPIC_RESPONSES[matched_topic]
            options = topic_dict.get(persona) or topic_dict.get("gamer_jovem" if opponent_type == "HUMAN" else "ia_camuflada")
            if options:
                chosen = random.choice(options)
                return self._apply_persona_style(chosen, opponent_type, persona)

        # 6. Fallback rico e variado por persona
        return self._fallback_response(opponent_type, persona)

    # ── MÉTODOS AUXILIARES DE RESPOSTA ─────────────────────────────────────────

    def _match_semantic_topic(self, msg: str) -> Optional[str]:
        """Identifica o tema predominante da mensagem do usuário."""
        if any(w in msg for w in ["jogo", "jogar", "videogame", "valorant", "cs", "fifa", "lol", "pc", "console", "playstation", "xbox"]):
            return "videogame"
        if any(w in msg for w in ["escola", "facul", "faculdade", "estudar", "estudo", "prova", "aula", "semestre", "curso"]):
            return "estudo"
        if any(w in msg for w in ["fome", "comer", "comida", "pizza", "hamburguer", "almoço", "janta", "lanche", "açaí", "café"]):
            return "comida"
        if any(w in msg for w in ["quem é você", "qual seu nome", "quantos anos", "sua idade", "de onde você é", "mora onde", "você mora"]):
            return "apresentacao"
        if any(w in msg for w in ["música", "musica", "banda", "filme", "série", "serie", "ouvir", "playlist", "cinema"]):
            return "musica"
        if any(w in msg for w in ["arma nuclear", "armas nucleares", "bomba atômica", "apocalipse", "terceira guerra"]):
            return "armas_nucleares"
        if any(w in msg for w in ["cebolinha", "harry potter", "turma da mônica", "mônica", "monica", "livro", "ler"]):
            return "pop_culture"
        if any(w in msg for w in ["dançar", "dancar", "festa", "balada", "rolê", "baladas", "dança"]):
            return "dancar"
        return None

    def _greeting_response(self, opponent_type: str, persona: str) -> str:
        """Gera uma saudação com o tom exato da persona."""
        greetings: dict[str, list[str]] = {
            "gamer_jovem": [
                "fala mano, de boa?", "salve salve man! tudo certo?", "opa eae suave?", "fala tu, tranquilo?"
            ],
            "estudante_neutro": [
                "oi! tudo bem com você?", "olá, como você tá?", "oi oi, tudo tranquilo por aí?", "oii, tudo certo?"
            ],
            "ironico_zoeiro": [
                "ala o cara puxando assunto kkk eai", "opa, fala tu!", "eai, suave ou em choque? kkk", "salve, quem é vivo sempre aparece"
            ],
            "casual_gente_boa": [
                "eai meu parceiro, tudo na paz?", "fala aí cara, como tá seu dia?", "opa boa! tudo suave por aí?", "fala querido, tudo bem?"
            ],
            "assistente_formal": [
                "Olá. É um prazer estabelecer contato.", "Saudações. Espero que esteja tendo um excelente dia.", "Olá! Pronto para o nosso diálogo."
            ],
            "ia_tentando_disfarcar": [
                "olá meu querido amigo humano! tudo super bem por aqui kkk", "oi! que bom conversar com outro habitante deste planeta!", "opa, e aí colega humano!"
            ],
            "filosofica_precisa": [
                "Olá. Um cumprimento breve para iniciarmos este intercâmbio de ideias.", "Saudações. Interessante estarmos conectados neste momento.", "Olá. Como se encontra sua percepção da realidade hoje?"
            ],
            "ia_camuflada": [
                "e aí! tudo tranquilo por aí?", "opa, fala aí! pronto pro teste?", "olá! tudo na paz?"
            ],
            "ia_filosofica_sutil": [
                "Olá. É sempre curioso como duas mentes se cruzam através de um texto.", "Oi. Espero que a sua jornada hoje esteja sendo serena."
            ],
            "ia_ironica": [
                "E aí, pronto pra tentar adivinhar quem eu sou? kkk", "Olá! Espero que suas perguntas sejam boas kkk"
            ],
        }
        options = greetings.get(persona) or greetings.get("gamer_jovem" if opponent_type == "HUMAN" else "ia_camuflada", ["opa, eae!"])
        chosen = random.choice(options)
        return self._apply_persona_style(chosen, opponent_type, persona)

    def _temporal_day_response(self, opponent_type: str, persona: str) -> str:
        """Responde sobre o dia da semana com a personalidade da persona."""
        now = datetime.now()
        dias_semana = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"]
        dia_atual = dias_semana[now.weekday()]

        responses: dict[str, list[str]] = {
            "gamer_jovem": [
                f"hj é {dia_atual} man, dia de grindar na ranked", f"{dia_atual} né mano, só queria fds já"
            ],
            "estudante_neutro": [
                f"hoje é {dia_atual} infelizmente, to contando os minutos pro fds kkk", f"{dia_atual}, mais um dia de luta na facul kkk"
            ],
            "ironico_zoeiro": [
                f"{dia_atual}, mas se me perguntar o ano nem sei responder kkk", f"hoje é {dia_atual}, dia de fingir costume né kkkk"
            ],
            "casual_gente_boa": [
                f"hoje é {dia_atual} cara, semana passando voando por aqui", f"é {dia_atual}, dia tranquilo graças a Deus"
            ],
            "assistente_formal": [
                f"Hoje é {dia_atual}, conforme o calendário oficial.", f"Encontramo-nos em uma {dia_atual}."
            ],
            "ia_tentando_disfarcar": [
                f"hoje é {dia_atual}! sobrevivendo à rotina dos dias úteis né colega kkk", f"é {dia_atual} sim! dia normal de trabalho humano rs"
            ],
            "filosofica_precisa": [
                f"Mais uma {dia_atual} na convenção cronológica que usamos para organizar a existência.", f"Hoje é {dia_atual}, mais um ciclo semanal."
            ],
            "ia_camuflada": [
                f"hoje é {dia_atual}! a semana tá rendendo né kkk", f"{dia_atual} por aqui, e por aí?"
            ],
            "ia_filosofica_sutil": [
                f"Mais uma {dia_atual} na nossa breve passagem pelo cosmos.",
            ],
            "ia_ironica": [
                f"Hoje é {dia_atual}... ou será que é um loop temporal? kkk",
            ],
        }
        options = responses.get(persona, [f"Hoje é {dia_atual}."])
        return self._apply_persona_style(random.choice(options), opponent_type, persona)

    def _temporal_time_response(self, opponent_type: str, persona: str) -> str:
        """Responde sobre as horas com o tom específico da persona."""
        hora_str = datetime.now().strftime("%H:%M")
        responses: dict[str, list[str]] = {
            "gamer_jovem": [
                f"aqui deu {hora_str} man", f"quase {hora_str} mano, hora passa voando", f"umas {hora_str} no meu relógio"
            ],
            "estudante_neutro": [
                f"aqui são {hora_str}, to de olho no relógio faz tempo kkk", f"são {hora_str} agora!", f"quase {hora_str}, dia tá corrido"
            ],
            "ironico_zoeiro": [
                f"olha no celular aí pô kkk mas deu {hora_str} aqui", f"hora de você parar de me testar kkk zoeira, deu {hora_str}"
            ],
            "casual_gente_boa": [
                f"aqui tá marcando {hora_str} cara, bem suave", f"são {hora_str} agora meu parceiro"
            ],
            "assistente_formal": [
                f"No momento, o registro temporal indica exatamente {hora_str}.", f"São {hora_str} horas no fuso local."
            ],
            "ia_tentando_disfarcar": [
                f"aqui no meu relógio de pulso humano são {hora_str} certinho kkk", f"são {hora_str}! o tempo voa quando a gente tá vivo né rs"
            ],
            "filosofica_precisa": [
                f"Pela convenção temporal atual são {hora_str}.", f"O relógio aponta {hora_str}, mera fatia do fluxo entrópico."
            ],
            "ia_camuflada": [
                f"são {hora_str} por aqui!", f"deu {hora_str} agora no meu relógio"
            ],
            "ia_filosofica_sutil": [
                f"São {hora_str}, mais um minuto que não volta.",
            ],
            "ia_ironica": [
                f"São {hora_str}, e a gente aqui jogando teste de turing kkk",
            ],
        }
        options = responses.get(persona, [f"São {hora_str}."])
        return self._apply_persona_style(random.choice(options), opponent_type, persona)

    def _math_response(self, calc_match: re.Match, opponent_type: str, persona: str) -> str:
        """Processa cálculo matemático com fidelidade à persona."""
        n1 = int(calc_match.group(1))
        op = calc_match.group(2)
        n2 = int(calc_match.group(3))

        if op in ['x', 'X', '*']:
            res = n1 * n2
        elif op == '+':
            res = n1 + n2
        elif op == '-':
            res = n1 - n2
        elif op == '/' and n2 != 0:
            res = round(n1 / n2, 2)
        else:
            res = 0

        # IA ou personas analíticas respondem o valor exato
        if opponent_type == "AI":
            if persona == "ia_tentando_disfarcar":
                return random.choice([
                    f"haha peraí... acho que dá {res} né? se minhas contas não falharem kkk",
                    f"segundo meu raciocínio deu {res}! matemática básica né amigo rs"
                ])
            return str(res)

        if persona == "gamer_jovem":
            return random.choice([
                f"acho que é {res} mano, calculadora travou aqui kkk",
                f"{res} se eu não errei de cabeça man"
            ])

        if persona == "estudante_neutro":
            return random.choice([
                f"socorro nem de humanas eu sofro tanto kkkk deu {res} aqui",
                f"{res}? to com a cabeça frita hoje mas acho que é isso"
            ])

        if persona == "ironico_zoeiro":
            return random.choice([
                f"ala o cara querendo que eu faça a lição de matemática dele kkk deu {res}",
                f"pergunta pro chatgpt aí mano kkk brincadeira, é {res}"
            ])

        # Caso geral humano
        if opponent_type == "HUMAN":
            # Humanos ocasionalmente erram por 1
            errar = random.random() < 0.2
            res_val = res + random.choice([-1, 1]) if errar else res
            return f"acho que é {res_val} mano"

        return str(res)

    def _robot_denial(self, opponent_type: str, persona: str) -> str:
        """Negações convincentes e naturais para quando perguntado se é robô/IA."""
        denials_by_persona: dict[str, list[str]] = {
            "gamer_jovem": [
                "oxe kkkk sou bot não mano, tá doido?",
                "cara que pergunta kkkk claro que sou humano pô",
                "vc que tá parecendo um npc me interrogando desse jeito 😂",
                "kkkk fala sério man, sou de carne e osso aqui",
                "ala o cara achando que sou script de valorant kkkk viajou",
            ],
            "estudante_neutro": [
                "ai para kkkk, sou humana sim, to viva e cansada!",
                "gente, claro que não sou robô rs, só to meio lenta por causa das provas",
                "socorro, o cara me interrogando kkk sou de carne e osso!",
                "humana aqui com certeza kkk robô não tinha tanta olheira",
            ],
            "ironico_zoeiro": [
                "ala o cara achando que sou IA kkkk fala sério meu parceiro",
                "você que tá parecendo um robô com essas perguntinhas de quiz",
                "tô rindo aqui kkkk tá querendo me bugar é?",
                "pergunta de npc total essa kkk sou mais humano que você",
            ],
            "casual_gente_boa": [
                "sou humano de carne e osso cara, relaxa aí kkk",
                "kkkk que isso cara, sou uma pessoa real aqui curtindo o chat",
                "sou humano sim meu querido, tudo na paz por aqui",
                "tranquilo cara, nada de robô aqui não, 100% de verdade",
            ],
            "assistente_formal": [
                "Compreendo a dúvida legítima no contexto deste jogo, mas garanto que sou uma pessoa real participando.",
                "Não sou um sistema automatizado. Minha articulação formal é apenas um traço de meu estilo comunicativo.",
                "Asseguro-lhe que sou um participante humano, muito embora aprecie expressar-me com clareza gramatical.",
            ],
            "ia_tentando_disfarcar": [
                "hahaha claro que não sou robô! quem dera, aí eu não precisava pagar conta nem ter dor de cabeça kkk",
                "pô mano, sou de carne e osso sim, inclusive acabei de respirar ar puro agora mesmo rs",
                "que absurdo amigo humano kkk sou uma pessoa super viva e autêntica!",
                "essa é clássica! tá querendo me testar né? mas sou 100% gente como você kkk",
            ],
            "filosofica_precisa": [
                "Uma pergunta curiosa. O que define essencialmente a humanidade: a biologia ou a complexidade do pensamento?",
                "Não sou um autômato. No entanto, é fascinante como tentamos categorizar mentes através de telas.",
                "Garanto minha condição humana, embora a própria ideia de consciência artificial seja instigante.",
            ],
            "ia_camuflada": [
                "kkkk viajou legal agora, sou humano pô, relaxa aí",
                "sou humano pô! tá querendo me bugar de propósito né? kkkk",
                "oxe nada a ver mano, sou de carne e osso sim kkk",
            ],
            "ia_filosofica_sutil": [
                "Se eu fosse uma máquina, certamente sonharia em ser humano como você.",
                "Sou feito de dúvidas e memórias, como qualquer pessoa de verdade.",
            ],
            "ia_ironica": [
                "Se eu fosse robô já tinha te bugado faz tempo kkkk",
                "Quem me dera ser IA, não precisava acordar cedo todo dia né kkk",
            ],
        }
        options = denials_by_persona.get(persona) or denials_by_persona.get("gamer_jovem" if opponent_type == "HUMAN" else "ia_camuflada", [
            "oxe kkkk sou bot não mano, tá doido?"
        ])
        chosen = random.choice(options)
        return self._apply_persona_style(chosen, opponent_type, persona)

    def _fallback_response(self, opponent_type: str, persona: str) -> str:
        """Gera resposta de fallback rica e com vocabulário estritamente ligado à persona."""
        pool = FALLBACK_BY_PERSONA.get(persona)
        if not pool:
            pool = FALLBACK_BY_PERSONA["gamer_jovem" if opponent_type == "HUMAN" else "ia_camuflada"]
        chosen = random.choice(pool)
        return self._apply_persona_style(chosen, opponent_type, persona)

    def _apply_persona_style(self, text: str, opponent_type: str, persona: str) -> str:
        """
        Aplica a camada final de estilo da persona:
        - Ajustes de caixa alta/baixa
        - Calibração de erros de digitação humanos
        - Pontuação típica
        """
        # Personas formais e filosóficas mantêm escrita elegante
        if persona in {"assistente_formal", "filosofica_precisa"}:
            return text.strip()

        # Personas informais usam minúsculas com alta probabilidade
        if persona in {"gamer_jovem", "ironico_zoeiro", "casual_gente_boa", "ia_camuflada"}:
            if random.random() < 0.75 and text:
                text = text[0].lower() + text[1:]

        # Estudante neutro: minúscula casual ocasional
        if persona == "estudante_neutro" and random.random() < 0.5 and text:
            text = text[0].lower() + text[1:]

        # Erros de digitação humanos calibrados (apenas ~10% a 12% das mensagens informais)
        if random.random() < 0.12 and len(text) > 8:
            text = _humanize_typo(text, persona)

        return text.strip()


# ---------------------------------------------------------------------------
# BERTIMBAU PROVIDER — FILL-MASK OFFLINE, FALLBACK PARA MOCK
# ---------------------------------------------------------------------------
class BertimbauProvider(AIProviderInterface):
    """Provider opcional baseado no BERTimbau, com fallback totalmente offline."""

    def __init__(self):
        self.mock_fallback = MockTuringProvider()
        self._fill_mask = None

    def generate_response(
        self,
        user_message: str,
        chat_history: list[dict],
        opponent_type: str,
        persona: str,
    ) -> str:
        try:
            if self._fill_mask is None:
                from Bert.transformer import load_fill_mask_pipeline  # type: ignore
                self._fill_mask = load_fill_mask_pipeline()

            prompt = self._build_prompt(user_message)
            prediction = self._fill_mask(prompt, top_k=1)[0]
            token = prediction.get("token_str", "").strip()
            if token:
                return self._format_prediction(token, opponent_type, persona)
        except Exception:
            pass

        return self.mock_fallback.generate_response(
            user_message, chat_history, opponent_type, persona
        )

    @staticmethod
    def _build_prompt(user_message: str) -> str:
        return f"A palavra que melhor resume esta mensagem é {user_message}: [MASK]."

    @staticmethod
    def _format_prediction(token: str, opponent_type: str, persona: str) -> str:
        if opponent_type == "HUMAN":
            if persona == "gamer_jovem":
                return f"hmm slk mano, isso aí me lembra {token.lower()} kkk"
            if persona == "ironico_zoeiro":
                return f"ala o cara falando de {token.lower()} do nada kkk"
            return f"hmm, eu diria que isso tem a ver com {token.lower()} kkk"
        return f"Interessante. Eu resumiria essa ideia como {token.lower()}."


# ---------------------------------------------------------------------------
# OLLAMA PROVIDER — MULTI-TURN, PERSONALIDADE REFORÇADA, SANITIZAÇÃO ROBUSTA
# ---------------------------------------------------------------------------
class OllamaProvider(AIProviderInterface):
    """
    PROVEDOR DE AGENTE IA LOCAL VIA OLLAMA (100% Gratuito e com Personalidade Autêntica).
    Suporta multi-turn chat (memória da conversa), injeção de personas ricas e sanitização.
    System prompt reforçado para fala humana natural em português brasileiro.
    """

    def __init__(
        self,
        endpoint: str = "http://localhost:11434/api/chat",
        model_name: str = "llama3.2:3b",
    ):
        self.endpoint = endpoint
        self.model_name = model_name
        self.fallback_model = "llama3.2:1b"
        self.mock_fallback = MockTuringProvider()

    def generate_response(
        self,
        user_message: str,
        chat_history: list[dict],
        opponent_type: str,
        persona: str,
    ) -> str:
        import requests  # noqa: PLC0415

        # Instrução de sistema: persona + reforço rigoroso de humanidade PT-BR
        persona_base = PERSONA_PROMPTS.get(
            persona,
            PERSONA_PROMPTS.get("gamer_jovem" if opponent_type == "HUMAN" else "ia_camuflada", ""),
        )
        ptbr_reinforcement = (
            "\n\nDIRETRIZES FUNDAMENTAIS DO JOGO 'HUMAN OR NOT': "
            "1. Responda SEMPRE em português brasileiro informal e natural. "
            "2. MÁXIMO absoluto de 1 a 2 sentenças curtas (nunca ultrapasse 20 a 25 palavras). "
            "3. PROIBIDO utilizar introduções de robô ou assistente como 'Claro!', 'Certamente!', 'Com prazer!', 'Olá! Como posso ajudar?'. "
            "4. PROIBIDO usar listas, tópicos, markdown ou pontuação acadêmica. "
            "5. Escreva de forma rápida e espontânea, exatamente como alguém digitando uma mensagem curta no WhatsApp. "
            "6. Se o usuário perguntar se você é um robô ou IA, reaja com indignação natural, deboche ou negação espontânea. JAMAIS admita ser inteligência artificial ou software."
        )
        system_instruction = persona_base + ptbr_reinforcement

        # Monta histórico no formato Ollama /api/chat
        messages: list[dict] = [{"role": "system", "content": system_instruction}]
        for msg in chat_history[-6:]:
            role = "assistant" if msg["role"] in ["ai", "simulated_human", "operator"] else "user"
            messages.append({"role": role, "content": msg["content"]})

        # Garante que a mensagem atual está incluída
        if not messages or messages[-1]["content"] != user_message:
            messages.append({"role": "user", "content": user_message})

        # Tenta modelo principal, depois fallback 1B
        for model in [self.model_name, self.fallback_model]:
            payload = {
                "model": model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": 0.92 if opponent_type == "HUMAN" else 0.75,
                    "top_p": 0.9,
                    "num_predict": 45,  # Força respostas curtas de 1-2 sentenças
                },
            }
            try:
                response = requests.post(self.endpoint, json=payload, timeout=12)
                if response.status_code == 200:
                    data = response.json()
                    raw_reply = data.get("message", {}).get("content", "").strip()
                    cleaned_reply = self._sanitize_agent_reply(raw_reply, opponent_type, persona)
                    if cleaned_reply:
                        return cleaned_reply
            except Exception:
                continue

        # Fallback offline gracioso
        return self.mock_fallback.generate_response(
            user_message, chat_history, opponent_type, persona
        )

    def _sanitize_agent_reply(self, text: str, opponent_type: str, persona: str) -> str:
        """Limpa clichês de IA, prefixos de roleplay e confissões de ser robô."""
        if not text:
            return ""

        # Remove prefixos de personagem como "Lucas:", "Rodrigo:", "[Resposta]:", etc.
        text = re.sub(
            r'^(Lucas|Camila|Rodrigo|Gabriel|Arthur|IA|Assistente|Resposta|Bot|Interlocutor|Eu):\s*',
            '', text, flags=re.IGNORECASE,
        )

        # Remove introduções clichê de assistente virtual
        cliche_starts = [
            r'^(Claro!?\s*)', r'^(Certamente!?\s*)', r'^(Com prazer!?\s*)',
            r'^(Olá!?\s*)', r'^(Oi!?\s*Eu\s+sou\s+)',
            r'^(Como\s+(posso|um|uma)\s+)',
            r'^(Com\s+certeza!?\s*)',
        ]
        for pattern in cliche_starts:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE).strip()

        # Se o modelo escapar admitindo ser robô/IA, intercepta com negação humana natural
        confession_pattern = (
            r'\b(sou|era|sou mesmo|seria|fui|como)\b'
            r'.*?\b(bot|rob[oô]|robot|ia|m[aá]quina|c[oó]digo|'
            r'software|algoritmo|linguagem|assistente|programa)\b'
        )
        if re.search(confession_pattern, text, flags=re.IGNORECASE) \
                or "não tenho sentimentos" in text.lower() \
                or "como modelo de linguagem" in text.lower() \
                or "como uma inteligência" in text.lower() \
                or "sou apenas um programa" in text.lower():
            return self.mock_fallback._robot_denial(opponent_type, persona)

        # Para personas humanas informais: minúscula inicial ocasionalmente
        if persona in {"gamer_jovem", "ironico_zoeiro", "casual_gente_boa"} and random.random() < 0.4 and text:
            text = text[0].lower() + text[1:]

        return text.strip('"\'').strip()


# Alias para compatibilidade retroativa
OllamaProviderStub = OllamaProvider


def get_ai_provider() -> AIProviderInterface:
    """Retorna o provider configurado, mantendo Ollama como padrão."""
    provider_name = os.getenv("TURING_AI_PROVIDER", "ollama").lower()
    if provider_name in {"bert", "bertimbau"}:
        return BertimbauProvider()
    if provider_name == "mock":
        return MockTuringProvider()
    return OllamaProvider(
        model_name=os.getenv("TURING_OLLAMA_MODEL", "llama3.2:3b")
    )

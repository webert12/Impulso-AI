
import os, re, json, random
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "change-me")

PRODUCTS = {
    "vision_pro": {
        "name": "Vision Pro",
        "description": "Bot/plataforma de geração e análise de sinais para operações de curto prazo.",
        "audiences": [
            "adultos interessados em trading e análise de mercado",
            "pessoas que buscam ferramentas de apoio à análise",
            "traders iniciantes que precisam de organização e alertas"
        ],
        "proof_rules": [
            "não prometer lucro ou taxa de acerto",
            "deixar claro que operações envolvem risco",
            "usar linguagem de ferramenta/apoio à decisão"
        ]
    },
    "salao": {
        "name": "Fio&Caixa - Gestão & Agendamento",
        "description": "SaaS para gestão, agenda, clientes, serviços e financeiro de salões de beleza.",
        "audiences": [
            "donas de salão de beleza",
            "profissionais de beleza com agenda própria",
            "pequenos salões que usam caderno/WhatsApp para organizar a operação"
        ],
        "proof_rules": [
            "não inventar resultados de clientes",
            "mostrar economia de tempo e organização como benefícios, sem garantia"
        ]
    }
}

OBJECTIVES = {
    "leads": "gerar leads qualificados",
    "whatsapp": "levar pessoas para uma conversa no WhatsApp",
    "demo": "conseguir demonstrações/testes",
    "sale": "gerar vendas",
    "content": "gerar conteúdo para atrair público"
}

def clean(s, default=""):
    return (s or default).strip()

def audience_for(product, custom):
    if custom:
        return custom
    return ", ".join(PRODUCTS[product]["audiences"][:2])

def generate(data):
    product = data.get("product", "salao")
    obj = data.get("objective", "whatsapp")
    audience = audience_for(product, clean(data.get("audience")))
    offer = clean(data.get("offer"))
    price = clean(data.get("price"))
    channel = clean(data.get("channel"), "Instagram + WhatsApp")
    tone = clean(data.get("tone"), "profissional, direto e humano")
    brand = PRODUCTS[product]["name"]

    if product == "vision_pro":
        hooks = [
            "Pare de operar sem plano.",
            "Transforme análise em processo.",
            "Mais organização para acompanhar suas operações.",
            "Uma ferramenta para quem quer analisar antes de agir.",
            "Seu processo de análise pode ser mais disciplinado."
        ]
        titles = [
            "Conheça o Vision Pro",
            "Organize sua rotina de análise",
            "Análise antes da entrada",
            "Uma ferramenta para apoiar seu processo",
            "Teste uma nova forma de acompanhar sinais"
        ]
        interests = [
            "trading", "mercado financeiro", "análise técnica",
            "forex", "criptomoedas", "educação financeira", "day trade"
        ]
        ctas = ["Conhecer o Vision Pro", "Ver como funciona", "Falar no WhatsApp", "Solicitar demonstração"]
        creative = [
            "Tela do sistema + destaque para análise/confluências + CTA para conhecer a ferramenta.",
            "Vídeo curto mostrando o fluxo: alerta → confirmação → acompanhamento.",
            "Carrossel: problema → processo → recursos → aviso de risco → CTA."
        ]
        scripts = [
            "Gancho: Você ainda toma decisões sem um processo claro? Mostre rapidamente o Vision Pro, explique que ele é uma ferramenta de apoio à análise e finalize convidando a pessoa a conhecer o sistema. Inclua aviso de risco e nunca prometa resultado.",
            "Gancho: Antes de qualquer entrada, o que você deveria conferir? Mostre os recursos de análise e organização do Vision Pro. CTA: conheça a ferramenta."
        ]
        copy_base = f"Se você acompanha operações de curto prazo, ter um processo organizado pode fazer diferença. O {brand} reúne recursos para acompanhar sinais e critérios de análise em um só lugar. {offer or 'Conheça a ferramenta e veja como funciona.'} Operações financeiras envolvem riscos e não há garantia de lucro."
    else:
        hooks = [
            "Sua agenda ainda depende de caderno e mensagens espalhadas?",
            "Quanto tempo seu salão perde organizando a agenda?",
            "Seu salão precisa de mais organização, não de mais planilhas.",
            "Imagine ter agenda, clientes e financeiro em um só lugar.",
            "Pare de perder informações entre WhatsApp, caderno e planilhas."
        ]
        titles = [
            "Organize seu salão em um só lugar",
            "Agenda + clientes + financeiro",
            "Seu salão mais organizado",
            "Gestão de salão sem complicação",
            "Conheça o Fio&Caixa"
        ]
        interests = [
            "salão de beleza", "cabeleireiro", "manicure",
            "empreendedorismo", "gestão de pequenos negócios",
            "beleza", "MEI", "marketing para salão"
        ]
        ctas = ["Testar agora", "Agendar demonstração", "Conhecer o sistema", "Falar no WhatsApp"]
        creative = [
            "Gravação de tela mostrando agenda, cadastro de clientes e financeiro, com textos curtos na tela.",
            "Antes/depois: caderno + WhatsApp espalhados versus painel organizado.",
            "Carrossel: agenda → clientes → serviços → financeiro → CTA."
        ]
        scripts = [
            "Gancho: sua agenda ainda fica espalhada no WhatsApp e no caderno? Mostre o Fio&Caixa organizando agenda, clientes e financeiro. Finalize com CTA para testar/conhecer.",
            "Gancho: três coisas que uma dona de salão precisa enxergar todos os dias. Mostre agenda, clientes e financeiro no sistema. CTA para demonstração."
        ]
        copy_base = f"Se você administra um salão, organização também é parte do crescimento. O {brand} reúne agenda, clientes, serviços e financeiro em um só lugar. {offer or 'Conheça o sistema e veja como ele pode simplificar sua rotina.'}"

    ctas = list(dict.fromkeys(ctas))
    return {
        "campaign": {
            "name": f"{brand} | {OBJECTIVES.get(obj, obj)} | {channel}",
            "objective": OBJECTIVES.get(obj, obj),
            "audience": audience,
            "offer": offer or "Demonstração/avaliação do produto",
            "budget_note": "Comece com orçamento pequeno e valide criativo/público antes de escalar.",
            "channels": channel
        },
        "ad_sets": [
            {"name": "Conjunto A | Intenção", "audience": audience, "interests": interests[:4]},
            {"name": "Conjunto B | Problema", "audience": audience, "interests": interests[4:]},
            {"name": "Conjunto C | Amplo", "audience": audience, "interests": ["público amplo + criativo forte"]}
        ],
        "copies": [
            copy_base,
            f"{hooks[1]} {copy_base}",
            f"{hooks[0]} {copy_base}"
        ],
        "titles": titles,
        "hooks": hooks,
        "ctas": ctas,
        "creatives": creative,
        "scripts": scripts,
        "ab_tests": [
            {"test": "Hook", "A": hooks[0], "B": hooks[2], "metric": "CTR / retenção inicial"},
            {"test": "Oferta", "A": offer or "Conheça a ferramenta", "B": "Solicite uma demonstração", "metric": "taxa de conversão"},
            {"test": "CTA", "A": ctas[0], "B": ctas[-1], "metric": "cliques / conversas"}
        ],
        "compliance": PRODUCTS[product]["proof_rules"],
        "price": price,
        "tone": tone
    }

@app.route("/")
def index():
    return render_template("index.html", products=PRODUCTS, objectives=OBJECTIVES)

@app.post("/api/generate")
def api_generate():
    data = request.get_json(silent=True) or {}
    return jsonify(generate(data))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=False)

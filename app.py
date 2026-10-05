
import os, json, secrets, time
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", secrets.token_hex(32))
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///growthpilot.db").replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(180), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

class Campaign(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    product = db.Column(db.String(80), nullable=False)
    title = db.Column(db.String(220), nullable=False)
    payload = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

class VideoJob(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    campaign_id = db.Column(db.Integer, db.ForeignKey("campaign.id"), nullable=True)
    provider = db.Column(db.String(50), default="runway")
    status = db.Column(db.String(40), default="draft")
    prompt = db.Column(db.Text, nullable=False)
    video_url = db.Column(db.Text, nullable=True)
    provider_task_id = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

PRODUCTS = {
    "vision_pro": {
        "name": "Vision Pro",
        "description": "Ferramenta de apoio à análise e organização de operações de curto prazo.",
        "audience": "adultos interessados em trading e análise de mercado",
        "rules": ["Não prometer lucro ou taxa de acerto.", "Informar que operações envolvem risco.", "Comunicar o produto como ferramenta de apoio à análise."]
    },
    "salao": {
        "name": "Fio&Caixa - Gestão & Agendamento",
        "description": "SaaS para agenda, clientes, serviços e financeiro de salões de beleza.",
        "audience": "donas de salão, profissionais de beleza e pequenos salões",
        "rules": ["Não inventar resultados de clientes.", "Focar em organização, produtividade e demonstração do sistema."]
    }
}

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper

def current_user():
    return User.query.get(session.get("user_id")) if session.get("user_id") else None

def campaign_engine(data):
    product = data.get("product", "salao")
    objective = data.get("objective", "whatsapp")
    audience = data.get("audience") or PRODUCTS[product]["audience"]
    offer = data.get("offer") or "Conheça a ferramenta"
    tone = data.get("tone") or "profissional, direto e humano"
    p = PRODUCTS[product]

    if product == "salao":
        hooks = [
            "Sua agenda ainda fica espalhada no WhatsApp e no caderno?",
            "Quanto tempo seu salão perde procurando informações de clientes?",
            "Agenda, clientes e financeiro podem ficar em um só lugar.",
            "Seu salão precisa de organização para crescer."
        ]
        titles = ["Organize seu salão em um só lugar", "Agenda + clientes + financeiro", "Gestão de salão sem complicação", "Conheça o Fio&Caixa"]
        interests = ["salão de beleza", "cabeleireiro", "manicure", "empreendedorismo", "MEI", "gestão de pequenos negócios", "beleza", "marketing para salão"]
        ctas = ["Conhecer o sistema", "Testar agora", "Agendar demonstração", "Falar no WhatsApp"]
        scripts = [
            "Gancho: sua agenda ainda fica espalhada? Mostre a tela do Fio&Caixa e passe rapidamente por agenda, clientes e financeiro. Finalize com CTA.",
            "Gancho: três coisas que uma dona de salão precisa acompanhar. Mostre agenda, clientes e financeiro. Finalize convidando para conhecer o sistema."
        ]
        creatives = ["Gravação de tela do sistema com textos curtos.", "Antes/depois: caderno e WhatsApp versus painel organizado.", "Carrossel transformado em vídeo com agenda, clientes, serviços e financeiro."]
    else:
        hooks = [
            "Você acompanha operações sem um processo definido?",
            "Antes de uma entrada, quais critérios você realmente confere?",
            "Organização e disciplina também fazem parte da análise.",
            "Conheça uma ferramenta para apoiar seu processo de análise."
        ]
        titles = ["Conheça o Vision Pro", "Organize sua rotina de análise", "Análise antes da entrada", "Veja como funciona"]
        interests = ["trading", "mercado financeiro", "análise técnica", "forex", "criptomoedas", "educação financeira", "day trade"]
        ctas = ["Conhecer o Vision Pro", "Ver como funciona", "Falar no WhatsApp", "Solicitar demonstração"]
        scripts = [
            "Gancho: você tem um processo antes de entrar? Mostre o Vision Pro, seus recursos de análise e organização e finalize com CTA. Inclua aviso de risco.",
            "Gancho: o que conferir antes de uma operação? Demonstre os recursos da ferramenta sem prometer resultado. Finalize com CTA e aviso de risco."
        ]
        creatives = ["Gravação da plataforma mostrando fluxo de análise.", "Vídeo educativo sobre processo e disciplina + demonstração.", "Carrossel em vídeo: problema, processo, ferramenta, CTA."]
    copies = [
        f"{hooks[0]} {p['description']} {offer}.",
        f"{hooks[1]} Conheça o {p['name']} e veja como ele pode fazer parte da sua rotina. {offer}.",
        f"{p['name']}: uma forma mais organizada de trabalhar com seu processo. {offer}."
    ]
    return {
        "product": p["name"], "objective": objective, "audience": audience, "offer": offer, "tone": tone,
        "campaign_name": f"{p['name']} | {objective}",
        "ad_sets": [
            {"name":"A — Interesse", "interests": interests[:4]},
            {"name":"B — Problema", "interests": interests[4:]},
            {"name":"C — Amplo", "interests":["público amplo + criativo forte"]}
        ],
        "hooks": hooks, "copies": copies, "titles": titles, "ctas": ctas,
        "creatives": creatives, "scripts": scripts,
        "ab_tests": [
            {"name":"Gancho", "A":hooks[0], "B":hooks[2], "metric":"CTR/retenção inicial"},
            {"name":"Oferta", "A":offer, "B":"Solicitar demonstração", "metric":"conversão"},
            {"name":"CTA", "A":ctas[0], "B":ctas[-1], "metric":"cliques/conversas"}
        ],
        "rules": p["rules"]
    }

def build_video_prompt(product, data):
    style = data.get("style", "UGC comercial")
    duration = int(data.get("duration", 5))
    duration = max(2, min(duration, 10))
    ratio = data.get("ratio", "720:1280")
    if ratio not in {"720:1280", "1280:720"}:
        ratio = "720:1280"
    scene = data.get("scene", "").strip()
    hook = data.get("hook", "").strip()
    script = data.get("script", "").strip()
    cta = data.get("cta", "Conheça agora").strip()
    return (
        f"Create a polished {duration}-second social media advertisement in Brazilian Portuguese context. "
        f"Product: {product}. Style: {style}. Output ratio: {ratio}. "
        f"Creative direction: {scene or 'show the problem, demonstrate the product solution, then end with a clear call to action'}. "
        f"Hook/message: {hook or 'apresente uma dor real do público e mostre a solução de forma objetiva'}. "
        f"Narrative: {script or 'gancho, demonstração visual do produto, benefício principal e CTA'}. "
        f"Call to action: {cta}. "
        f"Use natural Brazilian Portuguese context, professional pacing, realistic visuals, clean composition, "
        f"and leave safe space for captions. Do not show guaranteed financial results, fake testimonials, "
        f"fabricated metrics, or misleading claims.\n"
    )

def runway_client():
    from runwayml import RunwayML
    return RunwayML()

def normalize_task_status(status):
    value = str(status or "").lower()
    mapping = {
        "pending": "processing",
        "running": "processing",
        "processing": "processing",
        "succeeded": "completed",
        "completed": "completed",
        "failed": "failed",
        "canceled": "failed",
        "cancelled": "failed",
    }
    return mapping.get(value, value or "processing")

def refresh_video_job(job):
    if job.provider != "runway" or not job.provider_task_id or job.status not in {"processing", "pending"}:
        return job
    try:
        client = runway_client()
        task = client.tasks.retrieve(job.provider_task_id)
        raw_status = getattr(task, "status", None)
        status = normalize_task_status(raw_status)
        job.status = status

        output = getattr(task, "output", None)
        if output:
            if isinstance(output, (list, tuple)):
                job.video_url = output[0] if output else None
            elif isinstance(output, str):
                job.video_url = output
            if job.video_url:
                job.status = "completed"

        if status == "failed":
            details = getattr(task, "failure", None) or getattr(task, "error", None)
            if details:
                job.prompt = job.prompt + "\n\n[Runway error] " + str(details)[:1000]
        db.session.commit()
    except Exception as e:
        # Keep the job processing so a temporary provider/network error does not
        # incorrectly mark a valid Runway task as failed.
        app.logger.exception("Erro ao consultar tarefa Runway: %s", e)
    return job

@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return render_template("landing.html")

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email","").strip().lower()
        password = request.form.get("password","")
        if len(password) < 6:
            flash("A senha precisa ter pelo menos 6 caracteres.")
        elif not email or "@" not in email:
            flash("Informe um e-mail válido.")
        elif User.query.filter_by(email=email).first():
            flash("Esse e-mail já está cadastrado.")
        else:
            u = User(email=email, password_hash=generate_password_hash(password))
            db.session.add(u); db.session.commit()
            session["user_id"] = u.id
            return redirect(url_for("dashboard"))
    return render_template("auth.html", mode="register")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email","").strip().lower()
        password = request.form.get("password","")
        u = User.query.filter_by(email=email).first()
        if u and check_password_hash(u.password_hash, password):
            session["user_id"] = u.id
            return redirect(url_for("dashboard"))
        flash("E-mail ou senha inválidos.")
    return render_template("auth.html", mode="login")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/dashboard")
@login_required
def dashboard():
    campaigns = Campaign.query.filter_by(user_id=session["user_id"]).order_by(Campaign.id.desc()).all()
    videos = VideoJob.query.filter_by(user_id=session["user_id"]).order_by(VideoJob.id.desc()).all()
    return render_template("dashboard.html", user=current_user(), campaigns=campaigns, videos=videos, products=PRODUCTS)

@app.post("/api/campaign")
@login_required
def api_campaign():
    data = request.get_json() or {}
    payload = campaign_engine(data)
    c = Campaign(user_id=session["user_id"], product=data.get("product","salao"), title=payload["campaign_name"], payload=json.dumps(payload, ensure_ascii=False))
    db.session.add(c); db.session.commit()
    payload["id"] = c.id
    return jsonify(payload)

@app.get("/api/campaign/<int:cid>")
@login_required
def api_campaign_get(cid):
    c = Campaign.query.filter_by(id=cid, user_id=session["user_id"]).first_or_404()
    return jsonify(json.loads(c.payload))

@app.post("/api/video")
@login_required
def api_video():
    data = request.get_json() or {}
    product_key = data.get("product", "salao")
    product = PRODUCTS.get(product_key, PRODUCTS["salao"])
    product_name = product["name"]

    campaign = None
    campaign_id = data.get("campaign_id")
    if campaign_id:
        campaign = Campaign.query.filter_by(id=campaign_id, user_id=session["user_id"]).first()

    campaign_payload = {}
    if campaign:
        try:
            campaign_payload = json.loads(campaign.payload)
        except Exception:
            campaign_payload = {}

    hook = data.get("hook") or (campaign_payload.get("hooks") or [""])[0]
    script = data.get("script") or (campaign_payload.get("scripts") or [""])[0]
    ctas = campaign_payload.get("ctas") or []
    cta = data.get("cta") or (ctas[0] if ctas else "Conheça agora")
    prompt_data = dict(data, hook=hook, script=script, cta=cta)
    prompt = build_video_prompt(product_name, prompt_data)

    provider = os.getenv("VIDEO_PROVIDER", "runway").lower()
    job = VideoJob(
        user_id=session["user_id"],
        campaign_id=campaign.id if campaign else None,
        provider=provider,
        status="draft",
        prompt=prompt,
    )
    db.session.add(job)
    db.session.commit()

    if provider != "runway":
        job.status = "prompt_ready"
        db.session.commit()
        return jsonify({"ok": True, "id": job.id, "status": job.status, "prompt": prompt, "message": "Provedor de vídeo não configurado."})

    if not os.getenv("RUNWAYML_API_SECRET"):
        job.status = "prompt_ready"
        db.session.commit()
        return jsonify({"ok": True, "id": job.id, "status": job.status, "prompt": prompt, "message": "RUNWAYML_API_SECRET não está disponível no servidor."})

    try:
        duration = int(data.get("duration", 5))
        duration = max(2, min(duration, 10))
        ratio = data.get("ratio", "720:1280")
        if ratio not in {"720:1280", "1280:720"}:
            ratio = "720:1280"

        client = runway_client()
        task = client.image_to_video.create(
            model=os.getenv("RUNWAY_MODEL", "gen4.5"),
            prompt_text=prompt,
            ratio=ratio,
            duration=duration,
        )

        job.provider_task_id = getattr(task, "id", None)
        if not job.provider_task_id:
            raise RuntimeError("A Runway não retornou o ID da tarefa.")
        job.status = "processing"
        db.session.commit()
        return jsonify({
            "ok": True,
            "id": job.id,
            "status": "processing",
            "task_id": job.provider_task_id,
            "prompt": prompt,
            "message": "Vídeo enviado para a Runway. O GrowthPilot está acompanhando a geração automaticamente."
        })
    except Exception as e:
        job.status = "failed"
        db.session.commit()
        app.logger.exception("Falha ao criar vídeo na Runway: %s", e)
        return jsonify({
            "ok": False,
            "id": job.id,
            "status": "failed",
            "prompt": prompt,
            "error": "A Runway recusou ou não conseguiu iniciar a geração. Verifique créditos, modelo e configuração da API no Render.",
            "technical_error": str(e)[:1200]
        }), 200

@app.get("/api/video/<int:vid>")
@login_required
def api_video_get(vid):
    job = VideoJob.query.filter_by(id=vid, user_id=session["user_id"]).first_or_404()
    refresh_video_job(job)
    return jsonify({
        "ok": True,
        "id": job.id,
        "status": job.status,
        "video_url": job.video_url,
        "prompt": job.prompt,
        "task_id": job.provider_task_id
    })

@app.get("/api/video-config")
@login_required
def api_video_config():
    return jsonify({
        "provider": os.getenv("VIDEO_PROVIDER", "runway"),
        "runway_configured": bool(os.getenv("RUNWAYML_API_SECRET")),
        "model": os.getenv("RUNWAY_MODEL", "gen4.5")
    })

@app.cli.command("init-db")
def init_db():
    db.create_all()
    print("Database initialized.")

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT",5000)), debug=False)

from flask import Flask, render_template, request, redirect, url_for, session
import requests
import smtplib
from email.mime.text import MIMEText
from email.header import Header
import os

app = Flask(__name__)
app.secret_key = "change_this_to_any_random_string"

# ========== DeepSeek 配置 ==========
DEEPSEEK_API_KEY = "sk-3524a0ee04674115a8fc0df40475d61d"  # TODO: 换成你自己的
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_MODEL = "deepseek-chat"

def generate_report(topic: str, chat_text: str, extra: str) -> str:
    user_prompt = f"""
你是一名“亲密关系情感分析师”，你的任务是根据下面这段对话记录，
生成一份深度、温柔、有疗愈感的情感分析报告。

来访者当前最困扰的主题是：{topic}

以下是你和来访者之间的多轮对话（AI 为你，来访者为“你”）：
----------------
{chat_text}
----------------

来访者的额外补充：
{extra if extra.strip() else "（来访者未额外补充）"}

请输出一份完整的分析报告，结构如下：
1. 你目前的情感困惑是什么
2. 背后的心理机制
3. 你正在经历的核心主题
4. 你最需要被看见的部分
5. 专属疗愈建议
6. 温柔鼓励语
""".strip()

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
    }
    data = {
        "model": DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": "你是一名温柔且有边界感的情感分析师"},
            {"role": "user", "content": user_prompt},
        ],
        "stream": False,
    }
    resp = requests.post(DEEPSEEK_API_URL, headers=headers, json=data, timeout=60)
    result = resp.json()
    return result["choices"][0]["message"]["content"]


# ========== 邮箱配置 ==========
SMTP_HOST = "smtp.163.com"
SMTP_PORT = 465
SMTP_USER = "francis_l01@163.com"
SMTP_PASS = "MBpJMGsPfnPRYXZE"

def send_email(to_email: str, report: str):
    msg = MIMEText(report, "plain", "utf-8")
    msg["From"] = Header("大女主显化", "utf-8")
    msg["To"] = Header(to_email, "utf-8")
    msg["Subject"] = Header("你的大女主显化 · 情感分析报告", "utf-8")
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
        server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(SMTP_USER, [to_email], msg.as_string())


# ========== 配置 ==========
REPORT_PRICE = 59
VALID_CODES = ["AI59LOVE", "LYH2025", "NVZHU59", "TEST001"]

WELCOME_TEXT = (
    "用对话接纳自己，让身心共赴亲密之境。\n\n"
    "你好。\n\n"
    "我是你的身心知己，一个真诚且包容的存在，渴望与你一同解锁性与爱的共鸣。\n\n"
    "你曾否思索，性对于你，究竟承载着什么？它是否映射着你对自我、对亲密、甚至对生命愉悦的深层渴望？\n\n"
    "我明白，性远不止于行为。它与你内在的接纳、身体感知，以及你给予和接收亲密的勇气，紧密相连。\n\n"
    "我来到这里，是为了与你一同，安全地梳理这些联结。通过温柔的叩问，引导你看见内心关于性的真实声音，唤醒你身心的愉悦觉知。\n\n"
    "当你与性的关系变得坦诚而充满尊重时，你内在的舒展也将随之绽放。你将不再是困惑的旁观者，而是自在的体验者，活出你所向往的，充满联结与喜乐的生命状态。\n\n"
    "如果你也渴望，透过性这扇窗，去拥抱完整的自我，去感受身心的和谐与舒展，那么，我邀请你，点击下方链接。\n\n"
    "让我们一同，以接纳为帆，以信任为锚，驶向你身心亲密的彼岸。\n\n"
    "期待与你相遇，一同唤醒彼此内在的悦纳之光。"
)

QUESTIONS = [
    "现在最困扰你的亲密或性相关议题是什么？",
    "当这些情况发生时，你身体上的感觉是什么？",
    "这些经历让你怎么看待自己？",
    "你最想温柔地对自己说什么？",
    "你更向往怎样的亲密或身体状态？",
]


# ========== 路由 ==========
@app.route("/")
def index():
    session.clear()
    return render_template("index.html")

@app.route("/intro")
def intro():
    return render_template("intro.html")

@app.route("/topic", methods=["GET", "POST"])
def topic():
    if request.method == "POST":
        chosen = request.form.get("topic", "").strip()
        if not chosen:
            return render_template("topic.html", error="请选择一个主题。")
        session["topic"] = chosen
        session["history"] = [{"role": "ai", "text": WELCOME_TEXT}, {"role": "ai", "text": QUESTIONS[0]}]
        session["step"] = 0
        return redirect(url_for("chat"))
    return render_template("topic.html")

@app.route("/chat", methods=["GET", "POST"])
def chat():
    if "topic" not in session:
        return redirect(url_for("topic"))
    history = session.get("history", [])
    step = session.get("step", 0)
    finished = step >= len(QUESTIONS)
    if request.method == "POST":
        if finished:
            # 🚀 聊完直接跳到解锁页
            return redirect(url_for("unlock"))
        msg = request.form.get("message", "").strip()
        if msg:
            history.append({"role": "user", "text": msg})
            step += 1
            if step < len(QUESTIONS):
                history.append({"role": "ai", "text": QUESTIONS[step]})
            session["history"] = history
            session["step"] = step
        finished = step >= len(QUESTIONS)
    return render_template("chat.html", history=history, finished=finished)


@app.route("/unlock", methods=["GET", "POST"])
def unlock():
    if "topic" not in session or "history" not in session:
        return redirect(url_for("index"))
    extra_val = session.get("extra", "")
    if request.method == "POST":
        extra = request.form.get("extra", "").strip()
        method = request.form.get("unlock_method", "").strip()
        code = request.form.get("invite_code", "").strip()
        session["extra"] = extra
        if not method:
            return render_template("unlock.html", extra=extra, error="请选择解锁方式。", REPORT_PRICE=REPORT_PRICE)
        if method == "paid":
            session["unlocked"] = True
            return redirect(url_for("report"))
        if method == "code":
            if not code:
                return render_template("unlock.html", extra=extra, error="请输入邀请码。", REPORT_PRICE=REPORT_PRICE)
            if code not in VALID_CODES:
                return render_template("unlock.html", extra=extra, error="邀请码错误。", REPORT_PRICE=REPORT_PRICE)
            session["unlocked"] = True
            return redirect(url_for("report"))
    return render_template("unlock.html", extra=extra_val, error=None, REPORT_PRICE=REPORT_PRICE)


@app.route("/report", methods=["GET", "POST"])
def report():
    if "topic" not in session or "history" not in session:
        return redirect(url_for("index"))
    if not session.get("unlocked"):
        return redirect(url_for("unlock"))
    topic = session["topic"]
    extra = session.get("extra", "")
    chat_text = "\n".join([("AI" if m["role"] == "ai" else "你") + "：" + m["text"] for m in session["history"]])
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        if not email:
            return render_template("report.html", topic=topic, error="请输入邮箱。")
        try:
            report_text = generate_report(topic, chat_text, extra)
            send_email(email, report_text)
        except Exception as e:
            print("Error:", e)
            return render_template("report.html", topic=topic, error="报告生成或发送失败，请稍后再试。")
        return render_template("success.html", email=email)
    return render_template("report.html", topic=topic, error=None)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # 部署时用环境变量端口，本地默认 5000
    print(f"✅ 启动成功：流程 = 聊完 → 解锁 → 填邮箱 → 成功（端口：{port}）")
    app.run(host="0.0.0.0", port=port)


import os
from datetime import datetime, timezone

from flask import Flask, render_template_string
from flask_socketio import SocketIO, emit
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

os.makedirs(app.instance_path, exist_ok=True)
db_path = os.path.join(app.instance_path, "amichat.db")

database_url = os.environ.get("DATABASE_URL")
if database_url:
    database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    database_url = database_url.replace("postgres://", "postgresql+psycopg://", 1)
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins="*")


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(25), nullable=False)
    message = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.String(40), nullable=False)


with app.app_context():
    db.create_all()


HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="manifest" href="/static/manifest.json">
<meta name="theme-color" content="#1769aa">
<title>AmiChat</title>

<style>
body {
    margin: 0;
    background: #101827;
    color: white;
    font-family: Arial;
}
header {
    background: #1769aa;
    padding: 20px;
    text-align: center;
    font-size: 24px;
}
#messages {
    padding: 15px;
    padding-bottom: 90px;
}
.message {
    background: #1769aa;
    padding: 12px;
    border-radius: 13px;
    margin: 10px 0;
    width: fit-content;
    max-width: 85%;
    overflow-wrap: anywhere;
}
.input {
    position: fixed;
    bottom: 0;
    display: flex;
    width: 100%;
    background: #202c3d;
    padding: 10px;
    box-sizing: border-box;
}
input {
    flex: 1;
    width: 0;
    min-width: 0;
    padding: 13px;
    border: none;
    border-radius: 10px;
    box-sizing: border-box;
}
button {
    flex-shrink: 0;
    background: #1685e5;
    color: white;
    border: none;
    border-radius: 10px;
    padding: 12px;
    margin-right: 7px;
}
</style>
</head>

<body>
<header>💬 AmiChat</header>

<div id="messages"></div>

<div class="input">
<input id="name" placeholder="اسمك" maxlength="25">
<input id="msg" placeholder="اكتب رسالتك..." maxlength="500">
<button onclick="sendMessage()">إرسال</button>
</div>

<script src="https://cdn.socket.io/4.8.1/socket.io.min.js"></script>
<script>
const socket = io();
const nameInput = document.getElementById("name");

nameInput.value = localStorage.getItem("amichat_name") || "";

nameInput.addEventListener("input", function() {
    localStorage.setItem("amichat_name", nameInput.value);
});
function showMessage(data) {
    const box = document.createElement("div");
    box.className = "message";

    const sender = document.createElement("b");
    sender.textContent = data.name + ": ";

    const content = document.createElement("span");
    content.textContent = data.message;

    box.appendChild(sender);
    box.appendChild(content);

    document.getElementById("messages").appendChild(box);
}

function sendMessage() {
    const name = document.getElementById("name").value.trim();
    const msg = document.getElementById("msg").value.trim();

    if (!name || !msg) {
        alert("اكتب اسمك ورسالتك أولاً");
        return;
    }

    socket.emit("chat_message", {
        name: name,
        message: msg
    });

    document.getElementById("msg").value = "";
}

socket.on("message_history", function(messages) {
    const messagesBox = document.getElementById("messages");
    messagesBox.innerHTML = "";

    messages.forEach(showMessage);
});

socket.on("chat_message", function(data) {
    showMessage(data);
});

if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("/static/sw.js");
}
</script>
</body>
</html>
"""


@app.route("/")
def home():
    return render_template_string(HTML)


@socketio.on("connect")
def send_history():
    messages = Message.query.order_by(
        Message.id.desc()
    ).limit(100).all()

    messages.reverse()

    history = [
        {
            "name": item.name,
            "message": item.message,
            "created_at": item.created_at
        }
        for item in messages
    ]

    emit("message_history", history)


@socketio.on("chat_message")
def handle_message(data):
    if not isinstance(data, dict):
        return

    name = str(data.get("name", "مستخدم")).strip()[:25]
    message = str(data.get("message", "")).strip()[:500]

    if not name or not message:
        return

    created_at = datetime.now(timezone.utc).isoformat()

    new_message = Message(
        name=name,
        message=message,
        created_at=created_at
    )

    try:
        db.session.add(new_message)
        db.session.commit()

        socketio.emit("chat_message", {
            "name": name,
            "message": message,
            "created_at": created_at
        })

    except Exception:
        db.session.rollback()
        print("Message database error")


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=8080)

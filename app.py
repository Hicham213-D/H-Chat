

from flask import Flask, request, jsonify, render_template_string
from flask_socketio import SocketIO, emit

app = Flask(__name__)

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
<script>
if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("/static/sw.js");
}
</script>
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
    box-sizing: border-box;}

button {
    flex-shrink: 0;
    margin: 0;
}
}
button {
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
<input id="name" placeholder="اسمك">
<input id="msg" placeholder="اكتب رسالتك...">
<button onclick="sendMessage()">إرسال</button>
</div>

<script src="https://cdn.socket.io/4.8.1/socket.io.min.js"></script>
<script>
const socket = io();

function sendMessage() {
    const name = document.getElementById("name").value.trim();
    const msg = document.getElementById("msg").value.trim();

    if (!name || !msg) {
        alert("اكتب اسمك ورسالتك أولاً");
        return;
    }

    socket.emit("chat_message", {name: name, message: msg});
    document.getElementById("msg").value = "";
}

socket.on("chat_message", function(data) {
    const box = document.createElement("div");
    box.className = "message";

    const sender = document.createElement("b");
    sender.textContent = data.name + ": ";

    const content = document.createElement("span");
    content.textContent = data.message;

    box.appendChild(sender);
    box.appendChild(content);
    document.getElementById("messages").appendChild(box);
});
</script>
<script>
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

@socketio.on("chat_message")
def handle_message(data):
    name = str(data.get("name", "مستخدم"))[:25]
    message = str(data.get("message", ""))[:500]

    if message.strip():
        emit("chat_message", {
            "name": name,
            "message": message
        }, broadcast=True)

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=8080)

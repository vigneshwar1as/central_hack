from flask import Flask, render_template_string, jsonify, request
import datetime
import time

app = Flask(__name__)

# Dictionary to store data for every ESP that connects
live_data = {}

@app.route("/")
def home():
    return render_template_string(html_page)

@app.route("/api/update", methods=["POST"])
def update_sensor_data():
    try:
        data = request.json
        if not data:
            return jsonify({"status": "error", "message": "Invalid JSON"}), 400
            
        p_id = data.get("id")
        
        if p_id:
            # Add server-side tracking info
            data["last_seen_ts"] = time.time()
            data["last_sync"] = datetime.datetime.now().strftime("%H:%M:%S")
            
            # Ensure default values exist for the UI
            data.setdefault("name", "Unknown Device")
            data.setdefault("priority", "Normal")
            data.setdefault("alert", False)
            
            live_data[p_id] = data
            return jsonify({"status": "success", "received_id": p_id}), 200
        
        return jsonify({"status": "error", "message": "No ID provided"}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/data")
def get_dashboard_data():
    current_time = time.time()
    OFFLINE_THRESHOLD = 20  # Seconds of silence before marking 'Disconnected'
    display_list = []

    # Process all devices that have EVER connected
    for p_id, p_info in live_data.items():
        device_status = p_info.copy()
        
        # Determine if device is silent
        is_silent = (current_time - p_info["last_seen_ts"] > OFFLINE_THRESHOLD)
        
        if is_silent:
            device_status["status_label"] = "Disconnected"
            device_status["is_offline"] = True
        else:
            device_status["status_label"] = device_status.get("priority", "Active")
            device_status["is_offline"] = False
            
        display_list.append(device_status)
    
    # Sort: Alerts first, then Active devices, then Disconnected at the bottom
    display_list.sort(key=lambda x: (not x.get('alert', False), x.get('is_offline', False), x.get('name', '')))
    
    if not display_list:
        return jsonify([{
            "id": "---", "name": "Waiting for Device", "age": "--",
            "condition": "Searching for signals...", "hr": "--", "spo2": "--",
            "bp": "--/--", "temp": "--", "battery": "--", "fall": False,
            "status_label": "Standby", "alert": False, "last_sync": "No Signal", "location": "---"
        }])
        
    return jsonify(display_list)

html_page = """
<!DOCTYPE html>
<html>
<head>
    <title>DASN Multi-Device Monitoring</title>
    <meta charset="UTF-8">
    <style>
        body { margin: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0f172a; color: white; }
        header { padding: 20px; text-align: center; background: #1e293b; font-size: 26px; font-weight: bold; border-bottom: 4px solid #3b82f6; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }
        .container { padding: 20px; display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 20px; }
        .card { background: #1e293b; padding: 20px; border-radius: 12px; border-left: 6px solid #475569; transition: all 0.3s ease; position: relative; }
        
        /* State Styles */
        .alert-active { border-left-color: #ef4444; background: #451a1a; transform: translateY(-5px); box-shadow: 0 10px 15px -3px rgba(239, 68, 68, 0.2); }
        .offline-card { opacity: 0.55; border-left-color: #64748b; filter: grayscale(0.4); }
        
        .row { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 15px; }
        .field { background: #0f172a; padding: 12px; border-radius: 8px; font-size: 0.9em; border: 1px solid #334155; }
        .status-badge { padding: 4px 12px; border-radius: 20px; font-size: 0.75em; font-weight: bold; text-transform: uppercase; }
        
        /* Badge Colors */
        .bg-normal { background: #065f46; color: #34d399; }
        .bg-critical { background: #7f1d1d; color: #fca5a5; animation: pulse 2s infinite; }
        .bg-offline { background: #334155; color: #94a3b8; }
        
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
    </style>
</head>
<body>
<header>DASN – Community Health Monitoring System</header>
<div class="container" id="dashboard"></div>
<script>
function updateUI() {
    fetch('/api/data').then(res => res.json()).then(data => {
        let html = "";
        data.forEach(p => {
            const isAlert = p.alert === true;
            const isOffline = p.is_offline === true;
            const badgeClass = isOffline ? 'bg-offline' : (isAlert ? 'bg-critical' : 'bg-normal');
            
            html += `
            <div class="card ${isAlert && !isOffline ? 'alert-active' : ''} ${isOffline ? 'offline-card' : ''}">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <h2 style="margin:0;">${p.name}</h2>
                    <span class="status-badge ${badgeClass}">
                        ${isOffline ? '○ ' : (isAlert ? '⚠ ' : '● ')}${p.status_label}
                    </span>
                </div>
                <div style="color:#94a3b8; margin: 5px 0 15px 0; font-size: 0.9em;">ID: ${p.id}</div>
                <div class="row">
                    <div class="field">❤️ HR: <b>${p.hr || '--'}</b></div>
                    <div class="field">🫁 SpO₂: <b>${p.spo2 || '--'}%</b></div>
                    <div class="field">🌡 Temp: <b>${p.temp || '--'}°C</b></div>
                    <div class="field">🚶 Fall: <b>${p.fall ? "YES" : "NO"}</b></div>
                    <div class="field" style="grid-column: span 2;">⏱ Last Sync: <b>${p.last_sync || 'No Signal'}</b></div>
                </div>
            </div>`;
        });
        document.getElementById("dashboard").innerHTML = html;
    }).catch(err => console.error("Update Error:", err));
}
setInterval(updateUI, 2000);
updateUI();
</script>
</body>
</html>"""

if __name__ == "__main__":
    # Ensure host is 0.0.0.0 to be visible to ESP32/other devices on Wi-Fi
    app.run(host='0.0.0.0', port=5000, debug=True)

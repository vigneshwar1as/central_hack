from flask import Flask, render_template_string, jsonify, request
import datetime
import time

app = Flask(__name__)

# Stores the latest data and the last time we heard from the device
live_data = {}

# Metadata for your patients
patients_metadata = {
    1: {"name": "Ravi Kumar", "age": 72, "condition": "Hypertension"},
    2: {"name": "Anita Sharma", "age": 68, "condition": "Diabetes"},
    3: {"name": "Joseph Mathew", "age": 75, "condition": "Cardiac Risk"},
    4: {"name": "Meera Iyer", "age": 70, "condition": "Osteoporosis"},
    5: {"name": "Suresh Reddy", "age": 74, "condition": "Respiratory Risk"}
}

@app.route("/")
def home():
    return render_template_string(html_page)

@app.route("/api/update", methods=["POST"])
def update_sensor_data():
    data = request.json
    patient_id = data.get("id")
    
    if patient_id:
        # Store the current time as a 'timestamp' to track 'last seen'
        data["last_seen_ts"] = time.time() 
        data["last_sync"] = datetime.datetime.now().strftime("%H:%M:%S")
        live_data[patient_id] = data
        return jsonify({"status": "success"}), 200
    return jsonify({"status": "error", "message": "No ID provided"}), 400

@app.route("/api/data")
def get_dashboard_data():
    combined_results = []
    current_time = time.time()
    TIMEOUT_SECONDS = 10  # If no data in 10s, consider device offline

    for p_id, meta in patients_metadata.items():
        # Check if we have data AND if that data is fresh
        if p_id in live_data and (current_time - live_data[p_id]["last_seen_ts"] < TIMEOUT_SECONDS):
            combined_results.append({**meta, **live_data[p_id]})
        else:
            # Revert to -- if nothing is received or device timed out
            combined_results.append({
                **meta, 
                "id": p_id, 
                "hr": "--", 
                "spo2": "--", 
                "bp": "--/--", 
                "temp": "--", 
                "battery": "--", 
                "fall": False, 
                "location": "Offline", 
                "last_sync": "No Signal", 
                "alert": False, 
                "priority": "Disconnected"
            })
    
    combined_results.sort(key=lambda x: x.get('alert', False), reverse=True)
    return jsonify(combined_results)

# (The html_page string remains the same as your previous working version)
html_page = """
<!DOCTYPE html>
<html>
<head>
    <title>DASN Community Monitoring</title>
    <meta charset="UTF-8">
    <style>
        body { margin: 0; font-family: Arial; background: #0f172a; color: white; }
        header { padding: 20px; text-align: center; background: #1e293b; font-size: 24px; font-weight: bold; border-bottom: 3px solid #334155; }
        .container { padding: 20px; }
        .card { background: #1e293b; padding: 20px; border-radius: 10px; margin-bottom: 20px; border-left: 5px solid #334155; transition: 0.3s; }
        .alert-border { border-left: 5px solid #ef4444; background: #2d1b1b; }
        .row { display: flex; flex-wrap: wrap; gap: 20px; margin-top: 15px; }
        .field { flex: 1 1 180px; background: #0f172a; padding: 10px; border-radius: 5px; }
        .normal { color: #22c55e; }
        .critical { color: #ef4444; font-weight: bold; }
    </style>
</head>
<body>
<header>DASN – Community Health Monitoring Command Center</header>
<div class="container" id="dashboard"></div>
<script>
function loadData() {
    fetch('/api/data').then(res => res.json()).then(data => {
        let html = "";
        data.forEach(p => {
            const isAlert = p.alert === true;
            html += `
            <div class="card ${isAlert ? 'alert-border' : ''}">
                <div style="display:flex; justify-content:space-between;">
                    <h2>${p.name} (Age ${p.age})</h2>
                    <span class="${isAlert ? 'critical' : 'normal'}">${isAlert ? '⚠ ' + p.priority : '● ' + p.priority}</span>
                </div>
                <p>Condition: ${p.condition}</p>
                <div class="row">
                    <div class="field">❤️ HR: ${p.hr} BPM</div>
                    <div class="field">🫁 SpO₂: ${p.spo2}%</div>
                    <div class="field">🩸 BP: ${p.bp}</div>
                    <div class="field">🌡 Temp: ${p.temp}°C</div>
                    <div class="field">🔋 Battery: ${p.battery}%</div>
                    <div class="field">📍 Location: ${p.location}</div>
                    <div class="field">⏱ Last Sync: ${p.last_sync}</div>
                    <div class="field">🚶 Fall: ${p.fall ? "YES" : "NO"}</div>
                </div>
            </div>`;
        });
        document.getElementById("dashboard").innerHTML = html;
    });
}
setInterval(loadData, 2000);
loadData();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)

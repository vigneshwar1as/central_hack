from flask import Flask, render_template_string, jsonify, request
import datetime
import time

app = Flask(__name__)

# Live data storage (In-memory for this example)
live_data = {}

@app.route("/")
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route("/api/update", methods=["POST"])
def update_sensor_data():
    try:
        data = request.json
        if not data:
            return jsonify({"status": "error", "message": "Invalid JSON"}), 400
            
        p_id = data.get("id")
        if p_id:
            # Server-side metadata
            data["last_seen_ts"] = time.time()
            data["last_sync"] = datetime.datetime.now().strftime("%H:%M:%S")
            data["timestamp"] = datetime.datetime.now().isoformat()
            
            # Default values for UI consistency
            data.setdefault("name", f"Patient {p_id}")
            data.setdefault("condition", "Monitoring")
            data.setdefault("room", "N/A")
            data.setdefault("doctor", "On Call")
            data.setdefault("priority", "Normal")
            data.setdefault("alert", False)
            data.setdefault("alerts", [])
            data.setdefault("risk_score", 0)
            data.setdefault("location", "Home")
            
            live_data[p_id] = data
            return jsonify({"status": "success", "received_id": p_id}), 200
        
        return jsonify({"status": "error", "message": "No ID provided"}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/data")
def get_dashboard_data():
    current_time = time.time()
    OFFLINE_THRESHOLD = 20 
    display_list = []

    for p_id, p_info in live_data.items():
        device_status = p_info.copy()
        is_silent = (current_time - p_info["last_seen_ts"] > OFFLINE_THRESHOLD)
        
        if is_silent:
            device_status["priority"] = "Disconnected"
            device_status["is_offline"] = True
        else:
            device_status["is_offline"] = False
            
        display_list.append(device_status)
    
    # Sort: Higher priority and risk scores first
    priority_order = {'Emergency': 4, 'Critical': 3, 'High': 2, 'Normal': 1, 'Disconnected': 0}
    display_list.sort(key=lambda x: (priority_order.get(x.get('priority'), 0)), reverse=True)
    
    return jsonify(display_list)

@app.route("/api/stats")
def stats():
    current_data = list(live_data.values())
    if not current_data:
        return jsonify({"total_patients": 0, "active_alerts": 0})
    
    return jsonify({
        "total_patients": len(current_data),
        "active_alerts": sum(1 for p in current_data if p.get("alert")),
        "critical_count": sum(1 for p in current_data if p.get("priority") == "Critical"),
        "emergency_count": sum(1 for p in current_data if p.get("priority") == "Emergency"),
        "timestamp": datetime.datetime.now().isoformat()
    })

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>DASN Live Health Monitoring</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        :root {
            --bg-dark: #0f172a;
            --bg-card: #1e293b;
            --bg-header: #2d3a4f;
            --text-primary: #ffffff;
            --text-secondary: #94a3b8;
            --success: #22c55e;
            --warning: #f59e0b;
            --danger: #ef4444;
            --critical: #b91c1c;
            --emergency: #7f1d1d;
            --disconnected: #64748b;
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: 'Inter', -apple-system, sans-serif;
            background: var(--bg-dark);
            color: var(--text-primary);
            line-height: 1.6;
        }

        header {
            background: var(--bg-header);
            padding: 1rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 3px solid #3b82f6;
        }

        .logo { font-size: 1.5rem; font-weight: 700; color: #60a5fa; }

        .stats-bar { display: flex; gap: 2rem; }
        .stat-item { display: flex; flex-direction: column; align-items: center; }
        .stat-label { font-size: 0.8rem; color: var(--text-secondary); }
        .stat-value { font-size: 1.2rem; font-weight: 600; }

        .container { padding: 2rem; max-width: 1600px; margin: 0 auto; }

        .card-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 1.5rem;
        }

        .card {
            background: var(--bg-card);
            border-radius: 16px;
            padding: 1.5rem;
            transition: all 0.3s ease;
            border-left: 4px solid var(--success);
            position: relative;
            overflow: hidden;
        }

        .card.emergency { border-left-color: var(--emergency); background: #2d1a1a; }
        .card.critical { border-left-color: var(--critical); background: #2a1a1a; }
        .card.high { border-left-color: var(--warning); }
        .card.disconnected { border-left-color: var(--disconnected); opacity: 0.7; }

        .risk-meter {
            position: absolute; bottom: 0; left: 0; height: 4px;
            background: linear-gradient(90deg, var(--success), var(--warning), var(--danger));
        }

        .vitals-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
            background: rgba(0, 0, 0, 0.2);
            padding: 1rem;
            border-radius: 12px;
            margin: 1rem 0;
        }

        .vital { display: flex; flex-direction: column; }
        .vital-label { font-size: 0.7rem; color: var(--text-secondary); text-transform: uppercase; }
        .vital-value { font-size: 1.1rem; font-weight: 600; }

        .priority-badge {
            padding: 0.3rem 0.8rem;
            border-radius: 9999px;
            font-size: 0.7rem;
            font-weight: 700;
            text-transform: uppercase;
        }

        .alert-banner {
            background: rgba(239, 68, 68, 0.15);
            border: 1px solid var(--danger);
            padding: 8px;
            border-radius: 8px;
            font-size: 0.9rem;
            margin-top: 10px;
        }

        .abnormal { color: var(--danger); }
    </style>
</head>
<body>
    <header>
        <div class="logo">🏥 DASN Live Dashboard</div>
        <div class="stats-bar">
            <div class="stat-item"><span class="stat-label">Active</span><span class="stat-value" id="activeAlerts">0</span></div>
            <div class="stat-item"><span class="stat-label">Critical</span><span class="stat-value" id="criticalCount">0</span></div>
            <div class="stat-item"><span class="stat-label">Last Sync</span><span class="stat-value" id="lastUpdated">--</span></div>
        </div>
    </header>

    <div class="container">
        <div id="dashboard" class="card-grid">
            <p style="text-align: center; grid-column: 1/-1;">Waiting for device signals...</p>
        </div>
    </div>

    <script>
        function getPriorityColor(p) {
            const colors = {'Emergency':'#7f1d1d','Critical':'#b91c1c','High':'#f59e0b','Normal':'#22c55e','Disconnected':'#64748b'};
            return colors[p] || '#22c55e';
        }

        function updateUI() {
            Promise.all([
                fetch('/api/data').then(res => res.json()),
                fetch('/api/stats').then(res => res.json())
            ]).then(([patients, stats]) => {
                document.getElementById('activeAlerts').textContent = stats.active_alerts || 0;
                document.getElementById('criticalCount').textContent = stats.critical_count || 0;
                document.getElementById('lastUpdated').textContent = new Date().toLocaleTimeString();

                let html = '';
                patients.forEach(p => {
                    const statusClass = p.priority.toLowerCase();
                    html += `
                        <div class="card ${statusClass}">
                            <div class="risk-meter" style="width: ${p.risk_score || 0}%"></div>
                            <div style="display:flex; justify-content:space-between; align-items:start">
                                <div>
                                    <h2 style="font-size:1.1rem">${p.name}</h2>
                                    <p style="font-size:0.8rem; color:var(--text-secondary)">ID: ${p.id} • ${p.condition}</p>
                                </div>
                                <span class="priority-badge" style="background: ${getPriorityColor(p.priority)}">
                                    ${p.priority}
                                </span>
                            </div>
                            
                            <div class="vitals-grid">
                                <div class="vital"><span class="vital-label">Heart Rate</span><span class="vital-value">${p.hr || '--'} BPM</span></div>
                                <div class="vital"><span class="vital-label">SpO2</span><span class="vital-value ${p.spo2 < 90 ? 'abnormal' : ''}">${p.spo2 || '--'}%</span></div>
                                <div class="vital"><span class="vital-label">Temp</span><span class="vital-value">${p.temp || '--'}°C</span></div>
                                <div class="vital"><span class="vital-label">Fall</span><span class="vital-value ${p.fall ? 'abnormal' : ''}">${p.fall ? 'YES' : 'NO'}</span></div>
                            </div>

                            <div style="display:flex; justify-content:space-between; font-size:0.75rem; color:var(--text-secondary)">
                                <span>📍 ${p.location}</span>
                                <span>⏱ ${p.last_sync}</span>
                            </div>
                            ${p.alert ? `<div class="alert-banner">⚠️ <b>Alert:</b> ${p.alerts.join(', ') || 'Abnormal Vitals'}</div>` : ''}
                        </div>
                    `;
                });
                if(patients.length > 0) document.getElementById('dashboard').innerHTML = html;
            });
        }

        setInterval(updateUI, 2000);
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)

#!/usr/bin/env python3
"""
Socket.io Test Server for Phase 3 Testing

This is a simple Flask + Socket.io server for testing the recognition engine's
Socket.io emission. Run this server in one terminal, then run the recognition
engine in another with --socket-url http://localhost:5000

Installation:
    pip install flask flask-socketio python-socketio

Usage:
    python3 test_socket_server.py

Then in another terminal:
    python3 recognition_engine_ui.py --socket-url http://localhost:5000 --debug
"""

import json
from datetime import datetime
from flask import Flask, render_template_string
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'recognition-engine-secret'
socketio = SocketIO(app, cors_allowed_origins="*")

# Store recent events
recent_events = []
max_events = 20

# HTML dashboard for visualization
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Socket.io Recognition Dashboard</title>
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
    <style>
        body {
            font-family: monospace;
            background: #1e1e1e;
            color: #00ff00;
            padding: 20px;
            margin: 0;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        h1 {
            text-align: center;
            color: #00ffff;
            border-bottom: 2px solid #00ffff;
            padding-bottom: 10px;
        }
        .status {
            background: #2a2a2a;
            padding: 15px;
            margin: 10px 0;
            border-left: 4px solid #ff6b6b;
        }
        .status.connected {
            border-left-color: #51cf66;
            color: #51cf66;
        }
        .event {
            background: #2a2a2a;
            padding: 12px;
            margin: 8px 0;
            border-left: 4px solid #845ef7;
            border-radius: 2px;
            font-size: 13px;
        }
        .event.translation {
            border-left-color: #00ff88;
            color: #00ff88;
        }
        .timestamp {
            color: #888;
            font-size: 11px;
        }
        .concept {
            color: #ffff00;
            font-weight: bold;
        }
        .score {
            color: #ff6b6b;
        }
        #events {
            max-height: 600px;
            overflow-y: auto;
        }
        .counter {
            text-align: center;
            font-size: 18px;
            margin: 15px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎯 Socket.io Recognition Engine Dashboard</h1>
        
        <div id="status" class="status">
            <span>🔴 Not connected</span>
        </div>
        
        <div class="counter">
            <span>Events received: <span id="eventCount" style="color: #ffff00;">0</span></span>
        </div>
        
        <h2>📡 Recent Events</h2>
        <div id="events"></div>
    </div>

    <script>
        const socket = io();
        let eventCount = 0;

        socket.on('connect', function() {
            console.log('Connected to server');
            document.getElementById('status').innerHTML = '🟢 Connected to recognition engine';
            document.getElementById('status').classList.add('connected');
        });

        socket.on('disconnect', function() {
            console.log('Disconnected from server');
            document.getElementById('status').innerHTML = '🔴 Disconnected from recognition engine';
            document.getElementById('status').classList.remove('connected');
        });

        socket.on('translation_event', function(data) {
            console.log('Translation event:', data);
            eventCount++;
            document.getElementById('eventCount').innerText = eventCount;
            
            const timestamp = new Date(data.timestamp * 1000).toLocaleTimeString();
            const html = `
                <div class="event translation">
                    <div class="timestamp">${timestamp}</div>
                    <div>📝 <span class="concept">${data.concept_name}</span> 
                         (ID: ${data.concept_id})</div>
                    <div>📊 Score: <span class="score">${data.similarity_score.toFixed(3)}</span></div>
                    <div>🎯 BSL Target: ${data.bsl_target_path || 'N/A'}</div>
                    <div>✅ Status: ${data.verification_status}</div>
                </div>
            `;
            
            const eventsDiv = document.getElementById('events');
            eventsDiv.insertAdjacentHTML('afterbegin', html);
            
            // Keep only last 20 events
            while (eventsDiv.children.length > 20) {
                eventsDiv.removeChild(eventsDiv.lastChild);
            }
        });

        socket.on('sign_recognized', function(data) {
            console.log('Legacy sign_recognized event:', data);
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Serve the dashboard."""
    return render_template_string(HTML_TEMPLATE)

@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    print(f"✅ Recognition engine connected")
    emit('connect_response', {'status': 'server_connected'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    print(f"❌ Recognition engine disconnected")

@socketio.on('translation_event')
def handle_translation_event(data):
    """Handle translation event from recognition engine."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    concept_name = data.get('concept_name', 'UNKNOWN')
    concept_id = data.get('concept_id', '')
    score = data.get('similarity_score', 0)
    bsl_target = data.get('bsl_target_path', 'N/A')
    
    print(f"\n[{timestamp}] 📡 TRANSLATION EVENT")
    print(f"  Concept: {concept_name} ({concept_id})")
    print(f"  Score: {score:.3f}")
    print(f"  BSL Target: {bsl_target}")
    print(f"  Status: {data.get('verification_status', 'unknown')}")
    print(f"  Source: {data.get('source', 'unknown')}")
    
    # Store event
    event_data = {
        'timestamp': timestamp,
        'concept_name': concept_name,
        'concept_id': concept_id,
        'score': score,
        'bsl_target': bsl_target,
        'status': data.get('verification_status', 'unknown')
    }
    recent_events.append(event_data)
    if len(recent_events) > max_events:
        recent_events.pop(0)
    
    # Forward to connected UI clients (if any)
    emit('translation_event', data, broadcast=True, skip_sid=True)

@socketio.on('sign_recognized')
def handle_sign_recognized(data):
    """Handle legacy sign_recognized event (backward compatible)."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"\n[{timestamp}] 📡 LEGACY sign_recognized")
    print(f"  Concept: {data.get('concept', 'unknown')}")
    print(f"  Score: {data.get('score', 0):.3f}")

if __name__ == '__main__':
    print("=" * 70)
    print("🔌 Socket.io Test Server for Recognition Engine")
    print("=" * 70)
    print("\n📍 Server running on: http://localhost:5000")
    print("\n🎯 Dashboard: Open http://localhost:5000 in browser")
    print("\n🚀 To connect recognition engine:")
    print("   python3 recognition_engine_ui.py --socket-url http://localhost:5000 --debug")
    print("\n📡 Server will print events as they arrive.")
    print("   Press Ctrl+C to stop.\n")
    print("-" * 70)
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, 
                 allow_unsafe_werkzeug=True)

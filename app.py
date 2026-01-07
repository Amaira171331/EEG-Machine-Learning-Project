import threading
import time
import numpy as np
import pandas as pd
from flask import Flask, render_template, jsonify, request
from pythonosc import dispatcher, osc_server
from collections import deque
import os 
import json

# ==============================================================================
# CONFIGURATION
# ==============================================================================
OSC_IP, OSC_PORT = "0.0.0.0", 5000      
WEB_PORT = 5001      
WINDOW_SIZE = 10     
SMOOTHING_FACTOR = 0.3 
SAVE_DIR = r"C:\Users\meeta\OneDrive\Desktop\EEFISEF\muse_project"
FULL_SAVE_FILE_PATH = os.path.join(SAVE_DIR, "session_results.csv")

# ==============================================================================
# GLOBAL STATE
# ==============================================================================
data_store = {
    'alpha': deque(maxlen=WINDOW_SIZE), 'beta': deque(maxlen=WINDOW_SIZE), 
    'theta': deque(maxlen=WINDOW_SIZE), 'gamma': deque(maxlen=WINDOW_SIZE),
    'h_alpha': [], 'h_beta': [], 'h_theta': [], 'h_gamma': [], 'h_focus': []
}

session_state = {
    'phase': 'IDLE', 'group': 'test', 'calibration_data': [], 'personal_threshold': 0.5, 
    'interventions': 0, 'smoothed_focus': 0.0, 'low_focus_duration': 0, 'intervention_hold_time': 0
}

def calculate_focus_score():
    if not data_store['alpha'] or len(data_store['alpha']) < WINDOW_SIZE: return 0 
    a, t, b, g = [np.mean(data_store[k]) for k in ['alpha', 'theta', 'beta', 'gamma']]
    total = a + t + b + g
    # Focus Score uses all 4 bands for stability and depth
    return ((b + g) / total) / ((a + t) / total) if total != 0 else 0

def osc_handler(address, *args):
    val = np.mean([x for x in args if not np.isnan(x)])
    key = address.split('/')[-1].split('_')[0]
    if key in data_store: 
        data_store[key].append(val)
        if session_state['phase'] == 'CALIBRATING' and key == 'alpha':
            session_state['calibration_data'].append(calculate_focus_score())
        if session_state['phase'] == 'READING':
            data_store[f'h_{key}'].append(val)
            if key == 'alpha':
                data_store['h_focus'].append(calculate_focus_score())

app = Flask(__name__)

@app.route('/')
def index(): return render_template('index.html')

@app.route('/get_session_content/<sid>')
def get_content(sid):
    json_path = os.path.join(os.path.dirname(__file__), "content.json")
    with open(json_path, 'r') as f:
        data = json.load(f)
        return jsonify(data.get(str(sid), {}))

@app.route('/start_calibration', methods=['POST'])
def start_calib():
    session_state['phase'], session_state['calibration_data'] = 'CALIBRATING', []
    return jsonify({"status": "Started"})

@app.route('/end_calibration', methods=['POST'])
def end_calib():
    session_state['phase'] = 'IDLE'
    if session_state['calibration_data']:
        mean_v = np.mean(session_state['calibration_data'])
        session_state['personal_threshold'] = max(mean_v - (0.15 * np.std(session_state['calibration_data'])), 0.1)
    return jsonify({"threshold": round(session_state['personal_threshold'], 3)})

@app.route('/start_reading', methods=['POST'])
def start_reading():
    d = request.json
    session_state['phase'] = 'READING'
    session_state['group'] = d.get('group', 'test')
    session_state['interventions'] = 0
    for k in ['h_alpha', 'h_beta', 'h_theta', 'h_gamma', 'h_focus']: data_store[k] = []
    return jsonify({"status": "Started"})

@app.route('/get_status')
def get_status():
    raw = calculate_focus_score()
    session_state['smoothed_focus'] = (SMOOTHING_FACTOR * raw) + ((1 - SMOOTHING_FACTOR) * session_state['smoothed_focus'])
    f, t = session_state['smoothed_focus'], session_state['personal_threshold']
    intervene, audio = False, False
    
    if session_state['phase'] == 'READING':
        # Logic runs for both groups to log intervention counts
        if f < t:
            session_state['low_focus_duration'] += 1
            if session_state['low_focus_duration'] == 5:
                session_state['interventions'] += 1
                session_state['intervention_hold_time'] = 10
            if session_state['low_focus_duration'] == 6: audio = True
        else: session_state['low_focus_duration'] = 0
        
        if session_state['intervention_hold_time'] > 0:
            intervene = True
            session_state['intervention_hold_time'] -= 1
            
    return jsonify({
        "focus": round(f, 3), 
        "threshold": round(t, 3), 
        "intervene": intervene, 
        "play_audio": audio, 
        "intervention_count": session_state['interventions']
    })

@app.route('/save_session', methods=['POST'])
def save():
    d = request.json
    if not os.path.exists(SAVE_DIR): os.makedirs(SAVE_DIR)
    row = {
        'User_ID': d.get('user_id'), 
        'Group': d.get('group'),
        'Session': d.get('session_id'), 
        'Date': time.strftime("%Y-%m-%d %H:%M:%S"),
        'Read_Time_Sec': d.get('reading_duration'), 
        'Avg_Focus': round(np.mean(data_store['h_focus']), 4) if data_store['h_focus'] else 0,
        'Avg_Alpha': round(np.mean(data_store['h_alpha']), 4) if data_store['h_alpha'] else 0,
        'Avg_Beta': round(np.mean(data_store['h_beta']), 4) if data_store['h_beta'] else 0,
        'Avg_Theta': round(np.mean(data_store['h_theta']), 4) if data_store['h_theta'] else 0,
        'Avg_Gamma': round(np.mean(data_store['h_gamma']), 4) if data_store['h_gamma'] else 0,
        'Threshold': session_state['personal_threshold'], 
        'Interventions': session_state['interventions'],
        'Quiz_Score': d.get('quiz_score'), 
        'Memory_Score': d.get('memory_score'), 
        'Memory_Errors': d.get('memory_errors')
    }
    df = pd.DataFrame([row])
    df.to_csv(FULL_SAVE_FILE_PATH, mode='a', header=not os.path.exists(FULL_SAVE_FILE_PATH), index=False)
    return jsonify({"status": "Saved"})

def start_osc():
    disp = dispatcher.Dispatcher()
    for b in ['alpha', 'beta', 'theta', 'gamma']: disp.map(f"/muse/elements/{b}_absolute", osc_handler)
    osc_server.ThreadingOSCUDPServer((OSC_IP, OSC_PORT), disp).serve_forever()

if __name__ == '__main__':
    threading.Thread(target=start_osc, daemon=True).start()
    app.run(debug=False, port=WEB_PORT, threaded=True)
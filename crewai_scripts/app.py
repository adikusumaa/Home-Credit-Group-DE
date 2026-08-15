# crewai_scripts/app.py
import os
import sys
import json
from flask import Flask, request, jsonify

sys.path.insert(0, '/opt/crewai')             
sys.path.insert(0, '/opt/airflow/dags')            
sys.path.insert(0, '/opt/airflow/dags/crewai_agents')

try:
    # Import langsung dari crewai_agents.crews
    from crewai_agents.crews import incident_crew
    print("[✓] Import incident_crew sukses dari crewai_agents.crews")
except ImportError as e:
    print(f"[!] Import gagal: {e}")
    # Coba alternatif jika struktur berbeda
    try:
        from crews import incident_crew
        print("[✓] Import incident_crew sukses dari crews (fallback)")
    except ImportError as e2:
        print(f"[✗] KRITIKAL: Tidak bisa import incident_crew. Error: {e2}")
        sys.exit(1)

app = Flask(__name__)

@app.route('/run', methods=['POST'])
def run_crew():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid JSON'}), 400
    dag_id = data.get('dag_id')
    if not dag_id:
        return jsonify({'error': 'Missing dag_id'}), 400
    
    print(f"[API] Menerima request untuk DAG: {dag_id}")
    try:
        result = incident_crew.kickoff(inputs={"dag_id": dag_id})
        return jsonify({
            'status': 'success',
            'dag_id': dag_id,
            'result': str(result)
        })
    except Exception as e:
        print(f"[API] ERROR: {e}")
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
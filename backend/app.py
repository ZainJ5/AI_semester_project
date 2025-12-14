from flask import Flask, request, jsonify
from flask_cors import CORS
from services.ml_service import MLService
from services.graph_service import GraphService
from models.prediction_log import PredictionLogger

app = Flask(__name__)
CORS(app)  

ml_service = MLService()
graph_service = GraphService(ml_service)
logger = PredictionLogger()

@app.route('/api/predict', methods=['POST'])
def predict_endpoint():
    data = request.get_json()
    country = data.get('country')
    if not country: return jsonify({'error': 'No country'}), 400
    
    result = ml_service.predict_country(country)
    return jsonify({'country': country, 'prediction': result})

@app.route('/api/simulation/spread', methods=['POST'])
def spread_simulation_endpoint():
    data = request.get_json()
    country = data.get('country')
    if not country: return jsonify({'error': 'No country'}), 400
    
    graph_data = graph_service.build_simulation_bfs(country)
    return jsonify(graph_data)

@app.route('/api/simulation/path', methods=['POST'])
def path_analysis_endpoint():
    data = request.get_json()
    start = data.get('start_country')
    end = data.get('end_country')
    
    result = graph_service.find_safest_path_a_star(start, end)
    return jsonify(result)

@app.route('/api/logs', methods=['GET'])
def get_logs_endpoint():
    """Get recent prediction logs"""
    limit = request.args.get('limit', default=50, type=int)
    country = request.args.get('country', default=None, type=str)
    
    if country:
        logs = logger.get_logs_by_country(country, limit)
    else:
        logs = logger.get_recent_logs(limit)
    
    return jsonify({
        'total': len(logs),
        'logs': logs
    })

@app.route('/api/logs/clear', methods=['POST'])
def clear_logs_endpoint():
    """Clear all prediction logs"""
    try:
        logger.clear_logs()
        return jsonify({'message': 'Logs cleared successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)

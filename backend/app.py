from flask import Flask, request, jsonify
from flask_cors import CORS
from services.ml_service import MLService
from services.graph_service import GraphService

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

# Initialize Services
ml_service = MLService()
graph_service = GraphService(ml_service)

@app.route('/api/predict', methods=['POST'])
def predict_endpoint():
    # Simple ML Prediction
    data = request.get_json()
    country = data.get('country')
    if not country: return jsonify({'error': 'No country'}), 400
    
    result = ml_service.predict_country(country)
    return jsonify({'country': country, 'prediction': result})

@app.route('/api/simulation/spread', methods=['POST'])
def spread_simulation_endpoint():
    # BFS Endpoint for Graph Visualization
    data = request.get_json()
    country = data.get('country')
    if not country: return jsonify({'error': 'No country'}), 400
    
    # Run BFS
    graph_data = graph_service.build_simulation_bfs(country)
    return jsonify(graph_data)

@app.route('/api/simulation/path', methods=['POST'])
def path_analysis_endpoint():
    # A* Endpoint
    data = request.get_json()
    start = data.get('start_country')
    end = data.get('end_country')
    
    result = graph_service.find_safest_path_a_star(start, end)
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
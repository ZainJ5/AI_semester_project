import heapq
from collections import deque
from services.api_service import APIService
from utils.constants import GEO_COORDS

class GraphService:
    
    def __init__(self, ml_service):
        self.ml_service = ml_service

    def build_simulation_bfs(self, start_country, max_depth=2):
        """
        Uses BFS to simulate disease spread layers.
        Level 0: Start Country
        Level 1: Direct Flights
        Level 2: Connecting Flights
        """
        queue = deque([(start_country, 0)]) # (Country, Depth)
        visited = set([start_country])
        
        nodes = []
        links = []
        
        # Predict for root
        root_pred = self.ml_service.predict_country(start_country)
        nodes.append({
            "id": start_country, 
            "group": 0, 
            "cases": root_pred['malaria'],
            "coords": GEO_COORDS.get(start_country, {'lat': 0, 'lng': 0})
        })

        while queue:
            current_country, depth = queue.popleft()
            
            if depth >= max_depth:
                continue

            # Get neighbors (Flights)
            neighbors = APIService.fetch_flight_connections(current_country)
            
            for neighbor in neighbors:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, depth + 1))
                    
                    # Predict for neighbor
                    pred = self.ml_service.predict_country(neighbor)
                    
                    nodes.append({
                        "id": neighbor,
                        "group": depth + 1,
                        "cases": pred['malaria'],
                        "coords": GEO_COORDS.get(neighbor, {'lat': 0, 'lng': 0})
                    })
                
                # Add Link
                links.append({
                    "source": current_country,
                    "target": neighbor,
                    "value": 1 # Weight could be flight volume
                })
        
        return {"nodes": nodes, "links": links}

    def find_safest_path_a_star(self, start, end):
        """
        Uses A* to find a path.
        Cost = Disease Cases (We want to find path with LOWEST disease risk).
        Heuristic = Physical Distance (Haversine approximation).
        """
        # Priority Queue: (Estimated_Total_Cost, Current_Cost, Current_Node, Path_History)
        pq = [(0, 0, start, [start])]
        visited = set()
        
        while pq:
            est_total, current_cost, current_node, path = heapq.heappop(pq)
            
            if current_node == end:
                return {"path": path, "total_risk_cost": current_cost}
            
            if current_node in visited:
                continue
            visited.add(current_node)
            
            neighbors = APIService.fetch_flight_connections(current_node)
            
            for neighbor in neighbors:
                if neighbor not in visited:
                    # Cost = Predicted Cases in Neighbor (The "danger" of going there)
                    pred = self.ml_service.predict_country(neighbor)
                    risk_cost = pred['malaria'] / 1000.0 # Normalize logic
                    
                    new_cost = current_cost + risk_cost
                    
                    # Heuristic: Simple Euclidean distance diff between lat/long (Simplified)
                    c1 = GEO_COORDS.get(neighbor, {'lat':0, 'lng':0})
                    c2 = GEO_COORDS.get(end, {'lat':0, 'lng':0})
                    heuristic = abs(c1['lat'] - c2['lat']) + abs(c1['lng'] - c2['lng'])
                    
                    heapq.heappush(pq, (new_cost + heuristic, new_cost, neighbor, path + [neighbor]))
                    
        return {"error": "No path found"}
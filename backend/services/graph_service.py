import heapq
from collections import deque
from services.api_service import APIService
from utils.constants import GEO_COORDS, REGION_MAP

class GraphService:
    
    def __init__(self, ml_service):
        self.ml_service = ml_service

    def build_simulation_bfs(self, start_country, max_depth=2):
        """
        Uses BFS to simulate disease spread layers.
        Level 0: Start Country
        Level 1: Direct Flights
        Level 2: Connecting Flights
        
        Only processes countries from the training dataset (120 countries).
        """
        # Validate start country is in training dataset
        if start_country not in REGION_MAP:
            return {
                "error": f"Country '{start_country}' not found in training dataset",
                "nodes": [],
                "links": []
            }
        
        queue = deque([(start_country, 0)])  # (Country, Depth)
        visited = set([start_country])
        
        nodes = []
        links = []
        
        # Predict for root
        try:
            root_pred = self.ml_service.predict_country(start_country)
            nodes.append({
                "id": start_country, 
                "group": 0, 
                "cases": root_pred['malaria'],
                "risk_level": root_pred['risk_level'],
                "coords": GEO_COORDS.get(start_country, {'lat': 0, 'lng': 0})
            })
        except Exception as e:
            return {
                "error": f"Failed to predict for {start_country}: {str(e)}",
                "nodes": [],
                "links": []
            }

        while queue:
            current_country, depth = queue.popleft()
            
            if depth >= max_depth:
                continue

            # Get neighbors (Flights) - already filtered to dataset countries
            neighbors = APIService.fetch_flight_connections(current_country)
            
            for neighbor in neighbors:
                # Double-check neighbor is in training dataset
                if neighbor not in REGION_MAP:
                    continue
                    
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, depth + 1))
                    
                    # Predict for neighbor
                    try:
                        pred = self.ml_service.predict_country(neighbor)
                        
                        nodes.append({
                            "id": neighbor,
                            "group": depth + 1,
                            "cases": pred['malaria'],
                            "risk_level": pred['risk_level'],
                            "coords": GEO_COORDS.get(neighbor, {'lat': 0, 'lng': 0})
                        })
                    except Exception as e:
                        print(f"Warning: Failed to predict for {neighbor}: {e}")
                        continue
                
                # Add Link
                links.append({
                    "source": current_country,
                    "target": neighbor,
                    "value": 1  # Weight could be flight volume
                })
        
        return {
            "nodes": nodes, 
            "links": links,
            "total_countries": len(nodes),
            "max_depth": max_depth
        }

    def find_safest_path_a_star(self, start, end):
        """
        Uses A* to find the safest path between two countries.
        
        Cost Function: Disease risk (malaria cases) - LOWER is better
        Heuristic: Geographic distance (Manhattan distance using lat/lng)
        
        Only processes countries from the training dataset (120 countries).
        
        Returns path with lowest cumulative disease risk.
        """
        # Validate both countries are in training dataset
        if start not in REGION_MAP:
            return {"error": f"Start country '{start}' not found in training dataset"}
        if end not in REGION_MAP:
            return {"error": f"End country '{end}' not found in training dataset"}
        
        if start == end:
            return {
                "path": [start],
                "total_risk_cost": 0,
                "message": "Start and end countries are the same"
            }
        
        # Priority Queue: (Estimated_Total_Cost, Current_Cost, Current_Node, Path_History)
        pq = [(0, 0, start, [start])]
        visited = set()
        
        # Track best costs to avoid revisiting with worse cost
        best_cost = {start: 0}
        
        while pq:
            est_total, current_cost, current_node, path = heapq.heappop(pq)
            
            if current_node == end:
                # Get predictions for all nodes in path for details
                path_details = []
                for country in path:
                    try:
                        pred = self.ml_service.predict_country(country)
                        path_details.append({
                            "country": country,
                            "malaria_cases": pred['malaria'],
                            "dengue_cases": pred['dengue'],
                            "risk_level": pred['risk_level']
                        })
                    except Exception as e:
                        print(f"Warning: Failed to get details for {country}: {e}")
                        path_details.append({
                            "country": country,
                            "malaria_cases": 0,
                            "error": str(e)
                        })
                
                return {
                    "path": path,
                    "total_risk_cost": round(current_cost, 2),
                    "path_length": len(path),
                    "path_details": path_details
                }
            
            if current_node in visited:
                continue
            visited.add(current_node)
            
            # Get flight connections (already filtered to dataset countries)
            neighbors = APIService.fetch_flight_connections(current_node)
            
            for neighbor in neighbors:
                # Double-check neighbor is in training dataset
                if neighbor not in REGION_MAP or neighbor in visited:
                    continue
                
                try:
                    # Cost = Predicted malaria cases in neighbor (disease risk)
                    pred = self.ml_service.predict_country(neighbor)
                    
                    # Normalize risk: divide by 100 to keep costs reasonable
                    # Higher malaria cases = higher cost (less safe)
                    risk_cost = pred['malaria'] / 100.0
                    
                    new_cost = current_cost + risk_cost
                    
                    # Only proceed if this is a better path to this neighbor
                    if neighbor in best_cost and new_cost >= best_cost[neighbor]:
                        continue
                    best_cost[neighbor] = new_cost
                    
                    # Heuristic: Manhattan distance (simplified geographic distance)
                    c1 = GEO_COORDS.get(neighbor, {'lat': 0, 'lng': 0})
                    c2 = GEO_COORDS.get(end, {'lat': 0, 'lng': 0})
                    heuristic = abs(c1['lat'] - c2['lat']) + abs(c1['lng'] - c2['lng'])
                    
                    # A* formula: f(n) = g(n) + h(n)
                    estimated_total = new_cost + heuristic
                    
                    heapq.heappush(pq, (estimated_total, new_cost, neighbor, path + [neighbor]))
                    
                except Exception as e:
                    print(f"Warning: Failed to process neighbor {neighbor}: {e}")
                    continue
                    
        return {
            "error": f"No path found between {start} and {end}",
            "visited_countries": len(visited)
        }
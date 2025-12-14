import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, CircleMarker, Polyline, Popup, useMap } from 'react-leaflet';
import { Route, Navigation, AlertCircle } from 'lucide-react';
import CountrySelect from './CountrySelect';
import LoadingSpinner from './LoadingSpinner';
import StatsCard from './StatsCard';
import { apiService } from '../services/api';
import 'leaflet/dist/leaflet.css';

const MapController = ({ center }) => {
  const map = useMap();
  useEffect(() => {
    if (center) {
      map.setView(center, 3);
    }
  }, [center, map]);
  return null;
};

const PathAnalysis = () => {
  const [startCountry, setStartCountry] = useState('');
  const [endCountry, setEndCountry] = useState('');
  const [loading, setLoading] = useState(false);
  const [pathData, setPathData] = useState(null);
  const [error, setError] = useState(null);

  const handleFindPath = async () => {
    if (!startCountry || !endCountry) {
      setError('Please select both start and end countries');
      return;
    }

    if (startCountry === endCountry) {
      setError('Start and end countries must be different');
      return;
    }

    setLoading(true);
    setError(null);
    setPathData(null);

    try {
      const result = await apiService.findSafestPath(startCountry, endCountry);
      setPathData(result);
    } catch (err) {
      setError('Failed to find path. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Mock coordinates - you should import from backend's GEO_COORDS
  const getCoordinates = (country) => {
    const coords = {
      'Pakistan': { lat: 30.3753, lng: 69.3451 },
      'Bangladesh': { lat: 23.6850, lng: 90.3563 },
      'Iran': { lat: 32.4279, lng: 53.6880 },
      'United Arab Emirates': { lat: 23.4241, lng: 53.8478 },
      'Saudi Arabia': { lat: 23.8859, lng: 45.0792 },
      'Germany': { lat: 51.1657, lng: 10.4515 },
      'Belgium': { lat: 50.5039, lng: 4.4699 },
      'Egypt': { lat: 26.8206, lng: 30.8025 },
      'Ethiopia': { lat: 9.1450, lng: 40.4897 },
      'Kenya': { lat: -0.0236, lng: 37.9062 },
      'Nigeria': { lat: 9.0820, lng: 8.6753 },
      'Brazil': { lat: -14.2350, lng: -51.9253 },
      'Mexico': { lat: 23.6345, lng: -102.5528 },
      'Japan': { lat: 36.2048, lng: 138.2529 },
      'Singapore': { lat: 1.3521, lng: 103.8198 },
      // Add more as needed
    };
    return coords[country] || { lat: 0, lng: 0 };
  };

  const mapCenter = pathData && pathData.path && pathData.path.length > 0
    ? [getCoordinates(pathData.path[0]).lat, getCoordinates(pathData.path[0]).lng]
    : [20, 0];

  return (
    <div className="path-analysis-container">
      <div className="path-header">
        <Route size={32} className="header-icon" />
        <div>
          <h2>Safest Path Analysis</h2>
          <p>A* algorithm to find the route with lowest disease risk between countries</p>
        </div>
      </div>

      <div className="path-control">
        <div className="path-inputs">
          <div className="input-group">
            <label>Start Country</label>
            <CountrySelect 
              value={startCountry}
              onChange={setStartCountry}
              placeholder="Select start country"
            />
          </div>
          <Navigation size={24} className="arrow-icon" />
          <div className="input-group">
            <label>Destination Country</label>
            <CountrySelect 
              value={endCountry}
              onChange={setEndCountry}
              placeholder="Select destination"
            />
          </div>
        </div>
        <button 
          className="btn btn-primary"
          onClick={handleFindPath}
          disabled={!startCountry || !endCountry || loading}
        >
          {loading ? 'Finding Path...' : 'Find Safest Path'}
        </button>
      </div>

      {error && <div className="alert alert-error">{error}</div>}
      {loading && <LoadingSpinner message="Calculating safest route using A*..." />}

      {pathData && (
        <>
          {pathData.path ? (
            <>
              <div className="stats-grid">
                <StatsCard
                  title="Total Risk Score"
                  value={pathData.total_risk_cost?.toFixed(4) || 'N/A'}
                  icon={AlertCircle}
                  color="#ef4444"
                  subtitle="Lower is safer"
                />
                <StatsCard
                  title="Stops"
                  value={pathData.path.length - 1}
                  icon={Route}
                  color="#3b82f6"
                  subtitle={`${pathData.path.length} countries`}
                />
              </div>

              <div className="path-route">
                <h4>Route</h4>
                <div className="route-path">
                  {pathData.path.map((country, idx) => (
                    <React.Fragment key={idx}>
                      <span className="route-country">{country}</span>
                      {idx < pathData.path.length - 1 && (
                        <span className="route-arrow">→</span>
                      )}
                    </React.Fragment>
                  ))}
                </div>
              </div>

              <div className="map-container">
                <MapContainer 
                  center={mapCenter} 
                  zoom={3} 
                  style={{ height: '500px', width: '100%' }}
                  scrollWheelZoom={true}
                >
                  <MapController center={mapCenter} />
                  <TileLayer
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                  />
                  
                  {/* Draw path */}
                  <Polyline
                    positions={pathData.path.map(country => {
                      const coords = getCoordinates(country);
                      return [coords.lat, coords.lng];
                    })}
                    color="#3b82f6"
                    weight={3}
                    opacity={0.8}
                  />

                  {/* Draw markers */}
                  {pathData.path.map((country, idx) => {
                    const coords = getCoordinates(country);
                    const isStart = idx === 0;
                    const isEnd = idx === pathData.path.length - 1;
                    
                    return (
                      <CircleMarker
                        key={`marker-${idx}`}
                        center={[coords.lat, coords.lng]}
                        radius={isStart || isEnd ? 10 : 6}
                        fillColor={isStart ? '#10b981' : isEnd ? '#ef4444' : '#3b82f6'}
                        color="#ffffff"
                        weight={2}
                        opacity={1}
                        fillOpacity={0.8}
                      >
                        <Popup>
                          <div className="map-popup">
                            <strong>{country}</strong>
                            <div>
                              {isStart && 'Start Point'}
                              {isEnd && 'Destination'}
                              {!isStart && !isEnd && `Stop ${idx}`}
                            </div>
                          </div>
                        </Popup>
                      </CircleMarker>
                    );
                  })}
                </MapContainer>
              </div>

              <div className="path-legend">
                <h4>Route Legend</h4>
                <div className="legend-items">
                  <div className="legend-item">
                    <span className="legend-color" style={{ backgroundColor: '#10b981' }}></span>
                    <span>Start Point</span>
                  </div>
                  <div className="legend-item">
                    <span className="legend-color" style={{ backgroundColor: '#3b82f6' }}></span>
                    <span>Transit Points</span>
                  </div>
                  <div className="legend-item">
                    <span className="legend-color" style={{ backgroundColor: '#ef4444' }}></span>
                    <span>Destination</span>
                  </div>
                </div>
              </div>
            </>
          ) : (
            <div className="alert alert-info">
              No path found between the selected countries. They may not be connected through available flight routes.
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default PathAnalysis;

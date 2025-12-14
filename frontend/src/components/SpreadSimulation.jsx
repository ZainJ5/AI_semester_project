import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, CircleMarker, Polyline, Popup, useMap } from 'react-leaflet';
import { GitBranch, Play, Info, Pause, RotateCcw, Activity, TrendingUp, Globe } from 'lucide-react';
import CountrySelect from './CountrySelect';
import LoadingSpinner from './LoadingSpinner';
import { apiService } from '../services/api';
import 'leaflet/dist/leaflet.css';

// Component to reset map view
const MapController = ({ center }) => {
  const map = useMap();
  useEffect(() => {
    if (center) {
      map.setView(center, 3);
    }
  }, [center, map]);
  return null;
};

const SpreadSimulation = () => {
  const [selectedCountry, setSelectedCountry] = useState('');
  const [loading, setLoading] = useState(false);
  const [simulationData, setSimulationData] = useState(null);
  const [error, setError] = useState(null);
  const [animationStep, setAnimationStep] = useState(0);
  const [isAnimating, setIsAnimating] = useState(false);

  const handleSimulate = async () => {
    if (!selectedCountry) {
      setError('Please select a country');
      return;
    }

    console.log('[Simulation] Starting simulation for:', selectedCountry);
    setLoading(true);
    setError(null);
    setSimulationData(null);
    setAnimationStep(0);

    try {
      const result = await apiService.getSpreadSimulation(selectedCountry);
      console.log('[Simulation] Received result:', result);
      console.log('[Simulation] Nodes:', result.nodes?.length, 'Links:', result.links?.length);
      setSimulationData(result);
    } catch (err) {
      console.error('[Simulation] Error occurred:', err);
      setError('Failed to fetch simulation. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const startAnimation = () => {
    setIsAnimating(true);
    setAnimationStep(0);
  };

  const pauseAnimation = () => {
    setIsAnimating(false);
  };

  const resetAnimation = () => {
    setIsAnimating(false);
    setAnimationStep(simulationData ? simulationData.nodes.length : 0);
  };

  useEffect(() => {
    if (isAnimating && simulationData) {
      const maxSteps = simulationData.nodes.length;
      if (animationStep < maxSteps) {
        const timer = setTimeout(() => {
          setAnimationStep(prev => prev + 1);
        }, 800);
        return () => clearTimeout(timer);
      } else {
        setIsAnimating(false);
      }
    }
  }, [isAnimating, animationStep, simulationData]);

  const getNodeColor = (group) => {
    const colors = ['#ef4444', '#f97316', '#f59e0b', '#84cc16'];
    return colors[group] || '#64748b';
  };

  const getNodeRadius = (cases) => {
    return Math.max(5, Math.min(20, cases / 5));
  };

  const visibleNodes = simulationData ? simulationData.nodes.slice(0, animationStep + 1) : [];
  const visibleLinks = simulationData 
    ? simulationData.links.filter(link => 
        visibleNodes.some(n => n.id === link.source) && 
        visibleNodes.some(n => n.id === link.target)
      )
    : [];

  const mapCenter = simulationData && simulationData.nodes.length > 0
    ? [simulationData.nodes[0].coords.lat, simulationData.nodes[0].coords.lng]
    : [20, 0];

  return (
    <div className="spread-simulation-container">
      <div className="simulation-header">
        <GitBranch size={32} className="header-icon" />
        <div>
          <h2>Disease Spread Simulation</h2>
          <p>BFS-based visualization showing how disease spreads through flight connections</p>
        </div>
      </div>

      <div className="simulation-control">
        <CountrySelect 
          value={selectedCountry}
          onChange={setSelectedCountry}
          placeholder="Select origin country"
        />
        <button 
          className="btn btn-primary"
          onClick={handleSimulate}
          disabled={!selectedCountry || loading}
        >
          {loading ? 'Simulating...' : 'Run Simulation'}
        </button>
        {simulationData && !isAnimating && (
          <button 
            className="btn btn-secondary"
            onClick={startAnimation}
          >
            <Play size={18} />
            Animate Spread
          </button>
        )}
      </div>

      {error && <div className="alert alert-error">{error}</div>}
      {loading && <LoadingSpinner message="Running BFS simulation..." />}

      {simulationData && (
        <>
          <div className="simulation-info">
            <Info size={18} />
            <span>
              Showing {visibleNodes.length} of {simulationData.nodes.length} countries
              {isAnimating && ' (Animating...)'}
            </span>
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
              
              {/* Draw connections */}
              {visibleLinks.map((link, idx) => {
                const sourceNode = simulationData.nodes.find(n => n.id === link.source);
                const targetNode = simulationData.nodes.find(n => n.id === link.target);
                if (sourceNode && targetNode) {
                  return (
                    <Polyline
                      key={`link-${idx}`}
                      positions={[
                        [sourceNode.coords.lat, sourceNode.coords.lng],
                        [targetNode.coords.lat, targetNode.coords.lng]
                      ]}
                      color="#94a3b8"
                      weight={1}
                      opacity={0.5}
                    />
                  );
                }
                return null;
              })}

              {/* Draw nodes */}
              {visibleNodes.map((node, idx) => (
                <CircleMarker
                  key={`node-${idx}`}
                  center={[node.coords.lat, node.coords.lng]}
                  radius={getNodeRadius(node.cases)}
                  fillColor={getNodeColor(node.group)}
                  color="#ffffff"
                  weight={2}
                  opacity={1}
                  fillOpacity={0.7}
                >
                  <Popup>
                    <div className="map-popup">
                      <strong>{node.id}</strong>
                      <div>Level: {node.group}</div>
                      <div>Cases: {node.cases.toFixed(2)}</div>
                    </div>
                  </Popup>
                </CircleMarker>
              ))}
            </MapContainer>
          </div>

          <div className="simulation-legend">
            <h4>Spread Levels</h4>
            <div className="legend-items">
              <div className="legend-item">
                <span className="legend-color" style={{ backgroundColor: '#ef4444' }}></span>
                <span>Level 0 - Origin</span>
              </div>
              <div className="legend-item">
                <span className="legend-color" style={{ backgroundColor: '#f97316' }}></span>
                <span>Level 1 - Direct</span>
              </div>
              <div className="legend-item">
                <span className="legend-color" style={{ backgroundColor: '#f59e0b' }}></span>
                <span>Level 2 - Indirect</span>
              </div>
            </div>
          </div>

          <div className="simulation-stats">
            <div className="stat-item">
              <span className="stat-label">Total Countries Affected:</span>
              <span className="stat-value">{simulationData.nodes.length}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Flight Connections:</span>
              <span className="stat-value">{simulationData.links.length}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Average Cases:</span>
              <span className="stat-value">
                {(simulationData.nodes.reduce((sum, n) => sum + n.cases, 0) / simulationData.nodes.length).toFixed(2)}
              </span>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default SpreadSimulation;

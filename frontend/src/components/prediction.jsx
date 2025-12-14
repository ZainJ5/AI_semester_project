import React, { useState } from 'react';
import { Activity, Droplets, Users, MapPin, TrendingUp, Calendar } from 'lucide-react';
import CountrySelect from './CountrySelect';
import LoadingSpinner from './LoadingSpinner';
import StatsCard from './StatsCard';
import { apiService } from '../services/api';

const Prediction = () => {
  const [selectedCountry, setSelectedCountry] = useState('');
  const [loading, setLoading] = useState(false);
  const [prediction, setPrediction] = useState(null);
  const [error, setError] = useState(null);

  const handlePredict = async () => {
    if (!selectedCountry) {
      setError('Please select a country');
      return;
    }

    console.log('[Prediction] Starting prediction for:', selectedCountry);
    setLoading(true);
    setError(null);
    setPrediction(null);

    try {
      const result = await apiService.predictCountry(selectedCountry);
      console.log('[Prediction] Received result:', result);
      console.log('[Prediction] Prediction data:', result.prediction);
      setPrediction(result);
    } catch (err) {
      console.error('[Prediction] Error occurred:', err);
      setError('Failed to fetch prediction. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const getRiskLevel = (cases) => {
    if (cases < 50) return { level: 'Low', color: '#10b981', bgColor: '#d1fae5' };
    if (cases < 80) return { level: 'Medium', color: '#f59e0b', bgColor: '#fef3c7' };
    return { level: 'High', color: '#ef4444', bgColor: '#fee2e2' };
  };

  return (
    <div className="prediction-container">
      <div className="prediction-header">
        <Activity size={32} className="header-icon" />
        <div>
          <h2>Disease Prediction</h2>
          <p>Select a country to predict malaria cases using ML model</p>
        </div>
      </div>

      <div className="prediction-control">
        <CountrySelect 
          value={selectedCountry}
          onChange={setSelectedCountry}
          placeholder="Select a country for prediction"
        />
        <button 
          className="btn btn-primary"
          onClick={handlePredict}
          disabled={!selectedCountry || loading}
        >
          {loading ? 'Predicting...' : 'Predict Cases'}
        </button>
      </div>

      {error && (
        <div className="alert alert-error">
          {error}
        </div>
      )}

      {loading && <LoadingSpinner message="Analyzing data and predicting..." />}

      {prediction && (
        <div className="prediction-results">
          <div className="result-header">
            <MapPin size={24} />
            <h3>{prediction.country}</h3>
          </div>

          <div className="stats-grid">
            <StatsCard
              title="Predicted Malaria Cases"
              value={prediction.prediction?.malaria?.toFixed(2) || 'N/A'}
              icon={Activity}
              color="#ef4444"
              subtitle="Cases per month"
            />
            <StatsCard
              title="Predicted Dengue Cases"
              value={prediction.prediction?.dengue?.toFixed(2) || 'N/A'}
              icon={Droplets}
              color="#8b5cf6"
              subtitle="Cases per month"
            />
          </div>

          {prediction.prediction?.malaria && (
            <div className="risk-assessment">
              <h4>Risk Assessment</h4>
              <div 
                className="risk-badge"
                style={{
                  backgroundColor: getRiskLevel(prediction.prediction.malaria).bgColor,
                  color: getRiskLevel(prediction.prediction.malaria).color,
                }}
              >
                <span className="risk-level">
                  {getRiskLevel(prediction.prediction.malaria).level} Risk
                </span>
                <span className="risk-value">
                  {prediction.prediction.malaria.toFixed(2)} cases/month
                </span>
              </div>
            </div>
          )}

          {prediction.prediction?.features_used && (
            <>
              {/* Environmental Factors */}
              <div className="features-details">
                <h4>🌡️ Environmental Conditions</h4>
                <div className="features-grid">
                  <div className="feature-item">
                    <TrendingUp size={18} />
                    <span className="feature-label">Temperature:</span>
                    <span className="feature-value">
                      {prediction.prediction.features_used.temperature?.toFixed(1)}°C
                    </span>
                  </div>
                  <div className="feature-item">
                    <Droplets size={18} />
                    <span className="feature-label">Humidity:</span>
                    <span className="feature-value">
                      {prediction.prediction.features_used.humidity}%
                    </span>
                  </div>
                  <div className="feature-item">
                    <Droplets size={18} />
                    <span className="feature-label">Precipitation:</span>
                    <span className="feature-value">
                      {prediction.prediction.features_used.precipitation} mm
                    </span>
                  </div>
                  <div className="feature-item">
                    <Activity size={18} />
                    <span className="feature-label">Vector Index:</span>
                    <span className="feature-value">
                      {prediction.prediction.features_used.vector_index?.toFixed(2)}
                    </span>
                  </div>
                  <div className="feature-item">
                    <Droplets size={18} />
                    <span className="feature-label">Water Stagnation:</span>
                    <span className="feature-value">
                      {prediction.prediction.features_used.water_stagnation_index?.toFixed(2)}
                    </span>
                  </div>
                </div>
              </div>

              {/* Population & Healthcare */}
              <div className="features-details">
                <h4>🏥 Population & Healthcare</h4>
                <div className="features-grid">
                  <div className="feature-item">
                    <Users size={18} />
                    <span className="feature-label">Population Density:</span>
                    <span className="feature-value">
                      {prediction.prediction.features_used.population_density?.toFixed(1)} /km²
                    </span>
                  </div>
                  <div className="feature-item">
                    <Activity size={18} />
                    <span className="feature-label">Healthcare Budget:</span>
                    <span className="feature-value">
                      ${prediction.prediction.features_used.healthcare_budget?.toFixed(0)}/capita
                    </span>
                  </div>
                  <div className="feature-item">
                    <MapPin size={18} />
                    <span className="feature-label">Region:</span>
                    <span className="feature-value">
                      {prediction.prediction.features_used.region}
                    </span>
                  </div>
                  <div className="feature-item">
                    <Calendar size={18} />
                    <span className="feature-label">Time Period:</span>
                    <span className="feature-value">
                      {new Date(0, prediction.prediction.features_used.month - 1).toLocaleString('default', { month: 'short' })} {prediction.prediction.features_used.year}
                    </span>
                  </div>
                </div>
              </div>

              {/* Historical Malaria Data */}
              <div className="features-details">
                <h4>📊 Historical Malaria Data (WHO)</h4>
                <div className="features-grid">
                  <div className="feature-item">
                    <TrendingUp size={18} />
                    <span className="feature-label">Last Month:</span>
                    <span className="feature-value">
                      {prediction.prediction.features_used.malaria_lag_1?.toFixed(2)} cases
                    </span>
                  </div>
                  <div className="feature-item">
                    <TrendingUp size={18} />
                    <span className="feature-label">Same Month Last Year:</span>
                    <span className="feature-value">
                      {prediction.prediction.features_used.malaria_lag_12?.toFixed(2)} cases
                    </span>
                  </div>
                  <div className="feature-item">
                    <TrendingUp size={18} />
                    <span className="feature-label">3-Month Average:</span>
                    <span className="feature-value">
                      {prediction.prediction.features_used.malaria_rolling_mean_3?.toFixed(2)} cases
                    </span>
                  </div>
                </div>
              </div>

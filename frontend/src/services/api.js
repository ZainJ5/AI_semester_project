import axios from 'axios';

const API_BASE_URL = 'http://localhost:5000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const apiService = {
  predictCountry: async (country) => {
    try {
      console.log('[API] Sending prediction request for country:', country);
      const response = await api.post('/predict', { country });
      console.log('[API] Prediction response:', response.data);
      return response.data;
    } catch (error) {
      console.error('[API] Prediction error:', error);
      console.error('[API] Error details:', error.response?.data || error.message);
      throw error;
    }
  },

  getSpreadSimulation: async (country) => {
    try {
      console.log('[API] Sending spread simulation request for country:', country);
      const response = await api.post('/simulation/spread', { country });
      console.log('[API] Spread simulation response:', response.data);
      return response.data;
    } catch (error) {
      console.error('[API] Spread simulation error:', error);
      console.error('[API] Error details:', error.response?.data || error.message);
      throw error;
    }
  },

  findSafestPath: async (startCountry, endCountry) => {
    try {
      console.log('[API] Sending path finding request from', startCountry, 'to', endCountry);
      const response = await api.post('/simulation/path', {
        start_country: startCountry,
        end_country: endCountry,
      });
      console.log('[API] Path finding response:', response.data);
      return response.data;
    } catch (error) {
      console.error('[API] Path finding error:', error);
      console.error('[API] Error details:', error.response?.data || error.message);
      throw error;
    }
  },
};

export default apiService;

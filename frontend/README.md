# Disease Prediction System - Frontend

A comprehensive, professional web application for disease prediction, spread simulation, and path analysis using AI/ML models and real-time APIs.

## 🌟 Features

### 1. **Interactive 3D Globe**
- Real-time visualization of countries with disease data
- Click on any country marker to view ML predictions
- Auto-rotating globe with smooth animations
- Country-specific prediction details with risk levels

### 2. **Disease Prediction**
- AI-powered predictions for Malaria and Dengue
- Real-time data from Weather APIs, Population APIs, and WHO
- Interactive charts (Bar charts, Radar charts)
- Detailed environmental factors display
- Risk level indicators (High/Medium/Low)

### 3. **Spread Simulation (BFS)**
- Breadth-First Search algorithm visualization
- Animated disease spread through flight connections
- Interactive force-directed graph
- Real-time statistics and progress tracking

### 4. **Path Analysis (A* Algorithm)**
- Find the safest route between countries
- 3D globe visualization of the path
- Animated arcs showing the route
- Detailed path steps with risk calculations

## 🚀 Getting Started

### Prerequisites
- Node.js (v16 or higher)
- Backend server running on `http://localhost:5000`

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

## 📦 Key Technologies

- **React 18.3.1** - UI framework
- **React Globe.gl** - 3D globe visualization
- **Three.js** - 3D graphics
- **React Force Graph 2D** - Graph visualization
- **Recharts** - Charts and graphs
- **Framer Motion** - Animations
- **Axios** - API communication

## 🏗️ Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── InteractiveGlobe.jsx
│   │   ├── DiseasePrediction.jsx
│   │   ├── SpreadSimulation.jsx
│   │   └── PathAnalysis.jsx
│   ├── services/
│   │   └── api.js
│   ├── App.jsx
│   └── main.jsx
└── package.json
```

## 🔌 API Endpoints

1. **POST /api/predict** - Get disease predictions
2. **POST /api/simulation/spread** - Run BFS simulation
3. **POST /api/simulation/path** - Find safest path

## 🎨 Design Highlights

- Modern dark theme with gradients
- Smooth animations using Framer Motion
- Professional UI/UX
- Fully responsive design
- Interactive visualizations

---

**Made with ❤️ using React and modern web technologies**

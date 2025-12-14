import React, { useState } from 'react';
import { Activity, GitBranch, Route, BarChart3 } from 'lucide-react';
import Prediction from './components/Prediction';
import SpreadSimulation from './components/SpreadSimulation';
import PathAnalysis from './components/PathAnalysis';
import './index.css';

function App() {
  const [activeTab, setActiveTab] = useState('prediction');

  const tabs = [
    { id: 'prediction', label: 'Prediction', icon: Activity },
    { id: 'spread', label: 'Spread Simulation', icon: GitBranch },
    { id: 'path', label: 'Path Analysis', icon: Route },
  ];

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-content">
          <div className="header-title">
            <BarChart3 size={36} className="app-logo" />
            <div>
              <h1>Disease Spread Analytics</h1>
              <p>ML-powered prediction and graph-based simulation platform</p>
            </div>
          </div>
        </div>
      </header>

      <nav className="app-nav">
        <div className="nav-container">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                className={`nav-tab ${activeTab === tab.id ? 'active' : ''}`}
                onClick={() => setActiveTab(tab.id)}
              >
                <Icon size={20} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>
      </nav>

      <main className="app-main">
        <div className="main-content">
          {activeTab === 'prediction' && <Prediction />}
          {activeTab === 'spread' && <SpreadSimulation />}
          {activeTab === 'path' && <PathAnalysis />}
        </div>
      </main>

      <footer className="app-footer">
        <p>© 2025 Disease Spread Analytics | Powered by Machine Learning & Graph Algorithms</p>
      </footer>
    </div>
  );
}

export default App;

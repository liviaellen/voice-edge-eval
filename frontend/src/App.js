import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import Analytics from './pages/Analytics';
import Configuration from './pages/Configuration';
import './App.css';

function App() {
  return (
    <Router>
      <div className="app">
        <nav className="navbar">
          <div className="navbar-brand">
            <h1>⚡ Emotion AI Platform</h1>
            <span className="version">v2.0</span>
          </div>
          <div className="navbar-links">
            <Link to="/" className="nav-link">Dashboard</Link>
            <Link to="/analytics" className="nav-link">Analytics</Link>
            <Link to="/config" className="nav-link">Configuration</Link>
          </div>
        </nav>

        <main className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/config" element={<Configuration />} />
          </Routes>
        </main>

        <footer className="footer">
          <p>Emotion AI Platform © 2024 | Powered by Hume AI</p>
        </footer>
      </div>
    </Router>
  );
}

export default App;

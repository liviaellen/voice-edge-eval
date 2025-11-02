import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import Analytics from './pages/Analytics';
import Configuration from './pages/Configuration';
import LiveAnalysis from './pages/LiveAnalysis';
import './App.css';

function NavBar() {
  const location = useLocation();

  const isActive = (path) => {
    return location.pathname === path ? 'nav-link active' : 'nav-link';
  };

  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <h1>⚡ Emotion AI Platform</h1>
        <span className="version">v2.0</span>
      </div>
      <div className="navbar-links">
        <Link to="/" className={isActive('/')}>Dashboard</Link>
        <Link to="/live" className={isActive('/live')}>Live Analysis</Link>
        <Link to="/analytics" className={isActive('/analytics')}>Analytics</Link>
        <Link to="/config" className={isActive('/config')}>Configuration</Link>
      </div>
    </nav>
  );
}

function App() {
  return (
    <Router>
      <div className="app">
        <NavBar />

        <main className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/live" element={<LiveAnalysis />} />
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

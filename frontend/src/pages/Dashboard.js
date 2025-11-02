import React, { useState, useEffect } from 'react';
import axios from 'axios';

function Dashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchDashboardStats();
    // Auto-refresh every 10 seconds
    const interval = setInterval(fetchDashboardStats, 10000);
    return () => clearInterval(interval);
  }, []);

  const fetchDashboardStats = async () => {
    try {
      const response = await axios.get('/dashboard/stats');
      setStats(response.data);
      setLoading(false);
      setError(null);
    } catch (err) {
      console.error('Error fetching dashboard stats:', err);
      setError('Failed to load dashboard data');
      setLoading(false);
    }
  };

  const handleResetStats = async () => {
    if (window.confirm('Are you sure you want to reset all statistics? This cannot be undone.')) {
      try {
        await axios.post('/dashboard/stats/reset');
        fetchDashboardStats();
        alert('Statistics reset successfully!');
      } catch (err) {
        alert('Error resetting statistics: ' + err.message);
      }
    }
  };

  if (loading) {
    return <div className="loading">Loading dashboard...</div>;
  }

  if (error) {
    return <div className="error">{error}</div>;
  }

  const { stats: analyticsStats, configuration } = stats;
  const rizzScore = analyticsStats?.rizz_score || 75;
  const rizzClass = rizzScore > 80 ? 'high' : rizzScore >= 40 ? 'medium' : 'low';

  return (
    <div className="dashboard">
      <h1>Dashboard Overview</h1>

      {/* Configuration Status */}
      <div className="card">
        <h2>⚙️ System Configuration</h2>
        <div style={{ display: 'flex', gap: '2rem', marginTop: '1rem' }}>
          <div>
            <span style={{ color: configuration?.hume_ai ? '#48bb78' : '#f56565' }}>
              {configuration?.hume_ai ? '✓' : '✗'}
            </span>
            {' '}Hume AI: {configuration?.hume_ai ? 'Configured' : 'Not configured'}
          </div>
          <div>
            <span style={{ color: configuration?.google_cloud_storage ? '#48bb78' : '#f56565' }}>
              {configuration?.google_cloud_storage ? '✓' : '✗'}
            </span>
            {' '}Google Cloud Storage: {configuration?.google_cloud_storage ? 'Configured' : 'Not configured'}
          </div>
          <div>
            <span style={{ color: configuration?.omi_integration ? '#48bb78' : '#f56565' }}>
              {configuration?.omi_integration ? '✓' : '✗'}
            </span>
            {' '}Omi Integration: {configuration?.omi_integration ? 'Configured' : 'Not configured'}
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-value">{analyticsStats?.total_requests || 0}</div>
          <div className="stat-label">Total Requests</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{analyticsStats?.successful_analyses || 0}</div>
          <div className="stat-label">Successful Analyses</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{analyticsStats?.failed_analyses || 0}</div>
          <div className="stat-label">Failed Analyses</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">
            {analyticsStats?.successful_analyses > 0
              ? ((analyticsStats.successful_analyses / analyticsStats.total_requests) * 100).toFixed(1)
              : 0}%
          </div>
          <div className="stat-label">Success Rate</div>
        </div>
      </div>

      {/* Rizz Meter */}
      <div className="rizz-meter">
        <h3>⚡ Emotional Health Score</h3>
        <div className="rizz-bar">
          <div
            className={`rizz-fill ${rizzClass}`}
            style={{ width: `${rizzScore}%` }}
          />
        </div>
        <div className="rizz-score">
          {rizzScore.toFixed(1)}%
          {' '}
          {rizzScore > 80 ? '😎 Positive Vibes!' : rizzScore >= 40 ? '😐 Neutral Energy' : '😔 Negative Energy'}
        </div>
      </div>

      {/* Recent Activity */}
      {analyticsStats?.last_request_time && (
        <div className="card">
          <h2>📊 Last Activity</h2>
          <p><strong>Time:</strong> {analyticsStats.last_request_time}</p>
          <p><strong>User ID:</strong> {analyticsStats.last_uid?.substring(0, 8)}****</p>
          {analyticsStats.recent_emotions?.length > 0 && (
            <div className="emotion-tags">
              {analyticsStats.recent_emotions.slice(0, 5).map((emotion, idx) => (
                <span key={idx} className="emotion-tag">{emotion}</span>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Recent Notifications */}
      {analyticsStats?.recent_notifications?.length > 0 && (
        <div className="card">
          <h2>📱 Recent Notifications</h2>
          {analyticsStats.recent_notifications.slice(0, 5).map((notif, idx) => (
            <div key={idx} style={{
              background: '#f7fafc',
              padding: '1rem',
              marginBottom: '0.5rem',
              borderRadius: '5px',
              borderLeft: '3px solid #667eea'
            }}>
              <p style={{ margin: '0 0 0.5rem 0', fontWeight: 'bold' }}>{notif.message}</p>
              <p style={{ margin: 0, fontSize: '0.85rem', color: '#718096' }}>
                <span style={{ marginRight: '1rem' }}>🕒 {notif.timestamp}</span>
                <span>👤 {notif.uid?.substring(0, 8)}****</span>
              </p>
            </div>
          ))}
        </div>
      )}

      {/* Actions */}
      <div className="card">
        <h2>🔧 Actions</h2>
        <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
          <button className="btn btn-primary" onClick={fetchDashboardStats}>
            🔄 Refresh Dashboard
          </button>
          <button className="btn btn-danger" onClick={handleResetStats}>
            🗑️ Reset Statistics
          </button>
        </div>
        <p style={{ marginTop: '1rem', color: '#718096', fontSize: '0.9rem' }}>
          Dashboard auto-refreshes every 10 seconds
        </p>
      </div>
    </div>
  );
}

export default Dashboard;

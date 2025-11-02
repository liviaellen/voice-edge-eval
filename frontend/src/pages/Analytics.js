import React, { useState, useEffect } from 'react';
import axios from 'axios';

function Analytics() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const fetchAnalytics = async () => {
    try {
      const response = await axios.get('/dashboard/stats');
      setStats(response.data);
      setLoading(false);
    } catch (err) {
      console.error('Error fetching analytics:', err);
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="loading">Loading analytics...</div>;
  }

  const emotionCounts = stats?.stats?.emotion_counts || {};
  const totalEmotions = Object.values(emotionCounts).reduce((a, b) => a + b, 0);
  const sortedEmotions = Object.entries(emotionCounts)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 12);

  return (
    <div className="analytics">
      <h1>Emotion Analytics</h1>

      <div className="card">
        <h2>🎭 Emotion Distribution</h2>
        <p style={{ color: '#718096', marginBottom: '1.5rem' }}>
          Cumulative counts and percentages of all detected emotions
        </p>

        {sortedEmotions.length > 0 ? (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))', gap: '1rem' }}>
            {sortedEmotions.map(([emotion, count]) => {
              const percentage = ((count / totalEmotions) * 100).toFixed(1);
              const barWidth = ((count / sortedEmotions[0][1]) * 100).toFixed(1);

              return (
                <div key={emotion} style={{
                  background: '#f7fafc',
                  padding: '1rem',
                  borderRadius: '5px',
                  borderLeft: '3px solid #667eea'
                }}>
                  <div style={{ fontWeight: 'bold', color: '#2d3748', marginBottom: '0.5rem' }}>
                    {emotion}
                  </div>
                  <div style={{ color: '#718096', fontSize: '0.85rem', marginBottom: '0.5rem' }}>
                    Count: {count} | {percentage}%
                  </div>
                  <div style={{
                    background: '#e2e8f0',
                    height: '8px',
                    borderRadius: '4px',
                    overflow: 'hidden'
                  }}>
                    <div style={{
                      background: 'linear-gradient(90deg, #667eea, #764ba2)',
                      height: '100%',
                      width: `${barWidth}%`,
                      transition: 'width 0.3s ease'
                    }} />
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <p style={{ color: '#718096', textAlign: 'center', padding: '2rem' }}>
            No emotion data available yet
          </p>
        )}
      </div>

      {stats?.emotion_summary?.success && (
        <div className="card">
          <h2>📊 Emotion Summary</h2>
          <p style={{ fontSize: '1.1rem', color: '#2d3748' }}>
            {stats.emotion_summary.summary}
          </p>
          <p style={{ marginTop: '1rem', color: '#718096' }}>
            Total Detections: {stats.emotion_summary.total_detections}
          </p>
        </div>
      )}

      <div className="card">
        <h2>📈 API Endpoints</h2>
        <div style={{ display: 'grid', gap: '1rem', marginTop: '1rem' }}>
          <div>
            <h3 style={{ fontSize: '1.1rem', marginBottom: '0.5rem' }}>Audio Edge (Omi)</h3>
            <code style={{
              background: '#2d3748',
              color: '#48bb78',
              padding: '0.5rem 1rem',
              borderRadius: '5px',
              display: 'block',
              fontSize: '0.9rem'
            }}>
              POST /audio-edge?sample_rate=16000&uid=user123
            </code>
            <p style={{ marginTop: '0.5rem', color: '#718096', fontSize: '0.9rem' }}>
              Original endpoint for Omi devices with emotion notifications
            </p>
          </div>

          <div>
            <h3 style={{ fontSize: '1.1rem', marginBottom: '0.5rem' }}>Audio Analytics (Stream)</h3>
            <code style={{
              background: '#2d3748',
              color: '#48bb78',
              padding: '0.5rem 1rem',
              borderRadius: '5px',
              display: 'block',
              fontSize: '0.9rem'
            }}>
              POST /audio-analytics/analyze?sample_rate=16000&user_id=session_123
            </code>
            <p style={{ marginTop: '0.5rem', color: '#718096', fontSize: '0.9rem' }}>
              Stream endpoint for analytics without notifications
            </p>
          </div>

          <div>
            <h3 style={{ fontSize: '1.1rem', marginBottom: '0.5rem' }}>Text Analytics</h3>
            <code style={{
              background: '#2d3748',
              color: '#48bb78',
              padding: '0.5rem 1rem',
              borderRadius: '5px',
              display: 'block',
              fontSize: '0.9rem'
            }}>
              POST /audio-analytics/analyze-text?user_id=session_123
            </code>
            <p style={{ marginTop: '0.5rem', color: '#718096', fontSize: '0.9rem' }}>
              Text emotion analysis (max 10,000 characters)
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Analytics;

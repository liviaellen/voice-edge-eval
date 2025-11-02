import React, { useState, useEffect } from 'react';
import axios from 'axios';

const AVAILABLE_EMOTIONS = [
  // Positive
  { name: 'Joy', emoji: '😊', category: 'positive' },
  { name: 'Amusement', emoji: '😄', category: 'positive' },
  { name: 'Satisfaction', emoji: '😌', category: 'positive' },
  { name: 'Excitement', emoji: '🤩', category: 'positive' },
  { name: 'Desire', emoji: '😍', category: 'positive' },
  // Negative
  { name: 'Anger', emoji: '😠', category: 'negative' },
  { name: 'Sadness', emoji: '😢', category: 'negative' },
  { name: 'Anxiety', emoji: '😰', category: 'negative' },
  { name: 'Fear', emoji: '😨', category: 'negative' },
  { name: 'Distress', emoji: '😖', category: 'negative' },
  // Neutral
  { name: 'Calmness', emoji: '😌', category: 'neutral' },
  { name: 'Interest', emoji: '🤔', category: 'neutral' },
  { name: 'Surprise', emoji: '😲', category: 'neutral' },
  { name: 'Contemplation', emoji: '🤨', category: 'neutral' },
  { name: 'Determination', emoji: '😤', category: 'neutral' }
];

function Configuration() {
  const [config, setConfig] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedEmotions, setSelectedEmotions] = useState({});
  const [saveStatus, setSaveStatus] = useState('');

  useEffect(() => {
    fetchConfig();
  }, []);

  const fetchConfig = async () => {
    try {
      const response = await axios.get('/dashboard/emotion-config');
      setConfig(response.data.current_config);
      setSelectedEmotions(response.data.current_config.emotion_thresholds || {});
      setLoading(false);
    } catch (err) {
      console.error('Error fetching config:', err);
      setLoading(false);
    }
  };

  const handleEmotionToggle = (emotionName) => {
    setSelectedEmotions(prev => {
      const newSelected = { ...prev };
      if (newSelected[emotionName] !== undefined) {
        delete newSelected[emotionName];
      } else {
        newSelected[emotionName] = 0;
      }
      return newSelected;
    });
  };

  const selectAll = () => {
    const allEmotions = {};
    AVAILABLE_EMOTIONS.forEach(e => {
      allEmotions[e.name] = 0;
    });
    setSelectedEmotions(allEmotions);
  };

  const clearAll = () => {
    setSelectedEmotions({});
  };

  const saveConfig = async () => {
    setSaveStatus('Saving...');
    try {
      await axios.post('/dashboard/emotion-config', {
        notification_enabled: true,
        emotion_thresholds: selectedEmotions
      });
      setSaveStatus('✅ Configuration saved successfully!');
      setTimeout(() => setSaveStatus(''), 3000);
    } catch (err) {
      setSaveStatus('❌ Error saving configuration');
      console.error('Error saving config:', err);
    }
  };

  if (loading) {
    return <div className="loading">Loading configuration...</div>;
  }

  return (
    <div className="configuration">
      <h1>Configuration</h1>

      <div className="card">
        <h2>⚙️ Emotion Tracking Configuration</h2>
        <p style={{ color: '#718096', marginBottom: '1rem' }}>
          Select which emotions trigger notifications for the Audio Edge endpoint.
          Leave all unchecked for ALL emotions.
        </p>

        <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem' }}>
          <button className="btn btn-primary" onClick={selectAll}>
            ✓ Select All
          </button>
          <button className="btn" onClick={clearAll} style={{ background: '#718096', color: 'white' }}>
            ✗ Clear All
          </button>
        </div>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))',
          gap: '0.75rem',
          marginBottom: '1.5rem'
        }}>
          {AVAILABLE_EMOTIONS.map(emotion => (
            <label
              key={emotion.name}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                padding: '0.75rem',
                background: selectedEmotions[emotion.name] !== undefined ? '#e6f0ff' : '#f7fafc',
                border: selectedEmotions[emotion.name] !== undefined ? '2px solid #667eea' : '2px solid transparent',
                borderRadius: '5px',
                cursor: 'pointer',
                transition: 'all 0.2s'
              }}
            >
              <input
                type="checkbox"
                checked={selectedEmotions[emotion.name] !== undefined}
                onChange={() => handleEmotionToggle(emotion.name)}
                style={{ cursor: 'pointer' }}
              />
              <span>{emotion.emoji} {emotion.name}</span>
            </label>
          ))}
        </div>

        <button className="btn btn-primary" onClick={saveConfig} style={{ fontSize: '1.1rem' }}>
          💾 Save Configuration
        </button>

        {saveStatus && (
          <p style={{
            marginTop: '1rem',
            color: saveStatus.includes('✅') ? '#48bb78' : '#f56565',
            fontWeight: 'bold'
          }}>
            {saveStatus}
          </p>
        )}
      </div>

      <div className="card">
        <h2>🔌 Current Configuration</h2>
        <div style={{ background: '#2d3748', color: '#48bb78', padding: '1rem', borderRadius: '5px', fontFamily: 'monospace' }}>
          <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
            {JSON.stringify(config, null, 2)}
          </pre>
        </div>
      </div>

      <div className="card">
        <h2>ℹ️ Configuration Guide</h2>
        <ul style={{ color: '#2d3748', lineHeight: '1.8' }}>
          <li>
            <strong>Empty emotion thresholds:</strong> The system will notify for ALL detected emotions
          </li>
          <li>
            <strong>Selected emotions:</strong> Only the selected emotions will trigger notifications
          </li>
          <li>
            <strong>Audio Edge endpoint:</strong> Uses this configuration for Omi notifications
          </li>
          <li>
            <strong>Audio Analytics endpoint:</strong> Does NOT send notifications (stream analytics only)
          </li>
        </ul>
      </div>
    </div>
  );
}

export default Configuration;

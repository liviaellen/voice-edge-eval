import React, { useState } from 'react';
import axios from 'axios';
import './TimeSeries.css';

function TimeSeries() {
  const [file, setFile] = useState(null);
  const [chunkDuration, setChunkDuration] = useState(5);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);

  const handleFileChange = (event) => {
    const selectedFile = event.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      setError(null);
      setResult(null);
    }
  };

  const handleAnalyze = async () => {
    if (!file) {
      setError('Please select an audio file first');
      return;
    }

    setLoading(true);
    setError(null);
    setUploadProgress(0);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await axios.post(
        `/timeseries/analyze?user_id=timeseries_user&chunk_duration=${chunkDuration}`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          onUploadProgress: (progressEvent) => {
            const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            setUploadProgress(percentCompleted);
          }
        }
      );

      setResult(response.data);
      setUploadProgress(0);
    } catch (err) {
      setError('Analysis failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  const getSentimentColor = (sentiment) => {
    if (sentiment === 1) return '#48bb78'; // Positive - Green
    if (sentiment === -1) return '#f56565'; // Negative - Red
    return '#4299e1'; // Neutral - Blue
  };

  const getSentimentLabel = (sentiment) => {
    if (sentiment === 1) return 'Positive';
    if (sentiment === -1) return 'Negative';
    return 'Neutral';
  };

  const getSentimentEmoji = (sentiment) => {
    if (sentiment === 1) return '😊';
    if (sentiment === -1) return '😔';
    return '😐';
  };

  return (
    <div className="timeseries">
      <h1>📊 Time-Series Emotion Analysis</h1>
      <p className="subtitle">Analyze emotions over time with chunk-based processing</p>

      {/* Upload Section */}
      <div className="card upload-section">
        <h2>Upload Audio File</h2>

        <div className="file-upload-container">
          <input
            type="file"
            id="timeseries-upload"
            accept="audio/*"
            onChange={handleFileChange}
            disabled={loading}
            style={{ display: 'none' }}
          />
          <label htmlFor="timeseries-upload" className="file-upload-label">
            {file ? (
              <div className="file-selected">
                <span className="file-icon">🎵</span>
                <div className="file-details">
                  <div className="file-name">{file.name}</div>
                  <div className="file-size">{(file.size / 1024).toFixed(2)} KB</div>
                </div>
              </div>
            ) : (
              <div className="file-placeholder">
                <span className="upload-icon">📁</span>
                <p>Click to select audio file</p>
                <span className="file-hint">WAV, MP3, M4A supported</span>
              </div>
            )}
          </label>
        </div>

        <div className="chunk-selector">
          <label>
            <strong>Chunk Duration:</strong>
            <select
              value={chunkDuration}
              onChange={(e) => setChunkDuration(Number(e.target.value))}
              disabled={loading}
              className="chunk-dropdown"
            >
              <option value={5}>5 seconds</option>
              <option value={10}>10 seconds</option>
            </select>
          </label>
          <p className="chunk-hint">
            Audio will be split into {chunkDuration}-second chunks for analysis
          </p>
        </div>

        <button
          className="btn btn-primary btn-large"
          onClick={handleAnalyze}
          disabled={!file || loading}
        >
          {loading ? '⏳ Analyzing...' : '🔍 Analyze Timeline'}
        </button>

        {loading && uploadProgress > 0 && (
          <div className="progress-container">
            <div className="progress-bar">
              <div className="progress-fill" style={{ width: `${uploadProgress}%` }} />
            </div>
            <p className="progress-text">{uploadProgress}%</p>
          </div>
        )}
      </div>

      {/* Error Display */}
      {error && (
        <div className="error-card">
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* Results */}
      {result && (
        <>
          {/* Aggregation Summary */}
          <div className="card aggregation-card">
            <h2>📈 Overall Summary</h2>

            <div className="summary-grid">
              <div className="summary-item">
                <div className="summary-label">Total Duration</div>
                <div className="summary-value">{result.file_info.total_duration.toFixed(1)}s</div>
              </div>
              <div className="summary-item">
                <div className="summary-label">Total Chunks</div>
                <div className="summary-value">{result.file_info.total_chunks}</div>
              </div>
              <div className="summary-item">
                <div className="summary-label">Chunk Size</div>
                <div className="summary-value">{result.file_info.chunk_duration}s</div>
              </div>
            </div>

            <div className="sentiment-summary">
              <h3>Sentiment Distribution</h3>
              <div className="sentiment-bars">
                <div className="sentiment-bar-item">
                  <div className="sentiment-bar-header">
                    <span>😊 Positive</span>
                    <span>{result.aggregation.overall_sentiment.positive_percentage.toFixed(1)}%</span>
                  </div>
                  <div className="sentiment-bar">
                    <div
                      className="sentiment-bar-fill positive"
                      style={{ width: `${result.aggregation.overall_sentiment.positive_percentage}%` }}
                    />
                  </div>
                </div>

                <div className="sentiment-bar-item">
                  <div className="sentiment-bar-header">
                    <span>😐 Neutral</span>
                    <span>{result.aggregation.overall_sentiment.neutral_percentage.toFixed(1)}%</span>
                  </div>
                  <div className="sentiment-bar">
                    <div
                      className="sentiment-bar-fill neutral"
                      style={{ width: `${result.aggregation.overall_sentiment.neutral_percentage}%` }}
                    />
                  </div>
                </div>

                <div className="sentiment-bar-item">
                  <div className="sentiment-bar-header">
                    <span>😔 Negative</span>
                    <span>{result.aggregation.overall_sentiment.negative_percentage.toFixed(1)}%</span>
                  </div>
                  <div className="sentiment-bar">
                    <div
                      className="sentiment-bar-fill negative"
                      style={{ width: `${result.aggregation.overall_sentiment.negative_percentage}%` }}
                    />
                  </div>
                </div>
              </div>

              <div className="dominant-sentiment">
                <h4>Dominant Sentiment</h4>
                <div className={`sentiment-badge ${result.aggregation.overall_sentiment.dominant}`}>
                  {getSentimentEmoji(
                    result.aggregation.overall_sentiment.dominant === 'positive' ? 1 :
                    result.aggregation.overall_sentiment.dominant === 'negative' ? -1 : 0
                  )}
                  {' '}
                  {result.aggregation.overall_sentiment.dominant.toUpperCase()}
                </div>
              </div>
            </div>
          </div>

          {/* Timeline Visualization */}
          <div className="card timeline-card">
            <h2>⏱️ Emotion Timeline</h2>

            <div className="timeline-graph">
              {result.timeline.map((chunk, idx) => (
                <div key={idx} className="timeline-chunk">
                  <div className="chunk-header">
                    <span className="chunk-time">{chunk.timestamp.toFixed(1)}s - {chunk.end_timestamp.toFixed(1)}s</span>
                    <span className={`chunk-sentiment ${getSentimentLabel(chunk.dominant_sentiment).toLowerCase()}`}>
                      {getSentimentEmoji(chunk.dominant_sentiment)} {getSentimentLabel(chunk.dominant_sentiment)}
                    </span>
                  </div>

                  <div
                    className="chunk-bar"
                    style={{
                      background: getSentimentColor(chunk.dominant_sentiment),
                      height: `${Math.abs(chunk.sentiment_score || 0) * 100 + 20}px`,
                      opacity: 0.8
                    }}
                  />

                  {chunk.emotions && chunk.emotions.length > 0 && (
                    <div className="chunk-emotions">
                      {chunk.emotions.map((emotion, eidx) => (
                        <div key={eidx} className="chunk-emotion">
                          <span className="emotion-name">{emotion.name}</span>
                          <span className="emotion-score">{(emotion.score * 100).toFixed(0)}%</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Sentiment Graph */}
          <div className="card graph-card">
            <h2>📉 Sentiment Graph</h2>
            <div className="sentiment-graph">
              <div className="graph-y-axis">
                <span className="y-label">+1</span>
                <span className="y-label">0</span>
                <span className="y-label">-1</span>
              </div>
              <div className="graph-canvas">
                <div className="graph-line positive"></div>
                <div className="graph-line neutral"></div>
                <div className="graph-line negative"></div>

                <svg className="graph-svg" viewBox="0 0 1000 300" preserveAspectRatio="none">
                  <polyline
                    points={result.timeline.map((chunk, idx) => {
                      const x = (idx / (result.timeline.length - 1)) * 1000;
                      const y = 150 - (chunk.dominant_sentiment * 120);
                      return `${x},${y}`;
                    }).join(' ')}
                    fill="none"
                    stroke="#667eea"
                    strokeWidth="3"
                  />
                  {result.timeline.map((chunk, idx) => {
                    const x = (idx / (result.timeline.length - 1)) * 1000;
                    const y = 150 - (chunk.dominant_sentiment * 120);
                    return (
                      <circle
                        key={idx}
                        cx={x}
                        cy={y}
                        r="6"
                        fill={getSentimentColor(chunk.dominant_sentiment)}
                        stroke="white"
                        strokeWidth="2"
                      />
                    );
                  })}
                </svg>
              </div>
            </div>
            <div className="graph-x-axis">
              <span>0s</span>
              <span>{(result.file_info.total_duration / 2).toFixed(0)}s</span>
              <span>{result.file_info.total_duration.toFixed(0)}s</span>
            </div>
          </div>

          {/* Top Emotions */}
          <div className="card emotions-summary-card">
            <h2>🎭 Top Emotions Detected</h2>
            <div className="emotions-summary-list">
              {result.aggregation.emotion_summary.top_emotions.map((emotion, idx) => (
                <div key={idx} className="emotion-summary-item">
                  <div className="emotion-rank">#{idx + 1}</div>
                  <div className="emotion-details">
                    <div className="emotion-header">
                      <span className="emotion-name-big">{emotion.name}</span>
                      <span className={`emotion-sentiment ${getSentimentLabel(emotion.sentiment).toLowerCase()}`}>
                        {getSentimentEmoji(emotion.sentiment)}
                      </span>
                    </div>
                    <div className="emotion-stats">
                      <span>Avg: {(emotion.average_score * 100).toFixed(1)}%</span>
                      <span>•</span>
                      <span>Appeared {emotion.count}x</span>
                    </div>
                    <div className="emotion-bar-summary">
                      <div
                        className="emotion-bar-fill-summary"
                        style={{
                          width: `${emotion.average_score * 100}%`,
                          background: getSentimentColor(emotion.sentiment)
                        }}
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

export default TimeSeries;

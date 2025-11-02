import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import './LiveAnalysis.css';

function LiveAnalysis() {
  const [isRecording, setIsRecording] = useState(false);
  const [audioUrl, setAudioUrl] = useState(null);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);

  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const streamRef = useRef(null);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
    };
  }, []);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data);
      };

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        const url = URL.createObjectURL(audioBlob);
        setAudioUrl(url);
      };

      mediaRecorder.start();
      setIsRecording(true);
      setError(null);
      setAnalysisResult(null);
    } catch (err) {
      setError('Failed to access microphone: ' + err.message);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);

      // Stop all tracks
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
    }
  };

  const analyzeRecording = async () => {
    if (!audioChunksRef.current.length) return;

    setLoading(true);
    setError(null);

    try {
      const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
      const formData = new FormData();
      formData.append('file', audioBlob, 'recording.wav');

      const response = await axios.post(
        '/audio-analytics/upload?user_id=live_recording',
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

      setAnalysisResult(response.data);
      setUploadProgress(0);
    } catch (err) {
      setError('Analysis failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setLoading(true);
    setError(null);
    setAnalysisResult(null);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await axios.post(
        '/audio-analytics/upload?user_id=file_upload',
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

      setAnalysisResult(response.data);
      setUploadProgress(0);

      // Create audio URL for playback
      const url = URL.createObjectURL(file);
      setAudioUrl(url);
    } catch (err) {
      setError('Upload failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  const getRizzColor = (score) => {
    if (score > 80) return '#48bb78';
    if (score >= 40) return '#4299e1';
    return '#f56565';
  };

  return (
    <div className="live-analysis">
      <h1>🎤 Live Audio Analysis</h1>

      <div className="analysis-grid">
        {/* Recording Section */}
        <div className="card record-card">
          <h2>Record Audio</h2>
          <div className="record-controls">
            {!isRecording ? (
              <button
                className="btn btn-record"
                onClick={startRecording}
                disabled={loading}
              >
                <span className="record-icon">🔴</span>
                Start Recording
              </button>
            ) : (
              <button
                className="btn btn-stop"
                onClick={stopRecording}
              >
                <span className="record-icon">⏹️</span>
                Stop Recording
              </button>
            )}
          </div>

          {isRecording && (
            <div className="recording-indicator">
              <div className="pulse-dot"></div>
              <span>Recording...</span>
            </div>
          )}

          {audioUrl && !isRecording && (
            <div className="audio-player">
              <h3>Recording Preview</h3>
              <audio src={audioUrl} controls style={{ width: '100%' }} />
              <button
                className="btn btn-primary"
                onClick={analyzeRecording}
                disabled={loading}
                style={{ marginTop: '1rem', width: '100%' }}
              >
                {loading ? 'Analyzing...' : '🔍 Analyze Recording'}
              </button>
            </div>
          )}
        </div>

        {/* File Upload Section */}
        <div className="card upload-card">
          <h2>Upload Audio File</h2>
          <div className="upload-zone">
            <input
              type="file"
              id="audio-upload"
              accept="audio/*"
              onChange={handleFileUpload}
              disabled={loading}
              style={{ display: 'none' }}
            />
            <label htmlFor="audio-upload" className="upload-label">
              <div className="upload-icon">📁</div>
              <p>Click to upload audio file</p>
              <span className="upload-hint">WAV, MP3, M4A supported</span>
            </label>
          </div>
        </div>
      </div>

      {/* Upload Progress */}
      {loading && uploadProgress > 0 && (
        <div className="card progress-card">
          <h3>Upload Progress</h3>
          <div className="progress-bar">
            <div
              className="progress-fill"
              style={{ width: `${uploadProgress}%` }}
            />
          </div>
          <p className="progress-text">{uploadProgress}%</p>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="error-card">
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* Analysis Results */}
      {analysisResult && (
        <div className="results-section">
          <div className="card results-card">
            <h2>📊 Analysis Results</h2>

            {/* Rizz Score */}
            <div className="rizz-display">
              <h3>Emotional Health Score</h3>
              <div className="rizz-circle" style={{
                background: `conic-gradient(${getRizzColor(analysisResult.analytics.rizz_score)} ${analysisResult.analytics.rizz_score * 3.6}deg, #e2e8f0 0deg)`
              }}>
                <div className="rizz-inner">
                  <div className="rizz-value">{analysisResult.analytics.rizz_score.toFixed(1)}%</div>
                  <div className="rizz-status">{analysisResult.analytics.rizz_status}</div>
                </div>
              </div>
            </div>

            {/* Top Emotions */}
            {analysisResult.emotion_analysis.predictions && analysisResult.emotion_analysis.predictions.length > 0 && (
              <div className="emotions-display">
                <h3>Detected Emotions</h3>
                <div className="emotions-grid">
                  {analysisResult.emotion_analysis.predictions[0].top_3_emotions?.map((emotion, idx) => (
                    <div key={idx} className="emotion-item">
                      <div className="emotion-name">{emotion.name}</div>
                      <div className="emotion-score-bar">
                        <div
                          className="emotion-score-fill"
                          style={{
                            width: `${emotion.score * 100}%`,
                            background: `hsl(${(1 - emotion.score) * 120}, 70%, 50%)`
                          }}
                        />
                      </div>
                      <div className="emotion-score">{(emotion.score * 100).toFixed(1)}%</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* File Info */}
            {analysisResult.file_info && (
              <div className="file-info">
                <h3>File Information</h3>
                <div className="info-grid">
                  <div className="info-item">
                    <span className="info-label">Filename:</span>
                    <span className="info-value">{analysisResult.file_info.original_filename}</span>
                  </div>
                  <div className="info-item">
                    <span className="info-label">Size:</span>
                    <span className="info-value">{(analysisResult.file_info.file_size_bytes / 1024).toFixed(2)} KB</span>
                  </div>
                  <div className="info-item">
                    <span className="info-label">Type:</span>
                    <span className="info-value">{analysisResult.file_info.file_type.toUpperCase()}</span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* All Emotions Detail */}
          {analysisResult.emotion_analysis.predictions && analysisResult.emotion_analysis.predictions.length > 0 && (
            <div className="card emotions-detail-card">
              <h2>All Detected Emotions</h2>
              <div className="emotions-list">
                {analysisResult.emotion_analysis.predictions[0].emotions?.slice(0, 15).map((emotion, idx) => (
                  <div key={idx} className="emotion-row">
                    <span className="emotion-rank">#{idx + 1}</span>
                    <span className="emotion-name-detail">{emotion.name}</span>
                    <div className="emotion-bar-detail">
                      <div
                        className="emotion-bar-fill-detail"
                        style={{ width: `${emotion.score * 100}%` }}
                      />
                    </div>
                    <span className="emotion-percentage">{(emotion.score * 100).toFixed(1)}%</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default LiveAnalysis;

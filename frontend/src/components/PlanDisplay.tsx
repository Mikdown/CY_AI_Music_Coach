import React, { useState, useEffect } from 'react';
import { coachAPI, AssessmentData } from '../services/api';
import '../styles/PlanDisplay.css';

interface PlanDisplayProps {
  sessionId: string;
  plan: string;
  assessment: AssessmentData;
  onRefine: () => void;
}

export const PlanDisplay: React.FC<PlanDisplayProps> = ({ sessionId, plan, assessment, onRefine }) => {
  const [isCopied, setIsCopied] = useState(false);
  const [youtubeVideos, setYoutubeVideos] = useState<string>('');
  const [loadingVideos, setLoadingVideos] = useState(true);
  const [videoError, setVideoError] = useState<string | null>(null);

  useEffect(() => {
    // Fetch YouTube recommendations when component mounts
    const fetchVideos = async () => {
      try {
        setLoadingVideos(true);
        setVideoError(null);
        const response = await coachAPI.getYouTubeRecommendations(assessment);
        if (response.success && response.videos) {
          setYoutubeVideos(response.videos);
        } else {
          setVideoError('Could not load video recommendations');
        }
      } catch (error) {
        console.error('Error fetching YouTube videos:', error);
        setVideoError('Failed to load video recommendations. Please try again.');
      } finally {
        setLoadingVideos(false);
      }
    };

    fetchVideos();
  }, [assessment]);

  const handleCopyPlan = () => {
    navigator.clipboard.writeText(plan);
    setIsCopied(true);
    setTimeout(() => setIsCopied(false), 2000);
  };

  return (
    <div className="plan-display">
      <div className="plan-container">
        <div className="plan-header">
          <h2>🎸 Your 30-Minute Practice Plan</h2>
          <p className="plan-subtitle">Personalized just for you</p>
        </div>

        <div className="plan-content">
          <div className="plan-text">
            {plan.split('\n').map((line, idx) => (
              <p key={idx}>{line || <br />}</p>
            ))}
          </div>
        </div>

        {/* YouTube Recommendations Section */}
        <div className="youtube-section">
          <h3>📹 Learning Resources</h3>
          {loadingVideos ? (
            <p className="loading">Loading video recommendations...</p>
          ) : videoError ? (
            <p className="error">{videoError}</p>
          ) : youtubeVideos ? (
            <div className="youtube-content">
              {youtubeVideos.split('\n').map((line, idx) => (
                <p key={idx}>{line || <br />}</p>
              ))}
            </div>
          ) : (
            <p className="no-videos">No video recommendations available</p>
          )}
        </div>

        <div className="plan-actions">
          <button className="action-button copy" onClick={handleCopyPlan}>
            {isCopied ? '✅ Copied!' : '📋 Copy Plan'}
          </button>
          <button className="action-button refine" onClick={onRefine}>
            ✏️ Refine Plan
          </button>
        </div>

        <div className="plan-info">
          <p>Session ID: <code>{sessionId}</code></p>
        </div>
      </div>
    </div>
  );
};

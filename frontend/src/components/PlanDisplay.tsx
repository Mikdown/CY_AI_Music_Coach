import React, { useState } from 'react';
import '../styles/PlanDisplay.css';

interface PlanDisplayProps {
  sessionId: string;
  plan: string;
  onRefine: () => void;
}

export const PlanDisplay: React.FC<PlanDisplayProps> = ({ sessionId, plan, onRefine }) => {
  const [isCopied, setIsCopied] = useState(false);

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

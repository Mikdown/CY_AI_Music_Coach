import React, { useState, useEffect } from 'react';
import { AssessmentPhase } from './components/AssessmentPhase';
import { PlanDisplay } from './components/PlanDisplay';
import { RefinementChat } from './components/RefinementChat';
import { coachAPI, AssessmentData } from './services/api';
import './styles/App.css';

type Phase = 'assessment' | 'plan' | 'refinement';

interface AppState {
  phase: Phase;
  sessionId: string | null;
  plan: string | null;
  assessment: AssessmentData | null;
  error: string | null;
}

function App() {
  const [appState, setAppState] = useState<AppState>({
    phase: 'assessment',
    sessionId: null,
    plan: null,
    assessment: null,
    error: null,
  });

  useEffect(() => {
    // Health check on mount with retry
    let retries = 0;
    const maxRetries = 3;
    
    const checkHealth = async () => {
      try {
        await coachAPI.healthCheck();
        console.log('✅ Backend connected');
        setAppState((prev) => ({ ...prev, error: null }));
      } catch (err) {
        console.error('Backend health check failed:', err, `(attempt ${retries + 1}/${maxRetries})`);
        if (retries < maxRetries) {
          retries++;
          setTimeout(checkHealth, 1500); // Retry after 1.5 seconds
        } else {
          setAppState((prev) => ({
            ...prev,
            error: 'Could not connect to the backend. Make sure the API server is running on http://localhost:8000',
          }));
        }
      }
    };
    
    checkHealth();
  }, []);

  const handleAssessmentComplete = (sessionId: string, plan: string, assessment: AssessmentData) => {
    setAppState({
      phase: 'plan',
      sessionId,
      plan,
      assessment,
      error: null,
    });
  };

  const handleRefinePage = () => {
    setAppState((prev) => ({
      ...prev,
      phase: 'refinement',
    }));
  };

  const handleBackToPlan = () => {
    setAppState((prev) => ({
      ...prev,
      phase: 'plan',
    }));
  };

  const handleReset = async () => {
    if (appState.sessionId) {
      try {
        await coachAPI.resetSession(appState.sessionId);
      } catch (err) {
        console.error('Error resetting session:', err);
      }
    }

    setAppState({
      phase: 'assessment',
      sessionId: null,
      plan: null,
      assessment: null,
      error: null,
    });
  };

  if (appState.error) {
    return (
      <div className="app-error">
        <div className="error-container">
          <h1>❌ Connection Error</h1>
          <p>{appState.error}</p>
          <p className="error-help">
            To start the backend, run:
            <br />
            <code>cd /Users/miked/CY_AI_Music_Coach && python -m uvicorn api.main:app --reload</code>
          </p>
          <button onClick={() => window.location.reload()}>Retry</button>
        </div>
      </div>
    );
  }

  return (
    <div className="app">
      {appState.phase === 'assessment' && (
        <AssessmentPhase onAssessmentComplete={handleAssessmentComplete} />
      )}

      {appState.phase === 'plan' && appState.sessionId && appState.plan && appState.assessment && (
        <div className="plan-page">
          <PlanDisplay
            sessionId={appState.sessionId}
            plan={appState.plan}
            assessment={appState.assessment}
            onRefine={handleRefinePage}
          />
          <div className="plan-footer">
            <button className="reset-button" onClick={handleReset}>
              🔄 Start New Session
            </button>
          </div>
        </div>
      )}

      {appState.phase === 'refinement' && appState.sessionId && appState.plan && (
        <RefinementChat
          sessionId={appState.sessionId}
          currentPlan={appState.plan}
          onBackToPlan={handleBackToPlan}
        />
      )}
    </div>
  );
}

export default App;

import React, { useState } from 'react';
import { coachAPI, AssessmentData } from '../services/api';
import '../styles/AssessmentPhase.css';

interface AssessmentPhaseProps {
  onAssessmentComplete: (sessionId: string, plan: string) => void;
}

const ASSESSMENT_QUESTIONS = [
  {
    id: 'guitar_type',
    question: 'What guitar are you using today?',
    options: ['Acoustic', 'Electric', 'Classical'],
  },
  {
    id: 'skill_level',
    question: "What's your current guitar level?",
    options: ['Beginner', 'Intermediate', 'Advanced'],
  },
  {
    id: 'genre',
    question: 'Which musical style interests you?',
    options: ['Rock', 'Blues', 'Jazz', 'Metal', 'Pop', 'Funk', 'Classical'],
  },
  {
    id: 'session_focus',
    question: 'What should the session focus on?',
    options: ['Technique & Warm-ups', 'Chords & Rhythm', 'Scales & Soloing', 'Song Learning', 'Mixed Routine'],
  },
  {
    id: 'mood',
    question: 'What mood appeals to you?',
    options: ['Mellow', 'Energetic', 'Moody', 'Challenging', 'Fun'],
  },
];

export const AssessmentPhase: React.FC<AssessmentPhaseProps> = ({ onAssessmentComplete }) => {
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState<Partial<AssessmentData>>({});
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const currentQuestion = ASSESSMENT_QUESTIONS[currentQuestionIndex];
  const isLastQuestion = currentQuestionIndex === ASSESSMENT_QUESTIONS.length - 1;

  const handleOptionSelect = async (selectedValue: string) => {
    // Update answers
    const updatedAnswers = {
      ...answers,
      [currentQuestion.id]: selectedValue,
    };
    setAnswers(updatedAnswers);

    // Auto-advance to next question or submit
    if (!isLastQuestion) {
      // Slight delay for visual feedback
      setTimeout(() => {
        setCurrentQuestionIndex(currentQuestionIndex + 1);
      }, 300);
    } else {
      // Final answer - submit assessment
      await submitAssessment(updatedAnswers as AssessmentData);
    }
  };

  const submitAssessment = async (assessmentData: AssessmentData) => {
    console.log('📧 Submitting assessment:', assessmentData);
    setIsLoading(true);
    setError(null);

    try {
      console.log('⏳ Waiting for plan generation...');
      const response = await coachAPI.submitAssessment(assessmentData);
      console.log('✅ Assessment response received:', response);
      
      if (!response.session_id || !response.plan) {
        throw new Error('Invalid response: missing session_id or plan');
      }
      
      onAssessmentComplete(response.session_id, response.plan);
    } catch (err: any) {
      console.error('❌ Error submitting assessment:', err);
      const errorMsg = err.response?.data?.detail || err.message || 'Failed to generate practice plan';
      setError(`${errorMsg}. Please try again.`);
      setIsLoading(false);
    }
  };

  const handlePrevious = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(currentQuestionIndex - 1);
    }
  };

  if (isLoading) {
    return (
      <div className="assessment-phase loading">
        <div className="spinner"></div>
        <p>Generating your personalized 30-minute practice plan...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="assessment-phase error">
        <div className="error-message">
          <h2>Oops!</h2>
          <p>{error}</p>
          <button onClick={() => window.location.reload()}>Try Again</button>
        </div>
      </div>
    );
  }

  return (
    <div className="assessment-phase">
      <div className="assessment-container">
        <div className="progress-bar">
          <div 
            className="progress-fill"
            style={{ width: `${((currentQuestionIndex + 1) / ASSESSMENT_QUESTIONS.length) * 100}%` }}
          ></div>
        </div>

        <div className="question-card">
          <h2 className="question-count">
            Question {currentQuestionIndex + 1} of {ASSESSMENT_QUESTIONS.length}
          </h2>
          
          <p className="question-text">{currentQuestion.question}</p>

          <div className="options-grid">
            {currentQuestion.options.map((option) => (
              <button
                key={option}
                className={`option-button ${answers[currentQuestion.id as keyof AssessmentData] === option ? 'selected' : ''}`}
                onClick={() => handleOptionSelect(option)}
                disabled={isLoading}
              >
                {option}
              </button>
            ))}
          </div>

          <div className="navigation-buttons">
            <button
              className="nav-button prev"
              onClick={handlePrevious}
              disabled={currentQuestionIndex === 0 || isLoading}
            >
              ← Previous
            </button>
            {isLastQuestion && answers[currentQuestion.id as keyof AssessmentData] && (
              <button
                className="nav-button submit"
                onClick={() => submitAssessment(answers as AssessmentData)}
                disabled={isLoading}
              >
                Generate Plan →
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

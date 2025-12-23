'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import Header from '../../components/Header';
import config from '../../lib/config';
import { generateMaskedId, storeMaskedIdMapping, getCurrentMaskedId } from '../../lib/session-utils';

interface GuestSession {
  session_id: string;
  createdAt: string;
  expiresAt: string;
  active: boolean;
  ip_address?: string;
  user_agent?: string;
  last_active?: string;
}

interface GuestSessionResponse {
  success: boolean;
  data: GuestSession;
}

export default function ProjectsPage() {
  const [guestSession, setGuestSession] = useState<GuestSession | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isCreatingSession, setIsCreatingSession] = useState(false);

  useEffect(() => {
    // Check for existing session on component mount
    checkExistingSession();
  }, []);

  const checkExistingSession = async () => {
    try {
      const sessionId = localStorage.getItem('neural_playground_session_id');
      if (sessionId) {
        // Validate session with backend API
        const response = await fetch(`${config.apiBaseUrl}${config.api.guests.sessionById(sessionId)}`);
        if (response.ok) {
          const sessionResponse: GuestSessionResponse = await response.json();
          if (sessionResponse.success && sessionResponse.data.active) {
            // Check if session is still valid
            const now = new Date();
            const expiresAt = new Date(sessionResponse.data.expiresAt);
            
            if (now < expiresAt) {
              setGuestSession(sessionResponse.data);
            } else {
              // Session expired, remove it
              localStorage.removeItem('neural_playground_session_id');
      localStorage.removeItem('neural_playground_session_created');
          localStorage.removeItem('neural_playground_session_created');
            localStorage.removeItem('neural_playground_session_created');
              localStorage.removeItem('neural_playground_session_created');
            }
          } else {
            // Session invalid, remove it
            localStorage.removeItem('neural_playground_session_id');
      localStorage.removeItem('neural_playground_session_created');
          localStorage.removeItem('neural_playground_session_created');
            localStorage.removeItem('neural_playground_session_created');
          }
        } else {
          // Session not found on server, remove local storage
          localStorage.removeItem('neural_playground_session_id');
      localStorage.removeItem('neural_playground_session_created');
          localStorage.removeItem('neural_playground_session_created');
        }
      }
    } catch (error) {
      console.error('Error checking session:', error);
      localStorage.removeItem('neural_playground_session_id');
      localStorage.removeItem('neural_playground_session_created');
    }
    setIsLoading(false);
  };

  const createGuestSession = async (): Promise<string | null> => {
    try {
      setIsCreatingSession(true);
      
      const response = await fetch(`${config.apiBaseUrl}${config.api.guests.session}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const sessionResponse: GuestSessionResponse = await response.json();
        if (sessionResponse.success) {
          // Generate masked ID for URL
          const maskedId = generateMaskedId(sessionResponse.data.session_id);
          
          // Store session ID, creation timestamp, and masked ID mapping
          const now = Date.now();
          const sevenDaysFromNow = now + (7 * 24 * 60 * 60 * 1000); // 7 days in milliseconds
          
          localStorage.setItem('neural_playground_session_id', sessionResponse.data.session_id);
          localStorage.setItem('neural_playground_session_created', now.toString());
          localStorage.setItem('neural_playground_session_expires', sevenDaysFromNow.toString());
          localStorage.setItem('neural_playground_session_last_activity', now.toString());
          storeMaskedIdMapping(maskedId, sessionResponse.data.session_id);
          
          setGuestSession(sessionResponse.data);
          return maskedId; // Return masked ID instead of session ID
        }
      }
      
      throw new Error('Failed to create guest session');
    } catch (error) {
      console.error('Error creating guest session:', error);
      return null;
    } finally {
      setIsCreatingSession(false);
    }
  };



  const handleTryNow = async () => {
    if (guestSession) {
      // User has existing session, get or generate masked ID
      const currentMaskedId = getCurrentMaskedId();
      if (currentMaskedId) {
        window.location.href = `/projects/${currentMaskedId}`;
      } else {
        // Generate new masked ID for existing session
        const maskedId = generateMaskedId(guestSession.session_id);
        storeMaskedIdMapping(maskedId, guestSession.session_id);
        window.location.href = `/projects/${maskedId}`;
      }
    } else {
      // Check localStorage for existing session first
      const existingSessionId = localStorage.getItem('neural_playground_session_id');
      if (existingSessionId) {
        // Check if we have a masked ID for this session
        const currentMaskedId = getCurrentMaskedId();
        if (currentMaskedId) {
          window.location.href = `/projects/${currentMaskedId}`;
        } else {
          // Generate masked ID for existing session
          const maskedId = generateMaskedId(existingSessionId);
          storeMaskedIdMapping(maskedId, existingSessionId);
          window.location.href = `/projects/${maskedId}`;
        }
        return;
      }
      
      // Create new session and redirect
      const maskedId = await createGuestSession();
      if (maskedId) {
        window.location.href = `/projects/${maskedId}`;
      } else {
        alert('Failed to create session. Please try again.');
      }
    }
  };

  return (
    <div className="min-h-screen bg-[#1c1c1c] text-white">
      {/* Header Component */}
      <Header />

      {/* Main Content */}
      <main className="pt-24 pb-20 px-4 sm:px-6 lg:px-8">
        <div>
          {/* Back Button */}
          <div className="flex justify-start mb-8">
            <Link
              href="/"
              className="p-2 text-white/70 hover:text-white hover:bg-[#bc6cd3]/10 rounded-lg transition-all duration-300 flex items-center gap-2 text-sm"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              Back to Home
            </Link>
          </div>
          
          <div className="text-center">
            {/* Main Heading */}
            <h1 className="text-4xl md:text-6xl font-bold mb-8">
              Get started with machine learning
            </h1>
          
          
          {/* Try It Now / Go to Projects Button */}
          <button 
            onClick={handleTryNow}
            disabled={isLoading || isCreatingSession}
            className="bg-[#dcfc84] text-[#1c1c1c] px-10 py-4 rounded-lg text-xl font-medium hover:scale-105 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? 'Loading...' : isCreatingSession ? 'Creating session...' : guestSession ? 'Go to your projects' : 'Try it now'}
          </button>
          
          {guestSession && (
            <p className="text-sm text-white mt-4">
              Welcome back! Session expires on{' '}
              {new Date(guestSession.expiresAt).toLocaleDateString()} at{' '}
              {new Date(guestSession.expiresAt).toLocaleTimeString()}
            </p>
          )}
          
          {/* Optional additional content section */}
          <div className="mt-20">
            <div className="grid md:grid-cols-3 gap-8 text-left">
              <div className="bg-[#1c1c1c] border border-[#bc6cd3]/20 rounded-lg p-6">
                <h3 className="text-xl font-bold mb-4 text-center text-white">🎮 Create Games</h3>
                <p className="text-white text-center">
                  Build interactive games using Scratch and machine learning
                </p>
              </div>
              
              <div className="bg-[#1c1c1c] border border-[#bc6cd3]/20 rounded-lg p-6">
                <h3 className="text-xl font-bold mb-4 text-center text-white">🤖 Train AI</h3>
                <p className="text-white text-center">
                  Teach computers to recognize patterns and make decisions
                </p>
              </div>
              
              <div className="bg-[#1c1c1c] border border-[#bc6cd3]/20 rounded-lg p-6">
                <h3 className="text-xl font-bold mb-4 text-center text-white">📚 Learn</h3>
                <p className="text-white text-center">
                  Understand machine learning concepts through hands-on projects
                </p>
              </div>
            </div>
          </div>
            </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-[#1c1c1c] border-t border-[#bc6cd3]/20 py-8 px-4 sm:px-6 lg:px-8">
        <div className="text-center">
          <p className="text-sm text-white">
            © 2024 TheNeural Playground. Empowering the next generation of AI creators.
          </p>
        </div>
      </footer>
    </div>
  );
}

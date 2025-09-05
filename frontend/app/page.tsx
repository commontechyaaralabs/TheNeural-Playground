'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import Header from '../components/Header';
import config from '../lib/config';
import { 
  getOrCreateMaskedId
} from '../lib/session-utils';
import { cleanupSessionWithReason, SessionCleanupReason } from '../lib/session-cleanup';

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

export default function Home() {
  const [hasActiveSession, setHasActiveSession] = useState(false);
  const [userSessionId, setUserSessionId] = useState<string>('');
  const [isCheckingSession, setIsCheckingSession] = useState(true);

  // Function to clean up session and reset local state
  const handleSessionCleanup = async (reason: SessionCleanupReason, sessionId?: string) => {
    await cleanupSessionWithReason(reason, sessionId);
    
    // Reset local state
    setHasActiveSession(false);
    setUserSessionId('');
  };

  const checkExistingSession = async () => {
    console.log('🔍 Checking for existing session...');
    
    try {
      const storedSessionId = localStorage.getItem('neural_playground_session_id');
      const sessionCreatedAt = localStorage.getItem('neural_playground_session_created');
      
      console.log('📋 Session check details:', {
        hasSessionId: !!storedSessionId,
        sessionId: storedSessionId?.substring(0, 8) + '...',
        hasCreatedTime: !!sessionCreatedAt,
        createdTime: sessionCreatedAt ? new Date(parseInt(sessionCreatedAt)).toISOString() : null
      });
      
      if (!storedSessionId) {
        console.log('❌ No session ID found in localStorage');
        setIsCheckingSession(false);
        return;
      }

      // Check if session is expired based on 7-day rule
      const sessionExpiresAt = localStorage.getItem('neural_playground_session_expires');
      const now = Date.now();
      
      // First check explicit expiry time if available
      if (sessionExpiresAt) {
        const expiryTime = parseInt(sessionExpiresAt);
        if (now > expiryTime) {
          console.log('⏰ Session expired based on explicit expiry time, cleaning up');
          await handleSessionCleanup(SessionCleanupReason.EXPIRED_7_DAYS, storedSessionId);
          setIsCheckingSession(false);
          return;
        }
        console.log(`📅 Session expires at: ${new Date(expiryTime).toISOString()}`);
      } else if (sessionCreatedAt) {
        // Fallback to creation time check for older sessions
        const createdDate = new Date(parseInt(sessionCreatedAt));
        const daysDiff = (now - createdDate.getTime()) / (1000 * 3600 * 24);
        
        console.log(`📅 Session age: ${daysDiff.toFixed(1)} days (fallback check)`);
        
        if (daysDiff >= 7) {
          console.log('⏰ Session expired after 7 days (fallback), cleaning up');
          await handleSessionCleanup(SessionCleanupReason.EXPIRED_7_DAYS, storedSessionId);
          setIsCheckingSession(false);
          return;
        }
      }

      // Validate session with backend
      console.log('🌐 Validating session with backend API...');
      const response = await fetch(`${config.apiBaseUrl}${config.api.guests.sessionById(storedSessionId)}`);
      
      console.log('📡 API Response:', {
        status: response.status,
        ok: response.ok,
        url: response.url
      });
      
      if (response.ok) {
        const sessionResponse: GuestSessionResponse = await response.json();
        console.log('📄 Session response:', {
          success: sessionResponse.success,
          active: sessionResponse.data?.active,
          expiresAt: sessionResponse.data?.expiresAt
        });
        
        if (sessionResponse.success && sessionResponse.data.active) {
          const now = new Date();
          const expiresAt = new Date(sessionResponse.data.expiresAt);
          
          console.log('⏱️ Time check:', {
            now: now.toISOString(),
            expiresAt: expiresAt.toISOString(),
            isValid: now < expiresAt
          });
          
          if (now < expiresAt) {
            // Session is valid, generate masked ID and set state
            // Get or create masked ID (reuses existing if available)
            const maskedId = getOrCreateMaskedId(storedSessionId);
            
            // Update last activity time
            localStorage.setItem('neural_playground_session_last_activity', Date.now().toString());
            
            setUserSessionId(maskedId);
            setHasActiveSession(true);
            console.log('✅ Session is valid! Setting hasActiveSession to true');
            console.log('🔗 Using masked ID:', maskedId);
            console.log('⏰ Updated last activity time');
          } else {
            // Session expired on backend
            console.log('⏰ Session expired on backend');
            await handleSessionCleanup(SessionCleanupReason.EXPIRED_BACKEND, storedSessionId);
          }
        } else {
          // Session inactive
          console.log('❌ Session inactive on backend');
          await handleSessionCleanup(SessionCleanupReason.INACTIVE_BACKEND, storedSessionId);
        }
      } else {
        // Session not found on server
        console.log('❌ Session not found on server, status:', response.status);
        
        // Get error details
        try {
          const errorText = await response.text();
          console.log('Error details:', errorText);
        } catch {
          console.log('Could not read error response');
        }
        
        await handleSessionCleanup(SessionCleanupReason.NOT_FOUND_BACKEND, storedSessionId);
      }
    } catch (error) {
      console.error('❌ Network error checking existing session:', error);
      // Don't remove session on network errors, just don't show as active
      // This allows users to still access their session if there are temporary network issues
    }
    
    // Final state will be logged after state updates
    setIsCheckingSession(false);
  };

  useEffect(() => {
    checkExistingSession();
  }, []);

  // Add useEffect to log final state changes
  useEffect(() => {
    if (!isCheckingSession) {
      console.log('🏁 Session check complete. Final state:', { 
        hasActiveSession, 
        userSessionId: userSessionId ? userSessionId.substring(0, 8) + '...' : null,
        buttonText: hasActiveSession ? 'Go to Projects →' : 'Get Started →'
      });
    }
  }, [isCheckingSession, hasActiveSession, userSessionId]);

  const getProjectsUrl = () => {
    if (hasActiveSession && userSessionId) {
      return `/projects/${userSessionId}`;
    }
    return '/projects';
  };

  const getButtonText = () => {
    console.log('🔘 Button text check:', { isCheckingSession, hasActiveSession, userSessionId });
    
    if (isCheckingSession) {
      return 'Loading...';
    }
    if (hasActiveSession) {
      return 'Go to Projects →';
    }
    return 'Get Started →';
  };

  return (
    <div className="min-h-screen bg-[#1c1c1c] text-white">
      {/* Header Component */}
      <Header showAboutLink={true} />

      {/* Hero Section */}
      <section className="pt-24 pb-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto text-center">
          <h1 className="text-4xl md:text-6xl font-bold mb-6 text-white">
            Teach a computer to{' '}
            <span className="text-[#dcfc84]">
              play a game
            </span>
          </h1>
          
          <p className="text-xl md:text-2xl text-white mb-6 max-w-4xl mx-auto">
            Discover the fascinating world of machine learning through interactive game development. 
            Learn and create your own AI Model - Gather Data, Train the AI models and deploy as part of your UI environment to see it in action.
          </p>
          
          {isCheckingSession && (
            <p className="text-lg text-[#dcfc84] mb-6 max-w-4xl mx-auto">
              Please wait for few minutes until system gets started
            </p>
          )}
          
          <div className="flex flex-col sm:flex-row gap-6 justify-center">
            <Link 
              href={getProjectsUrl()}
              className={`px-8 py-4 rounded-lg text-lg font-medium transition-all duration-300 text-center ${
                isCheckingSession 
                  ? 'bg-gray-500 text-gray-300 cursor-not-allowed' 
                  : 'bg-[#dcfc84] text-[#1c1c1c] hover:scale-105'
              }`}
            >
              {getButtonText()}
            </Link>
            <Link 
              href="/about"
              className="border border-[#bc6cd3] text-white px-8 py-4 rounded-lg text-lg font-medium hover:bg-[#bc6cd3] hover:text-[#1c1c1c] transition-all duration-300 text-center"
            >
              Learn More
            </Link>
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-5xl font-bold mb-4 text-white">How It Works</h2>
            <p className="text-xl text-white max-w-3xl mx-auto">
              Follow these three simple steps to create your own AI-powered game
            </p>
          </div>
          
          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                number: "1",
                title: "Collect Examples",
                description: "Gather training data by collecting examples of objects, actions, or patterns you want your AI to recognize."
              },
              {
                number: "2", 
                title: "Train Your Model",
                description: "Use our intuitive training interface to teach your computer to recognize the patterns in your examples."
              },
                             {
                 number: "3",
                 title: "Create & Play", 
                 description: "Build and deploy your AI models inside games in Scratch and more to leverage your trained AI model for interactive experiences."
               }
            ].map((step, index) => (
              <div key={index} className="relative">
                <div className="bg-[#1c1c1c] border border-[#bc6cd3]/20 rounded-lg p-8 h-full">
                  <div className="w-12 h-12 bg-[#dcfc84] rounded-full flex items-center justify-center text-[#1c1c1c] font-bold text-lg mb-6">
                    {step.number}
                  </div>
                  <h3 className="text-xl font-bold mb-4 text-white">{step.title}</h3>
                  <p className="text-white">{step.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl md:text-5xl font-bold mb-6 text-white">
            Ready to Start Your AI Journey?
          </h2>
          <p className="text-xl text-white mb-12">
            Join thousands of students and educators who are already creating amazing AI-powered projects.
          </p>
          <Link 
            href={getProjectsUrl()}
            className={`px-12 py-4 rounded-lg text-xl font-medium transition-all duration-300 inline-block text-center ${
              isCheckingSession 
                ? 'bg-gray-500 text-gray-300 cursor-not-allowed' 
                : 'bg-[#dcfc84] text-[#1c1c1c] hover:scale-105'
            }`}
          >
            {hasActiveSession ? 'Go to Your Projects' : 'Start Creating Now'}
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-[#1c1c1c] border-t border-[#bc6cd3]/20 py-8 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto text-center">
          <p className="text-sm text-white">
            © 2024 TheNeural Playground. Empowering the next generation of AI creators.
          </p>
        </div>
      </footer>
    </div>
  );
}

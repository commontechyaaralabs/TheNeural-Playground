'use client';


import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import Header from '../../../../components/Header';
import config from '../../../../lib/config';
import { 
  getSessionIdFromMaskedId, 
  isMaskedId, 
  isSessionId, 
  getOrCreateMaskedId,
  getProjectIdFromMaskedId,
  isMaskedProjectId,
  isProjectId
} from '../../../../lib/session-utils';
import { cleanupSessionWithReason, SessionCleanupReason } from '../../../../lib/session-cleanup';
import Link from 'next/link'

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

interface Project {
  id: string;
  name: string;
  type: string;  // Changed from model_type to type
  createdAt: string;
  description?: string;
  status?: string;
  maskedId?: string;
}

export default function ProjectDetailsPage() {
  const [guestSession, setGuestSession] = useState<GuestSession | null>(null);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isValidSession, setIsValidSession] = useState(false);
  const [actualSessionId, setActualSessionId] = useState<string>('');
  const [actualProjectId, setActualProjectId] = useState<string>('');

  const params = useParams();
  const urlUserId = params?.userid as string;
  const urlProjectId = params?.projectid as string;

  useEffect(() => {
    validateGuestSession();
  }, [urlUserId, urlProjectId]); // eslint-disable-line react-hooks/exhaustive-deps

  const validateGuestSession = async () => {
    if (!urlUserId || !urlProjectId) {
      setIsLoading(false);
      return;
    }

    try {
      let sessionId: string;
      let projectId: string;

      // Check if URL param is a masked ID or full session ID
      if (isMaskedId(urlUserId)) {
        const realSessionId = getSessionIdFromMaskedId(urlUserId);
        if (!realSessionId) {
          window.location.href = '/projects';
          return;
        }
        sessionId = realSessionId;
      } else if (isSessionId(urlUserId)) {
        const maskedId = getOrCreateMaskedId(urlUserId);
        window.location.href = `/projects/${maskedId}/${urlProjectId}`;
        return;
      } else {
        window.location.href = '/projects';
        return;
      }

      // Check if project ID is masked
      if (isMaskedProjectId(urlProjectId)) {
        const realProjectId = getProjectIdFromMaskedId(urlProjectId);
        if (!realProjectId) {
          window.location.href = `/projects/${urlUserId}`;
          return;
        }
        projectId = realProjectId;
      } else if (isProjectId(urlProjectId)) {
        projectId = urlProjectId;
      } else {
        window.location.href = `/projects/${urlUserId}`;
        return;
      }

      // Check if session exists in localStorage
      const storedSessionId = localStorage.getItem('neural_playground_session_id');
      
      if (!storedSessionId) {
        window.location.href = '/projects';
        return;
      }

      if (storedSessionId !== sessionId) {
        const correctMaskedId = getOrCreateMaskedId(storedSessionId);
        window.location.href = `/projects/${correctMaskedId}`;
        return;
      }

      // Validate session with backend API
      const response = await fetch(`${config.apiBaseUrl}${config.api.guests.sessionById(sessionId)}`);
      
      if (response.ok) {
        const sessionResponse: GuestSessionResponse = await response.json();
        if (sessionResponse.success && sessionResponse.data.active) {
          const now = new Date();
          const expiresAt = new Date(sessionResponse.data.expiresAt);
          
          if (now < expiresAt) {
            setActualSessionId(sessionId);
            setActualProjectId(projectId);
            setGuestSession(sessionResponse.data);
            setIsValidSession(true);
            
            // Load project after setting session as valid
            await loadProject(sessionId, projectId);
          } else {
            console.error('Session expired');
                        await cleanupSessionWithReason(SessionCleanupReason.EXPIRED_BACKEND);
            window.location.href = '/projects';
            return;
          }
        } else {
          console.error('Session inactive');
                      await cleanupSessionWithReason(SessionCleanupReason.INACTIVE_BACKEND);
          window.location.href = '/projects';
          return;
        }
      } else {
        console.error('Session validation failed:', response.status);
                    await cleanupSessionWithReason(SessionCleanupReason.NOT_FOUND_BACKEND);
        window.location.href = '/projects';
        return;
      }
    } catch (error) {
      console.error('Error validating session:', error);
                  await cleanupSessionWithReason(SessionCleanupReason.EXPIRED_BACKEND);
      window.location.href = '/projects';
      return;
    }
    setIsLoading(false);
  };

  const loadProject = async (sessionId: string, projectId: string) => {
    try {
      console.log('Loading project:', projectId, 'for session:', sessionId);
      
      // Load all projects for the session and find the specific project
      const response = await fetch(`${config.apiBaseUrl}/api/guests/session/${sessionId}/projects`);
      
      if (response.ok) {
        const projectsResponse = await response.json();
        console.log('Projects response:', projectsResponse);
        
        if (projectsResponse.success && projectsResponse.data) {
          console.log('Available projects:', projectsResponse.data.map((p: Project) => ({ id: p.id, name: p.name })));
          
          // Find the specific project by ID
          const project = projectsResponse.data.find((p: Project) => p.id === projectId);
          
          if (project) {
            console.log('Found project:', project);
            setSelectedProject(project);
          } else {
            // Project not found in the session's projects
            console.error('Project not found in session projects. Looking for:', projectId);
            console.error('Available project IDs:', projectsResponse.data.map((p: Project) => p.id));
            window.location.href = `/projects/${urlUserId}`;
            return;
          }
        } else {
          // No projects found or empty response
          console.error('No projects found for session or invalid response structure');
          window.location.href = `/projects/${urlUserId}`;
          return;
        }
      } else {
        // Failed to load projects
        console.error('Failed to load session projects:', response.status);
        window.location.href = `/projects/${urlUserId}`;
        return;
      }
    } catch (error) {
      console.error('Error loading session projects:', error);
      window.location.href = `/projects/${urlUserId}`;
      return;
    }
  };



  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#1c1c1c] text-white">
        <Header />
        <main className="pt-24 pb-20 px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-center min-h-[400px]">
            <div className="text-white text-xl">Loading...</div>
          </div>
        </main>
      </div>
    );
  }

  if (!isValidSession) {
    return (
      <div className="min-h-screen bg-[#1c1c1c] text-white">
        <Header />
        <main className="pt-24 pb-20 px-4 sm:px-6 lg:px-8">
          <div className="max-w-4xl mx-auto text-center">
            <h1 className="text-3xl md:text-4xl font-semibold text-white mb-4">
              Session Expired
            </h1>
            <p className="text-lg text-white mb-8">
              Your session has expired. Please start a new session.
            </p>
            <Link 
              href="/projects"
              className="bg-[#dcfc84] text-[#1c1c1c] px-8 py-4 rounded-lg text-lg font-medium hover:scale-105 transition-all duration-300 inline-block"
            >
              Start New Session
            </Link>
          </div>
        </main>
      </div>
    );
  }

  if (!selectedProject) {
    return (
      <div className="min-h-screen bg-[#1c1c1c] text-white">
        <Header />
        <main className="pt-24 pb-20 px-4 sm:px-6 lg:px-8">
          <div className="max-w-4xl mx-auto text-center">
            <h1 className="text-3xl md:text-4xl font-semibold text-white mb-4">
              Project Not Found
            </h1>
            <p className="text-lg text-white mb-8">
              The project you&apos;re looking for doesn&apos;t exist or you don&apos;t have access to it.
            </p>
            <Link 
              href={`/projects/${urlUserId}`}
              className="bg-[#dcfc84] text-[#1c1c1c] px-8 py-4 rounded-lg text-lg font-medium hover:scale-105 transition-all duration-300 inline-block"
            >
              Back to Projects
            </Link>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#1c1c1c] text-white">
      <Header />

      <main className="pt-24 pb-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          {/* Navigation Breadcrumb */}
          <div className="mb-6 text-lg font-semibold text-white">
            <span>
              <Link href={`/projects/${urlUserId}`} className="hover:text-[#dcfc84] transition-colors">
                Projects List
              </Link>
            </span>
            <span className="mx-2">→</span>
            <span className="text-white">&ldquo;{selectedProject.name}&rdquo;</span>
          </div>

          {/* Project Header with Back Button */}
          <div className="flex items-center mb-12">
            <Link
              href={`/projects/${urlUserId}`}
              className="p-2 text-white/70 hover:text-white hover:bg-[#bc6cd3]/10 rounded-lg transition-all duration-300 mr-4"
            >
              <svg 
                className="w-6 h-6" 
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
              >
                <path 
                  strokeLinecap="round" 
                  strokeLinejoin="round" 
                  strokeWidth={2} 
                  d="M15 19l-7-7 7-7" 
                />
              </svg>
            </Link>
            <h1 className="text-3xl md:text-4xl font-semibold text-white text-center flex-1">
              &ldquo;{selectedProject.name}&rdquo;
            </h1>
          </div>

          {/* ML Action Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl mx-auto">
            {/* Train Card */}
            <div className="bg-[#1c1c1c] border border-[#bc6cd3]/20 rounded-xl p-8 text-center hover:bg-[#bc6cd3]/5 transition-all duration-300 flex flex-col">
              <h2 className="text-2xl md:text-3xl font-bold text-blue-400 mb-6">
                1. Collect Data
              </h2>
              <p className="text-white mb-8 text-sm md:text-base leading-relaxed flex-grow">
                Collect examples of what you want the AI to recognize
              </p>
              <button 
                onClick={() => {
                  window.location.href = `/projects/${urlUserId}/${urlProjectId}/train`;
                }}
                className="w-full bg-[#dcfc84] hover:bg-[#dcfc84]/90 text-[#1c1c1c] py-3 px-6 rounded-lg font-medium transition-all duration-300"
              >
                Collect Data
              </button>
            </div>

            {/* Learn & Test Card */}
            <div className="bg-[#1c1c1c] border border-[#bc6cd3]/20 rounded-xl p-8 text-center hover:bg-[#bc6cd3]/5 transition-all duration-300 flex flex-col">
              <h2 className="text-2xl md:text-3xl font-bold text-purple-400 mb-6">
                2. Train the AI
              </h2>
              <p className="text-white mb-8 text-sm md:text-base leading-relaxed flex-grow">
                Use the data from Step 1 to train computer and build an AI model
              </p>
              <button 
                onClick={() => {
                  window.location.href = `/projects/${urlUserId}/${urlProjectId}/learn`;
                }}
                className="w-full bg-[#dcfc84] hover:bg-[#dcfc84]/90 text-[#1c1c1c] py-3 px-6 rounded-lg font-medium transition-all duration-300"
              >
                Train the AI
              </button>
            </div>

            {/* Make Card */}
            <div className="bg-[#1c1c1c] border border-[#bc6cd3]/20 rounded-xl p-8 text-center hover:bg-[#bc6cd3]/5 transition-all duration-300 flex flex-col">
              <h2 className="text-2xl md:text-3xl font-bold text-orange-400 mb-6">
                3. Use the AI
              </h2>
              <p className="text-white mb-8 text-sm md:text-base leading-relaxed flex-grow">
                Use the AI / Machine learning model inside your User Interface (UI) like Scratch and more...
              </p>
              <button 
                onClick={() => {
                  window.location.href = `/projects/${urlUserId}/${urlProjectId}/make`;
                }}
                className="w-full bg-[#dcfc84] hover:bg-[#dcfc84]/90 text-[#1c1c1c] py-3 px-6 rounded-lg font-medium transition-all duration-300"
              >
                Use the AI
              </button>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

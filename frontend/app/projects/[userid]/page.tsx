'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import Header from '../../../components/Header';
import config from '../../../lib/config';
import { 
  getSessionIdFromMaskedId, 
  isMaskedId, 
  isSessionId, 
  getOrCreateMaskedId,
  generateMaskedProjectId,
  storeMaskedProjectIdMapping,
  getProjectIdFromMaskedId,
  isMaskedProjectId
} from '../../../lib/session-utils';
import { cleanupSessionWithReason, SessionCleanupReason, updateSessionActivity } from '../../../lib/session-cleanup';

/**
 * Projects Page with Hash-Based Navigation
 * 
 * URL Structure:
 * - /projects/{userId} - Main projects list (default)
 * - /projects/{userId}#new-project - Create new project form
 * - /projects/{userId}#project-{projectId} - ML Project Section (Train/Test/Make)
 * - /projects/{userId}#project-{projectId}/train - Training section for specific project
 * 
 * Sections:
 * 1. projects-list: Shows existing projects or "No Projects Found" state
 * 2. new-project: Project creation form
 * 3. project-details: ML Project Section with Train/Test/Make cards
 * 4. project-train: Training interface for specific project
 * 
 * Navigation Flow:
 * - Train button → /projects/{userId}#project-{projectId}/train (stays on same page)
 * - Back from Train → /projects/{userId}#project-{projectId} (returns to specific project's ML section)
 * 
 * Note: Training functionality is now integrated into the main page using hash navigation
 */

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
  type: string;  // Changed from model_type to type to match backend
  createdAt: string;
  description?: string;
  status?: string;
  maskedId?: string;
  teachable_machine_link?: string;  // Changed from teachable_link to teachable_machine_link to match backend
  modelStatus?: 'available' | 'unavailable';  // Model training status
}



function CreateProjectPage() {
  const [projectName, setProjectName] = useState('');
  const [projectType, setProjectType] = useState('');
  const [teachableLink, setTeachableLink] = useState('');
  const [projects, setProjects] = useState<Project[]>([]);
  const [currentSection, setCurrentSection] = useState<'projects-list' | 'new-project' | 'project-details' | 'edit-project'>('projects-list');
  const [selectedProject] = useState<Project | null>(null);
  const [editingProject, setEditingProject] = useState<Project | null>(null);
  const [guestSession, setGuestSession] = useState<GuestSession | null>(null);
  const [isValidSession, setIsValidSession] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingProjects, setIsLoadingProjects] = useState(false);
  const [isCreatingProject, setIsCreatingProject] = useState(false);
  const [isUpdatingProject, setIsUpdatingProject] = useState(false);
  const [urlValidation, setUrlValidation] = useState<{
    isValidating: boolean;
    isValid: boolean | null;
    error: string | null;
  }>({
    isValidating: false,
    isValid: null,
    error: null
  });
  const [validationTimeout, setValidationTimeout] = useState<NodeJS.Timeout | null>(null);
  


  const params = useParams();
  const urlParam = params?.userid as string;
  const [actualSessionId, setActualSessionId] = useState<string>('');

  useEffect(() => {
    validateGuestSession();
  }, [urlParam]); // eslint-disable-line react-hooks/exhaustive-deps

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (validationTimeout) {
        clearTimeout(validationTimeout);
      }
    };
  }, [validationTimeout]);



  const validateGuestSession = async () => {
    if (!urlParam) {
      setIsLoading(false);
      return;
    }

    try {
      let sessionId: string;

      // Check if URL param is a masked ID or full session ID
      if (isMaskedId(urlParam)) {
        // URL has masked ID, get the real session ID
        const realSessionId = getSessionIdFromMaskedId(urlParam);
        if (!realSessionId) {
          // Masked ID not found, redirect to main projects page
          window.location.href = '/projects';
          return;
        }
        sessionId = realSessionId;
      } else if (isSessionId(urlParam)) {
        // URL has full session ID, redirect to masked version
        const maskedId = getOrCreateMaskedId(urlParam);
        window.location.href = `/projects/${maskedId}`;
        return;
      } else {
        // Invalid URL format
        window.location.href = '/projects';
        return;
      }

      // Check if session exists in localStorage
      const storedSessionId = localStorage.getItem('neural_playground_session_id');
      
      if (!storedSessionId) {
        // No session stored, redirect to main projects page
        window.location.href = '/projects';
        return;
      }

      if (storedSessionId !== sessionId) {
        // Session ID doesn't match stored session, redirect to correct one
        const correctMaskedId = getOrCreateMaskedId(storedSessionId);
        window.location.href = `/projects/${correctMaskedId}`;
        return;
      }

      // Validate session with backend API
      const response = await fetch(`${config.apiBaseUrl}${config.api.guests.sessionById(sessionId)}`);
      
      if (response.ok) {
        const sessionResponse: GuestSessionResponse = await response.json();
        if (sessionResponse.success && sessionResponse.data.active) {
          // Check if session is still valid
          const now = new Date();
          const expiresAt = new Date(sessionResponse.data.expiresAt);
          
          if (now < expiresAt) {
            setActualSessionId(sessionId);
            setGuestSession(sessionResponse.data);
            setIsValidSession(true);
            
            // Update session activity
            updateSessionActivity();
            
            // Start loading projects immediately
            setIsLoadingProjects(true);
            loadGuestProjects(sessionResponse.data.session_id);
          } else {
            // Session expired
                        await cleanupSessionWithReason(SessionCleanupReason.EXPIRED_BACKEND);
            window.location.href = '/projects';
            return;
          }
        } else {
          // Session inactive
                      await cleanupSessionWithReason(SessionCleanupReason.INACTIVE_BACKEND);
          window.location.href = '/projects';
          return;
        }
      } else {
        // Session not found on server
                    await cleanupSessionWithReason(SessionCleanupReason.EXPIRED_BACKEND);
        window.location.href = '/projects';
        return;
      }
    } catch (error) {
      console.error('Error validating session:', error);
      await cleanupSessionWithReason(SessionCleanupReason.ERROR_FALLBACK);
      window.location.href = '/projects';
      return;
    }
    setIsLoading(false);
  };

  const loadGuestProjects = async (sessionId: string) => {
    try {
      const response = await fetch(`${config.apiBaseUrl}/api/guests/session/${sessionId}/projects`);
      
      if (response.ok) {
        const projectsResponse = await response.json();
        if (projectsResponse.success && projectsResponse.data) {
          // Generate and store masked IDs for each project
          const projectsWithMaskedIds = (projectsResponse.data as Project[]).map((project: Project) => {
            const maskedProjectId = generateMaskedProjectId(project.id);
            
            // Check if mapping already exists
            const existingId = getProjectIdFromMaskedId(maskedProjectId);
            if (!existingId) {
              storeMaskedProjectIdMapping(maskedProjectId, project.id);
            }
            
            return {
              ...project,
              maskedId: maskedProjectId
            };
          });
          
          // Load model status for each project in parallel
          const projectsWithStatus = await Promise.all(
            projectsWithMaskedIds.map(async (project) => {
              // Only fetch model status for text recognition and image recognition projects
              if (project.type === 'text-recognition' || project.type === 'image-recognition') {
                const modelStatus = await getProjectModelStatus(project.maskedId || project.id);
                return {
                  ...project,
                  modelStatus
                };
              }
              return project;
            })
          );
          
          setProjects(projectsWithStatus);
        } else {
          // No projects found or empty response
          setProjects([]);
        }
      } else {
        console.error('Failed to load projects:', response.status);
        setProjects([]);
      }
    } catch (error) {
      console.error('Error loading projects:', error);
      setProjects([]);
    } finally {
      // Always stop loading projects when done
      setIsLoadingProjects(false);
    }
  };

  const createGuestProject = async (projectData: { name: string; type: string; description?: string; teachable_machine_link?: string }) => {
    try {
      // Get session ID from localStorage
      const sessionId = localStorage.getItem('neural_playground_session_id');
      if (!sessionId) {
        throw new Error('No session found');
      }

      const payload = {
        name: projectData.name,
        description: projectData.description || "",
        type: projectData.type,
        createdBy: "",
        teacher_id: "",
        classroom_id: "",
        student_id: "",
        tags: [],
        notes: "",
        config: {
          epochs: 100,
          batchSize: 32,
          learningRate: 0.001,
          validationSplit: 0.2
        },
        teachable_machine_link: projectData.teachable_machine_link || undefined
      };
      

      const response = await fetch(`${config.apiBaseUrl}/api/guests/session/${sessionId}/projects`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        const projectResponse = await response.json();
        if (projectResponse.success) {
          // Generate masked project ID and store mapping
          const maskedProjectId = generateMaskedProjectId(projectResponse.data.id);
          storeMaskedProjectIdMapping(maskedProjectId, projectResponse.data.id);
          
          // Return project data with masked ID for UI
          return {
            ...projectResponse.data,
            maskedId: maskedProjectId
          };
        }
      }
      
      // Handle different error status codes
      if (response.status === 404) {
        throw new Error('Session not found');
      } else if (response.status === 403) {
        throw new Error('Session expired or invalid');
      } else {
        throw new Error('Failed to create project');
      }
    } catch (error) {
      console.error('Error creating project:', error);
      throw error;
    }
  };

  const updateGuestProject = async (projectId: string, projectData: { name: string; teachable_machine_link?: string }) => {
    try {
      // Get session ID from localStorage
      const sessionId = localStorage.getItem('neural_playground_session_id');
      if (!sessionId) {
        throw new Error('No session found');
      }

      // If it's a masked ID, get the real project ID
      let realProjectId = projectId;
      if (isMaskedProjectId(projectId)) {
        const actualId = getProjectIdFromMaskedId(projectId);
        if (actualId) {
          realProjectId = actualId;
        }
      }

      const payload = {
        name: projectData.name,
        teachable_machine_link: projectData.teachable_machine_link || undefined
      };

      const response = await fetch(`${config.apiBaseUrl}/api/guests/session/${sessionId}/projects/${realProjectId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        const projectResponse = await response.json();
        if (projectResponse.success) {
          return projectResponse.data;
        }
      }
      
      // Handle different error status codes
      if (response.status === 404) {
        throw new Error('Project or session not found');
      } else if (response.status === 403) {
        throw new Error('Session expired or invalid');
      } else {
        throw new Error('Failed to update project');
      }
    } catch (error) {
      console.error('Error updating project:', error);
      throw error;
    }
  };

  // Debounced validation function
  const debouncedValidateUrl = (url: string) => {
    // Clear existing timeout
    if (validationTimeout) {
      clearTimeout(validationTimeout);
    }
    
    // Only validate if there's a URL and it looks like a Teachable Machine URL
    if (url.trim() && url.includes('teachablemachine.withgoogle.com/models/')) {
      const timeout = setTimeout(async () => {
        setUrlValidation({ isValidating: true, isValid: null, error: null });
        
        const isValid = await validateTeachableMachineUrl(url);
        setUrlValidation({ 
          isValidating: false, 
          isValid, 
          error: isValid ? null : 'Invalid Teachable Machine URL. Please enter a valid URL.' 
        });
      }, 1000); // 1 second delay
      
      setValidationTimeout(timeout);
    } else if (url.trim()) {
      // If it's not a Teachable Machine URL format, show error immediately
      setUrlValidation({ 
        isValidating: false, 
        isValid: false, 
        error: 'Please enter a valid Teachable Machine URL (e.g., https://teachablemachine.withgoogle.com/models/9ofJResGz/)' 
      });
    } else {
      // Empty URL, reset validation
      setUrlValidation({ isValidating: false, isValid: null, error: null });
    }
  };

  // Validate Teachable Machine URL
  const validateTeachableMachineUrl = async (url: string): Promise<boolean> => {
    console.log('Validating URL:', url);
    
    if (!url || !url.trim()) {
      console.log('No URL provided');
      return false;
    }

    // Normalize URL - add https:// if missing
    let normalizedUrl = url.trim();
    if (!normalizedUrl.startsWith('http://') && !normalizedUrl.startsWith('https://')) {
      normalizedUrl = 'https://' + normalizedUrl;
    }

    // Check if it's a valid Teachable Machine URL format
    if (!normalizedUrl.includes('teachablemachine.withgoogle.com/models/')) {
      console.log('Invalid Teachable Machine URL format - missing teachablemachine.withgoogle.com/models/');
      return false;
    }

    // Check if URL has a proper model ID (should have something after /models/)
    const modelIdMatch = normalizedUrl.match(/teachablemachine\.withgoogle\.com\/models\/([^\/]+)/);
    if (!modelIdMatch || !modelIdMatch[1] || modelIdMatch[1].length < 3) {
      console.log('Invalid Teachable Machine URL format - missing or invalid model ID');
      return false;
    }

    // Ensure URL ends with /
    if (!normalizedUrl.endsWith('/')) {
      normalizedUrl += '/';
    }

    // Check if model.json exists
    const modelUrl = normalizedUrl + 'model.json';
    console.log('Checking model URL:', modelUrl);
    
    try {
      const response = await fetch(modelUrl, { 
        method: 'HEAD',
        mode: 'cors'
      });
      console.log('Response status:', response.status, 'OK:', response.ok);
      return response.ok;
    } catch (error) {
      console.error('Error validating Teachable Machine URL:', error);
      return false;
    }
  };

  const getProjectModelStatus = async (projectId: string): Promise<'available' | 'unavailable'> => {
    try {
      // Get session ID from localStorage
      const sessionId = localStorage.getItem('neural_playground_session_id');
      if (!sessionId) {
        console.log('❌ No session ID found in localStorage');
        return 'unavailable';
      }

      // If it's a masked ID, get the real project ID
      let realProjectId = projectId;
      if (isMaskedProjectId(projectId)) {
        const actualId = getProjectIdFromMaskedId(projectId);
        if (actualId) {
          realProjectId = actualId;
        }
      }

      console.log(`🔍 Checking training status for project: ${projectId} (real: ${realProjectId})`);
      const response = await fetch(`${config.apiBaseUrl}/api/guests/session/${sessionId}/projects/${realProjectId}/train`);
      
      if (response.ok) {
        const trainingStatusResponse = await response.json();
        console.log('📊 Training status API response:', JSON.stringify(trainingStatusResponse, null, 2));
        
        if (trainingStatusResponse.success) {
          const projectStatus = trainingStatusResponse.projectStatus;
          const currentJob = trainingStatusResponse.currentJob;
          
          console.log('📋 Training status analysis:');
          console.log('- Project Status:', projectStatus);
          console.log('- Current Job:', currentJob);
          
          // Check if project is trained
          if (projectStatus === 'trained') {
            console.log('✅ Project is trained - model should be available');
            return 'available';
          } else if (projectStatus === 'training' && currentJob && currentJob.status === 'ready') {
            console.log('✅ Training job completed - model should be available');
            return 'available';
          } else {
            console.log('❌ Project not trained yet');
            console.log('- Project Status:', projectStatus);
            console.log('- Job Status:', currentJob?.status);
            return 'unavailable';
          }
        } else {
          console.log('❌ Training status API returned success: false');
        }
      } else {
        console.error('❌ Training status API request failed:', response.status, response.statusText);
        const errorText = await response.text();
        console.error('Error response:', errorText);
      }
      
      return 'unavailable';
    } catch (error) {
      console.error('❌ Error getting training status:', error);
      return 'unavailable';
    }
  };



  const handleCreateProject = () => {
    setCurrentSection('new-project');
    // Reset validation state when creating new project
    setUrlValidation({ isValidating: false, isValid: null, error: null });
    // Update URL hash
    window.location.hash = '#new-project';
  };

  const handleEditProject = (project: Project) => {
    setEditingProject(project);
    setProjectName(project.name);
    setProjectType(project.type);
    setTeachableLink(project.teachable_machine_link || '');
    // Reset validation state when editing project
    setUrlValidation({ isValidating: false, isValid: null, error: null });
    setCurrentSection('edit-project');
    // Update URL hash
    window.location.hash = '#edit-project';
  };

  const handleFormSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (projectName.trim() && projectType) {
      setIsCreatingProject(true);
      
      // Validate Teachable Machine URL if required
      if (projectType === 'image-recognition-teachable-machine' || projectType === 'pose-recognition-teachable-machine') {
        if (!teachableLink || !teachableLink.trim()) {
          alert('Teachable Machine link is required for this project type.');
          setIsCreatingProject(false);
          return;
        }
        console.log('Validating Teachable Machine URL...');
        setUrlValidation({ isValidating: true, isValid: null, error: null });
        
        const isValid = await validateTeachableMachineUrl(teachableLink);
        console.log('Validation result:', isValid);
        
        if (!isValid) {
          setUrlValidation({ 
            isValidating: false, 
            isValid: false, 
            error: 'Invalid Teachable Machine URL. Please enter a valid URL.' 
          });
          alert('Invalid Teachable Machine URL. Please enter a valid URL.');
          setIsCreatingProject(false);
          return;
        } else {
          setUrlValidation({ 
            isValidating: false, 
            isValid: true, 
            error: null 
          });
        }
      }
      
      try {
        const newProject = await createGuestProject({
          name: projectName.trim(),
          type: projectType,
          description: '',
          teachable_machine_link: (projectType === 'image-recognition-teachable-machine' || projectType === 'pose-recognition-teachable-machine') ? teachableLink : undefined
        });
        
        console.log('Created project:', newProject);
        
        // If it's a teachable machine project, open Scratch editor
        if ((projectType === 'image-recognition-teachable-machine' || projectType === 'pose-recognition-teachable-machine') && newProject.id) {
          const scratchUrl = `${config.scratchEditor.gui}?sessionId=${actualSessionId}&projectId=${newProject.id}&teachableLink=${encodeURIComponent(teachableLink)}`;
          window.open(scratchUrl, '_blank');
        }
        
        // Reset form
        setProjectName('');
        setProjectType('');
        setTeachableLink('');
        
        // Reload projects to get updated list
        if (actualSessionId) {
          setIsLoadingProjects(true);
          await loadGuestProjects(actualSessionId);
        }
        
        // For teachable machine projects, stay on projects list
        if (projectType === 'image-recognition-teachable-machine' || projectType === 'pose-recognition-teachable-machine') {
          setCurrentSection('projects-list');
          window.location.hash = '';
        } else {
          // For other project types, navigate to project details page
          window.location.href = `/projects/${urlParam}/${newProject.maskedId}`;
        }
      } catch (error: unknown) {
        const errorMessage = error instanceof Error ? error.message : 'Failed to create project. Please try again.';
        alert(errorMessage);
        
        // If session-related error, redirect to main page
        if (errorMessage.includes('Session') || errorMessage.includes('session')) {
          window.location.href = '/projects';
        }
      } finally {
        setIsCreatingProject(false);
      }
    }
  };

  const handleUpdateFormSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (projectName.trim() && editingProject) {
      setIsUpdatingProject(true);
      
      // Validate Teachable Machine URL if required
      if ((editingProject.type === 'image-recognition-teachable-machine' || editingProject.type === 'pose-recognition-teachable-machine') && teachableLink) {
        console.log('Validating Teachable Machine URL for update...');
        setUrlValidation({ isValidating: true, isValid: null, error: null });
        
        const isValid = await validateTeachableMachineUrl(teachableLink);
        console.log('Validation result:', isValid);
        
        if (!isValid) {
          setUrlValidation({ 
            isValidating: false, 
            isValid: false, 
            error: 'Invalid Teachable Machine URL. Please enter a valid URL.' 
          });
          alert('Invalid Teachable Machine URL. Please enter a valid URL.');
          setIsUpdatingProject(false);
          return;
        } else {
          setUrlValidation({ 
            isValidating: false, 
            isValid: true, 
            error: null 
          });
        }
      }
      
      try {
        await updateGuestProject(editingProject.maskedId || editingProject.id, {
          name: projectName.trim(),
          teachable_machine_link: (editingProject.type === 'image-recognition-teachable-machine' || editingProject.type === 'pose-recognition-teachable-machine') ? teachableLink : undefined
        });
        
        // Reset form
        setProjectName('');
        setProjectType('');
        setTeachableLink('');
        setEditingProject(null);
        
        // Reload projects to get updated list
        if (actualSessionId) {
          setIsLoadingProjects(true);
          await loadGuestProjects(actualSessionId);
        }
        
        // Return to projects list
        setCurrentSection('projects-list');
        window.location.hash = '';
      } catch (error: unknown) {
        const errorMessage = error instanceof Error ? error.message : 'Failed to update project. Please try again.';
        alert(errorMessage);
        
        // If session-related error, redirect to main page
        if (errorMessage.includes('Session') || errorMessage.includes('session')) {
          window.location.href = '/projects';
        }
      } finally {
        setIsUpdatingProject(false);
      }
    }
  };

  const handleDeleteProject = async (projectId: string) => {
    if (actualSessionId && confirm('Are you sure you want to delete this project?')) {
      try {
        // If it's a masked ID, get the real project ID
        let realProjectId = projectId;
        if (isMaskedProjectId(projectId)) {
          const actualId = getProjectIdFromMaskedId(projectId);
          if (actualId) {
            realProjectId = actualId;
          }
        }

        const response = await fetch(`${config.apiBaseUrl}/api/guests/session/${actualSessionId}/projects/${realProjectId}`, {
          method: 'DELETE',
        });

        if (response.ok) {
          // Reload projects to get updated list
          setIsLoadingProjects(true);
          await loadGuestProjects(actualSessionId);
        } else {
          alert('Failed to delete project. Please try again.');
        }
      } catch (error) {
        console.error('Error deleting project:', error);
        alert('Failed to delete project. Please try again.');
      }
    }
  };

  // const handleExportProject = (projectId: string) => {
  //   const project = projects.find(p => p.id === projectId);
  //   console.log('Exporting project:', project);
  //   // Handle export logic here - could be implemented later with API endpoint
  //   alert('Export functionality will be available soon!');
  // };

  const handleProjectClick = (project: Project) => {
    // For teachable machine and text recognition projects, don't redirect - let the Launch button handle it
    if (project.type === 'image-recognition-teachable-machine' || project.type === 'pose-recognition-teachable-machine' || project.type === 'text-recognition' || project.type === 'image-recognition') {
      return;
    } else {
      // For other project types, navigate to the project-specific page using masked project ID
      const projectId = project.maskedId || project.id;
      window.location.href = `/projects/${urlParam}/${projectId}`;
    }
  };

  const handleLaunchProject = (project: Project) => {
    if (project.type === 'image-recognition-teachable-machine' || project.type === 'pose-recognition-teachable-machine') {
      if (project.teachable_machine_link) {
        const scratchUrl = `${config.scratchEditor.gui}?sessionId=${actualSessionId}&projectId=${project.id}&teachableLink=${encodeURIComponent(project.teachable_machine_link)}`;
        window.open(scratchUrl, '_blank');
      } else {
        // If no teachable machine link, show an alert or redirect to edit the project
        const projectTypeName = project.type === 'image-recognition-teachable-machine' ? 'image recognition' : 'pose recognition';
        alert(`This ${projectTypeName} project needs a Teachable Machine link. Please edit the project to add one.`);
        // Optionally, you could open the edit modal here
        // handleEditProject(project);
      }
    } else if (project.type === 'text-recognition' || project.type === 'image-recognition') {
      // Navigate to the project-specific page for text recognition and image recognition
      const projectId = project.maskedId || project.id;
      window.location.href = `/projects/${urlParam}/${projectId}`;
    }
  };

  const handleBackToProjects = () => {
    // Navigate back to projects list using masked ID
    window.location.href = `/projects/${urlParam}`;
  };

  const handleCancel = () => {
    setCurrentSection('projects-list');
    setProjectName('');
    setProjectType('');
    setTeachableLink('');
    setEditingProject(null);
    // Reset validation state when canceling
    setUrlValidation({ isValidating: false, isValid: null, error: null });
    window.location.hash = '';
  };



  return (
    <div className="min-h-screen bg-[#1c1c1c] text-white">
      {/* Header Component */}
      <Header />

      {/* Main Content */}
      <main className="pt-24 pb-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          {/* Back to Home Button */}
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
          
          {/* Navigation Breadcrumb */}
                      <div className="mb-6 text-lg font-semibold text-white">
              {currentSection === 'projects-list' && (
                <span>Projects List</span>
              )}
              {currentSection === 'new-project' && (
                <span>Projects List → <span className="text-[#dcfc84]">Create New Project</span></span>
              )}
              {currentSection === 'edit-project' && (
                <span>Projects List → <span className="text-[#dcfc84]">Edit Project</span></span>
              )}



            </div>
          {isLoading ? (
            /* Loading State */
            <div className="flex items-center justify-center min-h-[400px]">
              <div className="text-white text-xl">Loading...</div>
            </div>
          ) : !isValidSession ? (
            /* Invalid Session */
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
          ) : (
            /* Valid Session Content */
            <div>
              {currentSection === 'project-details' && selectedProject ? (
            /* ML Project Section */
            <div>
              {/* Project Header with Back Button */}
              <div className="flex items-center mb-12">
                <button
                  onClick={handleBackToProjects}
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
                </button>
                <h1 className="text-3xl md:text-4xl font-semibold text-white text-center flex-1">
                  &ldquo;{selectedProject.name}&rdquo;
                </h1>
              </div>

              {/* ML Action Cards */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl mx-auto">
                {/* Train Card */}
                <div className="bg-[#1c1c1c] border border-[#bc6cd3]/20 rounded-xl p-8 text-center hover:bg-[#bc6cd3]/5 transition-all duration-300">
                  <h2 className="text-2xl md:text-3xl font-bold text-white mb-6">
                    Train
                  </h2>
                  <p className="text-white mb-8 text-sm md:text-base leading-relaxed min-h-[3rem]">
                    Collect examples of what you want the computer to recognise
                  </p>
                                     <button 
                     onClick={() => {
                       const projectId = selectedProject.maskedId || selectedProject.id;
                       window.location.href = `/projects/${urlParam}/${projectId}/train`;
                     }}
                     className="w-full bg-[#dcfc84] hover:bg-[#dcfc84]/90 text-[#1c1c1c] py-3 px-6 rounded-lg font-medium transition-all duration-300"
                   >
                     Train
                   </button>
                </div>

                {/* Learn & Test Card */}
                <div className="bg-[#1c1c1c] border border-[#bc6cd3]/20 rounded-xl p-8 text-center hover:bg-[#bc6cd3]/5 transition-all duration-300">
                  <h2 className="text-2xl md:text-3xl font-bold text-white mb-6">
                    Learn & Test
                  </h2>
                  <p className="text-white mb-8 text-sm md:text-base leading-relaxed min-h-[3rem]">
                    Use the examples to train the computer to recognise text
                  </p>
                  <button className="w-full bg-[#dcfc84] hover:bg-[#dcfc84]/90 text-[#1c1c1c] py-3 px-6 rounded-lg font-medium transition-all duration-300">
                    Learn & Test
                  </button>
                </div>

                {/* Make Card */}
                <div className="bg-[#1c1c1c] border border-[#bc6cd3]/20 rounded-xl p-8 text-center hover:bg-[#bc6cd3]/5 transition-all duration-300">
                  <h2 className="text-2xl md:text-3xl font-bold text-white mb-6">
                    Make
                  </h2>
                  <p className="text-white mb-8 text-sm md:text-base leading-relaxed min-h-[3rem]">
                    Use the machine learning model you&apos;ve trained to make a game or app, in Scratch, Python, or EduBlocks
                  </p>
                  <button className="w-full bg-[#dcfc84] hover:bg-[#dcfc84]/90 text-[#1c1c1c] py-3 px-6 rounded-lg font-medium transition-all duration-300">
                    Make
                  </button>
                </div>
              </div>
            </div>

          ) : currentSection === 'projects-list' && isLoadingProjects ? (
            /* Loading Projects State */
            <div className="max-w-4xl mx-auto text-center">
              <div className="flex flex-col items-center justify-center min-h-[400px]">
                {/* Loading Spinner */}
                <div className="mx-auto w-12 h-12 border-4 border-[#bc6cd3]/20 border-t-[#dcfc84] rounded-full animate-spin mb-4"></div>
                <div className="text-white text-xl">Loading projects...</div>
              </div>
            </div>
          ) : currentSection === 'projects-list' && projects.length === 0 ? (
            /* No Projects State */
            <div className="max-w-4xl mx-auto text-center">
              {/* Plus Icon */}
              <div className="mx-auto w-20 h-20 bg-[#bc6cd3]/20 rounded-full flex items-center justify-center mb-8">
                <svg 
                  className="w-10 h-10 text-white" 
                  fill="none" 
                  stroke="currentColor" 
                  viewBox="0 0 24 24"
                >
                  <path 
                    strokeLinecap="round" 
                    strokeLinejoin="round" 
                    strokeWidth={2} 
                    d="M12 6v6m0 0v6m0-6h6m-6 0H6" 
                  />
                </svg>
              </div>

              {/* No Projects Found Title */}
              <h1 className="text-3xl md:text-4xl font-semibold text-white mb-4">
                No Projects Found
              </h1>

              {/* Subtitle */}
              <p className="text-lg text-white mb-12 max-w-2xl mx-auto">
                You haven&apos;t created any projects yet. Start building your AI text recognition model!
              </p>

              {/* Create New Project Button */}
              <button
                onClick={handleCreateProject}
                className="bg-[#dcfc84] text-[#1c1c1c] px-8 py-4 rounded-lg text-lg font-medium hover:scale-105 transition-all duration-300 inline-flex items-center gap-3"
              >
                <svg 
                  className="w-5 h-5" 
                  fill="none" 
                  stroke="currentColor" 
                  viewBox="0 0 24 24"
                >
                  <path 
                    strokeLinecap="round" 
                    strokeLinejoin="round" 
                    strokeWidth={2} 
                    d="M12 6v6m0 0v6m0-6h6m-6 0H6" 
                  />
                </svg>
                Create New Project
              </button>
            </div>
          ) : currentSection === 'projects-list' && projects.length > 0 ? (
            /* Projects Grid */
            <div>
              {/* Header with Add Project Button */}
              <div className="flex justify-end items-center mb-8">
                <button
                  onClick={handleCreateProject}
                  className="bg-[#1c1c1c] border border-[#bc6cd3]/20 text-white px-6 py-3 rounded-lg hover:bg-[#bc6cd3]/10 transition-all duration-300 inline-flex items-center gap-2"
                >
                  <svg 
                    className="w-5 h-5" 
                    fill="none" 
                    stroke="currentColor" 
                    viewBox="0 0 24 24"
                  >
                    <path 
                      strokeLinecap="round" 
                      strokeLinejoin="round" 
                      strokeWidth={2} 
                      d="M12 6v6m0 0v6m0-6h6m-6 0H6" 
                    />
                  </svg>
                  Add a new project
                </button>
              </div>

              

              {/* Projects Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {projects.map((project) => (
                  <div
                    key={project.id}
                    className={`bg-[#1c1c1c] border border-[#bc6cd3]/20 rounded-xl p-6 hover:bg-[#bc6cd3]/5 transition-all duration-300 ${
                      project.type === 'image-recognition-teachable-machine' || project.type === 'text-recognition' || project.type === 'image-recognition' ? '' : 'cursor-pointer'
                    }`}
                    onClick={() => handleProjectClick(project)}
                  >
                    <div className="flex justify-between items-start mb-4">
                      <h3 className="text-xl font-semibold text-white truncate flex-1">
                        {project.name}
                      </h3>
                      <div className="flex gap-2 ml-4">
                        {/* Edit Button - Only for teachable machine projects */}
                        {(project.type === 'image-recognition-teachable-machine' || project.type === 'pose-recognition-teachable-machine') && (
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleEditProject(project);
                            }}
                            className="p-2 text-white/70 hover:text-white hover:bg-white/10 rounded-lg transition-all duration-300"
                            title="Edit project"
                          >
                            <svg 
                              className="w-5 h-5" 
                              fill="none" 
                              stroke="currentColor" 
                              viewBox="0 0 24 24"
                            >
                              <path 
                                strokeLinecap="round" 
                                strokeLinejoin="round" 
                                strokeWidth={2} 
                                d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" 
                              />
                            </svg>
                          </button>
                        )}
                        {/* Delete Button */}
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDeleteProject(project.maskedId || project.id);
                          }}
                          className="p-2 text-white/70 hover:text-red-400 hover:bg-white/10 rounded-lg transition-all duration-300"
                          title="Delete project"
                        >
                          <svg 
                            className="w-5 h-5" 
                            fill="none" 
                            stroke="currentColor" 
                            viewBox="0 0 24 24"
                          >
                            <path 
                              strokeLinecap="round" 
                              strokeLinejoin="round" 
                              strokeWidth={2} 
                              d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" 
                            />
                          </svg>
                        </button>
                      </div>
                    </div>
                    
                                         <div className="text-white mb-4">
                       <span className="text-sm">Project Type: </span>
                       <span className="text-[#dcfc84] font-medium">
                         {project.type === 'text-recognition' ? 'Text Recognition' : 
                          project.type === 'image-recognition' ? 'Image Recognition' :
                          project.type === 'image-recognition-teachable-machine' ? 'Image Recognition - Teachable Machine' :
                          project.type === 'pose-recognition-teachable-machine' ? 'Pose Recognition - Teachable Machine' :
                          project.type === 'classification' ? 'Classification' :
                          project.type === 'regression' ? 'Regression' :
                          project.type === 'custom' ? 'Custom' :
                          project.type}
                       </span>
                     </div>
                     
                     {/* Model Status - Only show for text recognition and image recognition projects */}
                     {(project.type === 'text-recognition' || project.type === 'image-recognition') && (
                       <div className="text-white mb-4">
                         <span className="text-sm">Model Trained: </span>
                         <span className={`font-medium ${
                           project.modelStatus === 'available' ? 'text-green-400' : 'text-red-400'
                         }`}>
                           {project.modelStatus === 'available' ? 'True' : 'False'}
                         </span>
                       </div>
                     )}
                    
                    {/* Teachable Machine Link - Only show for teachable machine projects */}
                    {(project.type === 'image-recognition-teachable-machine' || project.type === 'pose-recognition-teachable-machine') && project.teachable_machine_link && (
                      <div className="text-white mb-4">
                        <span className="text-sm">Teachable Link: </span>
                        <a 
                          href={project.teachable_machine_link}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-[#dcfc84] font-medium hover:underline break-all"
                          onClick={(e) => e.stopPropagation()}
                        >
                          {(() => {
                            const displayUrl = project.teachable_machine_link.replace(/^https?:\/\//, '');
                            return displayUrl.length > 50 
                              ? `${displayUrl.substring(0, 50)}...` 
                              : displayUrl;
                          })()}
                        </a>
                      </div>
                    )}
                    
                                                              {/* Launch Button and Date Info in Parallel */}
                     <div className={`mt-4 flex items-start justify-between gap-4 ${project.type === 'text-recognition' || project.type === 'image-recognition' ? 'mt-16' : ''}`}>
                       {/* Launch Button - For teachable machine and text recognition projects */}
                       {project.type === 'image-recognition-teachable-machine' || project.type === 'pose-recognition-teachable-machine' || project.type === 'text-recognition' || project.type === 'image-recognition' ? (
                         <button
                           onClick={(e) => {
                             e.stopPropagation();
                             handleLaunchProject(project);
                           }}
                           className="bg-[#dcfc84] hover:bg-[#dcfc84]/90 text-[#1c1c1c] py-1.5 px-3 rounded-lg text-sm font-medium transition-all duration-300 flex-shrink-0 mt-1"
                         >
                           Launch
                         </button>
                       ) : (
                         <div></div>
                       )}
                       
                       {/* Date Information */}
                       <div className="text-right flex-shrink-0">
                         <div className="text-xs text-white/50">
                           Created: {new Date(project.createdAt).toLocaleDateString('en-US')}
                         </div>
                         <div className="text-xs text-white/50 mt-1">
                           Session expires: {guestSession ? new Date(guestSession.expiresAt).toLocaleDateString('en-US') : 'Unknown'}
                         </div>
                       </div>
                     </div>
                  </div>
                ))}
              </div>
            </div>
          ) : currentSection === 'new-project' ? (
            /* Project Creation Form */
            <div className="max-w-md mx-auto">
              <div className="text-center mb-8">
                <h1 className="text-3xl md:text-4xl font-semibold text-white mb-4">
                  Create New Project
                </h1>
                <p className="text-lg text-white">
                  Set up your AI project details
                </p>
              </div>

              <form onSubmit={handleFormSubmit} className="space-y-6">
                {/* Project Name Input */}
                <div>
                  <label htmlFor="projectName" className="block text-sm font-medium text-white mb-2">
                    Project Name
                  </label>
                  <input
                    type="text"
                    id="projectName"
                    value={projectName}
                    onChange={(e) => setProjectName(e.target.value)}
                    placeholder="Enter project name"
                    className="w-full px-4 py-3 bg-[#1c1c1c] border border-[#bc6cd3]/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-[#dcfc84] focus:ring-1 focus:ring-[#dcfc84] transition-all duration-300"
                    required
                  />
                </div>

                {/* Project Type Dropdown */}
                <div>
                  <label htmlFor="projectType" className="block text-sm font-medium text-white mb-2">
                    Project Type
                  </label>
                  <select
                    id="projectType"
                    value={projectType}
                    onChange={(e) => setProjectType(e.target.value)}
                    className="w-full px-4 py-3 bg-[#1c1c1c] border border-[#bc6cd3]/20 rounded-lg text-white focus:outline-none focus:border-[#dcfc84] focus:ring-1 focus:ring-[#dcfc84] transition-all duration-300"
                    required
                  >
                    <option value="" disabled className="bg-[#1c1c1c] text-gray-400">
                      Select Type
                    </option>
                    <option value="text-recognition" className="bg-[#1c1c1c] text-white">
                      Text Recognition
                    </option>
                    <option value="image-recognition" className="bg-[#1c1c1c] text-white">
                      Image Recognition
                    </option>
                    <option value="image-recognition-teachable-machine" className="bg-[#1c1c1c] text-white">
                      Image Recognition - Teachable Machine
                    </option>
                    <option value="pose-recognition-teachable-machine" className="bg-[#1c1c1c] text-white">
                      Pose Recognition - Teachable Machine
                    </option>
                  </select>
                </div>

                {/* Teachable Link Field - Only show for Image Recognition and Pose Recognition */}
                {(projectType === 'image-recognition-teachable-machine' || projectType === 'pose-recognition-teachable-machine') && (
                  <div>
                    <label htmlFor="teachableLink" className="block text-sm font-medium text-white mb-2">
                      Teachable Link
                    </label>
                    <input
                      type="text"
                      id="teachableLink"
                      value={teachableLink}
                      onChange={(e) => {
                        const value = e.target.value;
                        setTeachableLink(value);
                        debouncedValidateUrl(value);
                      }}
                      placeholder="Enter your Teachable Link (e.g., https://teachablemachine.withgoogle.com/models/9ofJResGz/)"
                      className={`w-full px-4 py-3 bg-[#1c1c1c] border rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-1 transition-all duration-300 ${
                        teachableLink.trim() && urlValidation.isValid === false 
                          ? 'border-red-500 focus:border-red-500 focus:ring-red-500' 
                          : teachableLink.trim() && urlValidation.isValid === true 
                          ? 'border-green-500 focus:border-green-500 focus:ring-green-500'
                          : 'border-[#bc6cd3]/20 focus:border-[#dcfc84] focus:ring-[#dcfc84]'
                      }`}
                    />
                    
                    {/* Validation feedback - only show when there's a URL entered */}
                    {teachableLink.trim() && urlValidation.isValidating && (
                      <div className="mt-2 text-sm text-blue-400 flex items-center">
                        <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-blue-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Validating URL...
                      </div>
                    )}
                    
                    {teachableLink.trim() && urlValidation.isValid === true && (
                      <div className="mt-2 text-sm text-green-400 flex items-center">
                        <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                        </svg>
                        Valid Teachable Machine URL
                      </div>
                    )}
                    
                    {teachableLink.trim() && urlValidation.error && (
                      <div className="mt-2 text-sm text-red-400 flex items-center">
                        <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                        </svg>
                        {urlValidation.error}
                      </div>
                    )}
                  </div>
                )}

                {/* Form Buttons */}
                <div className="flex gap-4 pt-4">
                  <button
                    type="button"
                    onClick={handleCancel}
                    className="flex-1 px-6 py-3 border border-[#bc6cd3]/30 text-white rounded-lg hover:bg-[#bc6cd3]/10 transition-all duration-300"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isCreatingProject}
                    className="flex-1 bg-[#dcfc84] text-[#1c1c1c] px-6 py-3 rounded-lg font-medium hover:scale-105 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isCreatingProject ? 'Creating...' : 'Create Project'}
                  </button>
                </div>
              </form>
            </div>
          ) : currentSection === 'edit-project' ? (
            /* Edit Project Form */
            <div className="max-w-md mx-auto">
              <div className="text-center mb-8">
                <h1 className="text-3xl md:text-4xl font-semibold text-white mb-4">
                  Edit Project
                </h1>
                <p className="text-lg text-white">
                  Update your AI project details
                </p>
              </div>

              <form onSubmit={handleUpdateFormSubmit} className="space-y-6">
                {/* Project Name Input */}
                <div>
                  <label htmlFor="editProjectName" className="block text-sm font-medium text-white mb-2">
                    Project Name
                  </label>
                  <input
                    type="text"
                    id="editProjectName"
                    value={projectName}
                    onChange={(e) => setProjectName(e.target.value)}
                    placeholder="Enter project name"
                    className="w-full px-4 py-3 bg-[#1c1c1c] border border-[#bc6cd3]/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-[#dcfc84] focus:ring-1 focus:ring-[#dcfc84] transition-all duration-300"
                    required
                  />
                </div>

                {/* Project Type Dropdown - Disabled */}
                <div>
                  <label htmlFor="editProjectType" className="block text-sm font-medium text-white mb-2">
                    Project Type
                  </label>
                  <select
                    id="editProjectType"
                    value={projectType}
                    disabled
                    className="w-full px-4 py-3 bg-[#1c1c1c] border border-[#bc6cd3]/20 rounded-lg text-white focus:outline-none focus:border-[#dcfc84] focus:ring-1 focus:ring-[#dcfc84] transition-all duration-300 opacity-50 cursor-not-allowed"
                  >
                    <option value="text-recognition" className="bg-[#1c1c1c] text-white">
                      Text Recognition
                    </option>
                    <option value="image-recognition-teachable-machine" className="bg-[#1c1c1c] text-white">
                      Image Recognition - Teachable Machine
                    </option>
                    <option value="pose-recognition-teachable-machine" className="bg-[#1c1c1c] text-white">
                      Pose Recognition - Teachable Machine
                    </option>
                  </select>
                  <p className="text-xs text-white/50 mt-1">Project type cannot be changed</p>
                </div>

                {/* Teachable Link Field - Only show for teachable machine projects */}
                {(projectType === 'image-recognition-teachable-machine' || projectType === 'pose-recognition-teachable-machine') && (
                  <div>
                    <label htmlFor="editTeachableLink" className="block text-sm font-medium text-white mb-2">
                      Teachable Link
                    </label>
                    <input
                      type="text"
                      id="editTeachableLink"
                      value={teachableLink}
                      onChange={(e) => {
                        const value = e.target.value;
                        setTeachableLink(value);
                        debouncedValidateUrl(value);
                      }}
                      placeholder="Enter your Teachable Link (e.g., https://teachablemachine.withgoogle.com/models/9ofJResGz/)"
                      className={`w-full px-4 py-3 bg-[#1c1c1c] border rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-1 transition-all duration-300 ${
                        teachableLink.trim() && urlValidation.isValid === false 
                          ? 'border-red-500 focus:border-red-500 focus:ring-red-500' 
                          : teachableLink.trim() && urlValidation.isValid === true 
                          ? 'border-green-500 focus:border-green-500 focus:ring-green-500'
                          : 'border-[#bc6cd3]/20 focus:border-[#dcfc84] focus:ring-[#dcfc84]'
                      }`}
                    />
                    
                    {/* Validation feedback - only show when there's a URL entered */}
                    {teachableLink.trim() && urlValidation.isValidating && (
                      <div className="mt-2 text-sm text-blue-400 flex items-center">
                        <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-blue-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Validating URL...
                      </div>
                    )}
                    
                    {teachableLink.trim() && urlValidation.isValid === true && (
                      <div className="mt-2 text-sm text-green-400 flex items-center">
                        <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                        </svg>
                        Valid Teachable Machine URL
                      </div>
                    )}
                    
                    {teachableLink.trim() && urlValidation.error && (
                      <div className="mt-2 text-sm text-red-400 flex items-center">
                        <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                        </svg>
                        {urlValidation.error}
                      </div>
                    )}
                  </div>
                )}

                {/* Form Buttons */}
                <div className="flex gap-4 pt-4">
                  <button
                    type="button"
                    onClick={handleCancel}
                    className="flex-1 px-6 py-3 border border-[#bc6cd3]/30 text-white rounded-lg hover:bg-[#bc6cd3]/10 transition-all duration-300"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isUpdatingProject}
                    className="flex-1 bg-[#dcfc84] text-[#1c1c1c] px-6 py-3 rounded-lg font-medium hover:scale-105 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isUpdatingProject ? 'Updating...' : 'Update Project'}
                  </button>
                </div>
              </form>
            </div>
          ) : null}
            </div>
          )}
        </div>
      </main>


    </div>
  );
}

// Main component that handles user sessions and project management
// Route: /projects/[userId] - where userId is the temporary 96-hour session ID
export default function ProjectPage() {
  return <CreateProjectPage />;
}
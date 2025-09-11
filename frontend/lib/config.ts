// Configuration for the Neural Playground frontend - Updated for local development
export const config = {
  // Backend API base URL
  apiBaseUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080', // Backend running on 8080
  
  // Scratch Editor URLs
  scratchEditor: {
    gui: process.env.NEXT_PUBLIC_SCRATCH_EDITOR_URL || 'http://localhost:8601',
    vm: process.env.NEXT_PUBLIC_SCRATCH_VM_URL || 'http://localhost:8602',
  },
  
  // API endpoints
  api: {
    guests: {
      session: '/api/guests/session',
      sessionById: (sessionId: string) => `/api/guests/session/${sessionId}`,
      deleteSession: (sessionId: string) => `/api/guests/session/${sessionId}`,
      projectById: (sessionId: string, projectId: string) => `/api/guests/session/${sessionId}/projects/${projectId}`,
      examples: (sessionId: string, projectId: string) => `/api/guests/session/${sessionId}/projects/${projectId}/examples`,
      images: (sessionId: string, projectId: string) => `/api/guests/session/${sessionId}/projects/${projectId}/images`,
      trainModel: (sessionId: string, projectId: string) => `/api/guests/session/${sessionId}/projects/${projectId}/train`,
      trainingStatus: (sessionId: string, projectId: string) => `/api/guests/session/${sessionId}/projects/${projectId}/train`,
      predict: (sessionId: string, projectId: string) => `/api/guests/session/${sessionId}/projects/${projectId}/predict`,
      deleteModel: (projectId: string) => `/api/guests/projects/${projectId}/model`,
      deleteExamplesByLabel: (sessionId: string, projectId: string, label: string) => `/api/guests/projects/${projectId}/examples/${label}`,
      deleteSpecificExample: (sessionId: string, projectId: string, label: string, exampleIndex: number) => `/api/guests/projects/${projectId}/examples/${label}/${exampleIndex}`,
      deleteLabel: (sessionId: string, projectId: string, label: string) => `/api/guests/projects/${projectId}/labels/${label}`,
      deleteEmptyLabel: (sessionId: string, projectId: string, label: string) => `/api/guests/projects/${projectId}/labels/${label}/empty`,
    },
  },
} as const;

export default config;

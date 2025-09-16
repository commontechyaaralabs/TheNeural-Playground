// Configuration for the Neural Playground frontend - Updated for local development
export const config = {
  // Backend API base URL
  apiBaseUrl: process.env.NEXT_PUBLIC_API_URL || 'https://playgroundai-backend-uaaur7no2a-uc.a.run.app', // Backend running on Cloud Run
  
  // Scratch Editor URLs
  scratchEditor: {
    gui: process.env.NEXT_PUBLIC_SCRATCH_EDITOR_URL || 'https://scratch-editor-uaaur7no2a-uc.a.run.app',
    vm: process.env.NEXT_PUBLIC_SCRATCH_VM_URL || 'https://scratch-editor-uaaur7no2a-uc.a.run.app',
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
      uploadImage: (sessionId: string, projectId: string) => `/api/guests/session/${sessionId}/projects/${projectId}/images`,
      trainModel: (sessionId: string, projectId: string) => `/api/guests/session/${sessionId}/projects/${projectId}/train`,
      trainingStatus: (sessionId: string, projectId: string) => `/api/guests/session/${sessionId}/projects/${projectId}/train`,
      predict: (sessionId: string, projectId: string) => `/api/guests/session/${sessionId}/projects/${projectId}/predict`,
      deleteModel: (projectId: string) => `/api/guests/projects/${projectId}/model`,
      deleteExamplesByLabel: (sessionId: string, projectId: string, label: string) => `/api/guests/projects/${projectId}/examples/${label}`,
      deleteSpecificExample: (sessionId: string, projectId: string, label: string, exampleIndex: number) => `/api/guests/projects/${projectId}/examples/${label}/${exampleIndex}`,
      deleteLabel: (sessionId: string, projectId: string, label: string) => `/api/guests/projects/${projectId}/labels/${label}`,
      deleteEmptyLabel: (sessionId: string, projectId: string, label: string) => `/api/guests/projects/${projectId}/labels/${label}/empty`,
      // Image delete endpoints
      deleteImageExamplesByLabel: (sessionId: string, projectId: string, label: string) => `/api/guests/session/${sessionId}/projects/${projectId}/images/${label}`,
      deleteSpecificImageExample: (sessionId: string, projectId: string, label: string, exampleIndex: number) => `/api/guests/session/${sessionId}/projects/${projectId}/images/${label}/${exampleIndex}`,
      deleteImageLabel: (sessionId: string, projectId: string, label: string) => `/api/guests/session/${sessionId}/projects/${projectId}/images/labels/${label}`,
      deleteEmptyImageLabel: (sessionId: string, projectId: string, label: string) => `/api/guests/session/${sessionId}/projects/${projectId}/images/labels/${label}/empty`,
    },
  },
} as const;

export default config;

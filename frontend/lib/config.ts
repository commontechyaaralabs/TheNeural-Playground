// Configuration for the Neural Playground frontend - Updated for local development
export const config = {
  // Backend API base URL
  apiBaseUrl: process.env.NEXT_PUBLIC_API_URL || 'https://playground-backend-v2-uaaur7no2a-uc.a.run.app',
  
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
    agents: {
      create: '/agent/create',
      list: (sessionId: string) => `/agent?session_id=${sessionId}`,
      delete: (agentId: string, sessionId: string) => `/agent/${agentId}?session_id=${sessionId}`,
      chat: '/chat',
      chatTeach: '/chat/teach',
      chatHistory: (agentId: string, sessionId: string) => `/chat/history?agent_id=${agentId}&session_id=${sessionId}`,
      clearChatHistory: (agentId: string, sessionId: string) => `/chat/history?agent_id=${agentId}&session_id=${sessionId}`,
      persona: {
        get: (agentId: string) => `/agent/${agentId}/persona`,
        update: (agentId: string) => `/agent/${agentId}/persona`,
      },
      settings: {
        get: (agentId: string) => `/agent/${agentId}/settings`,
        update: (agentId: string) => `/agent/${agentId}/settings`,
      },
      knowledge: {
        text: '/kb/text',
        file: '/kb/file',
        link: '/kb/link',
        qna: '/kb/qna',
        list: (agentId: string, kbType?: string) => `/kb/list?agent_id=${agentId}${kbType ? `&kb_type=${kbType}` : ''}`,
        get: (knowledgeId: string) => `/kb/${knowledgeId}`,
        update: (knowledgeId: string) => `/kb/${knowledgeId}`,
        delete: (knowledgeId: string) => `/kb/${knowledgeId}`,
        viewFile: (knowledgeId: string) => `/kb/file/view/${knowledgeId}`,
      },
      rules: {
        save: '/rules/save',
        list: (agentId: string) => `/rules?agentId=${agentId}`,
      },
      training: {
        message: '/training/message',
        apply: '/training/apply',
        reject: (changeId: string) => `/training/reject/${changeId}`,
        sessions: (agentId: string) => `/training/sessions?agent_id=${agentId}`,
        history: (agentId: string, sessionId: string) => `/training/history?agent_id=${agentId}&session_id=${sessionId}`,
        restart: (agentId: string, sessionId: string) => `/training/restart?agent_id=${agentId}&session_id=${sessionId}`,
        greeting: (agentId: string) => `/training/greeting?agent_id=${agentId}`,
        initialize: (agentId: string, sessionId: string) => `/training/initialize?agent_id=${agentId}&session_id=${sessionId}`,
        pending: (agentId: string, sessionId: string) => `/training/pending/${agentId}?session_id=${sessionId}`,
        editMessage: (messageId: string) => `/training/message/${messageId}`,
        deleteMessage: (messageId: string) => `/training/message/${messageId}`,
        clearHistory: (agentId: string, sessionId: string) => `/training/history/clear?agent_id=${agentId}&session_id=${sessionId}`,
        // Chat management endpoints (Playground AI-like)
        createChat: '/training/chats',
        getChats: (agentId: string) => `/training/chats?agent_id=${agentId}`,
        getChat: (chatId: string) => `/training/chats/${chatId}`,
        archiveChat: (chatId: string) => `/training/chats/${chatId}/archive`,
        deleteChat: (chatId: string) => `/training/chats/${chatId}`,
      },
    },
  },
} as const;

export default config;

# Chat History Implementation (Playground AI-like)

## Overview
This implementation provides a Playground AI-like chat history system where:
- **Ongoing Chat**: The current active conversation
- **Chat History**: Previous archived conversations (read-only)
- **Chat Management**: Create, archive, and switch between chats

## Database Schema (Firestore)

### Collection: `training_chats`
```json
{
  "chat_id": "CHAT_ABC123",
  "agent_id": "AGENT_XYZ",
  "session_id": "SESSION_123",
  "messages": [
    {
      "message_id": "MSG_001",
      "role": "user|assistant",
      "content": "Message content",
      "created_at": "2025-01-15T10:00:00Z",
      "metadata": {}
    }
  ],
  "created_at": "2025-01-15T10:00:00Z",
  "updated_at": "2025-01-15T10:00:00Z",
  "is_active": true,
  "title": "Optional chat title",
  "message_count": 5
}
```

### Collection: `training_messages` (existing)
Messages are stored here and linked via `session_id`.

## Backend API Endpoints

### 1. Create Chat
```http
POST /training/chats
Content-Type: application/json

{
  "agent_id": "AGENT_XYZ",
  "session_id": "SESSION_123" // Optional
}
```

**Response:**
```json
{
  "success": true,
  "chat": {
    "chat_id": "CHAT_ABC123",
    "agent_id": "AGENT_XYZ",
    "session_id": "SESSION_123",
    "messages": [...],
    "created_at": "2025-01-15T10:00:00Z",
    "updated_at": "2025-01-15T10:00:00Z",
    "is_active": true,
    "title": null,
    "message_count": 1
  }
}
```

### 2. Get All Chats
```http
GET /training/chats?agent_id=AGENT_XYZ
```

**Response:**
```json
{
  "success": true,
  "chats": [
    {
      "chat_id": "CHAT_ABC123",
      "is_active": false,
      "message_count": 10,
      "updated_at": "2025-01-14T10:00:00Z",
      ...
    }
  ],
  "ongoing_chat": {
    "chat_id": "CHAT_XYZ789",
    "is_active": true,
    "message_count": 5,
    ...
  }
}
```

### 3. Get Chat by ID
```http
GET /training/chats/CHAT_ABC123
```

**Response:**
```json
{
  "success": true,
  "chat": {
    "chat_id": "CHAT_ABC123",
    "is_active": false,
    "messages": [...],
    ...
  }
}
```

### 4. Archive Chat
```http
POST /training/chats/CHAT_ABC123/archive
```

**Response:**
```json
{
  "success": true,
  "message": "Chat archived successfully"
}
```

## Frontend Implementation

### State Structure
```typescript
interface ChatState {
  ongoingChat: Chat | null;      // Current active chat
  previousChats: Chat[];         // Archived chats
  viewingChat: Chat | null;       // Currently viewing (ongoing or previous)
  isReadOnly: boolean;            // True when viewing previous chat
}

interface Chat {
  chat_id: string;
  agent_id: string;
  session_id: string;
  messages: ChatMessage[];
  created_at: string;
  updated_at: string;
  is_active: boolean;
  title: string | null;
  message_count: number;
}

interface ChatMessage {
  message_id: string;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
  metadata: Record<string, any>;
}
```

### Component Flow

1. **TeachYourAgent Component**
   - On mount: Load ongoing chat or create new one
   - Display messages from `viewingChat`
   - If `isReadOnly`: Disable input, show "Viewing previous chat" banner
   - "Ongoing Chat" button: Switch back to active chat

2. **ChatHistory Component**
   - Show list of previous chats
   - Show "Ongoing Chat" option at top
   - Clicking a chat: Load it in read-only mode
   - Clicking "Ongoing Chat": Return to active chat

3. **Chat Switching Logic**
   ```typescript
   // Switch to ongoing chat
   const switchToOngoing = () => {
     setViewingChat(ongoingChat);
     setIsReadOnly(false);
   };

   // Switch to previous chat (read-only)
   const switchToPrevious = (chatId: string) => {
     const chat = previousChats.find(c => c.chat_id === chatId);
     if (chat) {
       setViewingChat(chat);
       setIsReadOnly(true);
     }
   };
   ```

### Key Behaviors

1. **Ongoing Chat**
   - Always active (`is_active: true`)
   - Can send messages
   - Persists across page reloads
   - Only one ongoing chat per agent

2. **Previous Chats**
   - Archived (`is_active: false`)
   - Read-only (cannot send messages)
   - Immutable (messages cannot be edited)
   - Sorted by `updated_at` (newest first)

3. **Reset Chat**
   - Archives current ongoing chat
   - Creates new ongoing chat
   - Previous chat remains in history

4. **New Chat**
   - Archives current ongoing chat
   - Creates new ongoing chat
   - Previous chat remains accessible

## Usage Examples

### Example 1: Initialize Chat
```typescript
// On component mount
const initializeChat = async () => {
  const response = await fetch(`${apiBaseUrl}/training/chats`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ agent_id: agentId })
  });
  const data = await response.json();
  setOngoingChat(data.chat);
  setViewingChat(data.chat);
  setIsReadOnly(false);
};
```

### Example 2: Load All Chats
```typescript
const loadChats = async () => {
  const response = await fetch(`${apiBaseUrl}/training/chats?agent_id=${agentId}`);
  const data = await response.json();
  setOngoingChat(data.ongoing_chat);
  setPreviousChats(data.chats);
};
```

### Example 3: Switch to Previous Chat
```typescript
const viewPreviousChat = async (chatId: string) => {
  const response = await fetch(`${apiBaseUrl}/training/chats/${chatId}`);
  const data = await response.json();
  setViewingChat(data.chat);
  setIsReadOnly(true); // Previous chats are read-only
};
```

### Example 4: Reset Chat (Archive + Create New)
```typescript
const resetChat = async () => {
  if (ongoingChat) {
    // Archive current chat
    await fetch(`${apiBaseUrl}/training/chats/${ongoingChat.chat_id}/archive`, {
      method: 'POST'
    });
  }
  
  // Create new chat
  const response = await fetch(`${apiBaseUrl}/training/chats`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ agent_id: agentId })
  });
  const data = await response.json();
  setOngoingChat(data.chat);
  setViewingChat(data.chat);
  setIsReadOnly(false);
  
  // Reload chat list
  await loadChats();
};
```

## Integration Notes

1. **Backward Compatibility**: Existing `training_messages` collection continues to work
2. **Session Management**: `session_id` links messages to chats
3. **Message Storage**: Messages stored in both `training_messages` (for queries) and `chats.messages` (for quick access)
4. **Performance**: Chat documents include message summaries for fast loading

## Next Steps

1. Update `TeachYourAgent.tsx` to use new chat management
2. Update `ChatHistory.tsx` to show chats from new API
3. Add "Ongoing Chat" button in chat history
4. Implement read-only mode for previous chats
5. Update "Reset Chat" to archive current chat


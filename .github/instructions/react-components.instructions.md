---
applyTo: "**/frontend/src/**/*.{tsx,ts}"
---

# React/TypeScript Component Guidelines

When working on the frontend components, please follow these guidelines:

## Component Structure

1. **Use functional components** with TypeScript
2. **Place components** in `frontend/src/components/`
3. **Define types** in `frontend/src/types/api.ts` for API-related types

## Naming Conventions

- Components: `PascalCase` (e.g., `ChatWindow.tsx`, `StatePanel.tsx`)
- Hooks: `useCamelCase` (e.g., `useGameState`)
- Types/Interfaces: `PascalCase` (e.g., `ChatMessage`, `GameState`)

## TypeScript Requirements

1. **Always define prop types** for components:

```typescript
interface ChatWindowProps {
  sessionId: string;
  messages: ChatMessage[];
  onSendMessage: (content: string) => void;
}

export const ChatWindow: React.FC<ChatWindowProps> = ({ 
  sessionId, 
  messages, 
  onSendMessage 
}) => {
  // Component implementation
};
```

2. **Use strict typing** - avoid `any` type
3. **Define API response types** matching backend Pydantic models

## State Management

1. Use **React hooks** (`useState`, `useEffect`, `useCallback`)
2. Keep state close to where it's used
3. Lift state up only when necessary for sharing

## API Integration

Use the centralized API service in `frontend/src/services/api.ts`:

```typescript
import { api } from '../services/api';

// Example usage
const response = await api.createSession(config);
const chatResult = await api.chat(sessionId, roleId, message);
```

## Styling

1. Use CSS modules or inline styles as appropriate
2. Keep styles in `.css` files alongside components
3. Use CSS variables for theming consistency

## Key Components Reference

- `ChatWindow.tsx` - Main chat display and message history
- `ChatInput.tsx` - Message input and character selection
- `StatePanel.tsx` - Game state display
- `StateDiffsPanel.tsx` - State change visualization
- `DiceRoller.tsx` - Dice rolling interface
- `ProfileManager.tsx` - LLM profile management
- `TopNav.tsx` - Navigation and session controls

## Backend API Types

Keep types in sync with backend schemas. Key types:

```typescript
// Match backend ChatResponse
interface ChatResponse {
  content: string | null;
  state_diffs: StateDiff[];
  current_state: GameState;
  tool_calls: ToolCall[];
  role_id: string;
  is_ai: boolean;
  error?: string;
  used_profile_id?: string;
}

// Match backend StateDiff
interface StateDiff {
  path: string;
  operation: string;
  value: any;
  previous_value?: any;
}
```

## Error Handling

1. Display user-friendly error messages
2. Log errors to console for debugging
3. Handle loading states appropriately

## Build and Lint

```bash
cd frontend

# Install dependencies
npm install

# Development server
npm run dev

# Type checking
npx tsc -b --noEmit

# Linting
npm run lint

# Production build
npm run build
```


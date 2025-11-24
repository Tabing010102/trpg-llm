# TRPG-LLM Frontend

A minimal web frontend for the TRPG-LLM system built with React and TypeScript.

## Features

### Top Navigation
- Displays current session ID
- "New Session" button to create a new game session with default configuration

### Chat Window (Left Panel)
- Displays messages in chronological order
- Shows character name, type (GM/Player/NPC), and AI badge
- For AI messages: "Redraw" button to regenerate the last message from that character

### Chat Input (Bottom Left)
- Role selection dropdown (lists all characters)
- Text input area
- Send button to submit messages

### State Panel (Right Top)
- **Game Flow**: Current turn, phase, and active actor
- **Global State**: Key-value pairs from the game state
- **Characters**: Character cards showing HP, SAN, and other stats

### Recent State Changes (Right Middle)
- Displays state diffs from the last action
- Shows path, operation type, new value, and previous value
- Color-coded by operation type (set, add, subtract, etc.)

### Debug Panel (Right Bottom - Collapsible)
- "Refresh Events" button to fetch event history
- Event list showing:
  - Event ID, type, actor, timestamp
  - Number of state diffs
  - "Edit" button to modify event data
- Event editing:
  - JSON editor for event data
  - Saves changes and recomputes state

## Getting Started

### Prerequisites
- Node.js 20+ and npm
- Backend server running on `http://localhost:8000`

### Installation

```bash
cd frontend
npm install
```

### Development

Start the development server:

```bash
npm run dev
```

The application will be available at `http://localhost:5173` (or the next available port).

The dev server is configured to proxy API requests to the backend at `http://localhost:8000`.

### Production Build

Build the application:

```bash
npm run build
```

Preview the production build:

```bash
npm run preview
```

## Project Structure

```
frontend/
├── src/
│   ├── components/          # React components
│   │   ├── TopNav.tsx       # Top navigation bar
│   │   ├── ChatWindow.tsx   # Message display
│   │   ├── ChatInput.tsx    # Message input
│   │   ├── StatePanel.tsx   # Game state display
│   │   ├── StateDiffsPanel.tsx  # Recent state changes
│   │   └── DebugPanel.tsx   # Debug/event history
│   ├── services/            # API client
│   │   └── api.ts           # Backend API service
│   ├── types/               # TypeScript types
│   │   └── api.ts           # API data types
│   ├── App.tsx              # Main application
│   ├── App.css              # Application styles (dark theme)
│   ├── main.tsx             # Entry point
│   └── index.css            # Global styles
├── vite.config.ts           # Vite configuration
├── package.json             # Dependencies
└── tsconfig.json            # TypeScript configuration
```

## API Integration

The frontend connects to the following backend endpoints:

- `POST /sessions` - Create new session
- `GET /sessions/{session_id}` - Get session state
- `GET /sessions/{session_id}/history` - Get event history
- `POST /api/v1/sessions/{session_id}/chat` - Send chat message
- `POST /sessions/{session_id}/redraw` - Redraw AI message
- `POST /sessions/{session_id}/events/{event_id}/edit` - Edit event

## Usage

1. **Start Backend**: Make sure the TRPG-LLM backend is running on port 8000
2. **Start Frontend**: Run `npm run dev`
3. **Create Session**: Click "New Session" to initialize a game
4. **Send Messages**: Select a role and type a message
5. **View State**: Monitor state changes in the right panel
6. **Debug**: Expand debug panel to view and edit events

## Dark Theme

The application uses a developer-friendly dark theme inspired by VS Code:
- Background: `#1e1e1e`
- Monospace font (Consolas/Monaco)
- Color-coded messages by character type
- Syntax highlighting for JSON/code blocks

## Default Configuration

The frontend creates new sessions with a demo configuration:
- **GM**: AI-controlled game master
- **Player1**: Human-controlled player character
- **Location**: Village Square
- **System**: Generic rule system

You can modify the `DEFAULT_CONFIG` in `App.tsx` to use different configurations.

## Error Handling

- API errors are displayed as toast notifications
- Errors auto-dismiss after 5 seconds
- Last valid state is retained on error

## Technologies

- **React 19** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **CSS3** - Styling (no external CSS framework)

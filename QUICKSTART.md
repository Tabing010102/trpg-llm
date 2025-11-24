# Quick Start Guide

This guide will help you get the TRPG-LLM system up and running with the web frontend.

## Prerequisites

- Python 3.8+
- Node.js 20+
- npm 10+
- LLM API key (OpenAI, Anthropic, etc.) - optional for testing without AI

## Step 1: Clone and Setup Backend

```bash
# Clone the repository
git clone https://github.com/Tabing010102/trpg-llm.git
cd trpg-llm

# Install Python dependencies
pip install -r requirements.txt
```

## Step 2: Configure LLM (Optional)

If you want to use AI characters, set up your LLM API key:

```bash
# Create .env file
echo "OPENAI_API_KEY=your-api-key-here" > .env

# Or export as environment variable
export OPENAI_API_KEY=your-api-key-here
```

For testing without AI, you can skip this step. The frontend will work, but AI characters won't respond.

## Step 3: Start Backend Server

```bash
# Start the FastAPI server
python -m trpg_llm.main --host 0.0.0.0 --port 8000

# Server will be available at http://localhost:8000
# API docs available at http://localhost:8000/docs
```

You should see output like:
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

## Step 4: Start Frontend (New Terminal)

Open a new terminal window:

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies (first time only)
npm install

# Start development server
npm run dev
```

You should see:
```
ROLLDOWN-VITE v7.2.5  ready in 185 ms

➜  Local:   http://localhost:5173/
➜  Network: http://10.x.x.x:5173/
```

## Step 5: Open Browser

1. Open your browser to `http://localhost:5173`
2. Click the **"New Session"** button
3. You should see:
   - Session ID displayed at the top
   - Character stats in the right panel (Hero with HP: 20, level: 1)
   - Global state showing location: "Village Square"

## Step 6: Send Your First Message

1. The role selector should automatically select "Hero (player)"
2. Type a message in the text box, for example:
   ```
   Hello! I'm looking for an adventure. What can I do in the village?
   ```
3. Click **"Send"**
4. Your message will appear in the chat window

## Step 7: Explore Features

### View State Changes
- After any action, check the "Recent State Changes" panel
- It shows what changed (path, operation, value)

### View Event History
1. Click "▶ Debug Panel" to expand it
2. Click "🔄 Refresh Events"
3. See all events (game_start, message, etc.)
4. Click "✏️ Edit" on any event to modify its data

### Test AI Redraw (if configured)
- If you have an AI message in chat (from Game Master)
- Click the "🔄 Redraw" button below the message
- The AI will regenerate its response

## Troubleshooting

### Backend won't start
- Check if port 8000 is already in use
- Make sure all Python dependencies are installed: `pip install -r requirements.txt`

### Frontend won't connect to backend
- Make sure backend is running on port 8000
- Check browser console for errors (F12)
- Verify proxy settings in `frontend/vite.config.ts`

### "Session created successfully!" but no state
- Check backend logs for errors
- Verify the configuration in `frontend/src/App.tsx` (DEFAULT_CONFIG)

### AI characters don't respond
- Set up your LLM API key (see Step 2)
- Check backend logs for API errors
- Verify your API key has credits/quota

### Cannot send messages
- Make sure a session is created (session ID shown at top)
- Select a role from the dropdown
- Type some text in the input field

## Next Steps

1. **Create custom games**: Edit `configs/simple_game.json` or `configs/coc_example.yaml`
2. **Explore the API**: Visit `http://localhost:8000/docs` for interactive API documentation
3. **Read the docs**: Check `README.md` and `frontend/README.md` for more details
4. **Join the community**: Report issues or contribute on GitHub

## Development Tips

### Hot Reload
- Backend: Use `--reload` flag: `python -m trpg_llm.main --reload`
- Frontend: Vite has hot reload by default

### View Backend Logs
- All requests and errors are logged to the terminal
- Look for INFO and ERROR messages

### Inspect Network Requests
- Press F12 in browser
- Go to Network tab
- See all API calls and responses

### Build for Production

Backend:
```bash
# Use production ASGI server
pip install gunicorn
gunicorn trpg_llm.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker
```

Frontend:
```bash
cd frontend
npm run build
npm run preview  # Test production build
```

## Common Use Cases

### Running a Solo Game
1. Create session with AI GM
2. Control all player characters yourself
3. Use chat to drive the narrative

### Testing Game Logic
1. Send messages and actions
2. View state changes in real-time
3. Edit events to test different scenarios
4. Use Debug Panel to track event history

### Debugging State Issues
1. Expand Debug Panel
2. Refresh Events to see complete history
3. Edit problematic events
4. Watch state recompute automatically

## Support

For issues, questions, or contributions:
- GitHub Issues: https://github.com/Tabing010102/trpg-llm/issues
- Documentation: Check README.md files
- API Docs: http://localhost:8000/docs (when server is running)

Happy gaming! 🎲

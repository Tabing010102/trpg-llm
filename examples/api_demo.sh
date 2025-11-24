#!/bin/bash
# API Demo Script for TRPG-LLM
# This script demonstrates the REST API functionality

set -e

API_URL="http://localhost:8000"
BOLD='\033[1m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BOLD}TRPG-LLM API Demo${NC}\n"

# Check if server is running
echo -e "${YELLOW}Checking server health...${NC}"
curl -s "$API_URL/" | python -m json.tool
echo ""

# Create a game session
echo -e "${YELLOW}Creating game session...${NC}"
SESSION_RESPONSE=$(curl -s -X POST "$API_URL/sessions" \
  -H "Content-Type: application/json" \
  -d '{
    "config": {
      "name": "Demo Adventure",
      "rule_system": "generic",
      "description": "API demo game",
      "characters": {
        "player1": {
          "id": "player1",
          "name": "Adventurer",
          "type": "player",
          "control": "human",
          "attributes": {"strength": 15},
          "state": {"hp": 30}
        },
        "gm": {
          "id": "gm",
          "name": "GM",
          "type": "gm",
          "control": "human"
        }
      },
      "llm_config": {"default_model": "gpt-3.5-turbo"},
      "workflow": {"turn_order": ["gm", "player1"]},
      "tools": [],
      "initial_state": {"location": "Forest"}
    }
  }')

SESSION_ID=$(echo "$SESSION_RESPONSE" | python -c "import sys, json; print(json.load(sys.stdin)['session_id'])")
echo -e "${GREEN}Session created: $SESSION_ID${NC}\n"

# Roll dice
echo -e "${YELLOW}Rolling 1d20+3 for initiative...${NC}"
DICE_RESULT=$(curl -s -X POST "$API_URL/sessions/$SESSION_ID/dice" \
  -H "Content-Type: application/json" \
  -d '{
    "notation": "1d20+3",
    "character_id": "player1",
    "reason": "Initiative"
  }' | python -c "import sys, json; r = json.load(sys.stdin)['result']; print(f\"Roll: {r['rolls'][0]}, Modifier: {r['modifier']}, Total: {r['final_result']}\")")
echo "$DICE_RESULT"
echo ""

# Add a message
echo -e "${YELLOW}GM narrates...${NC}"
curl -s -X POST "$API_URL/sessions/$SESSION_ID/messages" \
  -H "Content-Type: application/json" \
  -d '{
    "sender_id": "gm",
    "content": "A wild goblin appears!",
    "message_type": "narration"
  }' > /dev/null
echo "Message added"
echo ""

# Perform an action
echo -e "${YELLOW}Player attacks...${NC}"
curl -s -X POST "$API_URL/sessions/$SESSION_ID/actions" \
  -H "Content-Type: application/json" \
  -d '{
    "actor_id": "player1",
    "action_type": "attack",
    "data": {"target": "goblin"}
  }' > /dev/null
echo "Action recorded"
echo ""

# Roll attack damage
echo -e "${YELLOW}Rolling 1d6+2 for damage...${NC}"
curl -s -X POST "$API_URL/sessions/$SESSION_ID/dice" \
  -H "Content-Type: application/json" \
  -d '{
    "notation": "1d6+2",
    "character_id": "player1",
    "reason": "Attack damage"
  }' | python -c "import sys, json; r = json.load(sys.stdin)['result']; print(f\"Damage: {r['final_result']}\")"
echo ""

# Update player HP (goblin counter-attacks)
echo -e "${YELLOW}Goblin counter-attacks! Updating player HP...${NC}"
curl -s -X POST "$API_URL/sessions/$SESSION_ID/state" \
  -H "Content-Type: application/json" \
  -d '{
    "actor_id": "gm",
    "path": "characters.player1.state.hp",
    "operation": "subtract",
    "value": 5
  }' | python -c "import sys, json; hp = json.load(sys.stdin)['state']['characters']['player1']['state']['hp']; print(f\"Player HP: {hp}\")"
echo ""

# Get current state
echo -e "${YELLOW}Current game state:${NC}"
curl -s "$API_URL/sessions/$SESSION_ID" | python -c "
import sys, json
state = json.load(sys.stdin)['state']
print(f\"Location: {state['state']['location']}\")
print(f\"Turn: {state['current_turn']}\")
print(f\"Total messages: {len(state['messages'])}\")
"
echo ""

# Get event history
echo -e "${YELLOW}Event history:${NC}"
curl -s "$API_URL/sessions/$SESSION_ID/history" | python -c "
import sys, json
events = json.load(sys.stdin)['events']
print(f\"Total events: {len(events)}\")
for e in events:
    print(f\"  - {e['type']} (id: {e['id'][:8]}...)\")
"
echo ""

# Demonstrate rollback
echo -e "${YELLOW}Rolling back to event 2...${NC}"
EVENT_ID=$(curl -s "$API_URL/sessions/$SESSION_ID/history" | python -c "import sys, json; print(json.load(sys.stdin)['events'][1]['id'])")
curl -s -X POST "$API_URL/sessions/$SESSION_ID/rollback" \
  -H "Content-Type: application/json" \
  -d "{\"event_id\": \"$EVENT_ID\"}" | python -c "
import sys, json
state = json.load(sys.stdin)['state']
print(f\"Player HP after rollback: {state['characters']['player1']['state']['hp']}\")
"
echo ""

# Delete session
echo -e "${YELLOW}Cleaning up: deleting session...${NC}"
curl -s -X DELETE "$API_URL/sessions/$SESSION_ID" | python -m json.tool
echo ""

echo -e "${GREEN}${BOLD}Demo completed!${NC}"

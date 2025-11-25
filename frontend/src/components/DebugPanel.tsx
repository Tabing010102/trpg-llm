import React, { useState } from 'react';
import type { Event } from '../types/api';

interface DebugPanelProps {
  sessionId: string | null;
  events: Event[];
  onRefreshEvents: () => void;
  onEditEvent: (eventId: string, newData: Record<string, unknown>) => void;
  onRollbackToEvent: (eventId: string) => void;
}

const DebugPanel: React.FC<DebugPanelProps> = ({
  sessionId,
  events,
  onRefreshEvents,
  onEditEvent,
  onRollbackToEvent,
}) => {
  const [expanded, setExpanded] = useState(false);
  const [editingEventId, setEditingEventId] = useState<string | null>(null);
  const [editData, setEditData] = useState('');

  const handleStartEdit = (event: Event) => {
    setEditingEventId(event.id);
    setEditData(JSON.stringify(event.data, null, 2));
  };

  const handleSaveEdit = () => {
    if (!editingEventId) return;
    try {
      const parsedData = JSON.parse(editData);
      onEditEvent(editingEventId, parsedData);
      setEditingEventId(null);
      setEditData('');
    } catch (error) {
      alert('Invalid JSON: ' + (error as Error).message);
    }
  };

  const handleCancelEdit = () => {
    setEditingEventId(null);
    setEditData('');
  };

  const handleRollback = (eventId: string) => {
    if (window.confirm('Are you sure you want to rollback to this event? All events after this will be removed.')) {
      onRollbackToEvent(eventId);
    }
  };

  return (
    <div className="debug-panel">
      <div className="panel-header" onClick={() => setExpanded(!expanded)}>
        <h3>{expanded ? '▼' : '▶'} Debug Panel</h3>
      </div>
      
      {expanded && (
        <div className="panel-content">
          <div className="panel-actions">
            <button
              className="btn btn-small"
              onClick={onRefreshEvents}
              disabled={!sessionId}
            >
              🔄 Refresh Events
            </button>
          </div>

          <div className="events-list">
            <h4>Event History ({events.length})</h4>
            {events.length === 0 ? (
              <p className="text-muted">No events</p>
            ) : (
              <div className="events-table">
                {events.map((event, index) => (
                  <div key={event.id} className="event-row">
                    {editingEventId === event.id ? (
                      <div className="event-edit-form">
                        <div className="edit-header">
                          <strong>Editing Event: {event.id.slice(0, 8)}...</strong>
                          <div>
                            <button className="btn btn-small btn-primary" onClick={handleSaveEdit}>
                              Save
                            </button>
                            <button className="btn btn-small" onClick={handleCancelEdit}>
                              Cancel
                            </button>
                          </div>
                        </div>
                        <textarea
                          value={editData}
                          onChange={(e) => setEditData(e.target.value)}
                          rows={10}
                          className="edit-textarea"
                        />
                      </div>
                    ) : (
                      <>
                        <div className="event-info">
                          <div className="event-id">
                            <strong>#{index + 1}</strong> - {event.id.slice(0, 8)}...
                          </div>
                          <div className="event-type">
                            <strong>Type:</strong> {event.type}
                          </div>
                          {event.actor_id && (
                            <div className="event-actor">
                              <strong>Actor:</strong> {event.actor_id}
                            </div>
                          )}
                          <div className="event-time">
                            <strong>Time:</strong>{' '}
                            {new Date(event.timestamp).toLocaleString()}
                          </div>
                          <div className="event-diffs">
                            <strong>Diffs:</strong> {event.state_diffs.length}
                          </div>
                        </div>
                        <div className="event-actions">
                          <button
                            className="btn btn-small"
                            onClick={() => handleStartEdit(event)}
                            title="Edit event data"
                          >
                            ✏️
                          </button>
                          {index < events.length - 1 && (
                            <button
                              className="btn btn-small btn-warning"
                              onClick={() => handleRollback(event.id)}
                              title="Rollback to this event (removes all events after this)"
                            >
                              ⏪
                            </button>
                          )}
                        </div>
                      </>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default DebugPanel;

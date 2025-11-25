import React, { useState, useRef } from 'react';
import type { LLMProfile } from '../types/api';

interface ProfileManagerProps {
  profiles: LLMProfile[];
  onLoadProfiles: (profiles: LLMProfile[]) => void;
  onAddProfile: (profile: LLMProfile) => void;
  onDeleteProfile: (profileId: string) => void;
  onClose: () => void;
}

const ProfileManager: React.FC<ProfileManagerProps> = ({
  profiles,
  onLoadProfiles,
  onAddProfile,
  onDeleteProfile,
  onClose,
}) => {
  const [error, setError] = useState<string | null>(null);
  const [newProfileJson, setNewProfileJson] = useState('');
  const [showAddForm, setShowAddForm] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      const text = await file.text();
      const data = JSON.parse(text);
      
      // Check if it's an array of profiles or a single profile
      if (Array.isArray(data)) {
        onLoadProfiles(data);
      } else if (data.profiles && Array.isArray(data.profiles)) {
        // Handle { profiles: [...] } format
        onLoadProfiles(data.profiles);
      } else if (data.id) {
        // Single profile
        onLoadProfiles([data]);
      } else {
        throw new Error('Invalid profile format. Expected array of profiles or { profiles: [...] }');
      }
      
      setError(null);
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    } catch (err) {
      setError('Failed to parse file: ' + (err as Error).message);
    }
  };

  const handleAddProfile = () => {
    try {
      const profile = JSON.parse(newProfileJson);
      if (!profile.id) {
        throw new Error("Profile must have an 'id' field");
      }
      onAddProfile(profile);
      setNewProfileJson('');
      setShowAddForm(false);
      setError(null);
    } catch (err) {
      setError('Invalid JSON: ' + (err as Error).message);
    }
  };

  const exampleProfile = JSON.stringify({
    id: 'my-profile',
    provider_type: 'openai',
    model: 'gpt-4',
    temperature: 0.7,
    base_url: 'https://api.openai.com/v1',
    api_key_ref: 'OPENAI_API_KEY'
  }, null, 2);

  return (
    <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal-content profile-manager">
        <div className="modal-header">
          <h2>LLM Profile Manager</h2>
          <button className="btn btn-small" onClick={onClose}>✕</button>
        </div>

        {error && (
          <div className="error-message">{error}</div>
        )}

        <div className="profile-section">
          <h3>Load Profiles from File</h3>
          <p className="hint">Upload a JSON file containing an array of LLM profiles</p>
          <input
            ref={fileInputRef}
            type="file"
            accept=".json"
            onChange={handleFileUpload}
            className="file-input"
          />
        </div>

        <div className="profile-section">
          <div className="section-header">
            <h3>Current Profiles ({profiles.length})</h3>
            <button
              className="btn btn-small btn-primary"
              onClick={() => setShowAddForm(!showAddForm)}
            >
              {showAddForm ? 'Cancel' : '+ Add Profile'}
            </button>
          </div>

          {showAddForm && (
            <div className="add-profile-form">
              <p className="hint">Enter profile JSON:</p>
              <textarea
                value={newProfileJson}
                onChange={(e) => setNewProfileJson(e.target.value)}
                placeholder={exampleProfile}
                rows={8}
                className="profile-textarea"
              />
              <button
                className="btn btn-primary"
                onClick={handleAddProfile}
                disabled={!newProfileJson.trim()}
              >
                Add Profile
              </button>
            </div>
          )}

          {profiles.length === 0 ? (
            <p className="text-muted">No profiles loaded. Upload a JSON file to add profiles.</p>
          ) : (
            <div className="profiles-list">
              {profiles.map((profile) => (
                <div key={profile.id} className="profile-item">
                  <div className="profile-info">
                    <div className="profile-id">{profile.id}</div>
                    <div className="profile-details">
                      <span className="profile-model">{profile.model}</span>
                      <span className="profile-provider">{profile.provider_type}</span>
                      <span className="profile-temp">temp: {profile.temperature}</span>
                    </div>
                  </div>
                  <button
                    className="btn btn-small btn-danger"
                    onClick={() => onDeleteProfile(profile.id)}
                    title="Delete profile"
                  >
                    🗑️
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ProfileManager;

import { useState, useEffect, useRef } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { sendProfileChatMessage, createProfile, getProfile, updateProfile } from '../api/client';
import './CreateProfile.css';

const SENSITIVITY_FIELDS = [
  { key: 'violence',        label: 'Violence',         icon: '⚔️' },
  { key: 'blood_gore',      label: 'Blood / Gore',     icon: '🩸' },
  { key: 'self_harm',       label: 'Self-Harm',        icon: '🩹' },
  { key: 'suicide',         label: 'Suicide',          icon: '⚠️' },
  { key: 'gun_weapon',      label: 'Gun / Weapon',     icon: '🔫' },
  { key: 'abuse',           label: 'Abuse',            icon: '🚫' },
  { key: 'death_grief',     label: 'Death / Grief',    icon: '🕊️' },
  { key: 'sexual_content',  label: 'Sexual Content',   icon: '🔞' },
  { key: 'bullying',        label: 'Bullying',         icon: '😤' },
  { key: 'substance_use',   label: 'Substance Use',    icon: '💊' },
  { key: 'flash_seizure',   label: 'Flash / Seizure',  icon: '⚡' },
  { key: 'loud_sensory',    label: 'Loud / Sensory',   icon: '🔊' },
];

const SENSITIVITY_LABELS = ['Not Sensitive', 'Slightly', 'Moderate', 'Sensitive', 'Very Sensitive'];

const defaultSensitivities = Object.fromEntries(SENSITIVITY_FIELDS.map((f) => [f.key, 3]));

// ─── Edit Form ───────────────────────────────────────────────────────────────

function EditProfileForm({ profileId }) {
  const navigate = useNavigate();
  const [name, setName] = useState('');
  const [age, setAge] = useState('');
  const [sensitivities, setSensitivities] = useState(defaultSensitivities);
  const [calmingStrategy, setCalmingStrategy] = useState('');
  const [additionalDetails, setAdditionalDetails] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    getProfile(profileId).then((res) => {
      const p = res.data;
      setName(p.name);
      setAge(String(p.age));
      setSensitivities({ ...defaultSensitivities, ...p.sensitivities });
      setCalmingStrategy(p.calming_strategy || '');
      setAdditionalDetails(p.additional_details || '');
      setLoading(false);
    }).catch(() => navigate('/'));
  }, [profileId, navigate]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await updateProfile(profileId, {
        name,
        age: parseInt(age),
        sensitivities,
        calming_strategy: calmingStrategy,
        additional_details: additionalDetails,
      });
      navigate('/');
    } catch (err) {
      alert('Failed to update profile. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="form-loading"><div className="spinner" /><p>Loading profile...</p></div>;

  return (
    <div className="create-profile-chat">
      <header className="form-header">
        <h1>Edit Profile</h1>
        <p className="form-subtitle">Update the sensitivity settings for this profile.</p>
      </header>

      <form onSubmit={handleSubmit} className="profile-edit-form">
        <section className="edit-section">
          <h2>Basic Info</h2>
          <div className="edit-field">
            <label htmlFor="name">Name</label>
            <input id="name" type="text" value={name} onChange={(e) => setName(e.target.value)} required maxLength={100} />
          </div>
          <div className="edit-field">
            <label htmlFor="age">Age</label>
            <input id="age" type="number" min={1} max={120} value={age} onChange={(e) => setAge(e.target.value)} required className="age-number-input" />
          </div>
        </section>

        <section className="edit-section">
          <h2>Sensitivities</h2>
          <p className="edit-hint">1 = Not sensitive &nbsp;→&nbsp; 5 = Very sensitive</p>
          <div className="sliders-grid">
            {SENSITIVITY_FIELDS.map((f) => (
              <div key={f.key} className="slider-row">
                <div className="slider-label">
                  <span>{f.icon}</span><span>{f.label}</span>
                </div>
                <div className="slider-control">
                  <input
                    type="range" min={1} max={5} step={1}
                    value={sensitivities[f.key]}
                    onChange={(e) => setSensitivities((prev) => ({ ...prev, [f.key]: parseInt(e.target.value) }))}
                  />
                  <span className={`sensitivity-badge s-${sensitivities[f.key]}`}>
                    {SENSITIVITY_LABELS[sensitivities[f.key] - 1]}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="edit-section">
          <h2>Calming Strategy</h2>
          <div className="edit-field">
            <textarea
              value={calmingStrategy}
              onChange={(e) => setCalmingStrategy(e.target.value)}
              placeholder="e.g. Deep breathing, looking at pictures of puppies..."
              maxLength={500} rows={3}
            />
          </div>
        </section>

        <section className="edit-section">
          <h2>Additional Notes</h2>
          <p className="edit-hint">Context gathered during the initial profile setup.</p>
          <div className="edit-field">
            <textarea
              value={additionalDetails}
              onChange={(e) => setAdditionalDetails(e.target.value)}
              placeholder="No additional details recorded yet."
              maxLength={2000} rows={4}
            />
          </div>
        </section>

        <div className="form-actions">
          <button type="button" className="btn btn-secondary" onClick={() => navigate('/')}>Cancel</button>
          <button type="submit" className="btn btn-primary" disabled={saving || !name.trim() || !age}>
            {saving ? 'Saving...' : 'Update Profile'}
          </button>
        </div>
      </form>
    </div>
  );
}

// ─── Create Chat ──────────────────────────────────────────────────────────────

function CreateProfileChat() {
  const navigate = useNavigate();
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState('');
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [chatComplete, setChatComplete] = useState(false);
  const [finalProfile, setFinalProfile] = useState(null);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    const initChat = async () => {
      setLoading(true);
      try {
        const res = await sendProfileChatMessage([]);
        setMessages([{ role: 'assistant', content: res.data.reply }]);
      } catch {
        setMessages([{ role: 'assistant', content: 'Chat service unavailable. Check backend connection and API keys.' }]);
      } finally {
        setLoading(false);
      }
    };
    initChat();
  }, []);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!inputText.trim() || loading || chatComplete) return;

    const newMessages = [...messages, { role: 'user', content: inputText.trim() }];
    setMessages(newMessages);
    setInputText('');
    setLoading(true);

    try {
      const res = await sendProfileChatMessage(newMessages);
      setMessages((prev) => [...prev, { role: 'assistant', content: res.data.reply }]);
      if (res.data.is_complete && res.data.profile_data) {
        setChatComplete(true);
        setFinalProfile(res.data.profile_data);
      }
    } catch {
      setMessages((prev) => prev.slice(0, -1));
      alert('Failed to send message. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveProfile = async () => {
    if (!finalProfile) return;
    setSaving(true);
    try {
      await createProfile(finalProfile);
      navigate('/');
    } catch {
      alert('Failed to save profile. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="create-profile-chat">
      <header className="form-header">
        <h1>Create Profile</h1>
        <p className="form-subtitle">Chat with our AI assistant to set up your personalized sensitivity profile.</p>
      </header>

      <div className="chat-container">
        <div className="chat-messages">
          {messages.map((msg, idx) => (
            <div key={idx} className={`chat-message ${msg.role}`}>
              <div className="message-bubble">{msg.content}</div>
            </div>
          ))}
          {loading && (
            <div className="chat-message assistant">
              <div className="message-bubble typing-indicator">
                <span className="dot" /><span className="dot" /><span className="dot" />
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {chatComplete ? (
          <div className="chat-complete">
            <h3>Profile Ready!</h3>
            <p>The assistant has collected all the information needed.</p>
            <button className="btn btn-primary" onClick={handleSaveProfile} disabled={saving}>
              {saving ? 'Saving...' : 'Save Profile'}
            </button>
          </div>
        ) : (
          <form className="chat-input-area" onSubmit={handleSend}>
            <input
              type="text" value={inputText} onChange={(e) => setInputText(e.target.value)}
              placeholder="Type your answer here..." disabled={loading} autoFocus
            />
            <button type="submit" className="btn btn-primary" disabled={!inputText.trim() || loading}>Send</button>
          </form>
        )}
      </div>

      {!chatComplete && (
        <div className="form-actions" style={{ marginTop: '1.5rem', justifyContent: 'center' }}>
          <button type="button" className="btn btn-secondary" onClick={() => navigate('/')}>Cancel</button>
        </div>
      )}
    </div>
  );
}

// ─── Root export ─────────────────────────────────────────────────────────────

export default function CreateProfile() {
  const { id } = useParams();
  return id ? <EditProfileForm profileId={id} /> : <CreateProfileChat />;
}

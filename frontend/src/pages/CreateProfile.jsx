import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { createProfile, getProfile, updateProfile } from '../api/client';
import './CreateProfile.css';

const SENSITIVITY_FIELDS = [
  { key: 'violence', label: 'Violence', icon: '⚔️' },
  { key: 'blood_gore', label: 'Blood / Gore', icon: '🩸' },
  { key: 'self_harm', label: 'Self-Harm', icon: '🩹' },
  { key: 'suicide', label: 'Suicide', icon: '⚠️' },
  { key: 'gun_weapon', label: 'Gun / Weapon', icon: '🔫' },
  { key: 'abuse', label: 'Abuse', icon: '🚫' },
  { key: 'death_grief', label: 'Death / Grief', icon: '🕊️' },
  { key: 'sexual_content', label: 'Sexual Content', icon: '🔞' },
  { key: 'bullying', label: 'Bullying', icon: '😤' },
  { key: 'substance_use', label: 'Substance Use', icon: '💊' },
  { key: 'flash_seizure', label: 'Flash / Seizure', icon: '⚡' },
  { key: 'loud_sensory', label: 'Loud / Sensory', icon: '🔊' },
];

const TOLERANCE_LABELS = ['None', 'Low', 'Moderate', 'High', 'Very High'];

const defaultSensitivities = Object.fromEntries(SENSITIVITY_FIELDS.map((f) => [f.key, 3]));

export default function CreateProfile() {
  const { id } = useParams();
  const isEdit = Boolean(id);
  const navigate = useNavigate();

  const [name, setName] = useState('');
  const [age, setAge] = useState('');
  const [sensitivities, setSensitivities] = useState(defaultSensitivities);
  const [calmingStrategy, setCalmingStrategy] = useState('');
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(isEdit);

  useEffect(() => {
    if (isEdit) {
      getProfile(id).then((res) => {
        const p = res.data;
        setName(p.name);
        setAge(String(p.age_band || ''));
        setSensitivities(p.sensitivities);
        setCalmingStrategy(p.calming_strategy || '');
        setLoading(false);
      }).catch(() => {
        navigate('/');
      });
    }
  }, [id, isEdit, navigate]);

  const handleSliderChange = (key, value) => {
    setSensitivities((prev) => ({ ...prev, [key]: parseInt(value) }));
  };



  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);

    const payload = {
      name,
      age_band: age,
      sensitivities,
      calming_strategy: calmingStrategy,
    };

    try {
      // 1. Save profile to Supabase as before
      if (isEdit) {
        await updateProfile(id, payload);
      } else {
        await createProfile(payload);
      }

      // 2. Call recommendation API
      const recResponse = await fetch('http://localhost:8000/api/recommendations', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          child_name: name,
          age_band: age + ' yrs',
          violence: sensitivities.violence,
          blood: sensitivities.blood_gore,
          self_harm: sensitivities.self_harm,
          suicide: sensitivities.suicide,
          gun_weapon: sensitivities.gun_weapon,
          abuse: sensitivities.abuse,
          death_grief: sensitivities.death_grief,
          sexual_content: sensitivities.sexual_content,
          bullying: sensitivities.bullying,
          substance_use: sensitivities.substance_use,
          flash_seizure: sensitivities.flash_seizure,
          loud_sensory: sensitivities.loud_sensory,
          calming_strategy: calmingStrategy,
          reference_film: null,
        })
      });

      const recData = await recResponse.json();

      // 3. Go to recommendations page
      navigate('/recommendations', {
        state: {
          recommendations: recData.recommendations,
          reference_film: recData.reference_film,
          child_name: name,
        }
      });

    } catch (err) {
      console.error('Error:', err);
      alert('Something went wrong. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <div className="form-loading"><div className="spinner" /><p>Loading profile...</p></div>;
  }

  return (
    <div className="create-profile">
      <header className="form-header">
        <h1>{isEdit ? 'Edit Profile' : 'Create Profile'}</h1>
        <p className="form-subtitle">Set up sensitivity preferences for personalized viewing plans.</p>
      </header>

      <form onSubmit={handleSubmit} className="profile-form">
        {/* Basic info */}
        <section className="form-section">
          <h2>Basic Info</h2>
          <div className="field">
            <label htmlFor="name">Name</label>
            <input id="name" type="text" value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Alex" required maxLength={100} />
          </div>
          <div className="field">
            <label htmlFor="age">Age</label>
            <input id="age" type="number" min={1} max={120} value={age} onChange={(e) => setAge(e.target.value)} placeholder="e.g. 12" required className="age-input" />
          </div>
        </section>



        {/* Sensitivity sliders */}
        <section className="form-section">
          <h2>Sensitivity Sliders</h2>
          <p className="section-desc">1 = not sensitive (high tolerance) → 5 = very sensitive (low tolerance)</p>
          <div className="sliders-grid">
            {SENSITIVITY_FIELDS.map((field) => (
              <div key={field.key} className="slider-row">
                <div className="slider-label">
                  <span className="slider-icon">{field.icon}</span>
                  <span>{field.label}</span>
                </div>
                <div className="slider-control">
                  <input type="range" min={1} max={5} step={1} value={sensitivities[field.key]} onChange={(e) => handleSliderChange(field.key, e.target.value)} />
                  <span className={`tolerance-badge t-${sensitivities[field.key]}`}>{TOLERANCE_LABELS[sensitivities[field.key] - 1]}</span>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Calming strategy */}
        <section className="form-section">
          <h2>Calming Strategy</h2>
          <p className="section-desc">Describe what helps calm you down during breaks — breathing exercises, looking at cute animals, listening to music, etc.</p>
          <div className="field">
            <textarea
              id="calmingStrategy"
              value={calmingStrategy}
              onChange={(e) => setCalmingStrategy(e.target.value)}
              placeholder="e.g. Deep breathing with counting to 5, looking at pictures of puppies, listening to calm music, taking a short walk..."
              maxLength={500}
              rows={3}
            />
            <span className="char-count">{calmingStrategy.length}/500</span>
          </div>
        </section>

        <div className="form-actions">
          <button type="button" className="btn btn-secondary" onClick={() => navigate('/')}>Cancel</button>
          <button type="submit" className="btn btn-primary" disabled={saving || !name.trim() || !age}>
            {saving ? 'Saving...' : isEdit ? 'Update Profile' : 'Create Profile'}
          </button>
        </div>
      </form>
    </div>
  );
}

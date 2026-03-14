import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { getProfiles, deleteProfile } from '../api/client';
import './Home.css';

export default function Home() {
  const [profiles, setProfiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    loadProfiles();
  }, []);

  const loadProfiles = async () => {
    try {
      const res = await getProfiles();
      setProfiles(res.data);
    } catch (err) {
      console.error('Failed to load profiles', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id, name) => {
    if (!confirm(`Delete profile for ${name}?`)) return;
    try {
      await deleteProfile(id);
      setProfiles((prev) => prev.filter((p) => p.id !== id));
    } catch (err) {
      console.error('Failed to delete profile', err);
    }
  };

  if (loading) {
    return <div className="home-loading"><div className="spinner" /><p>Loading profiles...</p></div>;
  }

  return (
    <div className="home">
      <main className="home-main">
        <section className="profiles-section">
          <div className="section-header">
            <h2>Profiles</h2>
            <Link to="/profiles/new" className="btn btn-primary">+ New Profile</Link>
          </div>

          {profiles.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">👤</div>
              <h3>No profiles yet</h3>
              <p>Create a profile to get started with personalized viewing plans.</p>
              <Link to="/profiles/new" className="btn btn-primary">Create First Profile</Link>
            </div>
          ) : (
            <div className="profile-grid">
              {profiles.map((profile) => (
                <div key={profile.id} className="profile-card">
                  <div className="profile-card-header">
                    <div className="profile-avatar">{profile.name.charAt(0).toUpperCase()}</div>
                    <div className="profile-info">
                      <h3>{profile.name}</h3>
                      <span className="age-badge">Age {profile.age}</span>
                    </div>
                  </div>
                  {profile.calming_strategy && (
                    <div className="profile-card-meta">
                      <span className="calming-tag">💆 {profile.calming_strategy}</span>
                    </div>
                  )}
                  <div className="profile-card-actions">
                    <button className="btn btn-secondary" onClick={() => navigate(`/profiles/${profile.id}/edit`)}>Edit</button>
                    <button className="btn btn-ghost" onClick={() => navigate('/movies')}>Browse Movies</button>
                    <button className="btn btn-danger-ghost" onClick={() => handleDelete(profile.id, profile.name)}>Delete</button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      </main>
    </div>
  );
}

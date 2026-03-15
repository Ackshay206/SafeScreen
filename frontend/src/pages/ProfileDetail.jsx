import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { getProfile, getRecommendations } from '../api/client';
import './ProfileDetail.css';

/* ── score ring (copied from Recommendations.jsx) ── */
function ScoreRing({ score }) {
  const pct = Math.round((score ?? 0.5) * 100);
  const r   = 20;
  const circ = 2 * Math.PI * r;
  const dash = circ * (pct / 100);
  return (
    <div className="score-ring-wrap">
      <svg width={48} height={48} style={{ transform: 'rotate(-90deg)' }}>
        <circle cx={24} cy={24} r={r} fill="none" stroke="var(--surface-2)" strokeWidth={4} />
        <circle
          cx={24} cy={24} r={r} fill="none"
          stroke="var(--accent)" strokeWidth={4}
          strokeDasharray={`${dash} ${circ}`}
          strokeLinecap="round"
          style={{ transition: 'stroke-dasharray 1s ease' }}
        />
      </svg>
      <span className="score-ring-val">{pct}%</span>
    </div>
  );
}

export default function ProfileDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [profile, setProfile] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [recLoading, setRecLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, [id]);

  const loadData = async () => {
    try {
      setLoading(true);
      const res = await getProfile(id);
      const p = res.data;
      setProfile(p);
      setLoading(false);

      // Now fetch recommendations using the sensitivities
      fetchRecommendations(p);
    } catch (err) {
      console.error('Failed to load profile', err);
      navigate('/');
    }
  };

  const fetchRecommendations = async (p) => {
    try {
      setRecLoading(true);
      const payload = {
        child_name: p.name,
        age_band: String(p.age),
        ...p.sensitivities,
      };
      const recRes = await getRecommendations(payload);
      setRecommendations(recRes.data.recommendations || []);
    } catch (err) {
      console.error('Failed to load recommendations', err);
      // Backend returns 404 if no movies match
      setRecommendations([]);
    } finally {
      setRecLoading(false);
    }
  };

  if (loading) {
    return <div className="profile-detail-loading"><div className="spinner" /><p>Loading profile...</p></div>;
  }

  // Deduplicate recommendations
  const seen = new Set();
  const safePicks = recommendations.filter(r => {
    const k = (r.title || '').toLowerCase();
    if (seen.has(k)) return false;
    seen.add(k);
    return true;
  });

  return (
    <div className="profile-detail">
      <header className="pd-header">
        <div className="pd-avatar-wrap">
          <div className="pd-avatar">{profile.name.charAt(0).toUpperCase()}</div>
          <div>
            <h1>{profile.name}</h1>
            <p className="pd-meta">Age {profile.age}</p>
          </div>
        </div>
        <div className="pd-actions">
          <Link to={`/profiles/${id}/edit`} className="btn btn-secondary">✏️ Edit Profile</Link>
          <Link to="/movies" className="btn btn-primary">🎬 Browse Movies</Link>
        </div>
      </header>

      {profile.calming_strategy && (
        <section className="pd-section calming-section">
          <h3>💆 Calming Strategy</h3>
          <p>{profile.calming_strategy}</p>
        </section>
      )}

      <section className="pd-section">
        <h2>Recommended Safe Movies</h2>
        <p className="pd-subtitle">
          Based on {profile.name}'s specific sensitivity settings, these movies have been curated as safe viewing options.
        </p>

        {recLoading ? (
          <div className="pd-loading-recs">
            <span className="spinner"></span>
            <p>Analyzing library for safe movies...</p>
          </div>
        ) : safePicks.length === 0 ? (
          <div className="pd-empty">
            <p>No completely safe movies found in the database. Try adjusting the sensitivity levels or analyze more movies.</p>
          </div>
        ) : (
          <div className="pd-recs-grid">
            {safePicks.map((rec, i) => (
               <div key={rec.title} className={`pd-rec-card ${i === 0 ? 'top-pick' : ''}`}>
                 {i === 0 && <div className="pd-top-pick-badge">TOP PICK</div>}
                 
                 <div className="pd-rec-header">
                   <div className="pd-rec-title-wrap">
                     <h3>{rec.title} {rec.year && <span className="pd-rec-year">({rec.year})</span>}</h3>
                     <div className="pd-rec-tags">
                        {(Array.isArray(rec.genres || rec.genre) ? (rec.genres || rec.genre) : (rec.genres || rec.genre || '').split(/,\s*/)).filter(Boolean).map(g => (
                          <span key={g} className="pd-rec-tag">{g}</span>
                        ))}
                     </div>
                   </div>
                   <ScoreRing score={rec.similarity_score} />
                 </div>

                 <div className="pd-rec-body">
                   <p>{rec.reason}</p>
                 </div>
                 
                 <div className="pd-rec-footer">
                   {/* Here we can link to the MovieDetail page if we have the movie_id. 
                       Currently recommendations only return title. In a real app we'd want ID. 
                       For now, navigating to the dashboard is fine, or we could look up by title. */}
                 </div>
               </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

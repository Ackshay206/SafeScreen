import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getMovie } from '../api/client';
import './MovieDetail.css';

const FLAG_META = {
  violence: { label: 'Violence', icon: '⚔️' },
  blood_gore: { label: 'Blood / Gore', icon: '🩸' },
  self_harm: { label: 'Self-Harm', icon: '🩹' },
  suicide: { label: 'Suicide', icon: '⚠️' },
  gun_weapon: { label: 'Gun / Weapon', icon: '🔫' },
  abuse: { label: 'Abuse', icon: '🚫' },
  death_grief: { label: 'Death / Grief', icon: '🕊️' },
  sexual_content: { label: 'Sexual Content', icon: '🔞' },
  bullying: { label: 'Bullying', icon: '😤' },
  substance_use: { label: 'Substance Use', icon: '💊' },
  flash_seizure: { label: 'Flash / Seizure', icon: '⚡' },
  loud_sensory: { label: 'Loud / Sensory', icon: '🔊' },
};

export default function MovieDetail() {
  const { id } = useParams();
  const [movie, setMovie] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getMovie(id).then((res) => setMovie(res.data)).catch(console.error).finally(() => setLoading(false));
  }, [id]);

  if (loading) return <div className="detail-loading"><div className="spinner" /><p>Loading movie...</p></div>;
  if (!movie) return <div className="detail-loading"><p>Movie not found.</p><Link to="/movies" className="btn btn-primary">← Back to Dashboard</Link></div>;

  const flagEntries = Object.entries(movie.overall_flags || {}).filter(([, v]) => v !== 'none');

  // Build intensity data for the segment timeline
  const maxIntensity = (flags) => Math.max(...Object.values(flags));
  const intensityColor = (val) => {
    if (val === 0) return 'var(--safe)';
    if (val <= 2) return 'var(--mild)';
    if (val <= 3) return 'var(--moderate)';
    return 'var(--intense)';
  };

  return (
    <div className="movie-detail">

      <div className="detail-hero">
        <img src={movie.poster_url} alt={movie.title} className="detail-poster" />
        <div className="detail-hero-info">
          <h1>{movie.title}</h1>
          <div className="detail-meta">
            <span className="mpaa-badge-lg">{movie.mpaa_rating}</span>
            <span>{movie.year}</span>
            <span className="dot">·</span>
            <span>{movie.runtime_minutes} min</span>
            <span className="dot">·</span>
            <span>{movie.genre.join(', ')}</span>
          </div>
          <p className="detail-synopsis">{movie.synopsis}</p>
        </div>
      </div>

      {/* Overall flags */}
      <section className="detail-section">
        <h2>Content Flags</h2>
        {flagEntries.length === 0 ? (
          <p className="no-flags">No content flags detected for this movie.</p>
        ) : (
          <div className="flags-grid">
            {flagEntries.map(([key, severity]) => (
              <div key={key} className={`flag-card severity-${severity}`}>
                <span className="flag-card-icon">{FLAG_META[key]?.icon}</span>
                <span className="flag-card-label">{FLAG_META[key]?.label}</span>
                <span className="flag-card-severity">{severity}</span>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Plain-language summary */}
      <section className="detail-section">
        <h2>Safety Summary</h2>
        <div className="summary-box">{movie.plain_language_summary}</div>
      </section>

      {/* Segment timeline */}
      {movie.segments && movie.segments.length > 0 && (
        <section className="detail-section">
          <h2>Scene-by-Scene Timeline</h2>
          <div className="timeline">
            {movie.segments.map((seg) => {
              const peak = maxIntensity(seg.flags);
              return (
                <div key={seg.segment_id} className="timeline-segment">
                  <div className="timeline-bar" style={{ backgroundColor: intensityColor(peak) }}>
                    <span className="timeline-time">{seg.start_time} – {seg.end_time}</span>
                  </div>
                  <div className="timeline-body">
                    <div className="timeline-flags">
                      {Object.entries(seg.flags).filter(([, v]) => v > 0).length === 0 ? (
                        <span className="mini-flag safe-flag">✓ No flags</span>
                      ) : (
                        Object.entries(seg.flags).filter(([, v]) => v > 0).map(([key, intensity]) => (
                          <span key={key} className={`mini-flag intensity-${intensity}`}>
                            {FLAG_META[key]?.label} ({intensity}/5)
                          </span>
                        ))
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      )}
    </div>
  );
}

import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getMovies } from '../api/client';
import './MovieDashboard.css';

const FLAG_LABELS = {
  violence: { label: 'Violence', icon: '⚔️' },
  blood_gore: { label: 'Blood', icon: '🩸' },
  self_harm: { label: 'Self-Harm', icon: '🩹' },
  suicide: { label: 'Suicide', icon: '⚠️' },
  gun_weapon: { label: 'Guns', icon: '🔫' },
  abuse: { label: 'Abuse', icon: '🚫' },
  death_grief: { label: 'Death', icon: '🕊️' },
  sexual_content: { label: 'Sexual', icon: '🔞' },
  bullying: { label: 'Bullying', icon: '😤' },
  substance_use: { label: 'Substances', icon: '💊' },
  flash_seizure: { label: 'Flash', icon: '⚡' },
  loud_sensory: { label: 'Loud/Sensory', icon: '🔊' },
};

const SEVERITY_ORDER = ['intense', 'moderate', 'mild'];

export default function MovieDashboard() {
  const [movies, setMovies] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getMovies().then((res) => setMovies(res.data)).catch(console.error).finally(() => setLoading(false));
  }, []);

  const activeFlags = (flags) => {
    if (!flags) return [];
    return Object.entries(flags)
      .filter(([, severity]) => severity !== 'none')
      .sort((a, b) => SEVERITY_ORDER.indexOf(a[1]) - SEVERITY_ORDER.indexOf(b[1]))
      .slice(0, 5); // show top 5 to avoid clutter
  };

  if (loading) {
    return <div className="dash-loading"><div className="spinner" /><p>Loading movies...</p></div>;
  }

  return (
    <div className="movie-dashboard">
      <header className="dash-header">
        <div className="dash-header-content">
          <h1>🎬 Movie Dashboard</h1>
          <p className="dash-tagline">Select a movie to view its safety summary and create a viewing plan.</p>
        </div>
      </header>

      <main className="dash-main">
        {movies.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">🎞️</div>
            <h3>No movies yet</h3>
            <p>Run the seed script to add sample movies to the database.</p>
          </div>
        ) : (
          <div className="movie-grid">
            {movies.map((movie) => (
              <Link key={movie.id} to={`/movies/${movie.id}`} className="movie-card">
                <div className="movie-poster-wrap">
                  <img src={movie.poster_url} alt={movie.title} className="movie-poster" loading="lazy" onError={(e) => { e.target.src = ''; e.target.classList.add('poster-fallback'); }} />
                  <span className="mpaa-badge">{movie.mpaa_rating}</span>
                </div>
                <div className="movie-card-body">
                  <h3 className="movie-title">{movie.title}</h3>
                  <div className="movie-meta">
                    <span>{movie.year}</span>
                    <span className="dot">·</span>
                    <span>{movie.genre.slice(0, 2).join(', ')}</span>
                  </div>
                  <div className="flag-chips">
                    {activeFlags(movie.overall_flags).map(([key, severity]) => (
                      <span key={key} className={`flag-chip severity-${severity}`} title={`${FLAG_LABELS[key]?.label}: ${severity}`}>
                        {FLAG_LABELS[key]?.icon} {severity}
                      </span>
                    ))}
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}

import { useLocation, useNavigate } from 'react-router-dom';
import { useEffect, useState } from 'react';

/* ── palette ── */
const ACCENT  = '#6C63FF';
const ACCENT2 = '#A78BFA';
const DARK    = '#0F0E17';
const CARD_BG = '#1A1929';
const SURFACE = '#231F3A';
const TEXT     = '#EDE9FE';
const MUTED    = '#9CA3AF';

/* ── score ring ── */
function ScoreRing({ score }) {
  const pct = Math.round((score ?? 0.5) * 100);
  const r   = 22;
  const circ = 2 * Math.PI * r;
  const dash = circ * (pct / 100);
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}>
      <svg width={56} height={56} style={{ transform: 'rotate(-90deg)' }}>
        <circle cx={28} cy={28} r={r} fill="none" stroke={SURFACE} strokeWidth={5} />
        <circle
          cx={28} cy={28} r={r} fill="none"
          stroke={ACCENT} strokeWidth={5}
          strokeDasharray={`${dash} ${circ}`}
          strokeLinecap="round"
          style={{ transition: 'stroke-dasharray 1s ease' }}
        />
      </svg>
      <span style={{
        position: 'absolute',
        fontSize: '0.75rem',
        fontWeight: 700,
        color: TEXT,
        marginTop: 18,
        userSelect: 'none'
      }}>{pct}%</span>
      <span style={{ fontSize: '0.65rem', color: MUTED, letterSpacing: '0.05em' }}>MATCH</span>
    </div>
  );
}

/* ── hero card (top pick) ── */
function HeroCard({ rec, index }) {
  const [visible, setVisible] = useState(false);
  useEffect(() => { const t = setTimeout(() => setVisible(true), index * 120); return () => clearTimeout(t); }, [index]);

  const genres = (rec.genres || rec.genre || '').split(/,\s*/).filter(Boolean);

  return (
    <div style={{
      opacity: visible ? 1 : 0,
      transform: visible ? 'translateY(0)' : 'translateY(20px)',
      transition: 'opacity 0.5s ease, transform 0.5s ease',
      background: index === 0
        ? `linear-gradient(135deg, ${CARD_BG} 0%, #1e1438 100%)`
        : CARD_BG,
      borderRadius: 20,
      padding: index === 0 ? '2rem' : '1.4rem 1.6rem',
      border: index === 0 ? `1.5px solid ${ACCENT}55` : `1px solid #2e2a48`,
      boxShadow: index === 0 ? `0 0 40px ${ACCENT}22` : 'none',
      position: 'relative',
      overflow: 'hidden',
    }}>
      {index === 0 && (
        <div style={{
          position: 'absolute', top: 0, right: 0,
          background: `linear-gradient(135deg, ${ACCENT}, ${ACCENT2})`,
          padding: '6px 18px',
          borderBottomLeftRadius: 14,
          fontSize: '0.7rem', fontWeight: 700, letterSpacing: '0.08em',
          color: '#fff',
        }}>
          TOP PICK
        </div>
      )}

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '1rem' }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          {index > 0 && (
            <span style={{ fontSize: '0.65rem', fontWeight: 700, color: ACCENT2, letterSpacing: '0.08em' }}>
              #{rec.rank}
            </span>
          )}
          <h2 style={{
            fontSize: index === 0 ? '1.4rem' : '1.1rem',
            fontWeight: 700,
            color: TEXT,
            margin: '4px 0 6px',
            lineHeight: 1.2,
          }}>
            {rec.title}
            {rec.year && (
              <span style={{ fontSize: '0.8em', color: MUTED, fontWeight: 400, marginLeft: 8 }}>
                ({rec.year})
              </span>
            )}
          </h2>

          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 10 }}>
            {genres.map(g => (
              <span key={g} style={{
                background: `${ACCENT}22`,
                color: ACCENT2,
                padding: '3px 10px',
                borderRadius: 99,
                fontSize: '0.72rem',
                fontWeight: 600,
                border: `1px solid ${ACCENT}44`,
              }}>{g}</span>
            ))}
            {rec.mpaa_rating && (
              <span style={{
                background: '#ffffff10',
                color: MUTED,
                padding: '3px 10px',
                borderRadius: 99,
                fontSize: '0.72rem',
                fontWeight: 600,
                border: '1px solid #ffffff18',
              }}>{rec.mpaa_rating}</span>
            )}
          </div>
        </div>

        <div style={{ position: 'relative', flexShrink: 0 }}>
          <ScoreRing score={rec.similarity_score} />
        </div>
      </div>

      {rec.reason && (
        <p style={{
          margin: 0,
          fontSize: '0.875rem',
          color: index === 0 ? '#c4b8f0' : MUTED,
          lineHeight: 1.6,
          borderTop: `1px solid #ffffff10`,
          paddingTop: '0.85rem',
          marginTop: '0.25rem',
        }}>
          {rec.reason}
        </p>
      )}
    </div>
  );
}

/* ── main page ── */
export default function Recommendations() {
  const location = useLocation();
  const navigate = useNavigate();
  const data     = location.state;

  if (!data || !data.recommendations) {
    return (
      <div style={{
        minHeight: '100vh', background: DARK, display: 'flex',
        flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
        gap: '1rem', fontFamily: 'Inter, system-ui, sans-serif', color: TEXT,
      }}>
        <p style={{ color: MUTED }}>No recommendations found. Please fill out a profile first.</p>
        <button
          onClick={() => navigate('/profiles/new')}
          style={primaryBtn}
        >Create Profile</button>
      </div>
    );
  }

  const { recommendations, reference_film, child_name } = data;
  // Dedupe client-side as final safety net
  const seen = new Set();
  const recs = recommendations.filter(r => {
    const k = (r.title || '').toLowerCase();
    if (seen.has(k)) return false;
    seen.add(k);
    return true;
  });

  const top  = recs[0];
  const rest = recs.slice(1);

  return (
    <div style={{
      minHeight: '100vh',
      background: DARK,
      fontFamily: "'Inter', system-ui, sans-serif",
      color: TEXT,
    }}>
      {/* glow blob */}
      <div style={{
        position: 'fixed', top: '-150px', left: '50%', transform: 'translateX(-50%)',
        width: 500, height: 500,
        background: `radial-gradient(circle, ${ACCENT}30 0%, transparent 70%)`,
        pointerEvents: 'none', zIndex: 0,
      }} />

      <div style={{ position: 'relative', zIndex: 1, maxWidth: 680, margin: '0 auto', padding: '3rem 1.5rem 4rem' }}>

        {/* header */}
        <div style={{ marginBottom: '2.5rem' }}>
          <p style={{ fontSize: '0.75rem', fontWeight: 700, letterSpacing: '0.12em', color: ACCENT2, margin: '0 0 8px' }}>
            SAFE PICKS
          </p>
          <h1 style={{ fontSize: '2rem', fontWeight: 800, margin: '0 0 6px', lineHeight: 1.2 }}>
            {child_name ? `For ${child_name}` : 'Your recommendations'}
          </h1>
          {reference_film && (
            <p style={{ fontSize: '0.875rem', color: MUTED, margin: 0 }}>
              Based on watching&nbsp;<strong style={{ color: TEXT }}>{reference_film}</strong>
            </p>
          )}
        </div>

        {/* top pick label */}
        {top && (
          <>
            <div style={{ marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ fontSize: '1.1rem' }}>🎬</span>
              <span style={{ fontSize: '0.8rem', fontWeight: 600, color: MUTED, letterSpacing: '0.06em' }}>
                BEST MATCH FOR {(child_name || 'THIS PROFILE').toUpperCase()}
              </span>
            </div>
            <HeroCard rec={top} index={0} />
          </>
        )}

        {/* additional picks */}
        {rest.length > 0 && (
          <>
            <div style={{ margin: '2rem 0 0.75rem', display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ fontSize: '0.8rem', fontWeight: 600, color: MUTED, letterSpacing: '0.06em' }}>
                ALSO SAFE
              </span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
              {rest.map((rec, i) => (
                <HeroCard key={rec.title} rec={rec} index={i + 1} />
              ))}
            </div>
          </>
        )}

        {/* no recs fallback */}
        {!top && (
          <div style={{
            background: CARD_BG, borderRadius: 16,
            padding: '2rem', textAlign: 'center', border: '1px solid #2e2a48',
          }}>
            <p style={{ color: MUTED, margin: 0 }}>
              No movies matched this profile's sensitivity settings yet. More will appear once the full library is analyzed.
            </p>
          </div>
        )}

        {/* actions */}
        <div style={{ marginTop: '2.5rem', display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
          <button onClick={() => navigate(-1)} style={ghostBtn}>
            ← Edit profile
          </button>
          <button onClick={() => navigate('/movies')} style={primaryBtn}>
            Browse all movies
          </button>
        </div>
      </div>
    </div>
  );
}

const primaryBtn = {
  padding: '11px 24px',
  borderRadius: 10,
  border: 'none',
  background: `linear-gradient(135deg, ${ACCENT}, ${ACCENT2})`,
  color: '#fff',
  cursor: 'pointer',
  fontSize: '0.9rem',
  fontWeight: 600,
  fontFamily: 'inherit',
  boxShadow: `0 4px 20px ${ACCENT}44`,
  transition: 'opacity 0.2s',
};

const ghostBtn = {
  padding: '11px 24px',
  borderRadius: 10,
  border: '1px solid #2e2a48',
  background: 'transparent',
  color: TEXT,
  cursor: 'pointer',
  fontSize: '0.9rem',
  fontWeight: 500,
  fontFamily: 'inherit',
  transition: 'border-color 0.2s',
};

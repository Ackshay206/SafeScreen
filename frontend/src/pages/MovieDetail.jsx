import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getMovie, getProfiles, generateViewingPlan, submitFeedback } from '../api/client';
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

const ACTION_COLORS = {
  skip: { bg: '#fee2e2', color: '#dc2626', border: '#fca5a5' },
  blur: { bg: '#ffedd5', color: '#ea580c', border: '#fdba74' },
  mute: { bg: '#fef3c7', color: '#d97706', border: '#fcd34d' },
  pause_and_prompt: { bg: '#dbeafe', color: '#2563eb', border: '#93c5fd' },
  parent_present: { bg: '#e0e7ff', color: '#4f46e5', border: '#a5b4fc' },
  continue: { bg: '#dcfce7', color: '#16a34a', border: '#86efac' },
};

const ACTION_ICONS = {
  skip: '⏭️', blur: '🔲', mute: '🔇',
  pause_and_prompt: '⏸️', parent_present: '👨‍👩‍👧', continue: '✅',
};

const MODE_STYLES = {
  safe: { bg: '#dcfce7', color: '#166534', icon: '🟢' },
  minor_caution: { bg: '#fef3c7', color: '#92400e', icon: '🟡' },
  co_view_suggested: { bg: '#dbeafe', color: '#1e40af', icon: '🔵' },
  co_view_required: { bg: '#e0e7ff', color: '#3730a3', icon: '🟣' },
  heavy_modification: { bg: '#ffedd5', color: '#9a3412', icon: '🟠' },
  not_recommended: { bg: '#fee2e2', color: '#991b1b', icon: '🔴' },
};

/* ── Feedback Modal ── */
function FeedbackModal({ plan, profileId, movieId, onClose }) {
  const [strictness, setStrictness] = useState('about_right');
  const [distressed, setDistressed] = useState(false);
  const [distressLevel, setDistressLevel] = useState('none');
  const [triggeredFlags, setTriggeredFlags] = useState([]);
  const [note, setNote] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState(null);

  const flaggedInPlan = (plan?.segment_actions || [])
    .flatMap(s => s.triggered_flags || [])
    .filter((v, i, a) => a.indexOf(v) === i);

  const toggleFlag = (f) => {
    setTriggeredFlags(prev =>
      prev.includes(f) ? prev.filter(x => x !== f) : [...prev, f]
    );
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    try {
      const res = await submitFeedback({
        profile_id: profileId,
        movie_id: movieId,
        plan_id: plan?.plan_id || null,
        strictness_rating: strictness,
        child_seemed_distressed: distressed,
        distress_level: distressLevel,
        triggered_flags: triggeredFlags,
        optional_note: note,
      });
      setResult(res.data);
    } catch (err) {
      console.error(err);
      setResult({ message: 'Failed to submit feedback. Please try again.', calming_videos: [], show_calming: false });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="feedback-overlay" onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <div className="feedback-modal">
        {!result ? (
          <>
            <div className="fm-header">
              <h2>Post-Watch Feedback</h2>
              <button className="fm-close" onClick={onClose}>×</button>
            </div>

            <div className="fm-body">
              <div className="fm-question">
                <label>How was the viewing plan's strictness?</label>
                <div className="fm-options">
                  {[
                    { val: 'too_strict', label: '🔒 Too Strict', desc: 'Skipped/blurred more than needed' },
                    { val: 'about_right', label: '✅ About Right', desc: 'Plan matched my experience' },
                    { val: 'too_loose', label: '⚠️ Too Loose', desc: 'Should have flagged more content' },
                  ].map(opt => (
                    <button
                      key={opt.val}
                      className={`fm-option ${strictness === opt.val ? 'selected' : ''}`}
                      onClick={() => setStrictness(opt.val)}
                    >
                      <span className="fm-opt-label">{opt.label}</span>
                      <span className="fm-opt-desc">{opt.desc}</span>
                    </button>
                  ))}
                </div>
              </div>

              <div className="fm-question">
                <label>Was the viewer distressed during or after watching?</label>
                <div className="fm-toggle-row">
                  <button
                    className={`fm-toggle ${!distressed ? 'selected' : ''}`}
                    onClick={() => { setDistressed(false); setDistressLevel('none'); }}
                  >No</button>
                  <button
                    className={`fm-toggle ${distressed ? 'selected' : ''}`}
                    onClick={() => { setDistressed(true); setDistressLevel('mild'); }}
                  >Yes</button>
                </div>
              </div>

              {distressed && (
                <>
                  <div className="fm-question">
                    <label>How severe was the distress?</label>
                    <div className="fm-options horizontal">
                      {['mild', 'moderate', 'severe'].map(lvl => (
                        <button
                          key={lvl}
                          className={`fm-option small ${distressLevel === lvl ? 'selected' : ''}`}
                          onClick={() => setDistressLevel(lvl)}
                        >
                          {lvl.charAt(0).toUpperCase() + lvl.slice(1)}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="fm-question">
                    <label>Which content types caused distress? (select all that apply)</label>
                    <div className="fm-flag-chips">
                      {(flaggedInPlan.length > 0 ? flaggedInPlan : Object.keys(FLAG_META)).map(f => (
                        <button
                          key={f}
                          className={`fm-flag-chip ${triggeredFlags.includes(f) ? 'selected' : ''}`}
                          onClick={() => toggleFlag(f)}
                        >
                          {FLAG_META[f]?.icon} {FLAG_META[f]?.label || f}
                        </button>
                      ))}
                    </div>
                  </div>
                </>
              )}

              <div className="fm-question">
                <label>Any additional notes? (optional)</label>
                <textarea
                  className="fm-textarea"
                  value={note}
                  onChange={(e) => setNote(e.target.value)}
                  placeholder="e.g., The scene at 0:45:00 was more intense than expected..."
                  rows={3}
                />
              </div>
            </div>

            <div className="fm-footer">
              <button className="btn btn-secondary" onClick={onClose}>Cancel</button>
              <button className="btn btn-primary" onClick={handleSubmit} disabled={submitting}>
                {submitting ? 'Submitting...' : 'Submit Feedback'}
              </button>
            </div>
          </>
        ) : (
          <>
            <div className="fm-header">
              <h2>{result.show_calming ? '💆 Calming Resources' : '✅ Feedback Submitted'}</h2>
              <button className="fm-close" onClick={onClose}>×</button>
            </div>

            <div className="fm-body">
              <p className="fm-result-msg">{result.message}</p>

              {result.show_calming && result.calming_videos?.length > 0 && (
                <div className="fm-calming-videos">
                  <h3>Recommended Calming Videos</h3>
                  <div className="fm-video-list">
                    {result.calming_videos.map((vid, i) => (
                      <a
                        key={i}
                        href={vid.youtube_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="fm-video-card"
                      >
                        <div className="fm-video-icon">▶️</div>
                        <div className="fm-video-info">
                          <span className="fm-video-title">{vid.title}</span>
                          <span className="fm-video-reason">{vid.reason}</span>
                        </div>
                        <span className="fm-video-arrow">→</span>
                      </a>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="fm-footer">
              <button className="btn btn-primary" onClick={onClose}>Done</button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

/* ── Viewing Plan Panel ── */
function ViewingPlanPanel({ plan, profileId, movieId }) {
  const [expandedSeg, setExpandedSeg] = useState(null);
  const [showFeedback, setShowFeedback] = useState(false);
  const mode = plan.overall_mode || {};
  const modeStyle = MODE_STYLES[mode.mode] || MODE_STYLES.safe;
  const actions = mode.action_summary || {};

  return (
    <div className="viewing-plan-panel">
      <div className="vp-header">
        <div className="vp-header-top">
          <h2>Viewing Plan for {plan.child_name}</h2>
          {plan.child_age && <span className="vp-age-badge">Age {plan.child_age}</span>}
        </div>
        <div className="vp-mode-card" style={{ background: modeStyle.bg, color: modeStyle.color }}>
          <span className="vp-mode-icon">{modeStyle.icon}</span>
          <div className="vp-mode-text">
            <strong>{mode.mode?.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}</strong>
            <p>{mode.description}</p>
          </div>
          {mode.co_viewing && <span className="vp-coview-badge">👨‍👩‍👧 Co-viewing Recommended</span>}
        </div>
      </div>

      {plan.parent_summary && (
        <div className="vp-summary-card">
          <h3>📋 Summary</h3>
          <p>{plan.parent_summary}</p>
        </div>
      )}

      <div className="vp-stats-bar">
        <div className="vp-stat"><span className="vp-stat-num">{plan.total_segments}</span><span className="vp-stat-label">Total Scenes</span></div>
        <div className="vp-stat safe"><span className="vp-stat-num">{plan.safe_segments}</span><span className="vp-stat-label">Safe</span></div>
        <div className="vp-stat flagged"><span className="vp-stat-num">{plan.flagged_segments}</span><span className="vp-stat-label">Flagged</span></div>
        <div className="vp-stat sessions"><span className="vp-stat-num">{plan.sessions?.length || 1}</span><span className="vp-stat-label">Sessions</span></div>
      </div>

      {plan.flagged_segments > 0 && (
        <div className="vp-action-breakdown">
          <h3>Action Breakdown</h3>
          <div className="vp-action-chips">
            {Object.entries(actions).filter(([, v]) => v > 0).map(([action, count]) => {
              const ac = ACTION_COLORS[action] || ACTION_COLORS.continue;
              return (
                <div key={action} className="vp-action-chip" style={{ background: ac.bg, color: ac.color, borderColor: ac.border }}>
                  <span>{ACTION_ICONS[action] || '•'}</span>
                  <span className="vp-action-chip-label">{action.replace(/_/g, ' ')}</span>
                  <span className="vp-action-chip-count">{count}</span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {plan.sessions && plan.sessions.length > 1 && (
        <div className="vp-sessions">
          <h3>🎬 Session Pacing</h3>
          <p className="vp-sessions-hint">We recommend splitting this into {plan.sessions.length} viewing sessions.</p>
          <div className="vp-session-cards">
            {plan.sessions.map((sess, i) => (
              <div key={i} className="vp-session-card">
                <div className="vp-session-header">
                  <span className="vp-session-num">Session {sess.session}</span>
                  <span className="vp-session-time">{sess.start_time} – {sess.end_time}</span>
                </div>
                <div className="vp-session-meta">
                  <span>Scenes {sess.start_segment}–{sess.end_segment}</span>
                  {sess.flagged_count > 0 && <span className="vp-session-flag-count">⚠️ {sess.flagged_count} flagged</span>}
                </div>
                {sess.is_checkpoint && sess.checkpoint_message && (
                  <div className="vp-checkpoint">⏸️ {sess.checkpoint_message}</div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {plan.calming_strategy && (
        <div className="vp-calming">
          <h3>💆 Calming Strategy</h3>
          <p>{plan.calming_strategy}</p>
        </div>
      )}

      <div className="vp-timeline">
        <h3>Scene-by-Scene Plan</h3>
        <div className="vp-segments">
          {(plan.segment_actions || []).map((seg) => {
            const ac = ACTION_COLORS[seg.overall_action] || ACTION_COLORS.continue;
            const isExpanded = expandedSeg === seg.segment_id;
            return (
              <div key={seg.segment_id} className={`vp-seg ${seg.is_safe ? 'safe' : 'flagged'}`}>
                <div className="vp-seg-header" onClick={() => setExpandedSeg(isExpanded ? null : seg.segment_id)} style={{ cursor: 'pointer' }}>
                  <div className="vp-seg-left">
                    <div className="vp-seg-bar" style={{ backgroundColor: ac.color }} />
                    <span className="vp-seg-time">{seg.start_time} – {seg.end_time}</span>
                  </div>
                  <div className="vp-seg-action-badge" style={{ background: ac.bg, color: ac.color, border: `1px solid ${ac.border}` }}>
                    {ACTION_ICONS[seg.overall_action]} {seg.action_description}
                  </div>
                  <span className="vp-seg-expand">{isExpanded ? '▾' : '▸'}</span>
                </div>
                {isExpanded && (
                  <div className="vp-seg-details">
                    <p className="vp-seg-summary">{seg.summary}</p>
                    {seg.triggered_flags?.length > 0 && (
                      <div className="vp-seg-flags">
                        {seg.triggered_flags.map(f => (
                          <span key={f} className="vp-seg-flag-chip" style={{ background: ac.bg, color: ac.color }}>
                            {FLAG_META[f]?.icon} {FLAG_META[f]?.label || f}
                          </span>
                        ))}
                      </div>
                    )}
                    {seg.flag_details?.length > 0 && (
                      <div className="vp-seg-flag-details">
                        {seg.flag_details.map((fd, i) => (
                          <div key={i} className="vp-flag-detail-row">
                            <span>{FLAG_META[fd.flag]?.icon} {FLAG_META[fd.flag]?.label}</span>
                            <span className="vp-flag-sensitivity">Sensitivity: {fd.sensitivity}/5</span>
                            <span className="vp-flag-action" style={{ color: (ACTION_COLORS[fd.action] || {}).color }}>→ {fd.description}</span>
                          </div>
                        ))}
                      </div>
                    )}
                    {seg.parent_prompt && <div className="vp-parent-prompt">🔔 {seg.parent_prompt}</div>}
                    {seg.calming_tip && <div className="vp-calming-tip">💆 Calming tip: {seg.calming_tip}</div>}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      <div className="vp-footer">
        <button className="btn btn-primary vp-watched-btn" onClick={() => setShowFeedback(true)}>
          ✓ Mark as Watched & Give Feedback
        </button>
      </div>

      {showFeedback && (
        <FeedbackModal plan={plan} profileId={profileId} movieId={movieId} onClose={() => setShowFeedback(false)} />
      )}
    </div>
  );
}

/* ── Main MovieDetail Page ── */
export default function MovieDetail() {
  const { id } = useParams();
  const [movie, setMovie] = useState(null);
  const [loading, setLoading] = useState(true);
  const [profiles, setProfiles] = useState([]);
  const [selectedProfile, setSelectedProfile] = useState('');
  const [planLoading, setPlanLoading] = useState(false);
  const [viewingPlan, setViewingPlan] = useState(null);
  const [planError, setPlanError] = useState('');

  useEffect(() => {
    getMovie(id).then((res) => setMovie(res.data)).catch(console.error).finally(() => setLoading(false));
    getProfiles().then((res) => setProfiles(res.data)).catch(console.error);
  }, [id]);

  const handleGeneratePlan = async () => {
    if (!selectedProfile) return;
    setPlanLoading(true);
    setPlanError('');
    setViewingPlan(null);
    try {
      const res = await generateViewingPlan(id, selectedProfile);
      setViewingPlan(res.data);
    } catch (err) {
      setPlanError(err.response?.data?.detail || 'Failed to generate viewing plan.');
    } finally {
      setPlanLoading(false);
    }
  };

  if (loading) return <div className="detail-loading"><div className="spinner" /><p>Loading movie...</p></div>;
  if (!movie) return <div className="detail-loading"><p>Movie not found.</p><Link to="/movies" className="btn btn-primary">← Back</Link></div>;

  const flagEntries = Object.entries(movie.overall_flags || {}).filter(([, v]) => v !== 'none');
  const hasSegments = movie.segments && movie.segments.length > 0;

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

      <section className="detail-section">
        <h2>Safety Summary</h2>
        <div className="summary-box">{movie.plain_language_summary}</div>
      </section>

      <section className="detail-section vp-generate-section">
        <h2>🛡️ Generate Viewing Plan</h2>
        {!hasSegments ? (
          <div className="vp-no-segments"><p>This movie hasn't been analyzed yet. Run the analysis first.</p></div>
        ) : (
          <>
            <div className="vp-generate-controls">
              <div className="vp-profile-select-wrapper">
                <label htmlFor="profile-select">Select a profile:</label>
                <select id="profile-select" value={selectedProfile} onChange={(e) => { setSelectedProfile(e.target.value); setViewingPlan(null); setPlanError(''); }} className="vp-profile-select">
                  <option value="">Choose a profile...</option>
                  {profiles.map((p) => (<option key={p.id} value={p.id}>{p.name} (Age {p.age})</option>))}
                </select>
              </div>
              <button className="btn btn-primary vp-generate-btn" onClick={handleGeneratePlan} disabled={!selectedProfile || planLoading}>
                {planLoading ? <><span className="btn-spinner" /> Generating...</> : '🛡️ Generate Viewing Plan'}
              </button>
            </div>
            {profiles.length === 0 && <p className="vp-no-profiles">No profiles found. <Link to="/profiles/new">Create one first</Link>.</p>}
            {planError && <div className="vp-error"><span>⚠️</span> {planError}</div>}
            {viewingPlan && <ViewingPlanPanel plan={viewingPlan} profileId={selectedProfile} movieId={id} />}
          </>
        )}
      </section>

      {hasSegments && !viewingPlan && (
        <section className="detail-section">
          <h2>Scene-by-Scene Timeline</h2>
          <div className="timeline">
            {movie.segments.map((seg) => {
              const flags = Array.isArray(seg.flags) ? seg.flags : Object.entries(seg.flags || {}).filter(([,v]) => v !== 'none').map(([k]) => k);
              const hasFlags = flags.length > 0;
              return (
                <div key={seg.segment_id} className="timeline-segment">
                  <div className="timeline-bar" style={{ backgroundColor: hasFlags ? 'var(--moderate)' : 'var(--safe)' }}>
                    <span className="timeline-time">{seg.start_time} – {seg.end_time}</span>
                  </div>
                  <div className="timeline-body">
                    <div className="timeline-flags">
                      {!hasFlags ? (
                        <span className="mini-flag safe-flag">✓ No flags</span>
                      ) : flags.map((key) => (
                        <span key={key} className="mini-flag flagged-tag">{FLAG_META[key]?.icon} {FLAG_META[key]?.label || key}</span>
                      ))}
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
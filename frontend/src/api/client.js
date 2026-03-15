import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api',
  headers: { 'Content-Type': 'application/json' },
});

// ---- Profiles ----
export const getProfiles = () => api.get('/profiles');
export const getProfile = (id) => api.get(`/profiles/${id}`);
export const createProfile = (data) => api.post('/profiles', data);
export const updateProfile = (id, data) => api.put(`/profiles/${id}`, data);
export const deleteProfile = (id) => api.delete(`/profiles/${id}`);
export const sendProfileChatMessage = (messages) => api.post('/profile_chat', { messages });

// ---- Movies ----
export const getMovies = () => api.get('/movies');
export const getMovie = (id) => api.get(`/movies/${id}`);
export const getMovieSafety = (id) => api.get(`/movies/${id}/safety`);
export const getRecommendations = (data) => api.post('/recommendations', data);

// ---- Viewing Plans ----
export const generateViewingPlan = (movieId, profileId) =>
  api.post(`/viewing-plan/${movieId}`, { profile_id: profileId });

export const getExistingPlan = (movieId, profileId) =>
  api.get(`/viewing-plan/${movieId}/${profileId}`);

// ---- Feedback ----
export const submitFeedback = (data) => api.post('/feedback', data);

export const getExistingFeedback = (movieId, profileId) =>
  api.get(`/feedback/${movieId}/${profileId}`);

export default api;
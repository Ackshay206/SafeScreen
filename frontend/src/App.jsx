import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Home from './pages/Home';
import CreateProfile from './pages/CreateProfile';
import MovieDashboard from './pages/MovieDashboard';
import MovieDetail from './pages/MovieDetail';
import Recommendations from './pages/Recommendations';
import ProfileDetail from './pages/ProfileDetail';

export default function App() {
  return (
    <BrowserRouter>
      <Navbar />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/profiles/new" element={<CreateProfile />} />
        <Route path="/profiles/:id" element={<ProfileDetail />} />
        <Route path="/profiles/:id/edit" element={<CreateProfile />} />
        <Route path="/movies" element={<MovieDashboard />} />
        <Route path="/movies/:id" element={<MovieDetail />} />
        <Route path="/recommendations" element={<Recommendations />} />
      </Routes>
    </BrowserRouter>
  );
}

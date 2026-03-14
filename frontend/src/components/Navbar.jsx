import { NavLink } from 'react-router-dom';
import './Navbar.css';

export default function Navbar() {
  return (
    <nav className="navbar">
      <NavLink to="/" className="nav-brand">🛡️ SafeScreen</NavLink>
      <div className="nav-links">
        <NavLink to="/" end className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          Profiles
        </NavLink>
        <NavLink to="/movies" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          Movies
        </NavLink>
      </div>
    </nav>
  );
}

import React from 'react';
import { NavLink } from 'react-router-dom';
import { ShieldCheck, LayoutDashboard, Image, Video, Mic, UserCheck, History, LogIn } from 'lucide-react';

export const Navbar = () => {
  return (
    <nav className="navbar">
      <div className="navbar-container">
        <NavLink to="/" className="nav-brand">
          <ShieldCheck size={28} color="#818cf8" />
          <span>Veri<span className="gradient-text">AI</span></span>
        </NavLink>

        <ul className="nav-links">
          <li>
            <NavLink to="/" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`} end>
              <ShieldCheck size={18} /> Home
            </NavLink>
          </li>
          <li>
            <NavLink to="/dashboard" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              <LayoutDashboard size={18} /> Dashboard
            </NavLink>
          </li>
          <li>
            <NavLink to="/image-detection" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              <Image size={18} /> Image AI
            </NavLink>
          </li>
          <li>
            <NavLink to="/video-detection" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              <Video size={18} /> Video AI
            </NavLink>
          </li>
          <li>
            <NavLink to="/audio-analysis" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              <Mic size={18} /> Audio AI
            </NavLink>
          </li>
          <li>
            <NavLink to="/identity-verification" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              <UserCheck size={18} /> Identity Verification
            </NavLink>
          </li>
          <li>
            <NavLink to="/history" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              <History size={18} /> Audit History
            </NavLink>
          </li>
          <li>
            <NavLink to="/login" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              <LogIn size={18} /> Login
            </NavLink>
          </li>
        </ul>
      </div>
    </nav>
  );
};

export default Navbar;

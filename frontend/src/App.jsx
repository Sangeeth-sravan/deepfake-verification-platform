import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import HomePage from './pages/HomePage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import DashboardPage from './pages/DashboardPage';
import ImageDetectionPage from './pages/ImageDetectionPage';
import VideoDetectionPage from './pages/VideoDetectionPage';
import AudioAnalysisPage from './pages/AudioAnalysisPage';
import IdentityVerificationPage from './pages/IdentityVerificationPage';
import ResultsPage from './pages/ResultsPage';
import HistoryPage from './pages/HistoryPage';

function NotFoundPage() {
  return (
    <div style={{ textAlign: 'center', padding: '4rem 1rem' }}>
      <h1 style={{ fontSize: '3rem', color: '#ef4444', marginBottom: '1rem' }}>404</h1>
      <h2 style={{ marginBottom: '1rem' }}>Page Not Found</h2>
      <p style={{ color: 'var(--text-muted)', marginBottom: '2rem' }}>
        The requested resource or verification route does not exist.
      </p>
      <Link to="/" className="btn btn-primary">
        Return to Home Page
      </Link>
    </div>
  );
}

export function App() {
  return (
    <Router>
      <div className="app-container">
        <Navbar />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/image-detection" element={<ImageDetectionPage />} />
            <Route path="/video-detection" element={<VideoDetectionPage />} />
            <Route path="/audio-analysis" element={<AudioAnalysisPage />} />
            <Route path="/identity-verification" element={<IdentityVerificationPage />} />
            <Route path="/results/:id" element={<ResultsPage />} />
            <Route path="/results" element={<HistoryPage />} />
            <Route path="/history" element={<HistoryPage />} />
            <Route path="*" element={<NotFoundPage />} />
          </Routes>
        </main>
        <Footer />
      </div>
    </Router>
  );
}

export default App;

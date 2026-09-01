import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import ResultCard from '../components/ResultCard';
import LoadingSpinner from '../components/LoadingSpinner';
import apiService from '../services/api';

export const ResultsPage = () => {
  const { id } = useParams();
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchDetails = async () => {
      setLoading(true);
      try {
        if (id) {
          const data = await apiService.getVerificationDetails(id);
          setResult(data);
        }
      } catch (err) {
        setError(err.message || 'This verification record could not be loaded.');
      } finally {
        setLoading(false);
      }
    };
    fetchDetails();
  }, [id]);

  return (
    <div>
      <Link to="/history" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem', color: '#818cf8', marginBottom: '1.5rem', textDecoration: 'none' }}>
        <ArrowLeft size={16} /> Back to History
      </Link>

      <h1>Verification <span className="gradient-text">Report Details</span></h1>

      {loading ? (
        <LoadingSpinner label="Loading Verification Result Details..." />
      ) : error ? (
        <div className="alert-box warning">{error}</div>
      ) : (
        <ResultCard result={result} onDownloadReport={(vid) => window.open(apiService.getReportPdfUrl(vid))} />
      )}
    </div>
  );
};

export default ResultsPage;

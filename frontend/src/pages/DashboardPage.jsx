import React, { useState, useEffect, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  ShieldCheck, ShieldAlert, FileText, CheckCircle2, AlertTriangle,
  RefreshCw, Image as ImageIcon, Video as VideoIcon, Mic, UserCheck,
  AlertCircle
} from 'lucide-react';
import RiskBadge from '../components/RiskBadge';
import StatCard from '../components/StatCard';
import apiService from '../services/api';

/** Format an ISO timestamp into a short local date-time string. */
function fmtTs(iso) {
  if (!iso) return '—';
  try {
    return new Date(iso).toLocaleString(undefined, {
      dateStyle: 'short',
      timeStyle: 'short',
    });
  } catch {
    return iso;
  }
}

/** Human-readable label for a verification type. */
const TYPE_LABELS = {
  IMAGE: 'Image Scan',
  VIDEO: 'Video Scan',
  AUDIO: 'Audio Scan',
  DIGITAL_IDENTITY: 'Identity Check',
};

export const DashboardPage = () => {
  const navigate = useNavigate();

  const [stats, setStats] = useState({
    total: 0,
    low_risk: 0,
    medium_risk: 0,
    high_risk: 0,
    by_type: { IMAGE: 0, VIDEO: 0, AUDIO: 0, DIGITAL_IDENTITY: 0 },
  });
  const [recentHistory, setRecentHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchDashboardData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [statsData, historyData] = await Promise.all([
        apiService.getStats(),
        apiService.getHistory({ limit: 8 }),
      ]);

      if (statsData) {
        setStats({
          total: statsData.by_type
            ? Object.values(statsData.by_type).reduce((a, b) => a + b, 0)
            : 0,
          low_risk: statsData.by_risk_level?.LOW ?? 0,
          medium_risk: statsData.by_risk_level?.MEDIUM ?? 0,
          high_risk: statsData.by_risk_level?.HIGH ?? 0,
          by_type: {
            IMAGE: statsData.by_type?.IMAGE ?? 0,
            VIDEO: statsData.by_type?.VIDEO ?? 0,
            AUDIO: statsData.by_type?.AUDIO ?? 0,
            DIGITAL_IDENTITY: statsData.by_type?.DIGITAL_IDENTITY ?? 0,
          },
        });
      }

      if (historyData?.history) {
        setRecentHistory(historyData.history.slice(0, 8));
      }
    } catch (err) {
      setError(
        'Unable to load dashboard data. Make sure the backend server is running on port 8000.'
      );
      console.error('Dashboard fetch error:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);

  return (
    <div>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1>Verification <span className="gradient-text">Dashboard</span></h1>
          <p className="subtext">Live overview of all media scans and identity verifications</p>
        </div>
        <button className="btn btn-secondary" onClick={fetchDashboardData} disabled={loading} id="dashboard-refresh-btn">
          <RefreshCw size={16} className={loading ? 'spinner' : ''} /> Refresh
        </button>
      </div>

      {/* Error banner */}
      {error && (
        <div className="alert-box warning" style={{ marginBottom: '1.5rem' }}>
          <AlertCircle size={20} />
          <span>{error}</span>
        </div>
      )}

      {/* Primary Stats Row */}
      <div className="grid-4" style={{ marginBottom: '1.5rem' }}>
        <StatCard
          title="Total Scans"
          value={stats.total}
          icon={FileText}
          color="#818cf8"
          subtitle="All verification types"
        />
        <StatCard
          title="Low Risk / Verified"
          value={stats.low_risk}
          icon={CheckCircle2}
          color="#10b981"
          subtitle="Passed all forensic checks"
        />
        <StatCard
          title="Medium Risk"
          value={stats.medium_risk}
          icon={AlertTriangle}
          color="#f59e0b"
          subtitle="Manual review recommended"
        />
        <StatCard
          title="High Risk Alerts"
          value={stats.high_risk}
          icon={ShieldAlert}
          color="#ef4444"
          subtitle="Suspicious or unverified"
        />
      </div>

      {/* Per-Type Breakdown */}
      <div className="grid-4" style={{ marginBottom: '2.5rem' }}>
        <StatCard
          title="Image Scans"
          value={stats.by_type.IMAGE}
          icon={ImageIcon}
          color="#818cf8"
          subtitle="ELA + FFT forensics"
        />
        <StatCard
          title="Video Scans"
          value={stats.by_type.VIDEO}
          icon={VideoIcon}
          color="#22d3ee"
          subtitle="Frame sampling analysis"
        />
        <StatCard
          title="Audio Scans"
          value={stats.by_type.AUDIO}
          icon={Mic}
          color="#a78bfa"
          subtitle="Spectral + waveform checks"
        />
        <StatCard
          title="Identity Checks"
          value={stats.by_type.DIGITAL_IDENTITY}
          icon={UserCheck}
          color="#34d399"
          subtitle="ELA + face + liveness"
        />
      </div>

      {/* Recent Activity Table */}
      <div className="glass-card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h3>Recent Verification Audits</h3>
          <Link to="/history" style={{ color: '#818cf8', fontSize: '0.9rem', textDecoration: 'none' }}>
            View Full Audit Log →
          </Link>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>Verification ID</th>
                <th>Type</th>
                <th>Result</th>
                <th>Confidence</th>
                <th>Risk</th>
                <th>Timestamp</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {recentHistory.map((row) => (
                <tr
                  key={row.verification_id}
                  style={{ cursor: 'pointer' }}
                  onClick={() => navigate(`/results/${row.verification_id}`)}
                >
                  <td style={{ fontWeight: 600, color: '#818cf8' }}>{row.verification_id}</td>
                  <td>{TYPE_LABELS[row.verification_type] || row.verification_type}</td>
                  <td style={{ fontWeight: 600 }}>{row.result}</td>
                  <td>{(row.confidence * 100).toFixed(0)}%</td>
                  <td><RiskBadge level={row.risk_level} score={row.risk_score} /></td>
                  <td style={{ color: 'var(--text-subtle)', fontSize: '0.85rem' }}>
                    {fmtTs(row.timestamp)}
                  </td>
                  <td onClick={(e) => e.stopPropagation()}>
                    <Link
                      to={`/results/${row.verification_id}`}
                      className="btn btn-secondary"
                      style={{ padding: '0.3rem 0.6rem', fontSize: '0.8rem' }}
                    >
                      Details
                    </Link>
                  </td>
                </tr>
              ))}
              {!recentHistory.length && !loading && (
                <tr>
                  <td colSpan="7" style={{ textAlign: 'center', padding: '2.5rem', color: 'var(--text-subtle)' }}>
                    No scans yet. Upload an image, video, audio file, or ID document to create the first record.
                  </td>
                </tr>
              )}
              {loading && (
                <tr>
                  <td colSpan="7" style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-subtle)' }}>
                    Loading...
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;

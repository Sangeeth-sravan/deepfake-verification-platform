import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { Search, Filter, Download, ExternalLink, AlertCircle, RefreshCw } from 'lucide-react';
import RiskBadge from '../components/RiskBadge';
import apiService from '../services/api';

/** Format ISO timestamp to short locale string. */
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

const TYPE_OPTIONS = [
  { value: 'ALL', label: 'All Verification Types' },
  { value: 'IMAGE', label: 'Image Scans' },
  { value: 'VIDEO', label: 'Video Scans' },
  { value: 'AUDIO', label: 'Audio Scans' },
  { value: 'DIGITAL_IDENTITY', label: 'Identity Checks' },
];

const RISK_OPTIONS = [
  { value: 'ALL', label: 'All Risk Levels' },
  { value: 'LOW', label: 'Low Risk' },
  { value: 'MEDIUM', label: 'Medium Risk' },
  { value: 'HIGH', label: 'High Risk' },
];

export const HistoryPage = () => {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('ALL');
  const [filterRisk, setFilterRisk] = useState('ALL');

  const fetchHistory = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = { limit: 200 };
      if (filterType !== 'ALL') params.verification_type = filterType;
      if (filterRisk !== 'ALL') params.risk_level = filterRisk;
      const data = await apiService.getHistory(params);
      if (data?.history) {
        setHistory(data.history);
      }
    } catch (err) {
      setError(
        err?.message ||
        'Unable to load verification history. Make sure the backend server is running.'
      );
    } finally {
      setLoading(false);
    }
  }, [filterType, filterRisk]);

  useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);

  // Client-side search on top of server-side type + risk filters
  const filteredHistory = history.filter((item) => {
    if (!searchTerm) return true;
    const q = searchTerm.toLowerCase();
    return (
      item.verification_id.toLowerCase().includes(q) ||
      item.result.toLowerCase().includes(q) ||
      (item.filename || '').toLowerCase().includes(q)
    );
  });

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1>Verification <span className="gradient-text">Audit History</span></h1>
          <p className="subtext">Search and inspect all historical media scans and identity checks.</p>
        </div>
        <button
          className="btn btn-secondary"
          onClick={fetchHistory}
          disabled={loading}
          id="history-refresh-btn"
        >
          <RefreshCw size={16} className={loading ? 'spinner' : ''} /> Refresh
        </button>
      </div>

      {error && (
        <div className="alert-box warning" style={{ marginBottom: '1.5rem' }}>
          <AlertCircle size={20} />
          <span>{error}</span>
        </div>
      )}

      {/* Filter and Search Bar */}
      <div className="glass-card" style={{ marginBottom: '1.5rem', display: 'flex', gap: '0.75rem', flexWrap: 'wrap', alignItems: 'center' }}>
        {/* Search */}
        <div style={{ flex: 1, minWidth: '220px', display: 'flex', alignItems: 'center', background: 'rgba(255,255,255,0.05)', padding: '0.6rem 1rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--glass-border)' }}>
          <Search size={18} color="var(--text-subtle)" style={{ marginRight: '0.5rem', flexShrink: 0 }} />
          <input
            id="history-search"
            type="text"
            placeholder="Search by ID, result, or filename..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{ background: 'transparent', border: 'none', color: 'var(--text-main)', outline: 'none', width: '100%', fontSize: '0.9rem' }}
          />
        </div>

        {/* Type filter */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Filter size={16} color="var(--text-subtle)" />
          <select
            id="history-type-filter"
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            style={{ background: 'rgba(20,27,42,0.95)', color: 'var(--text-main)', border: '1px solid var(--glass-border)', padding: '0.6rem 0.9rem', borderRadius: 'var(--radius-sm)', outline: 'none', cursor: 'pointer', fontSize: '0.88rem' }}
          >
            {TYPE_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </div>

        {/* Risk level filter */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <select
            id="history-risk-filter"
            value={filterRisk}
            onChange={(e) => setFilterRisk(e.target.value)}
            style={{ background: 'rgba(20,27,42,0.95)', color: 'var(--text-main)', border: '1px solid var(--glass-border)', padding: '0.6rem 0.9rem', borderRadius: 'var(--radius-sm)', outline: 'none', cursor: 'pointer', fontSize: '0.88rem' }}
          >
            {RISK_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </div>

        <span style={{ color: 'var(--text-subtle)', fontSize: '0.85rem', marginLeft: 'auto' }}>
          {filteredHistory.length} record{filteredHistory.length !== 1 ? 's' : ''}
        </span>
      </div>

      {/* Audit History Table */}
      <div className="glass-card">
        <div style={{ overflowX: 'auto' }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>Verification ID</th>
                <th>Type</th>
                <th>Result</th>
                <th>Confidence</th>
                <th>Risk Rating</th>
                <th>File</th>
                <th>Timestamp</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="8" style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-subtle)' }}>
                    Loading records…
                  </td>
                </tr>
              ) : filteredHistory.length > 0 ? (
                filteredHistory.map((row) => (
                  <tr key={row.verification_id}>
                    <td style={{ fontWeight: 600, color: '#818cf8', fontFamily: 'monospace' }}>{row.verification_id}</td>
                    <td>
                      <span style={{
                        fontSize: '0.78rem',
                        fontWeight: 700,
                        padding: '0.2rem 0.55rem',
                        borderRadius: '12px',
                        background: row.verification_type === 'DIGITAL_IDENTITY'
                          ? 'rgba(52,211,153,0.12)'
                          : row.verification_type === 'AUDIO'
                            ? 'rgba(167,139,250,0.12)'
                            : row.verification_type === 'VIDEO'
                              ? 'rgba(34,211,238,0.12)'
                              : 'rgba(129,140,248,0.12)',
                        color: row.verification_type === 'DIGITAL_IDENTITY'
                          ? '#34d399'
                          : row.verification_type === 'AUDIO'
                            ? '#a78bfa'
                            : row.verification_type === 'VIDEO'
                              ? '#22d3ee'
                              : '#818cf8',
                      }}>
                        {row.verification_type}
                      </span>
                    </td>
                    <td style={{ fontWeight: 600 }}>{row.result}</td>
                    <td>{(row.confidence * 100).toFixed(0)}%</td>
                    <td><RiskBadge level={row.risk_level} score={row.risk_score} /></td>
                    <td style={{ color: 'var(--text-subtle)', fontSize: '0.82rem', maxWidth: '140px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {row.filename || '—'}
                    </td>
                    <td style={{ color: 'var(--text-subtle)', fontSize: '0.82rem', whiteSpace: 'nowrap' }}>
                      {fmtTs(row.timestamp)}
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: '0.4rem' }}>
                        <Link
                          to={`/results/${row.verification_id}`}
                          className="btn btn-secondary"
                          style={{ padding: '0.3rem 0.6rem', fontSize: '0.78rem' }}
                        >
                          <ExternalLink size={13} /> Details
                        </Link>
                        <a
                          href={apiService.getReportPdfUrl(row.verification_id)}
                          target="_blank"
                          rel="noreferrer"
                          className="btn btn-secondary"
                          style={{ padding: '0.3rem 0.6rem', fontSize: '0.78rem' }}
                        >
                          <Download size={13} /> PDF
                        </a>
                      </div>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="8" style={{ textAlign: 'center', padding: '2.5rem', color: 'var(--text-subtle)' }}>
                    No records matched your filter criteria.
                    {(filterType !== 'ALL' || filterRisk !== 'ALL' || searchTerm) && (
                      <button
                        onClick={() => { setFilterType('ALL'); setFilterRisk('ALL'); setSearchTerm(''); }}
                        style={{ marginLeft: '0.75rem', background: 'none', border: 'none', color: '#818cf8', cursor: 'pointer', textDecoration: 'underline', fontSize: '0.9rem' }}
                      >
                        Clear filters
                      </button>
                    )}
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

export default HistoryPage;

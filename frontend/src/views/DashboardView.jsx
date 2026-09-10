/**
 * ROLE: Page View: searchable request dashboard
 * CALLED BY: App for /dashboard and /requests alias
 * CALLS: api.listRequests, AppLink, StatusBadge and formatting helper
 * DATA IN: Up to 100 latest request DTOs; local search/filter state
 * DATA OUT: Summary counts and filtered table
 * WHY: Keep page display/search separate from backend persistence.
 * SECURITY / RELIABILITY: Counts/search cover the loaded 100 records, not necessarily the
 *     entire database. Loads on entry and manual refresh; no automatic dashboard polling.
 *     User data is rendered as text.
 * FLOW: App for /dashboard and /requests alias -> this module -> api.listRequests, AppLink,
 *     StatusBadge and formatting helper
 */

import { useCallback, useEffect, useMemo, useState } from 'react';
import AppLink from '../components/AppLink.jsx';
import StatusBadge from '../components/StatusBadge.jsx';
import { formatDateTime } from '../helpers/formatting.js';
import './requests.css';

function isClosed(record) {
  return ['solved', 'closed'].includes((record.status || '').toLowerCase());
}

function matchesQuery(record, query) {
  if (!query) return true;
  const values = [
    record.id,
    record.requester_name,
    record.requester_email,
    record.asset_type,
    record.status,
    record.zendesk_ticket_id,
    record.zendesk_status,
    record.zendesk_sync_status,
  ];
  return values.some((value) =>
    String(value ?? '')
      .toLowerCase()
      .includes(query),
  );
}

export default function DashboardView({ api, navigate }) {
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');
  const [query, setQuery] = useState('');
  const [filter, setFilter] = useState('all');

  const load = useCallback(
    async ({ quiet = false } = {}) => {
      if (quiet) setRefreshing(true);
      else setLoading(true);
      setError('');
      try {
        // services/api.js reads request_controller.py; these local request DTOs drive display/filtering, not Zendesk calls.
        setRecords(await api.listRequests(100, 0));
      } catch (problem) {
        setError(problem.message);
      } finally {
        if (quiet) setRefreshing(false);
        else setLoading(false);
      }
    },
    [api],
  );

  useEffect(() => {
    load();
  }, [load]);

  const summary = useMemo(() => {
    const active = records.filter((record) => !isClosed(record)).length;
    const linked = records.filter((record) => record.zendesk_ticket_id).length;
    const attention = records.filter(
      (record) => record.zendesk_sync_status === 'sync_failed',
    ).length;
    return { total: records.length, active, linked, attention };
  }, [records]);

  const filteredRecords = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    return records.filter((record) => {
      const filterMatch =
        filter === 'all' ||
        (filter === 'active' && !isClosed(record)) ||
        (filter === 'sync_failed' && record.zendesk_sync_status === 'sync_failed') ||
        (filter === 'solved' && isClosed(record));
      return filterMatch && matchesQuery(record, normalizedQuery);
    });
  }, [records, query, filter]);

  return (
    <>
      <header className="page-heading queue-heading">
        <div>
          <p className="eyebrow">SERVICE DESK</p>
          <h1>IT Service Desk Dashboard</h1>
          <p>
            Monitor requests, linked Zendesk tickets and integration errors from one
            place. Search by request, requester, asset or Zendesk ticket number.
          </p>
        </div>
        <button
          type="button"
          className="button secondary"
          onClick={() => load({ quiet: true })}
          disabled={refreshing}
        >
          {refreshing ? 'Refreshing…' : 'Refresh dashboard'}
        </button>
      </header>

      <section className="queue-summary" aria-label="Dashboard summary">
        <div className="queue-stat">
          <span>Total requests</span>
          <strong>{summary.total}</strong>
        </div>
        <div className="queue-stat">
          <span>Active</span>
          <strong>{summary.active}</strong>
        </div>
        <div className="queue-stat">
          <span>Zendesk linked</span>
          <strong>{summary.linked}</strong>
        </div>
        <div className={`queue-stat ${summary.attention ? 'attention' : ''}`}>
          <span>Sync errors</span>
          <strong>{summary.attention}</strong>
        </div>
      </section>

      {summary.attention > 0 && (
        <p className="notice error dashboard-alert" role="status">
          {summary.attention} request{summary.attention === 1 ? '' : 's'} need sync
          attention. Use the Sync errors filter to isolate them.
        </p>
      )}

      <section className="panel queue-panel">
        <div className="panel-heading queue-panel-heading">
          <div>
            <h2>Requests</h2>
            <p className="muted">
              PostgreSQL is the local system of record. Open any row to inspect the full
              request and its Zendesk synchronisation path.
            </p>
          </div>
          <AppLink className="button primary" to="/request" navigate={navigate}>
            ＋ New request
          </AppLink>
        </div>

        <div className="dashboard-controls">
          <div className="dashboard-search">
            <label htmlFor="request-search">Search requests</label>
            <input
              id="request-search"
              type="search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Request ID, name, email, asset or Zendesk ticket"
            />
          </div>
          <div className="dashboard-filter">
            <label htmlFor="request-filter">Show</label>
            <select
              id="request-filter"
              value={filter}
              onChange={(event) => setFilter(event.target.value)}
            >
              <option value="all">All requests</option>
              <option value="active">Active requests</option>
              <option value="sync_failed">Sync errors</option>
              <option value="solved">Solved / closed</option>
            </select>
          </div>
          <span className="dashboard-result-count">
            {filteredRecords.length} of {records.length} shown
          </span>
        </div>

        {loading ? (
          <p className="queue-state muted" role="status">
            Loading requests…
          </p>
        ) : error ? (
          <div className="queue-state">
            <p className="notice error" role="alert">
              {error}
            </p>
            <button className="button secondary" onClick={() => load()}>
              Try again
            </button>
          </div>
        ) : records.length === 0 ? (
          <div className="queue-empty">
            <strong>No requests yet.</strong>
            <p>Create the first asset request and it will appear here.</p>
          </div>
        ) : filteredRecords.length === 0 ? (
          <div className="queue-empty">
            <strong>No requests match this search.</strong>
            <p>Clear the search or change the filter to see more requests.</p>
          </div>
        ) : (
          <div className="queue-table-wrap">
            <table className="queue-table">
              <thead>
                <tr>
                  <th>Request</th>
                  <th>Requester</th>
                  <th>Asset</th>
                  <th>Portal status</th>
                  <th>Zendesk ticket</th>
                  <th>Sync</th>
                  <th>Updated</th>
                  <th aria-label="Open request" />
                </tr>
              </thead>
              <tbody>
                {filteredRecords.map((record) => (
                  <tr
                    key={record.id}
                    className={
                      record.zendesk_sync_status === 'sync_failed'
                        ? 'queue-row-attention'
                        : ''
                    }
                  >
                    <td>
                      <AppLink
                        className="queue-request-link"
                        to={`/requests/${record.id}`}
                        navigate={navigate}
                      >
                        #{record.id}
                      </AppLink>
                    </td>
                    <td>
                      <strong>{record.requester_name}</strong>
                      <small>{record.requester_email}</small>
                    </td>
                    <td>{record.asset_type}</td>
                    <td>
                      <StatusBadge status={record.status} />
                    </td>
                    <td>
                      {record.zendesk_ticket_id ? (
                        <span className="ticket-reference">
                          #{record.zendesk_ticket_id}
                          <small>{record.zendesk_status || 'linked'}</small>
                        </span>
                      ) : (
                        <span className="muted">Pending</span>
                      )}
                    </td>
                    <td>
                      <StatusBadge status={record.zendesk_sync_status} />
                    </td>
                    <td>{formatDateTime(record.updated_at)}</td>
                    <td className="queue-open-cell">
                      <AppLink
                        className="queue-open-link"
                        to={`/requests/${record.id}`}
                        navigate={navigate}
                        aria-label={`Open request ${record.id}`}
                      >
                        View →
                      </AppLink>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </>
  );
}

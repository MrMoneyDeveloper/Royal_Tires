import { useCallback, useEffect, useMemo, useState } from 'react';
import AppLink from '../components/AppLink.jsx';
import StatusBadge from '../components/StatusBadge.jsx';

function formatDate(value) {
  return value
    ? new Date(value).toLocaleString(undefined, {
        dateStyle: 'medium',
        timeStyle: 'short',
      })
    : '—';
}

export default function RequestsView({ api, navigate }) {
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');

  const load = useCallback(
    async ({ quiet = false } = {}) => {
      if (quiet) setRefreshing(true);
      else setLoading(true);
      setError('');
      try {
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
    const active = records.filter(
      (record) => !['solved', 'closed'].includes(record.status),
    ).length;
    const linked = records.filter((record) => record.zendesk_ticket_id).length;
    const attention = records.filter(
      (record) => record.zendesk_sync_status === 'sync_failed',
    ).length;
    return { total: records.length, active, linked, attention };
  }, [records]);

  return (
    <>
      <header className="page-heading queue-heading">
        <div>
          <p className="eyebrow">SERVICE DESK</p>
          <h1>Request queue</h1>
          <p>
            See every request stored in the portal and the Zendesk ticket currently
            linked to it.
          </p>
        </div>
        <button
          type="button"
          className="button secondary"
          onClick={() => load({ quiet: true })}
          disabled={refreshing}
        >
          {refreshing ? 'Refreshing…' : 'Refresh queue'}
        </button>
      </header>

      <section className="queue-summary" aria-label="Request queue summary">
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
          <span>Sync attention</span>
          <strong>{summary.attention}</strong>
        </div>
      </section>

      <section className="panel queue-panel">
        <div className="panel-heading queue-panel-heading">
          <div>
            <h2>Incoming asset requests</h2>
            <p className="muted">
              PostgreSQL is the local system of record. Zendesk linkage and sync state
              are shown alongside each request.
            </p>
          </div>
          <AppLink className="button primary" to="/request" navigate={navigate}>
            ＋ New request
          </AppLink>
        </div>

        {loading ? (
          <p className="muted" role="status">
            Loading requests…
          </p>
        ) : error ? (
          <div>
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
                </tr>
              </thead>
              <tbody>
                {records.map((record) => (
                  <tr key={record.id}>
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
                    <td>{formatDate(record.updated_at)}</td>
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

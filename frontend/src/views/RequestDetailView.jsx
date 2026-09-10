import { useCallback, useEffect, useState } from 'react';
import AppLink from '../components/AppLink.jsx';
import StatusBadge from '../components/StatusBadge.jsx';

export function formatDate(value) {
  return value
    ? new Date(value).toLocaleString(undefined, {
        dateStyle: 'medium',
        timeStyle: 'short',
      })
    : 'Not yet synced';
}

export default function RequestDetailView({ id, api, navigate }) {
  const [record, setRecord] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchRecord = useCallback(
    async ({ quiet = false } = {}) => {
      if (quiet) setRefreshing(true);
      else setLoading(true);
      setError('');
      try {
        setRecord(await api.getRequest(id));
      } catch (problem) {
        setError(
          problem.status === 404
            ? 'This request could not be found. Check the request number and try again.'
            : problem.message,
        );
      } finally {
        if (quiet) setRefreshing(false);
        else setLoading(false);
      }
    },
    [id, api],
  );

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError('');
    api
      .getRequest(id)
      .then((value) => {
        if (active) setRecord(value);
      })
      .catch((problem) => {
        if (active)
          setError(
            problem.status === 404
              ? 'This request could not be found. Check the request number and try again.'
              : problem.message,
          );
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    // Once Zendesk is linked, silently refresh so a status change made by an
    // agent appears on the tracking page without a browser reload.
    const timer = window.setInterval(() => {
      if (active) {
        api.getRequest(id).then((value) => {
          if (active) setRecord(value);
        }).catch(() => {});
      }
    }, 10000);

    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, [id, api]);

  return (
    <>
      <AppLink
        className="text-link back-link"
        to="/request"
        navigate={navigate}
      >
        ← Back to new request
      </AppLink>
      <header className="page-heading">
        <p className="eyebrow">REQUEST TRACKING</p>
        <h1>Request #{id}</h1>
        <p>Your equipment request and its latest progress.</p>
      </header>
      {loading ? (
        <div className="panel" role="status">
          Loading request…
        </div>
      ) : error ? (
        <div className="panel">
          <p className="notice error" role="alert">
            {error}
          </p>
          <button
            className="button secondary"
            onClick={() => fetchRecord()}
          >
            Try again
          </button>
        </div>
      ) : (
        record && (
          <div className="detail-layout">
            <section className="panel">
              <div className="panel-heading">
                <h2>{record.asset_type} request</h2>
                <StatusBadge status={record.status} />
              </div>
              <dl className="detail-grid">
                <div>
                  <dt>Requester</dt>
                  <dd>{record.requester_name}</dd>
                </div>
                <div>
                  <dt>Email</dt>
                  <dd>{record.requester_email}</dd>
                </div>
                <div>
                  <dt>Created</dt>
                  <dd>{formatDate(record.created_at)}</dd>
                </div>
                <div>
                  <dt>Last updated</dt>
                  <dd>{formatDate(record.updated_at)}</dd>
                </div>
              </dl>
              <div className="reason-block">
                <h3>Business reason</h3>
                <p>{record.reason}</p>
              </div>
            </section>
            <section className="panel">
              <p className="eyebrow">HELPDESK CONNECTION</p>
              <div className="panel-heading">
                <h2>Zendesk synchronisation</h2>
                <button
                  type="button"
                  className="button secondary"
                  onClick={() => fetchRecord({ quiet: true })}
                  disabled={refreshing}
                >
                  {refreshing ? 'Refreshing…' : 'Refresh status'}
                </button>
              </div>
              <dl className="stacked-details">
                <div>
                  <dt>Ticket</dt>
                  <dd>
                    {record.zendesk_ticket_id
                      ? `#${record.zendesk_ticket_id}`
                      : 'Awaiting ticket creation'}
                  </dd>
                </div>
                <div>
                  <dt>Zendesk status</dt>
                  <dd>
                    <StatusBadge status={record.zendesk_status} />
                  </dd>
                </div>
                <div>
                  <dt>Sync state</dt>
                  <dd>
                    <StatusBadge status={record.zendesk_sync_status} />
                  </dd>
                </div>
                <div>
                  <dt>Last successful sync</dt>
                  <dd>{formatDate(record.zendesk_last_synced_at)}</dd>
                </div>
              </dl>
              {record.zendesk_ticket_id ? (
                <p className="muted">
                  Zendesk status changes are pushed back to this portal. This page also
                  checks for fresh data every 10 seconds while it is open.
                </p>
              ) : (
                <p className="muted">
                  Your request is saved. Ticket creation is pending.
                </p>
              )}
            </section>
          </div>
        )
      )}
    </>
  );
}

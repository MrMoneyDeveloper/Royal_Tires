import { useCallback, useEffect, useState } from 'react';
import AppLink from '../components/AppLink.jsx';
import StatusBadge from '../components/StatusBadge.jsx';
import SyncStatePanel from '../components/SyncStatePanel.jsx';

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

    // The browser only polls our API. Zendesk status itself arrives through the
    // authenticated server-side webhook and is persisted before this view reads it.
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
        to="/requests"
        navigate={navigate}
      >
        ← Back to request queue
      </AppLink>
      <header className="page-heading">
        <p className="eyebrow">REQUEST TRACKING</p>
        <h1>Request #{id}</h1>
        <p>Your equipment request, Zendesk link and latest synchronized status.</p>
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
          <button className="button secondary" onClick={() => fetchRecord()}>
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
            <SyncStatePanel
              record={record}
              refreshing={refreshing}
              onRefresh={() => fetchRecord({ quiet: true })}
            />
          </div>
        )
      )}
    </>
  );
}

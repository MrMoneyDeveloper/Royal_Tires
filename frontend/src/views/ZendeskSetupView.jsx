import { useEffect, useState } from 'react';
import './zendesk-setup.css';

export default function ZendeskSetupView({ api }) {
  const [setup, setSetup] = useState(null);
  const [loading, setLoading] = useState(true);
  const [connecting, setConnecting] = useState(false);
  const [applying, setApplying] = useState(false);
  const [confirmed, setConfirmed] = useState(false);
  const [error, setError] = useState('');

  async function load() {
    setLoading(true);
    setConfirmed(false);
    setError('');
    try {
      setSetup(await api.getZendeskSetup());
    } catch (problem) {
      setError(problem.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function connect() {
    setConnecting(true);
    setConfirmed(false);
    setError('');
    try {
      setSetup(await api.connectZendesk());
    } catch (problem) {
      setError(problem.message);
    } finally {
      setConnecting(false);
    }
  }

  async function applyConfiguration() {
    if (!confirmed || !setup?.plan_fingerprint) return;
    setApplying(true);
    setError('');
    try {
      setSetup(await api.applyZendeskSetup(setup.plan_fingerprint));
      setConfirmed(false);
    } catch (problem) {
      setError(problem.message);
      if (problem.status === 409) setConfirmed(false);
    } finally {
      setApplying(false);
    }
  }

  const plan = setup?.plan ?? [];
  const verification = setup?.verification ?? [];

  return (
    <>
      <div className="page-heading">
        <p className="eyebrow">INTEGRATION SETUP</p>
        <h1>Zendesk configuration</h1>
        <p>
          Credentials stay in the Render backend environment. Test the connection,
          inspect the live Zendesk configuration, then approve only the exact plan shown.
        </p>
      </div>

      {error && (
        <p className="notice error" role="alert">
          {error}
        </p>
      )}

      <div className="zendesk-setup-grid">
        <section className="panel">
          <div className="zendesk-panel-heading">
            <div>
              <p className="eyebrow">01 · CONNECTION</p>
              <h2>Backend environment</h2>
            </div>
            <span className={`setup-chip ${setup?.connected ? 'ok' : ''}`}>
              {setup?.connected ? 'Connected' : 'Not connected'}
            </span>
          </div>

          <p className="muted setup-copy">
            Zendesk domain, API email and API token are configured server-side in
            Render. The browser never receives or stores the Zendesk API token.
          </p>

          <div className="connection-summary" aria-live="polite">
            <strong>
              {setup?.environment_configured
                ? 'Zendesk environment variables detected'
                : 'Zendesk environment variables missing'}
            </strong>
            <span>ZENDESK_SUBDOMAIN</span>
            <span>ZENDESK_EMAIL</span>
            <span>ZENDESK_API_TOKEN · hidden server-side</span>
          </div>

          <div className="action-row">
            <button
              type="button"
              className="button primary"
              disabled={connecting || !setup?.environment_configured}
              onClick={connect}
            >
              {connecting ? 'Testing environment connection…' : 'Test environment connection'}
              <span aria-hidden="true">→</span>
            </button>
          </div>

          {setup?.connected && (
            <div className="connection-summary" aria-live="polite">
              <strong>{setup.instance}</strong>
              <span>{setup.user?.name || 'Zendesk user'}</span>
              <span>{setup.user?.email}</span>
              <span>Role: {setup.user?.role || 'unknown'}</span>
            </div>
          )}

          {!loading && setup && !setup.environment_configured && (
            <p className="notice error">
              Add ZENDESK_SUBDOMAIN, ZENDESK_EMAIL and ZENDESK_API_TOKEN to the Render
              web service environment, save, and let the backend restart.
            </p>
          )}
        </section>

        <section className="panel">
          <div className="zendesk-panel-heading">
            <div>
              <p className="eyebrow">02 · DRY RUN</p>
              <h2>Configuration plan</h2>
            </div>
            <span className={`setup-chip ${setup?.configured ? 'ok' : ''}`}>
              {setup?.configured ? 'Configured' : 'Review first'}
            </span>
          </div>

          {loading ? (
            <p className="muted">Checking Zendesk setup state…</p>
          ) : !setup?.connected ? (
            <p className="muted">
              Test the environment connection first. That operation is read-only and
              does not create or change Zendesk configuration.
            </p>
          ) : (
            <>
              <p className="notice setup-notice">
                {setup.message ||
                  'This plan is read-only. No Zendesk configuration changes until you confirm below.'}
              </p>

              <div className="plan-list" aria-label="Zendesk configuration plan">
                {plan.map((item) => (
                  <div className="plan-row" key={item.key}>
                    <div>
                      <strong>{item.name}</strong>
                      <span>{item.object_type}</span>
                    </div>
                    <div className="plan-result">
                      <span className={`plan-action ${item.action}`}>
                        {item.action.toUpperCase()}
                      </span>
                      {item.existing_id ? <small>#{item.existing_id}</small> : null}
                    </div>
                  </div>
                ))}
              </div>

              {setup.plan_fingerprint && (
                <p className="muted setup-copy">
                  Reviewed plan ref: <code>{setup.plan_fingerprint.slice(0, 12)}</code>.
                  If Zendesk changes before deployment, the backend refuses the apply
                  and requires a fresh review.
                </p>
              )}

              <label className="confirm-box">
                <input
                  type="checkbox"
                  checked={confirmed}
                  onChange={(event) => setConfirmed(event.target.checked)}
                />
                <span>
                  I reviewed this exact dry-run plan. Create only the missing Royal
                  Tyres configuration and do not delete unrelated Zendesk data.
                </span>
              </label>

              <div className="action-row">
                <button
                  type="button"
                  className="button primary"
                  disabled={
                    applying ||
                    !setup.can_configure ||
                    !setup.plan_fingerprint ||
                    !confirmed
                  }
                  onClick={applyConfiguration}
                >
                  {applying
                    ? 'Applying & verifying…'
                    : setup.configured
                      ? 'Re-apply & verify configuration'
                      : 'Apply configuration'}
                  <span aria-hidden="true">→</span>
                </button>
                <button type="button" className="button secondary" onClick={load}>
                  Refresh plan
                </button>
              </div>

              {!setup.can_configure && (
                <p className="notice error">
                  The configured Zendesk user is not an admin. An admin API identity is
                  required to create brands, groups, fields, forms and views.
                </p>
              )}
            </>
          )}
        </section>
      </div>

      {verification.length > 0 && (
        <section className="panel verification-panel">
          <p className="eyebrow">03 · VERIFY AFTER</p>
          <h2>Zendesk configuration verification</h2>
          <div className="verification-grid">
            {verification.map((item) => (
              <div className="verification-item" key={`${item.object_type}-${item.id}`}>
                <span className={`verify-dot ${item.ok ? 'ok' : ''}`} />
                <div>
                  <strong>{item.object_type}</strong>
                  <small>#{item.id} · {item.result}</small>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}
    </>
  );
}

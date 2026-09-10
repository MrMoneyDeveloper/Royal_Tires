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

  async function connect(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const fields = new FormData(form);
    setConnecting(true);
    setConfirmed(false);
    setError('');
    try {
      const result = await api.connectZendesk({
        subdomain: fields.get('subdomain'),
        email: fields.get('email'),
        api_token: fields.get('api_token'),
      });
      setSetup(result);
      form.elements.api_token.value = '';
    } catch (problem) {
      setError(problem.message);
    } finally {
      setConnecting(false);
    }
  }

  async function applyConfiguration() {
    if (!confirmed) return;
    setApplying(true);
    setError('');
    try {
      setSetup(await api.applyZendeskSetup());
      setConfirmed(false);
    } catch (problem) {
      setError(problem.message);
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
        <h1>Connect Zendesk</h1>
        <p>
          Test the sandbox login, inspect existing configuration, then apply only
          the missing Royal Tyres objects after confirmation.
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
              <h2>Zendesk sandbox login</h2>
            </div>
            <span className={`setup-chip ${setup?.connected ? 'ok' : ''}`}>
              {setup?.connected ? 'Connected' : 'Not connected'}
            </span>
          </div>

          <p className="muted setup-copy">
            The API token is sent to the FastAPI backend over HTTPS, encrypted
            server-side, and never returned to the browser.
          </p>

          <form onSubmit={connect}>
            <div className="field">
              <label htmlFor="zendesk-subdomain">Zendesk domain or subdomain</label>
              <input
                id="zendesk-subdomain"
                name="subdomain"
                placeholder="digify7 or digify7.zendesk.com"
                required
                autoComplete="off"
              />
            </div>
            <div className="field">
              <label htmlFor="zendesk-email">Zendesk admin email</label>
              <input
                id="zendesk-email"
                name="email"
                type="email"
                placeholder="admin@example.com"
                required
                autoComplete="username"
              />
            </div>
            <div className="field">
              <label htmlFor="zendesk-token">API token</label>
              <input
                id="zendesk-token"
                name="api_token"
                type="password"
                placeholder="Paste the active API token"
                required
                autoComplete="new-password"
              />
            </div>
            <button className="button primary" disabled={connecting}>
              {connecting ? 'Testing connection…' : 'Test & connect'}
              <span aria-hidden="true">→</span>
            </button>
          </form>

          {setup?.connected && (
            <div className="connection-summary" aria-live="polite">
              <strong>{setup.instance}</strong>
              <span>{setup.user?.name || 'Zendesk user'}</span>
              <span>{setup.user?.email}</span>
              <span>Role: {setup.user?.role || 'unknown'}</span>
            </div>
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
            <p className="muted">Checking saved Zendesk configuration…</p>
          ) : !setup?.connected ? (
            <p className="muted">
              Connect Zendesk first. Nothing is created or changed during the
              connection test.
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

              {!setup.configured && (
                <label className="confirm-box">
                  <input
                    type="checkbox"
                    checked={confirmed}
                    onChange={(event) => setConfirmed(event.target.checked)}
                  />
                  <span>
                    I reviewed the dry-run plan. Create only the missing Royal
                    Tyres configuration and do not delete unrelated Zendesk data.
                  </span>
                </label>
              )}

              <div className="action-row">
                <button
                  type="button"
                  className="button primary"
                  disabled={
                    applying ||
                    !setup.can_configure ||
                    (!setup.configured && !confirmed)
                  }
                  onClick={applyConfiguration}
                >
                  {applying
                    ? 'Applying & verifying…'
                    : setup.configured
                      ? 'Verify configuration again'
                      : 'Apply configuration'}
                  <span aria-hidden="true">→</span>
                </button>
                <button type="button" className="button secondary" onClick={load}>
                  Refresh plan
                </button>
              </div>

              {!setup.can_configure && (
                <p className="notice error">
                  The connected Zendesk user is not an admin. An admin login is
                  required to create brands, groups, fields and forms.
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

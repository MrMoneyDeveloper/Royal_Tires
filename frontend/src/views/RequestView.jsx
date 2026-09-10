/**
 * ROLE: Page View: create request and show result
 * CALLED BY: App for /request
 * CALLS: AssetRequestForm, api.createRequest, AppLink and StatusBadge
 * DATA IN: Form values and injected api/navigate
 * DATA OUT: Created request summary or error
 * WHY: Own page-level submission state without SQL or Zendesk HTTP logic.
 * SECURITY / RELIABILITY: Renders response text normally. The backend, not this page,
 *     guarantees commit-before-Zendesk.
 * FLOW: App for /request -> this module -> AssetRequestForm, api.createRequest, AppLink and
 *     StatusBadge
 */

import { useState } from 'react';
import AssetRequestForm from '../components/AssetRequestForm.jsx';
import AppLink from '../components/AppLink.jsx';
import StatusBadge from '../components/StatusBadge.jsx';

export default function RequestView({ api, navigate }) {
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [created, setCreated] = useState(null);

  async function submit(values) {
    setSubmitting(true);
    setError('');
    try {
      setCreated(await api.createRequest(values));
    } catch (problem) {
      setError(problem.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <>
      <header className="page-heading">
        <p className="eyebrow">YOUR WORKPLACE, EQUIPPED</p>
        <h1>Request an IT asset</h1>
        <p>Get the equipment you need to do your best work.</p>
      </header>
      <div className="request-layout">
        <section className="panel form-panel">
          {created ? (
            <div className="success-state" role="status">
              <span className="success-mark" aria-hidden="true">
                ✓
              </span>
              <p className="eyebrow">REQUEST #{created.id}</p>
              <h2>You're on the list.</h2>
              <p>Request successfully saved.</p>
              <StatusBadge status={created.status} />
              <p>
                {created.zendesk_ticket_id
                  ? `Zendesk ticket #${created.zendesk_ticket_id} has been created.`
                  : 'Zendesk synchronisation is pending. Your request is safely saved.'}
              </p>
              <div className="action-row">
                <AppLink
                  className="button primary"
                  to={`/requests/${created.id}`}
                  navigate={navigate}
                >
                  Track this request <span aria-hidden="true">→</span>
                </AppLink>
                <button
                  className="button secondary"
                  onClick={() => setCreated(null)}
                >
                  New request
                </button>
              </div>
            </div>
          ) : (
            <AssetRequestForm
              onSubmit={submit}
              submitting={submitting}
              error={error}
            />
          )}
        </section>
        <aside className="request-aside">
          <div className="aside-illustration" aria-hidden="true">
            <svg viewBox="0 0 240 160">
              <rect
                x="35"
                y="24"
                width="170"
                height="108"
                rx="9"
                fill="#dbe9df"
                stroke="#426b58"
                strokeWidth="3"
              />
              <rect
                x="47"
                y="36"
                width="146"
                height="81"
                rx="3"
                fill="#f7faf5"
              />
              <path d="M21 132h198l-13 12H34z" fill="#426b58" />
              <path
                d="m101 74 13 13 27-29"
                fill="none"
                stroke="#426b58"
                strokeWidth="6"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <circle cx="191" cy="36" r="20" fill="#d8ec8e" />
              <path d="M191 27v18m-9-9h18" stroke="#254537" strokeWidth="2" />
            </svg>
          </div>
          <h2>From request to ready.</h2>
          <p>A simple way to keep your equipment needs moving.</p>
          <ol className="process-list">
            <li>
              <strong>Tell us what you need</strong>
              <span>Pick an asset and add your business reason.</span>
            </li>
            <li>
              <strong>IT takes it from here</strong>
              <span>Your request is recorded for the team to review.</span>
            </li>
            <li>
              <strong>Follow its progress</strong>
              <span>Use your request number to check the latest status.</span>
            </li>
          </ol>
          <div className="aside-note">
            Your request stays saved even if the helpdesk connection is
            temporarily unavailable.
          </div>
        </aside>
      </div>
    </>
  );
}

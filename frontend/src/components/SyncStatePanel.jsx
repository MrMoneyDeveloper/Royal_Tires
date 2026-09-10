import StatusBadge from './StatusBadge.jsx';
import { formatDateTime } from '../helpers/formatting.js';
import './sync-state.css';

export default function SyncStatePanel({ record, refreshing, onRefresh }) {
  const linked = Boolean(record.zendesk_ticket_id);
  const failed = record.zendesk_sync_status === 'sync_failed';

  return (
    <section className="panel sync-panel">
      <div className="sync-panel-topline">
        <p className="eyebrow">HELPDESK SYNC</p>
        <StatusBadge status={record.zendesk_sync_status} />
      </div>
      <div className="panel-heading sync-panel-heading">
        <div>
          <h2>
            {linked
              ? `Zendesk ticket #${record.zendesk_ticket_id}`
              : 'Zendesk ticket pending'}
          </h2>
          <p className="muted">
            {linked
              ? 'This portal keeps the local request linked to Zendesk and receives agent status changes through the authenticated webhook.'
              : 'The request is safely stored locally. Zendesk ticket creation has not completed yet.'}
          </p>
        </div>
        <button
          type="button"
          className="button secondary"
          onClick={onRefresh}
          disabled={refreshing}
        >
          {refreshing ? 'Refreshing…' : 'Refresh status'}
        </button>
      </div>

      {failed && (
        <p className="notice error">
          The local request is safe, but the latest Zendesk sync failed. The request can
          be reconciled without recreating the employee request.
        </p>
      )}

      <div className="sync-path" aria-label="Request synchronisation path">
        <div>
          <span>1</span>
          <strong>Portal</strong>
          <small>PostgreSQL record</small>
        </div>
        <b aria-hidden="true">→</b>
        <div>
          <span>2</span>
          <strong>Zendesk</strong>
          <small>
            {linked ? `Ticket #${record.zendesk_ticket_id}` : 'Awaiting link'}
          </small>
        </div>
        <b aria-hidden="true">→</b>
        <div>
          <span>3</span>
          <strong>Status callback</strong>
          <small>Webhook → portal</small>
        </div>
      </div>

      <dl className="sync-details">
        <div>
          <dt>Portal status</dt>
          <dd>
            <StatusBadge status={record.status} />
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
          <dd>
            {formatDateTime(record.zendesk_last_synced_at, 'Not yet synced')}
          </dd>
        </div>
      </dl>

      <p className="sync-footnote">
        {linked
          ? 'The browser only reads the Royal Tyres API. It never connects directly to Zendesk. While this page is open, it also checks the local API every 10 seconds for a fresh webhook-updated status.'
          : 'PostgreSQL remains the primary record even if Zendesk is temporarily unavailable.'}
      </p>
    </section>
  );
}

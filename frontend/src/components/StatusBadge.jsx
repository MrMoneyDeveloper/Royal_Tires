/**
 * ROLE: Reusable component: readable status label
 * CALLED BY: Views and SyncStatePanel
 * CALLS: Local statusLabel helper
 * DATA IN: Status string or missing value
 * DATA OUT: Text badge and CSS class
 * WHY: Present statuses consistently across pages.
 * SECURITY / RELIABILITY: React renders the label as text; missing status has an explicit
 *     fallback.
 * FLOW: Views and SyncStatePanel -> this module -> Local statusLabel helper
 */

export function statusLabel(value) {
  if (!value) return 'Not available';
  return value
    .replaceAll('_', ' ')
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export default function StatusBadge({ status }) {
  return (
    <span className={`status status-${status ?? 'unknown'}`}>
      <span aria-hidden="true" />
      {statusLabel(status)}
    </span>
  );
}

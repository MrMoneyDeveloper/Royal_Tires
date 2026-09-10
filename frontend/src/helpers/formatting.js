/**
 * ROLE: Helper: timestamp display formatting
 * CALLED BY: DashboardView, RequestDetailView and SyncStatePanel
 * CALLS: Date.toLocaleString
 * DATA IN: Timestamp and optional fallback
 * DATA OUT: Localized date/time text
 * WHY: Share formatting without owning page state or HTTP.
 * SECURITY / RELIABILITY: Output depends on browser locale/timezone; it does not change the
 *     stored UTC value.
 * FLOW: DashboardView, RequestDetailView and SyncStatePanel -> this module ->
 *     Date.toLocaleString
 */

export function formatDateTime(value, fallback = '—') {
  return value
    ? new Date(value).toLocaleString(undefined, {
        dateStyle: 'medium',
        timeStyle: 'short',
      })
    : fallback;
}

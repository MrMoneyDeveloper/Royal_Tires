export function formatDateTime(value, fallback = '—') {
  return value
    ? new Date(value).toLocaleString(undefined, {
        dateStyle: 'medium',
        timeStyle: 'short',
      })
    : fallback;
}

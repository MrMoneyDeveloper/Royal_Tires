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

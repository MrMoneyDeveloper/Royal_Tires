export const ASSET_TYPES = [
  'Laptop',
  'Monitor',
  'Mouse',
  'Keyboard',
  'Headset',
  'Docking Station',
  'Other',
];

export function validateRequest(values) {
  const errors = {};
  const name = values.requester_name.trim();
  const email = values.requester_email.trim();
  const reason = values.reason.trim();
  if (name.length < 2 || name.length > 100)
    errors.requester_name = 'Enter a name between 2 and 100 characters.';
  if (email.length > 254 || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email))
    errors.requester_email = 'Enter a valid email address.';
  if (!ASSET_TYPES.includes(values.asset_type))
    errors.asset_type = 'Choose an asset from the list.';
  if (reason.length < 10 || reason.length > 1000)
    errors.reason = 'Explain your request in 10 to 1,000 characters.';
  return errors;
}

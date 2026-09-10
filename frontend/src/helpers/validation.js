/**
 * ROLE: Pure helper: request input checks
 * CALLED BY: AssetRequestForm and unit tests
 * CALLS: String/regex checks only
 * DATA IN: Form values
 * DATA OUT: Field error map and meaningful character count
 * WHY: Keep reusable deterministic checks outside JSX.
 * SECURITY / RELIABILITY: No business workflow or network access. Counts non-whitespace
 *     characters; backend Pydantic remains the authoritative boundary.
 * FLOW: AssetRequestForm and unit tests -> this module -> String/regex checks only
 */

export const ASSET_TYPES = [
  'Laptop',
  'Monitor',
  'Mouse',
  'Keyboard',
  'Headset',
  'Docking Station',
  'Other',
];

export function meaningfulCharacterCount(value = '') {
  return value.replace(/\s/g, '').length;
}

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
  if (meaningfulCharacterCount(reason) < 10 || reason.length > 1000)
    errors.reason =
      'Explain your request using at least 10 non-whitespace characters (maximum 1,000 total).';
  return errors;
}

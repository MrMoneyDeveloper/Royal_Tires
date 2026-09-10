import assert from 'node:assert/strict';
import test from 'node:test';
import {
  meaningfulCharacterCount,
  validateRequest,
} from '../src/helpers/validation.js';

const valid = {
  requester_name: 'Test User',
  requester_email: 'test@example.com',
  asset_type: 'Laptop',
  reason: 'A replacement for development work.',
};

test('accepts a valid request and trimmed input', () => {
  assert.deepEqual(
    validateRequest({ ...valid, reason: `  ${valid.reason} ` }),
    {},
  );
});

test('rejects missing fields, unsupported assets, and invalid email', () => {
  assert.deepEqual(
    Object.keys(
      validateRequest({
        requester_name: '',
        requester_email: 'bad',
        asset_type: 'Server',
        reason: ' ',
      }),
    ),
    ['requester_name', 'requester_email', 'asset_type', 'reason'],
  );
});

test('enforces input length boundaries', () => {
  assert.ok(validateRequest({ ...valid, reason: 'a'.repeat(1001) }).reason);
  assert.ok(
    validateRequest({ ...valid, requester_name: 'a'.repeat(101) })
      .requester_name,
  );
  assert.deepEqual(
    validateRequest({
      ...valid,
      reason: 'a'.repeat(1000),
      requester_name: 'ab',
    }),
    {},
  );
});

test('does not count spaces, tabs, or newlines toward the business reason minimum', () => {
  const padded = 'ab\n\n\n\t   cd\n\n\n\nef';
  assert.equal(meaningfulCharacterCount(padded), 6);
  assert.ok(validateRequest({ ...valid, reason: padded }).reason);
});

test('accepts ten meaningful characters even when formatted across lines', () => {
  const formatted = 'abcde\n\n  fghij';
  assert.equal(meaningfulCharacterCount(formatted), 10);
  assert.deepEqual(validateRequest({ ...valid, reason: formatted }), {});
});

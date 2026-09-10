import assert from 'node:assert/strict';
import test from 'node:test';
import { createApi, ApiError } from '../src/services/api.js';

const credentials = { username: 'test-user', password: 'test-password' };
const options = { baseUrl: 'https://api.example.com/' };

test('requires configured API origin', () => {
  assert.throws(() => createApi(credentials, { baseUrl: '' }), ApiError);
});

test('sends Basic Auth and JSON to configured backend', async (t) => {
  let call;
  t.mock.method(globalThis, 'fetch', async (...args) => {
    call = args;
    return new Response('{"id":7}', { status: 201 });
  });
  assert.deepEqual(
    await createApi(credentials, options).createRequest({
      reason: 'Example reason',
    }),
    { id: 7 },
  );
  assert.equal(call[0], 'https://api.example.com/api/requests');
  assert.equal(
    call[1].headers.Authorization,
    `Basic ${btoa('test-user:test-password')}`,
  );
  assert.equal(JSON.parse(call[1].body).reason, 'Example reason');
});

test('tests Zendesk connection without sending credentials from the browser', async (t) => {
  let call;
  t.mock.method(globalThis, 'fetch', async (...args) => {
    call = args;
    return new Response('{"connected":true}', { status: 200 });
  });

  await createApi(credentials, options).connectZendesk();

  assert.equal(call[0], 'https://api.example.com/api/zendesk/connect');
  assert.equal(call[1].method, 'POST');
  assert.equal(call[1].body, undefined);
});

test('sends the exact reviewed Zendesk plan fingerprint on apply', async (t) => {
  let call;
  t.mock.method(globalThis, 'fetch', async (...args) => {
    call = args;
    return new Response('{"configured":true}', { status: 200 });
  });
  const fingerprint = 'a'.repeat(64);

  await createApi(credentials, options).applyZendeskSetup(fingerprint);

  assert.equal(call[0], 'https://api.example.com/api/zendesk/apply');
  assert.deepEqual(JSON.parse(call[1].body), {
    confirm: true,
    plan_fingerprint: fingerprint,
  });
});

test('reports validation errors and handles revoked authentication', async (t) => {
  t.mock.method(
    globalThis,
    'fetch',
    async () =>
      new Response('{"detail":[{"loc":["body","reason"],"msg":"Too short"}]}', {
        status: 422,
      }),
  );
  await assert.rejects(
    createApi(credentials, options).listRequests(),
    /reason: Too short/,
  );
  let expired = false;
  globalThis.fetch = async () =>
    new Response('{"detail":"Invalid credentials"}', { status: 401 });
  await assert.rejects(
    createApi(credentials, {
      ...options,
      onUnauthorized: () => {
        expired = true;
      },
    }).listRequests(),
    { status: 401 },
  );
  assert.ok(expired);
});

test('network errors offer an actionable message', async (t) => {
  t.mock.method(globalThis, 'fetch', async () => {
    throw new TypeError('Failed to fetch');
  });
  await assert.rejects(
    createApi(credentials, options).listRequests(),
    /Check that the backend is running/,
  );
});

import { test, expect } from '@playwright/test';

const plan = [
  ['brand', 'Brand', 'Royal Tyres'],
  ['group', 'Group', 'Royal Tyres | IT Service Desk'],
  ['asset_type_field', 'Ticket field', 'RT | Asset Type'],
  ['local_request_id_field', 'Ticket field', 'RT | Local Request ID'],
  ['request_source_field', 'Ticket field', 'RT | Request Source'],
  ['ticket_form', 'Ticket form', 'Royal Tyres | IT Asset Request'],
  ['view', 'View', 'Royal Tyres | IT Asset Requests'],
  ['email_target', 'Email target', 'Royal Tyres | Demo Notifications'],
  ['status_webhook', 'Webhook', 'Royal Tyres | Asset Status Sync'],
  ['trigger_new_email', 'Trigger', 'Royal Tyres | Notify Demo Receiver - New Request'],
  ['trigger_status_email', 'Trigger', 'Royal Tyres | Notify Demo Receiver - Status Update'],
  ['trigger_status_sync', 'Trigger', 'Royal Tyres | Sync Status to Asset Portal'],
].map(([key, object_type, name]) => ({
  key,
  object_type,
  name,
  action: 'create',
  existing_id: null,
  details: key === 'email_target' ? 'Receiver: farhaanhotd1@gmail.com' : null,
}));

const planFingerprint = 'a'.repeat(64);
const common = {
  environment_configured: true,
  workflow_environment_ready: true,
  notification_email: 'farhaanhotd1@gmail.com',
};

test('tests env credentials, previews and explicitly applies complete Zendesk workflow', async ({ page }) => {
  let connected = false;
  let configured = false;

  await page.route('http://127.0.0.1:8001/api/**', async (route) => {
    const request = route.request();
    if (request.headers().authorization !== `Basic ${btoa('test-user:test-password')}`) {
      return route.fulfill({ status: 401, json: { detail: 'Invalid credentials' } });
    }

    const url = new URL(request.url());
    if (url.pathname === '/api/requests') return route.fulfill({ json: [] });

    if (url.pathname === '/api/zendesk/setup') {
      return route.fulfill({
        json: connected
          ? {
              ...common,
              connected: true,
              configured,
              can_configure: true,
              instance: 'example.zendesk.com',
              user: { name: 'Admin User', email: 'admin@example.com', role: 'admin' },
              plan,
              plan_fingerprint: planFingerprint,
              ids: null,
              verification: [],
              message: 'Connection verified. Review the complete dry-run plan before applying configuration.',
            }
          : {
              ...common,
              connected: false,
              configured: false,
              can_configure: false,
              instance: null,
              user: null,
              plan: [],
              plan_fingerprint: planFingerprint,
              ids: null,
              verification: [],
              message: 'Zendesk credentials are present in the backend environment. Test the connection to build the dry-run plan.',
            },
      });
    }

    if (url.pathname === '/api/zendesk/connect') {
      connected = true;
      expect(request.postData()).toBeNull();
      return route.fulfill({
        json: {
          ...common,
          connected: true,
          configured: false,
          can_configure: true,
          instance: 'example.zendesk.com',
          user: { name: 'Admin User', email: 'admin@example.com', role: 'admin' },
          plan,
          plan_fingerprint: planFingerprint,
          ids: null,
          verification: [],
          message: 'Connection verified from backend environment variables. Review the complete plan and confirm before any Zendesk configuration is changed.',
        },
      });
    }

    if (url.pathname === '/api/zendesk/apply') {
      configured = true;
      expect(request.postDataJSON()).toEqual({
        confirm: true,
        plan_fingerprint: planFingerprint,
      });
      return route.fulfill({
        json: {
          ...common,
          connected: true,
          configured: true,
          can_configure: true,
          instance: 'example.zendesk.com',
          user: { name: 'Admin User', email: 'admin@example.com', role: 'admin' },
          plan: plan.map((item, index) => ({
            ...item,
            action: 'reuse',
            existing_id: item.object_type === 'Webhook' ? '01TESTWEBHOOK' : 100 + index,
          })),
          plan_fingerprint: 'b'.repeat(64),
          ids: { brand_id: 100, group_id: 101, ticket_form_id: 105, view_id: 106 },
          verification: plan.map((item, index) => ({
            object_type: item.object_type,
            id: item.object_type === 'Webhook' ? '01TESTWEBHOOK' : 100 + index,
            ok: true,
            result: 'PASS',
          })),
          message: 'Zendesk configuration, demo email notifications and Track a request status sync were applied and verified successfully.',
        },
      });
    }

    return route.fulfill({ status: 404, json: { detail: 'Not found' } });
  });

  await page.goto('/zendesk-setup');
  await page.getByLabel('Username', { exact: true }).fill('test-user');
  await page.getByLabel('Password', { exact: true }).fill('test-password');
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();

  await expect(page.getByRole('heading', { name: 'Zendesk configuration' })).toBeVisible();
  await expect(page.getByText('Zendesk environment variables detected')).toBeVisible();
  await page.getByRole('button', { name: /Test environment connection/ }).click();

  await expect(page.getByText('example.zendesk.com')).toBeVisible();
  await expect(page.getByText('Royal Tyres | Demo Notifications')).toBeVisible();
  await expect(page.getByText('Royal Tyres | Asset Status Sync')).toBeVisible();
  await expect(page.getByText('Royal Tyres | Sync Status to Asset Portal')).toBeVisible();
  await expect(page.getByText('Receiver: farhaanhotd1@gmail.com', { exact: true })).toBeVisible();
  await expect(page.getByText('CREATE').first()).toBeVisible();
  await expect(page.getByText(/Reviewed plan ref:/)).toBeVisible();

  await page.getByText(/I reviewed this exact dry-run plan/).click();
  await page.getByRole('button', { name: /Apply configuration/ }).click();

  await expect(
    page.getByRole('heading', { name: 'Zendesk configuration verification' }),
  ).toBeVisible();
  await expect(page.getByText('PASS').first()).toBeVisible();
});

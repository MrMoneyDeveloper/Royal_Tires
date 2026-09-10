import { test, expect } from '@playwright/test';

const plan = [
  ['brand', 'Brand', 'Royal Tyres'],
  ['group', 'Group', 'Royal Tyres | IT Service Desk'],
  ['asset_type_field', 'Ticket field', 'RT | Asset Type'],
  ['local_request_id_field', 'Ticket field', 'RT | Local Request ID'],
  ['request_source_field', 'Ticket field', 'RT | Request Source'],
  ['ticket_form', 'Ticket form', 'Royal Tyres | IT Asset Request'],
  ['view', 'View', 'Royal Tyres | IT Asset Requests'],
].map(([key, object_type, name]) => ({
  key,
  object_type,
  name,
  action: 'create',
  existing_id: null,
}));

test('connects, previews and explicitly applies Zendesk configuration', async ({ page }) => {
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
              connected: true,
              configured,
              can_configure: true,
              instance: 'example.zendesk.com',
              user: { name: 'Admin User', email: 'admin@example.com', role: 'admin' },
              plan,
              ids: null,
              verification: [],
              message: 'Connection verified. Review the dry-run plan before applying configuration.',
            }
          : {
              connected: false,
              configured: false,
              can_configure: false,
              instance: null,
              user: null,
              plan: [],
              ids: null,
              verification: [],
              message: 'Connect a Zendesk sandbox to build the setup plan.',
            },
      });
    }

    if (url.pathname === '/api/zendesk/connect') {
      connected = true;
      expect(request.postDataJSON().api_token).toBe('secret-token');
      return route.fulfill({
        json: {
          connected: true,
          configured: false,
          can_configure: true,
          instance: 'example.zendesk.com',
          user: { name: 'Admin User', email: 'admin@example.com', role: 'admin' },
          plan,
          ids: null,
          verification: [],
          message: 'Connection verified. Review the plan and confirm before any Zendesk configuration is changed.',
        },
      });
    }

    if (url.pathname === '/api/zendesk/apply') {
      configured = true;
      expect(request.postDataJSON()).toEqual({ confirm: true });
      return route.fulfill({
        json: {
          connected: true,
          configured: true,
          can_configure: true,
          instance: 'example.zendesk.com',
          user: { name: 'Admin User', email: 'admin@example.com', role: 'admin' },
          plan: plan.map((item, index) => ({
            ...item,
            action: 'reuse',
            existing_id: 100 + index,
          })),
          ids: { brand_id: 100, group_id: 101, ticket_form_id: 105, view_id: 106 },
          verification: plan.map((item, index) => ({
            object_type: item.object_type,
            id: 100 + index,
            ok: true,
            result: 'PASS',
          })),
          message: 'Zendesk configuration applied and verified successfully.',
        },
      });
    }

    return route.fulfill({ status: 404, json: { detail: 'Not found' } });
  });

  await page.goto('/zendesk-setup');
  await page.getByLabel('Username', { exact: true }).fill('test-user');
  await page.getByLabel('Password', { exact: true }).fill('test-password');
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();

  await expect(page.getByRole('heading', { name: 'Connect Zendesk' })).toBeVisible();
  await page.getByLabel('Zendesk domain or subdomain').fill('example');
  await page.getByLabel('Zendesk admin email').fill('admin@example.com');
  await page.getByLabel('API token').fill('secret-token');
  await page.getByRole('button', { name: /Test & connect/ }).click();

  await expect(page.getByText('example.zendesk.com')).toBeVisible();
  await expect(page.getByText('Royal Tyres | IT Service Desk')).toBeVisible();
  await expect(page.getByText('CREATE').first()).toBeVisible();
  await expect(page.getByLabel('API token')).toHaveValue('');

  await page.getByText(/I reviewed the dry-run plan/).click();
  await page.getByRole('button', { name: /Apply configuration/ }).click();

  await expect(
    page.getByRole('heading', { name: 'Zendesk configuration verification' }),
  ).toBeVisible();
  await expect(page.getByText('PASS').first()).toBeVisible();
});

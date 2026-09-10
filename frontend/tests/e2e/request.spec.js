import { test, expect } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  let saved;
  await page.route('http://127.0.0.1:8001/api/**', async (route) => {
    const request = route.request();
    if (
      request.headers().authorization !==
      `Basic ${btoa('test-user:test-password')}`
    ) {
      return route.fulfill({
        status: 401,
        json: { detail: 'Invalid credentials' },
      });
    }

    const url = new URL(request.url());

    if (url.pathname === '/api/zendesk/setup') {
      return route.fulfill({
        json: {
          environment_configured: true,
          workflow_environment_ready: true,
          notification_email: 'demo@example.com',
          connected: false,
          configured: false,
          can_configure: false,
          instance: null,
          user: null,
          plan: [],
          plan_fingerprint: null,
          ids: null,
          verification: [],
          message: 'Zendesk credentials are present in the backend environment.',
        },
      });
    }

    if (request.method() === 'POST' && url.pathname === '/api/requests') {
      saved = {
        ...request.postDataJSON(),
        id: 27,
        status: 'new',
        zendesk_ticket_id: 54,
        zendesk_status: 'new',
        zendesk_sync_status: 'synced',
        zendesk_last_synced_at: '2026-09-10T10:00:05Z',
        created_at: '2026-09-10T10:00:00Z',
        updated_at: '2026-09-10T10:00:05Z',
      };
      return route.fulfill({ status: 201, json: saved });
    }

    if (url.pathname.startsWith('/api/requests/'))
      return route.fulfill({
        status: saved ? 200 : 404,
        json: saved ?? { detail: 'Request not found' },
      });

    if (url.pathname === '/api/requests')
      return route.fulfill({ json: saved ? [saved] : [] });

    return route.fulfill({ status: 404, json: { detail: 'Not found' } });
  });
});

async function signIn(page) {
  await page.getByLabel('Username', { exact: true }).fill('test-user');
  await page.getByLabel('Password', { exact: true }).fill('test-password');
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
}

test('login, validation, dashboard search, safe tracking, settings, and logout', async ({
  page,
}, testInfo) => {
  await page.goto('/request');
  await page.getByLabel('Username', { exact: true }).fill('wrong');
  await page.getByLabel('Password', { exact: true }).fill('wrong');
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
  await expect(page.getByRole('alert')).toContainText('incorrect');
  await signIn(page);
  await expect(
    page.getByRole('heading', { name: 'Request an IT asset' }),
  ).toBeVisible();
  await page.screenshot({
    path: testInfo.outputPath('request-form.png'),
    fullPage: true,
  });
  await page.getByRole('button', { name: 'Submit IT Asset Request' }).click();
  await expect(
    page.getByText('Enter a name between 2 and 100 characters.'),
  ).toBeVisible();
  await page.getByLabel('Requester name').fill('Test User');
  await page.getByLabel('Requester email').fill('test@example.com');
  await page.getByLabel('Asset type').selectOption('Laptop');
  const reason =
    '<img src=x onerror="window.xss=true"> Equipment needed for work.';
  await page.getByLabel('Business reason').fill(reason);
  await page.getByRole('button', { name: 'Submit IT Asset Request' }).click();
  await expect(page.getByText('Request successfully saved.')).toBeVisible();

  await page.getByRole('link', { name: 'Dashboard', exact: true }).click();
  await expect(page).toHaveURL(/\/dashboard$/);
  await expect(
    page.getByRole('heading', { name: 'IT Service Desk Dashboard' }),
  ).toBeVisible();
  await expect(page.getByRole('link', { name: '#27' })).toBeVisible();
  await expect(page.getByText('#54')).toBeVisible();
  await expect(page.getByText('Zendesk linked')).toBeVisible();
  await expect(page.getByText('Sync errors')).toBeVisible();

  await page.getByLabel('Search requests').fill('54');
  await expect(page.getByRole('link', { name: '#27' })).toBeVisible();
  await expect(page.getByText('1 of 1 shown')).toBeVisible();
  await page.getByLabel('Search requests').fill('nothing-here');
  await expect(page.getByText('No requests match this search.')).toBeVisible();
  await page.getByLabel('Search requests').fill('');

  await page.getByRole('link', { name: '#27' }).click();
  await expect(page).toHaveURL(/\/requests\/27$/);
  await expect(page.getByText(reason, { exact: true })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Zendesk ticket #54' })).toBeVisible();
  await expect(page.getByText(/Webhook → portal/)).toBeVisible();
  await expect(page.getByRole('link', { name: 'Back to dashboard' })).toBeVisible();
  expect(await page.evaluate(() => window.xss)).toBeUndefined();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBeTruthy();

  await page.getByRole('link', { name: 'Settings', exact: true }).click();
  await expect(page).toHaveURL(/\/settings$/);
  await expect(page.getByRole('heading', { name: 'Settings' })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Zendesk push & status sync' })).toBeVisible();
  await expect(page.getByRole('link', { name: /Open Swagger API docs/ })).toHaveAttribute(
    'href',
    'http://127.0.0.1:8001/docs',
  );

  await page.reload();
  await expect(
    page.getByRole('heading', { name: 'Welcome back.' }),
  ).toBeVisible();
  await signIn(page);
  await expect(page.getByRole('heading', { name: 'Settings' })).toBeVisible();
  await page.getByRole('button', { name: 'Sign out' }).click();
  await expect(
    page.getByRole('heading', { name: 'Welcome back.' }),
  ).toBeVisible();
});

test('business reason cannot satisfy the minimum with whitespace', async ({
  page,
}) => {
  await page.goto('/request');
  await signIn(page);
  await page.getByLabel('Requester name').fill('Test User');
  await page.getByLabel('Requester email').fill('test@example.com');
  await page.getByLabel('Asset type').selectOption('Laptop');
  await page.getByLabel('Business reason').fill('a\n\n\n\n\n\t    b\n\n\n\n\n');

  await expect(page.getByText(/2 meaningful/)).toBeVisible();
  await page.getByRole('button', { name: 'Submit IT Asset Request' }).click();

  await expect(
    page.getByText(/at least 10 non-whitespace characters/),
  ).toBeVisible();
  await expect(page.getByText('Request successfully saved.')).toHaveCount(0);
  await expect(page).toHaveURL(/\/request$/);
});

test('missing tracking record offers recovery', async ({ page }) => {
  await page.goto('/requests/999');
  await signIn(page);
  await expect(page.getByRole('alert')).toContainText('could not be found');
  await expect(page.getByRole('button', { name: 'Try again' })).toBeVisible();
});

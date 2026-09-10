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
    if (request.method() === 'POST') {
      saved = {
        ...request.postDataJSON(),
        id: 27,
        status: 'new',
        zendesk_ticket_id: null,
        zendesk_status: null,
        zendesk_sync_status: 'sync_pending',
        zendesk_last_synced_at: null,
        created_at: '2026-09-10T10:00:00Z',
        updated_at: '2026-09-10T10:00:00Z',
      };
      return route.fulfill({ status: 201, json: saved });
    }
    if (request.url().includes('/requests/'))
      return route.fulfill({
        status: saved ? 200 : 404,
        json: saved ?? { detail: 'Request not found' },
      });
    return route.fulfill({ json: saved ? [saved] : [] });
  });
});

async function signIn(page) {
  await page.getByLabel('Username', { exact: true }).fill('test-user');
  await page.getByLabel('Password', { exact: true }).fill('test-password');
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
}

test('login, validation, safe request tracking, and session logout', async ({
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
  await expect(
    page.getByText(/Zendesk synchronisation is pending/),
  ).toBeVisible();
  await page.getByRole('link', { name: 'Track this request' }).click();
  await expect(page).toHaveURL(/\/requests\/27$/);
  await expect(page.getByText(reason, { exact: true })).toBeVisible();
  expect(await page.evaluate(() => window.xss)).toBeUndefined();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBeTruthy();
  await page.reload();
  await expect(
    page.getByRole('heading', { name: 'Welcome back.' }),
  ).toBeVisible();
  await signIn(page);
  await expect(
    page.getByRole('heading', { name: 'Request #27' }),
  ).toBeVisible();
  await page.getByRole('button', { name: 'Sign out' }).click();
  await expect(
    page.getByRole('heading', { name: 'Welcome back.' }),
  ).toBeVisible();
});

test('missing tracking record offers recovery', async ({ page }) => {
  await page.goto('/requests/999');
  await signIn(page);
  await expect(page.getByRole('alert')).toContainText('could not be found');
  await expect(page.getByRole('button', { name: 'Try again' })).toBeVisible();
});

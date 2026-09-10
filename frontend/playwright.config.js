import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  use: { baseURL: 'http://127.0.0.1:5174', trace: 'retain-on-failure' },
  projects: [
    { name: 'desktop', use: { ...devices['Desktop Chrome'] } },
    { name: 'mobile', use: { ...devices['Pixel 7'] } },
  ],
  webServer: {
    command: 'npm run dev -- --host 127.0.0.1 --port 5174 --strictPort',
    url: 'http://127.0.0.1:5174',
    env: { VITE_API_URL: 'http://127.0.0.1:8001' },
    reuseExistingServer: false,
  },
});

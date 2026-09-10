/**
 * ROLE: Client composition: routes and in-memory login state
 * CALLED BY: main.jsx
 * CALLS: api.js, page Views, AppLayout and AuthLayout
 * DATA IN: Browser pathname and login form data
 * DATA OUT: Selected page and authenticated API client passed as props
 * WHY: Keep route/session composition outside page presentation.
 * SECURITY / RELIABILITY: Login probes listRequests; credentials live in the API closure,
 *     not localStorage. Refresh/sign-out drops that reference. Optional GSAP respects
 *     reduced-motion preferences.
 * FLOW: main.jsx -> this module -> api.js, page Views, AppLayout and AuthLayout
 */

import { useEffect, useMemo, useState } from 'react';
import AppLink from './components/AppLink.jsx';
import AppLayout from './layouts/AppLayout.jsx';
import AuthLayout from './layouts/AuthLayout.jsx';
import { createApi } from './services/api.js';
import DashboardView from './views/DashboardView.jsx';
import RequestDetailView from './views/RequestDetailView.jsx';
import RequestView from './views/RequestView.jsx';
import SettingsView from './views/SettingsView.jsx';

export default function App() {
  const [path, setPath] = useState(window.location.pathname);
  const [api, setApi] = useState(null);
  const [username, setUsername] = useState('');
  const [error, setError] = useState('');
  const [signingIn, setSigningIn] = useState(false);

  const apiDocsUrl = useMemo(() => {
    const baseUrl = import.meta.env?.VITE_API_URL;
    return baseUrl ? `${baseUrl.replace(/\/$/, '')}/docs` : '#';
  }, []);

  useEffect(() => {
    const pop = () => setPath(window.location.pathname);
    window.addEventListener('popstate', pop);
    return () => window.removeEventListener('popstate', pop);
  }, []);

  useEffect(() => {
    const gsap = window.gsap;
    if (!gsap || window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      return undefined;
    }

    const scope = document.querySelector(api ? '.main-content' : '.login-layout');
    if (!scope) return undefined;

    const context = gsap.context(() => {
      if (!api) {
        gsap.from(
          '.login-story .brand, .heritage-line, .login-story h1, .login-subcopy, .login-caption',
          {
            opacity: 0,
            y: 18,
            duration: 0.55,
            stagger: 0.08,
            ease: 'power2.out',
            clearProps: 'transform,opacity',
          },
        );
        gsap.from('.login-form', {
          opacity: 0,
          x: 24,
          duration: 0.6,
          delay: 0.12,
          ease: 'power2.out',
          clearProps: 'transform,opacity',
        });
        return;
      }

      const targets = scope.querySelectorAll(
        '.page-heading, .queue-summary > *, .panel, .settings-card',
      );
      if (targets.length) {
        gsap.fromTo(
          targets,
          { opacity: 0, y: 12 },
          {
            opacity: 1,
            y: 0,
            duration: 0.42,
            stagger: 0.04,
            ease: 'power2.out',
            clearProps: 'transform,opacity',
          },
        );
      }
    }, scope);

    return () => context.revert();
  }, [api, path]);

  function navigate(to) {
    window.history.pushState({}, '', to);
    setPath(to);
    window.scrollTo({ top: 0 });
  }

  function signOut() {
    setApi(null);
    setUsername('');
    setError('');
  }

  async function signIn(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const fields = new FormData(form);
    setSigningIn(true);
    setError('');
    try {
      // services/api.js creates the in-memory HTTP client; Views receive this client instead of credentials.
      const nextApi = createApi(
        { username: fields.get('username'), password: fields.get('password') },
        {
          onUnauthorized: () => {
            setApi(null);
            setError('Your credentials are no longer valid. Please sign in again.');
          },
        },
      );
      // api.js probes request_controller.py's protected GET; only a successful response enables authenticated Views.
      await nextApi.listRequests(1);
      setUsername(fields.get('username'));
      setApi(nextApi);
      form.reset();
    } catch (problem) {
      setError(
        problem.status === 401
          ? 'The username or password is incorrect.'
          : problem.message,
      );
    } finally {
      setSigningIn(false);
    }
  }

  if (!api) {
    return (
      <AuthLayout>
        <form className="login-form" onSubmit={signIn}>
          <p className="eyebrow">EMPLOYEE ACCESS</p>
          <h2>Welcome back.</h2>
          <p className="muted">Sign in to the Royal Tyres IT Service Desk.</p>
          <div className="field">
            <label htmlFor="username">Username</label>
            <input
              id="username"
              name="username"
              autoComplete="username"
              required
              autoFocus
            />
          </div>
          <div className="field">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              name="password"
              type="password"
              autoComplete="current-password"
              required
            />
          </div>
          {error && (
            <p className="notice error" role="alert">
              {error}
            </p>
          )}
          <button className="button primary full-width" disabled={signingIn}>
            {signingIn ? 'Signing in…' : 'Sign in'}{' '}
            <span aria-hidden="true">→</span>
          </button>
          <p className="login-footnote">
            Use the demo credentials configured for this portal.
            <br />
            Your session ends when you refresh or close this page.
          </p>
        </form>
      </AuthLayout>
    );
  }

  const match = path.match(/^\/requests\/(\d+)\/?$/);
  const isNewRequest = path === '/' || path === '/request' || path === '/request/';
  const isDashboard =
    path === '/dashboard' ||
    path === '/dashboard/' ||
    path === '/requests' ||
    path === '/requests/';
  const isSettings =
    path === '/settings' ||
    path === '/settings/' ||
    path === '/zendesk-setup' ||
    path === '/zendesk-setup/';
  const breadcrumb = isSettings
    ? 'Settings'
    : isDashboard
      ? 'Dashboard'
      : match
        ? `Request #${match[1]}`
        : 'New request';

  // Route browser paths to views/*.jsx; App composes pages while Services own business and HTTP work.
  let page;
  if (isNewRequest) {
    page = <RequestView api={api} navigate={navigate} />;
  } else if (isDashboard) {
    page = <DashboardView api={api} navigate={navigate} />;
  } else if (isSettings) {
    page = <SettingsView api={api} username={username} apiDocsUrl={apiDocsUrl} />;
  } else if (match) {
    page = (
      <RequestDetailView
        key={match[1]}
        id={match[1]}
        api={api}
        navigate={navigate}
      />
    );
  } else {
    page = (
      <section className="panel">
        <h1>Page not found</h1>
        <AppLink to="/dashboard" navigate={navigate}>
          Go to dashboard
        </AppLink>
      </section>
    );
  }

  return (
    <AppLayout
      navigate={navigate}
      apiDocsUrl={apiDocsUrl}
      username={username}
      breadcrumb={breadcrumb}
      isSettings={isSettings}
      isNewRequest={isNewRequest}
      isDashboard={isDashboard}
      hasRequestMatch={Boolean(match)}
      onSignOut={signOut}
    >
      {page}
    </AppLayout>
  );
}

import { useEffect, useMemo, useState } from 'react';
import { createApi } from './services/api.js';
import AppLink from './components/AppLink.jsx';
import RequestView from './views/RequestView.jsx';
import RequestsView from './views/RequestsView.jsx';
import RequestDetailView from './views/RequestDetailView.jsx';
import SettingsView from './views/SettingsView.jsx';

function Brand() {
  return (
    <div className="brand">
      <span className="brand-mark">R</span>
      <div>
        ROYAL TYRES<small>IT SERVICE DESK</small>
      </div>
    </div>
  );
}

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

  async function signIn(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const fields = new FormData(form);
    setSigningIn(true);
    setError('');
    try {
      const nextApi = createApi(
        { username: fields.get('username'), password: fields.get('password') },
        {
          onUnauthorized: () => {
            setApi(null);
            setError(
              'Your credentials are no longer valid. Please sign in again.',
            );
          },
        },
      );
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

  if (!api)
    return (
      <main className="login-layout">
        <section className="login-story">
          <Brand />
          <div>
            <p className="heritage-line">Trusted tyre workshop since 1939</p>
            <p className="eyebrow">INTERNAL IT · SUPPORTING THE WAY YOU WORK</p>
            <h1>
              Keep your work
              <br />
              <em>moving.</em>
            </h1>
            <p className="login-subcopy">
              Request the equipment you need, then follow it from the service desk
              through to Zendesk without losing sight of the request.
            </p>
          </div>
          <span className="login-caption">
            Passenger · Commercial · Workshop · Internal IT
          </span>
        </section>
        <section className="login-form-wrap">
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
        </section>
      </main>
    );

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

  return (
    <div className="app-layout">
      <aside className="sidebar">
        <Brand />
        <p className="nav-label">WORKSPACE</p>
        <nav aria-label="Main navigation">
          <AppLink
            to="/request"
            navigate={navigate}
            className={`nav-item ${isNewRequest ? 'active' : ''}`}
            aria-current={isNewRequest ? 'page' : undefined}
          >
            <span aria-hidden="true">＋</span> New request
          </AppLink>
          <AppLink
            to="/dashboard"
            navigate={navigate}
            className={`nav-item ${isDashboard || match ? 'active' : ''}`}
            aria-current={isDashboard ? 'page' : undefined}
          >
            <span aria-hidden="true">▦</span> Dashboard
          </AppLink>
          <a
            href={apiDocsUrl}
            target="_blank"
            rel="noreferrer"
            className="nav-item"
          >
            <span aria-hidden="true">↗</span> API docs
          </a>
        </nav>
        <div className="sidebar-bottom">
          <span className="small-dot" /> Trusted since 1939 · Internal IT
        </div>
      </aside>
      <div className="workspace">
        <header className="topbar">
          <span>
            IT Service Desk <span className="breadcrumb">/ {breadcrumb}</span>
          </span>
          <div className="account">
            <span className="avatar" aria-hidden="true">
              {username.slice(0, 1).toUpperCase()}
            </span>
            <span>{username}</span>
            <AppLink
              to="/settings"
              navigate={navigate}
              className={`account-link ${isSettings ? 'active' : ''}`}
              aria-current={isSettings ? 'page' : undefined}
            >
              Settings
            </AppLink>
            <button
              onClick={() => {
                setApi(null);
                setUsername('');
                setError('');
              }}
              className="signout"
            >
              Sign out
            </button>
          </div>
        </header>
        <main className="main-content">
          {isNewRequest ? (
            <RequestView api={api} navigate={navigate} />
          ) : isDashboard ? (
            <RequestsView api={api} navigate={navigate} />
          ) : isSettings ? (
            <SettingsView api={api} username={username} apiDocsUrl={apiDocsUrl} />
          ) : match ? (
            <RequestDetailView
              key={match[1]}
              id={match[1]}
              api={api}
              navigate={navigate}
            />
          ) : (
            <section className="panel">
              <h1>Page not found</h1>
              <AppLink to="/dashboard" navigate={navigate}>
                Go to dashboard
              </AppLink>
            </section>
          )}
        </main>
        <footer className="workspace-footer">
          Royal Tyres <span>IT Asset Request Tool</span>
        </footer>
      </div>
    </div>
  );
}

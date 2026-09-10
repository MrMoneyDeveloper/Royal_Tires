import { useEffect, useState } from 'react';
import { createApi } from './services/api.js';
import AppLink from './components/AppLink.jsx';
import RequestView from './views/RequestView.jsx';
import RequestDetailView from './views/RequestDetailView.jsx';

function Brand() {
  return (
    <div className="brand">
      <span className="brand-mark">R</span>
      <div>
        ROYAL TYRES<small>IT ASSET PORTAL</small>
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
  const [requestNumber, setRequestNumber] = useState('');

  useEffect(() => {
    const pop = () => setPath(window.location.pathname);
    window.addEventListener('popstate', pop);
    return () => window.removeEventListener('popstate', pop);
  }, []);

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
            <p className="eyebrow">SUPPORTING THE WAY YOU WORK</p>
            <h1>
              The right tools.
              <br />
              Ready for your work.
            </h1>
            <p>
              Request equipment, follow its progress, and keep your work moving.
            </p>
          </div>
          <span className="login-caption">
            Internal IT · Asset requests & tracking
          </span>
        </section>
        <section className="login-form-wrap">
          <form className="login-form" onSubmit={signIn}>
            <p className="eyebrow">EMPLOYEE ACCESS</p>
            <h2>Welcome back.</h2>
            <p className="muted">Sign in to your IT asset portal.</p>
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
  const isRequest = path === '/' || path === '/request' || path === '/request/';
  return (
    <div className="app-layout">
      <aside className="sidebar">
        <Brand />
        <p className="nav-label">WORKSPACE</p>
        <nav aria-label="Main navigation">
          <AppLink
            to="/request"
            navigate={navigate}
            className={`nav-item ${isRequest ? 'active' : ''}`}
            aria-current={isRequest ? 'page' : undefined}
          >
            <span aria-hidden="true">＋</span> New request
          </AppLink>
        </nav>
        <form
          className="track-form"
          onSubmit={(event) => {
            event.preventDefault();
            if (/^[1-9]\d*$/.test(requestNumber))
              navigate(`/requests/${requestNumber}`);
          }}
        >
          <label htmlFor="request-number">Track a request</label>
          <div>
            <input
              id="request-number"
              type="number"
              min="1"
              step="1"
              placeholder="Request ID"
              required
              value={requestNumber}
              onChange={(event) => setRequestNumber(event.target.value)}
            />
            <button aria-label="Find request">→</button>
          </div>
        </form>
        <div className="sidebar-bottom">
          <span className="small-dot" /> Built for your workday
        </div>
      </aside>
      <div className="workspace">
        <header className="topbar">
          <span>
            IT Service Desk <span className="breadcrumb">/ Asset requests</span>
          </span>
          <div className="account">
            <span className="avatar" aria-hidden="true">
              {username.slice(0, 1).toUpperCase()}
            </span>
            <span>{username}</span>
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
          {isRequest ? (
            <RequestView api={api} navigate={navigate} />
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
              <AppLink to="/request" navigate={navigate}>
                Go to new request
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

/**
 * ROLE: Shared component: primary navigation
 * CALLED BY: AppLayout
 * CALLS: Brand and AppLink
 * DATA IN: Route flags, navigation callback and docs URL
 * DATA OUT: Active navigation links
 * WHY: Reuse navigation across authenticated Views.
 * SECURITY / RELIABILITY: Swagger opens separately; no credentials are placed in its URL.
 * FLOW: AppLayout -> this module -> Brand and AppLink
 */

import AppLink from '../AppLink.jsx';
import Brand from './Brand.jsx';

export default function Sidebar({
  navigate,
  apiDocsUrl,
  isNewRequest,
  isDashboard,
  hasRequestMatch,
}) {
  return (
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
          className={`nav-item ${isDashboard || hasRequestMatch ? 'active' : ''}`}
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
  );
}

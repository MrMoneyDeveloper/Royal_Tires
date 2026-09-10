/**
 * ROLE: Shared component: account/navigation header
 * CALLED BY: AppLayout
 * CALLS: AppLink and onSignOut callback
 * DATA IN: Username, breadcrumb and navigation state
 * DATA OUT: Header and sign-out action
 * WHY: Separate header presentation from App session ownership.
 * SECURITY / RELIABILITY: Displays username as text. App clears the in-memory API reference
 *     on sign-out.
 * FLOW: AppLayout -> this module -> AppLink and onSignOut callback
 */

import AppLink from '../AppLink.jsx';

export default function Topbar({
  username,
  breadcrumb,
  isSettings,
  navigate,
  onSignOut,
}) {
  return (
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
        <button onClick={onSignOut} className="signout">
          Sign out
        </button>
      </div>
    </header>
  );
}

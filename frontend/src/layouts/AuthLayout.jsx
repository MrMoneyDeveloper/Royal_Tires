/**
 * ROLE: Layout: reusable sign-in shell
 * CALLED BY: App
 * CALLS: Brand and children
 * DATA IN: Login form child
 * DATA OUT: Unauthenticated page presentation
 * WHY: Keep visual shell separate from login behavior.
 * SECURITY / RELIABILITY: App/api.js perform sign-in; layout does not authenticate or retain
 *     credentials.
 * FLOW: App -> this module -> Brand and children
 */

import Brand from '../components/shared/Brand.jsx';

export default function AuthLayout({ children }) {
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
      <section className="login-form-wrap">{children}</section>
    </main>
  );
}

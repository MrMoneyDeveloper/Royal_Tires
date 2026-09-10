/**
 * ROLE: Shared component: footer
 * CALLED BY: AppLayout
 * CALLS: React presentation only
 * DATA IN: No business input
 * DATA OUT: Static footer markup
 * WHY: Keep shell wording in one reusable component.
 * SECURITY / RELIABILITY: No persistence, authentication or network behavior.
 * FLOW: AppLayout -> this module -> React presentation only
 */

export default function Footer() {
  return (
    <footer className="workspace-footer">
      Royal Tyres <span>IT Asset Request Tool</span>
    </footer>
  );
}

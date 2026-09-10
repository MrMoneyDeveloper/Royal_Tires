/**
 * ROLE: Shared component: brand identity
 * CALLED BY: AuthLayout and Sidebar
 * CALLS: React presentation only
 * DATA IN: No business input
 * DATA OUT: Brand markup
 * WHY: Keep the same identity across shells.
 * SECURITY / RELIABILITY: Static UI only; no authentication or external API calls.
 * FLOW: AuthLayout and Sidebar -> this module -> React presentation only
 */

export default function Brand() {
  return (
    <div className="brand">
      <span className="brand-mark">R</span>
      <div>
        ROYAL TYRES<small>IT SERVICE DESK</small>
      </div>
    </div>
  );
}

/**
 * ROLE: Reusable component: internal navigation link
 * CALLED BY: Views and shared navigation
 * CALLS: Injected navigate callback or native anchor behavior
 * DATA IN: Target path, children and anchor props
 * DATA OUT: SPA navigation on ordinary click
 * WHY: Share navigation behavior while preserving browser conventions.
 * SECURITY / RELIABILITY: Modified clicks remain native links; ordinary clicks preserve the
 *     current in-memory app state.
 * FLOW: Views and shared navigation -> this module -> Injected navigate callback or native
 *     anchor behavior
 */

export default function AppLink({ to, navigate, children, ...props }) {
  return (
    <a
      href={to}
      {...props}
      onClick={(event) => {
        if (
          event.button === 0 &&
          !event.ctrlKey &&
          !event.metaKey &&
          !event.shiftKey &&
          !event.altKey
        ) {
          event.preventDefault();
          navigate(to);
        }
      }}
    >
      {children}
    </a>
  );
}

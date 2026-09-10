import Footer from '../components/shared/Footer.jsx';
import Sidebar from '../components/shared/Sidebar.jsx';
import Topbar from '../components/shared/Topbar.jsx';

export default function AppLayout({
  children,
  navigate,
  apiDocsUrl,
  username,
  breadcrumb,
  isSettings,
  isNewRequest,
  isDashboard,
  hasRequestMatch,
  onSignOut,
}) {
  return (
    <div className="app-layout">
      <Sidebar
        navigate={navigate}
        apiDocsUrl={apiDocsUrl}
        isNewRequest={isNewRequest}
        isDashboard={isDashboard}
        hasRequestMatch={hasRequestMatch}
      />
      <div className="workspace">
        <Topbar
          username={username}
          breadcrumb={breadcrumb}
          isSettings={isSettings}
          navigate={navigate}
          onSignOut={onSignOut}
        />
        <main className="main-content">{children}</main>
        <Footer />
      </div>
    </div>
  );
}

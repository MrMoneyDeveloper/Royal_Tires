/**
 * ROLE: React entry point
 * CALLED BY: Vite-built browser entry
 * CALLS: ReactDOM, App and shared CSS
 * DATA IN: Root DOM element
 * DATA OUT: Mounted React application
 * WHY: Keep browser bootstrapping separate from routes and pages.
 * SECURITY / RELIABILITY: StrictMode may repeat development effects; no credentials are
 *     embedded here.
 * FLOW: Vite-built browser entry -> this module -> ReactDOM, App and shared CSS
 */

import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.jsx';
import './styles.css';
import './royal-brand.css';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);

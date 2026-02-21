import React from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';
import App from './App';
import * as serviceWorkerRegistration from './serviceWorkerRegistration';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

// Register service worker for PWA functionality
serviceWorkerRegistration.register({
  onUpdate: (registration) => {
    console.log('New content available, please refresh!');
    // You can show a notification to the user here
  },
  onSuccess: (registration) => {
    console.log('Service worker registered successfully');
  },
});

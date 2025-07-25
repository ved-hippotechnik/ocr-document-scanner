// PWA Utilities for OCR Document Scanner

export const registerServiceWorker = async () => {
  if ('serviceWorker' in navigator) {
    try {
      const registration = await navigator.serviceWorker.register('/sw.js');
      console.log('Service Worker registered successfully:', registration);
      
      // Check for updates
      registration.addEventListener('updatefound', () => {
        const newWorker = registration.installing;
        console.log('Service Worker update found');
        
        newWorker.addEventListener('statechange', () => {
          if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
            console.log('Service Worker update available');
            // Notify main app about update
            window.dispatchEvent(new CustomEvent('sw-update-available'));
          }
        });
      });
      
      return registration;
    } catch (error) {
      console.error('Service Worker registration failed:', error);
      throw error;
    }
  } else {
    console.warn('Service Worker not supported');
    return null;
  }
};

export const unregisterServiceWorker = async () => {
  if ('serviceWorker' in navigator) {
    try {
      const registration = await navigator.serviceWorker.ready;
      const result = await registration.unregister();
      console.log('Service Worker unregistered:', result);
      return result;
    } catch (error) {
      console.error('Service Worker unregistration failed:', error);
      throw error;
    }
  }
  return false;
};

export const updateServiceWorker = async () => {
  if ('serviceWorker' in navigator) {
    try {
      const registration = await navigator.serviceWorker.ready;
      const result = await registration.update();
      console.log('Service Worker updated:', result);
      return result;
    } catch (error) {
      console.error('Service Worker update failed:', error);
      throw error;
    }
  }
  return null;
};

export const requestNotificationPermission = async () => {
  if ('Notification' in window) {
    try {
      const permission = await Notification.requestPermission();
      console.log('Notification permission:', permission);
      return permission === 'granted';
    } catch (error) {
      console.error('Notification permission request failed:', error);
      return false;
    }
  }
  return false;
};

export const subscribeToPushNotifications = async () => {
  if ('serviceWorker' in navigator && 'PushManager' in window) {
    try {
      const registration = await navigator.serviceWorker.ready;
      
      // Generate VAPID keys on the server and replace this
      const vapidPublicKey = 'YOUR_VAPID_PUBLIC_KEY_HERE';
      
      const subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(vapidPublicKey)
      });
      
      console.log('Push subscription created:', subscription);
      
      // Send subscription to server
      await fetch('/api/v2/push/subscribe', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        },
        body: JSON.stringify(subscription)
      });
      
      return subscription;
    } catch (error) {
      console.error('Push subscription failed:', error);
      throw error;
    }
  }
  return null;
};

export const unsubscribeFromPushNotifications = async () => {
  if ('serviceWorker' in navigator && 'PushManager' in window) {
    try {
      const registration = await navigator.serviceWorker.ready;
      const subscription = await registration.pushManager.getSubscription();
      
      if (subscription) {
        await subscription.unsubscribe();
        console.log('Push subscription removed');
        
        // Notify server
        await fetch('/api/v2/push/unsubscribe', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('authToken')}`
          },
          body: JSON.stringify({ endpoint: subscription.endpoint })
        });
      }
      
      return true;
    } catch (error) {
      console.error('Push unsubscription failed:', error);
      throw error;
    }
  }
  return false;
};

export const checkForUpdates = async () => {
  if ('serviceWorker' in navigator) {
    try {
      const registration = await navigator.serviceWorker.ready;
      await registration.update();
      console.log('Checked for Service Worker updates');
      return true;
    } catch (error) {
      console.error('Update check failed:', error);
      return false;
    }
  }
  return false;
};

export const clearCache = async () => {
  if ('caches' in window) {
    try {
      const cacheNames = await caches.keys();
      await Promise.all(
        cacheNames.map(name => caches.delete(name))
      );
      console.log('All caches cleared');
      return true;
    } catch (error) {
      console.error('Cache clearing failed:', error);
      return false;
    }
  }
  return false;
};

export const isAppInstalled = () => {
  // Check if app is running in standalone mode
  const isStandalone = window.matchMedia('(display-mode: standalone)').matches;
  // Check for iOS standalone mode
  const isIOSStandalone = window.navigator.standalone === true;
  
  return isStandalone || isIOSStandalone;
};

export const getBrowserInstallPrompt = () => {
  return new Promise((resolve) => {
    const handleBeforeInstallPrompt = (e) => {
      e.preventDefault();
      window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
      resolve(e);
    };
    
    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
    
    // Timeout after 5 seconds
    setTimeout(() => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
      resolve(null);
    }, 5000);
  });
};

export const installApp = async (deferredPrompt) => {
  if (!deferredPrompt) return false;
  
  try {
    deferredPrompt.prompt();
    const result = await deferredPrompt.userChoice;
    console.log('Install prompt result:', result);
    return result.outcome === 'accepted';
  } catch (error) {
    console.error('App installation failed:', error);
    return false;
  }
};

export const getInstallInstructions = () => {
  const userAgent = navigator.userAgent;
  
  if (/iPhone|iPad|iPod/.test(userAgent)) {
    return {
      browser: 'Safari',
      steps: [
        'Tap the Share button at the bottom of the screen',
        'Scroll down and tap "Add to Home Screen"',
        'Tap "Add" in the top right corner'
      ]
    };
  } else if (/Android/.test(userAgent)) {
    if (/Chrome/.test(userAgent)) {
      return {
        browser: 'Chrome',
        steps: [
          'Tap the menu button (three dots)',
          'Tap "Add to Home screen"',
          'Tap "Add" to confirm'
        ]
      };
    } else {
      return {
        browser: 'Browser',
        steps: [
          'Open the menu',
          'Look for "Add to Home screen" or "Install"',
          'Follow the prompts to install'
        ]
      };
    }
  } else {
    return {
      browser: 'Desktop',
      steps: [
        'Look for an install button in the address bar',
        'Or check the browser menu for "Install" option',
        'Follow the prompts to install'
      ]
    };
  }
};

// Helper function to convert VAPID key
function urlBase64ToUint8Array(base64String) {
  const padding = '='.repeat((4 - base64String.length % 4) % 4);
  const base64 = (base64String + padding)
    .replace(/-/g, '+')
    .replace(/_/g, '/');

  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);

  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
}

export const isPWASupported = () => {
  return 'serviceWorker' in navigator && 'PushManager' in window;
};

export const getConnectionStatus = () => {
  return {
    online: navigator.onLine,
    connection: navigator.connection || navigator.mozConnection || navigator.webkitConnection,
    effectiveType: navigator.connection?.effectiveType || 'unknown'
  };
};

export const waitForConnection = () => {
  return new Promise((resolve) => {
    if (navigator.onLine) {
      resolve(true);
    } else {
      const handleOnline = () => {
        window.removeEventListener('online', handleOnline);
        resolve(true);
      };
      window.addEventListener('online', handleOnline);
    }
  });
};
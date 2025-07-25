import { useState, useEffect } from 'react';

export const usePWA = () => {
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [isInstalled, setIsInstalled] = useState(false);
  const [deferredPrompt, setDeferredPrompt] = useState(null);
  const [updateAvailable, setUpdateAvailable] = useState(false);

  useEffect(() => {
    // Check if app is installed
    const checkInstalled = () => {
      const isStandalone = window.matchMedia('(display-mode: standalone)').matches;
      const isWebApp = window.navigator.standalone === true;
      setIsInstalled(isStandalone || isWebApp);
    };

    // Online/offline status
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    // Install prompt
    const handleBeforeInstallPrompt = (e) => {
      e.preventDefault();
      setDeferredPrompt(e);
    };

    const handleAppInstalled = () => {
      setIsInstalled(true);
      setDeferredPrompt(null);
    };

    checkInstalled();

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
    window.addEventListener('appinstalled', handleAppInstalled);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
      window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
      window.removeEventListener('appinstalled', handleAppInstalled);
    };
  }, []);

  useEffect(() => {
    // Service Worker registration and updates
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.ready.then((registration) => {
        // Check for updates
        registration.addEventListener('updatefound', () => {
          const newWorker = registration.installing;
          newWorker.addEventListener('statechange', () => {
            if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
              setUpdateAvailable(true);
            }
          });
        });
      });

      // Listen for service worker messages
      navigator.serviceWorker.addEventListener('message', (event) => {
        if (event.data && event.data.type === 'UPDATE_AVAILABLE') {
          setUpdateAvailable(true);
        }
      });
    }
  }, []);

  const installApp = async () => {
    if (!deferredPrompt) return false;

    try {
      deferredPrompt.prompt();
      const result = await deferredPrompt.userChoice;
      
      if (result.outcome === 'accepted') {
        setIsInstalled(true);
        setDeferredPrompt(null);
        return true;
      }
      
      return false;
    } catch (error) {
      console.error('Error installing app:', error);
      return false;
    }
  };

  const updateApp = async () => {
    if (!updateAvailable) return false;

    try {
      const registration = await navigator.serviceWorker.ready;
      const waiting = registration.waiting;
      
      if (waiting) {
        waiting.postMessage({ type: 'SKIP_WAITING' });
        waiting.addEventListener('statechange', () => {
          if (waiting.state === 'activated') {
            window.location.reload();
          }
        });
        return true;
      }
      
      return false;
    } catch (error) {
      console.error('Error updating app:', error);
      return false;
    }
  };

  const addToOfflineQueue = async (scanData) => {
    try {
      const request = indexedDB.open('OCRScanner', 1);
      
      return new Promise((resolve, reject) => {
        request.onerror = () => reject(request.error);
        request.onsuccess = () => {
          const db = request.result;
          const transaction = db.transaction(['pendingScans'], 'readwrite');
          const store = transaction.objectStore('pendingScans');
          
          const scanItem = {
            id: Date.now().toString(),
            data: scanData,
            timestamp: new Date().toISOString(),
            authToken: localStorage.getItem('authToken')
          };
          
          const addRequest = store.add(scanItem);
          
          addRequest.onsuccess = () => {
            // Register for background sync
            if ('serviceWorker' in navigator && 'sync' in window.ServiceWorkerRegistration.prototype) {
              navigator.serviceWorker.ready.then((registration) => {
                return registration.sync.register('background-scan');
              });
            }
            resolve(scanItem);
          };
          
          addRequest.onerror = () => reject(addRequest.error);
        };
        
        request.onupgradeneeded = (event) => {
          const db = event.target.result;
          if (!db.objectStoreNames.contains('pendingScans')) {
            db.createObjectStore('pendingScans', { keyPath: 'id' });
          }
        };
      });
    } catch (error) {
      console.error('Error adding to offline queue:', error);
      throw error;
    }
  };

  const getPendingScans = async () => {
    try {
      const request = indexedDB.open('OCRScanner', 1);
      
      return new Promise((resolve, reject) => {
        request.onerror = () => reject(request.error);
        request.onsuccess = () => {
          const db = request.result;
          
          if (!db.objectStoreNames.contains('pendingScans')) {
            resolve([]);
            return;
          }
          
          const transaction = db.transaction(['pendingScans'], 'readonly');
          const store = transaction.objectStore('pendingScans');
          const getAllRequest = store.getAll();
          
          getAllRequest.onsuccess = () => resolve(getAllRequest.result);
          getAllRequest.onerror = () => reject(getAllRequest.error);
        };
        
        request.onupgradeneeded = (event) => {
          const db = event.target.result;
          if (!db.objectStoreNames.contains('pendingScans')) {
            db.createObjectStore('pendingScans', { keyPath: 'id' });
          }
        };
      });
    } catch (error) {
      console.error('Error getting pending scans:', error);
      return [];
    }
  };

  const requestNotificationPermission = async () => {
    if ('Notification' in window) {
      const permission = await Notification.requestPermission();
      return permission === 'granted';
    }
    return false;
  };

  return {
    isOnline,
    isInstalled,
    canInstall: !!deferredPrompt,
    updateAvailable,
    installApp,
    updateApp,
    addToOfflineQueue,
    getPendingScans,
    requestNotificationPermission
  };
};
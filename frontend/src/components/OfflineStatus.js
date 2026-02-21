import React, { useState, useEffect } from 'react';
import { Alert, Snackbar, Box, Typography, Button, Chip } from '@mui/material';
import { WifiOff, Wifi, CloudOff, Sync } from '@mui/icons-material';

const OfflineStatus = () => {
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [showOfflineAlert, setShowOfflineAlert] = useState(false);
  const [showOnlineAlert, setShowOnlineAlert] = useState(false);
  const [pendingScans, setPendingScans] = useState(0);
  const [syncing, setSyncing] = useState(false);

  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true);
      setShowOnlineAlert(true);
      setShowOfflineAlert(false);
      
      // Check for pending scans and sync
      checkPendingScans();
    };

    const handleOffline = () => {
      setIsOnline(false);
      setShowOfflineAlert(true);
      setShowOnlineAlert(false);
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    // Initial check for pending scans
    checkPendingScans();

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  const checkPendingScans = async () => {
    try {
      const scans = await getPendingScansFromIndexedDB();
      setPendingScans(scans.length);
    } catch (error) {
      console.error('Error checking pending scans:', error);
    }
  };

  const getPendingScansFromIndexedDB = () => {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open('OCRScanner', 1);
      
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
  };

  const handleSyncPendingScans = async () => {
    if (!isOnline) return;
    
    setSyncing(true);
    try {
      // Trigger background sync
      if ('serviceWorker' in navigator && 'sync' in window.ServiceWorkerRegistration.prototype) {
        const registration = await navigator.serviceWorker.ready;
        await registration.sync.register('background-scan');
      }
      
      // Recheck pending scans after a short delay
      setTimeout(() => {
        checkPendingScans();
        setSyncing(false);
      }, 2000);
    } catch (error) {
      console.error('Error syncing pending scans:', error);
      setSyncing(false);
    }
  };

  const handleCloseOfflineAlert = () => {
    setShowOfflineAlert(false);
  };

  const handleCloseOnlineAlert = () => {
    setShowOnlineAlert(false);
  };

  return (
    <>
      {/* Connection Status Indicator */}
      <Box
        sx={{
          position: 'fixed',
          top: 16,
          left: 16,
          zIndex: 1300,
          display: 'flex',
          alignItems: 'center',
          gap: 1
        }}
      >
        <Chip
          icon={isOnline ? <Wifi /> : <WifiOff />}
          label={isOnline ? 'Online' : 'Offline'}
          color={isOnline ? 'success' : 'error'}
          size="small"
          sx={{
            backgroundColor: isOnline ? 'rgba(76, 175, 80, 0.1)' : 'rgba(244, 67, 54, 0.1)',
            backdropFilter: 'blur(10px)',
            border: `1px solid ${isOnline ? 'rgba(76, 175, 80, 0.3)' : 'rgba(244, 67, 54, 0.3)'}`,
          }}
        />
        
        {pendingScans > 0 && (
          <Chip
            icon={syncing ? <Sync className="spinning" /> : <CloudOff />}
            label={`${pendingScans} pending`}
            color="warning"
            size="small"
            onClick={handleSyncPendingScans}
            sx={{
              backgroundColor: 'rgba(255, 193, 7, 0.1)',
              backdropFilter: 'blur(10px)',
              border: '1px solid rgba(255, 193, 7, 0.3)',
              cursor: isOnline ? 'pointer' : 'default',
              '& .spinning': {
                animation: 'spin 1s linear infinite'
              }
            }}
          />
        )}
      </Box>

      {/* Offline Alert */}
      <Snackbar
        open={showOfflineAlert}
        autoHideDuration={4000}
        onClose={handleCloseOfflineAlert}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert
          onClose={handleCloseOfflineAlert}
          severity="warning"
          sx={{ width: '100%' }}
          icon={<WifiOff />}
        >
          <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
            You're offline
          </Typography>
          <Typography variant="body2">
            Some features may be limited. Scans will be queued for sync when you're back online.
          </Typography>
        </Alert>
      </Snackbar>

      {/* Online Alert */}
      <Snackbar
        open={showOnlineAlert}
        autoHideDuration={4000}
        onClose={handleCloseOnlineAlert}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert
          onClose={handleCloseOnlineAlert}
          severity="success"
          sx={{ width: '100%' }}
          icon={<Wifi />}
          action={
            pendingScans > 0 ? (
              <Button
                color="inherit"
                size="small"
                onClick={handleSyncPendingScans}
                disabled={syncing}
              >
                {syncing ? 'Syncing...' : 'Sync Now'}
              </Button>
            ) : null
          }
        >
          <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
            Back online!
          </Typography>
          {pendingScans > 0 && (
            <Typography variant="body2">
              {pendingScans} pending scan{pendingScans > 1 ? 's' : ''} will be processed.
            </Typography>
          )}
        </Alert>
      </Snackbar>

      {/* Global CSS for spinning animation */}
      <style jsx global>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </>
  );
};

export default OfflineStatus;
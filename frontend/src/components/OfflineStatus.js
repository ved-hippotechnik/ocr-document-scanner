import React, { useState, useEffect } from 'react';
import { Alert, Snackbar, Box, Typography, Button, Chip } from '@mui/material';
import { useTheme, alpha } from '@mui/material/styles';
import { WifiOff, Wifi, CloudOff, Sync, Cloud } from '@mui/icons-material';
import { useApiHealthCheck } from '../utils/resilience';

const OfflineStatus = () => {
  const theme = useTheme();
  // Q1 — tri-state health: 'healthy' | 'api_down' | 'offline'
  const apiHealth = useApiHealthCheck('/api/v3/health', 30000);
  const isOnline = apiHealth !== 'offline';
  const isApiDown = apiHealth === 'api_down';

  const [showOfflineAlert, setShowOfflineAlert] = useState(false);
  const [showOnlineAlert, setShowOnlineAlert] = useState(false);
  const [showApiDownAlert, setShowApiDownAlert] = useState(false);
  const [pendingScans, setPendingScans] = useState(0);
  const [syncing, setSyncing] = useState(false);
  const prevHealthRef = React.useRef(apiHealth);

  useEffect(() => {
    const prev = prevHealthRef.current;
    prevHealthRef.current = apiHealth;

    if (apiHealth === 'offline' && prev !== 'offline') {
      setShowOfflineAlert(true);
      setShowOnlineAlert(false);
      setShowApiDownAlert(false);
    } else if (apiHealth === 'api_down' && prev !== 'api_down') {
      setShowApiDownAlert(true);
      setShowOfflineAlert(false);
    } else if (apiHealth === 'healthy' && prev !== 'healthy') {
      setShowOnlineAlert(true);
      setShowOfflineAlert(false);
      setShowApiDownAlert(false);
      checkPendingScans();
    }
  }, [apiHealth]);

  useEffect(() => {
    checkPendingScans();
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
      // Q6 — Show sync failure to user (was console-only before)
      setShowOfflineAlert(true);
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
          zIndex: 1100,
          display: 'flex',
          alignItems: 'center',
          gap: 1
        }}
      >
        <Chip
          icon={isApiDown ? <Cloud /> : isOnline ? <Wifi /> : <WifiOff />}
          label={isApiDown ? 'API Down' : isOnline ? 'Online' : 'Offline'}
          color={isApiDown ? 'warning' : isOnline ? 'success' : 'error'}
          size="small"
          sx={{
            backgroundColor: isApiDown
              ? alpha(theme.palette.warning.main, 0.1)
              : isOnline
                ? alpha(theme.palette.success.main, 0.1)
                : alpha(theme.palette.error.main, 0.1),
            backdropFilter: 'blur(10px)',
            border: `1px solid ${isApiDown
              ? alpha(theme.palette.warning.main, 0.3)
              : isOnline
                ? alpha(theme.palette.success.main, 0.3)
                : alpha(theme.palette.error.main, 0.3)}`,
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
              backgroundColor: alpha(theme.palette.warning.main, 0.1),
              backdropFilter: 'blur(10px)',
              border: `1px solid ${alpha(theme.palette.warning.main, 0.3)}`,
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

      {/* API Down Alert */}
      <Snackbar
        open={showApiDownAlert}
        autoHideDuration={6000}
        onClose={() => setShowApiDownAlert(false)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert
          onClose={() => setShowApiDownAlert(false)}
          severity="warning"
          sx={{ width: '100%' }}
          icon={<Cloud />}
        >
          <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
            API server unreachable
          </Typography>
          <Typography variant="body2">
            Your internet is working but the server isn't responding. Uploads are disabled.
          </Typography>
        </Alert>
      </Snackbar>

    </>
  );
};

export default OfflineStatus;
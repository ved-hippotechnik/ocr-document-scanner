import React, { useState, useEffect } from 'react';
import { Button, Dialog, DialogActions, DialogContent, DialogTitle, Typography, Box, IconButton } from '@mui/material';
import { Close, InstallMobile, GetApp } from '@mui/icons-material';

const PWAInstallPrompt = () => {
  const [deferredPrompt, setDeferredPrompt] = useState(null);
  const [showInstallDialog, setShowInstallDialog] = useState(false);
  const [isInstalled, setIsInstalled] = useState(false);

  useEffect(() => {
    // Check if app is already installed
    const isStandalone = window.matchMedia('(display-mode: standalone)').matches;
    const isWebApp = window.navigator.standalone === true;
    setIsInstalled(isStandalone || isWebApp);

    // Listen for beforeinstallprompt event
    const handleBeforeInstallPrompt = (e) => {
      e.preventDefault();
      setDeferredPrompt(e);
    };

    // Listen for app installed event
    const handleAppInstalled = () => {
      setIsInstalled(true);
      setDeferredPrompt(null);
    };

    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
    window.addEventListener('appinstalled', handleAppInstalled);

    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
      window.removeEventListener('appinstalled', handleAppInstalled);
    };
  }, []);

  const handleInstallClick = () => {
    setShowInstallDialog(true);
  };

  const handleInstallConfirm = async () => {
    if (deferredPrompt) {
      deferredPrompt.prompt();
      const result = await deferredPrompt.userChoice;
      
      if (result.outcome === 'accepted') {
        setIsInstalled(true);
      }
      
      setDeferredPrompt(null);
    }
    setShowInstallDialog(false);
  };

  const handleInstallCancel = () => {
    setShowInstallDialog(false);
  };

  // Don't show install button if already installed or prompt not available
  if (isInstalled || !deferredPrompt) {
    return null;
  }

  return (
    <>
      <Button
        variant="outlined"
        startIcon={<InstallMobile />}
        onClick={handleInstallClick}
        sx={{
          position: 'fixed',
          top: 16,
          right: 16,
          zIndex: 1300,
          backgroundColor: 'rgba(255, 255, 255, 0.9)',
          backdropFilter: 'blur(10px)',
          border: '1px solid rgba(0, 122, 255, 0.3)',
          '&:hover': {
            backgroundColor: 'rgba(0, 122, 255, 0.1)',
          }
        }}
      >
        Install App
      </Button>

      <Dialog
        open={showInstallDialog}
        onClose={handleInstallCancel}
        maxWidth="sm"
        fullWidth
        PaperProps={{
          sx: {
            borderRadius: 3,
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            color: 'white'
          }
        }}
      >
        <DialogTitle sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <GetApp sx={{ mr: 1 }} />
            Install OCR Scanner
          </Box>
          <IconButton onClick={handleInstallCancel} sx={{ color: 'white' }}>
            <Close />
          </IconButton>
        </DialogTitle>
        
        <DialogContent>
          <Typography variant="body1" sx={{ mb: 2 }}>
            Install OCR Scanner for the best experience:
          </Typography>
          
          <Box sx={{ mb: 2 }}>
            <Typography variant="body2" sx={{ mb: 1, display: 'flex', alignItems: 'center' }}>
              📱 <span style={{ marginLeft: 8 }}>Works offline</span>
            </Typography>
            <Typography variant="body2" sx={{ mb: 1, display: 'flex', alignItems: 'center' }}>
              🚀 <span style={{ marginLeft: 8 }}>Faster performance</span>
            </Typography>
            <Typography variant="body2" sx={{ mb: 1, display: 'flex', alignItems: 'center' }}>
              🔔 <span style={{ marginLeft: 8 }}>Push notifications</span>
            </Typography>
            <Typography variant="body2" sx={{ mb: 1, display: 'flex', alignItems: 'center' }}>
              🎯 <span style={{ marginLeft: 8 }}>Quick access shortcuts</span>
            </Typography>
          </Box>
          
          <Typography variant="body2" sx={{ opacity: 0.8 }}>
            The app will be installed on your device and can be accessed like any other app.
          </Typography>
        </DialogContent>
        
        <DialogActions sx={{ px: 3, pb: 3 }}>
          <Button onClick={handleInstallCancel} sx={{ color: 'white' }}>
            Maybe Later
          </Button>
          <Button
            onClick={handleInstallConfirm}
            variant="contained"
            sx={{
              backgroundColor: 'rgba(255, 255, 255, 0.2)',
              '&:hover': {
                backgroundColor: 'rgba(255, 255, 255, 0.3)'
              }
            }}
          >
            Install Now
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default PWAInstallPrompt;
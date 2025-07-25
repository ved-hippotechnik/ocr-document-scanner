import React, { useState, useEffect } from 'react';
import { Snackbar, Alert, Button, Typography } from '@mui/material';
import { Update, Refresh } from '@mui/icons-material';
import { usePWA } from '../hooks/usePWA';

const UpdatePrompt = () => {
  const { updateAvailable, updateApp } = usePWA();
  const [showUpdatePrompt, setShowUpdatePrompt] = useState(false);
  const [updating, setUpdating] = useState(false);

  useEffect(() => {
    if (updateAvailable) {
      setShowUpdatePrompt(true);
    }
  }, [updateAvailable]);

  const handleUpdate = async () => {
    setUpdating(true);
    try {
      await updateApp();
      // The app will reload automatically after update
    } catch (error) {
      console.error('Error updating app:', error);
      setUpdating(false);
    }
  };

  const handleDismiss = () => {
    setShowUpdatePrompt(false);
  };

  return (
    <Snackbar
      open={showUpdatePrompt}
      anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
      sx={{ mt: 2 }}
    >
      <Alert
        severity="info"
        sx={{ 
          width: '100%',
          backgroundColor: 'rgba(25, 118, 210, 0.1)',
          backdropFilter: 'blur(10px)',
          border: '1px solid rgba(25, 118, 210, 0.3)'
        }}
        icon={<Update />}
        action={
          <div>
            <Button
              color="inherit"
              size="small"
              onClick={handleUpdate}
              disabled={updating}
              startIcon={updating ? <Refresh className="spinning" /> : <Update />}
              sx={{ mr: 1 }}
            >
              {updating ? 'Updating...' : 'Update'}
            </Button>
            <Button
              color="inherit"
              size="small"
              onClick={handleDismiss}
              disabled={updating}
            >
              Later
            </Button>
          </div>
        }
      >
        <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
          App Update Available
        </Typography>
        <Typography variant="body2">
          A new version of OCR Scanner is ready to install.
        </Typography>
      </Alert>
    </Snackbar>
  );
};

export default UpdatePrompt;
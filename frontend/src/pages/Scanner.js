import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  Button,
  Container,
  Paper,
  Typography,
  IconButton,
  CircularProgress,
  Alert,
  Snackbar,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Divider,
  Grid,
} from '@mui/material';
import {
  CameraAlt as CameraIcon,
  Upload as UploadIcon,
  Close as CloseIcon,
  DocumentScanner as ScanIcon,
  PhotoCamera as CameraAltIcon,
} from '@mui/icons-material';
import axios from 'axios';

const Scanner = () => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState(null);
  const [scanResult, setScanResult] = useState(null);
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [stream, setStream] = useState(null);
  const videoRef = useRef(null);
  const fileInputRef = useRef(null);

  // Handle video stream when dialog opens/closes
  useEffect(() => {
    if (dialogOpen && stream && videoRef.current) {
      videoRef.current.srcObject = stream;
    }
  }, [dialogOpen, stream]);

  // Cleanup stream on component unmount
  useEffect(() => {
    return () => {
      if (stream) {
        stream.getTracks().forEach(track => track.stop());
      }
    };
  }, [stream]);

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file) {
      setSelectedFile(file);
      const reader = new FileReader();
      reader.onloadend = () => {
        setPreview(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleDragOver = (event) => {
    event.preventDefault();
    event.stopPropagation();
  };

  const handleDrop = (event) => {
    event.preventDefault();
    event.stopPropagation();

    const file = event.dataTransfer.files[0];
    if (file) {
      setSelectedFile(file);
      const reader = new FileReader();
      reader.onloadend = () => {
        setPreview(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const startCamera = async () => {
    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({ 
        video: { 
          width: { ideal: 1280 },
          height: { ideal: 720 },
          facingMode: 'environment' // Use back camera if available
        } 
      });
      setStream(mediaStream);
      setDialogOpen(true);
    } catch (err) {
      console.error('Camera access error:', err);
      setError('Could not access camera: ' + err.message);
      setSnackbarMessage('Could not access camera: ' + err.message);
      setSnackbarOpen(true);
    }
  };

  const stopCamera = () => {
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
      setStream(null);
    }
    setDialogOpen(false);
  };

  const captureImage = () => {
    if (!videoRef.current) {
      setError('Camera not available');
      setSnackbarOpen(true);
      return;
    }

    try {
      const canvas = document.createElement('canvas');
      canvas.width = videoRef.current.videoWidth;
      canvas.height = videoRef.current.videoHeight;
      
      if (canvas.width === 0 || canvas.height === 0) {
        setError('Camera feed not ready. Please wait and try again.');
        setSnackbarOpen(true);
        return;
      }
      
      const ctx = canvas.getContext('2d');
      ctx.drawImage(videoRef.current, 0, 0);
      const imageDataUrl = canvas.toDataURL('image/jpeg', 0.8);
      
      setPreview(imageDataUrl);
      const file = dataURLtoFile(imageDataUrl, 'capture.jpg');
      
      if (file) {
        setSelectedFile(file);
        setSnackbarMessage('Image captured successfully!');
        setSnackbarOpen(true);
      }
      
      stopCamera();
    } catch (error) {
      console.error('Error capturing image:', error);
      setError('Error capturing image: ' + error.message);
      setSnackbarOpen(true);
    }
  };

  const dataURLtoFile = (dataurl, filename) => {
    try {
      const arr = dataurl.split(',');
      if (arr.length !== 2) {
        throw new Error('Invalid data URL format');
      }
      
      const mimeMatch = arr[0].match(/:(.*?);/);
      if (!mimeMatch) {
        throw new Error('Could not extract MIME type from data URL');
      }
      
      const mime = mimeMatch[1];
      const bstr = atob(arr[1]);
      let n = bstr.length;
      const u8arr = new Uint8Array(n);
      while (n--) {
        u8arr[n] = bstr.charCodeAt(n);
      }
      return new File([u8arr], filename, { type: mime });
    } catch (error) {
      console.error('Error converting data URL to file:', error);
      setError('Error processing captured image: ' + error.message);
      setSnackbarOpen(true);
      return null;
    }
  };

  const handleScan = async () => {
    if (!selectedFile) {
      setError('Please select or capture an image first');
      setSnackbarOpen(true);
      return;
    }

    setScanning(true);
    setError(null);
    setScanResult(null);

    const formData = new FormData();
    formData.append('image', selectedFile);

    try {
      const response = await axios.post('http://localhost:5002/api/scan', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });

      setScanResult(response.data);
      setSnackbarMessage('Document scanned successfully!');
      setSnackbarOpen(true);
    } catch (err) {
      setError('Error scanning document: ' + (err.response?.data?.message || err.message));
      setSnackbarOpen(true);
    } finally {
      setScanning(false);
    }
  };

  const resetScan = () => {
    setSelectedFile(null);
    setPreview(null);
    setScanResult(null);
    setError(null);
  };

  return (
    <Container maxWidth="lg" sx={{ mt: { xs: 2, sm: 3, md: 4 }, mb: { xs: 2, sm: 3, md: 4 } }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom sx={{ 
          display: 'flex', 
          alignItems: 'center',
          fontSize: { xs: '1.5rem', sm: '1.75rem', md: '2rem' }
        }}>
          <ScanIcon sx={{ mr: 1, fontSize: { xs: 24, sm: 28, md: 32 } }} />
          Document Scanner
        </Typography>
        <Typography variant="subtitle1" color="text.secondary">
          Upload or capture documents to extract information using OCR
        </Typography>
      </Box>

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper
            elevation={0}
            className="apple-card"
            sx={{
              p: { xs: 2, sm: 3 },
              height: '100%',
              borderRadius: 3,
              background: 'linear-gradient(145deg, rgba(255,255,255,0.9) 0%, rgba(255,255,255,0.6) 100%)',
              backdropFilter: 'blur(10px)',
              WebkitBackdropFilter: 'blur(10px)',
              boxShadow: '0 4px 20px rgba(0, 0, 0, 0.05)',
              border: '1px solid rgba(255, 255, 255, 0.3)',
            }}
          >
            <Box
              sx={{
                height: 400,
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'center',
                alignItems: 'center',
                border: '2px dashed rgba(0, 0, 0, 0.1)',
                borderRadius: 2,
                position: 'relative',
                overflow: 'hidden',
                backgroundColor: 'rgba(255, 255, 255, 0.5)',
              }}
              onDragOver={handleDragOver}
              onDrop={handleDrop}
            >
              {preview ? (
                <>
                  <img
                    src={preview}
                    alt="Document preview"
                    style={{
                      maxWidth: '100%',
                      maxHeight: '100%',
                      objectFit: 'contain'
                    }}
                  />
                  <Box
                    sx={{
                      position: 'absolute',
                      top: 8,
                      right: 8,
                      bgcolor: 'rgba(255, 255, 255, 0.9)',
                      borderRadius: '50%',
                    }}
                  >
                    <IconButton size="small" onClick={resetScan}>
                      <CloseIcon />
                    </IconButton>
                  </Box>
                </>
              ) : (
                <Box sx={{ textAlign: 'center', p: 3 }}>
                  <UploadIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
                  <Typography variant="h6" gutterBottom>
                    Drag and drop your document here
                  </Typography>
                  <Typography variant="body2" color="text.secondary" paragraph>
                    or use one of the options below
                  </Typography>
                  <Box sx={{ mt: 2 }}>
                    <Button
                      variant="contained"
                      component="label"
                      startIcon={<UploadIcon />}
                      sx={{ mr: 2 }}
                    >
                      Upload File
                      <input
                        type="file"
                        hidden
                        accept="image/*"
                        onChange={handleFileSelect}
                        ref={fileInputRef}
                      />
                    </Button>
                    <Button
                      variant="outlined"
                      startIcon={<CameraIcon />}
                      onClick={startCamera}
                    >
                      Use Camera
                    </Button>
                  </Box>
                </Box>
              )}
            </Box>

            <Box sx={{ mt: 3, display: 'flex', justifyContent: 'center' }}>
              <Button
                variant="contained"
                size="large"
                startIcon={<ScanIcon />}
                onClick={handleScan}
                disabled={!selectedFile || scanning}
                sx={{
                  px: 4,
                  py: 1,
                  borderRadius: 3,
                  fontSize: '1.1rem'
                }}
              >
                {scanning ? 'Scanning...' : 'Scan Document'}
              </Button>
            </Box>
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper
            elevation={0}
            className="apple-card"
            sx={{
              p: { xs: 2, sm: 3 },
              height: '100%',
              borderRadius: 3,
              background: 'linear-gradient(145deg, rgba(255,255,255,0.9) 0%, rgba(255,255,255,0.6) 100%)',
              backdropFilter: 'blur(10px)',
              WebkitBackdropFilter: 'blur(10px)',
              boxShadow: '0 4px 20px rgba(0, 0, 0, 0.05)',
              border: '1px solid rgba(255, 255, 255, 0.3)',
            }}
          >
            {scanning ? (
              <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', py: 8 }}>
                <CircularProgress size={48} sx={{ mb: 2 }} />
                <Typography variant="h6">Processing document...</Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                  This may take a few moments
                </Typography>
              </Box>
            ) : scanResult ? (
              <Box>
                <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                  Scan Results
                </Typography>
                <Divider sx={{ my: 2 }} />
                <Box sx={{ mt: 2 }}>
                  <Typography variant="subtitle1" gutterBottom>
                    Document Type: {scanResult.document_type}
                  </Typography>
                  <Typography variant="subtitle1" gutterBottom>
                    Nationality: {scanResult.nationality}
                  </Typography>
                  {scanResult.processing_method && (
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Processing: {scanResult.processing_method} 
                      {scanResult.confidence && ` (${scanResult.confidence} confidence)`}
                      {scanResult.processing_method === 'enhanced_emirates_id' && ' 🇦🇪'}
                      {scanResult.processing_method === 'enhanced_driving_license' && ' 🚗'}
                      {scanResult.processing_method === 'enhanced_aadhaar' && ' 🇮🇳'}
                    </Typography>
                  )}
                  {scanResult.extracted_info && (
                    <Box sx={{ mt: 2 }}>
                      <Typography variant="subtitle1" gutterBottom>
                        Extracted Information:
                      </Typography>
                      {Object.entries(scanResult.extracted_info)
                        .filter(([key, value]) => {
                          // Skip rendering the raw mrz_data object as it's too complex
                          if (key === 'mrz_data') {
                            return false;
                          }
                          
                          // Hide empty, null, undefined, or whitespace-only values
                          if (value === null || value === undefined || value === '') {
                            return false;
                          }
                          
                          // Hide whitespace-only strings
                          if (typeof value === 'string' && value.trim() === '') {
                            return false;
                          }
                          
                          // Hide empty objects and arrays
                          if (typeof value === 'object') {
                            if (Array.isArray(value) && value.length === 0) {
                              return false;
                            }
                            if (!Array.isArray(value) && Object.keys(value).length === 0) {
                              return false;
                            }
                          }
                          
                          return true;
                        })
                        .map(([key, value]) => {
                          // Convert value to displayable string
                          let displayValue;
                          if (typeof value === 'object') {
                            displayValue = JSON.stringify(value, null, 2);
                          } else {
                            displayValue = String(value);
                          }
                          
                          return (
                            <Typography key={key} variant="body2" sx={{ mb: 1 }}>
                              <strong>{key.replace(/_/g, ' ').toUpperCase()}:</strong> {displayValue}
                            </Typography>
                          );
                        })}
                    </Box>
                  )}
                </Box>
              </Box>
            ) : (
              <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', py: 8 }}>
                <ScanIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
                <Typography variant="h6">No scan results yet</Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                  Select or capture a document to start scanning
                </Typography>
              </Box>
            )}
          </Paper>
        </Grid>
      </Grid>

      {/* Camera Dialog */}
      <Dialog
        open={dialogOpen}
        onClose={stopCamera}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="h6">Capture Document</Typography>
            <IconButton edge="end" onClick={stopCamera}>
              <CloseIcon />
            </IconButton>
          </Box>
        </DialogTitle>
        <DialogContent>
          <Box sx={{ position: 'relative', width: '100%', height: 400 }}>
            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              onLoadedMetadata={() => {
                if (videoRef.current) {
                  videoRef.current.play();
                }
              }}
              style={{
                width: '100%',
                height: '100%',
                objectFit: 'cover',
                borderRadius: 8,
                backgroundColor: '#000'
              }}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={stopCamera}>Cancel</Button>
          <Button
            variant="contained"
            startIcon={<CameraAltIcon />}
            onClick={captureImage}
          >
            Capture
          </Button>
        </DialogActions>
      </Dialog>


      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbarOpen}
        autoHideDuration={6000}
        onClose={() => setSnackbarOpen(false)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert
          onClose={() => setSnackbarOpen(false)}
          severity={error ? 'error' : 'success'}
          sx={{ width: '100%' }}
        >
          {error || snackbarMessage}
        </Alert>
      </Snackbar>
    </Container>
  );
};

export default Scanner;

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
  Card,
  CardContent,
  Chip,
  LinearProgress,
  Switch,
  FormControlLabel,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Rating,
} from '@mui/material';
import {
  CameraAlt as CameraIcon,
  Upload as UploadIcon,
  Close as CloseIcon,
  DocumentScanner as ScanIcon,
  PhotoCamera as CameraAltIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  ExpandMore as ExpandMoreIcon,
  Speed as SpeedIcon,
  Assessment as AssessmentIcon,
  Security as SecurityIcon,
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
  const [qualityAssessment, setQualityAssessment] = useState(null);
  const [classificationResult, setClassificationResult] = useState(null);
  const [useEnhancedAPI, setUseEnhancedAPI] = useState(true);
  const [enableQualityCheck, setEnableQualityCheck] = useState(true);
  const [processingStats, setProcessingStats] = useState(null);
  const [documentType, setDocumentType] = useState('');
  
  const videoRef = useRef(null);
  const fileInputRef = useRef(null);

  // Available document types
  const documentTypes = [
    { value: '', label: 'Auto-detect' },
    { value: 'aadhaar', label: 'Aadhaar Card (India)' },
    { value: 'emirates_id', label: 'Emirates ID (UAE)' },
    { value: 'driving_license', label: 'Driving License (India)' },
    { value: 'passport', label: 'Passport (India)' },
    { value: 'drivers_license', label: 'Driver\'s License (US)' },
  ];

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
      reader.onload = (e) => {
        setPreview(e.target.result);
      };
      reader.readAsDataURL(file);
      
      // Reset previous results
      setScanResult(null);
      setQualityAssessment(null);
      setClassificationResult(null);
      setError(null);
    }
  };

  const handleDrop = (event) => {
    event.preventDefault();
    const file = event.dataTransfer.files[0];
    if (file && file.type.startsWith('image/')) {
      setSelectedFile(file);
      const reader = new FileReader();
      reader.onload = (e) => {
        setPreview(e.target.result);
      };
      reader.readAsDataURL(file);
      
      // Reset previous results
      setScanResult(null);
      setQualityAssessment(null);
      setClassificationResult(null);
      setError(null);
    }
  };

  const handleDragOver = (event) => {
    event.preventDefault();
  };

  const convertToBase64 = (file) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => {
        const base64 = reader.result.split(',')[1];
        resolve(base64);
      };
      reader.onerror = (error) => reject(error);
    });
  };

  const handleScan = async () => {
    if (!selectedFile) {
      showSnackbar('Please select an image first');
      return;
    }

    setScanning(true);
    setError(null);
    setScanResult(null);
    setQualityAssessment(null);
    setClassificationResult(null);

    try {
      const base64Image = await convertToBase64(selectedFile);
      const startTime = Date.now();

      if (useEnhancedAPI) {
        // Use enhanced API v2
        const response = await axios.post('/api/v2/scan', {
          image: base64Image,
          document_type: documentType || undefined,
          options: {
            enable_quality_check: enableQualityCheck,
            return_processed_images: false,
            ocr_language: 'eng'
          }
        });

        const processingTime = Date.now() - startTime;
        setProcessingStats({
          processingTime: processingTime,
          apiVersion: 'v2',
          serverProcessingTime: response.data.processing_time
        });

        if (response.data.success) {
          setScanResult(response.data);
          if (response.data.quality_score !== undefined) {
            setQualityAssessment({
              quality_score: response.data.quality_score,
              issues: response.data.quality_issues || []
            });
          }
          showSnackbar('Document scanned successfully!');
        } else {
          setError(response.data.error);
        }
      } else {
        // Use legacy API
        const response = await axios.post('/api/scan', {
          image: base64Image,
          document_type: documentType || undefined
        });

        const processingTime = Date.now() - startTime;
        setProcessingStats({
          processingTime: processingTime,
          apiVersion: 'v1',
          serverProcessingTime: response.data.processing_time
        });

        if (response.data.success) {
          setScanResult(response.data);
          showSnackbar('Document scanned successfully!');
        } else {
          setError(response.data.error);
        }
      }
    } catch (error) {
      console.error('Scan error:', error);
      if (error.response?.data?.error) {
        setError(error.response.data.error);
      } else {
        setError({
          code: 'NETWORK_ERROR',
          message: 'Failed to communicate with server',
          details: error.message
        });
      }
    } finally {
      setScanning(false);
    }
  };

  const handleClassifyOnly = async () => {
    if (!selectedFile) {
      showSnackbar('Please select an image first');
      return;
    }

    setScanning(true);
    setError(null);
    setClassificationResult(null);

    try {
      const base64Image = await convertToBase64(selectedFile);
      const response = await axios.post('/api/v2/classify', {
        image: base64Image
      });

      if (response.data.success) {
        setClassificationResult(response.data);
        showSnackbar('Document classified successfully!');
      } else {
        setError(response.data.error);
      }
    } catch (error) {
      console.error('Classification error:', error);
      if (error.response?.data?.error) {
        setError(error.response.data.error);
      } else {
        setError({
          code: 'NETWORK_ERROR',
          message: 'Failed to communicate with server',
          details: error.message
        });
      }
    } finally {
      setScanning(false);
    }
  };

  const handleQualityCheck = async () => {
    if (!selectedFile) {
      showSnackbar('Please select an image first');
      return;
    }

    setScanning(true);
    setError(null);
    setQualityAssessment(null);

    try {
      const base64Image = await convertToBase64(selectedFile);
      const response = await axios.post('/api/v2/quality', {
        image: base64Image
      });

      if (response.data.success) {
        setQualityAssessment(response.data);
        showSnackbar('Quality assessment completed!');
      } else {
        setError(response.data.error);
      }
    } catch (error) {
      console.error('Quality check error:', error);
      if (error.response?.data?.error) {
        setError(error.response.data.error);
      } else {
        setError({
          code: 'NETWORK_ERROR',
          message: 'Failed to communicate with server',
          details: error.message
        });
      }
    } finally {
      setScanning(false);
    }
  };

  const startCamera = async () => {
    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment' }
      });
      setStream(mediaStream);
      setDialogOpen(true);
    } catch (error) {
      console.error('Camera error:', error);
      showSnackbar('Could not access camera');
    }
  };

  const capturePhoto = () => {
    if (videoRef.current && stream) {
      const canvas = document.createElement('canvas');
      const video = videoRef.current;
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      const ctx = canvas.getContext('2d');
      ctx.drawImage(video, 0, 0);
      
      canvas.toBlob((blob) => {
        const file = new File([blob], 'captured-photo.jpg', { type: 'image/jpeg' });
        setSelectedFile(file);
        setPreview(canvas.toDataURL());
        handleCloseCamera();
        
        // Reset previous results
        setScanResult(null);
        setQualityAssessment(null);
        setClassificationResult(null);
        setError(null);
      }, 'image/jpeg');
    }
  };

  const handleCloseCamera = () => {
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
      setStream(null);
    }
    setDialogOpen(false);
  };

  const showSnackbar = (message) => {
    setSnackbarMessage(message);
    setSnackbarOpen(true);
  };

  const clearSelection = () => {
    setSelectedFile(null);
    setPreview(null);
    setScanResult(null);
    setQualityAssessment(null);
    setClassificationResult(null);
    setError(null);
    setProcessingStats(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const getQualityColor = (score) => {
    if (score >= 0.8) return 'success';
    if (score >= 0.5) return 'warning';
    return 'error';
  };

  const getQualityLabel = (score) => {
    if (score >= 0.8) return 'High Quality';
    if (score >= 0.5) return 'Medium Quality';
    return 'Low Quality';
  };

  const getSeverityIcon = (severity) => {
    switch (severity) {
      case 'high': return <ErrorIcon color="error" />;
      case 'medium': return <WarningIcon color="warning" />;
      case 'low': return <InfoIcon color="info" />;
      default: return <InfoIcon color="info" />;
    }
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography variant="h3" component="h1" gutterBottom align="center" sx={{ mb: 4 }}>
        Document Scanner
      </Typography>

      {/* Configuration Panel */}
      <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Configuration
        </Typography>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={6} md={3}>
            <FormControlLabel
              control={
                <Switch
                  checked={useEnhancedAPI}
                  onChange={(e) => setUseEnhancedAPI(e.target.checked)}
                />
              }
              label="Use Enhanced API v2"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <FormControlLabel
              control={
                <Switch
                  checked={enableQualityCheck}
                  onChange={(e) => setEnableQualityCheck(e.target.checked)}
                  disabled={!useEnhancedAPI}
                />
              }
              label="Quality Check"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={6}>
            <FormControl fullWidth size="small">
              <InputLabel>Document Type</InputLabel>
              <Select
                value={documentType}
                onChange={(e) => setDocumentType(e.target.value)}
                label="Document Type"
              >
                {documentTypes.map((type) => (
                  <MenuItem key={type.value} value={type.value}>
                    {type.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
        </Grid>
      </Paper>

      <Grid container spacing={4}>
        {/* Upload Section */}
        <Grid item xs={12} md={6}>
          <Paper elevation={3} sx={{ p: 3, height: 'fit-content' }}>
            <Typography variant="h5" gutterBottom>
              Upload Document
            </Typography>
            
            {!preview ? (
              <Box
                sx={{
                  border: '2px dashed #ccc',
                  borderRadius: 2,
                  p: 4,
                  textAlign: 'center',
                  minHeight: 300,
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'center',
                  alignItems: 'center',
                  cursor: 'pointer',
                  '&:hover': {
                    backgroundColor: '#f5f5f5',
                  },
                }}
                onDrop={handleDrop}
                onDragOver={handleDragOver}
                onClick={() => fileInputRef.current?.click()}
              >
                <UploadIcon sx={{ fontSize: 64, color: '#ccc', mb: 2 }} />
                <Typography variant="h6" color="textSecondary" gutterBottom>
                  Drop your document here or click to browse
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Supports JPG, PNG, WEBP (max 10MB)
                </Typography>
              </Box>
            ) : (
              <Box sx={{ position: 'relative' }}>
                <img
                  src={preview}
                  alt="Preview"
                  style={{
                    width: '100%',
                    height: 'auto',
                    maxHeight: 400,
                    objectFit: 'contain',
                    borderRadius: 8,
                  }}
                />
                <IconButton
                  sx={{
                    position: 'absolute',
                    top: 8,
                    right: 8,
                    backgroundColor: 'rgba(0,0,0,0.5)',
                    color: 'white',
                    '&:hover': {
                      backgroundColor: 'rgba(0,0,0,0.7)',
                    },
                  }}
                  onClick={clearSelection}
                >
                  <CloseIcon />
                </IconButton>
              </Box>
            )}

            <input
              type="file"
              accept="image/*"
              onChange={handleFileSelect}
              style={{ display: 'none' }}
              ref={fileInputRef}
            />

            <Box sx={{ mt: 2, display: 'flex', gap: 2, flexWrap: 'wrap' }}>
              <Button
                variant="contained"
                startIcon={<UploadIcon />}
                onClick={() => fileInputRef.current?.click()}
              >
                Browse Files
              </Button>
              <Button
                variant="outlined"
                startIcon={<CameraIcon />}
                onClick={startCamera}
              >
                Take Photo
              </Button>
              {selectedFile && (
                <>
                  <Button
                    variant="contained"
                    color="primary"
                    startIcon={<ScanIcon />}
                    onClick={handleScan}
                    disabled={scanning}
                  >
                    {scanning ? <CircularProgress size={20} /> : 'Scan Document'}
                  </Button>
                  {useEnhancedAPI && (
                    <>
                      <Button
                        variant="outlined"
                        startIcon={<AssessmentIcon />}
                        onClick={handleClassifyOnly}
                        disabled={scanning}
                      >
                        Classify Only
                      </Button>
                      <Button
                        variant="outlined"
                        startIcon={<SecurityIcon />}
                        onClick={handleQualityCheck}
                        disabled={scanning}
                      >
                        Quality Check
                      </Button>
                    </>
                  )}
                </>
              )}
            </Box>
          </Paper>
        </Grid>

        {/* Results Section */}
        <Grid item xs={12} md={6}>
          <Paper elevation={3} sx={{ p: 3 }}>
            <Typography variant="h5" gutterBottom>
              Results
            </Typography>

            {error && (
              <Alert severity="error" sx={{ mb: 2 }}>
                <Typography variant="subtitle2">{error.message}</Typography>
                {error.details && (
                  <Typography variant="body2" sx={{ mt: 1 }}>
                    {error.details}
                  </Typography>
                )}
              </Alert>
            )}

            {processingStats && (
              <Card sx={{ mb: 2 }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    <SpeedIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                    Performance Stats
                  </Typography>
                  <Grid container spacing={2}>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="textSecondary">
                        API Version: {processingStats.apiVersion}
                      </Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="textSecondary">
                        Total Time: {processingStats.processingTime}ms
                      </Typography>
                    </Grid>
                    {processingStats.serverProcessingTime && (
                      <Grid item xs={12}>
                        <Typography variant="body2" color="textSecondary">
                          Server Processing: {processingStats.serverProcessingTime}s
                        </Typography>
                      </Grid>
                    )}
                  </Grid>
                </CardContent>
              </Card>
            )}

            {qualityAssessment && (
              <Card sx={{ mb: 2 }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Quality Assessment
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <Rating
                      value={qualityAssessment.quality_score * 5}
                      precision={0.1}
                      readOnly
                      sx={{ mr: 2 }}
                    />
                    <Chip
                      label={getQualityLabel(qualityAssessment.quality_score)}
                      color={getQualityColor(qualityAssessment.quality_score)}
                      size="small"
                    />
                    <Typography variant="body2" sx={{ ml: 1 }}>
                      ({(qualityAssessment.quality_score * 100).toFixed(1)}%)
                    </Typography>
                  </Box>
                  
                  {qualityAssessment.issues && qualityAssessment.issues.length > 0 && (
                    <Accordion>
                      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                        <Typography>Quality Issues ({qualityAssessment.issues.length})</Typography>
                      </AccordionSummary>
                      <AccordionDetails>
                        <List dense>
                          {qualityAssessment.issues.map((issue, index) => (
                            <ListItem key={index}>
                              <ListItemIcon>
                                {getSeverityIcon(issue.severity)}
                              </ListItemIcon>
                              <ListItemText
                                primary={issue.type}
                                secondary={issue.description}
                              />
                            </ListItem>
                          ))}
                        </List>
                      </AccordionDetails>
                    </Accordion>
                  )}

                  {qualityAssessment.recommendations && (
                    <Accordion>
                      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                        <Typography>Recommendations</Typography>
                      </AccordionSummary>
                      <AccordionDetails>
                        <List dense>
                          {qualityAssessment.recommendations.map((rec, index) => (
                            <ListItem key={index}>
                              <ListItemIcon>
                                <CheckCircleIcon color="success" />
                              </ListItemIcon>
                              <ListItemText primary={rec} />
                            </ListItem>
                          ))}
                        </List>
                      </AccordionDetails>
                    </Accordion>
                  )}
                </CardContent>
              </Card>
            )}

            {classificationResult && (
              <Card sx={{ mb: 2 }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Document Classification
                  </Typography>
                  <Grid container spacing={2}>
                    <Grid item xs={12}>
                      <Typography variant="body1">
                        <strong>Type:</strong> {classificationResult.document_type}
                      </Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="textSecondary">
                        Confidence: {(classificationResult.confidence * 100).toFixed(1)}%
                      </Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="textSecondary">
                        Country: {classificationResult.country}
                      </Typography>
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            )}

            {scanResult && (
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Extracted Information
                  </Typography>
                  
                  <Box sx={{ mb: 2 }}>
                    <Chip
                      label={scanResult.document_type}
                      color="primary"
                      sx={{ mr: 1 }}
                    />
                    <Chip
                      label={`${(scanResult.confidence * 100).toFixed(1)}% confidence`}
                      color={scanResult.confidence > 0.8 ? 'success' : 'warning'}
                    />
                  </Box>

                  {scanResult.extracted_info && (
                    <Box>
                      {Object.entries(scanResult.extracted_info).map(([key, value]) => {
                        if (key === 'raw_text' || !value) return null;
                        return (
                          <Box key={key} sx={{ mb: 1 }}>
                            <Typography variant="body2" color="textSecondary">
                              {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}:
                            </Typography>
                            <Typography variant="body1" sx={{ ml: 2 }}>
                              {value}
                            </Typography>
                          </Box>
                        );
                      })}
                    </Box>
                  )}
                </CardContent>
              </Card>
            )}

            {!scanResult && !error && !classificationResult && !qualityAssessment && (
              <Box
                sx={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  minHeight: 300,
                  color: 'text.secondary',
                }}
              >
                <ScanIcon sx={{ fontSize: 64, mb: 2 }} />
                <Typography variant="h6">
                  Upload a document to get started
                </Typography>
              </Box>
            )}
          </Paper>
        </Grid>
      </Grid>

      {/* Camera Dialog */}
      <Dialog
        open={dialogOpen}
        onClose={handleCloseCamera}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Capture Photo
          <IconButton
            onClick={handleCloseCamera}
            sx={{ position: 'absolute', right: 8, top: 8 }}
          >
            <CloseIcon />
          </IconButton>
        </DialogTitle>
        <DialogContent>
          <Box sx={{ textAlign: 'center' }}>
            <video
              ref={videoRef}
              autoPlay
              playsInline
              style={{ width: '100%', maxWidth: 640, height: 'auto' }}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseCamera}>
            Cancel
          </Button>
          <Button
            variant="contained"
            startIcon={<CameraAltIcon />}
            onClick={capturePhoto}
          >
            Capture
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar */}
      <Snackbar
        open={snackbarOpen}
        autoHideDuration={6000}
        onClose={() => setSnackbarOpen(false)}
        message={snackbarMessage}
      />
    </Container>
  );
};

export default Scanner;

import React, { useState, useCallback, useEffect, useRef } from 'react';
import { API_URL } from '../config';
import { validateFile, showValidationError, clearValidationError } from '../utils/validation';
import { connectSession } from '../utils/websocket';
import {
  Box,
  Button,
  Card,
  CardContent,
  Typography,
  Alert,
  LinearProgress,
  Chip,
  Grid,
  Paper,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Rating,
  Tooltip,
  FormControl,
  InputLabel,
  Select,
  MenuItem
} from '@mui/material';
import {
  CloudUpload,
  AutoAwesome,
  CheckCircle,
  Warning,
  Error,
  Info,
  Speed,
  CheckCircleOutline,
  ExpandMore,
  Psychology,
  Analytics,
  Security,
  Language
} from '@mui/icons-material';
import { useDropzone } from 'react-dropzone';
import { toast } from 'react-toastify';

const AIScanner = () => {
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingStage, setProcessingStage] = useState('');
  const [progress, setProgress] = useState(0);
  const [results, setResults] = useState(null);
  const [classification, setClassification] = useState(null);
  const [qualityAssessment, setQualityAssessment] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [selectedLanguage, setSelectedLanguage] = useState('auto');
  const [availableLanguages, setAvailableLanguages] = useState([]);
  const wsCleanupRef = useRef(null);

  useEffect(() => {
    fetch(`${API_URL}/api/languages`)
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          setAvailableLanguages(data.languages);
        }
      })
      .catch(() => {
        setAvailableLanguages([{ code: 'eng', name: 'English' }]);
      });
  }, []);

  const onDrop = useCallback((acceptedFiles) => {
    if (acceptedFiles.length > 0) {
      const file = acceptedFiles[0];
      const validation = validateFile(file);
      
      if (!validation.isValid) {
        toast.error(validation.error);
        return;
      }
      
      processDocument(file);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.gif', '.webp'],
      'application/pdf': ['.pdf']
    },
    maxFiles: 1,
    maxSize: 50 * 1024 * 1024, // 50MB - consistent with validation utility
    multiple: false
  });

  const processDocument = async (file) => {
    setIsProcessing(true);
    setProgress(0);
    setResults(null);
    setClassification(null);
    setQualityAssessment(null);
    setRecommendations([]);

    try {
      // Convert file to base64
      const base64 = await fileToBase64(file);
      
      // Generate session ID for progress tracking
      const sessionId = `scan_${Date.now()}`;
      
      // Setup WebSocket for real-time updates
      setupWebSocket(sessionId);
      
      // Create FormData for file upload
      const formData = new FormData();
      // Convert base64 to blob
      const base64Response = await fetch(base64);
      const blob = await base64Response.blob();
      formData.append('image', blob, file.name);
      formData.append('document_type', 'auto');
      formData.append('quality_check', 'true');
      formData.append('validate_document', 'true');
      formData.append('session_id', sessionId);
      if (selectedLanguage && selectedLanguage !== 'auto') {
        formData.append('language', selectedLanguage);
      }
      
      // Call AI-enhanced scan endpoint
      const response = await fetch(`${API_URL}/api/v3/scan`, {
        method: 'POST',
        headers: {
          'X-Session-ID': sessionId
        },
        body: formData
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      if (data.success) {
        setResults(data.ocr_result);
        setClassification(data.classification);
        setQualityAssessment(data.quality_assessment);
        setRecommendations(data.recommendations || []);
        
        toast.success('Document processed successfully!');
      } else {
        throw new Error(data.error || 'Processing failed');
      }
      
    } catch (error) {
      console.error('Processing error:', error);
      toast.error(`Processing failed: ${error.message}`);
    } finally {
      setIsProcessing(false);
      setProgress(100);
    }
  };

  const setupWebSocket = (sessionId) => {
    // Clean up any previous session
    if (wsCleanupRef.current) {
      wsCleanupRef.current();
    }

    const cleanup = connectSession(sessionId, {
      onStart: (data) => {
        setProcessingStage(data?.message || 'Processing started...');
      },
      onProgress: (data) => {
        if (data?.progress != null) {
          setProgress(Math.min(data.progress, 95));
        }
        if (data?.message) {
          setProcessingStage(data.message);
        }
      },
      onComplete: (data) => {
        setProgress(100);
        setProcessingStage('Processing complete');
      },
      onError: (data) => {
        setProcessingStage(`Error: ${data?.error || 'Unknown error'}`);
      },
    });

    wsCleanupRef.current = cleanup;
  };

  // Clean up WebSocket on unmount
  useEffect(() => {
    return () => {
      if (wsCleanupRef.current) {
        wsCleanupRef.current();
      }
    };
  }, []);

  const fileToBase64 = (file) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => resolve(reader.result);
      reader.onerror = error => reject(error);
    });
  };

  const getConfidenceColor = (confidence) => {
    if (confidence >= 0.8) return 'success';
    if (confidence >= 0.6) return 'warning';
    return 'error';
  };

  const getQualityColor = (score) => {
    if (score >= 0.8) return 'success';
    if (score >= 0.6) return 'warning';
    return 'error';
  };

  const getRecommendationIcon = (type) => {
    switch (type) {
      case 'success': return <CheckCircle />;
      case 'warning': return <Warning />;
      case 'error': return <Error />;
      default: return <Info />;
    }
  };

  return (
    <Box sx={{ maxWidth: 1200, mx: 'auto', p: 3 }}>
      <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <AutoAwesome color="primary" />
        AI-Enhanced Document Scanner
      </Typography>

      <Typography variant="body1" color="text.secondary" gutterBottom>
        Upload a document for automatic classification and intelligent OCR processing
      </Typography>

      {/* Upload Area */}
      <Card sx={{ mt: 3, mb: 3 }}>
        <CardContent>
          <Box
            {...getRootProps()}
            sx={{
              border: '2px dashed',
              borderColor: isDragActive ? 'primary.main' : 'grey.300',
              borderRadius: 2,
              p: 4,
              textAlign: 'center',
              cursor: 'pointer',
              bgcolor: isDragActive ? 'primary.50' : 'transparent',
              transition: 'all 0.2s ease'
            }}
          >
            <input {...getInputProps()} />
            <CloudUpload sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" gutterBottom>
              {isDragActive ? 'Drop the document here' : 'Drag & drop a document or click to browse'}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Supports JPG, PNG, TIFF, BMP, GIF, WebP, PDF (max 50MB)
            </Typography>
          </Box>

          {/* Language Selector */}
          <Box sx={{ mt: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
            <Language color="action" />
            <FormControl size="small" sx={{ minWidth: 220 }}>
              <InputLabel id="language-select-label">OCR Language</InputLabel>
              <Select
                labelId="language-select-label"
                value={selectedLanguage}
                label="OCR Language"
                onChange={(e) => setSelectedLanguage(e.target.value)}
              >
                <MenuItem value="auto">Auto-detect</MenuItem>
                {availableLanguages.map((lang) => (
                  <MenuItem key={lang.code} value={lang.code}>
                    {lang.name} ({lang.code})
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <Typography variant="caption" color="text.secondary">
              Select the document language for better OCR accuracy
            </Typography>
          </Box>
        </CardContent>
      </Card>

      {/* Processing Progress */}
      {isProcessing && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Processing Document...
            </Typography>
            <LinearProgress 
              variant="determinate" 
              value={progress} 
              sx={{ mb: 2, height: 8, borderRadius: 4 }}
            />
            <Typography variant="body2" color="text.secondary">
              {processingStage}
            </Typography>
          </CardContent>
        </Card>
      )}

      {/* Classification Results */}
      {classification && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Psychology color="primary" />
              AI Classification
            </Typography>
            
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <Paper sx={{ p: 2, bgcolor: 'grey.50' }}>
                  <Typography variant="subtitle1" gutterBottom>
                    Document Type
                  </Typography>
                  <Chip
                    label={classification.document_name}
                    color="primary"
                    variant="outlined"
                    sx={{ mb: 1 }}
                  />
                  <Typography variant="body2" color="text.secondary">
                    {classification.document_type}
                  </Typography>
                </Paper>
              </Grid>
              
              <Grid item xs={12} md={6}>
                <Paper sx={{ p: 2, bgcolor: 'grey.50' }}>
                  <Typography variant="subtitle1" gutterBottom>
                    Confidence Score
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Rating
                      value={classification.confidence * 5}
                      readOnly
                      precision={0.1}
                      max={5}
                    />
                    <Chip
                      label={`${(classification.confidence * 100).toFixed(1)}%`}
                      color={getConfidenceColor(classification.confidence)}
                      size="small"
                    />
                  </Box>
                </Paper>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      )}

      {/* Quality Assessment */}
      {qualityAssessment && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Analytics color="primary" />
              Quality Assessment
            </Typography>
            
            <Grid container spacing={2}>
              <Grid item xs={12} md={4}>
                <Paper sx={{ p: 2, textAlign: 'center' }}>
                  <Speed sx={{ fontSize: 32, color: 'primary.main', mb: 1 }} />
                  <Typography variant="h6">
                    {(qualityAssessment.overall_score * 100).toFixed(1)}%
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Overall Quality
                  </Typography>
                </Paper>
              </Grid>
              
              <Grid item xs={12} md={4}>
                <Paper sx={{ p: 2, textAlign: 'center' }}>
                  <CheckCircleOutline sx={{ fontSize: 32, color: 'success.main', mb: 1 }} />
                  <Typography variant="h6">
                    {(qualityAssessment.extraction_completeness * 100).toFixed(1)}%
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Completeness
                  </Typography>
                </Paper>
              </Grid>
              
              <Grid item xs={12} md={4}>
                <Paper sx={{ p: 2, textAlign: 'center' }}>
                  <Security sx={{ fontSize: 32, color: 'warning.main', mb: 1 }} />
                  <Typography variant="h6">
                    {(qualityAssessment.data_validity.overall_validity * 100).toFixed(1)}%
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Data Validity
                  </Typography>
                </Paper>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      )}

      {/* Recommendations */}
      {recommendations.length > 0 && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              AI Recommendations
            </Typography>
            
            <List>
              {recommendations.map((rec, index) => (
                <ListItem key={index}>
                  <ListItemIcon>
                    {getRecommendationIcon(rec.type)}
                  </ListItemIcon>
                  <ListItemText
                    primary={rec.message}
                    secondary={`Action: ${rec.action}`}
                  />
                </ListItem>
              ))}
            </List>
          </CardContent>
        </Card>
      )}

      {/* Extracted Data */}
      {results && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Extracted Information
            </Typography>
            
            <Accordion>
              <AccordionSummary expandIcon={<ExpandMore />}>
                <Typography>Document Data</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Grid container spacing={2}>
                  {Object.entries(results.extracted_data || {}).map(([key, value]) => (
                    <Grid item xs={12} md={6} key={key}>
                      <Paper sx={{ p: 2, bgcolor: 'grey.50' }}>
                        <Typography variant="subtitle2" color="primary">
                          {key.replace(/_/g, ' ').toUpperCase()}
                        </Typography>
                        <Typography variant="body1">
                          {value || 'Not found'}
                        </Typography>
                      </Paper>
                    </Grid>
                  ))}
                </Grid>
              </AccordionDetails>
            </Accordion>
            
            <Accordion>
              <AccordionSummary expandIcon={<ExpandMore />}>
                <Typography>Raw Text</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Paper sx={{ p: 2, bgcolor: 'grey.50' }}>
                  <Typography variant="body2" component="pre" sx={{ whiteSpace: 'pre-wrap' }}>
                    {results.raw_text || 'No text extracted'}
                  </Typography>
                </Paper>
              </AccordionDetails>
            </Accordion>
          </CardContent>
        </Card>
      )}
    </Box>
  );
};

export default AIScanner;
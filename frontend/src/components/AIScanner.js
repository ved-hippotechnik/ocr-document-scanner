import React, { useState, useCallback, useEffect, useRef } from 'react';
import { API_URL } from '../config';
import { validateFile } from '../utils/validation';
import useFileValidation from '../hooks/useFileValidation';
import { fileToBase64 } from '../hooks/useDocumentScanning';
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
  FormControlLabel,
  InputLabel,
  Select,
  MenuItem,
  Switch
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
  Language,
  Visibility
} from '@mui/icons-material';
import { useDropzone } from 'react-dropzone';
import { toast } from 'react-toastify';
import { useProcessingGuard, useRequestDedup, useCircuitBreaker, withTimeout, generateErrorId } from '../utils/resilience';
import { trackApiCall, trackError } from '../utils/metrics';

const AIScanner = () => {
  const { validate: validateSingleFile } = useFileValidation();
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingStage, setProcessingStage] = useState('');
  const [progress, setProgress] = useState(0);
  const [results, setResults] = useState(null);
  const [classification, setClassification] = useState(null);
  const [qualityAssessment, setQualityAssessment] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [selectedLanguage, setSelectedLanguage] = useState('auto');
  const [availableLanguages, setAvailableLanguages] = useState([]);
  const [visionEnabled, setVisionEnabled] = useState(false);
  const [visionAvailable, setVisionAvailable] = useState(false);
  const wsCleanupRef = useRef(null);

  const { guard, isProcessing: guardProcessing } = useProcessingGuard();
  const dedup = useRequestDedup();
  const circuitBreaker = useCircuitBreaker({ failureThreshold: 5, resetTimeoutMs: 30000 });

  useEffect(() => {
    const controller = new AbortController();
    const { signal } = controller;

    // Fetch available languages
    fetch(`${API_URL}/api/v3/languages`, { signal })
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          setAvailableLanguages(data.languages);
        }
      })
      .catch((error) => {
        if (error.name !== 'AbortError') {
          setAvailableLanguages([{ code: 'eng', name: 'English' }]);
        }
      });

    // Check if Vision service is available
    fetch(`${API_URL}/api/ai/model/status`, { signal })
      .then(res => res.json())
      .then(data => {
        if (data.success && data.vision_available) {
          setVisionAvailable(true);
        }
      })
      .catch(() => {});

    return () => controller.abort();
  }, []);

  const onDrop = useCallback((acceptedFiles) => {
    if (acceptedFiles.length > 0) {
      const file = acceptedFiles[0];
      if (!validateSingleFile(file).isValid) return;
      processDocument(file);
    }
  }, [validateSingleFile]);

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

  const processDocument = guard(async (file) => {
    setIsProcessing(true);
    setProgress(0);
    setResults(null);
    setClassification(null);
    setQualityAssessment(null);
    setRecommendations([]);

    const dedupKey = `${file.name}-${file.size}`;

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
      if (visionEnabled) {
        formData.append('validate_with_vision', 'true');
      }

      const apiCallStart = Date.now();

      // Deduplicate by file identity, wrap in circuit breaker and hard timeout
      const data = await dedup(dedupKey, () =>
        circuitBreaker.call(() =>
          withTimeout(
            fetch(`${API_URL}/api/v3/scan`, {
              method: 'POST',
              headers: {
                'X-Session-ID': sessionId
              },
              body: formData
            }).then(async (response) => {
              if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
              }
              return response.json();
            }),
            120000,
            30000,
            () => toast.warning('Still processing, please wait...')
          )
        )
      );

      trackApiCall('/api/v3/scan', Date.now() - apiCallStart, true, {
        documentName: file.name,
        fileSize: file.size
      });

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
      const errorId = generateErrorId();
      trackError(errorId, 'AIScanner', error.message, { action: 'scan', fileName: file.name });

      if (error.message && error.message.startsWith('Request timed out')) {
        toast.error(`Document processing timed out. Please try again with a smaller file. (Ref: ${errorId})`);
      } else if (error.message && error.message.startsWith('Circuit breaker is open')) {
        toast.error(`API appears unreachable. Please try again later. (Ref: ${errorId})`);
      } else {
        toast.error(`Processing failed: ${error.message} (Ref: ${errorId})`);
      }
    } finally {
      setIsProcessing(false);
      setProgress(100);
    }
  });

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

      {/* Circuit Breaker Banner */}
      {circuitBreaker.state !== 'closed' && (
        <Alert severity="error" sx={{ mb: 2 }}>
          API appears unreachable. Uploads are temporarily disabled.
          {circuitBreaker.state === 'half_open' && ' Retrying...'}
        </Alert>
      )}

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
              cursor: (guardProcessing || circuitBreaker.state === 'open') ? 'not-allowed' : 'pointer',
              bgcolor: isDragActive ? 'primary.50' : 'transparent',
              transition: 'all 0.2s ease',
              opacity: (guardProcessing || circuitBreaker.state === 'open') ? 0.5 : 1,
              pointerEvents: (guardProcessing || circuitBreaker.state === 'open') ? 'none' : 'auto'
            }}
          >
            <input {...getInputProps()} disabled={guardProcessing || circuitBreaker.state === 'open'} />
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

          {/* Vision Enhancement Toggle */}
          {visionAvailable && (
            <Box sx={{ mt: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
              <Visibility color="action" />
              <FormControlLabel
                control={
                  <Switch
                    checked={visionEnabled}
                    onChange={(e) => setVisionEnabled(e.target.checked)}
                    color="secondary"
                  />
                }
                label="Enhance with AI Vision"
              />
              <Tooltip title="Uses Claude Vision AI to validate and correct OCR-extracted fields. Improves accuracy but may take a few extra seconds.">
                <Info fontSize="small" color="action" sx={{ cursor: 'help' }} />
              </Tooltip>
            </Box>
          )}
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
              {classification.classifier === 'vision' && (
                <Chip label="AI Vision" size="small" color="secondary" icon={<Visibility />} />
              )}
              {classification.classifier === 'ml' && (
                <Chip label="ML Model" size="small" color="info" />
              )}
              {classification.classifier === 'rule_based' && (
                <Chip label="Rule-based" size="small" color="default" />
              )}
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

            {/* Vision reasoning */}
            {classification.reasoning && (
              <Accordion sx={{ mt: 2 }}>
                <AccordionSummary expandIcon={<ExpandMore />}>
                  <Typography variant="body2">
                    <Visibility fontSize="small" sx={{ verticalAlign: 'middle', mr: 0.5 }} />
                    Vision Reasoning
                  </Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Typography variant="body2" color="text.secondary">
                    {classification.reasoning}
                  </Typography>
                </AccordionDetails>
              </Accordion>
            )}
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
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              Extracted Information
              {results.extracted_data?.vision_validated && (
                <Chip label="Vision Verified" size="small" color="secondary" icon={<Visibility />} />
              )}
              {results.extracted_data?.vision_assisted && (
                <Chip label="Vision Assisted" size="small" color="info" icon={<Visibility />} />
              )}
            </Typography>

            {/* Vision Corrections */}
            {results.extracted_data?.vision_corrections?.length > 0 && (
              <Alert severity="info" sx={{ mb: 2 }}>
                <Typography variant="subtitle2" gutterBottom>
                  AI Vision corrected {results.extracted_data.vision_corrections.length} field(s):
                </Typography>
                {results.extracted_data.vision_corrections.map((c, i) => (
                  <Typography key={i} variant="body2">
                    <strong>{c.field}</strong>: {c.original} → {c.corrected} ({c.reason})
                  </Typography>
                ))}
              </Alert>
            )}

            <Accordion>
              <AccordionSummary expandIcon={<ExpandMore />}>
                <Typography>Document Data</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Grid container spacing={2}>
                  {Object.entries(results.extracted_data || {}).filter(([key]) =>
                    !['vision_validated', 'vision_corrections', 'vision_confidence',
                      'vision_missing_fields', 'vision_assisted', 'vision_notes',
                      'processing_method', 'country_code', 'processor'].includes(key)
                  ).map(([key, value]) => (
                    <Grid item xs={12} md={6} key={key}>
                      <Paper sx={{ p: 2, bgcolor: 'grey.50' }}>
                        <Typography variant="subtitle2" color="primary">
                          {key.replace(/_/g, ' ').toUpperCase()}
                        </Typography>
                        <Typography variant="body1">
                          {typeof value === 'object' ? JSON.stringify(value) : (value || 'Not found')}
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
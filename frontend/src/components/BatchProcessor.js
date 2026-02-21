import React, { useState, useCallback } from 'react';
import { API_URL } from '../config';
import { validateFiles, formatFileSize as formatFileSizeUtil, showValidationError, clearValidationError } from '../utils/validation';
import {
  Box,
  Button,
  Card,
  CardContent,
  Typography,
  LinearProgress,
  Chip,
  Grid,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Collapse,
  Alert
} from '@mui/material';
import {
  CloudUpload,
  Delete,
  Preview,
  Download,
  CheckCircle,
  Error,
  Warning,
  ExpandMore,
  ExpandLess,
  Folder,
  InsertDriveFile,
  Analytics
} from '@mui/icons-material';
import { useDropzone } from 'react-dropzone';
import { toast } from 'react-toastify';

const BatchProcessor = () => {
  const [files, setFiles] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processedResults, setProcessedResults] = useState([]);
  const [progress, setProgress] = useState(0);
  const [currentFile, setCurrentFile] = useState('');
  const [showResults, setShowResults] = useState(false);
  const [selectedResult, setSelectedResult] = useState(null);
  const [expandedRows, setExpandedRows] = useState({});

  const onDrop = useCallback((acceptedFiles) => {
    const validation = validateFiles(acceptedFiles, 50);
    
    if (!validation.isValid) {
      toast.error(validation.error);
      return;
    }
    
    if (validation.validFiles.length < acceptedFiles.length) {
      toast.warning(validation.error); // Shows which files were skipped
    }
    
    const newFiles = validation.validFiles.map(file => ({
      id: `${Date.now()}-${Math.random()}`,
      file,
      name: file.name,
      size: file.size,
      status: 'pending',
      result: null,
      error: null
    }));
    
    setFiles(prev => [...prev, ...newFiles]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.gif', '.webp'],
      'application/pdf': ['.pdf']
    },
    maxSize: 50 * 1024 * 1024, // 50MB - consistent with validation utility
    multiple: true,
    noClick: false,
    noKeyboard: false
  });

  const removeFile = (fileId) => {
    setFiles(prev => prev.filter(f => f.id !== fileId));
  };

  const clearAll = () => {
    setFiles([]);
    setProcessedResults([]);
    setProgress(0);
    setShowResults(false);
  };

  const processBatch = async () => {
    if (files.length === 0) {
      toast.warning('Please add files to process');
      return;
    }

    setIsProcessing(true);
    setProgress(0);
    setProcessedResults([]);

    try {
      // Convert files to base64
      const imagePromises = files.map(async (fileItem) => {
        const base64 = await fileToBase64(fileItem.file);
        return {
          id: fileItem.id,
          image: base64
        };
      });

      const images = await Promise.all(imagePromises);

      // Process batch
      const response = await fetch(`${API_URL}/api/v3/batch-scan`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Session-ID': `batch_${Date.now()}`
        },
        body: JSON.stringify({ images })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      if (data.success) {
        setProcessedResults(data.results);
        setShowResults(true);
        
        // Update file statuses
        const updatedFiles = files.map(fileItem => {
          const result = data.results.find(r => r.id === fileItem.id);
          return {
            ...fileItem,
            status: result?.success ? 'completed' : 'failed',
            result: result,
            error: result?.error
          };
        });
        setFiles(updatedFiles);
        
        toast.success(`Batch processing completed! ${data.successful_extractions}/${data.total_processed} successful`);
      } else {
        throw new Error(data.error || 'Batch processing failed');
      }
      
    } catch (error) {
      console.error('Batch processing error:', error);
      toast.error(`Batch processing failed: ${error.message}`);
    } finally {
      setIsProcessing(false);
      setProgress(100);
    }
  };

  const fileToBase64 = (file) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => resolve(reader.result);
      reader.onerror = error => reject(error);
    });
  };

  const formatFileSize = formatFileSizeUtil; // Use unified utility

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed': return <CheckCircle color="success" />;
      case 'failed': return <Error color="error" />;
      case 'processing': return <LinearProgress />;
      default: return <InsertDriveFile color="action" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'success';
      case 'failed': return 'error';
      case 'processing': return 'warning';
      default: return 'default';
    }
  };

  const toggleRowExpansion = (id) => {
    setExpandedRows(prev => ({
      ...prev,
      [id]: !prev[id]
    }));
  };

  const exportResults = () => {
    const exportData = processedResults.map(result => ({
      filename: files.find(f => f.id === result.id)?.name,
      document_type: result.classification?.document_type,
      confidence: result.classification?.confidence,
      quality_score: result.quality_score,
      extracted_data: result.ocr_result?.extracted_data,
      success: result.success
    }));

    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `batch_results_${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const getOverallStats = () => {
    const total = processedResults.length;
    const successful = processedResults.filter(r => r.success).length;
    const failed = total - successful;
    const avgQuality = processedResults.reduce((sum, r) => sum + (r.quality_score || 0), 0) / total;
    const avgConfidence = processedResults.reduce((sum, r) => sum + (r.classification?.confidence || 0), 0) / total;

    return { total, successful, failed, avgQuality, avgConfidence };
  };

  return (
    <Box sx={{ maxWidth: 1200, mx: 'auto', p: 3 }}>
      <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <Folder color="primary" />
        Batch Document Processor
      </Typography>

      <Typography variant="body1" color="text.secondary" gutterBottom>
        Upload multiple documents for batch processing with AI classification
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
              {isDragActive ? 'Drop the documents here' : 'Drag & drop documents or click to browse'}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Select multiple files (JPG, PNG, TIFF, BMP, GIF, WebP, PDF - max 50MB each)
            </Typography>
          </Box>
        </CardContent>
      </Card>

      {/* File List */}
      {files.length > 0 && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">
                Files to Process ({files.length})
              </Typography>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <Button
                  variant="outlined"
                  onClick={clearAll}
                  disabled={isProcessing}
                  startIcon={<Delete />}
                >
                  Clear All
                </Button>
                <Button
                  variant="contained"
                  onClick={processBatch}
                  disabled={isProcessing}
                  startIcon={<Analytics />}
                >
                  Process Batch
                </Button>
              </Box>
            </Box>

            <List>
              {files.map((fileItem) => (
                <ListItem
                  key={fileItem.id}
                  sx={{
                    border: '1px solid',
                    borderColor: 'grey.200',
                    borderRadius: 1,
                    mb: 1
                  }}
                >
                  <ListItemIcon>
                    {getStatusIcon(fileItem.status)}
                  </ListItemIcon>
                  <ListItemText
                    primary={fileItem.name}
                    secondary={`${formatFileSize(fileItem.size)} • ${fileItem.status}`}
                  />
                  <Chip
                    label={fileItem.status}
                    color={getStatusColor(fileItem.status)}
                    size="small"
                    sx={{ mr: 1 }}
                  />
                  <IconButton
                    onClick={() => removeFile(fileItem.id)}
                    disabled={isProcessing}
                    color="error"
                    aria-label={`Remove ${fileItem.name} from batch`}
                  >
                    <Delete />
                  </IconButton>
                </ListItem>
              ))}
            </List>
          </CardContent>
        </Card>
      )}

      {/* Processing Progress */}
      {isProcessing && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Processing Batch...
            </Typography>
            <LinearProgress 
              variant="determinate" 
              value={progress} 
              sx={{ mb: 2, height: 8, borderRadius: 4 }}
            />
            <Typography variant="body2" color="text.secondary">
              {currentFile || 'Processing documents...'}
            </Typography>
          </CardContent>
        </Card>
      )}

      {/* Results Summary */}
      {showResults && processedResults.length > 0 && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">
                Processing Results
              </Typography>
              <Button
                variant="outlined"
                onClick={exportResults}
                startIcon={<Download />}
              >
                Export Results
              </Button>
            </Box>

            {/* Summary Stats */}
            <Grid container spacing={2} sx={{ mb: 3 }}>
              <Grid item xs={12} md={3}>
                <Paper sx={{ p: 2, textAlign: 'center' }}>
                  <Typography variant="h4" color="primary">
                    {getOverallStats().total}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Total Documents
                  </Typography>
                </Paper>
              </Grid>
              <Grid item xs={12} md={3}>
                <Paper sx={{ p: 2, textAlign: 'center' }}>
                  <Typography variant="h4" color="success.main">
                    {getOverallStats().successful}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Successful
                  </Typography>
                </Paper>
              </Grid>
              <Grid item xs={12} md={3}>
                <Paper sx={{ p: 2, textAlign: 'center' }}>
                  <Typography variant="h4" color="error.main">
                    {getOverallStats().failed}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Failed
                  </Typography>
                </Paper>
              </Grid>
              <Grid item xs={12} md={3}>
                <Paper sx={{ p: 2, textAlign: 'center' }}>
                  <Typography variant="h4" color="warning.main">
                    {(getOverallStats().avgQuality * 100).toFixed(1)}%
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Avg Quality
                  </Typography>
                </Paper>
              </Grid>
            </Grid>

            {/* Detailed Results Table */}
            <TableContainer component={Paper}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Document</TableCell>
                    <TableCell>Type</TableCell>
                    <TableCell>Confidence</TableCell>
                    <TableCell>Quality</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {processedResults.map((result) => {
                    const fileName = files.find(f => f.id === result.id)?.name || 'Unknown';
                    return (
                      <React.Fragment key={result.id}>
                        <TableRow>
                          <TableCell>{fileName}</TableCell>
                          <TableCell>
                            {result.classification?.document_name || 'Unknown'}
                          </TableCell>
                          <TableCell>
                            <Chip
                              label={`${((result.classification?.confidence || 0) * 100).toFixed(1)}%`}
                              color={result.classification?.confidence > 0.7 ? 'success' : 'warning'}
                              size="small"
                            />
                          </TableCell>
                          <TableCell>
                            <Chip
                              label={`${((result.quality_score || 0) * 100).toFixed(1)}%`}
                              color={result.quality_score > 0.7 ? 'success' : 'warning'}
                              size="small"
                            />
                          </TableCell>
                          <TableCell>
                            {result.success ? (
                              <CheckCircle color="success" />
                            ) : (
                              <Error color="error" />
                            )}
                          </TableCell>
                          <TableCell>
                            <IconButton
                              onClick={() => toggleRowExpansion(result.id)}
                              size="small"
                              aria-label={expandedRows[result.id] ? 'Collapse details' : 'Expand details'}
                            >
                              {expandedRows[result.id] ? <ExpandLess /> : <ExpandMore />}
                            </IconButton>
                          </TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell style={{ paddingBottom: 0, paddingTop: 0 }} colSpan={6}>
                            <Collapse in={expandedRows[result.id]} timeout="auto" unmountOnExit>
                              <Box sx={{ margin: 1 }}>
                                <Typography variant="h6" gutterBottom component="div">
                                  Extracted Data
                                </Typography>
                                <Grid container spacing={2}>
                                  {Object.entries(result.ocr_result?.extracted_data || {}).map(([key, value]) => (
                                    <Grid item xs={6} md={4} key={key}>
                                      <Paper sx={{ p: 1, bgcolor: 'grey.50' }}>
                                        <Typography variant="caption" color="primary">
                                          {key.replace(/_/g, ' ').toUpperCase()}
                                        </Typography>
                                        <Typography variant="body2">
                                          {value || 'Not found'}
                                        </Typography>
                                      </Paper>
                                    </Grid>
                                  ))}
                                </Grid>
                              </Box>
                            </Collapse>
                          </TableCell>
                        </TableRow>
                      </React.Fragment>
                    );
                  })}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      )}
    </Box>
  );
};

export default BatchProcessor;
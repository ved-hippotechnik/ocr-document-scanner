import React, { useState, useRef } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  Typography,
  CircularProgress,
  Alert,
  Paper,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  CloudUpload,
  Clear,
  CheckCircle,
  Error as ErrorIcon,
  Info,
} from '@mui/icons-material';
import { useDropzone } from 'react-dropzone';
import config from '../config';

const AccessibleScanner = () => {
  const [file, setFile] = useState(null);
  const [processing, setProcessing] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const fileInputRef = useRef(null);

  const onDrop = (acceptedFiles) => {
    if (acceptedFiles.length > 0) {
      const selectedFile = acceptedFiles[0];
      
      // Validate file size
      if (selectedFile.size > config.upload.maxSize) {
        setError(`File size exceeds ${config.upload.maxSize / (1024 * 1024)}MB limit`);
        return;
      }
      
      setFile(selectedFile);
      setError(null);
      setResult(null);
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': config.upload.allowedExtensions,
    },
    maxFiles: 1,
  });

  const handleScan = async () => {
    if (!file) {
      setError('Please select a file first');
      return;
    }

    setProcessing(true);
    setError(null);

    const formData = new FormData();
    formData.append('image', file);

    try {
      const response = await fetch(config.endpoints.scanV3, {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || 'Scan failed');
      }

      setResult(data);
    } catch (err) {
      setError(err.message || 'An error occurred during scanning');
    } finally {
      setProcessing(false);
    }
  };

  const handleClear = () => {
    setFile(null);
    setResult(null);
    setError(null);
  };

  return (
    <Box sx={{ maxWidth: 800, mx: 'auto', p: 3 }}>
      <Card>
        <CardContent>
          <Typography
            variant="h4"
            component="h1"
            gutterBottom
            id="scanner-title"
            tabIndex={0}
          >
            Document Scanner
          </Typography>

          {/* File Upload Area */}
          <Paper
            {...getRootProps()}
            sx={{
              p: 4,
              mb: 3,
              border: '2px dashed',
              borderColor: isDragActive ? 'primary.main' : 'grey.300',
              backgroundColor: isDragActive ? 'action.hover' : 'background.default',
              cursor: 'pointer',
              transition: 'all 0.3s',
              '&:hover': {
                borderColor: 'primary.main',
                backgroundColor: 'action.hover',
              },
            }}
            role="button"
            tabIndex={0}
            aria-label="Drop zone for file upload. Click or drag files here"
            aria-describedby="upload-instructions"
          >
            <input {...getInputProps()} aria-label="File input" />
            
            <Box sx={{ textAlign: 'center' }}>
              <CloudUpload
                sx={{ fontSize: 48, color: 'primary.main', mb: 2 }}
                aria-hidden="true"
              />
              
              <Typography
                variant="h6"
                id="upload-instructions"
                aria-live="polite"
              >
                {isDragActive
                  ? 'Drop the file here'
                  : 'Drag & drop a document, or click to select'}
              </Typography>
              
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                Supported formats: JPEG, PNG, PDF, TIFF
              </Typography>
              
              <Typography variant="caption" color="text.secondary">
                Maximum file size: {config.upload.maxSize / (1024 * 1024)}MB
              </Typography>
            </Box>
          </Paper>

          {/* Selected File Info */}
          {file && (
            <Alert
              severity="info"
              sx={{ mb: 2 }}
              action={
                <IconButton
                  aria-label="Clear selected file"
                  color="inherit"
                  size="small"
                  onClick={handleClear}
                >
                  <Clear />
                </IconButton>
              }
              role="status"
              aria-live="polite"
            >
              <Typography variant="body2">
                Selected: <strong>{file.name}</strong> ({(file.size / 1024).toFixed(2)} KB)
              </Typography>
            </Alert>
          )}

          {/* Error Message */}
          {error && (
            <Alert
              severity="error"
              sx={{ mb: 2 }}
              icon={<ErrorIcon />}
              role="alert"
              aria-live="assertive"
            >
              {error}
            </Alert>
          )}

          {/* Success Result */}
          {result && (
            <Alert
              severity="success"
              sx={{ mb: 2 }}
              icon={<CheckCircle />}
              role="status"
              aria-live="polite"
            >
              <Typography variant="body2">
                Document processed successfully!
              </Typography>
              {result.document_type && (
                <Typography variant="caption" display="block">
                  Type: {result.document_type}
                </Typography>
              )}
            </Alert>
          )}

          {/* Action Buttons */}
          <Box sx={{ display: 'flex', gap: 2, mt: 3 }}>
            <Tooltip title="Start scanning the selected document">
              <span>
                <Button
                  variant="contained"
                  color="primary"
                  onClick={handleScan}
                  disabled={!file || processing}
                  startIcon={processing ? <CircularProgress size={20} /> : <CheckCircle />}
                  fullWidth
                  aria-label="Scan document"
                  aria-busy={processing}
                  aria-disabled={!file || processing}
                >
                  {processing ? 'Processing...' : 'Scan Document'}
                </Button>
              </span>
            </Tooltip>

            <Tooltip title="Clear selection and results">
              <Button
                variant="outlined"
                color="secondary"
                onClick={handleClear}
                disabled={processing}
                startIcon={<Clear />}
                aria-label="Clear all"
                aria-disabled={processing}
              >
                Clear
              </Button>
            </Tooltip>
          </Box>

          {/* Results Display */}
          {result && result.data && (
            <Box sx={{ mt: 3 }}>
              <Typography
                variant="h6"
                component="h2"
                gutterBottom
                tabIndex={0}
              >
                Extracted Information
              </Typography>
              
              <Paper
                sx={{ p: 2, backgroundColor: 'grey.50' }}
                role="region"
                aria-label="Extracted document information"
                tabIndex={0}
              >
                <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
                  {JSON.stringify(result.data, null, 2)}
                </pre>
              </Paper>
            </Box>
          )}

          {/* Screen Reader Status */}
          <Box
            role="status"
            aria-live="polite"
            aria-atomic="true"
            className="sr-only"
            sx={{ position: 'absolute', left: '-9999px' }}
          >
            {processing && 'Processing document, please wait'}
            {result && 'Document processed successfully'}
            {error && `Error: ${error}`}
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
};

export default AccessibleScanner;
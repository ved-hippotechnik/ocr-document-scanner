import React from 'react';
import {
  Box,
  Typography,
  Button,
  Paper,
  Alert,
  Container
} from '@mui/material';
import { Error as ErrorIcon, Refresh as RefreshIcon } from '@mui/icons-material';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      retryCount: 0,
      maxRetries: 3
    };
  }

  static getDerivedStateFromError(error) {
    // Update state so the next render will show the fallback UI
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    // Log error details for debugging
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    
    this.setState({
      error,
      errorInfo,
      hasError: true
    });

    // Report error to logging service if available
    if (window.reportError) {
      window.reportError(error, errorInfo);
    }
  }

  handleRetry = () => {
    if (this.state.retryCount < this.state.maxRetries) {
      this.setState({
        hasError: false,
        error: null,
        errorInfo: null,
        retryCount: this.state.retryCount + 1
      });
    } else {
      // Reload the page if max retries exceeded
      window.location.reload();
    }
  };

  handleReload = () => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      const { retryCount, maxRetries, error } = this.state;
      const canRetry = retryCount < maxRetries;

      return (
        <Container maxWidth="md" sx={{ mt: 4 }}>
          <Paper
            elevation={3}
            sx={{
              p: 4,
              textAlign: 'center',
              borderRadius: 3,
              border: '1px solid',
              borderColor: 'error.light',
              background: 'linear-gradient(135deg, #fff5f5 0%, #fef2f2 100%)'
            }}
          >
            <Box sx={{ mb: 3 }}>
              <ErrorIcon
                sx={{
                  fontSize: 64,
                  color: 'error.main',
                  mb: 2
                }}
              />
              <Typography variant="h4" component="h1" gutterBottom sx={{ fontWeight: 600 }}>
                Oops! Something went wrong
              </Typography>
              <Typography variant="h6" color="text.secondary" sx={{ mb: 3 }}>
                {this.props.fallbackMessage || "We're sorry, but an unexpected error occurred."}
              </Typography>
            </Box>

            <Alert severity="error" sx={{ mb: 3, textAlign: 'left' }}>
              <Typography variant="body2" sx={{ fontWeight: 500, mb: 1 }}>
                Error Details:
              </Typography>
              <Typography variant="body2" component="pre" sx={{ 
                whiteSpace: 'pre-wrap',
                fontSize: '0.875rem',
                fontFamily: 'monospace',
                maxHeight: 200,
                overflow: 'auto'
              }}>
                {error?.message || 'Unknown error occurred'}
              </Typography>
              {retryCount > 0 && (
                <Typography variant="body2" sx={{ mt: 1, color: 'warning.main' }}>
                  Retry attempts: {retryCount}/{maxRetries}
                </Typography>
              )}
            </Alert>

            <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', flexWrap: 'wrap' }}>
              {canRetry && (
                <Button
                  variant="contained"
                  startIcon={<RefreshIcon />}
                  onClick={this.handleRetry}
                  sx={{
                    px: 3,
                    py: 1,
                    borderRadius: 2,
                    textTransform: 'none',
                    fontWeight: 500
                  }}
                >
                  Try Again
                </Button>
              )}
              
              <Button
                variant="outlined"
                onClick={this.handleReload}
                sx={{
                  px: 3,
                  py: 1,
                  borderRadius: 2,
                  textTransform: 'none',
                  fontWeight: 500
                }}
              >
                Reload Page
              </Button>

              {this.props.onGoHome && (
                <Button
                  variant="text"
                  onClick={this.props.onGoHome}
                  sx={{
                    px: 3,
                    py: 1,
                    textTransform: 'none',
                    fontWeight: 500
                  }}
                >
                  Go Home
                </Button>
              )}
            </Box>

            {process.env.NODE_ENV === 'development' && this.state.errorInfo && (
              <Box sx={{ mt: 3, p: 2, bgcolor: 'grey.100', borderRadius: 2 }}>
                <Typography variant="body2" sx={{ fontWeight: 500, mb: 1 }}>
                  Component Stack (Development Only):
                </Typography>
                <Typography
                  variant="body2"
                  component="pre"
                  sx={{
                    fontSize: '0.75rem',
                    fontFamily: 'monospace',
                    maxHeight: 150,
                    overflow: 'auto',
                    textAlign: 'left',
                    whiteSpace: 'pre-wrap'
                  }}
                >
                  {this.state.errorInfo.componentStack}
                </Typography>
              </Box>
            )}
          </Paper>
        </Container>
      );
    }

    return this.props.children;
  }
}

// Higher-order component for easier usage
export const withErrorBoundary = (Component, errorBoundaryProps = {}) => {
  const WrappedComponent = (props) => (
    <ErrorBoundary {...errorBoundaryProps}>
      <Component {...props} />
    </ErrorBoundary>
  );
  
  WrappedComponent.displayName = `withErrorBoundary(${Component.displayName || Component.name})`;
  return WrappedComponent;
};

// Hook for handling errors in functional components
export const useErrorHandler = () => {
  const [error, setError] = React.useState(null);

  const resetError = () => setError(null);

  const handleError = React.useCallback((error, errorInfo) => {
    console.error('Error caught by useErrorHandler:', error, errorInfo);
    setError(error);
  }, []);

  // Throw error to be caught by error boundary
  if (error) {
    throw error;
  }

  return { handleError, resetError };
};

export default ErrorBoundary;
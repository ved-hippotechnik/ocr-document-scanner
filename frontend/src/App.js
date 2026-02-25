import React, { useEffect, Suspense } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import CircularProgress from '@mui/material/CircularProgress';
import Box from '@mui/material/Box';
import Snackbar from '@mui/material/Snackbar';
import Alert from '@mui/material/Alert';
import ErrorBoundary from './components/ErrorBoundary';
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';
import PWAInstallPrompt from './components/PWAInstallPrompt';
import OfflineStatus from './components/OfflineStatus';
import UpdatePrompt from './components/UpdatePrompt';
import { registerServiceWorker, requestNotificationPermission } from './utils/pwaUtils';
import { initMetrics } from './utils/metrics';
import './App.css';

// Lazy-load heavy route components
const Scanner = React.lazy(() => import('./pages/Scanner'));
const AIScanner = React.lazy(() => import('./components/AIScanner'));
const BatchProcessor = React.lazy(() => import('./components/BatchProcessor'));
const AIDashboard = React.lazy(() => import('./components/AIDashboard'));
const AdminDashboard = React.lazy(() => import('./components/AdminDashboard'));
const DeveloperPortal = React.lazy(() => import('./pages/developer/DeveloperPortal'));
const DevDashboard = React.lazy(() => import('./pages/developer/DevDashboard'));
const ApiKeysPage = React.lazy(() => import('./pages/developer/ApiKeys'));
const UsageDashboardPage = React.lazy(() => import('./pages/developer/UsageDashboard'));
const WebhooksPage = React.lazy(() => import('./pages/developer/Webhooks'));
const DocumentationPage = React.lazy(() => import('./pages/developer/Documentation'));
const LoginForm = React.lazy(() => import('./components/Auth/LoginForm'));
const RegisterForm = React.lazy(() => import('./components/Auth/RegisterForm'));

function RouteLoader() {
  return (
    <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '60vh' }}>
      <CircularProgress />
    </Box>
  );
}

// Apple-inspired theme with responsive breakpoints
const theme = createTheme({
  breakpoints: {
    values: {
      xs: 0,
      sm: 600,
      md: 900,
      lg: 1200,
      xl: 1536,
    },
  },
  palette: {
    primary: {
      main: '#007AFF', // Apple blue
      light: '#42a5f5',
      dark: '#0056b3',
      contrastText: '#ffffff',
    },
    secondary: {
      main: '#34C759', // Apple green
      light: '#4cd964',
      dark: '#248a3d',
      contrastText: '#ffffff',
    },
    error: {
      main: '#FF3B30', // Apple red
    },
    warning: {
      main: '#FF9500', // Apple orange
    },
    info: {
      main: '#5AC8FA', // Apple light blue
    },
    success: {
      main: '#34C759', // Apple green
    },
    background: {
      default: '#F2F2F7', // Apple light gray background
      paper: '#FFFFFF',
    },
    text: {
      primary: '#000000',
      secondary: '#6C6C70', // Apple secondary text (WCAG AA compliant)
    },
    divider: 'rgba(0, 0, 0, 0.12)',
  },
  typography: {
    fontFamily: '"-apple-system", "BlinkMacSystemFont", "San Francisco", "Helvetica Neue", "Helvetica", "Arial", sans-serif',
    h1: {
      fontWeight: 700,
    },
    h2: {
      fontWeight: 700,
    },
    h3: {
      fontWeight: 600,
    },
    h4: {
      fontWeight: 600,
    },
    h5: {
      fontWeight: 500,
    },
    h6: {
      fontWeight: 500,
    },
    button: {
      textTransform: 'none', // Apple doesn't use uppercase buttons
      fontWeight: 500,
    },
  },
  shape: {
    borderRadius: 10, // Apple uses rounded corners
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          padding: '8px 16px',
          boxShadow: 'none',
          '&:hover': {
            boxShadow: 'none',
          },
        },
        contained: {
          boxShadow: 'none',
          '&:hover': {
            boxShadow: 'none',
          },
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          boxShadow: '0px 2px 8px rgba(0, 0, 0, 0.05)',
          borderRadius: 12,
        },
        elevation1: {
          boxShadow: '0px 2px 8px rgba(0, 0, 0, 0.05)',
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          boxShadow: '0px 2px 8px rgba(0, 0, 0, 0.05)',
          overflow: 'hidden',
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          boxShadow: '0px 1px 0px rgba(0, 0, 0, 0.1)',
          backgroundColor: 'rgba(255, 255, 255, 0.8)',
          backdropFilter: 'blur(10px)',
          color: '#000000',
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        root: {
          borderBottom: '1px solid rgba(0, 0, 0, 0.05)',
        },
        head: {
          fontWeight: 600,
          color: '#000000',
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          fontWeight: 500,
        },
      },
    },
    MuiDialog: {
      styleOverrides: {
        paper: {
          borderRadius: 12,
          boxShadow: '0px 8px 25px rgba(0, 0, 0, 0.15)',
        },
      },
    },
  },
});

function App() {
  const [globalAlert, setGlobalAlert] = React.useState(null);

  useEffect(() => {
    // Initialize client-side metrics collection (Q7)
    initMetrics();

    // Listen for session-expiring events from AuthContext (Q4)
    const handleSessionExpiring = () => {
      setGlobalAlert({ severity: 'warning', message: 'Your session is expiring soon. Please save your work.' });
    };

    // Listen for WebSocket failure events (Q1)
    const handleWsFailed = () => {
      setGlobalAlert({ severity: 'error', message: 'Real-time connection lost. Some features may be delayed.' });
    };

    window.addEventListener('session-expiring', handleSessionExpiring);
    window.addEventListener('websocket-failed', handleWsFailed);

    // Initialize PWA features
    const initializePWA = async () => {
      try {
        await registerServiceWorker();
        setTimeout(async () => {
          await requestNotificationPermission();
        }, 5000);
      } catch (error) {
        console.error('PWA initialization failed:', error);
      }
    };

    initializePWA();

    return () => {
      window.removeEventListener('session-expiring', handleSessionExpiring);
      window.removeEventListener('websocket-failed', handleWsFailed);
    };
  }, []);

  return (
    <ErrorBoundary fallbackMessage="The Document Scanner application encountered an error">
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Router>
          <div className="App">
            <ErrorBoundary fallbackMessage="Navigation system encountered an error">
              <Navbar />
            </ErrorBoundary>
            <div className="content">
              <Suspense fallback={<RouteLoader />}>
                <Routes>
                  <Route path="/" element={
                    <ErrorBoundary fallbackMessage="Dashboard failed to load">
                      <Dashboard />
                    </ErrorBoundary>
                  } />
                  <Route path="/scanner" element={
                    <ErrorBoundary fallbackMessage="Scanner failed to load">
                      <Scanner />
                    </ErrorBoundary>
                  } />
                  <Route path="/ai-scanner" element={
                    <ErrorBoundary fallbackMessage="AI Scanner failed to load">
                      <AIScanner />
                    </ErrorBoundary>
                  } />
                  <Route path="/batch-processor" element={
                    <ErrorBoundary fallbackMessage="Batch Processor failed to load">
                      <BatchProcessor />
                    </ErrorBoundary>
                  } />
                  <Route path="/ai-dashboard" element={
                    <ErrorBoundary fallbackMessage="AI Dashboard failed to load">
                      <AIDashboard />
                    </ErrorBoundary>
                  } />
                  <Route path="/admin" element={
                    <ErrorBoundary fallbackMessage="Admin Dashboard failed to load">
                      <AdminDashboard />
                    </ErrorBoundary>
                  } />
                  <Route path="/developer" element={
                    <ErrorBoundary fallbackMessage="Developer Portal failed to load">
                      <DeveloperPortal />
                    </ErrorBoundary>
                  }>
                    <Route index element={<DevDashboard />} />
                    <Route path="keys" element={<ApiKeysPage />} />
                    <Route path="usage" element={<UsageDashboardPage />} />
                    <Route path="webhooks" element={<WebhooksPage />} />
                    <Route path="docs" element={<DocumentationPage />} />
                  </Route>
                  <Route path="/auth/login" element={
                    <ErrorBoundary fallbackMessage="Login form failed to load">
                      <LoginForm />
                    </ErrorBoundary>
                  } />
                  <Route path="/auth/register" element={
                    <ErrorBoundary fallbackMessage="Registration form failed to load">
                      <RegisterForm />
                    </ErrorBoundary>
                  } />
                </Routes>
              </Suspense>
            </div>
            
            {/* PWA Components with Error Boundaries */}
            <ErrorBoundary fallbackMessage="PWA features encountered an error">
              <PWAInstallPrompt />
              <OfflineStatus />
              <UpdatePrompt />
            </ErrorBoundary>
          </div>
        </Router>

        {/* Global alerts for session expiry and WebSocket failures */}
        <Snackbar
          open={Boolean(globalAlert)}
          autoHideDuration={10000}
          onClose={() => setGlobalAlert(null)}
          anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
        >
          {globalAlert && (
            <Alert severity={globalAlert.severity} onClose={() => setGlobalAlert(null)} variant="filled">
              {globalAlert.message}
            </Alert>
          )}
        </Snackbar>
      </ThemeProvider>
    </ErrorBoundary>
  );
}

export default App;

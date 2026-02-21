import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import ErrorBoundary from './components/ErrorBoundary';
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';
import Scanner from './pages/Scanner';
import AIScanner from './components/AIScanner';
import BatchProcessor from './components/BatchProcessor';
import AIDashboard from './components/AIDashboard';
import PWAInstallPrompt from './components/PWAInstallPrompt';
import OfflineStatus from './components/OfflineStatus';
import UpdatePrompt from './components/UpdatePrompt';
import { registerServiceWorker, requestNotificationPermission } from './utils/pwaUtils';
import './App.css';

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
  useEffect(() => {
    // Initialize PWA features
    const initializePWA = async () => {
      try {
        // Enable service worker for PWA functionality
        await registerServiceWorker();
        console.log('PWA service worker enabled');
        
        // Request notification permission after a delay
        setTimeout(async () => {
          const hasPermission = await requestNotificationPermission();
          if (hasPermission) {
            console.log('Notification permission granted');
          }
        }, 5000);
      } catch (error) {
        console.error('PWA initialization failed:', error);
      }
    };

    initializePWA();
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
              </Routes>
            </div>
            
            {/* PWA Components with Error Boundaries */}
            <ErrorBoundary fallbackMessage="PWA features encountered an error">
              <PWAInstallPrompt />
              <OfflineStatus />
              <UpdatePrompt />
            </ErrorBoundary>
          </div>
        </Router>
      </ThemeProvider>
    </ErrorBoundary>
  );
}

export default App;

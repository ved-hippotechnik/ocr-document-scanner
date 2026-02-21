import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API_URL } from '../config';
import { 
  Box, 
  Button, 
  CircularProgress, 
  Container, 
  Grid, 
  Paper, 
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Alert,
  Divider,
  Chip,
  IconButton,
  Tooltip,
  Skeleton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  TextField,
  Tab,
  Tabs,
  Snackbar,
  Menu,
  MenuItem,
  useTheme,
  useMediaQuery,
  Stack,
  Card,
  CardContent
} from '@mui/material';
import { useScreenSize, getResponsiveTableConfig, getResponsiveSpacing } from '../utils/responsive';
import RefreshIcon from '@mui/icons-material/Refresh';
import DeleteIcon from '@mui/icons-material/Delete';
import DescriptionIcon from '@mui/icons-material/Description';
import PublicIcon from '@mui/icons-material/Public';
import BadgeIcon from '@mui/icons-material/Badge';
import PassportIcon from '@mui/icons-material/ArticleOutlined';
import CreditCardIcon from '@mui/icons-material/CreditCard';
import DownloadIcon from '@mui/icons-material/Download';
import VisibilityIcon from '@mui/icons-material/Visibility';
import CloseIcon from '@mui/icons-material/Close';
import CalendarTodayIcon from '@mui/icons-material/CalendarToday';
import FingerprintIcon from '@mui/icons-material/Fingerprint';
import PersonIcon from '@mui/icons-material/Person';
import EditIcon from '@mui/icons-material/Edit';
import PrintIcon from '@mui/icons-material/Print';
import MoreVertIcon from '@mui/icons-material/MoreVert';
import FileDownloadIcon from '@mui/icons-material/FileDownload';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import LocationOnIcon from '@mui/icons-material/LocationOn';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title as ChartTitle,
  Tooltip as ChartTooltip,
  Legend,
  ArcElement
} from 'chart.js';
import { Bar, Pie } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  ChartTitle,
  ChartTooltip,
  Legend,
  ArcElement
);

// Main Dashboard component
const Dashboard = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedScan, setSelectedScan] = useState(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editMode, setEditMode] = useState(false);
  const [editedScan, setEditedScan] = useState(null);
  const [tabValue, setTabValue] = useState(0);
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [menuAnchorEl, setMenuAnchorEl] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [documentsLoading, setDocumentsLoading] = useState(false);
  const menuOpen = Boolean(menuAnchorEl);
  
  // Responsive design hooks
  const theme = useTheme();
  const screenSize = useScreenSize();
  const tableConfig = getResponsiveTableConfig(screenSize);
  const spacing = getResponsiveSpacing(screenSize);
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const isTablet = useMediaQuery(theme.breakpoints.between('sm', 'md'));

  const fetchDocuments = async () => {
    setDocumentsLoading(true);
    try {
      const response = await axios.get(`${API_URL}/api/v2/documents`);
      // Ensure we're setting the documents array from the response
      setDocuments(response.data.documents || []);
      setError(null);
    } catch (err) {
      setError('Error fetching documents: ' + err.message);
    } finally {
      setDocumentsLoading(false);
    }
  };

  const fetchStats = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_URL}/api/stats`);
      setStats(response.data);
      setError(null);
    } catch (err) {
      setError('Error fetching statistics: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const resetStats = async () => {
    setLoading(true);
    try {
      await axios.post(`${API_URL}/api/v2/reset-stats`);
      fetchStats();
    } catch (err) {
      setError('Error resetting statistics: ' + err.message);
    }
  };

  const handleOpenScanDetails = (scan) => {
    setSelectedScan(scan);
    setDialogOpen(true);
    // Reset edit mode when opening dialog
    setEditMode(false);
    setEditedScan(null);
    setTabValue(0);
  };

  const handleCloseScanDetails = () => {
    setDialogOpen(false);
    // Keep the selected scan data for a smooth closing animation
    setTimeout(() => {
      setSelectedScan(null);
      setEditedScan(null);
      setEditMode(false);
    }, 300);
  };
  
  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };
  
  const handleEditClick = () => {
    setEditMode(true);
    // Create a deep copy of the selected scan for editing
    setEditedScan(JSON.parse(JSON.stringify(selectedScan)));
  };
  
  const handleCancelEdit = () => {
    setEditMode(false);
    setEditedScan(null);
  };
  
  const handleSaveEdit = async () => {
    try {
      // In a real application, you would send the edited data to the backend
      // For now, we'll update it locally in the stats object
      const updatedHistory = stats.scan_history.map(scan => {
        if (new Date(scan.timestamp).getTime() === new Date(selectedScan.timestamp).getTime()) {
          return editedScan;
        }
        return scan;
      });
      
      const updatedStats = {
        ...stats,
        scan_history: updatedHistory
      };
      
      setStats(updatedStats);
      setSelectedScan(editedScan);
      setEditMode(false);
      setEditedScan(null);
      
      setSnackbarMessage('Scan details updated successfully');
      setSnackbarOpen(true);
    } catch (error) {
      setSnackbarMessage('Error updating scan details: ' + error.message);
      setSnackbarOpen(true);
    }
  };
  
  const handleEditFieldChange = (field, value) => {
    setEditedScan(prev => {
      if (field.includes('.')) {
        // Handle nested fields like 'extracted_info.full_name'
        const [parent, child] = field.split('.');
        return {
          ...prev,
          [parent]: {
            ...prev[parent],
            [child]: value
          }
        };
      }
      return {
        ...prev,
        [field]: value
      };
    });
  };
  
  const handlePrintScan = () => {
    const printWindow = window.open('', '_blank');
    
    if (!printWindow) {
      setSnackbarMessage('Pop-up blocked. Please allow pop-ups for printing.');
      setSnackbarOpen(true);
      return;
    }
    
    const scanData = selectedScan;
    
    printWindow.document.write(`
      <!DOCTYPE html>
      <html>
        <head>
          <title>Scan Details - ${scanData.document_type}</title>
          <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .header { text-align: center; margin-bottom: 20px; }
            .section { margin-bottom: 20px; }
            .section-title { font-weight: bold; border-bottom: 1px solid #ccc; padding-bottom: 5px; margin-bottom: 10px; }
            .field { margin-bottom: 10px; }
            .field-name { font-weight: bold; }
            .field-value { margin-left: 10px; }
            .footer { margin-top: 30px; text-align: center; font-size: 0.8em; color: #666; }
          </style>
        </head>
        <body>
          <div class="header">
            <h1>Document Scan Details</h1>
            <p>Scanned on: ${new Date(scanData.timestamp).toLocaleString()}</p>
          </div>
          
          <div class="section">
            <h2 class="section-title">Document Information</h2>
            <div class="field">
              <span class="field-name">Document Type:</span>
              <span class="field-value">${scanData.document_type?.charAt(0).toUpperCase() + scanData.document_type?.slice(1).replace('_', ' ')}</span>
            </div>
            <div class="field">
              <span class="field-name">Nationality:</span>
              <span class="field-value">${scanData.nationality || 'Unknown'}</span>
            </div>
          </div>
          
          <div class="section">
            <h2 class="section-title">Extracted Information</h2>
            ${scanData.extracted_info?.full_name ? `
              <div class="field">
                <span class="field-name">Full Name:</span>
                <span class="field-value">${scanData.extracted_info.full_name}</span>
              </div>
            ` : ''}
            ${scanData.extracted_info?.document_number ? `
              <div class="field">
                <span class="field-name">Document Number:</span>
                <span class="field-value">${scanData.extracted_info.document_number}</span>
              </div>
            ` : ''}
            ${scanData.extracted_info?.birth_date ? `
              <div class="field">
                <span class="field-name">Date of Birth:</span>
                <span class="field-value">${scanData.extracted_info.birth_date}</span>
              </div>
            ` : ''}
            ${scanData.extracted_info?.expiry_date ? `
              <div class="field">
                <span class="field-name">Expiry Date:</span>
                <span class="field-value">${scanData.extracted_info.expiry_date}</span>
              </div>
            ` : ''}
            ${scanData.extracted_info?.place_of_issue ? `
              <div class="field">
                <span class="field-name">Place of Issue:</span>
                <span class="field-value">${scanData.extracted_info.place_of_issue}</span>
              </div>
            ` : ''}
            ${scanData.extracted_info?.issue_date ? `
              <div class="field">
                <span class="field-name">Issue Date:</span>
                <span class="field-value">${scanData.extracted_info.issue_date}</span>
              </div>
            ` : ''}
            ${scanData.extracted_info?.gender ? `
              <div class="field">
                <span class="field-name">Gender:</span>
                <span class="field-value">${scanData.extracted_info.gender}</span>
              </div>
            ` : ''}
          </div>
          
          ${scanData.extracted_text ? `
            <div class="section">
              <h2 class="section-title">Raw Extracted Text</h2>
              <pre style="white-space: pre-wrap; background: #f5f5f5; padding: 10px; border-radius: 5px;">${scanData.extracted_text}</pre>
            </div>
          ` : ''}
          
          <div class="footer">
            <p>Generated by OCR Document Scanner on ${new Date().toLocaleString()}</p>
          </div>
        </body>
      </html>
    `);
    
    printWindow.document.close();
    setTimeout(() => {
      printWindow.print();
    }, 500);
    
    setSnackbarMessage('Print preview opened');
    setSnackbarOpen(true);
  };
  
  const handleExportJSON = () => {
    const dataStr = JSON.stringify(selectedScan, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
    
    const exportFileDefaultName = `scan_${selectedScan.document_type}_${new Date(selectedScan.timestamp).toISOString().split('T')[0]}.json`;
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
    
    setSnackbarMessage('Exported scan details as JSON');
    setSnackbarOpen(true);
  };
  
  const handleMenuOpen = (event) => {
    setMenuAnchorEl(event.currentTarget);
  };
  
  const handleMenuClose = () => {
    setMenuAnchorEl(null);
  };
  
  const handleCopyToClipboard = () => {
    const textToCopy = JSON.stringify(selectedScan, null, 2);
    navigator.clipboard.writeText(textToCopy)
      .then(() => {
        setSnackbarMessage('Copied scan details to clipboard');
        setSnackbarOpen(true);
        handleMenuClose();
      })
      .catch(err => {
        setSnackbarMessage('Failed to copy: ' + err);
        setSnackbarOpen(true);
        handleMenuClose();
      });
  };

  const handlePrintTable = () => {
    const printWindow = window.open('', '_blank');
    
    if (!printWindow) {
      setSnackbarMessage('Pop-up blocked. Please allow pop-ups for printing.');
      setSnackbarOpen(true);
      return;
    }
    
    const tableData = documents.map((document, index) => ({
      index: index + 1,
      timestamp: new Date(document.timestamp).toLocaleString(),
      documentType: document.document_type?.charAt(0).toUpperCase() + document.document_type?.slice(1).replace('_', ' '),
      fullName: document.full_name || 'N/A',
      documentNumber: document.document_number || 'N/A',
      nationality: document.nationality
    }));
    
    printWindow.document.write(`
      <!DOCTYPE html>
      <html>
        <head>
          <title>Documents Table</title>
          <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; }
            th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
            th { background-color: #f2f2f2; font-weight: bold; }
            tr:nth-child(even) { background-color: #f9f9f9; }
            .header { text-align: center; margin-bottom: 20px; }
            .doc-number { font-family: monospace; font-size: 0.9em; }
          </style>
        </head>
        <body>
          <div class="header">
            <h1>Recent Documents Table</h1>
            <p>Generated on: ${new Date().toLocaleString()}</p>
          </div>
          <table>
            <thead>
              <tr>
                <th>#</th>
                <th>Timestamp</th>
                <th>Document Type</th>
                <th>Full Name</th>
                <th>Document Number</th>
                <th>Nationality</th>
              </tr>
            </thead>
            <tbody>
              ${tableData.map(row => `
                <tr>
                  <td>${row.index}</td>
                  <td>${row.timestamp}</td>
                  <td>${row.documentType}</td>
                  <td>${row.fullName}</td>
                  <td class="doc-number">${row.documentNumber}</td>
                  <td>${row.nationality}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </body>
      </html>
    `);
    
    printWindow.document.close();
    setTimeout(() => {
      printWindow.print();
    }, 500);
    
    setSnackbarMessage('Print preview opened');
    setSnackbarOpen(true);
  };

  const handleOpenDocumentDetails = (document) => {
    setSelectedScan(document);
    setDialogOpen(true);
    setEditMode(false);
    setEditedScan(null);
    setTabValue(0);
  };

  useEffect(() => {
    fetchStats();
    fetchDocuments();
  }, []);

  // Prepare chart data for document types
  const documentTypeChartData = {
    labels: stats?.document_types ? Object.keys(stats.document_types).map(type => type.charAt(0).toUpperCase() + type.slice(1)) : [],
    datasets: [
      {
        label: 'Document Types',
        data: stats?.document_types ? Object.values(stats.document_types) : [],
        backgroundColor: [
          'rgba(54, 162, 235, 0.6)',
          'rgba(255, 99, 132, 0.6)',
          'rgba(255, 206, 86, 0.6)',
        ],
        borderColor: [
          'rgba(54, 162, 235, 1)',
          'rgba(255, 99, 132, 1)',
          'rgba(255, 206, 86, 1)',
        ],
        borderWidth: 1,
      },
    ],
  };

  // Prepare chart data for nationalities
  const nationalitiesChartData = {
    labels: stats?.nationalities ? Object.keys(stats.nationalities) : [],
    datasets: [
      {
        label: 'Nationalities',
        data: stats?.nationalities ? Object.values(stats.nationalities) : [],
        backgroundColor: [
          'rgba(75, 192, 192, 0.6)',
          'rgba(153, 102, 255, 0.6)',
          'rgba(255, 159, 64, 0.6)',
          'rgba(255, 99, 132, 0.6)',
          'rgba(54, 162, 235, 0.6)',
          'rgba(255, 206, 86, 0.6)',
        ],
        borderColor: [
          'rgba(75, 192, 192, 1)',
          'rgba(153, 102, 255, 1)',
          'rgba(255, 159, 64, 1)',
          'rgba(255, 99, 132, 1)',
          'rgba(54, 162, 235, 1)',
          'rgba(255, 206, 86, 1)',
        ],
        borderWidth: 1,
      },
    ],
  };

  return (
    <Box sx={{ overflow: 'hidden' }}>
    <Container maxWidth="lg" sx={{ mt: { xs: 2, sm: 3, md: 4 }, mb: { xs: 2, sm: 3, md: 4 }, px: { xs: 1, sm: 2, md: 3 } }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" component="div" sx={{ display: 'flex', alignItems: 'center', fontSize: { xs: '1.5rem', sm: '1.75rem', md: '2rem' } }}>
            <DescriptionIcon sx={{ mr: 1, fontSize: { xs: 24, sm: 28, md: 32 } }} /> 
            Document Scanner Dashboard
          </Typography>
          <Typography variant="subtitle1" color="text.secondary">
            Monitor document scanning statistics and history
          </Typography>
        </Box>
        <Box>
          <Tooltip title="Refresh statistics">
            <Button 
              variant="contained" 
              startIcon={<RefreshIcon sx={{ fontSize: { xs: 16, sm: 18, md: 20 } }} />} 
              onClick={fetchStats}
              size="medium"
              sx={{ mr: { xs: 1, sm: 2 }, px: { xs: 2, sm: 3 } }}
            >
              Refresh
            </Button>
          </Tooltip>
          <Tooltip title="Reset all statistics data">
            <Button 
              variant="outlined" 
              color="error" 
              startIcon={<DeleteIcon sx={{ fontSize: { xs: 16, sm: 18, md: 20 } }} />} 
              onClick={resetStats}
              size="medium"
              sx={{ px: { xs: 2, sm: 3 } }}
            >
              Reset Stats
            </Button>
          </Tooltip>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {loading ? (
        <Box sx={{ width: '100%' }}>
          <Grid container spacing={{ xs: 2, sm: 3, md: 4 }}>
            {[1, 2, 3, 4].map((item) => (
              <Grid item xs={12} md={3} key={item}>
                <Skeleton variant="rectangular" height={120} animation="wave" />
              </Grid>
            ))}
            {[1, 2].map((item) => (
              <Grid item xs={12} md={6} key={`chart-${item}`}>
                <Skeleton variant="rectangular" height={300} animation="wave" />
              </Grid>
            ))}
            <Grid item xs={12}>
              <Skeleton variant="rectangular" height={400} animation="wave" />
            </Grid>
          </Grid>
        </Box>
      ) : stats ? (
        <Grid container spacing={{ xs: 2, sm: 3, md: 4 }} className="dashboard-container">
          {/* Summary Cards */}
          <Grid item xs={12} sm={6} md={3}>
            <Paper 
              elevation={0}
              className="apple-card"
              sx={{ 
                p: { xs: 3, sm: 4 }, 
                display: 'flex', 
                flexDirection: 'column', 
                height: { xs: 140, sm: 160, md: 180 }, 
                position: 'relative', 
                overflow: 'hidden',
                borderRadius: 3,
                background: 'linear-gradient(145deg, rgba(255,255,255,0.9) 0%, rgba(255,255,255,0.6) 100%)',
                backdropFilter: 'blur(10px)',
                WebkitBackdropFilter: 'blur(10px)',
                boxShadow: '0 4px 20px rgba(0, 0, 0, 0.05)',
                border: '1px solid rgba(255, 255, 255, 0.3)',
              }}
            >
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <Typography 
                  variant="h6" 
                  color="#007AFF" 
                  gutterBottom 
                  sx={{ 
                    fontSize: { xs: '1rem', sm: '1.1rem', md: '1.25rem' },
                    fontWeight: 600,
                    letterSpacing: '-0.5px',
                  }}
                >
                  Total Scanned
                </Typography>
                <Box 
                  sx={{ 
                    bgcolor: 'rgba(0, 122, 255, 0.1)', 
                    borderRadius: '50%',
                    p: 1,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  <DescriptionIcon sx={{ fontSize: { xs: 24, sm: 28, md: 32 }, color: '#007AFF' }} />
                </Box>
              </Box>
              <Typography 
                variant="h3" 
                component="div" 
                sx={{ 
                  mt: 2, 
                  fontWeight: 700, 
                  fontSize: { xs: '2rem', sm: '2.2rem', md: '2.7rem' },
                  letterSpacing: '-1px',
                  color: '#000',
                }}
              >
                {stats?.total_scanned || 0}
              </Typography>
              <Typography 
                variant="body2" 
                sx={{ 
                  color: '#8E8E93',
                  fontWeight: 500,
                  mt: 0.5,
                }}
              >
                Documents processed
              </Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Paper 
              elevation={0}
              className="apple-card"
              sx={{ 
                p: { xs: 3, sm: 4 }, 
                display: 'flex', 
                flexDirection: 'column', 
                height: { xs: 140, sm: 160, md: 180 }, 
                position: 'relative', 
                overflow: 'hidden',
                borderRadius: 3,
                background: 'linear-gradient(145deg, rgba(255,255,255,0.9) 0%, rgba(255,255,255,0.6) 100%)',
                backdropFilter: 'blur(10px)',
                WebkitBackdropFilter: 'blur(10px)',
                boxShadow: '0 4px 20px rgba(0, 0, 0, 0.05)',
                border: '1px solid rgba(255, 255, 255, 0.3)',
              }}
            >
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <Typography 
                  variant="h6" 
                  color="#5AC8FA" 
                  gutterBottom 
                  sx={{ 
                    fontSize: { xs: '1rem', sm: '1.1rem', md: '1.25rem' },
                    fontWeight: 600,
                    letterSpacing: '-0.5px',
                  }}
                >
                  Passports
                </Typography>
                <Box 
                  sx={{ 
                    bgcolor: 'rgba(90, 200, 250, 0.1)', 
                    borderRadius: '50%',
                    p: 1,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  <PassportIcon sx={{ fontSize: { xs: 24, sm: 28, md: 32 }, color: '#5AC8FA' }} />
                </Box>
              </Box>
              <Typography 
                variant="h3" 
                component="div" 
                sx={{ 
                  mt: 2, 
                  fontWeight: 700, 
                  fontSize: { xs: '2rem', sm: '2.2rem', md: '2.7rem' },
                  letterSpacing: '-1px',
                  color: '#000',
                }}
              >
                {stats?.document_types?.passport || 0}
              </Typography>
              <Typography 
                variant="body2" 
                sx={{ 
                  color: '#8E8E93',
                  fontWeight: 500,
                  mt: 0.5,
                }}
              >
                {((stats?.document_types?.passport || 0) / (stats?.total_scanned || 1) * 100).toFixed(1)}% of total
              </Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Paper 
              elevation={0}
              className="apple-card"
              sx={{ 
                p: { xs: 3, sm: 4 }, 
                display: 'flex', 
                flexDirection: 'column', 
                height: { xs: 140, sm: 160, md: 180 }, 
                position: 'relative', 
                overflow: 'hidden',
                borderRadius: 3,
                background: 'linear-gradient(145deg, rgba(255,255,255,0.9) 0%, rgba(255,255,255,0.6) 100%)',
                backdropFilter: 'blur(10px)',
                WebkitBackdropFilter: 'blur(10px)',
                boxShadow: '0 4px 20px rgba(0, 0, 0, 0.05)',
                border: '1px solid rgba(255, 255, 255, 0.3)',
              }}
            >
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <Typography 
                  variant="h6" 
                  color="#34C759" 
                  gutterBottom 
                  sx={{ 
                    fontSize: { xs: '1rem', sm: '1.1rem', md: '1.25rem' },
                    fontWeight: 600,
                    letterSpacing: '-0.5px',
                  }}
                >
                  ID Cards
                </Typography>
                <Box 
                  sx={{ 
                    bgcolor: 'rgba(52, 199, 89, 0.1)', 
                    borderRadius: '50%',
                    p: 1,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  <BadgeIcon sx={{ fontSize: { xs: 24, sm: 28, md: 32 }, color: '#34C759' }} />
                </Box>
              </Box>
              <Typography 
                variant="h3" 
                component="div" 
                sx={{ 
                  mt: 2, 
                  fontWeight: 700, 
                  fontSize: { xs: '2rem', sm: '2.2rem', md: '2.7rem' },
                  letterSpacing: '-1px',
                  color: '#000',
                }}
              >
                {stats?.document_types?.id_card || 0}
              </Typography>
              <Typography 
                variant="body2" 
                sx={{ 
                  color: '#8E8E93',
                  fontWeight: 500,
                  mt: 0.5,
                }}
              >
                {((stats?.document_types?.id_card || 0) / (stats?.total_scanned || 1) * 100).toFixed(1)}% of total
              </Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Paper 
              elevation={0}
              className="apple-card"
              sx={{ 
                p: { xs: 3, sm: 4 }, 
                display: 'flex', 
                flexDirection: 'column', 
                height: { xs: 140, sm: 160, md: 180 }, 
                position: 'relative', 
                overflow: 'hidden',
                borderRadius: 3,
                background: 'linear-gradient(145deg, rgba(255,255,255,0.9) 0%, rgba(255,255,255,0.6) 100%)',
                backdropFilter: 'blur(10px)',
                WebkitBackdropFilter: 'blur(10px)',
                boxShadow: '0 4px 20px rgba(0, 0, 0, 0.05)',
                border: '1px solid rgba(255, 255, 255, 0.3)',
              }}
            >
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <Typography 
                  variant="h6" 
                  color="#FF9500" 
                  gutterBottom 
                  sx={{ 
                    fontSize: { xs: '1rem', sm: '1.1rem', md: '1.25rem' },
                    fontWeight: 600,
                    letterSpacing: '-0.5px',
                  }}
                >
                  Countries
                </Typography>
                <Box 
                  sx={{ 
                    bgcolor: 'rgba(255, 149, 0, 0.1)', 
                    borderRadius: '50%',
                    p: 1,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  <PublicIcon sx={{ fontSize: { xs: 24, sm: 28, md: 32 }, color: '#FF9500' }} />
                </Box>
              </Box>
              <Typography 
                variant="h3" 
                component="div" 
                sx={{ 
                  mt: 2, 
                  fontWeight: 700, 
                  fontSize: { xs: '2rem', sm: '2.2rem', md: '2.7rem' },
                  letterSpacing: '-1px',
                  color: '#000',
                }}
              >
                {stats?.nationalities ? Object.keys(stats.nationalities).length : 0}
              </Typography>
              <Typography 
                variant="body2" 
                sx={{ 
                  color: '#8E8E93',
                  fontWeight: 500,
                  mt: 0.5,
                }}
              >
                Unique nationalities
              </Typography>
            </Paper>
          </Grid>

          {/* Charts */}
          <Grid item xs={12} sm={6} md={6}>
            <Paper 
              elevation={0}
              className="apple-card"
              sx={{ 
                p: { xs: 3, sm: 3.5, md: 4 }, 
                display: 'flex', 
                flexDirection: 'column', 
                height: { xs: 320, sm: 370, md: 400 },
                position: 'relative',
                overflow: 'hidden',
                borderRadius: 3,
                background: 'linear-gradient(145deg, rgba(255,255,255,0.9) 0%, rgba(255,255,255,0.6) 100%)',
                backdropFilter: 'blur(10px)',
                WebkitBackdropFilter: 'blur(10px)',
                boxShadow: '0 4px 20px rgba(0, 0, 0, 0.05)',
                border: '1px solid rgba(255, 255, 255, 0.3)',
              }}
            >
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography 
                  variant="h6" 
                  sx={{ 
                    fontSize: { xs: '1rem', sm: '1.1rem', md: '1.25rem' },
                    fontWeight: 600,
                    letterSpacing: '-0.5px',
                    color: '#000',
                  }}
                >
                  Document Types
                </Typography>
                <Chip 
                  label={`${stats?.document_types ? Object.keys(stats.document_types).length : 0} types`} 
                  size="small" 
                  sx={{
                    bgcolor: 'rgba(0, 122, 255, 0.1)',
                    color: '#007AFF',
                    fontWeight: 500,
                    border: 'none',
                    borderRadius: '12px',
                    height: '24px',
                    '& .MuiChip-label': {
                      px: 1.5,
                      fontSize: '0.75rem',
                    }
                  }}
                />
              </Box>
              <Divider sx={{ mb: 3, opacity: 0.6 }} />
              <Box sx={{ flexGrow: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', px: { xs: 1, sm: 2, md: 3 } }}>
                {stats?.total_scanned > 0 ? (
                  <Pie 
                    data={{
                      ...documentTypeChartData,
                      datasets: documentTypeChartData.datasets.map(dataset => ({
                        ...dataset,
                        backgroundColor: [
                          'rgba(0, 122, 255, 0.8)',   // Apple Blue
                          'rgba(52, 199, 89, 0.8)',   // Apple Green
                          'rgba(255, 149, 0, 0.8)',   // Apple Orange
                          'rgba(90, 200, 250, 0.8)',  // Apple Light Blue
                          'rgba(255, 59, 48, 0.8)',   // Apple Red
                        ],
                        borderColor: [
                          'rgba(0, 122, 255, 1)',
                          'rgba(52, 199, 89, 1)',
                          'rgba(255, 149, 0, 1)',
                          'rgba(90, 200, 250, 1)',
                          'rgba(255, 59, 48, 1)',
                        ],
                        borderWidth: 1,
                        hoverBackgroundColor: [
                          'rgba(0, 122, 255, 0.9)',
                          'rgba(52, 199, 89, 0.9)',
                          'rgba(255, 149, 0, 0.9)',
                          'rgba(90, 200, 250, 0.9)',
                          'rgba(255, 59, 48, 0.9)',
                        ],
                      }))
                    }}
                    options={{ 
                      maintainAspectRatio: false,
                      plugins: {
                        legend: {
                          position: window.innerWidth < 600 ? 'top' : 'bottom',
                          labels: {
                            boxWidth: window.innerWidth < 600 ? 10 : 15,
                            padding: window.innerWidth < 600 ? 10 : 15,
                            font: {
                              family: '-apple-system, BlinkMacSystemFont, "San Francisco", "Helvetica Neue", sans-serif',
                              size: window.innerWidth < 600 ? 10 : 12,
                              weight: 500,
                            },
                            color: '#000',
                          }
                        },
                        tooltip: {
                          callbacks: {
                            label: function(context) {
                              if (stats && stats.total_scanned) {
                                const label = context.label || '';
                                const value = context.raw || 0;
                                const percentage = ((value / stats.total_scanned) * 100).toFixed(1);
                                return `${label}: ${value} (${percentage}%)`;
                              }
                              return '';
                            }
                          }
                        }
                      }
                    }} 
                  />
                ) : (
                  <Box sx={{ textAlign: 'center', py: 5 }}>
                    <DescriptionIcon sx={{ fontSize: 60, color: 'text.disabled', mb: 2 }} />
                    <Typography variant="body1" color="text.secondary">
                      No documents scanned yet
                    </Typography>
                  </Box>
                )}
              </Box>
            </Paper>
          </Grid>
          <Grid item xs={12} sm={6} md={6}>
            <Paper 
              elevation={0}
              className="apple-card"
              sx={{ 
                p: { xs: 3, sm: 3.5, md: 4 }, 
                display: 'flex', 
                flexDirection: 'column', 
                height: { xs: 320, sm: 370, md: 400 },
                position: 'relative',
                overflow: 'hidden',
                borderRadius: 3,
                background: 'linear-gradient(145deg, rgba(255,255,255,0.9) 0%, rgba(255,255,255,0.6) 100%)',
                backdropFilter: 'blur(10px)',
                WebkitBackdropFilter: 'blur(10px)',
                boxShadow: '0 4px 20px rgba(0, 0, 0, 0.05)',
                border: '1px solid rgba(255, 255, 255, 0.3)',
              }}
            >
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography 
                  variant="h6" 
                  sx={{ 
                    fontSize: { xs: '1rem', sm: '1.1rem', md: '1.25rem' },
                    fontWeight: 600,
                    letterSpacing: '-0.5px',
                    color: '#000',
                  }}
                >
                  Top Nationalities
                </Typography>
                <Chip 
                  label={`${stats?.nationalities ? Object.keys(stats.nationalities).length : 0} countries`} 
                  size="small" 
                  sx={{
                    bgcolor: 'rgba(255, 149, 0, 0.1)',
                    color: '#FF9500',
                    fontWeight: 500,
                    border: 'none',
                    borderRadius: '12px',
                    height: '24px',
                    '& .MuiChip-label': {
                      px: 1.5,
                      fontSize: '0.75rem',
                    }
                  }}
                />
              </Box>
              <Divider sx={{ mb: 3, opacity: 0.6 }} />
              <Box sx={{ flexGrow: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', px: { xs: 1, sm: 2, md: 3 } }}>
                {stats?.nationalities && Object.keys(stats.nationalities).length > 0 ? (
                  <Bar 
                    data={{
                      ...nationalitiesChartData,
                      datasets: nationalitiesChartData.datasets.map(dataset => ({
                        ...dataset,
                        backgroundColor: 'rgba(255, 149, 0, 0.8)',
                        borderColor: 'rgba(255, 149, 0, 1)',
                        borderWidth: 1,
                        borderRadius: 6,
                        hoverBackgroundColor: 'rgba(255, 149, 0, 0.9)',
                      }))
                    }}
                    options={{ 
                      maintainAspectRatio: false,
                      indexAxis: 'y',
                      scales: {
                        y: {
                          beginAtZero: true,
                          grid: {
                            display: false,
                            drawBorder: false,
                          },
                          ticks: {
                            font: {
                              family: '-apple-system, BlinkMacSystemFont, "San Francisco", "Helvetica Neue", sans-serif',
                              size: window.innerWidth < 600 ? 10 : 12,
                              weight: 500,
                            },
                            color: '#8E8E93',
                          }
                        },
                        x: {
                          beginAtZero: true,
                          grid: {
                            color: 'rgba(0, 0, 0, 0.05)',
                            drawBorder: false,
                          },
                          ticks: {
                            precision: 0,
                            font: {
                              family: '-apple-system, BlinkMacSystemFont, "San Francisco", "Helvetica Neue", sans-serif',
                              size: window.innerWidth < 600 ? 10 : 12,
                              weight: 500,
                            },
                            color: '#8E8E93',
                          }
                        }
                      },
                      plugins: {
                        legend: {
                          display: false
                        },
                        tooltip: {
                          callbacks: {
                            label: function(context) {
                              if (stats && stats.total_scanned) {
                                const label = context.dataset.label || '';
                                const value = context.raw || 0;
                                const percentage = ((value / stats.total_scanned) * 100).toFixed(1);
                                return `${label}: ${value} documents (${percentage}%)`;
                              }
                              return '';
                            }
                          }
                        }
                      }
                    }} 
                  />
                ) : (
                  <Box sx={{ textAlign: 'center', py: 5 }}>
                    <PublicIcon sx={{ fontSize: 60, color: 'text.disabled', mb: 2 }} />
                    <Typography variant="body1" color="text.secondary">
                      No nationality data available
                    </Typography>
                  </Box>
                )}
              </Box>
            </Paper>
          </Grid>

          {/* Document List */}
          <Grid item xs={12}>
            <Paper 
              elevation={0}
              className="apple-card"
              sx={{ 
                p: { xs: 3, sm: 3.5, md: 4 }, 
                overflow: 'hidden',
                borderRadius: 3,
                background: 'linear-gradient(145deg, rgba(255,255,255,0.9) 0%, rgba(255,255,255,0.6) 100%)',
                backdropFilter: 'blur(10px)',
                WebkitBackdropFilter: 'blur(10px)',
                boxShadow: '0 4px 20px rgba(0, 0, 0, 0.05)',
                border: '1px solid rgba(255, 255, 255, 0.3)',
              }}
            >
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography 
                  variant="h6" 
                  sx={{ 
                    fontSize: { xs: '1rem', sm: '1.1rem', md: '1.25rem' },
                    fontWeight: 600,
                    letterSpacing: '-0.5px',
                    color: '#000',
                  }}
                >
                  Recent Documents
                </Typography>
                <Box>
                  <Button 
                    startIcon={<RefreshIcon />} 
                    size="small" 
                    onClick={fetchDocuments}
                    sx={{ 
                      mr: 1.5, 
                      color: '#007AFF',
                      borderRadius: '12px',
                      px: 2,
                      py: 0.75,
                      textTransform: 'none',
                      fontWeight: 500,
                      '&:hover': {
                        backgroundColor: 'rgba(0, 122, 255, 0.1)',
                      },
                    }}
                  >
                    Refresh
                  </Button>
                  <Button 
                    startIcon={<PrintIcon />} 
                    size="small" 
                    onClick={handlePrintTable}
                    disabled={documents.length === 0}
                    sx={{
                      bgcolor: '#007AFF',
                      color: '#fff',
                      borderRadius: '12px',
                      px: 2,
                      py: 0.75,
                      textTransform: 'none',
                      fontWeight: 500,
                      border: 'none',
                      '&:hover': {
                        bgcolor: 'rgba(0, 122, 255, 0.9)',
                      },
                      '&:disabled': {
                        bgcolor: 'rgba(0, 0, 0, 0.1)',
                        color: 'rgba(0, 0, 0, 0.3)',
                      },
                    }}
                  >
                    Print
                  </Button>
                </Box>
              </Box>
              <Divider sx={{ mb: 3, opacity: 0.6 }} />
              {documentsLoading ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', p: 4, flexDirection: 'column' }}>
                  <CircularProgress size={40} sx={{ color: '#007AFF', mb: 2 }} />
                  <Typography variant="body2" sx={{ color: '#8E8E93', fontWeight: 500 }}>
                    Loading documents...
                  </Typography>
                </Box>
              ) : error ? (
                <Alert 
                  severity="error" 
                  sx={{ 
                    mb: 2, 
                    borderRadius: 2,
                    bgcolor: 'rgba(255, 59, 48, 0.1)',
                    color: '#FF3B30',
                    '& .MuiAlert-icon': {
                      color: '#FF3B30',
                    },
                  }}
                >
                  {error}
                  <Button 
                    size="small" 
                    onClick={fetchDocuments} 
                    sx={{ 
                      ml: 2, 
                      color: '#FF3B30',
                      fontWeight: 500,
                      '&:hover': {
                        bgcolor: 'rgba(255, 59, 48, 0.1)',
                      },
                    }}
                  >
                    Retry
                  </Button>
                </Alert>
              ) : documents.length === 0 ? (
                <Alert 
                  severity="info" 
                  sx={{ 
                    mb: 2, 
                    borderRadius: 2,
                    bgcolor: 'rgba(0, 122, 255, 0.1)',
                    color: '#007AFF',
                    '& .MuiAlert-icon': {
                      color: '#007AFF',
                    },
                  }}
                >
                  No documents found. Start scanning to see your documents here.
                </Alert>
              ) : (
                <TableContainer 
                  sx={{ 
                    maxHeight: { xs: 350, sm: 400, md: 450 }, 
                    overflowX: 'auto',
                    borderRadius: 2,
                    '&::-webkit-scrollbar': {
                      width: '8px',
                      height: '8px',
                    },
                    '&::-webkit-scrollbar-track': {
                      backgroundColor: 'rgba(0, 0, 0, 0.05)',
                      borderRadius: '10px',
                    },
                    '&::-webkit-scrollbar-thumb': {
                      backgroundColor: 'rgba(0, 0, 0, 0.15)',
                      borderRadius: '10px',
                      '&:hover': {
                        backgroundColor: 'rgba(0, 0, 0, 0.25)',
                      },
                    },
                  }}
                >
                  <Table stickyHeader size={window.innerWidth < 600 ? 'small' : 'medium'}>
                    <TableHead>
                      <TableRow>
                        <TableCell 
                          sx={{ 
                            fontWeight: 600, 
                            p: { xs: 1.5, sm: 2 },
                            backgroundColor: 'rgba(255, 255, 255, 0.9)',
                            backdropFilter: 'blur(10px)',
                            WebkitBackdropFilter: 'blur(10px)',
                            color: '#000',
                            borderBottom: '1px solid rgba(0, 0, 0, 0.1)',
                            letterSpacing: '-0.3px',
                          }}
                        >
                          #
                        </TableCell>
                        <TableCell 
                          sx={{ 
                            fontWeight: 600, 
                            p: { xs: 1.5, sm: 2 }, 
                            display: { xs: 'none', sm: 'table-cell' },
                            backgroundColor: 'rgba(255, 255, 255, 0.9)',
                            backdropFilter: 'blur(10px)',
                            WebkitBackdropFilter: 'blur(10px)',
                            color: '#000',
                            borderBottom: '1px solid rgba(0, 0, 0, 0.1)',
                            letterSpacing: '-0.3px',
                          }}
                        >
                          Timestamp
                        </TableCell>
                        <TableCell 
                          sx={{ 
                            fontWeight: 600, 
                            p: { xs: 1.5, sm: 2 },
                            backgroundColor: 'rgba(255, 255, 255, 0.9)',
                            backdropFilter: 'blur(10px)',
                            WebkitBackdropFilter: 'blur(10px)',
                            color: '#000',
                            borderBottom: '1px solid rgba(0, 0, 0, 0.1)',
                            letterSpacing: '-0.3px',
                          }}
                        >
                          Document Type
                        </TableCell>
                        <TableCell 
                          sx={{ 
                            fontWeight: 600, 
                            p: { xs: 1.5, sm: 2 }, 
                            display: { xs: 'none', lg: 'table-cell' },
                            backgroundColor: 'rgba(255, 255, 255, 0.9)',
                            backdropFilter: 'blur(10px)',
                            WebkitBackdropFilter: 'blur(10px)',
                            color: '#000',
                            borderBottom: '1px solid rgba(0, 0, 0, 0.1)',
                            letterSpacing: '-0.3px',
                          }}
                        >
                          Full Name
                        </TableCell>
                        <TableCell 
                          sx={{ 
                            fontWeight: 600, 
                            p: { xs: 1.5, sm: 2 }, 
                            display: { xs: 'none', lg: 'table-cell' },
                            backgroundColor: 'rgba(255, 255, 255, 0.9)',
                            backdropFilter: 'blur(10px)',
                            WebkitBackdropFilter: 'blur(10px)',
                            color: '#000',
                            borderBottom: '1px solid rgba(0, 0, 0, 0.1)',
                            letterSpacing: '-0.3px',
                          }}
                        >
                          Document Number
                        </TableCell>
                        <TableCell 
                          sx={{ 
                            fontWeight: 600, 
                            p: { xs: 1.5, sm: 2 }, 
                            display: { xs: 'none', md: 'table-cell' },
                            backgroundColor: 'rgba(255, 255, 255, 0.9)',
                            backdropFilter: 'blur(10px)',
                            WebkitBackdropFilter: 'blur(10px)',
                            color: '#000',
                            borderBottom: '1px solid rgba(0, 0, 0, 0.1)',
                            letterSpacing: '-0.3px',
                          }}
                        >
                          Nationality
                        </TableCell>
                        <TableCell 
                          align="center" 
                          sx={{ 
                            fontWeight: 600, 
                            p: { xs: 1.5, sm: 2 },
                            backgroundColor: 'rgba(255, 255, 255, 0.9)',
                            backdropFilter: 'blur(10px)',
                            WebkitBackdropFilter: 'blur(10px)',
                            color: '#000',
                            borderBottom: '1px solid rgba(0, 0, 0, 0.1)',
                            letterSpacing: '-0.3px',
                          }}
                        >
                          Actions
                        </TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {documents.map((document, index) => (
                        <TableRow 
                          key={index}
                          sx={{
                            '&:nth-of-type(odd)': { backgroundColor: 'rgba(0, 0, 0, 0.02)' },
                            '&:hover': { backgroundColor: 'rgba(0, 0, 0, 0.04)' },
                            borderRadius: '8px',
                            overflow: 'hidden',
                          }}
                        >
                          <TableCell 
                            sx={{ 
                              p: { xs: 1.5, sm: 2 },
                              borderBottom: '1px solid rgba(0, 0, 0, 0.05)',
                              color: '#1C1C1E',
                            }}
                          >
                            {index + 1}
                          </TableCell>
                          <TableCell 
                            sx={{ 
                              p: { xs: 1.5, sm: 2 }, 
                              display: { xs: 'none', sm: 'table-cell' },
                              borderBottom: '1px solid rgba(0, 0, 0, 0.05)',
                              color: '#1C1C1E',
                            }}
                          >
                            <Box sx={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap' }}>
                              <Typography variant="body2" sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' }, fontWeight: 500 }}>
                                {new Date(document.timestamp).toLocaleString(undefined, { 
                                  year: 'numeric', 
                                  month: 'short', 
                                  day: 'numeric',
                                  hour: '2-digit',
                                  minute: '2-digit',
                                  hour12: true
                                })}
                              </Typography>
                              {index === 0 && (
                                <Chip 
                                  label="Latest" 
                                  size="small" 
                                  sx={{ 
                                    ml: 1, 
                                    height: { xs: 18, sm: 22 }, 
                                    bgcolor: 'rgba(0, 122, 255, 0.1)',
                                    color: '#007AFF',
                                    fontWeight: 500,
                                    border: 'none',
                                    borderRadius: '10px',
                                    '& .MuiChip-label': { 
                                      px: 1,
                                      fontSize: { xs: '0.6rem', sm: '0.7rem' } 
                                    } 
                                  }} 
                                />
                              )}
                            </Box>
                          </TableCell>
                          <TableCell 
                            sx={{ 
                              p: { xs: 1.5, sm: 2 },
                              borderBottom: '1px solid rgba(0, 0, 0, 0.05)',
                              color: '#1C1C1E',
                            }}
                          >
                            <Box sx={{ display: 'flex', alignItems: 'center' }}>
                              {document.document_type === 'passport' ? (
                                <Box 
                                  sx={{ 
                                    bgcolor: 'rgba(0, 122, 255, 0.1)',
                                    borderRadius: '50%',
                                    p: 0.75,
                                    mr: 1.5,
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                  }}
                                >
                                  <PassportIcon sx={{ fontSize: { xs: '0.9rem', sm: '1.1rem' }, color: '#007AFF' }} />
                                </Box>
                              ) : document.document_type === 'us_green_card' ? (
                                <Box 
                                  sx={{ 
                                    bgcolor: 'rgba(52, 199, 89, 0.1)',
                                    borderRadius: '50%',
                                    p: 0.75,
                                    mr: 1.5,
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                  }}
                                >
                                  <CreditCardIcon sx={{ fontSize: { xs: '0.9rem', sm: '1.1rem' }, color: '#34C759' }} />
                                </Box>
                              ) : (document.document_type === 'id_card' || document.document_type === 'ID Card') ? (
                                <Box 
                                  sx={{ 
                                    bgcolor: 'rgba(52, 199, 89, 0.1)',
                                    borderRadius: '50%',
                                    p: 0.75,
                                    mr: 1.5,
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                  }}
                                >
                                  <BadgeIcon sx={{ fontSize: { xs: '0.9rem', sm: '1.1rem' }, color: '#34C759' }} />
                                </Box>
                              ) : (
                                <Box 
                                  sx={{ 
                                    bgcolor: 'rgba(255, 149, 0, 0.1)',
                                    borderRadius: '50%',
                                    p: 0.75,
                                    mr: 1.5,
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                  }}
                                >
                                  <DescriptionIcon sx={{ fontSize: { xs: '0.9rem', sm: '1.1rem' }, color: '#FF9500' }} />
                                </Box>
                              )}
                              <Typography 
                                variant="body2" 
                                sx={{ 
                                  fontSize: { xs: '0.75rem', sm: '0.875rem' },
                                  fontWeight: 500,
                                }}
                              >
                                {document.document_type.charAt(0).toUpperCase() + document.document_type.slice(1).replace('_', ' ')}
                              </Typography>
                            </Box>
                          </TableCell>
                          <TableCell 
                            sx={{ 
                              p: { xs: 1.5, sm: 2 }, 
                              display: { xs: 'none', lg: 'table-cell' },
                              borderBottom: '1px solid rgba(0, 0, 0, 0.05)',
                              color: '#1C1C1E',
                            }}
                          >
                            <Box sx={{ display: 'flex', alignItems: 'center' }}>
                              <PersonIcon sx={{ fontSize: { xs: '0.9rem', sm: '1rem' }, mr: 1, color: 'text.secondary' }} />
                              <Typography 
                                variant="body2" 
                                sx={{ 
                                  fontSize: { xs: '0.75rem', sm: '0.875rem' },
                                  fontWeight: 500,
                                  maxWidth: '150px',
                                  overflow: 'hidden',
                                  textOverflow: 'ellipsis',
                                  whiteSpace: 'nowrap'
                                }}
                              >
                                {document.full_name || 'N/A'}
                              </Typography>
                            </Box>
                          </TableCell>
                          <TableCell 
                            sx={{ 
                              p: { xs: 1.5, sm: 2 }, 
                              display: { xs: 'none', lg: 'table-cell' },
                              borderBottom: '1px solid rgba(0, 0, 0, 0.05)',
                              color: '#1C1C1E',
                            }}
                          >
                            <Box sx={{ display: 'flex', alignItems: 'center' }}>
                              <FingerprintIcon sx={{ fontSize: { xs: '0.9rem', sm: '1rem' }, mr: 1, color: 'text.secondary' }} />
                              <Typography 
                                variant="body2" 
                                sx={{ 
                                  fontSize: { xs: '0.75rem', sm: '0.875rem' },
                                  fontWeight: 500,
                                  fontFamily: 'monospace',
                                  maxWidth: '120px',
                                  overflow: 'hidden',
                                  textOverflow: 'ellipsis',
                                  whiteSpace: 'nowrap'
                                }}
                              >
                                {document.document_number || 'N/A'}
                              </Typography>
                            </Box>
                          </TableCell>
                          <TableCell 
                            sx={{ 
                              p: { xs: 1.5, sm: 2 }, 
                              display: { xs: 'none', md: 'table-cell' },
                              borderBottom: '1px solid rgba(0, 0, 0, 0.05)',
                              color: '#1C1C1E',
                            }}
                          >
                            <Chip 
                              label={document.nationality} 
                              size="small" 
                              sx={{ 
                                height: { xs: 22, sm: 26 }, 
                                bgcolor: 'rgba(0, 0, 0, 0.05)',
                                color: '#1C1C1E',
                                fontWeight: 500,
                                border: 'none',
                                borderRadius: '12px',
                                '& .MuiChip-label': { 
                                  fontSize: { xs: '0.65rem', sm: '0.75rem' }, 
                                  px: { xs: 1, sm: 1.5 } 
                                } 
                              }}
                            />
                          </TableCell>
                          <TableCell 
                            align="center" 
                            sx={{ 
                              p: { xs: 1.5, sm: 2 },
                              borderBottom: '1px solid rgba(0, 0, 0, 0.05)',
                            }}
                          >
                            <Tooltip title="View document details">
                              <IconButton 
                                size="small" 
                                onClick={() => handleOpenDocumentDetails(document)}
                                sx={{ 
                                  p: { xs: 0.75, sm: 1 },
                                  color: '#007AFF',
                                  bgcolor: 'rgba(0, 122, 255, 0.1)',
                                  '&:hover': {
                                    bgcolor: 'rgba(0, 122, 255, 0.2)',
                                  },
                                }}
                              >
                                <VisibilityIcon sx={{ fontSize: { xs: '0.9rem', sm: '1.1rem' } }} />
                              </IconButton>
                            </Tooltip>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              )}
            </Paper>
          </Grid>

          {/* Scan History */}
          <Grid item xs={12}>
            <Paper sx={{ p: { xs: 2, sm: 2.5, md: 3 } }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Box>
                  <Typography variant="h6" color="primary" sx={{ fontSize: { xs: '1rem', sm: '1.1rem', md: '1.25rem' } }}>
                    Scan History
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {stats?.scan_history?.length || 0} {(stats?.scan_history?.length || 0) === 1 ? 'entry' : 'entries'} in total
                  </Typography>
                </Box>
                {stats?.scan_history?.length > 0 && (
                  <Tooltip title="Export scan history as CSV">
                    <IconButton 
                      color="primary"
                      size="small"
                      onClick={() => {
                        // Create CSV content with enhanced data
                        const headers = ['Document Type', 'Full Name', 'Document Number', 'Date of Birth', 'Nationality', 'Timestamp'];
                        const csvContent = [
                          headers.join(','),
                          ...stats.scan_history.map(scan => [
                            scan.document_type,
                            scan.extracted_info?.full_name || 'N/A',
                            scan.extracted_info?.document_number || 'N/A',
                            scan.extracted_info?.birth_date || 'N/A',
                            scan.nationality,
                            new Date(scan.timestamp).toLocaleString()
                          ].join(','))
                        ].join('\n');
                        
                        // Create download link
                        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
                        const url = URL.createObjectURL(blob);
                        const link = document.createElement('a');
                        link.setAttribute('href', url);
                        link.setAttribute('download', `scan_history_${new Date().toISOString().split('T')[0]}.csv`);
                        link.style.visibility = 'hidden';
                        document.body.appendChild(link);
                        setTimeout(() => {
                          link.click();
                          document.body.removeChild(link);
                        }, 100);
                      }}
                    >
                      <DownloadIcon sx={{ fontSize: { xs: 18, sm: 20, md: 22 } }} />
                    </IconButton>
                  </Tooltip>
                )}
              </Box>
              <Divider sx={{ mb: 2 }} />
              <TableContainer sx={{ maxHeight: { xs: 350, sm: 400, md: 450 }, overflowX: 'auto' }}>
                <Table stickyHeader size={window.innerWidth < 600 ? 'small' : 'medium'}>
                  <TableHead>
                    <TableRow>
                      <TableCell sx={{ fontWeight: 'bold', p: { xs: 1, sm: 2 } }}>#</TableCell>
                      <TableCell sx={{ fontWeight: 'bold', p: { xs: 1, sm: 2 }, display: { xs: 'none', sm: 'table-cell' } }}>Timestamp</TableCell>
                      <TableCell sx={{ fontWeight: 'bold', p: { xs: 1, sm: 2 } }}>Document Type</TableCell>
                      <TableCell sx={{ fontWeight: 'bold', p: { xs: 1, sm: 2 }, display: { xs: 'none', lg: 'table-cell' } }}>Full Name</TableCell>
                      <TableCell sx={{ fontWeight: 'bold', p: { xs: 1, sm: 2 }, display: { xs: 'none', lg: 'table-cell' } }}>Document No.</TableCell>
                      <TableCell sx={{ fontWeight: 'bold', p: { xs: 1, sm: 2 }, display: { xs: 'none', md: 'table-cell' } }}>Nationality</TableCell>
                      <TableCell align="center" sx={{ fontWeight: 'bold', p: { xs: 1, sm: 2 } }}>Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {stats?.scan_history?.length > 0 ? (
                      stats.scan_history.map((scan, index) => (
                        <TableRow 
                          key={index}
                          sx={{
                            '&:nth-of-type(odd)': { backgroundColor: 'rgba(0, 0, 0, 0.02)' },
                            '&:hover': { backgroundColor: 'rgba(0, 0, 0, 0.04)' },
                          }}
                        >
                          <TableCell sx={{ p: { xs: 1, sm: 2 } }}>{index + 1}</TableCell>
                          <TableCell sx={{ p: { xs: 1, sm: 2 }, display: { xs: 'none', sm: 'table-cell' } }}>
                            <Box sx={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap' }}>
                              {new Date(scan.timestamp).toLocaleString(undefined, { 
                                year: 'numeric', 
                                month: 'short', 
                                day: 'numeric',
                                hour: '2-digit',
                                minute: '2-digit',
                                hour12: true
                              })}
                              {index === 0 && (
                                <Chip 
                                  label="Latest" 
                                  color="primary" 
                                  size="small" 
                                  sx={{ ml: 1, height: { xs: 16, sm: 20 }, '& .MuiChip-label': { fontSize: { xs: '0.6rem', sm: '0.7rem' } } }} 
                                />
                              )}
                            </Box>
                          </TableCell>
                          <TableCell sx={{ p: { xs: 1, sm: 2 } }}>
                            <Box sx={{ display: 'flex', alignItems: 'center' }}>
                              {scan.document_type === 'passport' ? (
                                <PassportIcon sx={{ fontSize: { xs: '1rem', sm: '1.25rem' }, mr: { xs: 0.5, sm: 1 }, color: 'info.main' }} />
                              ) : scan.document_type === 'us_green_card' ? (
                                <CreditCardIcon sx={{ fontSize: { xs: '1rem', sm: '1.25rem' }, mr: { xs: 0.5, sm: 1 }, color: 'success.main' }} />
                              ) : (scan.document_type === 'id_card' || scan.document_type === 'ID Card') ? (
                                <BadgeIcon sx={{ fontSize: { xs: '1rem', sm: '1.25rem' }, mr: { xs: 0.5, sm: 1 }, color: 'success.main' }} />
                              ) : (
                                <DescriptionIcon sx={{ fontSize: { xs: '1rem', sm: '1.25rem' }, mr: { xs: 0.5, sm: 1 }, color: 'warning.main' }} />
                              )}
                              <Typography variant="body2" sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}>
                                {scan.document_type === 'id_card' ? 'ID Card' : 
                                 scan.document_type === 'driving_license' ? 'Driving License' :
                                 scan.document_type === 'us_green_card' ? 'US Green Card' :
                                 scan.document_type.charAt(0).toUpperCase() + scan.document_type.slice(1).replace('_', ' ')}
                              </Typography>
                            </Box>
                          </TableCell>
                          <TableCell sx={{ p: { xs: 1, sm: 2 }, display: { xs: 'none', lg: 'table-cell' } }}>
                            <Box sx={{ display: 'flex', alignItems: 'center' }}>
                              <PersonIcon sx={{ fontSize: { xs: '0.9rem', sm: '1rem' }, mr: 1, color: 'text.secondary' }} />
                              <Typography 
                                variant="body2" 
                                sx={{ 
                                  fontSize: { xs: '0.75rem', sm: '0.875rem' },
                                  maxWidth: '150px',
                                  overflow: 'hidden',
                                  textOverflow: 'ellipsis',
                                  whiteSpace: 'nowrap'
                                }}
                              >
                                {scan.extracted_info?.full_name || 'N/A'}
                              </Typography>
                            </Box>
                          </TableCell>
                          <TableCell sx={{ p: { xs: 1, sm: 2 }, display: { xs: 'none', lg: 'table-cell' } }}>
                            <Box sx={{ display: 'flex', alignItems: 'center' }}>
                              <FingerprintIcon sx={{ fontSize: { xs: '0.9rem', sm: '1rem' }, mr: 1, color: 'text.secondary' }} />
                              <Typography 
                                variant="body2" 
                                sx={{ 
                                  fontSize: { xs: '0.75rem', sm: '0.875rem' },
                                  fontFamily: 'monospace',
                                  maxWidth: '120px',
                                  overflow: 'hidden',
                                  textOverflow: 'ellipsis',
                                  whiteSpace: 'nowrap'
                                }}
                              >
                                {scan.extracted_info?.document_number || 'N/A'}
                              </Typography>
                            </Box>
                          </TableCell>
                          <TableCell sx={{ p: { xs: 1, sm: 2 }, display: { xs: 'none', md: 'table-cell' } }}>
                            <Chip 
                              label={scan.nationality} 
                              size="small" 
                              variant="outlined" 
                              color="default" 
                              sx={{ height: { xs: 20, sm: 24 }, '& .MuiChip-label': { fontSize: { xs: '0.65rem', sm: '0.75rem' }, px: { xs: 0.5, sm: 1 } } }}
                            />
                          </TableCell>
                          <TableCell align="center" sx={{ p: { xs: 1, sm: 2 } }}>
                            <Tooltip title="View scan details">
                              <IconButton 
                                size="small" 
                                color="primary" 
                                onClick={() => handleOpenScanDetails(scan)}
                                sx={{ p: { xs: 0.5, sm: 1 } }}
                              >
                                <VisibilityIcon sx={{ fontSize: { xs: '1rem', sm: '1.25rem' } }} />
                              </IconButton>
                            </Tooltip>
                          </TableCell>
                        </TableRow>
                      ))
                    ) : (
                      <TableRow>
                        <TableCell colSpan={7} align="center" sx={{ py: 4 }}>
                          <Box sx={{ textAlign: 'center' }}>
                            <DescriptionIcon sx={{ fontSize: { xs: 32, sm: 40 }, color: 'text.disabled', mb: 1 }} />
                            <Typography variant="body1" color="text.secondary">
                              No scan history available
                            </Typography>
                            <Typography variant="body2" color="text.secondary">
                              Use the Scanner page to scan documents
                            </Typography>
                          </Box>
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
            </Paper>
          </Grid>
        </Grid>
      ) : (
        <Typography variant="body1">No data available</Typography>
      )}
    </Container>

    {/* Scan Details Dialog */}
    <Dialog 
      open={dialogOpen} 
      onClose={handleCloseScanDetails}
      fullWidth
      maxWidth="md"
      sx={{
        '& .MuiDialog-paper': {
          width: '100%',
          margin: { xs: '16px', sm: '24px', md: '32px' },
          maxHeight: { xs: 'calc(100% - 32px)', sm: 'calc(100% - 48px)', md: 'calc(100% - 64px)' }
        }
      }}
    >
      <DialogTitle sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', pb: 1, px: { xs: 2, sm: 3 } }}>
        <Box sx={{ display: 'flex', alignItems: 'center', overflow: 'hidden' }}>
          {selectedScan?.document_type === 'passport' ? (
            <PassportIcon sx={{ mr: 1, color: 'info.main', fontSize: { xs: '1.25rem', sm: '1.5rem' } }} />
          ) : selectedScan?.document_type === 'us_green_card' ? (
            <CreditCardIcon sx={{ mr: 1, color: 'success.main', fontSize: { xs: '1.25rem', sm: '1.5rem' } }} />
          ) : (selectedScan?.document_type === 'id_card' || selectedScan?.document_type === 'ID Card') ? (
            <BadgeIcon sx={{ mr: 1, color: 'success.main', fontSize: { xs: '1.25rem', sm: '1.5rem' } }} />
          ) : (
            <DescriptionIcon sx={{ mr: 1, color: 'warning.main', fontSize: { xs: '1.25rem', sm: '1.5rem' } }} />
          )}
          <Typography variant="h6" sx={{ fontSize: { xs: '1rem', sm: '1.25rem' }, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
            {selectedScan?.document_type === 'us_green_card' ? 'US Green Card Details' : 
             selectedScan?.document_type?.charAt(0).toUpperCase() + selectedScan?.document_type?.slice(1).replace('_', ' ')} Details
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', ml: 1, flexShrink: 0 }}>
          {!editMode && (
            <>
              <Tooltip title="Print">
                <IconButton onClick={handlePrintScan} size="small" sx={{ mr: { xs: 0.5, sm: 1 }, p: { xs: 0.5, sm: 1 } }}>
                  <PrintIcon sx={{ fontSize: { xs: '1.1rem', sm: '1.25rem' } }} />
                </IconButton>
              </Tooltip>
              <Tooltip title="More options">
                <IconButton 
                  onClick={handleMenuOpen} 
                  size="small" 
                  sx={{ mr: { xs: 0.5, sm: 1 }, p: { xs: 0.5, sm: 1 } }}
                  aria-controls={menuOpen ? 'scan-menu' : undefined}
                  aria-haspopup="true"
                  aria-expanded={menuOpen ? 'true' : undefined}
                >
                  <MoreVertIcon sx={{ fontSize: { xs: '1.1rem', sm: '1.25rem' } }} />
                </IconButton>
              </Tooltip>
            </>
          )}
          <IconButton onClick={handleCloseScanDetails} size="small">
            <CloseIcon />
          </IconButton>
        </Box>
        
        {/* Options Menu */}
        <Menu
          id="scan-menu"
          anchorEl={menuAnchorEl}
          open={menuOpen}
          onClose={handleMenuClose}
          MenuListProps={{
            'aria-labelledby': 'more-options-button',
          }}
        >
          <MenuItem onClick={handleEditClick}>
            <EditIcon fontSize="small" sx={{ mr: 1 }} />
            Edit Details
          </MenuItem>
          <MenuItem onClick={handleExportJSON}>
            <FileDownloadIcon fontSize="small" sx={{ mr: 1 }} />
            Export as JSON
          </MenuItem>
          <MenuItem onClick={handleCopyToClipboard}>
            <ContentCopyIcon fontSize="small" sx={{ mr: 1 }} />
            Copy to Clipboard
          </MenuItem>
        </Menu>
      </DialogTitle>
      
      <Box sx={{ borderBottom: 1, borderColor: 'divider', px: { xs: 1, sm: 2 } }}>
        <Tabs 
          value={tabValue} 
          onChange={handleTabChange} 
          aria-label="scan details tabs"
          variant={window.innerWidth < 600 ? "scrollable" : "standard"}
          scrollButtons={window.innerWidth < 600 ? "auto" : false}
          allowScrollButtonsMobile
          sx={{ 
            minHeight: { xs: 40, sm: 48 },
            '& .MuiTab-root': { 
              minHeight: { xs: 40, sm: 48 },
              fontSize: { xs: '0.8rem', sm: '0.9rem' },
              px: { xs: 1, sm: 2 },
              py: { xs: 0.5, sm: 1 }
            }
          }}
        >
          <Tab label="Details" />
          <Tab label="Raw Text" />
          {selectedScan?.image_data && <Tab label="Image" />}
        </Tabs>
      </Box>
      <DialogContent dividers sx={{ px: { xs: 2, sm: 3 }, py: { xs: 2, sm: 2.5 } }}>
        {selectedScan && (
          <>
            {/* Tab Panel 0: Details */}
            {tabValue === 0 && (
              <Grid container spacing={{ xs: 2, sm: 3 }}>
                {/* Document Information */}
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle1" color="primary" gutterBottom sx={{ fontSize: { xs: '0.9rem', sm: '1rem', md: '1.1rem' } }}>
                    Document Information
                  </Typography>
                  {editMode ? (
                    <Box sx={{ mt: { xs: 1, sm: 2 } }}>
                      <TextField
                        label="Document Type"
                        value={editedScan.document_type || ''}
                        onChange={(e) => handleEditFieldChange('document_type', e.target.value)}
                        fullWidth
                        margin="dense"
                        size="small"
                        select
                        sx={{ 
                          mb: { xs: 1, sm: 1.5 },
                          '& .MuiInputLabel-root': { fontSize: { xs: '0.8rem', sm: '0.875rem' } },
                          '& .MuiInputBase-input': { fontSize: { xs: '0.8rem', sm: '0.875rem' } },
                          '& .MuiMenuItem-root': { fontSize: { xs: '0.8rem', sm: '0.875rem' } }
                        }}
                      >
                        <MenuItem value="passport">Passport</MenuItem>
                        <MenuItem value="id_card">ID Card</MenuItem>
                        <MenuItem value="driving_license">Driving License</MenuItem>
                        <MenuItem value="us_green_card">US Green Card</MenuItem>
                        <MenuItem value="other">Other</MenuItem>
                      </TextField>
                      <TextField
                        label="Nationality"
                        value={editedScan.nationality || ''}
                        onChange={(e) => handleEditFieldChange('nationality', e.target.value)}
                        fullWidth
                        margin="dense"
                        size="small"
                        sx={{ 
                          mb: { xs: 1, sm: 1.5 },
                          '& .MuiInputLabel-root': { fontSize: { xs: '0.8rem', sm: '0.875rem' } },
                          '& .MuiInputBase-input': { fontSize: { xs: '0.8rem', sm: '0.875rem' } }
                        }}
                      />
                      <TextField
                        label="Scan Date"
                        value={new Date(editedScan.timestamp).toISOString().split('T')[0]}
                        type="date"
                        fullWidth
                        margin="dense"
                        size="small"
                        InputLabelProps={{ shrink: true }}
                        onChange={(e) => {
                          const newDate = new Date(e.target.value);
                          const currentDate = new Date(editedScan.timestamp);
                          currentDate.setFullYear(newDate.getFullYear());
                          currentDate.setMonth(newDate.getMonth());
                          currentDate.setDate(newDate.getDate());
                          handleEditFieldChange('timestamp', currentDate.toISOString());
                        }}
                        sx={{ 
                          '& .MuiInputLabel-root': { fontSize: { xs: '0.8rem', sm: '0.875rem' } },
                          '& .MuiInputBase-input': { fontSize: { xs: '0.8rem', sm: '0.875rem' } }
                        }}
                      />
                    </Box>
                  ) : (
                    <List dense>
                      <ListItem>
                        <ListItemText 
                          primary="Document Type" 
                          secondary={selectedScan.document_type?.charAt(0).toUpperCase() + selectedScan.document_type?.slice(1).replace('_', ' ')}
                        />
                      </ListItem>
                      <ListItem>
                        <ListItemText 
                          primary="Nationality" 
                          secondary={selectedScan.nationality || 'Unknown'}
                        />
                      </ListItem>
                      <ListItem>
                        <ListItemText 
                          primary="Scan Date" 
                          secondary={new Date(selectedScan.timestamp).toLocaleString()}
                        />
                      </ListItem>
                    </List>
                  )}
                </Grid>
                
                {/* Extracted Information */}
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle1" color="primary" gutterBottom sx={{ fontSize: { xs: '0.9rem', sm: '1rem', md: '1.1rem' } }}>
                    Extracted Information
                  </Typography>
                  {editMode ? (
                    <Box sx={{ mt: { xs: 1, sm: 2 } }}>
                      <TextField
                        label="Full Name"
                        value={editedScan.extracted_info?.full_name || ''}
                        onChange={(e) => handleEditFieldChange('extracted_info.full_name', e.target.value)}
                        fullWidth
                        margin="dense"
                        size="small"
                        sx={{ 
                          mb: { xs: 1, sm: 1.5 },
                          '& .MuiInputLabel-root': { fontSize: { xs: '0.8rem', sm: '0.875rem' } },
                          '& .MuiInputBase-input': { fontSize: { xs: '0.8rem', sm: '0.875rem' } }
                        }}
                      />
                      <TextField
                        label="Document Number"
                        value={editedScan.extracted_info?.document_number || ''}
                        onChange={(e) => handleEditFieldChange('extracted_info.document_number', e.target.value)}
                        fullWidth
                        margin="dense"
                        size="small"
                        sx={{ 
                          mb: { xs: 1, sm: 1.5 },
                          '& .MuiInputLabel-root': { fontSize: { xs: '0.8rem', sm: '0.875rem' } },
                          '& .MuiInputBase-input': { fontSize: { xs: '0.8rem', sm: '0.875rem' } }
                        }}
                      />
                      <TextField
                        label="Date of Birth"
                        value={editedScan.extracted_info?.birth_date || ''}
                        onChange={(e) => handleEditFieldChange('extracted_info.birth_date', e.target.value)}
                        fullWidth
                        margin="dense"
                        size="small"
                        sx={{ 
                          mb: { xs: 1, sm: 1.5 },
                          '& .MuiInputLabel-root': { fontSize: { xs: '0.8rem', sm: '0.875rem' } },
                          '& .MuiInputBase-input': { fontSize: { xs: '0.8rem', sm: '0.875rem' } }
                        }}
                      />
                      <TextField
                        label="Expiry Date"
                        value={editedScan.extracted_info?.expiry_date || ''}
                        onChange={(e) => handleEditFieldChange('extracted_info.expiry_date', e.target.value)}
                        fullWidth
                        margin="dense"
                        size="small"
                        sx={{ 
                          mb: { xs: 1, sm: 1.5 },
                          '& .MuiInputLabel-root': { fontSize: { xs: '0.8rem', sm: '0.875rem' } },
                          '& .MuiInputBase-input': { fontSize: { xs: '0.8rem', sm: '0.875rem' } }
                        }}
                      />
                      <TextField
                        label="Place of Issue"
                        value={editedScan.extracted_info?.place_of_issue || ''}
                        onChange={(e) => handleEditFieldChange('extracted_info.place_of_issue', e.target.value)}
                        fullWidth
                        margin="dense"
                        size="small"
                        sx={{ 
                          mb: { xs: 1, sm: 1.5 },
                          '& .MuiInputLabel-root': { fontSize: { xs: '0.8rem', sm: '0.875rem' } },
                          '& .MuiInputBase-input': { fontSize: { xs: '0.8rem', sm: '0.875rem' } }
                        }}
                      />
                      <TextField
                        label="Issue Date"
                        value={editedScan.extracted_info?.issue_date || ''}
                        onChange={(e) => handleEditFieldChange('extracted_info.issue_date', e.target.value)}
                        fullWidth
                        margin="dense"
                        size="small"
                        sx={{ 
                          mb: { xs: 1, sm: 1.5 },
                          '& .MuiInputLabel-root': { fontSize: { xs: '0.8rem', sm: '0.875rem' } },
                          '& .MuiInputBase-input': { fontSize: { xs: '0.8rem', sm: '0.875rem' } }
                        }}
                      />
                      <TextField
                        label="Gender"
                        value={editedScan.extracted_info?.gender || ''}
                        onChange={(e) => handleEditFieldChange('extracted_info.gender', e.target.value)}
                        select
                        fullWidth
                        margin="dense"
                        size="small"
                        sx={{ 
                          '& .MuiInputLabel-root': { fontSize: { xs: '0.8rem', sm: '0.875rem' } },
                          '& .MuiInputBase-input': { fontSize: { xs: '0.8rem', sm: '0.875rem' } },
                          '& .MuiMenuItem-root': { fontSize: { xs: '0.8rem', sm: '0.875rem' } }
                        }}
                      >
                        <MenuItem value="M">Male</MenuItem>
                        <MenuItem value="F">Female</MenuItem>
                        <MenuItem value="X">Other</MenuItem>
                      </TextField>
                    </Box>
                  ) : (
                    <List dense sx={{ 
                      '& .MuiListItemText-primary': { fontSize: { xs: '0.8rem', sm: '0.875rem' } },
                      '& .MuiListItemText-secondary': { fontSize: { xs: '0.75rem', sm: '0.8rem' } },
                      '& .MuiSvgIcon-root': { fontSize: { xs: '1rem', sm: '1.25rem' } }
                    }}>
                      {selectedScan.extracted_info?.full_name && (
                        <ListItem>
                          <PersonIcon fontSize="small" sx={{ mr: 1, color: 'text.secondary' }} />
                          <ListItemText 
                            primary="Full Name" 
                            secondary={selectedScan.extracted_info.full_name}
                          />
                        </ListItem>
                      )}
                      {selectedScan.extracted_info?.document_number && (
                        <ListItem>
                          <FingerprintIcon fontSize="small" sx={{ mr: 1, color: 'text.secondary' }} />
                          <ListItemText 
                            primary="Document Number" 
                            secondary={selectedScan.extracted_info.document_number}
                          />
                        </ListItem>
                      )}
                      {selectedScan.extracted_info?.birth_date && (
                        <ListItem>
                          <CalendarTodayIcon fontSize="small" sx={{ mr: 1, color: 'text.secondary' }} />
                          <ListItemText 
                            primary="Date of Birth" 
                            secondary={selectedScan.extracted_info.birth_date}
                          />
                        </ListItem>
                      )}
                      {selectedScan.extracted_info?.expiry_date && (
                        <ListItem>
                          <CalendarTodayIcon fontSize="small" sx={{ mr: 1, color: 'text.secondary' }} />
                          <ListItemText 
                            primary="Expiry Date" 
                            secondary={selectedScan.extracted_info.expiry_date}
                          />
                        </ListItem>
                      )}
                      {selectedScan.extracted_info?.place_of_issue && (
                        <ListItem>
                          <LocationOnIcon fontSize="small" sx={{ mr: 1, color: 'text.secondary' }} />
                          <ListItemText 
                            primary="Place of Issue" 
                            secondary={selectedScan.extracted_info.place_of_issue}
                          />
                        </ListItem>
                      )}
                      {selectedScan.extracted_info?.issue_date && (
                        <ListItem>
                          <CalendarTodayIcon fontSize="small" sx={{ mr: 1, color: 'text.secondary' }} />
                          <ListItemText 
                            primary="Issue Date" 
                            secondary={selectedScan.extracted_info.issue_date}
                          />
                        </ListItem>
                      )}
                      {selectedScan.extracted_info?.gender && (
                        <ListItem>
                          <PersonIcon fontSize="small" sx={{ mr: 1, color: 'text.secondary' }} />
                          <ListItemText 
                            primary="Gender" 
                            secondary={selectedScan.extracted_info.gender}
                          />
                        </ListItem>
                      )}
                    </List>
                  )}
                </Grid>
              </Grid>
            )}
            
            {/* Tab Panel 1: Raw Text */}
            {tabValue === 1 && (
              <Box sx={{ px: { xs: 0, sm: 1 } }}>
                <Typography variant="subtitle1" color="primary" gutterBottom sx={{ fontSize: { xs: '0.9rem', sm: '1rem', md: '1.1rem' } }}>
                  Raw Extracted Text
                </Typography>
                {editMode ? (
                  <TextField
                    multiline
                    rows={10}
                    value={editedScan.extracted_text || ''}
                    onChange={(e) => handleEditFieldChange('extracted_text', e.target.value)}
                    fullWidth
                    variant="outlined"
                    sx={{ 
                      '& .MuiInputBase-input': { 
                        fontSize: { xs: '0.75rem', sm: '0.85rem' },
                        fontFamily: 'monospace'
                      }
                    }}
                  />
                ) : (
                  <Paper 
                    elevation={0} 
                    variant="outlined" 
                    sx={{ 
                      p: { xs: 1.5, sm: 2 }, 
                      maxHeight: { xs: 300, sm: 350, md: 400 }, 
                      overflow: 'auto',
                      fontSize: { xs: '0.75rem', sm: '0.85rem', md: '0.9rem' },
                      lineHeight: { xs: 1.4, sm: 1.5 },
                      fontFamily: 'monospace'
                    }}
                  >
                    {selectedScan.extracted_text}
                  </Paper>
                )}
              </Box>
            )}
            
            {/* Tab Panel 2: Image */}
            {tabValue === 2 && selectedScan.image_data && (
              <Box sx={{ textAlign: 'center', px: { xs: 0, sm: 1 } }}>
                <Typography variant="subtitle1" color="primary" gutterBottom sx={{ fontSize: { xs: '0.9rem', sm: '1rem', md: '1.1rem' } }}>
                  Document Image
                </Typography>
                <Box 
                  component="img"
                  src={selectedScan.image_data}
                  alt="Scanned document"
                  sx={{ 
                    maxWidth: '100%', 
                    maxHeight: { xs: 300, sm: 400, md: 500 },
                    boxShadow: 1,
                    border: '1px solid #ddd'
                  }}
                />
              </Box>
            )}
          </>
        )}
      </DialogContent>
      <DialogActions sx={{ px: { xs: 2, sm: 3 }, py: { xs: 1.5, sm: 2 } }}>
        {editMode ? (
          <>
            <Button 
              onClick={handleCancelEdit} 
              color="inherit"
              size={window.innerWidth < 600 ? "small" : "medium"}
              sx={{ 
                fontSize: { xs: '0.75rem', sm: '0.875rem' },
                px: { xs: 1.5, sm: 2 },
                py: { xs: 0.5, sm: 0.75 }
              }}
            >
              Cancel
            </Button>
            <Button 
              onClick={handleSaveEdit} 
              color="primary" 
              variant="contained"
              size={window.innerWidth < 600 ? "small" : "medium"}
              sx={{ 
                fontSize: { xs: '0.75rem', sm: '0.875rem' },
                px: { xs: 1.5, sm: 2 },
                py: { xs: 0.5, sm: 0.75 }
              }}
            >
              Save Changes
            </Button>
          </>
        ) : (
          <Button 
            onClick={handleCloseScanDetails} 
            color="primary"
            size={window.innerWidth < 600 ? "small" : "medium"}
            sx={{ 
              fontSize: { xs: '0.75rem', sm: '0.875rem' },
              px: { xs: 1.5, sm: 2 },
              py: { xs: 0.5, sm: 0.75 }
            }}
          >
            Close
          </Button>
        )}
      </DialogActions>
    </Dialog>
    
    {/* Snackbar for notifications */}
    <Snackbar 
      open={snackbarOpen} 
      autoHideDuration={6000} 
      onClose={() => setSnackbarOpen(false)}
      anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      sx={{ 
        mb: { xs: 1, sm: 2 },
        '& .MuiSnackbarContent-root': {
          minWidth: { xs: '80%', sm: 'auto' },
          maxWidth: { xs: '90%', sm: '80%', md: '60%' }
        }
      }}
    >
      <Alert 
        onClose={() => setSnackbarOpen(false)} 
        severity="success" 
        sx={{ 
          width: '100%',
          '& .MuiAlert-message': { 
            fontSize: { xs: '0.8rem', sm: '0.875rem' } 
          },
          '& .MuiAlert-icon': { 
            fontSize: { xs: '1.2rem', sm: '1.5rem' } 
          }
        }}
      >
        {snackbarMessage}
      </Alert>
    </Snackbar>
    </Box>
  );
};

export default Dashboard;

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API_URL } from '../../config';
import {
  Alert,
  Box,
  Button,
  Container,
  Grid,
  Skeleton,
  Snackbar,
  Tooltip,
  Typography,
  useMediaQuery,
  useTheme,
} from '@mui/material';
import { useScreenSize, getResponsiveTableConfig, getResponsiveSpacing } from '../../utils/responsive';
import RefreshIcon from '@mui/icons-material/Refresh';
import DeleteIcon from '@mui/icons-material/Delete';
import DescriptionIcon from '@mui/icons-material/Description';

import StatsOverview from './StatsOverview';
import DocumentTypeChart from './DocumentTypeChart';
import ProcessingTrendsChart from './ProcessingTrendsChart';
import RecentScansPanel from './RecentScansPanel';
import ScanHistoryTable from './ScanHistoryTable';
import ScanDetailDialog from './ScanDetailDialog';

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

  const theme = useTheme();
  const screenSize = useScreenSize();
  const tableConfig = getResponsiveTableConfig(screenSize);
  const spacing = getResponsiveSpacing(screenSize);
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const isTablet = useMediaQuery(theme.breakpoints.between('sm', 'md'));

  // ── API calls ──────────────────────────────────────────────────────────────

  const fetchDocuments = async () => {
    setDocumentsLoading(true);
    try {
      const response = await axios.get(`${API_URL}/api/v3/scan/history`);
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
      const response = await axios.get(`${API_URL}/api/v3/stats`);
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
      await axios.post(`${API_URL}/api/v3/stats/reset`);
      fetchStats();
    } catch (err) {
      setError('Error resetting statistics: ' + err.message);
    }
  };

  useEffect(() => {
    fetchStats();
    fetchDocuments();
  }, []);

  // ── Derived chart data ─────────────────────────────────────────────────────

  const documentTypeChartData = stats?.document_types
    ? Object.entries(stats.document_types).map(([type, count]) => ({
        name: type.charAt(0).toUpperCase() + type.slice(1).replace('_', ' '),
        value: count,
      }))
    : [];

  const nationalitiesChartData = stats?.nationalities
    ? Object.entries(stats.nationalities).map(([nation, count]) => ({
        name: nation,
        value: count,
      }))
    : [];

  // ── Dialog / edit handlers ─────────────────────────────────────────────────

  const handleOpenScanDetails = (scan) => {
    setSelectedScan(scan);
    setDialogOpen(true);
    setEditMode(false);
    setEditedScan(null);
    setTabValue(0);
  };

  const handleCloseScanDetails = () => {
    setDialogOpen(false);
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
    setEditedScan(JSON.parse(JSON.stringify(selectedScan)));
  };

  const handleCancelEdit = () => {
    setEditMode(false);
    setEditedScan(null);
  };

  const handleSaveEdit = async () => {
    try {
      const updatedHistory = stats.scan_history.map((scan) => {
        if (new Date(scan.timestamp).getTime() === new Date(selectedScan.timestamp).getTime()) {
          return editedScan;
        }
        return scan;
      });

      const updatedStats = { ...stats, scan_history: updatedHistory };
      setStats(updatedStats);
      setSelectedScan(editedScan);
      setEditMode(false);
      setEditedScan(null);
      setSnackbarMessage('Scan details updated successfully');
      setSnackbarOpen(true);
    } catch (err) {
      setSnackbarMessage('Error updating scan details: ' + err.message);
      setSnackbarOpen(true);
    }
  };

  const handleEditFieldChange = (field, value) => {
    setEditedScan((prev) => {
      if (field.includes('.')) {
        const [parent, child] = field.split('.');
        return { ...prev, [parent]: { ...prev[parent], [child]: value } };
      }
      return { ...prev, [field]: value };
    });
  };

  // ── Print / export helpers ─────────────────────────────────────────────────

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
            ${scanData.extracted_info?.full_name ? `<div class="field"><span class="field-name">Full Name:</span><span class="field-value">${scanData.extracted_info.full_name}</span></div>` : ''}
            ${scanData.extracted_info?.document_number ? `<div class="field"><span class="field-name">Document Number:</span><span class="field-value">${scanData.extracted_info.document_number}</span></div>` : ''}
            ${scanData.extracted_info?.birth_date ? `<div class="field"><span class="field-name">Date of Birth:</span><span class="field-value">${scanData.extracted_info.birth_date}</span></div>` : ''}
            ${scanData.extracted_info?.expiry_date ? `<div class="field"><span class="field-name">Expiry Date:</span><span class="field-value">${scanData.extracted_info.expiry_date}</span></div>` : ''}
            ${scanData.extracted_info?.place_of_issue ? `<div class="field"><span class="field-name">Place of Issue:</span><span class="field-value">${scanData.extracted_info.place_of_issue}</span></div>` : ''}
            ${scanData.extracted_info?.issue_date ? `<div class="field"><span class="field-name">Issue Date:</span><span class="field-value">${scanData.extracted_info.issue_date}</span></div>` : ''}
            ${scanData.extracted_info?.gender ? `<div class="field"><span class="field-name">Gender:</span><span class="field-value">${scanData.extracted_info.gender}</span></div>` : ''}
          </div>
          ${scanData.extracted_text ? `<div class="section"><h2 class="section-title">Raw Extracted Text</h2><pre style="white-space: pre-wrap; background: #f5f5f5; padding: 10px; border-radius: 5px;">${scanData.extracted_text}</pre></div>` : ''}
          <div class="footer">
            <p>Generated by OCR Document Scanner on ${new Date().toLocaleString()}</p>
          </div>
        </body>
      </html>
    `);
    printWindow.document.close();
    setTimeout(() => { printWindow.print(); }, 500);
    setSnackbarMessage('Print preview opened');
    setSnackbarOpen(true);
  };

  const handleExportJSON = () => {
    const dataStr = JSON.stringify(selectedScan, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,' + encodeURIComponent(dataStr);
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
    navigator.clipboard
      .writeText(textToCopy)
      .then(() => {
        setSnackbarMessage('Copied scan details to clipboard');
        setSnackbarOpen(true);
        handleMenuClose();
      })
      .catch((err) => {
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
      documentType:
        document.document_type?.charAt(0).toUpperCase() +
        document.document_type?.slice(1).replace('_', ' '),
      fullName: document.full_name || 'N/A',
      documentNumber: document.document_number || 'N/A',
      nationality: document.nationality,
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
              ${tableData
                .map(
                  (row) => `
                <tr>
                  <td>${row.index}</td>
                  <td>${row.timestamp}</td>
                  <td>${row.documentType}</td>
                  <td>${row.fullName}</td>
                  <td class="doc-number">${row.documentNumber}</td>
                  <td>${row.nationality}</td>
                </tr>
              `
                )
                .join('')}
            </tbody>
          </table>
        </body>
      </html>
    `);
    printWindow.document.close();
    setTimeout(() => { printWindow.print(); }, 500);
    setSnackbarMessage('Print preview opened');
    setSnackbarOpen(true);
  };

  // ── Render ─────────────────────────────────────────────────────────────────

  return (
    <Box sx={{ overflow: 'hidden' }}>
      <Container
        maxWidth="lg"
        sx={{
          mt: { xs: 2, sm: 3, md: 4 },
          mb: { xs: 2, sm: 3, md: 4 },
          px: { xs: 1, sm: 2, md: 3 },
        }}
      >
        {/* Header */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Box>
            <Typography
              variant="h4"
              component="div"
              sx={{
                display: 'flex',
                alignItems: 'center',
                fontSize: { xs: '1.5rem', sm: '1.75rem', md: '2rem' },
              }}
            >
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
            {/* Stats Cards */}
            <StatsOverview stats={stats} />

            {/* Charts */}
            <DocumentTypeChart stats={stats} documentTypeChartData={documentTypeChartData} />
            <ProcessingTrendsChart stats={stats} nationalitiesChartData={nationalitiesChartData} />

            {/* Recent Documents */}
            <RecentScansPanel
              documents={documents}
              documentsLoading={documentsLoading}
              error={error}
              onRefresh={fetchDocuments}
              onPrintTable={handlePrintTable}
              onViewDocument={handleOpenScanDetails}
            />

            {/* Scan History */}
            <ScanHistoryTable stats={stats} onViewScan={handleOpenScanDetails} />
          </Grid>
        ) : (
          <Typography variant="body1">No data available</Typography>
        )}
      </Container>

      {/* Scan Detail Dialog */}
      <ScanDetailDialog
        open={dialogOpen}
        selectedScan={selectedScan}
        editMode={editMode}
        editedScan={editedScan}
        tabValue={tabValue}
        menuAnchorEl={menuAnchorEl}
        menuOpen={menuOpen}
        onClose={handleCloseScanDetails}
        onTabChange={handleTabChange}
        onEditClick={handleEditClick}
        onCancelEdit={handleCancelEdit}
        onSaveEdit={handleSaveEdit}
        onEditFieldChange={handleEditFieldChange}
        onPrintScan={handlePrintScan}
        onExportJSON={handleExportJSON}
        onCopyToClipboard={handleCopyToClipboard}
        onMenuOpen={handleMenuOpen}
        onMenuClose={handleMenuClose}
      />

      {/* Snackbar */}
      <Snackbar
        open={snackbarOpen}
        autoHideDuration={6000}
        onClose={() => setSnackbarOpen(false)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
        sx={{
          mb: { xs: 1, sm: 2 },
          '& .MuiSnackbarContent-root': {
            minWidth: { xs: '80%', sm: 'auto' },
            maxWidth: { xs: '90%', sm: '80%', md: '60%' },
          },
        }}
      >
        <Alert
          onClose={() => setSnackbarOpen(false)}
          severity="success"
          sx={{
            width: '100%',
            '& .MuiAlert-message': { fontSize: { xs: '0.8rem', sm: '0.875rem' } },
            '& .MuiAlert-icon': { fontSize: { xs: '1.2rem', sm: '1.5rem' } },
          }}
        >
          {snackbarMessage}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default Dashboard;

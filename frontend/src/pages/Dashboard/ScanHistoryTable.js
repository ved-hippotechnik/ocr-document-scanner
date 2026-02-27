import React from 'react';
import {
  Box,
  Chip,
  Divider,
  Grid,
  IconButton,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tooltip,
  Typography,
} from '@mui/material';
import DownloadIcon from '@mui/icons-material/Download';
import DescriptionIcon from '@mui/icons-material/Description';
import BadgeIcon from '@mui/icons-material/Badge';
import PassportIcon from '@mui/icons-material/ArticleOutlined';
import CreditCardIcon from '@mui/icons-material/CreditCard';
import VisibilityIcon from '@mui/icons-material/Visibility';
import PersonIcon from '@mui/icons-material/Person';
import FingerprintIcon from '@mui/icons-material/Fingerprint';

const getDocumentTypeIcon = (documentType) => {
  if (documentType === 'passport') {
    return <PassportIcon sx={{ fontSize: { xs: '1rem', sm: '1.25rem' }, mr: { xs: 0.5, sm: 1 }, color: 'info.main' }} />;
  }
  if (documentType === 'us_green_card') {
    return <CreditCardIcon sx={{ fontSize: { xs: '1rem', sm: '1.25rem' }, mr: { xs: 0.5, sm: 1 }, color: 'success.main' }} />;
  }
  if (documentType === 'id_card' || documentType === 'ID Card') {
    return <BadgeIcon sx={{ fontSize: { xs: '1rem', sm: '1.25rem' }, mr: { xs: 0.5, sm: 1 }, color: 'success.main' }} />;
  }
  return <DescriptionIcon sx={{ fontSize: { xs: '1rem', sm: '1.25rem' }, mr: { xs: 0.5, sm: 1 }, color: 'warning.main' }} />;
};

const getDocumentTypeLabel = (documentType) => {
  if (documentType === 'id_card') return 'ID Card';
  if (documentType === 'driving_license') return 'Driving License';
  if (documentType === 'us_green_card') return 'US Green Card';
  return documentType.charAt(0).toUpperCase() + documentType.slice(1).replace('_', ' ');
};

const ScanHistoryTable = ({ stats, onViewScan }) => {
  const scanHistory = stats?.scan_history || [];
  const entryCount = scanHistory.length;

  const handleExportCSV = () => {
    const headers = ['Document Type', 'Full Name', 'Document Number', 'Date of Birth', 'Nationality', 'Timestamp'];
    const csvContent = [
      headers.join(','),
      ...scanHistory.map((scan) =>
        [
          scan.document_type,
          scan.extracted_info?.full_name || 'N/A',
          scan.extracted_info?.document_number || 'N/A',
          scan.extracted_info?.birth_date || 'N/A',
          scan.nationality,
          new Date(scan.timestamp).toLocaleString(),
        ].join(',')
      ),
    ].join('\n');

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
  };

  return (
    <Grid item xs={12}>
      <Paper sx={{ p: { xs: 2, sm: 2.5, md: 3 } }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Box>
            <Typography
              variant="h6"
              color="primary"
              sx={{ fontSize: { xs: '1rem', sm: '1.1rem', md: '1.25rem' } }}
            >
              Scan History
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {entryCount} {entryCount === 1 ? 'entry' : 'entries'} in total
            </Typography>
          </Box>
          {entryCount > 0 && (
            <Tooltip title="Export scan history as CSV">
              <IconButton color="primary" size="small" onClick={handleExportCSV}>
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
                <TableCell sx={{ fontWeight: 'bold', p: { xs: 1, sm: 2 }, display: { xs: 'none', sm: 'table-cell' } }}>
                  Timestamp
                </TableCell>
                <TableCell sx={{ fontWeight: 'bold', p: { xs: 1, sm: 2 } }}>Document Type</TableCell>
                <TableCell sx={{ fontWeight: 'bold', p: { xs: 1, sm: 2 }, display: { xs: 'none', lg: 'table-cell' } }}>
                  Full Name
                </TableCell>
                <TableCell sx={{ fontWeight: 'bold', p: { xs: 1, sm: 2 }, display: { xs: 'none', lg: 'table-cell' } }}>
                  Document No.
                </TableCell>
                <TableCell sx={{ fontWeight: 'bold', p: { xs: 1, sm: 2 }, display: { xs: 'none', md: 'table-cell' } }}>
                  Nationality
                </TableCell>
                <TableCell align="center" sx={{ fontWeight: 'bold', p: { xs: 1, sm: 2 } }}>
                  Actions
                </TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {entryCount > 0 ? (
                scanHistory.map((scan, index) => (
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
                          hour12: true,
                        })}
                        {index === 0 && (
                          <Chip
                            label="Latest"
                            color="primary"
                            size="small"
                            sx={{
                              ml: 1,
                              height: { xs: 16, sm: 20 },
                              '& .MuiChip-label': { fontSize: { xs: '0.6rem', sm: '0.7rem' } },
                            }}
                          />
                        )}
                      </Box>
                    </TableCell>
                    <TableCell sx={{ p: { xs: 1, sm: 2 } }}>
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        {getDocumentTypeIcon(scan.document_type)}
                        <Typography variant="body2" sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}>
                          {getDocumentTypeLabel(scan.document_type)}
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
                            whiteSpace: 'nowrap',
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
                            whiteSpace: 'nowrap',
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
                        sx={{
                          height: { xs: 20, sm: 24 },
                          '& .MuiChip-label': {
                            fontSize: { xs: '0.65rem', sm: '0.75rem' },
                            px: { xs: 0.5, sm: 1 },
                          },
                        }}
                      />
                    </TableCell>
                    <TableCell align="center" sx={{ p: { xs: 1, sm: 2 } }}>
                      <Tooltip title="View scan details">
                        <IconButton
                          size="small"
                          color="primary"
                          onClick={() => onViewScan(scan)}
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
  );
};

export default ScanHistoryTable;

import React from 'react';
import { alpha } from '@mui/material/styles';
import {
  Alert,
  Box,
  Button,
  CircularProgress,
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
  useTheme,
} from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import PrintIcon from '@mui/icons-material/Print';
import DescriptionIcon from '@mui/icons-material/Description';
import BadgeIcon from '@mui/icons-material/Badge';
import PassportIcon from '@mui/icons-material/ArticleOutlined';
import CreditCardIcon from '@mui/icons-material/CreditCard';
import VisibilityIcon from '@mui/icons-material/Visibility';
import PersonIcon from '@mui/icons-material/Person';
import FingerprintIcon from '@mui/icons-material/Fingerprint';

const DocumentTypeIcon = ({ documentType, theme }) => {
  if (documentType === 'passport') {
    return (
      <Box
        sx={{
          bgcolor: alpha(theme.palette.primary.main, 0.1),
          borderRadius: '50%',
          p: 0.75,
          mr: 1.5,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <PassportIcon sx={{ fontSize: { xs: '0.9rem', sm: '1.1rem' }, color: 'primary.main' }} />
      </Box>
    );
  }
  if (documentType === 'us_green_card') {
    return (
      <Box
        sx={{
          bgcolor: alpha(theme.palette.success.main, 0.1),
          borderRadius: '50%',
          p: 0.75,
          mr: 1.5,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <CreditCardIcon sx={{ fontSize: { xs: '0.9rem', sm: '1.1rem' }, color: 'success.main' }} />
      </Box>
    );
  }
  if (documentType === 'id_card' || documentType === 'ID Card') {
    return (
      <Box
        sx={{
          bgcolor: alpha(theme.palette.success.main, 0.1),
          borderRadius: '50%',
          p: 0.75,
          mr: 1.5,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <BadgeIcon sx={{ fontSize: { xs: '0.9rem', sm: '1.1rem' }, color: 'success.main' }} />
      </Box>
    );
  }
  return (
    <Box
      sx={{
        bgcolor: alpha(theme.palette.warning.main, 0.1),
        borderRadius: '50%',
        p: 0.75,
        mr: 1.5,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      <DescriptionIcon sx={{ fontSize: { xs: '0.9rem', sm: '1.1rem' }, color: 'warning.main' }} />
    </Box>
  );
};

const headerCellSx = {
  fontWeight: 600,
  p: { xs: 1.5, sm: 2 },
  backgroundColor: 'rgba(255, 255, 255, 0.9)',
  backdropFilter: 'blur(10px)',
  WebkitBackdropFilter: 'blur(10px)',
  color: 'text.primary',
  borderBottom: '1px solid rgba(0, 0, 0, 0.1)',
  letterSpacing: '-0.3px',
};

const RecentScansPanel = ({ documents, documentsLoading, error, onRefresh, onPrintTable, onViewDocument }) => {
  const theme = useTheme();

  return (
    <Grid item xs={12}>
      <Paper
        elevation={0}
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
              color: 'text.primary',
            }}
          >
            Recent Documents
          </Typography>
          <Box>
            <Button
              startIcon={<RefreshIcon />}
              size="small"
              onClick={onRefresh}
              sx={{
                mr: 1.5,
                color: 'primary.main',
                borderRadius: '12px',
                px: 2,
                py: 0.75,
                textTransform: 'none',
                fontWeight: 500,
                '&:hover': {
                  backgroundColor: alpha(theme.palette.primary.main, 0.1),
                },
              }}
            >
              Refresh
            </Button>
            <Button
              startIcon={<PrintIcon />}
              size="small"
              onClick={onPrintTable}
              disabled={documents.length === 0}
              sx={{
                bgcolor: 'primary.main',
                color: 'primary.contrastText',
                borderRadius: '12px',
                px: 2,
                py: 0.75,
                textTransform: 'none',
                fontWeight: 500,
                border: 'none',
                '&:hover': {
                  bgcolor: alpha(theme.palette.primary.main, 0.9),
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
            <CircularProgress size={40} sx={{ color: 'primary.main', mb: 2 }} />
            <Typography variant="body2" sx={{ color: 'text.secondary', fontWeight: 500 }}>
              Loading documents...
            </Typography>
          </Box>
        ) : error ? (
          <Alert
            severity="error"
            sx={{
              mb: 2,
              borderRadius: 2,
              bgcolor: alpha(theme.palette.error.main, 0.1),
              color: 'error.main',
              '& .MuiAlert-icon': { color: 'error.main' },
            }}
          >
            {error}
            <Button
              size="small"
              onClick={onRefresh}
              sx={{
                ml: 2,
                color: 'error.main',
                fontWeight: 500,
                '&:hover': { bgcolor: alpha(theme.palette.error.main, 0.1) },
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
              bgcolor: alpha(theme.palette.primary.main, 0.1),
              color: 'primary.main',
              '& .MuiAlert-icon': { color: 'primary.main' },
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
              '&::-webkit-scrollbar': { width: '8px', height: '8px' },
              '&::-webkit-scrollbar-track': {
                backgroundColor: 'rgba(0, 0, 0, 0.05)',
                borderRadius: '10px',
              },
              '&::-webkit-scrollbar-thumb': {
                backgroundColor: 'rgba(0, 0, 0, 0.15)',
                borderRadius: '10px',
                '&:hover': { backgroundColor: 'rgba(0, 0, 0, 0.25)' },
              },
            }}
          >
            <Table stickyHeader size={window.innerWidth < 600 ? 'small' : 'medium'}>
              <TableHead>
                <TableRow>
                  <TableCell sx={headerCellSx}>#</TableCell>
                  <TableCell sx={{ ...headerCellSx, display: { xs: 'none', sm: 'table-cell' } }}>
                    Timestamp
                  </TableCell>
                  <TableCell sx={headerCellSx}>Document Type</TableCell>
                  <TableCell sx={{ ...headerCellSx, display: { xs: 'none', lg: 'table-cell' } }}>
                    Full Name
                  </TableCell>
                  <TableCell sx={{ ...headerCellSx, display: { xs: 'none', lg: 'table-cell' } }}>
                    Document Number
                  </TableCell>
                  <TableCell sx={{ ...headerCellSx, display: { xs: 'none', md: 'table-cell' } }}>
                    Nationality
                  </TableCell>
                  <TableCell align="center" sx={headerCellSx}>Actions</TableCell>
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
                        color: 'text.primary',
                      }}
                    >
                      {index + 1}
                    </TableCell>
                    <TableCell
                      sx={{
                        p: { xs: 1.5, sm: 2 },
                        display: { xs: 'none', sm: 'table-cell' },
                        borderBottom: '1px solid rgba(0, 0, 0, 0.05)',
                        color: 'text.primary',
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
                            hour12: true,
                          })}
                        </Typography>
                        {index === 0 && (
                          <Chip
                            label="Latest"
                            size="small"
                            sx={{
                              ml: 1,
                              height: { xs: 18, sm: 22 },
                              bgcolor: alpha(theme.palette.primary.main, 0.1),
                              color: 'primary.main',
                              fontWeight: 500,
                              border: 'none',
                              borderRadius: '10px',
                              '& .MuiChip-label': {
                                px: 1,
                                fontSize: { xs: '0.6rem', sm: '0.7rem' },
                              },
                            }}
                          />
                        )}
                      </Box>
                    </TableCell>
                    <TableCell
                      sx={{
                        p: { xs: 1.5, sm: 2 },
                        borderBottom: '1px solid rgba(0, 0, 0, 0.05)',
                        color: 'text.primary',
                      }}
                    >
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <DocumentTypeIcon documentType={document.document_type} theme={theme} />
                        <Typography
                          variant="body2"
                          sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' }, fontWeight: 500 }}
                        >
                          {document.document_type.charAt(0).toUpperCase() +
                            document.document_type.slice(1).replace('_', ' ')}
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell
                      sx={{
                        p: { xs: 1.5, sm: 2 },
                        display: { xs: 'none', lg: 'table-cell' },
                        borderBottom: '1px solid rgba(0, 0, 0, 0.05)',
                        color: 'text.primary',
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
                            whiteSpace: 'nowrap',
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
                        color: 'text.primary',
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
                            whiteSpace: 'nowrap',
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
                        color: 'text.primary',
                      }}
                    >
                      <Chip
                        label={document.nationality}
                        size="small"
                        sx={{
                          height: { xs: 22, sm: 26 },
                          bgcolor: 'rgba(0, 0, 0, 0.05)',
                          color: 'text.primary',
                          fontWeight: 500,
                          border: 'none',
                          borderRadius: '12px',
                          '& .MuiChip-label': {
                            fontSize: { xs: '0.65rem', sm: '0.75rem' },
                            px: { xs: 1, sm: 1.5 },
                          },
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
                          onClick={() => onViewDocument(document)}
                          sx={{
                            p: { xs: 0.75, sm: 1 },
                            color: 'primary.main',
                            bgcolor: alpha(theme.palette.primary.main, 0.1),
                            '&:hover': { bgcolor: alpha(theme.palette.primary.main, 0.2) },
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
  );
};

export default RecentScansPanel;

import React, { useState, useEffect, useCallback } from 'react';
import { API_URL } from '../config';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Chip,
  LinearProgress,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Button,
  Divider,
} from '@mui/material';
import {
  CheckCircle,
  Error as ErrorIcon,
  Warning,
  Storage,
  Memory,
  Speed,
  Engineering,
  People,
  Description,
  Refresh,
  AdminPanelSettings,
} from '@mui/icons-material';
import Skeleton from '@mui/material/Skeleton';

const StatusChip = ({ ok, label }) => (
  <Chip
    size="small"
    icon={ok ? <CheckCircle /> : <ErrorIcon />}
    label={label || (ok ? 'Healthy' : 'Down')}
    color={ok ? 'success' : 'error'}
    variant="outlined"
  />
);

const AdminDashboard = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [health, setHealth] = useState(null);
  const [stats, setStats] = useState(null);
  const [aiStatus, setAiStatus] = useState(null);

  const fetchAll = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [healthRes, statsRes, aiRes] = await Promise.allSettled([
        fetch(`${API_URL}/api/v3/health`).then((r) => r.json()),
        fetch(`${API_URL}/api/v3/stats`).then((r) => r.json()),
        fetch(`${API_URL}/api/ai/model/status`).then((r) => r.json()),
      ]);
      if (healthRes.status === 'fulfilled') setHealth(healthRes.value);
      if (statsRes.status === 'fulfilled') setStats(statsRes.value);
      if (aiRes.status === 'fulfilled') setAiStatus(aiRes.value);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAll();
    const interval = setInterval(fetchAll, 30000); // auto-refresh every 30s
    return () => clearInterval(interval);
  }, [fetchAll]);

  if (loading && !health) {
    return (
      <Box sx={{ p: 3 }}>
        <Skeleton variant="text" width={300} height={48} sx={{ mb: 1 }} />
        <Skeleton variant="text" width={400} height={24} sx={{ mb: 3 }} />
        <Grid container spacing={2} sx={{ mb: 3 }}>
          {[0, 1, 2, 3].map((i) => (
            <Grid item xs={12} sm={6} md={3} key={i}>
              <Skeleton variant="rectangular" height={100} sx={{ borderRadius: 3 }} />
            </Grid>
          ))}
        </Grid>
        <Skeleton variant="rectangular" height={120} sx={{ mb: 3, borderRadius: 3 }} />
        <Skeleton variant="rectangular" height={200} sx={{ borderRadius: 3 }} />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Box>
          <Typography variant="h4" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <AdminPanelSettings /> Admin Dashboard
          </Typography>
          <Typography variant="subtitle1" color="text.secondary">
            System health, service status, and scan volume overview
          </Typography>
        </Box>
        <Button
          variant="outlined"
          startIcon={<Refresh />}
          onClick={fetchAll}
          disabled={loading}
        >
          Refresh
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {/* System Health */}
      <Typography variant="h6" sx={{ mb: 1 }}>
        System Health
      </Typography>
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Storage color="primary" />
                <Typography variant="subtitle2">Database</Typography>
              </Box>
              <StatusChip ok={health?.components?.database !== false} />
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Memory color="primary" />
                <Typography variant="subtitle2">Cache</Typography>
              </Box>
              <StatusChip ok={health?.components?.cache !== false} />
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Speed color="primary" />
                <Typography variant="subtitle2">OCR Engine</Typography>
              </Box>
              <StatusChip ok={health?.components?.ocr !== false} />
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Engineering color="primary" />
                <Typography variant="subtitle2">Celery</Typography>
              </Box>
              <StatusChip ok={health?.components?.celery !== false} />
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* AI / Vision Status */}
      <Typography variant="h6" sx={{ mb: 1 }}>
        AI & Vision Status
      </Typography>
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2}>
            <Grid item xs={4}>
              <Typography variant="body2" color="text.secondary">
                Vision Available
              </Typography>
              <StatusChip
                ok={aiStatus?.vision_available}
                label={aiStatus?.vision_available ? 'Active' : 'Disabled'}
              />
            </Grid>
            <Grid item xs={4}>
              <Typography variant="body2" color="text.secondary">
                ML Classifier
              </Typography>
              <StatusChip
                ok={aiStatus?.ml_fitted}
                label={aiStatus?.ml_fitted ? 'Trained' : 'Not trained'}
              />
            </Grid>
            <Grid item xs={4}>
              <Typography variant="body2" color="text.secondary">
                Classifier Chain
              </Typography>
              <Typography variant="body1">
                {aiStatus?.classifier_chain?.join(' → ') || 'N/A'}
              </Typography>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Scan Volume */}
      <Typography variant="h6" sx={{ mb: 1 }}>
        Scan Volume
      </Typography>
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Description color="primary" />
                <Typography variant="subtitle2">Total Scans</Typography>
              </Box>
              <Typography variant="h4">
                {stats?.total_scanned || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={9}>
          <Card>
            <CardContent>
              <Typography variant="subtitle2" gutterBottom>
                Scans by Document Type
              </Typography>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Document Type</TableCell>
                      <TableCell align="right">Count</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {stats?.document_types &&
                      Object.entries(stats.document_types)
                        .filter(([, count]) => count > 0)
                        .sort(([, a], [, b]) => b - a)
                        .map(([type, count]) => (
                          <TableRow key={type}>
                            <TableCell>{type.replace(/_/g, ' ')}</TableCell>
                            <TableCell align="right">{count}</TableCell>
                          </TableRow>
                        ))}
                    {(!stats?.document_types ||
                      Object.values(stats.document_types).every(
                        (v) => v === 0
                      )) && (
                      <TableRow>
                        <TableCell colSpan={2} align="center">
                          No scans recorded yet
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Nationalities */}
      {stats?.nationalities && Object.keys(stats.nationalities).length > 0 && (
        <>
          <Typography variant="h6" sx={{ mb: 1 }}>
            Nationalities Processed
          </Typography>
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {Object.entries(stats.nationalities)
                  .sort(([, a], [, b]) => b - a)
                  .map(([nat, count]) => (
                    <Chip
                      key={nat}
                      label={`${nat}: ${count}`}
                      variant="outlined"
                      size="small"
                    />
                  ))}
              </Box>
            </CardContent>
          </Card>
        </>
      )}
    </Box>
  );
};

export default AdminDashboard;

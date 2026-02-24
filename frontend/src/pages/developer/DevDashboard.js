import React, { useEffect, useState } from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Grid from '@mui/material/Grid';
import Paper from '@mui/material/Paper';
import Skeleton from '@mui/material/Skeleton';
import VpnKeyIcon from '@mui/icons-material/VpnKey';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import { useDeveloperApi } from '../../hooks/useDeveloperApi';

function StatCard({ icon, label, value, color = 'primary.main' }) {
  return (
    <Paper sx={{ p: 2.5, display: 'flex', alignItems: 'center', gap: 2 }}>
      <Box sx={{ color, display: 'flex' }}>{icon}</Box>
      <Box>
        <Typography variant="body2" color="text.secondary">{label}</Typography>
        <Typography variant="h5" fontWeight={600}>{value}</Typography>
      </Box>
    </Paper>
  );
}

export default function DevDashboard() {
  const { getUsage, listKeys, loading } = useDeveloperApi();
  const [summary, setSummary] = useState(null);
  const [keyCount, setKeyCount] = useState(0);

  useEffect(() => {
    getUsage(30).then((d) => setSummary(d.summary)).catch(() => {});
    listKeys().then((d) => setKeyCount(d.keys?.length || 0)).catch(() => {});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (loading && !summary) {
    return (
      <Box>
        <Typography variant="h5" fontWeight={600} gutterBottom>Developer Overview</Typography>
        <Grid container spacing={2}>
          {[1, 2, 3, 4].map((i) => (
            <Grid item xs={12} sm={6} md={3} key={i}><Skeleton variant="rounded" height={90} /></Grid>
          ))}
        </Grid>
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h5" fontWeight={600} gutterBottom>Developer Overview</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Manage your API keys, monitor usage, and configure webhooks.
      </Typography>

      <Grid container spacing={2}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard icon={<VpnKeyIcon />} label="Active Keys" value={summary?.active_keys ?? keyCount} />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard icon={<TrendingUpIcon />} label="Total Requests (30d)" value={summary?.total_requests ?? 0} color="secondary.main" />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard icon={<ErrorOutlineIcon />} label="Errors (30d)" value={summary?.total_errors ?? 0} color="error.main" />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard icon={<CheckCircleIcon />} label="Success Rate" value={`${summary?.success_rate ?? 100}%`} color="success.main" />
        </Grid>
      </Grid>

      <Paper sx={{ p: 3, mt: 3 }}>
        <Typography variant="h6" fontWeight={600} gutterBottom>Quick Start</Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
          1. Create an API key from the <strong>API Keys</strong> page.
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
          2. Use the key in the <code>X-API-Key</code> header of your requests.
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
          3. Optionally configure <strong>Webhooks</strong> to receive async results.
        </Typography>
        <Typography variant="body2" color="text.secondary">
          4. Monitor usage on the <strong>Usage</strong> page.
        </Typography>
      </Paper>
    </Box>
  );
}

import React, { useEffect, useState } from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Paper from '@mui/material/Paper';
import ToggleButton from '@mui/material/ToggleButton';
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup';
import Skeleton from '@mui/material/Skeleton';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line } from 'recharts';
import { useDeveloperApi } from '../../hooks/useDeveloperApi';

export default function UsageDashboard() {
  const { getUsage, loading } = useDeveloperApi();
  const [usage, setUsage] = useState([]);
  const [summary, setSummary] = useState(null);
  const [days, setDays] = useState(30);

  useEffect(() => {
    getUsage(days)
      .then((d) => {
        setUsage(d.usage || []);
        setSummary(d.summary || null);
      })
      .catch(() => {});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [days]);

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h5" fontWeight={600}>API Usage</Typography>
        <ToggleButtonGroup size="small" value={days} exclusive
          onChange={(_, v) => v && setDays(v)}>
          <ToggleButton value={7}>7d</ToggleButton>
          <ToggleButton value={30}>30d</ToggleButton>
          <ToggleButton value={90}>90d</ToggleButton>
        </ToggleButtonGroup>
      </Box>

      {loading && !summary ? (
        <Skeleton variant="rounded" height={300} />
      ) : (
        <>
          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography variant="subtitle1" fontWeight={600} gutterBottom>Requests Over Time</Typography>
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={usage}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" tickFormatter={(d) => new Date(d).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })} />
                <YAxis />
                <Tooltip />
                <Bar dataKey="requests" fill="#007AFF" radius={[4, 4, 0, 0]} />
                <Bar dataKey="errors" fill="#FF3B30" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </Paper>

          <Paper sx={{ p: 3 }}>
            <Typography variant="subtitle1" fontWeight={600} gutterBottom>Success Rate</Typography>
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={usage.map((d) => ({
                ...d,
                rate: d.requests > 0 ? Math.round((1 - d.errors / d.requests) * 100) : 100,
              }))}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" tickFormatter={(d) => new Date(d).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })} />
                <YAxis domain={[0, 100]} unit="%" />
                <Tooltip />
                <Line type="monotone" dataKey="rate" stroke="#34C759" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </Paper>
        </>
      )}
    </Box>
  );
}

import React from 'react';
import { alpha } from '@mui/material/styles';
import {
  Box,
  Chip,
  Divider,
  Grid,
  Paper,
  Typography,
  useTheme,
} from '@mui/material';
import PublicIcon from '@mui/icons-material/Public';
import { CHART_PALETTE_80 } from '../../utils/themeUtils';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
} from 'recharts';

const ProcessingTrendsChart = ({ stats, nationalitiesChartData }) => {
  const theme = useTheme();
  const countryCount = stats?.nationalities ? Object.keys(stats.nationalities).length : 0;
  const totalScanned = stats?.total_scanned || 0;
  const hasData = stats?.nationalities && countryCount > 0;

  return (
    <Grid item xs={12} sm={6} md={6}>
      <Paper
        elevation={0}
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
              color: 'text.primary',
            }}
          >
            Top Nationalities
          </Typography>
          <Chip
            label={`${countryCount} countries`}
            size="small"
            sx={{
              bgcolor: alpha(theme.palette.warning.main, 0.1),
              color: 'warning.main',
              fontWeight: 500,
              border: 'none',
              borderRadius: '12px',
              height: '24px',
              '& .MuiChip-label': {
                px: 1.5,
                fontSize: '0.75rem',
              },
            }}
          />
        </Box>
        <Divider sx={{ mb: 3, opacity: 0.6 }} />
        <Box sx={{ flexGrow: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', width: '100%' }}>
          {hasData ? (
            <ResponsiveContainer width="100%" height={240} role="img" aria-label="Top nationalities bar chart">
              <BarChart
                layout="vertical"
                data={nationalitiesChartData}
                margin={{ top: 4, right: 24, left: 8, bottom: 4 }}
              >
                <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="rgba(0,0,0,0.05)" />
                <XAxis
                  type="number"
                  allowDecimals={false}
                  tick={{ fill: theme.palette.text.secondary, fontSize: 12, fontWeight: 500 }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  type="category"
                  dataKey="name"
                  width={90}
                  tick={{ fill: theme.palette.text.secondary, fontSize: 12, fontWeight: 500 }}
                  axisLine={false}
                  tickLine={false}
                />
                <RechartsTooltip
                  formatter={(value) => {
                    const percentage = ((value / (totalScanned || 1)) * 100).toFixed(1);
                    return [`${value} documents (${percentage}%)`];
                  }}
                  cursor={{ fill: alpha(theme.palette.warning.main, 0.05) }}
                />
                <Bar
                  dataKey="value"
                  fill={CHART_PALETTE_80[2]}
                  radius={[0, 6, 6, 0]}
                  maxBarSize={28}
                />
              </BarChart>
            </ResponsiveContainer>
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
  );
};

export default ProcessingTrendsChart;

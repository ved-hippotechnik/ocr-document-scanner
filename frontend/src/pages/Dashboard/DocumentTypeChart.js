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
import DescriptionIcon from '@mui/icons-material/Description';
import { CHART_PALETTE_80 } from '../../utils/themeUtils';
import {
  PieChart,
  Pie,
  Cell,
  Tooltip as RechartsTooltip,
  Legend as RechartsLegend,
  ResponsiveContainer,
} from 'recharts';

const DocumentTypeChart = ({ stats, documentTypeChartData }) => {
  const theme = useTheme();
  const PIE_COLORS = CHART_PALETTE_80;
  const typeCount = stats?.document_types ? Object.keys(stats.document_types).length : 0;
  const totalScanned = stats?.total_scanned || 0;

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
            Document Types
          </Typography>
          <Chip
            label={`${typeCount} types`}
            size="small"
            sx={{
              bgcolor: alpha(theme.palette.primary.main, 0.1),
              color: 'primary.main',
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
          {totalScanned > 0 ? (
            <ResponsiveContainer width="100%" height={240} role="img" aria-label="Document types pie chart">
              <PieChart>
                <Pie
                  data={documentTypeChartData}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(1)}%`}
                  labelLine={true}
                >
                  {documentTypeChartData.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={PIE_COLORS[index % PIE_COLORS.length]}
                    />
                  ))}
                </Pie>
                <RechartsTooltip
                  formatter={(value, name) => {
                    const percentage = ((value / (totalScanned || 1)) * 100).toFixed(1);
                    return [`${value} (${percentage}%)`, name];
                  }}
                />
                <RechartsLegend
                  layout="horizontal"
                  verticalAlign="bottom"
                  align="center"
                  wrapperStyle={{ fontSize: '12px', fontWeight: 500, color: theme.palette.text.primary }}
                />
              </PieChart>
            </ResponsiveContainer>
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
  );
};

export default DocumentTypeChart;

import React from 'react';
import { alpha } from '@mui/material/styles';
import {
  Box,
  Grid,
  Paper,
  Typography,
  useTheme,
} from '@mui/material';
import DescriptionIcon from '@mui/icons-material/Description';
import PublicIcon from '@mui/icons-material/Public';
import BadgeIcon from '@mui/icons-material/Badge';
import PassportIcon from '@mui/icons-material/ArticleOutlined';

const StatCard = ({ title, value, subtitle, color, icon: Icon }) => {
  const theme = useTheme();

  return (
    <Paper
      elevation={0}
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
          color={color}
          gutterBottom
          sx={{
            fontSize: { xs: '1rem', sm: '1.1rem', md: '1.25rem' },
            fontWeight: 600,
            letterSpacing: '-0.5px',
          }}
        >
          {title}
        </Typography>
        <Box
          sx={{
            bgcolor: alpha(theme.palette[color.split('.')[0]]?.main || theme.palette.primary.main, 0.1),
            borderRadius: '50%',
            p: 1,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <Icon sx={{ fontSize: { xs: 24, sm: 28, md: 32 }, color }} />
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
          color: 'text.primary',
        }}
      >
        {value}
      </Typography>
      <Typography
        variant="body2"
        sx={{
          color: 'text.secondary',
          fontWeight: 500,
          mt: 0.5,
        }}
      >
        {subtitle}
      </Typography>
    </Paper>
  );
};

const StatsOverview = ({ stats }) => {
  const totalScanned = stats?.total_scanned || 0;
  const passportCount = stats?.document_types?.passport || 0;
  const idCardCount = stats?.document_types?.id_card || 0;
  const uniqueNationalities = stats?.nationalities ? Object.keys(stats.nationalities).length : 0;

  return (
    <>
      <Grid item xs={12} sm={6} md={3}>
        <StatCard
          title="Total Scanned"
          value={totalScanned}
          subtitle="Documents processed"
          color="primary.main"
          icon={DescriptionIcon}
        />
      </Grid>
      <Grid item xs={12} sm={6} md={3}>
        <StatCard
          title="Passports"
          value={passportCount}
          subtitle={`${((passportCount / (totalScanned || 1)) * 100).toFixed(1)}% of total`}
          color="info.main"
          icon={PassportIcon}
        />
      </Grid>
      <Grid item xs={12} sm={6} md={3}>
        <StatCard
          title="ID Cards"
          value={idCardCount}
          subtitle={`${((idCardCount / (totalScanned || 1)) * 100).toFixed(1)}% of total`}
          color="success.main"
          icon={BadgeIcon}
        />
      </Grid>
      <Grid item xs={12} sm={6} md={3}>
        <StatCard
          title="Countries"
          value={uniqueNationalities}
          subtitle="Unique nationalities"
          color="warning.main"
          icon={PublicIcon}
        />
      </Grid>
    </>
  );
};

export default StatsOverview;

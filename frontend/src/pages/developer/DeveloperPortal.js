import React from 'react';
import { Outlet, Link as RouterLink, useLocation } from 'react-router-dom';
import Box from '@mui/material/Box';
import Drawer from '@mui/material/Drawer';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import Typography from '@mui/material/Typography';
import Divider from '@mui/material/Divider';
import DashboardIcon from '@mui/icons-material/Dashboard';
import VpnKeyIcon from '@mui/icons-material/VpnKey';
import BarChartIcon from '@mui/icons-material/BarChart';
import WebhookIcon from '@mui/icons-material/Webhook';
import DescriptionIcon from '@mui/icons-material/Description';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';

const SIDEBAR_WIDTH = 240;

const NAV_ITEMS = [
  { label: 'Overview', path: '/developer', icon: <DashboardIcon />, exact: true },
  { label: 'API Keys', path: '/developer/keys', icon: <VpnKeyIcon /> },
  { label: 'Usage', path: '/developer/usage', icon: <BarChartIcon /> },
  { label: 'Webhooks', path: '/developer/webhooks', icon: <WebhookIcon /> },
  { label: 'Documentation', path: '/developer/docs', icon: <DescriptionIcon /> },
];

export default function DeveloperPortal() {
  const location = useLocation();
  const theme = useTheme();
  const isDesktop = useMediaQuery(theme.breakpoints.up('md'));

  const isActive = (item) =>
    item.exact ? location.pathname === item.path : location.pathname.startsWith(item.path);

  const sidebar = (
    <Box sx={{ width: SIDEBAR_WIDTH, pt: 2 }}>
      <Typography variant="subtitle2" sx={{ px: 2, pb: 1, color: 'text.secondary', fontWeight: 600 }}>
        Developer Portal
      </Typography>
      <Divider />
      <List>
        {NAV_ITEMS.map((item) => (
          <ListItem key={item.path} disablePadding>
            <ListItemButton
              component={RouterLink}
              to={item.path}
              selected={isActive(item)}
              sx={{ borderRadius: 1, mx: 1, my: 0.25 }}
            >
              <ListItemIcon sx={{ minWidth: 36, color: isActive(item) ? 'primary.main' : 'text.secondary' }}>
                {item.icon}
              </ListItemIcon>
              <ListItemText primary={item.label} primaryTypographyProps={{ fontSize: '0.9rem' }} />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
    </Box>
  );

  return (
    <Box sx={{ display: 'flex', minHeight: 'calc(100vh - 64px)' }}>
      {isDesktop && (
        <Drawer
          variant="permanent"
          sx={{
            width: SIDEBAR_WIDTH,
            flexShrink: 0,
            '& .MuiDrawer-paper': {
              width: SIDEBAR_WIDTH,
              position: 'relative',
              borderRight: '1px solid',
              borderColor: 'divider',
            },
          }}
        >
          {sidebar}
        </Drawer>
      )}
      <Box component="main" sx={{ flexGrow: 1, p: { xs: 2, md: 3 }, maxWidth: 1200 }}>
        <Outlet />
      </Box>
    </Box>
  );
}

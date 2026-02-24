import React, { useState, useEffect } from 'react';
import { Link as RouterLink, useLocation } from 'react-router-dom';
import AppBar from '@mui/material/AppBar';
import Box from '@mui/material/Box';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import IconButton from '@mui/material/IconButton';
import DocumentScannerIcon from '@mui/icons-material/DocumentScanner';
import DashboardIcon from '@mui/icons-material/Dashboard';
import SmartToy from '@mui/icons-material/SmartToy';
import BatchPrediction from '@mui/icons-material/BatchPrediction';
import Analytics from '@mui/icons-material/Analytics';
import CodeIcon from '@mui/icons-material/Code';
import MenuIcon from '@mui/icons-material/Menu';
import CloseIcon from '@mui/icons-material/Close';
import useScrollTrigger from '@mui/material/useScrollTrigger';
import Slide from '@mui/material/Slide';
import Drawer from '@mui/material/Drawer';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import Divider from '@mui/material/Divider';
import useMediaQuery from '@mui/material/useMediaQuery';
import { styled, useTheme } from '@mui/material/styles';
import { useScreenSize } from '../utils/responsive';

// Apple-style navigation button
const AppleNavButton = styled(Button)(({ theme, active }) => ({
  borderRadius: 20,
  padding: '6px 16px',
  margin: '0 6px',
  color: active ? theme.palette.primary.main : theme.palette.text.primary,
  backgroundColor: active ? 'rgba(0, 122, 255, 0.1)' : 'transparent',
  '&:hover': {
    backgroundColor: active ? 'rgba(0, 122, 255, 0.15)' : 'rgba(0, 0, 0, 0.04)',
  },
  fontWeight: 500,
  fontSize: '0.9rem',
  transition: 'all 0.2s',
}));

// Hide app bar on scroll down
function HideOnScroll(props) {
  const { children } = props;
  const trigger = useScrollTrigger();

  return (
    <Slide appear={false} direction="down" in={!trigger}>
      {children}
    </Slide>
  );
}

const Navbar = () => {
  const location = useLocation();
  const [scrolled, setScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const theme = useTheme();
  const screenSize = useScreenSize();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  // Add scroll listener to apply blur effect
  useEffect(() => {
    const handleScroll = () => {
      const isScrolled = window.scrollY > 10;
      if (isScrolled !== scrolled) {
        setScrolled(isScrolled);
      }
    };

    window.addEventListener('scroll', handleScroll);
    return () => {
      window.removeEventListener('scroll', handleScroll);
    };
  }, [scrolled]);

  return (
    <>
    <HideOnScroll>
      <AppBar
        position="sticky"
        elevation={0}
        className="apple-navbar"
        sx={{
          backgroundColor: scrolled ? 'rgba(255, 255, 255, 0.8)' : 'rgba(255, 255, 255, 0.98)',
          backdropFilter: 'blur(10px)',
          WebkitBackdropFilter: 'blur(10px)',
          borderBottom: '1px solid rgba(0, 0, 0, 0.1)',
          transition: 'all 0.3s ease',
        }}
      >
        <Toolbar sx={{ display: 'flex', justifyContent: 'space-between' }}>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <IconButton
              edge="start"
              component={RouterLink}
              to="/"
              aria-label="Go to home"
              sx={{
                color: '#007AFF',
                mr: 1.5,
                p: { xs: 1, sm: 1.5 },
                '&:hover': {
                  backgroundColor: 'rgba(0, 122, 255, 0.1)',
                },
              }}
            >
              <DocumentScannerIcon sx={{ fontSize: { xs: 20, sm: 24, md: 28 } }} />
            </IconButton>
            <Typography 
              variant="h6" 
              component="div" 
              sx={{ 
                fontWeight: 600,
                letterSpacing: '-0.5px',
                fontSize: { xs: '1.1rem', sm: '1.25rem' },
                color: '#000',
              }}
            >
              Document Scanner
            </Typography>
          </Box>
          
          {/* Desktop Navigation */}
          <Box sx={{ display: { xs: 'none', md: 'flex' } }}>
            <AppleNavButton
              component={RouterLink}
              to="/"
              active={location.pathname === '/' ? 1 : 0}
              startIcon={<DashboardIcon sx={{ fontSize: { xs: 16, sm: 18, md: 20 } }} />}
              sx={{ fontSize: { xs: '0.8rem', sm: '0.9rem' } }}
            >
              Dashboard
            </AppleNavButton>
            <AppleNavButton
              component={RouterLink}
              to="/scanner"
              active={location.pathname === '/scanner' ? 1 : 0}
              startIcon={<DocumentScannerIcon sx={{ fontSize: { xs: 16, sm: 18, md: 20 } }} />}
              sx={{ fontSize: { xs: '0.8rem', sm: '0.9rem' } }}
            >
              Scanner
            </AppleNavButton>
            <AppleNavButton
              component={RouterLink}
              to="/ai-scanner"
              active={location.pathname === '/ai-scanner' ? 1 : 0}
              startIcon={<SmartToy sx={{ fontSize: { xs: 16, sm: 18, md: 20 } }} />}
              sx={{ fontSize: { xs: '0.8rem', sm: '0.9rem' } }}
            >
              AI Scanner
            </AppleNavButton>
            <AppleNavButton
              component={RouterLink}
              to="/batch-processor"
              active={location.pathname === '/batch-processor' ? 1 : 0}
              startIcon={<BatchPrediction sx={{ fontSize: { xs: 16, sm: 18, md: 20 } }} />}
              sx={{ fontSize: { xs: '0.8rem', sm: '0.9rem' } }}
            >
              Batch
            </AppleNavButton>
            <AppleNavButton
              component={RouterLink}
              to="/ai-dashboard"
              active={location.pathname === '/ai-dashboard' ? 1 : 0}
              startIcon={<Analytics sx={{ fontSize: { xs: 16, sm: 18, md: 20 } }} />}
              sx={{ fontSize: { xs: '0.8rem', sm: '0.9rem' } }}
            >
              AI Analytics
            </AppleNavButton>
            <AppleNavButton
              component={RouterLink}
              to="/developer"
              active={location.pathname.startsWith('/developer') ? 1 : 0}
              startIcon={<CodeIcon sx={{ fontSize: { xs: 16, sm: 18, md: 20 } }} />}
              sx={{ fontSize: { xs: '0.8rem', sm: '0.9rem' } }}
            >
              Developer
            </AppleNavButton>
            <AppleNavButton
              component={RouterLink}
              to="/admin"
              active={location.pathname === '/admin' ? 1 : 0}
              startIcon={<DashboardIcon sx={{ fontSize: { xs: 16, sm: 18, md: 20 } }} />}
              sx={{ fontSize: { xs: '0.8rem', sm: '0.9rem' } }}
            >
              Admin
            </AppleNavButton>
          </Box>
          
          {/* Mobile Menu Button */}
          <IconButton
            sx={{ display: { xs: 'block', md: 'none' } }}
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            color="inherit"
            aria-label={mobileMenuOpen ? 'Close navigation menu' : 'Open navigation menu'}
            aria-expanded={mobileMenuOpen}
          >
            {mobileMenuOpen ? <CloseIcon /> : <MenuIcon />}
          </IconButton>
        </Toolbar>
      </AppBar>
    </HideOnScroll>

      {/* Mobile Drawer */}
      <Drawer
        anchor="right"
        open={mobileMenuOpen && isMobile}
        onClose={() => setMobileMenuOpen(false)}
        sx={{
          '& .MuiDrawer-paper': {
            width: { xs: '85%', sm: 320 },
            maxWidth: 320,
            backgroundColor: 'background.paper',
          },
        }}
      >
        <Box sx={{ p: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
            <Typography variant="h6" fontWeight={600}>
              Navigation
            </Typography>
            <IconButton onClick={() => setMobileMenuOpen(false)} aria-label="Close navigation menu">
              <CloseIcon />
            </IconButton>
          </Box>
          <Divider />
          <List>
            <ListItem disablePadding>
              <ListItemButton
                component={RouterLink}
                to="/"
                selected={location.pathname === '/'}
                onClick={() => setMobileMenuOpen(false)}
              >
                <ListItemIcon>
                  <DashboardIcon color={location.pathname === '/' ? 'primary' : 'inherit'} />
                </ListItemIcon>
                <ListItemText primary="Dashboard" />
              </ListItemButton>
            </ListItem>
            <ListItem disablePadding>
              <ListItemButton
                component={RouterLink}
                to="/scanner"
                selected={location.pathname === '/scanner'}
                onClick={() => setMobileMenuOpen(false)}
              >
                <ListItemIcon>
                  <DocumentScannerIcon color={location.pathname === '/scanner' ? 'primary' : 'inherit'} />
                </ListItemIcon>
                <ListItemText primary="Scanner" />
              </ListItemButton>
            </ListItem>
            <ListItem disablePadding>
              <ListItemButton
                component={RouterLink}
                to="/ai-scanner"
                selected={location.pathname === '/ai-scanner'}
                onClick={() => setMobileMenuOpen(false)}
              >
                <ListItemIcon>
                  <SmartToy color={location.pathname === '/ai-scanner' ? 'primary' : 'inherit'} />
                </ListItemIcon>
                <ListItemText primary="AI Scanner" />
              </ListItemButton>
            </ListItem>
            <ListItem disablePadding>
              <ListItemButton
                component={RouterLink}
                to="/batch-processor"
                selected={location.pathname === '/batch-processor'}
                onClick={() => setMobileMenuOpen(false)}
              >
                <ListItemIcon>
                  <BatchPrediction color={location.pathname === '/batch-processor' ? 'primary' : 'inherit'} />
                </ListItemIcon>
                <ListItemText primary="Batch Processor" />
              </ListItemButton>
            </ListItem>
            <ListItem disablePadding>
              <ListItemButton
                component={RouterLink}
                to="/ai-dashboard"
                selected={location.pathname === '/ai-dashboard'}
                onClick={() => setMobileMenuOpen(false)}
              >
                <ListItemIcon>
                  <Analytics color={location.pathname === '/ai-dashboard' ? 'primary' : 'inherit'} />
                </ListItemIcon>
                <ListItemText primary="AI Analytics" />
              </ListItemButton>
            </ListItem>
            <ListItem disablePadding>
              <ListItemButton
                component={RouterLink}
                to="/developer"
                selected={location.pathname.startsWith('/developer')}
                onClick={() => setMobileMenuOpen(false)}
              >
                <ListItemIcon>
                  <CodeIcon color={location.pathname.startsWith('/developer') ? 'primary' : 'inherit'} />
                </ListItemIcon>
                <ListItemText primary="Developer" />
              </ListItemButton>
            </ListItem>
            <ListItem disablePadding>
              <ListItemButton
                component={RouterLink}
                to="/admin"
                selected={location.pathname === '/admin'}
                onClick={() => setMobileMenuOpen(false)}
              >
                <ListItemIcon>
                  <DashboardIcon color={location.pathname === '/admin' ? 'primary' : 'inherit'} />
                </ListItemIcon>
                <ListItemText primary="Admin" />
              </ListItemButton>
            </ListItem>
          </List>
        </Box>
      </Drawer>
    </>
  );
};

export default Navbar;

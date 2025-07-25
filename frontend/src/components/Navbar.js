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
import useScrollTrigger from '@mui/material/useScrollTrigger';
import Slide from '@mui/material/Slide';
import { styled } from '@mui/material/styles';

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
          
          <Box sx={{ display: 'flex' }}>
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
          </Box>
        </Toolbar>
      </AppBar>
    </HideOnScroll>
  );
};

export default Navbar;

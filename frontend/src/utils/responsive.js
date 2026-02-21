// Responsive design utilities and breakpoints
import { useTheme } from '@mui/material/styles';
import { useMediaQuery } from '@mui/material';

// Custom breakpoints for OCR Scanner application
export const breakpoints = {
  xs: 0,     // Mobile devices
  sm: 600,   // Small tablets
  md: 900,   // Tablets
  lg: 1200,  // Desktop
  xl: 1536   // Large desktop
};

// Hook to detect current screen size
export const useScreenSize = () => {
  const theme = useTheme();
  
  return {
    isMobile: useMediaQuery(theme.breakpoints.down('sm')),
    isTablet: useMediaQuery(theme.breakpoints.between('sm', 'md')),
    isDesktop: useMediaQuery(theme.breakpoints.up('md')),
    isLargeDesktop: useMediaQuery(theme.breakpoints.up('lg')),
    
    // More specific queries
    isSmallScreen: useMediaQuery(theme.breakpoints.down('md')),
    isMediumScreen: useMediaQuery(theme.breakpoints.between('md', 'lg')),
    isLargeScreen: useMediaQuery(theme.breakpoints.up('lg')),
    
    // Orientation
    isPortrait: useMediaQuery('(orientation: portrait)'),
    isLandscape: useMediaQuery('(orientation: landscape)')
  };
};

// Responsive spacing utility
export const getResponsiveSpacing = (screenSize) => {
  if (screenSize.isMobile) {
    return {
      padding: 2,
      margin: 1,
      gap: 1
    };
  } else if (screenSize.isTablet) {
    return {
      padding: 3,
      margin: 2,
      gap: 2
    };
  } else {
    return {
      padding: 4,
      margin: 3,
      gap: 3
    };
  }
};

// Responsive grid columns
export const getResponsiveColumns = (screenSize) => {
  if (screenSize.isMobile) return 1;
  if (screenSize.isTablet) return 2;
  if (screenSize.isDesktop) return 3;
  return 4;
};

// Responsive font sizes
export const getResponsiveFontSize = (variant, screenSize) => {
  const fontSizes = {
    h1: {
      mobile: '1.75rem',
      tablet: '2.25rem',
      desktop: '2.5rem'
    },
    h2: {
      mobile: '1.5rem',
      tablet: '1.875rem',
      desktop: '2rem'
    },
    h3: {
      mobile: '1.25rem',
      tablet: '1.5rem',
      desktop: '1.75rem'
    },
    h4: {
      mobile: '1.125rem',
      tablet: '1.25rem',
      desktop: '1.5rem'
    },
    h5: {
      mobile: '1rem',
      tablet: '1.125rem',
      desktop: '1.25rem'
    },
    h6: {
      mobile: '0.875rem',
      tablet: '1rem',
      desktop: '1.125rem'
    },
    body1: {
      mobile: '0.875rem',
      tablet: '1rem',
      desktop: '1rem'
    },
    body2: {
      mobile: '0.75rem',
      tablet: '0.875rem',
      desktop: '0.875rem'
    }
  };

  if (screenSize.isMobile) return fontSizes[variant]?.mobile || '1rem';
  if (screenSize.isTablet) return fontSizes[variant]?.tablet || '1rem';
  return fontSizes[variant]?.desktop || '1rem';
};

// Responsive component dimensions
export const getResponsiveDimensions = (component, screenSize) => {
  const dimensions = {
    card: {
      mobile: { maxWidth: '100%', minHeight: 200 },
      tablet: { maxWidth: 600, minHeight: 250 },
      desktop: { maxWidth: 800, minHeight: 300 }
    },
    dialog: {
      mobile: { width: '95%', maxWidth: 400 },
      tablet: { width: '80%', maxWidth: 600 },
      desktop: { width: '60%', maxWidth: 800 }
    },
    drawer: {
      mobile: { width: '85%', maxWidth: 320 },
      tablet: { width: 320 },
      desktop: { width: 360 }
    },
    uploadZone: {
      mobile: { height: 150, padding: 2 },
      tablet: { height: 200, padding: 3 },
      desktop: { height: 250, padding: 4 }
    }
  };

  if (screenSize.isMobile) return dimensions[component]?.mobile;
  if (screenSize.isTablet) return dimensions[component]?.tablet;
  return dimensions[component]?.desktop;
};

// Responsive icon sizes
export const getResponsiveIconSize = (size = 'medium', screenSize) => {
  const sizes = {
    small: {
      mobile: 20,
      tablet: 24,
      desktop: 24
    },
    medium: {
      mobile: 24,
      tablet: 32,
      desktop: 40
    },
    large: {
      mobile: 32,
      tablet: 48,
      desktop: 56
    }
  };

  if (screenSize.isMobile) return sizes[size]?.mobile || 24;
  if (screenSize.isTablet) return sizes[size]?.tablet || 32;
  return sizes[size]?.desktop || 40;
};

// Responsive button sizes
export const getResponsiveButtonSize = (screenSize) => {
  if (screenSize.isMobile) return 'small';
  if (screenSize.isTablet) return 'medium';
  return 'large';
};

// Responsive table configuration
export const getResponsiveTableConfig = (screenSize) => {
  if (screenSize.isMobile) {
    return {
      size: 'small',
      padding: 'none',
      stickyHeader: false,
      showPagination: true,
      rowsPerPage: 5
    };
  } else if (screenSize.isTablet) {
    return {
      size: 'small',
      padding: 'normal',
      stickyHeader: true,
      showPagination: true,
      rowsPerPage: 10
    };
  } else {
    return {
      size: 'medium',
      padding: 'normal',
      stickyHeader: true,
      showPagination: true,
      rowsPerPage: 25
    };
  }
};

// Responsive navigation configuration
export const getResponsiveNavConfig = (screenSize) => {
  return {
    showDrawer: screenSize.isMobile || screenSize.isTablet,
    showTabs: screenSize.isDesktop,
    position: screenSize.isMobile ? 'bottom' : 'top',
    variant: screenSize.isMobile ? 'temporary' : 'permanent'
  };
};

// Export all utilities
export default {
  breakpoints,
  useScreenSize,
  getResponsiveSpacing,
  getResponsiveColumns,
  getResponsiveFontSize,
  getResponsiveDimensions,
  getResponsiveIconSize,
  getResponsiveButtonSize,
  getResponsiveTableConfig,
  getResponsiveNavConfig
};
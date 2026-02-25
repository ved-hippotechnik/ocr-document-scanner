import { alpha } from '@mui/material/styles';

// Apple-inspired chart color palette derived from the theme.
// Order: primary, success, warning, info, error
export const CHART_PALETTE = [
  '#007AFF', // theme.palette.primary.main
  '#34C759', // theme.palette.success.main
  '#FF9500', // theme.palette.warning.main
  '#5AC8FA', // theme.palette.info.main
  '#FF3B30', // theme.palette.error.main
];

// Same palette at 80% opacity for filled chart areas (pie slices, etc.)
export const CHART_PALETTE_80 = CHART_PALETTE.map((c) => alpha(c, 0.8));

// Get chart color by index (wraps around)
export const getChartColor = (index, opacity = 1) => {
  const base = CHART_PALETTE[index % CHART_PALETTE.length];
  return opacity < 1 ? alpha(base, opacity) : base;
};

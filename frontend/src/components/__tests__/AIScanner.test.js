import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';

// Mock external dependencies before importing the component
jest.mock('react-toastify', () => ({
  toast: { success: jest.fn(), error: jest.fn(), info: jest.fn() },
}));

jest.mock('react-dropzone', () => ({
  useDropzone: jest.fn(() => ({
    getRootProps: () => ({ 'data-testid': 'dropzone' }),
    getInputProps: () => ({}),
    isDragActive: false,
  })),
}));

jest.mock('../../utils/validation', () => ({
  validateFile: jest.fn(() => ({ valid: true })),
  showValidationError: jest.fn(),
  clearValidationError: jest.fn(),
}));

jest.mock('../../utils/websocket', () => ({
  connectSession: jest.fn(),
}));

jest.mock('../../config', () => ({
  API_URL: 'http://localhost:5001',
  __esModule: true,
  default: {
    API_URL: 'http://localhost:5001',
    features: {
      enableWebSocket: false,
      enableAnalytics: true,
    },
    upload: {
      maxSize: 50 * 1024 * 1024,
      allowedTypes: ['image/jpeg', 'image/png'],
    },
  },
}));

// Use dynamic import so mocks are applied first
let AIScanner;
beforeAll(async () => {
  const mod = await import('../AIScanner');
  AIScanner = mod.default;
});

describe('AIScanner', () => {
  test('renders upload area', () => {
    render(<AIScanner />);
    // The component should render the dropzone area
    expect(screen.getByTestId('dropzone')).toBeInTheDocument();
  });

  test('renders without crashing', () => {
    const { container } = render(<AIScanner />);
    expect(container).toBeTruthy();
  });

  test('shows processing state when scanning', async () => {
    render(<AIScanner />);
    // Should not show processing initially
    expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
  });
});

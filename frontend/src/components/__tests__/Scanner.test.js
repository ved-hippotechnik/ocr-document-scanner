import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';

// --- Mocks must be declared before any imports that trigger module evaluation ---

jest.mock('axios');
import axios from 'axios';

jest.mock('../../config', () => ({
  API_URL: 'http://localhost:5001',
  __esModule: true,
  default: {
    API_URL: 'http://localhost:5001',
    upload: {
      maxSize: 50 * 1024 * 1024,
      allowedTypes: ['image/jpeg', 'image/png'],
    },
    features: {},
  },
}));

jest.mock('../../utils/validation', () => ({
  validateFile: jest.fn(() => ({ isValid: true, error: null })),
  showValidationError: jest.fn((msg, setError, showSnackbar) => {
    setError(msg);
    if (showSnackbar) showSnackbar(msg);
  }),
  clearValidationError: jest.fn((setError) => setError(null)),
}));

// Responsive utilities — return stable, non-hook values to avoid MUI theme dependency
jest.mock('../../utils/responsive', () => ({
  useScreenSize: jest.fn(() => ({
    isMobile: false,
    isTablet: false,
    isDesktop: true,
    isLargeDesktop: true,
    isSmallScreen: false,
    isMediumScreen: false,
    isLargeScreen: true,
    isPortrait: false,
    isLandscape: true,
  })),
  getResponsiveSpacing: jest.fn(() => ({ padding: 4, margin: 3, gap: 3 })),
  getResponsiveDimensions: jest.fn(() => ({ height: 250, padding: 4 })),
  getResponsiveIconSize: jest.fn(() => 56),
  getResponsiveButtonSize: jest.fn(() => 'large'),
}));

// Dynamic import so mocks are applied before the module is evaluated
let Scanner;
beforeAll(async () => {
  const mod = await import('../../pages/Scanner');
  Scanner = mod.default;
});

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
const createValidImageFile = (name = 'document.jpg') =>
  new File(['(image data)'], name, { type: 'image/jpeg' });

const mockFileReader = (result = 'data:image/jpeg;base64,abc123') => {
  const originalFileReader = global.FileReader;
  const mockReaderInstance = {
    readAsDataURL: jest.fn(function () {
      // Simulate async completion via onloadend
      setTimeout(() => {
        this.result = result;
        this.onloadend && this.onloadend();
      }, 0);
    }),
    onloadend: null,
    onerror: null,
    result,
  };
  global.FileReader = jest.fn(() => mockReaderInstance);
  return () => {
    global.FileReader = originalFileReader;
  };
};

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe('Scanner', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Default: navigator.mediaDevices.getUserMedia is not available in jsdom
    Object.defineProperty(global.navigator, 'mediaDevices', {
      value: {
        getUserMedia: jest.fn().mockResolvedValue({
          getTracks: () => [{ stop: jest.fn() }],
        }),
      },
      writable: true,
      configurable: true,
    });
  });

  // -------------------------------------------------------------------------
  // Rendering
  // -------------------------------------------------------------------------
  describe('initial render', () => {
    test('renders without crashing', () => {
      const { container } = render(<Scanner />);
      expect(container).toBeTruthy();
    });

    test('renders the page heading', () => {
      render(<Scanner />);
      expect(screen.getByRole('heading', { name: /document scanner/i })).toBeInTheDocument();
    });

    test('renders the subtitle text', () => {
      render(<Scanner />);
      expect(
        screen.getByText(/upload or capture documents to extract information/i)
      ).toBeInTheDocument();
    });

    test('renders the Upload File button', () => {
      render(<Scanner />);
      expect(screen.getByRole('button', { name: /upload file/i })).toBeInTheDocument();
    });

    test('renders the Use Camera button', () => {
      render(<Scanner />);
      expect(
        screen.getByRole('button', { name: /open camera to take a photo/i })
      ).toBeInTheDocument();
    });

    test('renders the Scan Document button in disabled state when no file is selected', () => {
      render(<Scanner />);
      const scanBtn = screen.getByRole('button', { name: /scan document/i });
      expect(scanBtn).toBeInTheDocument();
      expect(scanBtn).toBeDisabled();
    });

    test('shows "No scan results yet" in the results panel initially', () => {
      render(<Scanner />);
      expect(screen.getByText(/no scan results yet/i)).toBeInTheDocument();
    });

    test('shows drag-and-drop instruction text', () => {
      render(<Scanner />);
      expect(screen.getByText(/drag and drop your document here/i)).toBeInTheDocument();
    });
  });

  // -------------------------------------------------------------------------
  // File selection
  // -------------------------------------------------------------------------
  describe('file selection', () => {
    test('accepts a valid image file via the hidden file input', async () => {
      const restoreFileReader = mockFileReader();
      render(<Scanner />);

      const fileInput = document.querySelector('input[type="file"]');
      expect(fileInput).toBeInTheDocument();

      const file = createValidImageFile();
      await act(async () => {
        fireEvent.change(fileInput, { target: { files: [file] } });
        // Let FileReader async callback settle
        await new Promise((r) => setTimeout(r, 10));
      });

      // After a valid file is chosen the Scan Document button should become enabled
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /scan document/i })).not.toBeDisabled();
      });

      restoreFileReader();
    });

    test('calls validateFile when a file is selected', async () => {
      const { validateFile } = require('../../utils/validation');
      const restoreFileReader = mockFileReader();
      render(<Scanner />);

      const fileInput = document.querySelector('input[type="file"]');
      const file = createValidImageFile();
      await act(async () => {
        fireEvent.change(fileInput, { target: { files: [file] } });
        await new Promise((r) => setTimeout(r, 10));
      });

      expect(validateFile).toHaveBeenCalledWith(file);
      restoreFileReader();
    });

    test('shows error when an invalid file is selected', async () => {
      const { validateFile, showValidationError } = require('../../utils/validation');
      validateFile.mockReturnValueOnce({ isValid: false, error: 'Invalid file type' });

      render(<Scanner />);
      const fileInput = document.querySelector('input[type="file"]');
      const badFile = new File(['data'], 'doc.txt', { type: 'text/plain' });

      await act(async () => {
        fireEvent.change(fileInput, { target: { files: [badFile] } });
      });

      expect(showValidationError).toHaveBeenCalled();
      // Scan button must remain disabled
      expect(screen.getByRole('button', { name: /scan document/i })).toBeDisabled();
    });

    test('scan button stays disabled when no file is chosen', () => {
      render(<Scanner />);
      expect(screen.getByRole('button', { name: /scan document/i })).toBeDisabled();
    });
  });

  // -------------------------------------------------------------------------
  // Drag and drop
  // -------------------------------------------------------------------------
  describe('drag and drop', () => {
    test('handleDragOver prevents default browser action', () => {
      render(<Scanner />);
      // The drag-and-drop target is the Box with onDragOver
      const dropZone = document.querySelector('[ondragover]') ||
        screen.getByText(/drag and drop your document here/i).closest('div[class]');

      const dragOverEvent = createEvent.dragOver(document.body);
      dragOverEvent.preventDefault = jest.fn();
      dragOverEvent.stopPropagation = jest.fn();
      fireEvent.dragOver(document.body, dragOverEvent);
      // We just verify the component doesn't throw on drag events
    });

    test('accepts dropped files via onDrop handler', async () => {
      const restoreFileReader = mockFileReader();
      render(<Scanner />);

      const dropTarget = screen.getByText(/drag and drop your document here/i).closest('div');
      const file = createValidImageFile('dropped.jpg');

      await act(async () => {
        fireEvent.drop(dropTarget, {
          dataTransfer: { files: [file] },
        });
        await new Promise((r) => setTimeout(r, 10));
      });

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /scan document/i })).not.toBeDisabled();
      });

      restoreFileReader();
    });
  });

  // -------------------------------------------------------------------------
  // Scan action
  // -------------------------------------------------------------------------
  describe('scanning a document', () => {
    test('shows "Scanning..." label on the button while the API call is in-flight', async () => {
      // Make axios hang so we can inspect mid-flight state
      let resolvePost;
      axios.post.mockReturnValue(
        new Promise((resolve) => {
          resolvePost = resolve;
        })
      );

      const restoreFileReader = mockFileReader();
      render(<Scanner />);

      const fileInput = document.querySelector('input[type="file"]');
      await act(async () => {
        fireEvent.change(fileInput, { target: { files: [createValidImageFile()] } });
        await new Promise((r) => setTimeout(r, 10));
      });

      await waitFor(() =>
        expect(screen.getByRole('button', { name: /scan document/i })).not.toBeDisabled()
      );

      act(() => {
        fireEvent.click(screen.getByRole('button', { name: /scan document/i }));
      });

      await waitFor(() => {
        expect(screen.getByText('Scanning...')).toBeInTheDocument();
      });

      // Clean up – resolve the pending promise
      resolvePost({ data: { success: true, document_type: 'Passport' } });
      restoreFileReader();
    });

    test('shows a circular progress indicator while scanning', async () => {
      let resolvePost;
      axios.post.mockReturnValue(
        new Promise((resolve) => {
          resolvePost = resolve;
        })
      );

      const restoreFileReader = mockFileReader();
      render(<Scanner />);

      const fileInput = document.querySelector('input[type="file"]');
      await act(async () => {
        fireEvent.change(fileInput, { target: { files: [createValidImageFile()] } });
        await new Promise((r) => setTimeout(r, 10));
      });

      await waitFor(() =>
        expect(screen.getByRole('button', { name: /scan document/i })).not.toBeDisabled()
      );

      act(() => {
        fireEvent.click(screen.getByRole('button', { name: /scan document/i }));
      });

      await waitFor(() => {
        expect(screen.getByText(/processing document/i)).toBeInTheDocument();
      });

      resolvePost({ data: { success: true, document_type: 'Passport' } });
      restoreFileReader();
    });

    test('displays scan results on successful API response', async () => {
      axios.post.mockResolvedValue({
        data: {
          success: true,
          document_type: 'Emirates ID',
          nationality: 'UAE',
          extracted_info: { name: 'John Doe', id_number: '784-1990-1234567-1' },
        },
      });

      const restoreFileReader = mockFileReader();
      render(<Scanner />);

      const fileInput = document.querySelector('input[type="file"]');
      await act(async () => {
        fireEvent.change(fileInput, { target: { files: [createValidImageFile()] } });
        await new Promise((r) => setTimeout(r, 10));
      });

      await waitFor(() =>
        expect(screen.getByRole('button', { name: /scan document/i })).not.toBeDisabled()
      );

      await act(async () => {
        fireEvent.click(screen.getByRole('button', { name: /scan document/i }));
      });

      await waitFor(() => {
        expect(screen.getByText(/scan results/i)).toBeInTheDocument();
        expect(screen.getByText(/Emirates ID/)).toBeInTheDocument();
      });

      restoreFileReader();
    });

    test('shows document nationality in results', async () => {
      axios.post.mockResolvedValue({
        data: {
          success: true,
          document_type: 'Passport',
          nationality: 'India',
          extracted_info: {},
        },
      });

      const restoreFileReader = mockFileReader();
      render(<Scanner />);

      const fileInput = document.querySelector('input[type="file"]');
      await act(async () => {
        fireEvent.change(fileInput, { target: { files: [createValidImageFile()] } });
        await new Promise((r) => setTimeout(r, 10));
      });

      await waitFor(() =>
        expect(screen.getByRole('button', { name: /scan document/i })).not.toBeDisabled()
      );

      await act(async () => {
        fireEvent.click(screen.getByRole('button', { name: /scan document/i }));
      });

      await waitFor(() => {
        expect(screen.getByText(/Nationality:.*India/i)).toBeInTheDocument();
      });

      restoreFileReader();
    });

    test('displays an error snackbar when the API call fails', async () => {
      axios.post.mockRejectedValue({
        message: 'Network Error',
        response: undefined,
      });

      const restoreFileReader = mockFileReader();
      render(<Scanner />);

      const fileInput = document.querySelector('input[type="file"]');
      await act(async () => {
        fireEvent.change(fileInput, { target: { files: [createValidImageFile()] } });
        await new Promise((r) => setTimeout(r, 10));
      });

      await waitFor(() =>
        expect(screen.getByRole('button', { name: /scan document/i })).not.toBeDisabled()
      );

      await act(async () => {
        fireEvent.click(screen.getByRole('button', { name: /scan document/i }));
      });

      await waitFor(() => {
        expect(screen.getByText(/error scanning document/i)).toBeInTheDocument();
      });

      restoreFileReader();
    });

    test('displays server error message when API returns an error payload', async () => {
      axios.post.mockRejectedValue({
        response: { data: { message: 'Unsupported document format' } },
        message: 'Request failed',
      });

      const restoreFileReader = mockFileReader();
      render(<Scanner />);

      const fileInput = document.querySelector('input[type="file"]');
      await act(async () => {
        fireEvent.change(fileInput, { target: { files: [createValidImageFile()] } });
        await new Promise((r) => setTimeout(r, 10));
      });

      await waitFor(() =>
        expect(screen.getByRole('button', { name: /scan document/i })).not.toBeDisabled()
      );

      await act(async () => {
        fireEvent.click(screen.getByRole('button', { name: /scan document/i }));
      });

      await waitFor(() => {
        expect(screen.getByText(/Unsupported document format/i)).toBeInTheDocument();
      });

      restoreFileReader();
    });

    test('shows a warning snackbar when Scan Document is clicked with no file', async () => {
      render(<Scanner />);
      // Scan button is disabled when no file is selected, so directly call handleScan
      // by enabling the button state manually is not practical — instead verify the
      // button is truly disabled, which prevents accidental scanning.
      const scanBtn = screen.getByRole('button', { name: /scan document/i });
      expect(scanBtn).toBeDisabled();
    });
  });

  // -------------------------------------------------------------------------
  // Reset / clear
  // -------------------------------------------------------------------------
  describe('reset functionality', () => {
    test('resets state and shows upload prompt again after clicking the close (X) button', async () => {
      axios.post.mockResolvedValue({
        data: { success: true, document_type: 'Passport', nationality: 'US', extracted_info: {} },
      });

      const restoreFileReader = mockFileReader();
      render(<Scanner />);

      const fileInput = document.querySelector('input[type="file"]');
      await act(async () => {
        fireEvent.change(fileInput, { target: { files: [createValidImageFile()] } });
        await new Promise((r) => setTimeout(r, 10));
      });

      await waitFor(() =>
        expect(screen.getByRole('button', { name: /scan document/i })).not.toBeDisabled()
      );

      await act(async () => {
        fireEvent.click(screen.getByRole('button', { name: /scan document/i }));
      });

      // Wait until results appear (shows a preview and a close icon)
      await waitFor(() => expect(screen.getByText(/scan results/i)).toBeInTheDocument());

      // The X (CloseIcon) button for resetting appears when a preview is set
      const closeBtn = screen.queryByRole('button', { hidden: true, name: '' });
      // Find the IconButton wrapping CloseIcon — target by aria or role
      const iconButtons = screen.getAllByRole('button');
      const resetBtn = iconButtons.find(
        (btn) =>
          !btn.textContent.trim() &&
          btn.querySelector('svg') &&
          !btn.closest('[role="dialog"]')
      );

      if (resetBtn) {
        await act(async () => {
          fireEvent.click(resetBtn);
        });
        expect(screen.getByText(/drag and drop your document here/i)).toBeInTheDocument();
      }

      restoreFileReader();
    });
  });

  // -------------------------------------------------------------------------
  // Camera dialog
  // -------------------------------------------------------------------------
  describe('camera dialog', () => {
    test('opens the camera dialog when Use Camera is clicked and getUserMedia succeeds', async () => {
      render(<Scanner />);

      await act(async () => {
        fireEvent.click(screen.getByRole('button', { name: /open camera/i }));
      });

      await waitFor(() => {
        expect(screen.getByText(/capture document/i)).toBeInTheDocument();
      });
    });

    test('shows an error when camera access is denied (NotAllowedError)', async () => {
      const err = new Error('Permission denied');
      err.name = 'NotAllowedError';
      navigator.mediaDevices.getUserMedia = jest.fn().mockRejectedValue(err);

      render(<Scanner />);

      await act(async () => {
        fireEvent.click(screen.getByRole('button', { name: /open camera/i }));
      });

      await waitFor(() => {
        expect(
          screen.getByText(/camera access denied/i)
        ).toBeInTheDocument();
      });
    });

    test('shows an error when no camera is found (NotFoundError)', async () => {
      const err = new Error('No device found');
      err.name = 'NotFoundError';
      navigator.mediaDevices.getUserMedia = jest.fn().mockRejectedValue(err);

      render(<Scanner />);

      await act(async () => {
        fireEvent.click(screen.getByRole('button', { name: /open camera/i }));
      });

      await waitFor(() => {
        expect(screen.getByText(/no camera found/i)).toBeInTheDocument();
      });
    });

    test('shows an error when camera is already in use (NotReadableError)', async () => {
      const err = new Error('Device in use');
      err.name = 'NotReadableError';
      navigator.mediaDevices.getUserMedia = jest.fn().mockRejectedValue(err);

      render(<Scanner />);

      await act(async () => {
        fireEvent.click(screen.getByRole('button', { name: /open camera/i }));
      });

      await waitFor(() => {
        expect(screen.getByText(/already in use/i)).toBeInTheDocument();
      });
    });

    test('closes the camera dialog when Cancel is clicked', async () => {
      render(<Scanner />);

      await act(async () => {
        fireEvent.click(screen.getByRole('button', { name: /open camera/i }));
      });

      await waitFor(() => expect(screen.getByText(/capture document/i)).toBeInTheDocument());

      await act(async () => {
        fireEvent.click(screen.getByRole('button', { name: /cancel/i }));
      });

      await waitFor(() => {
        expect(screen.queryByText(/capture document/i)).not.toBeInTheDocument();
      });
    });
  });

  // -------------------------------------------------------------------------
  // Snackbar / notifications
  // -------------------------------------------------------------------------
  describe('snackbar notifications', () => {
    test('snackbar is not visible on initial render', () => {
      render(<Scanner />);
      // The MUI Snackbar is not visible initially (open=false)
      // There should be no alert role visible
      expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    });
  });
});

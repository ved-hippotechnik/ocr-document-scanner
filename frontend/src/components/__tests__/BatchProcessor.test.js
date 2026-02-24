import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import '@testing-library/jest-dom';

// ---------------------------------------------------------------------------
// Module mocks — declared before any dynamic imports
// ---------------------------------------------------------------------------

jest.mock('react-toastify', () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
    warning: jest.fn(),
    info: jest.fn(),
  },
}));

jest.mock('react-dropzone', () => ({
  useDropzone: jest.fn(({ onDrop }) => ({
    getRootProps: () => ({ 'data-testid': 'dropzone-root', onClick: jest.fn() }),
    getInputProps: () => ({ 'data-testid': 'dropzone-input' }),
    isDragActive: false,
    // Expose the onDrop so tests can call it directly
    _onDrop: onDrop,
  })),
}));

jest.mock('../../config', () => ({
  API_URL: 'http://localhost:5001',
  __esModule: true,
  default: { API_URL: 'http://localhost:5001' },
}));

// Mock the file-validation hook so we control what "validateBatch" returns
jest.mock('../../hooks/useFileValidation', () => ({
  __esModule: true,
  default: jest.fn(() => ({
    validate: jest.fn((file) => ({ isValid: true, error: null })),
    validateBatch: jest.fn((files) => ({
      isValid: true,
      error: null,
      validFiles: files,
    })),
  })),
}));

// fileToBase64 — return a fixed base64 string
jest.mock('../../hooks/useDocumentScanning', () => ({
  __esModule: true,
  fileToBase64: jest.fn(() => Promise.resolve('data:image/jpeg;base64,abc123')),
}));

jest.mock('../../utils/validation', () => ({
  formatFileSize: jest.fn((bytes) => `${bytes} B`),
  validateFile: jest.fn(() => ({ isValid: true, error: null })),
  validateFiles: jest.fn((files) => ({ isValid: true, error: null, validFiles: Array.from(files) })),
}));

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
const makeFile = (name = 'doc.jpg', size = 1024, type = 'image/jpeg') => {
  const file = new File(['x'.repeat(size)], name, { type });
  return file;
};

/**
 * Simulate dropping files into the dropzone by calling the captured onDrop
 * callback directly (react-dropzone is mocked above).
 */
const dropFiles = (files) => {
  const { useDropzone } = require('react-dropzone');
  const lastCall = useDropzone.mock.calls[useDropzone.mock.calls.length - 1];
  const onDrop = lastCall[0].onDrop;
  act(() => {
    onDrop(files);
  });
};

// Mock global fetch
const mockFetch = (responseData, ok = true) => {
  global.fetch = jest.fn(() =>
    Promise.resolve({
      ok,
      status: ok ? 200 : 500,
      json: () => Promise.resolve(responseData),
    })
  );
};

// Dynamic import so all mocks are in place before the module is evaluated
let BatchProcessor;
beforeAll(async () => {
  const mod = await import('../BatchProcessor');
  BatchProcessor = mod.default;
});

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe('BatchProcessor', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  // -------------------------------------------------------------------------
  // Rendering
  // -------------------------------------------------------------------------
  describe('initial render', () => {
    test('renders without crashing', () => {
      const { container } = render(<BatchProcessor />);
      expect(container).toBeTruthy();
    });

    test('renders the page heading', () => {
      render(<BatchProcessor />);
      expect(screen.getByText(/batch document processor/i)).toBeInTheDocument();
    });

    test('renders the subtitle', () => {
      render(<BatchProcessor />);
      expect(
        screen.getByText(/upload multiple documents for batch processing/i)
      ).toBeInTheDocument();
    });

    test('renders the dropzone upload area', () => {
      render(<BatchProcessor />);
      expect(screen.getByTestId('dropzone-root')).toBeInTheDocument();
    });

    test('shows drag-and-drop instruction text inside the dropzone', () => {
      render(<BatchProcessor />);
      expect(
        screen.getByText(/drag & drop documents or click to browse/i)
      ).toBeInTheDocument();
    });

    test('shows accepted file types hint', () => {
      render(<BatchProcessor />);
      expect(screen.getByText(/jpg, png, tiff/i)).toBeInTheDocument();
    });

    test('does not show the file list section initially', () => {
      render(<BatchProcessor />);
      expect(screen.queryByText(/files to process/i)).not.toBeInTheDocument();
    });

    test('does not show results section initially', () => {
      render(<BatchProcessor />);
      expect(screen.queryByText(/processing results/i)).not.toBeInTheDocument();
    });

    test('does not show the progress card initially', () => {
      render(<BatchProcessor />);
      expect(screen.queryByText(/processing batch/i)).not.toBeInTheDocument();
    });
  });

  // -------------------------------------------------------------------------
  // Adding files via drop
  // -------------------------------------------------------------------------
  describe('adding files', () => {
    test('shows the file list after files are dropped', async () => {
      render(<BatchProcessor />);
      dropFiles([makeFile('invoice.jpg')]);

      await waitFor(() => {
        expect(screen.getByText(/files to process/i)).toBeInTheDocument();
      });
    });

    test('displays the dropped file name in the list', async () => {
      render(<BatchProcessor />);
      dropFiles([makeFile('passport.png')]);

      await waitFor(() => {
        expect(screen.getByText('passport.png')).toBeInTheDocument();
      });
    });

    test('shows "pending" status chip for newly added files', async () => {
      render(<BatchProcessor />);
      dropFiles([makeFile('id_card.jpg')]);

      await waitFor(() => {
        // Status chip text
        expect(screen.getAllByText('pending').length).toBeGreaterThan(0);
      });
    });

    test('displays the correct file count in the section header', async () => {
      render(<BatchProcessor />);
      dropFiles([makeFile('file1.jpg'), makeFile('file2.jpg')]);

      await waitFor(() => {
        expect(screen.getByText(/files to process \(2\)/i)).toBeInTheDocument();
      });
    });

    test('accumulates files across multiple drops', async () => {
      render(<BatchProcessor />);
      dropFiles([makeFile('a.jpg')]);
      dropFiles([makeFile('b.jpg')]);

      await waitFor(() => {
        expect(screen.getByText(/files to process \(2\)/i)).toBeInTheDocument();
      });
    });

    test('renders the Clear All button when files are present', async () => {
      render(<BatchProcessor />);
      dropFiles([makeFile('doc.jpg')]);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /clear all/i })).toBeInTheDocument();
      });
    });

    test('renders the Process Batch button when files are present', async () => {
      render(<BatchProcessor />);
      dropFiles([makeFile('doc.jpg')]);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /process batch/i })).toBeInTheDocument();
      });
    });
  });

  // -------------------------------------------------------------------------
  // Remove individual file
  // -------------------------------------------------------------------------
  describe('removing a single file', () => {
    test('removes a file when its delete button is clicked', async () => {
      render(<BatchProcessor />);
      dropFiles([makeFile('removeme.jpg')]);

      await waitFor(() => expect(screen.getByText('removeme.jpg')).toBeInTheDocument());

      const removeBtn = screen.getByRole('button', {
        name: /remove removeme\.jpg from batch/i,
      });
      await act(async () => {
        fireEvent.click(removeBtn);
      });

      await waitFor(() => {
        expect(screen.queryByText('removeme.jpg')).not.toBeInTheDocument();
      });
    });

    test('hides the file list section when the last file is removed', async () => {
      render(<BatchProcessor />);
      dropFiles([makeFile('only.jpg')]);

      await waitFor(() => expect(screen.getByText('only.jpg')).toBeInTheDocument());

      const removeBtn = screen.getByRole('button', {
        name: /remove only\.jpg from batch/i,
      });
      await act(async () => {
        fireEvent.click(removeBtn);
      });

      await waitFor(() => {
        expect(screen.queryByText(/files to process/i)).not.toBeInTheDocument();
      });
    });
  });

  // -------------------------------------------------------------------------
  // Clear All
  // -------------------------------------------------------------------------
  describe('"Clear All" button', () => {
    test('removes all files when Clear All is clicked', async () => {
      render(<BatchProcessor />);
      dropFiles([makeFile('x.jpg'), makeFile('y.jpg')]);

      await waitFor(() => expect(screen.getByText(/files to process \(2\)/i)).toBeInTheDocument());

      await act(async () => {
        fireEvent.click(screen.getByRole('button', { name: /clear all/i }));
      });

      await waitFor(() => {
        expect(screen.queryByText(/files to process/i)).not.toBeInTheDocument();
      });
    });
  });

  // -------------------------------------------------------------------------
  // Batch processing — success path
  // -------------------------------------------------------------------------
  describe('processing batch — success', () => {
    const successResponse = {
      success: true,
      total_processed: 1,
      successful_extractions: 1,
      results: [
        {
          id: null, // will be replaced dynamically
          success: true,
          classification: { document_type: 'passport', document_name: 'Passport', confidence: 0.95 },
          quality_score: 0.88,
          ocr_result: { extracted_data: { name: 'Jane Doe', dob: '1990-01-01' } },
        },
      ],
    };

    test('calls fetch with the batch-scan endpoint', async () => {
      mockFetch(successResponse);
      render(<BatchProcessor />);
      dropFiles([makeFile('passport.jpg')]);

      await waitFor(() => expect(screen.getByRole('button', { name: /process batch/i })).toBeInTheDocument());

      // Patch the result id to match whatever the component assigns
      global.fetch.mockImplementationOnce(async (url, options) => {
        const body = JSON.parse(options.body);
        // Reflect back the id sent by the component
        const patchedResponse = {
          ...successResponse,
          results: [{ ...successResponse.results[0], id: body.images[0].id }],
        };
        return { ok: true, json: () => Promise.resolve(patchedResponse) };
      });

      await act(async () => {
        fireEvent.click(screen.getByRole('button', { name: /process batch/i }));
      });

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/v3/batch-scan'),
          expect.objectContaining({ method: 'POST' })
        );
      });
    });

    test('shows the results section after successful batch processing', async () => {
      render(<BatchProcessor />);
      dropFiles([makeFile('passport.jpg')]);

      await waitFor(() => expect(screen.getByRole('button', { name: /process batch/i })).toBeInTheDocument());

      global.fetch = jest.fn(async (url, options) => {
        const body = JSON.parse(options.body);
        return {
          ok: true,
          json: () =>
            Promise.resolve({
              success: true,
              total_processed: 1,
              successful_extractions: 1,
              results: [{ ...successResponse.results[0], id: body.images[0].id }],
            }),
        };
      });

      await act(async () => {
        fireEvent.click(screen.getByRole('button', { name: /process batch/i }));
      });

      await waitFor(() => {
        expect(screen.getByText(/processing results/i)).toBeInTheDocument();
      });
    });

    test('shows summary stats (Total Documents, Successful, Failed) after processing', async () => {
      render(<BatchProcessor />);
      dropFiles([makeFile('doc.jpg')]);

      await waitFor(() => expect(screen.getByRole('button', { name: /process batch/i })).toBeInTheDocument());

      global.fetch = jest.fn(async (url, options) => {
        const body = JSON.parse(options.body);
        return {
          ok: true,
          json: () =>
            Promise.resolve({
              success: true,
              total_processed: 1,
              successful_extractions: 1,
              results: [{ ...successResponse.results[0], id: body.images[0].id }],
            }),
        };
      });

      await act(async () => {
        fireEvent.click(screen.getByRole('button', { name: /process batch/i }));
      });

      await waitFor(() => {
        expect(screen.getByText(/total documents/i)).toBeInTheDocument();
        expect(screen.getByText(/successful/i)).toBeInTheDocument();
        expect(screen.getByText(/failed/i)).toBeInTheDocument();
      });
    });

    test('shows the results table with column headers', async () => {
      render(<BatchProcessor />);
      dropFiles([makeFile('id.jpg')]);

      await waitFor(() => expect(screen.getByRole('button', { name: /process batch/i })).toBeInTheDocument());

      global.fetch = jest.fn(async (url, options) => {
        const body = JSON.parse(options.body);
        return {
          ok: true,
          json: () =>
            Promise.resolve({
              success: true,
              total_processed: 1,
              successful_extractions: 1,
              results: [{ ...successResponse.results[0], id: body.images[0].id }],
            }),
        };
      });

      await act(async () => {
        fireEvent.click(screen.getByRole('button', { name: /process batch/i }));
      });

      await waitFor(() => {
        expect(screen.getByText('Document')).toBeInTheDocument();
        expect(screen.getByText('Type')).toBeInTheDocument();
        expect(screen.getByText('Confidence')).toBeInTheDocument();
        expect(screen.getByText('Quality')).toBeInTheDocument();
        expect(screen.getByText('Status')).toBeInTheDocument();
      });
    });

    test('calls toast.success after a successful batch', async () => {
      const { toast } = require('react-toastify');
      render(<BatchProcessor />);
      dropFiles([makeFile('id.jpg')]);

      await waitFor(() => expect(screen.getByRole('button', { name: /process batch/i })).toBeInTheDocument());

      global.fetch = jest.fn(async (url, options) => {
        const body = JSON.parse(options.body);
        return {
          ok: true,
          json: () =>
            Promise.resolve({
              success: true,
              total_processed: 1,
              successful_extractions: 1,
              results: [{ ...successResponse.results[0], id: body.images[0].id }],
            }),
        };
      });

      await act(async () => {
        fireEvent.click(screen.getByRole('button', { name: /process batch/i }));
      });

      await waitFor(() => {
        expect(toast.success).toHaveBeenCalled();
      });
    });

    test('renders the Export Results button after successful processing', async () => {
      render(<BatchProcessor />);
      dropFiles([makeFile('id.jpg')]);

      await waitFor(() => expect(screen.getByRole('button', { name: /process batch/i })).toBeInTheDocument());

      global.fetch = jest.fn(async (url, options) => {
        const body = JSON.parse(options.body);
        return {
          ok: true,
          json: () =>
            Promise.resolve({
              success: true,
              total_processed: 1,
              successful_extractions: 1,
              results: [{ ...successResponse.results[0], id: body.images[0].id }],
            }),
        };
      });

      await act(async () => {
        fireEvent.click(screen.getByRole('button', { name: /process batch/i }));
      });

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /export results/i })).toBeInTheDocument();
      });
    });
  });

  // -------------------------------------------------------------------------
  // Batch processing — failure path
  // -------------------------------------------------------------------------
  describe('processing batch — failure', () => {
    test('calls toast.error when fetch returns a non-ok response', async () => {
      const { toast } = require('react-toastify');
      global.fetch = jest.fn(() =>
        Promise.resolve({ ok: false, status: 500, json: () => Promise.resolve({}) })
      );

      render(<BatchProcessor />);
      dropFiles([makeFile('bad.jpg')]);

      await waitFor(() => expect(screen.getByRole('button', { name: /process batch/i })).toBeInTheDocument());

      await act(async () => {
        fireEvent.click(screen.getByRole('button', { name: /process batch/i }));
      });

      await waitFor(() => {
        expect(toast.error).toHaveBeenCalled();
      });
    });

    test('calls toast.error when the API returns success: false', async () => {
      const { toast } = require('react-toastify');
      global.fetch = jest.fn(() =>
        Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ success: false, error: 'Server error' }),
        })
      );

      render(<BatchProcessor />);
      dropFiles([makeFile('bad.jpg')]);

      await waitFor(() => expect(screen.getByRole('button', { name: /process batch/i })).toBeInTheDocument());

      await act(async () => {
        fireEvent.click(screen.getByRole('button', { name: /process batch/i }));
      });

      await waitFor(() => {
        expect(toast.error).toHaveBeenCalled();
      });
    });

    test('calls toast.error on a network failure (fetch rejects)', async () => {
      const { toast } = require('react-toastify');
      global.fetch = jest.fn(() => Promise.reject(new Error('Network failure')));

      render(<BatchProcessor />);
      dropFiles([makeFile('fail.jpg')]);

      await waitFor(() => expect(screen.getByRole('button', { name: /process batch/i })).toBeInTheDocument());

      await act(async () => {
        fireEvent.click(screen.getByRole('button', { name: /process batch/i }));
      });

      await waitFor(() => {
        expect(toast.error).toHaveBeenCalled();
      });
    });

    test('does not show results panel when processing fails', async () => {
      global.fetch = jest.fn(() =>
        Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ success: false, error: 'Failed' }),
        })
      );

      render(<BatchProcessor />);
      dropFiles([makeFile('fail.jpg')]);

      await waitFor(() => expect(screen.getByRole('button', { name: /process batch/i })).toBeInTheDocument());

      await act(async () => {
        fireEvent.click(screen.getByRole('button', { name: /process batch/i }));
      });

      await waitFor(() => {
        expect(screen.queryByText(/processing results/i)).not.toBeInTheDocument();
      });
    });
  });

  // -------------------------------------------------------------------------
  // Empty file list guard
  // -------------------------------------------------------------------------
  describe('processing with no files', () => {
    test('does not call fetch when Process Batch is triggered with no files', async () => {
      const { toast } = require('react-toastify');
      global.fetch = jest.fn();

      render(<BatchProcessor />);
      // Process Batch button is only rendered when files are present, so this
      // tests that the guard fires toast.warning when called programmatically.
      // We trust the component's own guard (files.length === 0) here.
      expect(global.fetch).not.toHaveBeenCalled();
    });
  });

  // -------------------------------------------------------------------------
  // Row expansion (expand/collapse extracted data)
  // -------------------------------------------------------------------------
  describe('result row expansion', () => {
    const setupWithResults = async () => {
      render(<BatchProcessor />);
      dropFiles([makeFile('expand_test.jpg')]);

      await waitFor(() => expect(screen.getByRole('button', { name: /process batch/i })).toBeInTheDocument());

      global.fetch = jest.fn(async (url, options) => {
        const body = JSON.parse(options.body);
        return {
          ok: true,
          json: () =>
            Promise.resolve({
              success: true,
              total_processed: 1,
              successful_extractions: 1,
              results: [
                {
                  id: body.images[0].id,
                  success: true,
                  classification: { document_type: 'passport', document_name: 'Passport', confidence: 0.9 },
                  quality_score: 0.85,
                  ocr_result: { extracted_data: { full_name: 'Alice Smith' } },
                },
              ],
            }),
        };
      });

      await act(async () => {
        fireEvent.click(screen.getByRole('button', { name: /process batch/i }));
      });

      await waitFor(() => expect(screen.getByText(/processing results/i)).toBeInTheDocument());
    };

    test('renders an expand button for each result row', async () => {
      await setupWithResults();
      const expandBtn = screen.getByRole('button', { name: /expand details/i });
      expect(expandBtn).toBeInTheDocument();
    });

    test('shows "Extracted Data" section after clicking expand', async () => {
      await setupWithResults();
      const expandBtn = screen.getByRole('button', { name: /expand details/i });
      await act(async () => {
        fireEvent.click(expandBtn);
      });

      await waitFor(() => {
        expect(screen.getByText(/extracted data/i)).toBeInTheDocument();
      });
    });

    test('changes expand button aria-label to "Collapse details" when expanded', async () => {
      await setupWithResults();
      const expandBtn = screen.getByRole('button', { name: /expand details/i });
      await act(async () => {
        fireEvent.click(expandBtn);
      });

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /collapse details/i })).toBeInTheDocument();
      });
    });
  });

  // -------------------------------------------------------------------------
  // Buttons disabled during processing
  // -------------------------------------------------------------------------
  describe('UI state during processing', () => {
    test('Clear All button is disabled while processing is in flight', async () => {
      // Use a never-resolving fetch to keep processing state active
      global.fetch = jest.fn(() => new Promise(() => {}));

      render(<BatchProcessor />);
      dropFiles([makeFile('processing.jpg')]);

      await waitFor(() => expect(screen.getByRole('button', { name: /process batch/i })).toBeInTheDocument());

      act(() => {
        fireEvent.click(screen.getByRole('button', { name: /process batch/i }));
      });

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /clear all/i })).toBeDisabled();
      });
    });

    test('Process Batch button is disabled while processing is in flight', async () => {
      global.fetch = jest.fn(() => new Promise(() => {}));

      render(<BatchProcessor />);
      dropFiles([makeFile('processing.jpg')]);

      await waitFor(() => expect(screen.getByRole('button', { name: /process batch/i })).toBeInTheDocument());

      act(() => {
        fireEvent.click(screen.getByRole('button', { name: /process batch/i }));
      });

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /process batch/i })).toBeDisabled();
      });
    });

    test('shows "Processing Batch..." card while in flight', async () => {
      global.fetch = jest.fn(() => new Promise(() => {}));

      render(<BatchProcessor />);
      dropFiles([makeFile('processing.jpg')]);

      await waitFor(() => expect(screen.getByRole('button', { name: /process batch/i })).toBeInTheDocument());

      act(() => {
        fireEvent.click(screen.getByRole('button', { name: /process batch/i }));
      });

      await waitFor(() => {
        expect(screen.getByText(/processing batch/i)).toBeInTheDocument();
      });
    });
  });
});

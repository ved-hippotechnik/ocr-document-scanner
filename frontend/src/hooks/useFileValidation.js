import { useCallback } from 'react';
import { validateFile, validateFiles } from '../utils/validation';
import { toast } from 'react-toastify';

/**
 * Custom hook that wraps the validation utilities with toast notifications.
 * Eliminates the repeated validate-then-toast pattern in Scanner, AIScanner,
 * and BatchProcessor components.
 *
 * Usage:
 *   const { validate, validateBatch } = useFileValidation();
 *
 *   // Single file
 *   const result = validate(file);
 *   if (!result.isValid) return;
 *
 *   // Batch files
 *   const { validFiles } = validateBatch(files, 50);
 */
const useFileValidation = () => {
  /** Validate a single file; toasts on error. */
  const validate = useCallback((file) => {
    const result = validateFile(file);
    if (!result.isValid) {
      toast.error(result.error);
    }
    return result;
  }, []);

  /** Validate multiple files; toasts errors/warnings. Returns { isValid, error, validFiles }. */
  const validateBatch = useCallback((files, maxFiles = 50) => {
    const result = validateFiles(files, maxFiles);
    if (!result.isValid) {
      toast.error(result.error);
    } else if (result.error) {
      // Some files were skipped
      toast.warning(result.error);
    }
    return result;
  }, []);

  return { validate, validateBatch };
};

export default useFileValidation;

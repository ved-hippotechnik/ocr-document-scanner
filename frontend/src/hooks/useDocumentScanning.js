import { useState, useCallback } from 'react';

/**
 * Custom hook for managing document scanning lifecycle.
 * Provides shared state (isProcessing, progress, result, error)
 * and actions (startProcessing, completeProcessing, failProcessing, reset).
 *
 * Usage:
 *   const { isProcessing, progress, result, error, setProgress,
 *           startProcessing, completeProcessing, failProcessing, reset } = useDocumentScanning();
 *
 *   async function handleScan(file) {
 *     startProcessing();
 *     try {
 *       const data = await api.scan(file);
 *       completeProcessing(data);
 *     } catch (err) {
 *       failProcessing(err.message);
 *     }
 *   }
 */
const useDocumentScanning = () => {
  const [isProcessing, setIsProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const startProcessing = useCallback(() => {
    setIsProcessing(true);
    setProgress(0);
    setResult(null);
    setError(null);
  }, []);

  const completeProcessing = useCallback((data) => {
    setResult(data);
    setProgress(100);
    setIsProcessing(false);
  }, []);

  const failProcessing = useCallback((errorMsg) => {
    setError(errorMsg);
    setIsProcessing(false);
  }, []);

  const reset = useCallback(() => {
    setIsProcessing(false);
    setProgress(0);
    setResult(null);
    setError(null);
  }, []);

  return {
    isProcessing,
    progress,
    result,
    error,
    setProgress,
    startProcessing,
    completeProcessing,
    failProcessing,
    reset,
  };
};

/**
 * Convert a File object to a base64 data URL string.
 * Extracted here because AIScanner and BatchProcessor both need it.
 */
export const fileToBase64 = (file) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = () => resolve(reader.result);
    reader.onerror = (err) => reject(err);
  });
};

export default useDocumentScanning;

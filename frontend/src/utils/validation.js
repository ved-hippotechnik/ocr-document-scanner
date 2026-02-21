/**
 * Unified validation utilities for consistent form validation
 */

// File validation constants
export const FILE_VALIDATION = {
  MAX_SIZE: 50 * 1024 * 1024, // 50MB - consistent across all components
  ALLOWED_TYPES: [
    'image/jpeg',
    'image/jpg', 
    'image/png',
    'image/tiff',
    'image/tif',
    'image/bmp',
    'image/gif',
    'image/webp',
    'application/pdf'
  ],
  ALLOWED_EXTENSIONS: ['.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.gif', '.webp', '.pdf']
};

/**
 * Validate uploaded file
 * @param {File} file - The file to validate
 * @returns {Object} - {isValid: boolean, error: string|null}
 */
export const validateFile = (file) => {
  if (!file) {
    return { isValid: false, error: 'No file selected' };
  }

  // Check file size
  if (file.size > FILE_VALIDATION.MAX_SIZE) {
    const sizeMB = Math.round(FILE_VALIDATION.MAX_SIZE / (1024 * 1024));
    return { 
      isValid: false, 
      error: `File size must be less than ${sizeMB}MB. Current file is ${Math.round(file.size / (1024 * 1024))}MB.` 
    };
  }

  // Check file type
  if (!FILE_VALIDATION.ALLOWED_TYPES.includes(file.type)) {
    return { 
      isValid: false, 
      error: `Invalid file type. Supported formats: ${FILE_VALIDATION.ALLOWED_EXTENSIONS.join(', ')}` 
    };
  }

  // Check file extension as fallback
  const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();
  if (!FILE_VALIDATION.ALLOWED_EXTENSIONS.includes(fileExtension)) {
    return { 
      isValid: false, 
      error: `Invalid file extension. Supported formats: ${FILE_VALIDATION.ALLOWED_EXTENSIONS.join(', ')}` 
    };
  }

  // Additional checks
  if (file.size === 0) {
    return { isValid: false, error: 'File appears to be empty' };
  }

  if (file.name.length > 255) {
    return { isValid: false, error: 'Filename is too long (max 255 characters)' };
  }

  return { isValid: true, error: null };
};

/**
 * Validate multiple files for batch processing
 * @param {FileList|File[]} files - Files to validate
 * @param {number} maxFiles - Maximum number of files allowed
 * @returns {Object} - {isValid: boolean, error: string|null, validFiles: File[]}
 */
export const validateFiles = (files, maxFiles = 50) => {
  const fileArray = Array.from(files);
  
  if (fileArray.length === 0) {
    return { isValid: false, error: 'No files selected', validFiles: [] };
  }

  if (fileArray.length > maxFiles) {
    return { 
      isValid: false, 
      error: `Too many files selected. Maximum allowed: ${maxFiles}`, 
      validFiles: [] 
    };
  }

  const validFiles = [];
  const errors = [];

  for (let i = 0; i < fileArray.length; i++) {
    const validation = validateFile(fileArray[i]);
    if (validation.isValid) {
      validFiles.push(fileArray[i]);
    } else {
      errors.push(`${fileArray[i].name}: ${validation.error}`);
    }
  }

  if (errors.length > 0 && validFiles.length === 0) {
    return { 
      isValid: false, 
      error: `All files failed validation:\n${errors.join('\n')}`, 
      validFiles: [] 
    };
  }

  if (errors.length > 0) {
    return {
      isValid: true,
      error: `Some files were skipped:\n${errors.join('\n')}`,
      validFiles
    };
  }

  return { isValid: true, error: null, validFiles };
};

/**
 * Validate confidence threshold input
 * @param {number|string} value - Threshold value to validate
 * @returns {Object} - {isValid: boolean, error: string|null, value: number}
 */
export const validateConfidenceThreshold = (value) => {
  const numValue = typeof value === 'string' ? parseFloat(value) : value;
  
  if (isNaN(numValue)) {
    return { isValid: false, error: 'Confidence threshold must be a number', value: null };
  }

  if (numValue < 0 || numValue > 1) {
    return { 
      isValid: false, 
      error: 'Confidence threshold must be between 0 and 1', 
      value: null 
    };
  }

  return { isValid: true, error: null, value: numValue };
};

/**
 * Validate batch processing job name
 * @param {string} jobName - Job name to validate
 * @returns {Object} - {isValid: boolean, error: string|null}
 */
export const validateJobName = (jobName) => {
  if (!jobName || typeof jobName !== 'string') {
    return { isValid: false, error: 'Job name is required' };
  }

  if (jobName.trim().length < 3) {
    return { isValid: false, error: 'Job name must be at least 3 characters long' };
  }

  if (jobName.length > 100) {
    return { isValid: false, error: 'Job name must be less than 100 characters' };
  }

  // Check for valid characters (alphanumeric, spaces, hyphens, underscores)
  const validPattern = /^[a-zA-Z0-9\s_-]+$/;
  if (!validPattern.test(jobName)) {
    return { 
      isValid: false, 
      error: 'Job name can only contain letters, numbers, spaces, hyphens, and underscores' 
    };
  }

  return { isValid: true, error: null };
};

/**
 * Validate document type selection
 * @param {string} documentType - Document type to validate
 * @returns {Object} - {isValid: boolean, error: string|null}
 */
export const validateDocumentType = (documentType) => {
  const validTypes = [
    'auto',
    'passport',
    'emirates_id',
    'aadhaar_card', 
    'driving_license',
    'us_drivers_license'
  ];

  if (!documentType) {
    return { isValid: false, error: 'Document type is required' };
  }

  if (!validTypes.includes(documentType)) {
    return { 
      isValid: false, 
      error: `Invalid document type. Supported types: ${validTypes.join(', ')}` 
    };
  }

  return { isValid: true, error: null };
};

/**
 * Show validation error with consistent styling
 * @param {string} message - Error message to display
 * @param {Function} setError - State setter for error
 * @param {Function} showSnackbar - Optional snackbar function
 */
export const showValidationError = (message, setError, showSnackbar = null) => {
  setError(message);
  if (showSnackbar) {
    showSnackbar(message, 'error');
  }
};

/**
 * Clear validation errors
 * @param {Function} setError - State setter for error
 */
export const clearValidationError = (setError) => {
  setError(null);
};

/**
 * Format file size for display
 * @param {number} bytes - File size in bytes
 * @returns {string} - Formatted size string
 */
export const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

/**
 * Get file type icon based on extension
 * @param {string} filename - Name of the file
 * @returns {string} - Icon name for Material-UI
 */
export const getFileTypeIcon = (filename) => {
  const extension = filename.split('.').pop()?.toLowerCase();
  
  switch (extension) {
    case 'pdf':
      return 'PictureAsPdf';
    case 'jpg':
    case 'jpeg':
    case 'png':
    case 'gif':
    case 'webp':
    case 'bmp':
      return 'Image';
    case 'tiff':
    case 'tif':
      return 'Scanner';
    default:
      return 'InsertDriveFile';
  }
};

export default {
  validateFile,
  validateFiles,
  validateConfidenceThreshold,
  validateJobName,
  validateDocumentType,
  showValidationError,
  clearValidationError,
  formatFileSize,
  getFileTypeIcon,
  FILE_VALIDATION
};
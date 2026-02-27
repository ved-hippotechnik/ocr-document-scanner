// API Configuration
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001';
const WS_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:5001';

const config = {
  API_URL,
  WS_URL,
  endpoints: {
    // Health checks
    health: `${API_URL}/health`,
    healthReady: `${API_URL}/health/ready`,

    // Scanning endpoints
    scan: `${API_URL}/api/v3/scan`,

    // Processors & system
    processors: `${API_URL}/api/v3/processors`,
    stats: `${API_URL}/api/v3/stats`,
    languages: `${API_URL}/api/v3/languages`,

    // Authentication (no version prefix)
    login: `${API_URL}/api/auth/login`,
    register: `${API_URL}/api/auth/register`,
    refresh: `${API_URL}/api/auth/refresh`,
    profile: `${API_URL}/api/auth/profile`,

    // AI endpoints
    aiClassify: `${API_URL}/api/ai/classify`,
    aiProcessDocument: `${API_URL}/api/ai/process-document`,
    aiGetModels: `${API_URL}/api/ai/models`,
    aiMetrics: `${API_URL}/api/ai/metrics`,
    aiSupportedTypes: `${API_URL}/api/ai/supported-types`,
    aiFeedback: `${API_URL}/api/ai/feedback`,
    aiConfidenceThreshold: `${API_URL}/api/ai/confidence-threshold`,
    aiModelStatus: `${API_URL}/api/ai/model/status`,
    aiVisionClassify: `${API_URL}/api/ai/vision/classify`,
    aiVisionExtract: `${API_URL}/api/ai/vision/extract`,
    aiVisionValidate: `${API_URL}/api/ai/vision/validate`,

    // Analytics
    analyticsDashboard: `${API_URL}/api/v3/analytics/dashboard`,
    analyticsTrends: `${API_URL}/api/v3/analytics/trends`,
    analyticsExport: `${API_URL}/api/v3/analytics/export`,

    // Batch processing
    batchCreate: `${API_URL}/api/v3/batch`,
    batchStatus: `${API_URL}/api/v3/batch`,
    batchCancel: `${API_URL}/api/v3/batch`,

    // Developer portal
    developerKeys: `${API_URL}/api/v3/developer/keys`,
    developerUsage: `${API_URL}/api/v3/developer/usage`,
    developerWebhooks: `${API_URL}/api/v3/developer/webhooks`,
  },
  
  // File upload configuration
  upload: {
    maxSize: 50 * 1024 * 1024, // 50MB
    allowedTypes: ['image/jpeg', 'image/png', 'image/tiff', 'image/bmp', 'application/pdf'],
    allowedExtensions: ['.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.pdf'],
  },
  
  // Request configuration
  request: {
    timeout: 60000, // 60 seconds
    retries: 3,
    headers: {
      'Content-Type': 'application/json',
    },
  },
  
  // WebSocket configuration
  websocket: {
    reconnectInterval: 5000,
    maxReconnectAttempts: 10,
  },
  
  // Feature flags
  features: {
    enableWebSocket: process.env.REACT_APP_ENABLE_WEBSOCKET === 'true',
    enablePWA: process.env.REACT_APP_ENABLE_PWA !== 'false', // Default true
    enableOffline: process.env.REACT_APP_ENABLE_OFFLINE !== 'false', // Default true
    enableAnalytics: process.env.REACT_APP_ENABLE_ANALYTICS !== 'false', // Default true
    enableBatchProcessing: process.env.REACT_APP_ENABLE_BATCH !== 'false', // Default true
  },
};

export default config;
export const { endpoints } = config;
export { API_URL, WS_URL };
import React, { useState } from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Paper from '@mui/material/Paper';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import IconButton from '@mui/material/IconButton';
import Snackbar from '@mui/material/Snackbar';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';

const EXAMPLES = {
  curl: `# Scan a document
curl -X POST \\
  -H "X-API-Key: ocr_live_YOUR_KEY_HERE" \\
  -F "image=@document.jpg" \\
  https://your-domain.com/api/v3/scan

# Scan with document type hint
curl -X POST \\
  -H "X-API-Key: ocr_live_YOUR_KEY_HERE" \\
  -H "Content-Type: application/json" \\
  -d '{"image": "<base64>", "document_type": "passport"}' \\
  https://your-domain.com/api/v3/scan`,

  python: `import requests

API_KEY = "ocr_live_YOUR_KEY_HERE"
BASE_URL = "https://your-domain.com"

# Upload and scan a document
with open("document.jpg", "rb") as f:
    resp = requests.post(
        f"{BASE_URL}/api/v3/scan",
        headers={"X-API-Key": API_KEY},
        files={"image": f},
    )
    result = resp.json()
    print(result["extracted_data"])

# Verify webhook signature
import hmac, hashlib

def verify_signature(payload_bytes, signature, secret):
    expected = hmac.new(
        secret.encode(), payload_bytes, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)`,

  javascript: `const API_KEY = 'ocr_live_YOUR_KEY_HERE';
const BASE_URL = 'https://your-domain.com';

// Scan a document (browser)
async function scanDocument(file) {
  const form = new FormData();
  form.append('image', file);

  const res = await fetch(\`\${BASE_URL}/api/v3/scan\`, {
    method: 'POST',
    headers: { 'X-API-Key': API_KEY },
    body: form,
  });
  return res.json();
}

// Verify webhook signature (Node.js)
const crypto = require('crypto');

function verifySignature(payloadBody, signature, secret) {
  const expected = crypto
    .createHmac('sha256', secret)
    .update(payloadBody)
    .digest('hex');
  return crypto.timingSafeEqual(
    Buffer.from(\`sha256=\${expected}\`),
    Buffer.from(signature),
  );
}`,
};

function CodeBlock({ code, onCopy }) {
  return (
    <Box sx={{ position: 'relative' }}>
      <IconButton size="small" onClick={() => onCopy(code)}
        sx={{ position: 'absolute', top: 8, right: 8, bgcolor: 'background.paper' }}
        aria-label="Copy code">
        <ContentCopyIcon fontSize="small" />
      </IconButton>
      <Box component="pre" sx={{
        bgcolor: '#1e1e1e', color: '#d4d4d4', p: 2, borderRadius: 1,
        overflow: 'auto', fontSize: '0.85rem', lineHeight: 1.6,
      }}>
        <code>{code}</code>
      </Box>
    </Box>
  );
}

export default function Documentation() {
  const [tab, setTab] = useState(0);
  const [snackbar, setSnackbar] = useState(false);
  const langs = ['curl', 'python', 'javascript'];

  const copy = (text) => {
    navigator.clipboard.writeText(text);
    setSnackbar(true);
  };

  return (
    <Box>
      <Typography variant="h4" fontWeight={600} gutterBottom>API Documentation</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Integrate the OCR Document Scanner into your application using the examples below.
      </Typography>

      {/* Authentication */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" fontWeight={600} gutterBottom>Authentication</Typography>
        <Typography variant="body2" sx={{ mb: 1 }}>
          All API requests require an <code>X-API-Key</code> header with your API key:
        </Typography>
        <CodeBlock code={'X-API-Key: ocr_live_YOUR_KEY_HERE'} onCopy={copy} />
      </Paper>

      {/* Rate Limits */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" fontWeight={600} gutterBottom>Rate Limits</Typography>
        <Typography variant="body2">
          Each API key has a configurable rate limit (default 60 req/min). When exceeded, the API returns <code>429 Too Many Requests</code>.
          The <code>Retry-After</code> header indicates when to retry.
        </Typography>
      </Paper>

      {/* Endpoints */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" fontWeight={600} gutterBottom>Core Endpoints</Typography>
        <Box component="table" sx={{ width: '100%', borderCollapse: 'collapse', '& td, & th': { p: 1, textAlign: 'left', borderBottom: '1px solid', borderColor: 'divider' } }}>
          <thead>
            <tr><th>Method</th><th>Endpoint</th><th>Scope</th><th>Description</th></tr>
          </thead>
          <tbody>
            <tr><td><code>POST</code></td><td><code>/api/v3/scan</code></td><td>scan</td><td>Process a single document</td></tr>
            <tr><td><code>POST</code></td><td><code>/api/v3/scan</code></td><td>scan</td><td>Enhanced scan with quality assessment</td></tr>
            <tr><td><code>POST</code></td><td><code>/api/v3/batch</code></td><td>batch</td><td>Create a batch processing job</td></tr>
            <tr><td><code>POST</code></td><td><code>/api/ai/classify</code></td><td>ai</td><td>Classify document type via AI</td></tr>
            <tr><td><code>GET</code></td><td><code>/health</code></td><td>—</td><td>Service health check</td></tr>
          </tbody>
        </Box>
      </Paper>

      {/* Code Examples */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" fontWeight={600} gutterBottom>Code Examples</Typography>
        <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 2 }}>
          <Tab label="cURL" />
          <Tab label="Python" />
          <Tab label="JavaScript" />
        </Tabs>
        <CodeBlock code={EXAMPLES[langs[tab]]} onCopy={copy} />
      </Paper>

      {/* Webhooks */}
      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" fontWeight={600} gutterBottom>Webhook Verification</Typography>
        <Typography variant="body2" sx={{ mb: 1 }}>
          Each webhook delivery includes an <code>X-Webhook-Signature</code> header computed as <code>sha256=HMAC(secret, body)</code>.
          Always verify this signature before processing the payload. See the Python and JavaScript examples above for verification code.
        </Typography>
        <Typography variant="body2">
          Events: <code>scan.complete</code>, <code>scan.error</code>, <code>batch.complete</code>, <code>batch.error</code>
        </Typography>
      </Paper>

      <Snackbar open={snackbar} autoHideDuration={2000} onClose={() => setSnackbar(false)} message="Copied to clipboard" />
    </Box>
  );
}

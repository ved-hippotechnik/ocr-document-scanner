# OCR Document Scanner API Documentation

## Overview

The OCR Document Scanner provides a comprehensive REST API for document scanning, classification, and information extraction. The API supports multiple document types and provides advanced features like quality assessment, confidence scoring, and monitoring.

## Base URL

- **Development**: `http://localhost:5002`
- **Production**: `https://your-domain.com`

## Authentication

Currently, the API does not require authentication. This may be added in future versions.

## Endpoints

### Health Check

#### GET `/health`

Check the health status of the API.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-20T10:30:00Z",
  "version": "1.0.0"
}
```

---

### Document Scanning

#### POST `/api/scan` (Legacy)

Basic document scanning endpoint.

**Request Body:**
```json
{
  "image": "base64_encoded_image_string",
  "document_type": "optional_document_type"
}
```

**Response:**
```json
{
  "success": true,
  "document_type": "aadhaar",
  "confidence": 0.95,
  "extracted_info": {
    "document_number": "1234 5678 9012",
    "full_name": "John Doe",
    "date_of_birth": "01/01/1990",
    "gender": "Male",
    "address": "123 Main St, City, State"
  },
  "processing_time": 2.34
}
```

#### POST `/api/v2/scan` (Enhanced)

Enhanced document scanning with advanced features.

**Request Body:**
```json
{
  "image": "base64_encoded_image_string",
  "document_type": "optional_document_type",
  "options": {
    "enable_quality_check": true,
    "return_processed_images": false,
    "ocr_language": "eng"
  }
}
```

**Response:**
```json
{
  "success": true,
  "document_type": "aadhaar",  
  "confidence": 0.95,
  "quality_score": 0.87,
  "quality_issues": ["low_resolution", "blur"],
  "extracted_info": {
    "document_number": "1234 5678 9012",
    "full_name": "John Doe",
    "date_of_birth": "01/01/1990",
    "gender": "Male",
    "address": "123 Main St, City, State"
  },
  "processor_used": "AadhaarProcessor",
  "processing_time": 2.34,
  "timestamp": "2024-01-20T10:30:00Z"
}
```

---

### Document Classification

#### POST `/api/v2/classify`

Classify a document without full information extraction.

**Request Body:**
```json
{
  "image": "base64_encoded_image_string"
}
```

**Response:**
```json
{
  "success": true,
  "document_type": "passport",
  "confidence": 0.92,
  "country": "India",
  "processor": "PassportProcessor",
  "processing_time": 0.85
}
```

---

### Quality Assessment

#### POST `/api/v2/quality`

Assess the quality of a document image.

**Request Body:**
```json
{
  "image": "base64_encoded_image_string"
}
```

**Response:**
```json
{
  "success": true,
  "quality_score": 0.78,
  "issues": [
    {
      "type": "blur",
      "severity": "medium",
      "description": "Image appears to be slightly blurred"
    },
    {
      "type": "low_resolution",
      "severity": "low", 
      "description": "Image resolution could be higher for better OCR"
    }
  ],
  "recommendations": [
    "Take photo in better lighting",
    "Hold camera steady to avoid blur",
    "Move closer to document for higher resolution"
  ],
  "processing_time": 0.45
}
```

---

### Statistics and Monitoring

#### GET `/api/v2/stats`

Get API usage statistics and performance metrics.

**Response:**
```json
{
  "success": true,
  "stats": {
    "total_requests": 15420,
    "successful_scans": 14892,
    "error_rate": 0.034,
    "average_processing_time": 2.1,
    "document_types": {
      "aadhaar": 6234,
      "passport": 3421,
      "driving_license": 2890,
      "emirates_id": 1347,
      "us_drivers_license": 892,
      "unknown": 236
    },
    "quality_distribution": {
      "high": 0.68,
      "medium": 0.24,
      "low": 0.08
    }
  },
  "timestamp": "2024-01-20T10:30:00Z"
}
```

#### GET `/metrics`

Prometheus metrics endpoint for monitoring.

**Response:** (Prometheus format)
```
# HELP ocr_requests_total Total number of OCR requests
# TYPE ocr_requests_total counter
ocr_requests_total 15420

# HELP ocr_processing_duration_seconds OCR processing duration
# TYPE ocr_processing_duration_seconds histogram
ocr_processing_duration_seconds_bucket{le="1.0"} 3421
ocr_processing_duration_seconds_bucket{le="2.0"} 8932
...
```

---

## Supported Document Types

### 1. Aadhaar Card (India)
- **Document Type**: `aadhaar`
- **Country**: India (`IN`)
- **Extracted Fields**:
  - `document_number`: 12-digit Aadhaar number
  - `full_name`: Full name
  - `date_of_birth`: Date of birth
  - `gender`: Male/Female
  - `address`: Full address
  - `father_name`: Father's name
  - `mobile`: Mobile number (if available)
  - `email`: Email address (if available)

### 2. Emirates ID (UAE)
- **Document Type**: `emirates_id`
- **Country**: UAE (`AE`)
- **Extracted Fields**:
  - `document_number`: 15-digit Emirates ID number
  - `full_name`: Full name (English and Arabic)
  - `nationality`: Nationality
  - `date_of_birth`: Date of birth
  - `gender`: Male/Female
  - `issue_date`: Issue date
  - `expiry_date`: Expiry date

### 3. Indian Driving License
- **Document Type**: `driving_license`
- **Country**: India (`IN`)
- **Extracted Fields**:
  - `document_number`: DL number
  - `full_name`: Full name
  - `father_name`: Father's name
  - `date_of_birth`: Date of birth
  - `address`: Address
  - `issue_date`: Issue date
  - `validity_upto`: Validity date
  - `issuing_authority`: Issuing RTO
  - `class_of_vehicle`: Vehicle class
  - `blood_group`: Blood group

### 4. Indian Passport
- **Document Type**: `passport`
- **Country**: India (`IN`)
- **Extracted Fields**:
  - `document_number`: Passport number
  - `document_type`: Document type (P)
  - `country_code`: Country code (IND)
  - `surname`: Surname
  - `given_name`: Given name
  - `nationality`: Nationality
  - `date_of_birth`: Date of birth
  - `place_of_birth`: Place of birth
  - `sex`: M/F
  - `date_of_issue`: Issue date
  - `date_of_expiry`: Expiry date
  - `place_of_issue`: Place of issue
  - `file_number`: File number

### 5. US Driver's License
- **Document Type**: `drivers_license`
- **Country**: USA (`US`)
- **Extracted Fields**:
  - `document_number`: License number
  - `full_name`: Full name
  - `first_name`: First name
  - `last_name`: Last name
  - `date_of_birth`: Date of birth
  - `address`: Address
  - `city`: City
  - `state`: State
  - `zip_code`: ZIP code
  - `issue_date`: Issue date
  - `expiration_date`: Expiration date
  - `class`: License class
  - `restrictions`: Restrictions
  - `endorsements`: Endorsements
  - `height`: Height
  - `weight`: Weight
  - `sex`: M/F
  - `eyes`: Eye color
  - `hair`: Hair color

---

## Error Handling

### Error Response Format

```json
{
  "success": false,
  "error": {
    "code": "INVALID_IMAGE",
    "message": "The provided image is invalid or corrupted",
    "details": "Unable to decode base64 image data"
  },
  "timestamp": "2024-01-20T10:30:00Z"
}
```

### Common Error Codes

| Code | Description |
|------|-------------|
| `INVALID_IMAGE` | Invalid or corrupted image data |
| `UNSUPPORTED_FORMAT` | Unsupported image format |
| `FILE_TOO_LARGE` | Image file size exceeds limit |
| `PROCESSING_FAILED` | OCR processing failed |
| `DOCUMENT_NOT_DETECTED` | No supported document type detected |
| `LOW_CONFIDENCE` | Extracted information has low confidence |
| `RATE_LIMIT_EXCEEDED` | API rate limit exceeded |
| `INTERNAL_ERROR` | Internal server error |

---

## Rate Limiting

The API implements rate limiting to ensure fair usage:
- **Limit**: 100 requests per minute per IP
- **Headers**: 
  - `X-RateLimit-Limit`: Request limit
  - `X-RateLimit-Remaining`: Remaining requests
  - `X-RateLimit-Reset`: Reset timestamp

---

## Quality Assessment Details

### Quality Scores
- **High (0.8-1.0)**: Excellent image quality, optimal for OCR
- **Medium (0.5-0.79)**: Acceptable quality, may have minor issues
- **Low (0.0-0.49)**: Poor quality, likely to affect OCR accuracy

### Quality Issues
- `blur`: Image is blurred or out of focus
- `low_resolution`: Image resolution is too low
- `poor_lighting`: Inadequate or uneven lighting
- `skew`: Document is tilted or rotated
- `glare`: Reflective glare affects readability
- `noise`: Image has visual noise or artifacts
- `partial_document`: Document is partially cut off
- `low_contrast`: Poor contrast between text and background

---

## Best Practices

### Image Guidelines
1. **Resolution**: Minimum 300 DPI recommended
2. **Format**: JPEG or PNG preferred
3. **Size**: Maximum 10MB per image
4. **Lighting**: Even, natural lighting works best
5. **Angle**: Document should be flat and straight
6. **Background**: Plain, contrasting background
7. **Focus**: Ensure text is sharp and readable

### API Usage
1. **Retry Logic**: Implement exponential backoff for retries
2. **Error Handling**: Always check the `success` field
3. **Validation**: Validate extracted data for your use case
4. **Monitoring**: Monitor API response times and error rates
5. **Caching**: Cache results when appropriate
6. **Security**: Validate and sanitize all inputs

---

## Examples

### cURL Examples

#### Basic Scan
```bash
curl -X POST http://localhost:5002/api/scan \
  -H "Content-Type: application/json" \
  -d '{
    "image": "base64_encoded_image_here"
  }'
```

#### Enhanced Scan with Quality Check
```bash
curl -X POST http://localhost:5002/api/v2/scan \
  -H "Content-Type: application/json" \
  -d '{
    "image": "base64_encoded_image_here",
    "options": {
      "enable_quality_check": true
    }
  }'
```

#### Document Classification
```bash
curl -X POST http://localhost:5002/api/v2/classify \
  -H "Content-Type: application/json" \
  -d '{
    "image": "base64_encoded_image_here"
  }'
```

### Python Example

```python
import requests
import base64

# Read and encode image
with open('document.jpg', 'rb') as f:
    image_data = base64.b64encode(f.read()).decode()

# Make API request
response = requests.post('http://localhost:5002/api/v2/scan', json={
    'image': image_data,
    'options': {
        'enable_quality_check': True
    }
})

result = response.json()
if result['success']:
    print(f"Document Type: {result['document_type']}")
    print(f"Confidence: {result['confidence']}")
    print(f"Quality Score: {result['quality_score']}")
    print("Extracted Info:", result['extracted_info'])
else:
    print(f"Error: {result['error']['message']}")
```

### JavaScript Example

```javascript
async function scanDocument(imageFile) {
    // Convert file to base64
    const base64 = await new Promise((resolve) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result.split(',')[1]);
        reader.readAsDataURL(imageFile);
    });

    // Make API request
    const response = await fetch('http://localhost:5002/api/v2/scan', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            image: base64,
            options: {
                enable_quality_check: true
            }
        }),
    });

    const result = await response.json();
    
    if (result.success) {
        console.log('Document Type:', result.document_type);
        console.log('Confidence:', result.confidence);
        console.log('Extracted Info:', result.extracted_info);
    } else {
        console.error('Error:', result.error.message);
    }
}
```

---

## Changelog

### Version 2.0.0 (Latest)
- Added enhanced `/api/v2/scan` endpoint
- Added document classification endpoint
- Added quality assessment endpoint
- Added statistics and monitoring endpoints
- Improved error handling and response format
- Added support for US Driver's License
- Enhanced document processors with better accuracy

### Version 1.0.0
- Initial release with basic scanning functionality
- Support for Aadhaar, Emirates ID, and basic document types
- Basic OCR and information extraction

---

## Support

For support, issues, or feature requests:
- **GitHub**: [Repository Issues](https://github.com/ved-hippotechnik/ocr-document-scanner/issues)
- **Email**: support@your-domain.com
- **Documentation**: [Full Documentation](https://your-docs-site.com)

---

## License

This API is released under the MIT License. See the LICENSE file for details.

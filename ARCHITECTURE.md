# OCR Document Scanner — Architecture Document

## System Overview

The OCR Document Scanner is a full-stack application that combines traditional OCR (Tesseract) with AI-powered document classification (Claude Vision + RandomForest ML) to extract structured data from identity documents. It supports 14+ document types across 10+ countries.

```
┌─────────────────────────────────────────────────────┐
│              Frontend (React + Material-UI)          │
│                     Port 3000                        │
└───────────────────────┬─────────────────────────────┘
                        │ HTTP / WebSocket
                        ▼
┌─────────────────────────────────────────────────────┐
│              Flask API (Gunicorn)                    │
│              Port 5000 (prod) / 5001 (dev)          │
│                                                     │
│  ┌─────────────┐ ┌──────────┐ ┌──────────────────┐ │
│  │  Security   │→│  Routes  │→│ Business Logic   │ │
│  │  Middleware │ │ (5 files)│ │ (Processors, AI) │ │
│  └─────────────┘ └──────────┘ └────────┬─────────┘ │
│                                         │           │
│  ┌──────────────────────────────────────┘           │
│  │                                                  │
│  ▼                                                  │
│  ┌─────────┐ ┌──────────┐ ┌────────┐ ┌──────────┐ │
│  │ Claude  │ │Tesseract │ │  ML    │ │ Quality  │ │
│  │ Vision  │ │  OCR     │ │Classif.│ │ Analyzer │ │
│  └─────────┘ └──────────┘ └────────┘ └──────────┘ │
└──────┬──────────────────────────┬───────────────────┘
       │                          │
       ▼                          ▼
┌──────────────┐          ┌──────────────┐
│  PostgreSQL  │          │    Redis     │
│  (SQLite dev)│          │ Cache+Broker │
│  Port 5432   │          │  Port 6379   │
└──────────────┘          └──────┬───────┘
                                 │
                    ┌────────────┴────────────┐
                    ▼                         ▼
             ┌────────────┐           ┌────────────┐
             │   Celery   │           │   Celery   │
             │  Workers   │           │    Beat    │
             └────────────┘           └────────────┘
```

---

## 1. Frontend Architecture

**Stack**: React.js, Material-UI v5, Recharts, react-dropzone, react-toastify

| Component | File | Responsibility |
|-----------|------|----------------|
| AIScanner | `frontend/src/components/AIScanner.js` | Primary scanning UI with drag-and-drop, Vision toggle, classifier badges |
| AIDashboard | `frontend/src/components/AIDashboard.js` | Analytics charts and processing metrics |
| BatchProcessor | `frontend/src/components/BatchProcessor.js` | Multi-document batch processing UI |
| AccessibleScanner | `frontend/src/components/AccessibleScanner.js` | WCAG-compliant scanner variant |
| ErrorBoundary | `frontend/src/components/ErrorBoundary.js` | Graceful error handling |
| Navbar | `frontend/src/components/Navbar.js` | Navigation with auth integration |
| OfflineStatus | `frontend/src/components/OfflineStatus.js` | PWA offline indicator |

**Configuration**: `frontend/src/config.js` — centralized API endpoint registry with feature flags for WebSocket, PWA, offline mode, analytics, and batch processing.

**Theme**: Apple-inspired design system — primary blue (#007AFF), system fonts (San Francisco/Helvetica Neue).

---

## 2. API Layer

### Route Organization

| File | URL Prefix | Purpose |
|------|------------|---------|
| `backend/app/routes.py` | `/api` | Core OCR scan, stats, health |
| `backend/app/routes_enhanced.py` | `/api/v2` | Enhanced scan with base64 input |
| `backend/app/routes_improved.py` | `/api/v3` | Improved error handling and validation |
| `backend/app/routes_async.py` | `/api/async` | Celery-backed async processing |
| `backend/app/ai/routes.py` | `/api/ai` | AI classification, Vision, training |
| `backend/app/auth/routes.py` | `/api/auth` | Registration, login, JWT tokens |
| `backend/app/batch/routes.py` | `/api/batch` | Batch job submission and status |
| `backend/app/analytics/routes.py` | `/api/analytics` | Dashboard metrics and trends |

### Key Endpoints

```
POST /api/scan                    # OCR scan (multipart form)
POST /api/v2/scan                 # Enhanced scan (JSON/base64)
POST /api/ai/classify             # Document classification (Vision → ML → rules)
POST /api/ai/vision/classify      # Vision-only classification
POST /api/ai/vision/extract       # Direct Vision field extraction
POST /api/ai/vision/validate      # Validate OCR fields against image
GET  /api/ai/model/status         # Classifier chain status
POST /api/auth/register           # User registration
POST /api/auth/login              # JWT login
GET  /api/analytics/dashboard     # Analytics data
POST /api/batch/submit            # Batch job creation
```

### Security Middleware Pipeline

Every request passes through this chain (defined in `backend/app/security/middleware.py`):

```
Request → IP Validation → Rate Limiting → Size Validation →
Header Validation → JSON Payload Scanning → Route Handler →
Security Headers → Response
```

**Authentication**: JWT (HS256) via `@token_required` decorator. Access tokens expire in 24h, refresh tokens in 30 days. Account lockout after 5 failed login attempts.

---

## 3. Document Processing Pipeline

### Hybrid Classification Chain

```
Image Input
    │
    ├─[1]─→ Claude Vision classify_document()
    │       (zero-shot, no training needed)
    │       confidence > 0.5 → use result
    │
    ├─[2]─→ ML RandomForestClassifier
    │       (100 trees, max_depth=10)
    │       Requires training via /api/ai/train
    │
    └─[3]─→ Rule-based classifier
            (OCR text keyword matching)
            Always available as fallback
```

### OCR + Vision Extraction Pipeline

```
Classified Document
    │
    ▼
Tesseract OCR → Raw Text
    │
    ▼
Document Processor (regex extraction)
    │
    ├── OCR confidence ≥ 0.25
    │   │
    │   ├── validate_with_vision=true?
    │   │   ▼
    │   │   Claude Vision validates extracted fields
    │   │   Corrects OCR errors (O→0, I→1, etc.)
    │   │   Returns corrections + verified fields
    │   │
    │   └── Return extracted info
    │
    └── OCR confidence < 0.25 (auto-fallback)
        │
        ▼
        Claude Vision extract_fields_direct()
        Full VLM extraction, bypasses Tesseract
        │
        ▼
        Merge with any OCR results
```

### Supported Document Types & Processors

| Processor | Document | Country | Key Fields |
|-----------|----------|---------|------------|
| `emirates_id.py` | Emirates ID | UAE | Name, ID#, Nationality, DOB, Expiry |
| `aadhaar.py` | Aadhaar Card | India | Name, Aadhaar#, DOB, Gender, Address |
| `driving_license.py` | Driving License | India | Name, License#, DOB, Vehicle Class |
| `passport.py` | Passport | India | Name, Passport#, Nationality, DOB |
| `us_drivers_license.py` | Driver's License | USA | Name, License#, DOB, State |
| `us_green_card.py` | Green Card | USA | Name, Card#, DOB, Category |
| `pan_card.py` | PAN Card | India | Name, PAN#, Father's Name |
| `voter_id.py` | Voter ID | India | Name, ID#, Address |
| `uk_passport.py` | Passport | UK | Name, Passport#, DOB |
| `canadian_passport.py` | Passport | Canada | Name, Passport#, DOB |
| `australian_passport.py` | Passport | Australia | Name, Passport#, DOB |
| `german_passport.py` | Passport | Germany | Name, Passport#, DOB |
| `eu_id_card.py` | ID Card | EU | Name, ID#, Nationality |
| `japanese_my_number.py` | My Number Card | Japan | Name, Number, Address |

### Processor Base Class

```python
class DocumentProcessor:
    def process(image, text_results=None, language=None, validate_with_vision=False):
        preprocessed = self.preprocess(image)
        text = ocr_engine.extract_text(preprocessed)
        info = self.extract_info(text)
        # Auto-fallback to Vision if confidence < 0.25
        # Vision validation if validate_with_vision=True
        return info

    def preprocess(image) → np.ndarray      # Image enhancement
    def extract_info(text) → Dict            # Regex field extraction
```

---

## 4. AI/ML Components

### Claude Vision Service (`backend/app/ai/vision_service.py`)

```python
class ClaudeVisionService:
    model = "claude-sonnet-4-20250514"
    timeout = 30 seconds

    classify_document(image_bytes) → {
        document_type, document_name, confidence, reasoning, classifier: "vision"
    }

    validate_extracted_fields(image_bytes, extracted_info, doc_type) → {
        verified_fields, corrections: [{field, original, corrected, reason}],
        missing_fields, confidence
    }

    extract_fields_direct(image_bytes, doc_type) → {
        full_name, document_number, date_of_birth, ...,
        processing_method: "vision_extraction"
    }
```

**Document Type Mapping**: 42 aliases map Claude's natural language responses to internal codes (e.g., "Aadhaar Card" → `aadhaar`, "permanent resident card" → `us_green_card`).

### ML Classifier (`backend/app/ai/document_classifier.py`)

- **Algorithm**: scikit-learn RandomForestClassifier (100 trees, max_depth=10)
- **Features**: TF-IDF on OCR text + image metadata
- **Training**: Via `/api/ai/train` or auto-train from scan history
- **Persistence**: `models/document_classifier.pkl` (joblib)

### Quality Analyzer (`backend/app/quality.py`)

Scores document images on brightness, contrast, focus, and alignment (0-100 scale). Used to decide whether to trust OCR output or fall back to Vision.

---

## 5. Data Layer

### Database Models (`backend/app/database.py`)

| Model | Table | Purpose |
|-------|-------|---------|
| User | `users` | Authentication (email, username, password_hash, role) |
| LoginAttempt | `login_attempts` | Security audit trail |
| ScanHistory | `scan_history` | OCR results, confidence, processing time |
| DocumentTypeStats | `document_type_stats` | Aggregated per-type metrics |
| BatchProcessingJob | `batch_processing_jobs` | Batch job lifecycle |
| SystemMetrics | `system_metrics` | Performance telemetry |

**Connection Pooling** (production):
- Pool size: 20
- Max overflow: 40
- Pool timeout: 30s
- Pool recycle: 3600s

### Caching (`backend/app/cache/`)

| Layer | Implementation | Use Case |
|-------|---------------|----------|
| L1 | MemoryCache (dict) | Development, single-process |
| L2 | RedisCache | Production, multi-process |

Cache keys: `classification:{image_hash}` (TTL 3600s), `user_scans:{user_id}`, `document_stats`.

---

## 6. Async Processing

### Celery Configuration (`backend/app/celery_app.py`)

- **Broker**: Redis
- **Backend**: Redis
- **Queues**: `default`, `ocr_processing`, `batch_processing`, `analytics`, `maintenance`
- **Time limits**: Hard 300s, Soft 240s

### Tasks (`backend/app/tasks.py`)

| Task | Queue | Purpose |
|------|-------|---------|
| `process_document_async` | ocr_processing | Single document OCR |
| `batch_process_async` | batch_processing | Batch job execution |
| `generate_analytics_async` | analytics | Dashboard data refresh |
| `cleanup_old_files_async` | maintenance | File cleanup |

---

## 7. Monitoring & Observability

### Prometheus Metrics (`backend/app/monitoring.py`)

```
app_requests_total                    (Counter)
app_request_duration_seconds          (Histogram)
app_active_requests                   (Gauge)
ocr_processing_duration_seconds       (Histogram)
ocr_errors_total                      (Counter)
database_query_duration_seconds       (Histogram)
cache_hits_total / cache_misses_total (Counter)
system_cpu_usage_percent              (Gauge)
system_memory_usage_percent           (Gauge)
```

### Health Endpoints

```
GET /health          → basic liveness
GET /api/v2/health   → component-level status (db, cache, ocr, celery)
GET /api/ai/model/status → vision_available, ml_fitted, classifier_chain
```

### WebSocket (`backend/app/websocket/`)

flask-socketio for real-time progress updates during document processing. Events: `connected`, `progress_update`, `scan_complete`, `error`.

---

## 8. Security Architecture

### Defense-in-Depth Layers

1. **Network**: CORS whitelist, HTTPS enforcement (production)
2. **Authentication**: JWT tokens with expiry, refresh rotation
3. **Authorization**: Role-based (`@admin_required`, `@role_required`)
4. **Rate Limiting**: Per-endpoint limits (configurable, Redis-backed)
5. **Input Validation**: File type/size checks, JSON schema validation
6. **Content Scanning**: Regex-based XSS/SQLi/command injection detection
7. **Response Headers**: CSP, X-Frame-Options, HSTS, Referrer-Policy

### File Upload Security

- Max size: 16MB (configurable)
- Allowed types: JPEG, PNG, TIFF, BMP, PDF
- Magic byte validation
- Optional ClamAV virus scanning (production)

---

## 9. Deployment

### Docker Compose Services

| Service | Image | Port | Purpose |
|---------|-------|------|---------|
| ocr-scanner | Flask/Gunicorn | 5000 | Production API |
| backend-dev | Flask | 5001 | Development API |
| frontend-dev | Node/React | 3000 | Dev frontend |
| postgres | postgres:15-alpine | 5432 | Database |
| redis | redis:7-alpine | 6379 | Cache + broker |
| celery-worker | Flask + Celery | — | Async workers |
| celery-beat | Flask + Celery | — | Scheduled tasks |
| flower | Celery Flower | 5555 | Task monitor |

### Production Configuration

```bash
# Required
SECRET_KEY=<64-char random>
JWT_SECRET_KEY=<64-char random>
DATABASE_URL=postgresql://user:pass@host:5432/dbname
REDIS_URL=redis://:password@host:6379/0
CORS_ORIGINS=https://yourdomain.com

# Optional (Vision)
ANTHROPIC_API_KEY=sk-ant-...
VISION_MODEL=claude-sonnet-4-20250514
```

### Scaling Strategy

| Component | Strategy |
|-----------|----------|
| API | Horizontal: multiple Gunicorn workers behind load balancer |
| Workers | Horizontal: add Celery worker containers |
| Database | Vertical + read replicas for analytics |
| Cache | Redis Cluster or managed service |
| Frontend | CDN + static hosting |

---

## 10. Technology Stack Summary

| Layer | Technology | Version |
|-------|-----------|---------|
| Frontend | React.js | 18+ |
| UI Library | Material-UI | 5+ |
| Backend | Flask | 3.0+ |
| ORM | SQLAlchemy | 2.0 |
| OCR Engine | Tesseract (pytesseract) | 0.3.10 |
| Image Processing | OpenCV + Pillow | 4.9 / 10.3 |
| ML | scikit-learn | 1.3 |
| VLM | Anthropic Claude (anthropic SDK) | 0.42+ |
| Auth | PyJWT + bcrypt | 2.8 / 4.1 |
| Task Queue | Celery + Redis | 5.3 / 5.0 |
| WebSocket | flask-socketio | 5.3 |
| Monitoring | prometheus-client | 0.19 |
| Database | PostgreSQL (prod) / SQLite (dev) | 15 |
| Containerization | Docker Compose | — |

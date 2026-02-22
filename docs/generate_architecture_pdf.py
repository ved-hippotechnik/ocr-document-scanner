#!/usr/bin/env python3
"""
OCR Document Scanner - Technical Architecture PDF Generator

Generates a comprehensive technical architecture document covering
all layers of the OCR Document Scanner application.

Usage:
    python docs/generate_architecture_pdf.py

Requirements:
    pip install fpdf2
"""

import os
import sys
from datetime import datetime
from fpdf import FPDF


# ---------------------------------------------------------------------------
# Color palette
# ---------------------------------------------------------------------------
COLOR_PRIMARY = (41, 98, 255)       # Blue
COLOR_SECONDARY = (55, 71, 79)     # Dark gray-blue
COLOR_ACCENT = (0, 150, 136)       # Teal
COLOR_LIGHT_BG = (245, 247, 250)   # Light gray background
COLOR_TABLE_HEADER = (41, 98, 255) # Blue header
COLOR_TABLE_ALT = (240, 244, 255)  # Light blue alternate row
COLOR_CODE_BG = (240, 240, 240)    # Light gray code bg
COLOR_DIAGRAM_BG = (250, 250, 255) # Very light blue diagram bg
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)
COLOR_DARK_TEXT = (33, 33, 33)
COLOR_BORDER = (200, 200, 200)


class ArchitecturePDF(FPDF):
    """Custom PDF class with header/footer and helper methods."""

    def __init__(self):
        super().__init__(orientation='P', unit='mm', format='A4')
        self.set_auto_page_break(auto=True, margin=25)
        self.set_margins(20, 20, 20)
        self._chapter_num = 0
        self._in_cover = False
        self._toc_entries = []

    # ------------------------------------------------------------------
    # Header / Footer
    # ------------------------------------------------------------------
    def header(self):
        if self._in_cover:
            return
        self.set_font('Helvetica', 'B', 9)
        self.set_text_color(*COLOR_SECONDARY)
        self.cell(0, 8, 'OCR Document Scanner - Technical Architecture', align='L')
        self.set_draw_color(*COLOR_PRIMARY)
        self.set_line_width(0.5)
        self.line(20, 16, 190, 16)
        self.ln(10)

    def footer(self):
        if self._in_cover:
            return
        self.set_y(-20)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(*COLOR_SECONDARY)
        self.cell(0, 10, f'Page {self.page_no()}/{{nb}}', align='C')

    # ------------------------------------------------------------------
    # Cover page
    # ------------------------------------------------------------------
    def cover_page(self):
        self._in_cover = True
        self.add_page()

        # Blue banner at top
        self.set_fill_color(*COLOR_PRIMARY)
        self.rect(0, 0, 210, 100, 'F')

        # Title
        self.set_y(30)
        self.set_font('Helvetica', 'B', 32)
        self.set_text_color(*COLOR_WHITE)
        self.cell(0, 14, 'OCR Document Scanner', align='C', new_x='LMARGIN', new_y='NEXT')
        self.set_font('Helvetica', '', 18)
        self.cell(0, 10, 'Technical Architecture Document', align='C', new_x='LMARGIN', new_y='NEXT')

        # Accent line
        self.set_y(105)
        self.set_draw_color(*COLOR_ACCENT)
        self.set_line_width(1)
        self.line(60, 105, 150, 105)

        # Metadata
        self.set_y(115)
        self.set_font('Helvetica', '', 13)
        self.set_text_color(*COLOR_DARK_TEXT)
        self.cell(0, 10, f'Version 2.1  |  {datetime.now().strftime("%B %d, %Y")}', align='C', new_x='LMARGIN', new_y='NEXT')

        self.set_y(135)
        self.set_font('Helvetica', '', 11)
        self.set_text_color(*COLOR_SECONDARY)
        meta_lines = [
            'Full-Stack OCR Application with AI-Powered Document Classification',
            '',
            'Flask Backend  |  React Frontend  |  14 Document Processors',
            'Claude Vision AI  |  Celery Async  |  Docker Infrastructure',
            '',
            'Confidential - Internal Use Only',
        ]
        for line in meta_lines:
            self.cell(0, 7, line, align='C', new_x='LMARGIN', new_y='NEXT')

        # Bottom accent
        self.set_fill_color(*COLOR_PRIMARY)
        self.rect(0, 280, 210, 17, 'F')
        self.set_y(282)
        self.set_font('Helvetica', 'I', 9)
        self.set_text_color(*COLOR_WHITE)
        self.cell(0, 8, 'Generated automatically from codebase analysis', align='C')

        self._in_cover = False

    # ------------------------------------------------------------------
    # Table of Contents
    # ------------------------------------------------------------------
    def build_toc(self):
        self.add_page()
        self.set_font('Helvetica', 'B', 22)
        self.set_text_color(*COLOR_PRIMARY)
        self.cell(0, 14, 'Table of Contents', align='L', new_x='LMARGIN', new_y='NEXT')
        self.ln(6)

        self.set_font('Helvetica', '', 11)
        self.set_text_color(*COLOR_DARK_TEXT)

        toc_items = [
            ('1', 'Executive Summary'),
            ('2', 'System Architecture Overview'),
            ('3', 'Technology Stack'),
            ('4', 'Backend Architecture'),
            ('5', 'Frontend Architecture'),
            ('6', 'Database Architecture'),
            ('7', 'API Reference'),
            ('8', 'Security Architecture'),
            ('9', 'Infrastructure & Deployment'),
            ('10', 'Monitoring & Observability'),
            ('11', 'Performance Optimizations'),
            ('12', 'Data Flow Diagrams'),
            ('13', 'Appendices'),
        ]
        for num, title in toc_items:
            self.set_font('Helvetica', 'B', 11)
            self.cell(12, 8, f'{num}.', align='R')
            self.set_font('Helvetica', '', 11)
            self.cell(0, 8, f'  {title}', new_x='LMARGIN', new_y='NEXT')

    # ------------------------------------------------------------------
    # Helper methods
    # ------------------------------------------------------------------
    def chapter_title(self, number, title):
        self._chapter_num = number
        self.add_page()
        # Bookmark for PDF navigation
        self.start_section(f'{number}. {title}', level=0)
        self.set_font('Helvetica', 'B', 24)
        self.set_text_color(*COLOR_PRIMARY)
        self.cell(0, 14, f'{number}. {title}', new_x='LMARGIN', new_y='NEXT')
        self.set_draw_color(*COLOR_PRIMARY)
        self.set_line_width(0.8)
        self.line(20, self.get_y() + 1, 190, self.get_y() + 1)
        self.ln(8)

    def section_title(self, title, level=1):
        self.ln(4)
        if level == 1:
            self.set_font('Helvetica', 'B', 15)
            self.set_text_color(*COLOR_SECONDARY)
        else:
            self.set_font('Helvetica', 'B', 12)
            self.set_text_color(*COLOR_ACCENT)
        self.cell(0, 9, title, new_x='LMARGIN', new_y='NEXT')
        self.ln(2)

    def body_text(self, text):
        self.set_font('Helvetica', '', 10)
        self.set_text_color(*COLOR_DARK_TEXT)
        self.multi_cell(0, 5.5, text)
        self.ln(2)

    def bullet_list(self, items):
        self.set_font('Helvetica', '', 10)
        self.set_text_color(*COLOR_DARK_TEXT)
        for item in items:
            self.set_x(24)
            self.cell(5, 5.5, '-')
            self.set_x(29)
            self.multi_cell(161, 5.5, item)
            if self.get_y() > 270:
                self.add_page()
        self.ln(2)

    def code_block(self, text):
        self.ln(2)
        self.set_fill_color(*COLOR_CODE_BG)
        self.set_draw_color(*COLOR_BORDER)
        self.set_font('Courier', '', 8)
        self.set_text_color(*COLOR_DARK_TEXT)

        lines = text.split('\n')
        line_h = 4.2
        block_h = len(lines) * line_h + 6

        # Check page space
        if self.get_y() + block_h > 270:
            self.add_page()

        y_start = self.get_y()
        self.rect(20, y_start, 170, block_h, 'FD')
        self.set_xy(23, y_start + 3)

        for line in lines:
            self.cell(0, line_h, line, new_x='LMARGIN', new_y='NEXT')
            self.set_x(23)

        self.set_y(y_start + block_h + 2)
        self.ln(2)

    def ascii_diagram(self, text, title=None):
        self.ln(2)
        if title:
            self.set_font('Helvetica', 'BI', 10)
            self.set_text_color(*COLOR_SECONDARY)
            self.cell(0, 6, title, align='C', new_x='LMARGIN', new_y='NEXT')
            self.ln(1)

        self.set_fill_color(*COLOR_DIAGRAM_BG)
        self.set_draw_color(*COLOR_PRIMARY)
        self.set_line_width(0.4)
        self.set_font('Courier', '', 7.5)
        self.set_text_color(*COLOR_DARK_TEXT)

        lines = text.split('\n')
        line_h = 3.8
        block_h = len(lines) * line_h + 8

        if self.get_y() + block_h > 270:
            self.add_page()

        y_start = self.get_y()
        self.rect(22, y_start, 166, block_h, 'FD')
        self.set_xy(25, y_start + 4)

        for line in lines:
            self.cell(0, line_h, line, new_x='LMARGIN', new_y='NEXT')
            self.set_x(25)

        self.set_y(y_start + block_h + 2)
        self.ln(2)

    def add_table(self, headers, rows, col_widths=None):
        self.ln(2)
        num_cols = len(headers)
        if col_widths is None:
            col_widths = [170 / num_cols] * num_cols

        row_h = 7

        # Check if table fits, if not start new page
        table_h = (len(rows) + 1) * row_h + 4
        if self.get_y() + min(table_h, 50) > 270:
            self.add_page()

        # Header row
        self.set_fill_color(*COLOR_TABLE_HEADER)
        self.set_text_color(*COLOR_WHITE)
        self.set_font('Helvetica', 'B', 9)
        self.set_draw_color(*COLOR_WHITE)

        x_start = 20
        self.set_x(x_start)
        for i, h in enumerate(headers):
            self.cell(col_widths[i], row_h, f' {h}', border=1, fill=True)
        self.ln()

        # Data rows
        self.set_text_color(*COLOR_DARK_TEXT)
        self.set_font('Helvetica', '', 8.5)
        self.set_draw_color(*COLOR_BORDER)

        for idx, row in enumerate(rows):
            if self.get_y() + row_h > 270:
                self.add_page()
                # Repeat header
                self.set_fill_color(*COLOR_TABLE_HEADER)
                self.set_text_color(*COLOR_WHITE)
                self.set_font('Helvetica', 'B', 9)
                self.set_draw_color(*COLOR_WHITE)
                self.set_x(x_start)
                for i, h in enumerate(headers):
                    self.cell(col_widths[i], row_h, f' {h}', border=1, fill=True)
                self.ln()
                self.set_text_color(*COLOR_DARK_TEXT)
                self.set_font('Helvetica', '', 8.5)
                self.set_draw_color(*COLOR_BORDER)

            if idx % 2 == 1:
                self.set_fill_color(*COLOR_TABLE_ALT)
                fill = True
            else:
                self.set_fill_color(*COLOR_WHITE)
                fill = True

            self.set_x(x_start)
            for i, cell_text in enumerate(row):
                self.cell(col_widths[i], row_h, f' {str(cell_text)}', border=1, fill=fill)
            self.ln()

        self.ln(3)


# ======================================================================
# Chapter builders
# ======================================================================

def build_ch01(pdf):
    """Chapter 1: Executive Summary"""
    pdf.chapter_title(1, 'Executive Summary')

    pdf.section_title('1.1 System Overview')
    pdf.body_text(
        'The OCR Document Scanner is an enterprise-grade, full-stack application designed '
        'to extract structured data from identity documents using Optical Character Recognition (OCR) '
        'and Artificial Intelligence. The system supports 14 document types across 8 countries, '
        'combining Tesseract OCR with Claude Vision AI for industry-leading extraction accuracy.'
    )

    pdf.section_title('1.2 Key Capabilities')
    pdf.bullet_list([
        '14 specialized document processors (Aadhaar, Emirates ID, Passport, Driving License, etc.)',
        'AI hybrid pipeline: ML classifier + Claude Vision API for document classification',
        'Batch processing with Celery async task queues (5 dedicated queues)',
        'Real-time progress tracking via Socket.IO WebSocket',
        'JWT authentication with role-based access control',
        'Progressive Web App (PWA) with offline support and IndexedDB queue',
        'Docker multi-stage deployment with PostgreSQL, Redis, Nginx',
        'Prometheus metrics, structured JSON logging, health monitoring',
        'Duplicate document detection using perceptual hashing (pHash)',
        'MRZ (Machine Readable Zone) parsing for passports and travel documents',
        'Multi-page PDF document support with per-page OCR',
        'Automatic language detection and multi-language OCR',
        'Image dewarping for skewed document correction',
        'Webhook notifications for async processing completion',
    ])

    pdf.section_title('1.3 Target Audience')
    pdf.body_text(
        'This document is intended for software architects, backend/frontend developers, '
        'DevOps engineers, and technical leads involved in the development, deployment, '
        'and maintenance of the OCR Document Scanner application.'
    )

    pdf.section_title('1.4 Document Scope')
    pdf.body_text(
        'This technical architecture document covers every layer of the application: '
        'backend services, frontend components, database schema, API reference, '
        'security architecture, infrastructure, monitoring, performance optimizations, '
        'and data flow diagrams. All information is derived directly from codebase analysis.'
    )


def build_ch02(pdf):
    """Chapter 2: System Architecture Overview"""
    pdf.chapter_title(2, 'System Architecture Overview')

    pdf.section_title('2.1 High-Level Architecture')
    pdf.body_text(
        'The OCR Document Scanner follows a layered architecture with clear separation '
        'of concerns. The system comprises a React PWA frontend, Flask REST API backend, '
        'Celery async workers, and supporting infrastructure services.'
    )

    pdf.ascii_diagram("""
+------------------+        +-------------------+       +------------------+
|                  |  HTTPS |                   |       |                  |
|   React PWA      +------->+   Nginx Reverse   +------>+   Flask App      |
|   (Frontend)     |        |   Proxy (SSL)     |       |   (Gunicorn)     |
|                  |<-------+                   |<------+                  |
+------------------+        +-------------------+       +--------+---------+
                                    |                            |
                          WebSocket |                   +--------+---------+
                          Upgrade   |                   |                  |
                                    |            +------+  Socket.IO       |
                                    +----------->+      |  (WebSocket)     |
                                                 |      +------------------+
+------------------+                             |
|                  |        +-------------------+|      +------------------+
|  PostgreSQL      |<-------+ SQLAlchemy ORM    ||      |                  |
|  (Production)    |        +-------------------+|      |  Redis Cache     |
|  SQLite (Dev)    |                             +----->+  (Session/Queue) |
+------------------+                             |      +------------------+
                                                 |
                            +-------------------+|      +------------------+
                            |                   ||      |                  |
                            | Celery Workers    |<------+  Celery Beat     |
                            | (5 Queues)        ||      |  (Scheduler)     |
                            +-------------------+|      +------------------+
                                                 |
                    +------------------+         |      +------------------+
                    |                  |         |      |                  |
                    | Tesseract OCR    |<--------+----->+ Claude Vision AI |
                    | Engine           |                 | (Anthropic API)  |
                    +------------------+                 +------------------+
""", title='Figure 2.1: High-Level System Architecture')

    pdf.section_title('2.2 Request Flow')
    pdf.body_text(
        'A typical document scanning request flows through the following stages:'
    )

    pdf.ascii_diagram("""
Client Request
      |
      v
+---> Nginx (SSL termination, rate limiting)
      |
      v
+---> Flask App Factory (CORS, JWT validation, security middleware)
      |
      v
+---> Route Handler (validation, file upload processing)
      |
      +--> Sync Path                  +--> Async Path
      |    |                          |    |
      |    v                          |    v
      |    Image Preprocessing        |    Celery Task Dispatch
      |    (OpenCV, dewarping)        |    (Redis broker)
      |    |                          |    |
      |    v                          |    v
      |    Tesseract OCR              |    Worker: OCR Processing
      |    |                          |    |
      |    v                          |    v
      |    Document Detection         |    WebSocket: Progress Updates
      |    (Registry + AI)            |    |
      |    |                          |    v
      |    v                          |    Worker: Data Extraction
      |    Data Extraction            |    |
      |    (Processor-specific)       |    v
      |    |                          |    WebSocket: Results
      |    v                          |
      |    JSON Response              |
      |                               |
      v                               v
   Client receives result         Client receives via WebSocket
""", title='Figure 2.2: Request Flow')

    pdf.section_title('2.3 Component Interaction Map')
    pdf.body_text(
        'The backend is organized into modular blueprints, each with dedicated routes, '
        'services, and data models. Interaction between components follows the dependency '
        'injection pattern established by the Flask app factory.'
    )

    pdf.ascii_diagram("""
+-------------------------------------------------------------------+
|                        Flask App Factory                          |
|                        (app/__init__.py)                          |
+--------+--------+--------+--------+--------+--------+------------+
         |        |        |        |        |        |
         v        v        v        v        v        v
     +------+ +------+ +------+ +------+ +------+ +--------+
     | Core | | Auth | |  AI  | |Batch | |Async | |Analyt. |
     |Routes| |Routes| |Routes| |Routes| |Routes| |Routes  |
     +--+---+ +--+---+ +--+---+ +--+---+ +--+---+ +---+----+
        |        |        |        |        |          |
        v        v        v        v        v          v
   +----------+ +-----+ +-------+ +-------+ +------+ +--------+
   |Processor | | JWT | |Vision | | Batch | |Celery| |Dashboard|
   |Registry  | |Utils| |Service| |Process| | App  | |Service  |
   |(14 proc.)| |     | |       | |       | |      | |         |
   +----------+ +-----+ +-------+ +-------+ +------+ +--------+
        |                    |                   |
        v                    v                   v
   +----------+        +---------+         +----------+
   | Tesseract|        | Claude  |         | Redis    |
   | OCR      |        | API     |         | Broker   |
   +----------+        +---------+         +----------+
""", title='Figure 2.3: Component Interaction Map')


def build_ch03(pdf):
    """Chapter 3: Technology Stack"""
    pdf.chapter_title(3, 'Technology Stack')

    pdf.section_title('3.1 Backend Technologies')
    pdf.add_table(
        ['Technology', 'Version', 'Purpose'],
        [
            ['Flask', '3.1.x', 'Python web framework'],
            ['SQLAlchemy', '2.0.x', 'Database ORM'],
            ['Flask-SocketIO', '5.5.x', 'WebSocket support'],
            ['Celery', '5.4.x', 'Async task queue'],
            ['Redis', '5.2.x', 'Cache / message broker'],
            ['Tesseract OCR', '5.x', 'Optical character recognition engine'],
            ['OpenCV (cv2)', '4.x', 'Computer vision / image processing'],
            ['Pillow', '11.x', 'Image format handling'],
            ['scikit-learn', '1.6.x', 'ML document classifier'],
            ['PyJWT', '2.10.x', 'JWT token management'],
            ['bcrypt', '4.2.x', 'Password hashing'],
            ['anthropic', '0.42.x', 'Claude Vision AI SDK'],
            ['Gunicorn', '23.x', 'WSGI HTTP server'],
            ['pythonjsonlogger', '3.x', 'Structured JSON logging'],
            ['prometheus-client', '0.21.x', 'Metrics instrumentation'],
            ['python-dotenv', '1.x', 'Environment configuration'],
            ['imagehash', '4.3.x', 'Perceptual hashing (duplicate detection)'],
            ['langdetect', '1.0.x', 'Language auto-detection'],
            ['PyMuPDF (fitz)', '1.25.x', 'PDF parsing and rendering'],
        ],
        col_widths=[40, 22, 108]
    )

    pdf.section_title('3.2 Frontend Technologies')
    pdf.add_table(
        ['Technology', 'Version', 'Purpose'],
        [
            ['React', '18.x', 'UI component library'],
            ['Material-UI (MUI)', '7.x', 'Component design system'],
            ['React Router', '7.x', 'Client-side routing'],
            ['Axios', '1.x', 'HTTP client with interceptors'],
            ['Socket.IO Client', '4.x', 'WebSocket real-time updates'],
            ['Recharts', '2.x', 'Data visualization / charts'],
            ['React Dropzone', '14.x', 'Drag-and-drop file upload'],
            ['React Toastify', '11.x', 'Toast notifications'],
            ['Web Vitals', '4.x', 'Performance measurement'],
        ],
        col_widths=[40, 22, 108]
    )

    pdf.section_title('3.3 Infrastructure')
    pdf.add_table(
        ['Technology', 'Version', 'Purpose'],
        [
            ['Docker', 'Multi-stage', 'Containerization'],
            ['Docker Compose', 'v3.8', 'Service orchestration'],
            ['PostgreSQL', '15', 'Production database'],
            ['SQLite', '3.x', 'Development database'],
            ['Redis', '7-alpine', 'Cache and message broker'],
            ['Nginx', '1.25', 'Reverse proxy, SSL, load balancer'],
            ['GitHub Actions', '-', 'CI/CD pipeline (4 stages)'],
            ['Flower', '2.x', 'Celery task monitoring dashboard'],
        ],
        col_widths=[40, 22, 108]
    )


def build_ch04(pdf):
    """Chapter 4: Backend Architecture"""
    pdf.chapter_title(4, 'Backend Architecture')

    # 4.1 App Factory
    pdf.section_title('4.1 App Factory Initialization')
    pdf.body_text(
        'The Flask application uses the factory pattern (app/__init__.py). '
        'The create_app() function initializes 14 components in a specific order '
        'and returns a tuple of (app, socketio):'
    )

    pdf.add_table(
        ['#', 'Component', 'Description'],
        [
            ['1', 'Flask(__name__)', 'Create Flask app instance'],
            ['2', 'Config loading', 'Load from config dict + .env'],
            ['3', 'CORS', 'Cross-origin resource sharing setup'],
            ['4', 'SQLAlchemy', 'Database ORM initialization (db.init_app)'],
            ['5', 'DB table creation', 'db.create_all() within app context'],
            ['6', 'JWT Setup', 'Secret key, token expiry config'],
            ['7', 'Cache init', 'Redis (prod) or MemoryCache (dev)'],
            ['8', 'Monitoring', 'Prometheus metrics, structured logging'],
            ['9', 'Security middleware', '8-layer security pipeline'],
            ['10', 'Blueprint: core routes', '/api/* endpoints'],
            ['11', 'Blueprint: enhanced', '/api/v2/* endpoints'],
            ['12', 'Blueprint: auth', '/api/auth/* endpoints'],
            ['13', 'Blueprint: AI', '/api/ai/* endpoints'],
            ['14', 'Blueprint: batch', '/api/batch/* endpoints'],
            ['15', 'Blueprint: async', '/api/async/* endpoints'],
            ['16', 'Blueprint: analytics', '/analytics/* endpoints'],
            ['17', 'SocketIO', 'WebSocket event handlers'],
        ],
        col_widths=[10, 45, 115]
    )

    # 4.2 Processor Registry
    pdf.section_title('4.2 Document Processor Registry')
    pdf.body_text(
        'The ProcessorRegistry (app/processors/registry.py) manages 14 document processors, '
        'each with a priority-based detection system. When text is extracted via OCR, '
        'the registry iterates through processors by priority to detect the document type.'
    )

    pdf.add_table(
        ['Processor', 'Document Type', 'Country', 'Priority'],
        [
            ['AadhaarProcessor', 'Aadhaar Card', 'India', 'High'],
            ['EmiratesIDProcessor', 'Emirates ID', 'UAE', 'High'],
            ['PassportProcessor', 'Passport', 'Multi-country', 'High'],
            ['DrivingLicenseProcessor', 'Driving License', 'India', 'Medium'],
            ['USDriversLicenseProcessor', "US Driver's License", 'USA', 'Medium'],
            ['PanCardProcessor', 'PAN Card', 'India', 'Medium'],
            ['VoterIDProcessor', 'Voter ID', 'India', 'Medium'],
            ['RationCardProcessor', 'Ration Card', 'India', 'Low'],
            ['BirthCertProcessor', 'Birth Certificate', 'India', 'Low'],
            ['SSNCardProcessor', 'SSN Card', 'USA', 'Low'],
            ['MedicareCardProcessor', 'Medicare Card', 'Australia', 'Low'],
            ['NHSCardProcessor', 'NHS Card', 'UK', 'Low'],
            ['EUIDCardProcessor', 'EU ID Card', 'EU', 'Low'],
            ['CanadianDLProcessor', 'Canadian DL', 'Canada', 'Low'],
        ],
        col_widths=[45, 38, 35, 52]
    )

    pdf.body_text(
        'Each processor implements three core methods: detect(text) -> bool, '
        'extract_info(text) -> dict, and preprocess(image) -> image. '
        'The base class BaseProcessor (app/processors/__init__.py) provides default '
        'implementations for preprocessing that apply grayscale conversion, '
        'Gaussian blur, and adaptive thresholding.'
    )

    # 4.3 OCR Pipeline
    pdf.section_title('4.3 OCR Pipeline')
    pdf.ascii_diagram("""
 Input Image
      |
      v
 +--------------------+
 | Image Preprocessing |  <-- OpenCV: resize, grayscale, denoise
 | (per-processor)     |      adaptive threshold, dewarping
 +--------------------+
      |
      v
 +--------------------+
 | Quality Assessment  |  <-- Blur detection, brightness check,
 | (pre-OCR)          |      contrast analysis, resolution check
 +--------------------+
      |
      v
 +--------------------+
 | Tesseract OCR      |  <-- pytesseract.image_to_string()
 | (text extraction)   |      with language hints
 +--------------------+
      |
      v
 +--------------------+
 | Language Detection  |  <-- langdetect library
 | (auto)             |      select optimal Tesseract lang
 +--------------------+
      |
      v
 +--------------------+
 | Document Detection  |  <-- ProcessorRegistry.detect_document_type()
 | (registry scan)     |      priority-ordered processor matching
 +--------------------+
      |
      v
 +--------------------+
 | Data Extraction    |  <-- Processor-specific regex + NLP
 | (structured)       |      returns field-level data + confidence
 +--------------------+
      |
      v
 +--------------------+
 | Confidence Scoring |  <-- Per-field confidence (0.0 - 1.0)
 | (per-field)        |      overall document confidence
 +--------------------+
      |
      v
  JSON Response
""", title='Figure 4.1: OCR Processing Pipeline')

    # 4.4 AI/ML Hybrid Pipeline
    pdf.section_title('4.4 AI/ML Hybrid Pipeline')
    pdf.body_text(
        'The AI module (app/ai/) provides a hybrid classification pipeline that combines '
        'a local ML classifier with Claude Vision API for enhanced accuracy.'
    )

    pdf.ascii_diagram("""
  Document Image
       |
       v
  +-----------------------+
  | ML Classifier         |  <-- scikit-learn TF-IDF + SVM
  | (Local, fast)         |      trained on OCR text patterns
  +-----------------------+
       |
       |-- Confidence >= 0.8 ---> Use ML result
       |
       |-- Confidence < 0.8 -+
       |                     |
       v                     v
  +-----------------------+
  | Claude Vision API     |  <-- anthropic SDK
  | (Cloud, accurate)     |      base64 image + prompt
  +-----------------------+
       |
       v
  +-----------------------+
  | Result Validation     |  <-- Cross-check ML vs Vision
  | & Merging            |      highest confidence wins
  +-----------------------+
       |
       v
  +-----------------------+
  | Cache Result          |  <-- Redis: keyed by image hash
  | (avoid re-processing) |      TTL: 3600s (1 hour)
  +-----------------------+
       |
       v
   Classification Result
   (doc_type, confidence, fields)
""", title='Figure 4.2: AI Classification Pipeline')

    # 4.5 Authentication
    pdf.section_title('4.5 Authentication System')
    pdf.body_text(
        'The auth module (app/auth/) implements JWT-based authentication with bcrypt '
        'password hashing, role-based access control, and account lockout protection.'
    )

    pdf.add_table(
        ['Feature', 'Configuration', 'Details'],
        [
            ['Access Token', '24 hours', 'JWT with HS256 algorithm'],
            ['Refresh Token', '30 days', 'Separate secret, rotation support'],
            ['Password Hashing', 'bcrypt', '12 rounds default'],
            ['Account Lockout', '5 attempts / 15 min', 'IP + username tracking'],
            ['Roles', 'user, admin', 'Decorator-based enforcement'],
            ['Token Refresh', 'Auto on 401', 'Frontend Axios interceptor'],
            ['Secret Enforcement', 'Production only', 'Rejects default secrets in prod'],
        ],
        col_widths=[38, 38, 94]
    )

    # 4.6 Cache
    pdf.section_title('4.6 Caching Strategy')
    pdf.body_text(
        'The cache module (app/cache/) provides a unified interface with two backends: '
        'MemoryCache for development and RedisCache for production. Vision API results '
        'are cached using image content hash as the key.'
    )

    pdf.add_table(
        ['Cache Type', 'Backend', 'TTL', 'Use Case'],
        [
            ['Vision Cache', 'Redis/Memory', '3600s', 'AI classification results by image hash'],
            ['OCR Cache', 'Redis/Memory', '1800s', 'Tesseract OCR results'],
            ['Session Cache', 'Redis', '86400s', 'User session data'],
            ['Rate Limit', 'Redis', '60s', 'Request rate tracking'],
        ],
        col_widths=[35, 32, 22, 81]
    )

    # 4.7 Celery Async
    pdf.section_title('4.7 Asynchronous Processing (Celery)')
    pdf.body_text(
        'Celery (app/celery_app.py) provides distributed task processing with Redis as '
        'the message broker. Five dedicated queues ensure task isolation and prioritization.'
    )

    pdf.add_table(
        ['Queue Name', 'Purpose', 'Workers', 'Priority'],
        [
            ['ocr_processing', 'Single document OCR tasks', '2', 'Highest'],
            ['batch_processing', 'Batch job orchestration', '2', 'High'],
            ['analytics', 'Stats aggregation, reporting', '1', 'Medium'],
            ['maintenance', 'Cache cleanup, DB maintenance', '1', 'Low'],
            ['default', 'General-purpose tasks', '1', 'Normal'],
        ],
        col_widths=[38, 60, 25, 47]
    )

    # 4.8 WebSocket
    pdf.section_title('4.8 WebSocket Communication')
    pdf.body_text(
        'Flask-SocketIO (app/websocket/__init__.py) provides real-time bidirectional '
        'communication. Each client joins a room identified by their session or job ID.'
    )

    pdf.add_table(
        ['Event', 'Direction', 'Payload', 'Description'],
        [
            ['connect', 'Client -> Server', 'auth token', 'Join processing room'],
            ['processing_progress', 'Server -> Client', '{progress, step, message}', 'Progress update (0-100%)'],
            ['processing_complete', 'Server -> Client', '{result, doc_type, data}', 'Final extraction result'],
            ['processing_error', 'Server -> Client', '{error, code, details}', 'Error notification'],
            ['batch_progress', 'Server -> Client', '{job_id, completed, total}', 'Batch job progress'],
            ['disconnect', 'Bidirectional', '-', 'Leave room and cleanup'],
        ],
        col_widths=[38, 30, 50, 52]
    )

    # 4.9 New Features
    pdf.section_title('4.9 Advanced Features')

    pdf.section_title('Duplicate Document Detection', level=2)
    pdf.body_text(
        'Uses perceptual hashing (pHash) via the imagehash library to detect duplicate '
        'document submissions. The system computes a hash of each uploaded image and '
        'compares it against previously processed documents using Hamming distance. '
        'Documents with a distance below the threshold are flagged as potential duplicates.'
    )

    pdf.section_title('Webhook Notifications', level=2)
    pdf.body_text(
        'Async processing results can be delivered via webhook callbacks. When a batch '
        'job or async scan completes, the system sends an HTTP POST to the configured '
        'webhook URL with the processing results as a JSON payload.'
    )

    pdf.section_title('Language Auto-Detection', level=2)
    pdf.body_text(
        'The langdetect library analyzes extracted text to determine the document language. '
        'This information is used to optimize subsequent OCR passes by selecting the '
        'appropriate Tesseract language model (e.g., eng, hin, ara).'
    )

    pdf.section_title('MRZ Parsing', level=2)
    pdf.body_text(
        'Machine Readable Zone (MRZ) parsing extracts structured data from the bottom '
        'of passport and travel documents. The parser handles both TD1 (3-line) and '
        'TD3 (2-line) MRZ formats, extracting document number, nationality, date of birth, '
        'expiry date, and name fields with check digit validation.'
    )

    pdf.section_title('PDF Multi-Page Support', level=2)
    pdf.body_text(
        'PyMuPDF (fitz) enables processing of multi-page PDF documents. Each page is '
        'rendered to an image, processed through the OCR pipeline independently, and '
        'results are aggregated into a unified response with per-page data.'
    )

    pdf.section_title('Image Dewarping', level=2)
    pdf.body_text(
        'OpenCV-based dewarping corrects perspective distortion in photographed documents. '
        'The algorithm detects document edges using contour detection, computes the '
        'perspective transform matrix, and applies a warp to produce a flat, rectangular image.'
    )


def build_ch05(pdf):
    """Chapter 5: Frontend Architecture"""
    pdf.chapter_title(5, 'Frontend Architecture')

    pdf.section_title('5.1 Component Hierarchy')
    pdf.body_text(
        'The React frontend (frontend/src/) is organized as a single-page application '
        'with 6 primary routes, each wrapped in ErrorBoundary components for graceful '
        'error handling.'
    )

    pdf.ascii_diagram("""
  <App>
    |
    +-- <Navbar />
    |
    +-- <ErrorBoundary>
    |     |
    |     +-- Route: "/"           --> <Scanner />
    |     +-- Route: "/ai"         --> <AIScanner />
    |     +-- Route: "/dashboard"  --> <AIDashboard />
    |     +-- Route: "/batch"      --> <BatchProcessor />
    |     +-- Route: "/login"      --> <Login />
    |     +-- Route: "/admin"      --> <AdminDashboard />
    |
    +-- <OfflineStatus />
    +-- <ToastContainer />
""", title='Figure 5.1: Component Hierarchy')

    pdf.add_table(
        ['Component', 'File', 'Description'],
        [
            ['Scanner', 'Scanner.js', 'Basic OCR scanning with drag-and-drop upload'],
            ['AIScanner', 'AIScanner.js', 'AI-powered scanning with classification'],
            ['AIDashboard', 'AIDashboard.js', 'Analytics dashboard with charts'],
            ['BatchProcessor', 'BatchProcessor.js', 'Multi-document batch processing'],
            ['AdminDashboard', 'AdminDashboard.js', 'Admin panel (user mgmt, system stats)'],
            ['Login', 'Login.js', 'Authentication form'],
            ['Navbar', 'Navbar.js', 'Navigation with responsive drawer'],
            ['OfflineStatus', 'OfflineStatus.js', 'PWA offline indicator'],
        ],
        col_widths=[38, 42, 90]
    )

    pdf.section_title('5.2 State Management')
    pdf.body_text(
        'The frontend uses a pragmatic state management approach rather than a global '
        'store like Redux. State is managed at four levels:'
    )
    pdf.bullet_list([
        'Component local state (useState) - form inputs, UI toggles, loading states',
        'AuthContext (React Context) - user authentication state, JWT tokens, user profile',
        'localStorage - JWT token persistence, user preferences, theme settings',
        'IndexedDB - Offline processing queue, cached scan results for PWA mode',
    ])

    pdf.section_title('5.3 Progressive Web App (PWA)')
    pdf.body_text(
        'The application is a fully functional PWA with service worker registration, '
        'offline support, and install prompt handling.'
    )
    pdf.add_table(
        ['Feature', 'Implementation', 'Details'],
        [
            ['Service Worker', 'serviceWorkerRegistration.js', 'Cache-first strategy for static assets'],
            ['Offline Queue', 'IndexedDB', 'Queue scans when offline, sync when online'],
            ['Install Prompt', 'beforeinstallprompt event', 'Custom install banner'],
            ['Background Sync', 'Service Worker API', 'Retry failed requests when online'],
            ['App Manifest', 'manifest.json', 'Name, icons, theme color, display mode'],
        ],
        col_widths=[35, 55, 80]
    )

    pdf.section_title('5.4 API Integration')
    pdf.body_text(
        'All API communication uses Axios with request/response interceptors for '
        'automatic JWT token management. On receiving a 401 response, the interceptor '
        'automatically attempts to refresh the access token using the stored refresh token.'
    )

    pdf.code_block("""// Axios interceptor pattern (simplified)
axios.interceptors.response.use(
  response => response,
  async error => {
    if (error.response?.status === 401 && !error.config._retry) {
      error.config._retry = true;
      const newToken = await refreshAccessToken();
      error.config.headers.Authorization = `Bearer ${newToken}`;
      return axios(error.config);
    }
    return Promise.reject(error);
  }
);""")

    pdf.section_title('5.5 Theme & Responsive Design')
    pdf.body_text(
        'The UI uses a custom Material-UI theme with an Apple-inspired design language. '
        'Responsive breakpoints ensure the application works across all device sizes.'
    )
    pdf.add_table(
        ['Breakpoint', 'Width', 'Layout'],
        [
            ['xs', '0-599px', 'Single column, full-width components'],
            ['sm', '600-899px', 'Two columns, compact navigation'],
            ['md', '900-1199px', 'Standard desktop layout'],
            ['lg', '1200-1535px', 'Wide layout with sidebars'],
            ['xl', '1536px+', 'Full-width with maximum content area'],
        ],
        col_widths=[30, 35, 105]
    )


def build_ch06(pdf):
    """Chapter 6: Database Architecture"""
    pdf.chapter_title(6, 'Database Architecture')

    pdf.section_title('6.1 Entity Relationship Diagram')
    pdf.ascii_diagram("""
+-------------------+       +---------------------+       +---------------------+
|      User         |       |    LoginAttempt      |       |    ScanHistory      |
+-------------------+       +---------------------+       +---------------------+
| id (PK)           |<---+  | id (PK)             |       | id (PK)             |
| username (unique)  |    +--| user_id (FK)        |       | document_type       |
| email (unique)     |       | ip_address          |       | file_name           |
| password_hash      |       | success (bool)      |       | extracted_text      |
| role (user/admin)  |       | timestamp           |       | confidence_score    |
| is_active (bool)   |       | user_agent          |       | processing_time     |
| created_at         |       +---------------------+       | status              |
| last_login         |                                     | ip_address          |
+-------------------+                                      | created_at          |
                                                           +---------------------+

+---------------------+       +---------------------+       +---------------------+
| DocumentTypeStats   |       |BatchProcessingJob   |       |  SystemMetrics      |
+---------------------+       +---------------------+       +---------------------+
| id (PK)             |       | id (PK)             |       | id (PK)             |
| document_type       |       | job_id (unique)     |       | metric_name         |
| total_scans         |       | status              |       | metric_value        |
| successful_scans    |       | total_documents     |       | metric_type         |
| failed_scans        |       | processed_documents |       | tags (JSON)         |
| avg_confidence      |       | failed_documents    |       | timestamp           |
| avg_processing_time |       | results (JSON)      |       +---------------------+
| last_scanned        |       | created_at          |
+---------------------+       | updated_at          |
                              | webhook_url         |
                              +---------------------+
""", title='Figure 6.1: Entity Relationship Diagram')

    pdf.section_title('6.2 Model Details')

    pdf.section_title('User Model', level=2)
    pdf.add_table(
        ['Column', 'Type', 'Constraints', 'Description'],
        [
            ['id', 'Integer', 'PK, auto-increment', 'Unique user identifier'],
            ['username', 'String(80)', 'Unique, not null', 'Login username'],
            ['email', 'String(120)', 'Unique, not null', 'Email address'],
            ['password_hash', 'String(255)', 'Not null', 'bcrypt hashed password'],
            ['role', 'String(20)', "Default 'user'", 'User role (user/admin)'],
            ['is_active', 'Boolean', 'Default True', 'Account active status'],
            ['created_at', 'DateTime', 'Default utcnow', 'Registration timestamp'],
            ['last_login', 'DateTime', 'Nullable', 'Last login timestamp'],
        ],
        col_widths=[32, 28, 38, 72]
    )

    pdf.section_title('ScanHistory Model', level=2)
    pdf.add_table(
        ['Column', 'Type', 'Constraints', 'Description'],
        [
            ['id', 'Integer', 'PK, auto-increment', 'Unique scan identifier'],
            ['document_type', 'String(50)', 'Nullable', 'Detected document type'],
            ['file_name', 'String(255)', 'Nullable', 'Uploaded file name'],
            ['extracted_text', 'Text', 'Nullable', 'Raw OCR text'],
            ['confidence_score', 'Float', 'Nullable', 'Overall confidence (0-1)'],
            ['processing_time', 'Float', 'Nullable', 'Processing time (seconds)'],
            ['status', 'String(20)', "Default 'pending'", 'Processing status'],
            ['ip_address', 'String(45)', 'Nullable', 'Client IP address'],
            ['created_at', 'DateTime', 'Default utcnow', 'Scan timestamp'],
        ],
        col_widths=[32, 28, 38, 72]
    )

    pdf.section_title('BatchProcessingJob Model', level=2)
    pdf.add_table(
        ['Column', 'Type', 'Constraints', 'Description'],
        [
            ['id', 'Integer', 'PK, auto-increment', 'Internal identifier'],
            ['job_id', 'String(36)', 'Unique, not null', 'UUID job identifier'],
            ['status', 'String(20)', "Default 'pending'", 'Job status'],
            ['total_documents', 'Integer', 'Default 0', 'Total docs in batch'],
            ['processed_documents', 'Integer', 'Default 0', 'Docs processed so far'],
            ['failed_documents', 'Integer', 'Default 0', 'Failed documents count'],
            ['results', 'Text (JSON)', 'Nullable', 'JSON results array'],
            ['webhook_url', 'String(500)', 'Nullable', 'Callback URL'],
            ['created_at', 'DateTime', 'Default utcnow', 'Job creation time'],
            ['updated_at', 'DateTime', 'Auto-update', 'Last update time'],
        ],
        col_widths=[35, 28, 35, 72]
    )

    pdf.section_title('6.3 Connection Pooling')
    pdf.body_text(
        'Production PostgreSQL connections are managed via SQLAlchemy connection pooling:'
    )
    pdf.add_table(
        ['Parameter', 'Value', 'Description'],
        [
            ['pool_size', '20', 'Number of persistent connections'],
            ['max_overflow', '40', 'Additional connections beyond pool_size'],
            ['pool_pre_ping', 'True', 'Verify connections before use'],
            ['pool_recycle', '3600', 'Recycle connections after 1 hour'],
            ['pool_timeout', '30', 'Wait timeout for available connection'],
        ],
        col_widths=[40, 25, 105]
    )

    pdf.section_title('6.4 Migration Strategy')
    pdf.body_text(
        'Development uses SQLite for simplicity. Production uses PostgreSQL. '
        'The transition is handled via the DATABASE_URL environment variable. '
        'SQLAlchemy abstracts the dialect differences, though some PostgreSQL-specific '
        'features (JSON columns, array types) require conditional handling. '
        'Schema migrations should use Flask-Migrate (Alembic) in production.'
    )


def build_ch07(pdf):
    """Chapter 7: API Reference"""
    pdf.chapter_title(7, 'API Reference')

    pdf.body_text(
        'The API is organized into 9 blueprint groups. All endpoints return JSON. '
        'Authenticated endpoints require a Bearer JWT token in the Authorization header.'
    )

    # Core API
    pdf.section_title('7.1 Core API (/api/*)')
    pdf.add_table(
        ['Method', 'Path', 'Auth', 'Description'],
        [
            ['POST', '/api/scan', 'No', 'Process single document image'],
            ['GET', '/api/stats', 'No', 'Get processing statistics'],
            ['GET', '/api/processors', 'No', 'List available document processors'],
            ['GET', '/api/languages', 'No', 'List supported OCR languages'],
            ['GET', '/health', 'No', 'Basic health check'],
        ],
        col_widths=[18, 42, 15, 95]
    )

    # Enhanced API
    pdf.section_title('7.2 Enhanced API (/api/v2/*)')
    pdf.add_table(
        ['Method', 'Path', 'Auth', 'Description'],
        [
            ['POST', '/api/v2/scan', 'No', 'Enhanced scan with quality assessment'],
            ['POST', '/api/v2/classify', 'No', 'AI document classification only'],
            ['GET', '/api/v2/quality', 'No', 'Image quality analysis'],
            ['GET', '/api/v2/cache/stats', 'No', 'Cache hit/miss statistics'],
            ['GET', '/api/v2/health', 'No', 'Detailed health with dependencies'],
        ],
        col_widths=[18, 42, 15, 95]
    )

    # Improved API
    pdf.section_title('7.3 Improved API (/api/v3/*)')
    pdf.add_table(
        ['Method', 'Path', 'Auth', 'Description'],
        [
            ['POST', '/api/v3/scan', 'No', 'Latest scan with all enhancements'],
            ['GET', '/api/v3/health', 'No', 'Comprehensive health check'],
            ['GET', '/api/v3/processors', 'No', 'Detailed processor capabilities'],
        ],
        col_widths=[18, 42, 15, 95]
    )

    # Auth API
    pdf.section_title('7.4 Authentication API (/api/auth/*)')
    pdf.add_table(
        ['Method', 'Path', 'Auth', 'Description'],
        [
            ['POST', '/api/auth/register', 'No', 'Create new user account'],
            ['POST', '/api/auth/login', 'No', 'Authenticate and get tokens'],
            ['POST', '/api/auth/refresh', 'Refresh', 'Refresh access token'],
            ['GET', '/api/auth/profile', 'JWT', 'Get current user profile'],
            ['PUT', '/api/auth/profile', 'JWT', 'Update user profile'],
            ['GET', '/api/auth/admin/users', 'Admin', 'List all users (admin only)'],
            ['PUT', '/api/auth/admin/users/<id>', 'Admin', 'Modify user (admin only)'],
        ],
        col_widths=[18, 48, 16, 88]
    )

    # AI API
    pdf.section_title('7.5 AI API (/api/ai/*)')
    pdf.add_table(
        ['Method', 'Path', 'Auth', 'Description'],
        [
            ['POST', '/api/ai/classify', 'No', 'AI document classification'],
            ['POST', '/api/ai/vision/classify', 'No', 'Claude Vision classification'],
            ['POST', '/api/ai/feedback', 'JWT', 'Submit classification feedback'],
            ['GET', '/api/ai/metrics', 'No', 'AI performance metrics'],
            ['POST', '/api/ai/train', 'Admin', 'Trigger model retraining'],
        ],
        col_widths=[18, 48, 16, 88]
    )

    # Batch API
    pdf.section_title('7.6 Batch API (/api/batch/*)')
    pdf.add_table(
        ['Method', 'Path', 'Auth', 'Description'],
        [
            ['POST', '/api/batch/submit', 'JWT', 'Submit batch processing job'],
            ['GET', '/api/batch/status/<id>', 'JWT', 'Get batch job status'],
            ['GET', '/api/batch/results/<id>', 'JWT', 'Get batch job results'],
            ['POST', '/api/batch/cancel/<id>', 'JWT', 'Cancel a batch job'],
            ['GET', '/api/batch/export/<id>', 'JWT', 'Export results as CSV/JSON'],
        ],
        col_widths=[18, 48, 16, 88]
    )

    # Async API
    pdf.section_title('7.7 Async API (/api/async/*)')
    pdf.add_table(
        ['Method', 'Path', 'Auth', 'Description'],
        [
            ['POST', '/api/async/scan', 'No', 'Submit async scan (returns task ID)'],
            ['POST', '/api/async/batch', 'JWT', 'Submit async batch job'],
            ['GET', '/api/async/status/<id>', 'No', 'Check async task status'],
            ['POST', '/api/async/cancel/<id>', 'JWT', 'Cancel async task'],
        ],
        col_widths=[18, 48, 16, 88]
    )

    # Analytics API
    pdf.section_title('7.8 Analytics API (/analytics/*)')
    pdf.add_table(
        ['Method', 'Path', 'Auth', 'Description'],
        [
            ['GET', '/analytics/dashboard', 'No', 'Dashboard statistics and summaries'],
            ['GET', '/analytics/scan-history', 'No', 'Paginated scan history'],
            ['GET', '/analytics/document-stats', 'No', 'Per-document-type statistics'],
        ],
        col_widths=[18, 48, 16, 88]
    )

    # Monitoring
    pdf.section_title('7.9 Monitoring Endpoints')
    pdf.add_table(
        ['Method', 'Path', 'Auth', 'Description'],
        [
            ['GET', '/metrics', 'No', 'Prometheus metrics (text format)'],
            ['GET', '/api/metrics/summary', 'No', 'JSON metrics summary'],
        ],
        col_widths=[18, 48, 16, 88]
    )


def build_ch08(pdf):
    """Chapter 8: Security Architecture"""
    pdf.chapter_title(8, 'Security Architecture')

    pdf.section_title('8.1 JWT Token Lifecycle')
    pdf.ascii_diagram("""
  Client                          Server
    |                               |
    |  POST /api/auth/login         |
    |  {username, password}         |
    |------------------------------>|
    |                               |  Validate credentials
    |                               |  Check account lockout
    |                               |  Generate tokens
    |  {access_token, refresh_token}|
    |<------------------------------|
    |                               |
    |  GET /api/scan                |
    |  Authorization: Bearer <AT>   |
    |------------------------------>|
    |                               |  Verify JWT signature
    |                               |  Check expiry (24h)
    |  {scan result}                |
    |<------------------------------|
    |                               |
    |  --- Access token expires --- |
    |                               |
    |  POST /api/auth/refresh       |
    |  {refresh_token}              |
    |------------------------------>|
    |                               |  Verify refresh token
    |                               |  Check expiry (30d)
    |                               |  Generate new access token
    |  {new_access_token}           |
    |<------------------------------|
""", title='Figure 8.1: JWT Authentication Flow')

    pdf.section_title('8.2 Security Middleware Pipeline')
    pdf.body_text(
        'Every incoming request passes through an 8-layer security middleware pipeline '
        'defined in app/security/middleware.py:'
    )

    pdf.ascii_diagram("""
  Incoming Request
       |
       v
  [1] IP Allowlist/Blocklist Check
       |
       v
  [2] Rate Limiting (per IP + per endpoint)
       |
       v
  [3] Request Size Validation (max 16MB)
       |
       v
  [4] Security Headers Injection
       |  (X-Content-Type-Options, X-Frame-Options,
       |   X-XSS-Protection, Strict-Transport-Security)
       |
       v
  [5] JSON Content-Type Validation
       |
       v
  [6] Request Signing Verification (optional)
       |
       v
  [7] CORS Policy Enforcement
       |
       v
  [8] Response Security Headers
       |
       v
  Route Handler
""", title='Figure 8.2: Security Middleware Pipeline')

    pdf.section_title('8.3 Rate Limiting')
    pdf.add_table(
        ['Tier', 'Limit', 'Window', 'Scope'],
        [
            ['Standard', '100 requests', '1 minute', 'Per IP address'],
            ['Hourly', '500 requests', '1 hour', 'Per IP address'],
            ['Daily', '5,000 requests', '24 hours', 'Per IP address'],
            ['Auth', '20 requests', '1 minute', 'Login/register endpoints'],
            ['Upload', '30 requests', '1 minute', 'File upload endpoints'],
        ],
        col_widths=[30, 35, 30, 75]
    )

    pdf.section_title('8.4 File Upload Security')
    pdf.bullet_list([
        'Allowed extensions: .jpg, .jpeg, .png, .gif, .bmp, .tiff, .pdf',
        'Maximum file size: 16MB per file',
        'MIME type validation (content sniffing, not just extension)',
        'Filename sanitization (werkzeug.utils.secure_filename)',
        'Uploaded files stored in temporary directory, deleted after processing',
        'No file path traversal (absolute path construction)',
    ])

    pdf.section_title('8.5 Account Lockout')
    pdf.body_text(
        'After 5 failed login attempts within 15 minutes from the same IP address or '
        'username, the account is temporarily locked. The lockout duration is 15 minutes. '
        'Failed attempts are tracked in the LoginAttempt database table. '
        'Administrators can view and clear lockouts via the admin API.'
    )

    pdf.section_title('8.6 Production Security Enforcement')
    pdf.bullet_list([
        'SECRET_KEY must not be the default value in production (startup check)',
        'JWT_SECRET_KEY must be explicitly set in production',
        'Debug mode is disabled in production',
        'HTTPS is enforced via Nginx SSL termination',
        'Secure cookie flags (httponly, samesite, secure) in production',
    ])


def build_ch09(pdf):
    """Chapter 9: Infrastructure & Deployment"""
    pdf.chapter_title(9, 'Infrastructure & Deployment')

    pdf.section_title('9.1 Docker Multi-Stage Build')
    pdf.ascii_diagram("""
  +---------------------------+
  | Stage: base               |
  | python:3.11-slim          |
  | System deps, Tesseract    |
  +---------------------------+
              |
    +---------+---------+
    |                   |
    v                   v
  +----------------+  +----------------+
  | Stage: backend |  | Stage: frontend|
  | -builder       |  | node:18-alpine |
  | pip install    |  | npm install    |
  | requirements   |  | npm run build  |
  +----------------+  +----------------+
    |                   |
    +---------+---------+
              |
    +---------+---------+
    |                   |
    v                   v
  +----------------+  +----------------+
  | Stage: dev     |  | Stage: prod    |
  | Flask dev      |  | Gunicorn       |
  | server         |  | + static files |
  | (debug=True)   |  | (optimized)    |
  +----------------+  +----------------+
""", title='Figure 9.1: Docker Multi-Stage Build')

    pdf.section_title('9.2 Docker Compose Services')
    pdf.add_table(
        ['Service', 'Image', 'Ports', 'Depends On', 'Purpose'],
        [
            ['app', 'ocr-scanner:prod', '5001:5001', 'postgres, redis', 'Flask application'],
            ['postgres', 'postgres:15', '5432:5432', '-', 'Production database'],
            ['redis', 'redis:7-alpine', '6379:6379', '-', 'Cache and broker'],
            ['celery-worker', 'ocr-scanner:prod', '-', 'redis, postgres', 'Task worker (x2)'],
            ['celery-beat', 'ocr-scanner:prod', '-', 'redis', 'Scheduled tasks'],
            ['flower', 'ocr-scanner:prod', '5555:5555', 'redis', 'Celery monitoring'],
            ['nginx', 'nginx:1.25', '80, 443', 'app', 'Reverse proxy'],
        ],
        col_widths=[28, 32, 24, 32, 54]
    )

    pdf.section_title('9.3 Nginx Configuration')
    pdf.body_text(
        'Nginx serves as the reverse proxy with SSL termination, rate limiting, '
        'and load balancing capabilities.'
    )

    pdf.add_table(
        ['Feature', 'Configuration', 'Details'],
        [
            ['SSL', 'TLS 1.2+', 'Certificate and key in /etc/nginx/ssl/'],
            ['Rate Limit Zone 1', 'general: 10r/s', 'Global request rate limit'],
            ['Rate Limit Zone 2', 'api: 20r/s', 'API endpoint rate limit'],
            ['Rate Limit Zone 3', 'upload: 5r/s', 'File upload rate limit'],
            ['Upstream', 'app:5001', 'Load balance to Flask/Gunicorn'],
            ['WebSocket', '/socket.io/', 'Upgrade headers for WS proxy'],
            ['Static Files', '/static/', 'Serve frontend build directly'],
            ['Timeouts', '120s proxy_read', 'Long timeout for OCR processing'],
        ],
        col_widths=[35, 35, 100]
    )

    pdf.section_title('9.4 CI/CD Pipeline (GitHub Actions)')
    pdf.ascii_diagram("""
  Push / PR to main
        |
        v
  +-------------------+     +-------------------+
  | Stage 1: Test     |     | Stage 2: Security |
  |                   |     |                   |
  | - pytest          | --> | - pip-audit       |
  | - flake8 lint     |     | - safety check    |
  | - coverage report |     | - bandit scan     |
  +-------------------+     +-------------------+
                                    |
                                    v
                            +-------------------+
                            | Stage 3: Build    |
                            |                   |
                            | - Docker build    |
                            | - Push to registry|
                            +-------------------+
                                    |
                                    v
                            +-------------------+
                            | Stage 4: Deploy   |
                            |                   |
                            | - docker-compose  |
                            | - health check    |
                            | - rollback on fail|
                            +-------------------+
""", title='Figure 9.2: CI/CD Pipeline')

    pdf.section_title('9.5 Environment Variables')
    pdf.add_table(
        ['Variable', 'Default', 'Description'],
        [
            ['SECRET_KEY', 'dev-secret-key', 'Flask secret key (MUST change in prod)'],
            ['JWT_SECRET_KEY', 'jwt-secret-key', 'JWT signing key (MUST change in prod)'],
            ['DATABASE_URL', 'sqlite:///ocr_scanner.db', 'Database connection string'],
            ['REDIS_URL', 'redis://localhost:6379/0', 'Redis connection URL'],
            ['CELERY_BROKER_URL', 'redis://localhost:6379/1', 'Celery broker URL'],
            ['ANTHROPIC_API_KEY', '(none)', 'Claude Vision API key'],
            ['FLASK_ENV', 'development', 'Flask environment mode'],
            ['LOG_LEVEL', 'INFO', 'Application log level'],
            ['MAX_CONTENT_LENGTH', '16777216', 'Max upload size (16MB)'],
            ['GUNICORN_WORKERS', '2', 'Number of Gunicorn workers'],
        ],
        col_widths=[40, 45, 85]
    )


def build_ch10(pdf):
    """Chapter 10: Monitoring & Observability"""
    pdf.chapter_title(10, 'Monitoring & Observability')

    pdf.section_title('10.1 Prometheus Metrics')
    pdf.body_text(
        'The monitoring module (app/monitoring.py) exposes Prometheus-compatible metrics '
        'at the /metrics endpoint. Eight metric families cover all critical system indicators.'
    )

    pdf.add_table(
        ['Metric Name', 'Type', 'Labels', 'Description'],
        [
            ['http_requests_total', 'Counter', 'method, endpoint, status', 'Total HTTP requests'],
            ['http_request_duration_seconds', 'Histogram', 'method, endpoint', 'Request latency'],
            ['http_requests_active', 'Gauge', '-', 'Currently active requests'],
            ['ocr_processing_time_seconds', 'Histogram', 'document_type', 'OCR processing duration'],
            ['ocr_errors_total', 'Counter', 'error_type', 'Total OCR processing errors'],
            ['db_query_duration_seconds', 'Histogram', 'operation', 'Database query latency'],
            ['cache_hits_total', 'Counter', 'cache_type', 'Cache hit count'],
            ['cache_misses_total', 'Counter', 'cache_type', 'Cache miss count'],
        ],
        col_widths=[48, 22, 42, 58]
    )

    pdf.section_title('10.2 Structured Logging')
    pdf.body_text(
        'Application logs use JSON format via pythonjsonlogger for structured querying. '
        'Logs are written to rotating files and stdout.'
    )

    pdf.add_table(
        ['Parameter', 'Value', 'Description'],
        [
            ['Format', 'JSON', 'Structured JSON log entries'],
            ['Library', 'pythonjsonlogger', 'Python JSON logging formatter'],
            ['File Path', 'backend/logs/app.log', 'Primary log file'],
            ['Max File Size', '1 MB', 'Size before rotation'],
            ['Backup Count', '10', 'Number of rotated log files'],
            ['Console Output', 'StreamHandler', 'Also log to stdout'],
            ['Log Level', 'INFO (default)', 'Configurable via LOG_LEVEL env var'],
        ],
        col_widths=[35, 40, 95]
    )

    pdf.body_text('Example log entry:')
    pdf.code_block("""{
  "timestamp": "2026-02-22T10:30:45.123Z",
  "level": "INFO",
  "logger": "app.routes",
  "message": "Document processed successfully",
  "document_type": "aadhaar_card",
  "processing_time": 1.234,
  "confidence": 0.95,
  "request_id": "abc123"
}""")

    pdf.section_title('10.3 Health Endpoints')
    pdf.add_table(
        ['Endpoint', 'Level', 'Checks'],
        [
            ['/health', 'Basic', 'App is running'],
            ['/api/v2/health', 'Standard', 'App + database connectivity'],
            ['/api/v3/health', 'Comprehensive', 'App + DB + Redis + Celery + disk space'],
            ['/metrics', 'Prometheus', 'All metric families in text format'],
            ['/api/metrics/summary', 'JSON', 'Aggregated metrics summary'],
        ],
        col_widths=[42, 30, 98]
    )

    pdf.section_title('10.4 Celery Monitoring (Flower)')
    pdf.body_text(
        'Flower provides a web-based dashboard for monitoring Celery workers and tasks. '
        'It runs as a separate service in Docker Compose on port 5555 and offers:'
    )
    pdf.bullet_list([
        'Real-time worker status (online, offline, heartbeat)',
        'Task history with execution times and results',
        'Queue depth monitoring for all 5 queues',
        'Worker resource usage (CPU, memory)',
        'Task rate graphs and success/failure ratios',
    ])


def build_ch11(pdf):
    """Chapter 11: Performance Optimizations"""
    pdf.chapter_title(11, 'Performance Optimizations')

    pdf.section_title('11.1 Caching Strategy')
    pdf.body_text(
        'Multi-layer caching minimizes redundant computation and external API calls:'
    )
    pdf.bullet_list([
        'Vision API Cache: Results cached by image content hash (SHA-256). TTL: 1 hour. '
        'Eliminates redundant Claude Vision API calls for identical images.',
        'OCR Result Cache: Tesseract OCR results cached for 30 minutes. '
        'Prevents re-processing of recently scanned documents.',
        'Processor Detection Cache: Document type detection results cached in-memory '
        'for fast repeated lookups within the same request lifecycle.',
        'Static Asset Cache: Frontend build files served by Nginx with aggressive '
        'cache headers (1 year for hashed assets).',
    ])

    pdf.section_title('11.2 Database Connection Pooling')
    pdf.body_text(
        'SQLAlchemy connection pooling eliminates connection creation overhead. '
        'The pool maintains 20 persistent connections with up to 40 overflow connections. '
        'Connection health is verified before use (pool_pre_ping=True) to handle '
        'stale connections from PostgreSQL timeouts or restarts.'
    )

    pdf.section_title('11.3 Async Task Offloading')
    pdf.body_text(
        'Long-running operations are offloaded to Celery workers to keep the web server '
        'responsive. This includes batch processing, large PDF documents, and AI classification '
        'requests. The web server returns immediately with a task ID, and clients poll for '
        'results or receive them via WebSocket.'
    )

    pdf.section_title('11.4 Gunicorn Configuration')
    pdf.add_table(
        ['Parameter', 'Value', 'Rationale'],
        [
            ['workers', '2', 'CPU-bound OCR; 2 workers per core'],
            ['worker_class', 'eventlet', 'Async support for Socket.IO'],
            ['timeout', '120', 'Long timeout for OCR processing'],
            ['max_requests', '1000', 'Worker recycling to prevent memory leaks'],
            ['max_requests_jitter', '50', 'Stagger worker restarts'],
            ['graceful_timeout', '30', 'Time for in-flight requests to complete'],
            ['keep_alive', '5', 'Keep-alive timeout in seconds'],
        ],
        col_widths=[38, 25, 107]
    )

    pdf.section_title('11.5 Image Preprocessing Optimizations')
    pdf.bullet_list([
        'Images resized to optimal dimensions before OCR (max 2000px width)',
        'Grayscale conversion reduces processing time by ~30%',
        'Adaptive thresholding produces cleaner text regions',
        'Gaussian blur removes noise without losing text edges',
        'Document edge detection and dewarping improve OCR accuracy on photos',
        'Per-processor preprocessing applies document-specific optimizations',
    ])


def build_ch12(pdf):
    """Chapter 12: Data Flow Diagrams"""
    pdf.chapter_title(12, 'Data Flow Diagrams')

    pdf.section_title('12.1 Single Document Scan Flow')
    pdf.ascii_diagram("""
  User uploads image
        |
        v
  +-------------------+
  | Frontend          |
  | - File validation |
  | - Preview display |
  | - Upload via Axios|
  +-------------------+
        |
        | POST /api/scan (multipart/form-data)
        v
  +-------------------+
  | Backend Route     |
  | - Size check      |
  | - Extension check |
  | - MIME validation  |
  +-------------------+
        |
        v
  +-------------------+     +-------------------+
  | Image Preprocess  |     | Quality Check     |
  | - Resize          |---->| - Blur score      |
  | - Grayscale       |     | - Brightness      |
  | - Denoise         |     | - Contrast        |
  | - Dewarp          |     | - Resolution      |
  +-------------------+     +-------------------+
        |                           |
        v                           v
  +-------------------+     +-------------------+
  | Tesseract OCR     |     | Quality Report    |
  | - Text extraction |     | (included in      |
  | - Confidence map  |     |  response)        |
  +-------------------+     +-------------------+
        |
        v
  +-------------------+
  | Document Detection|
  | - Registry scan   |
  | - AI fallback     |
  +-------------------+
        |
        v
  +-------------------+
  | Data Extraction   |
  | - Regex patterns  |
  | - Field mapping   |
  | - Confidence calc |
  +-------------------+
        |
        v
  +-------------------+
  | Save to DB        |
  | - ScanHistory     |
  | - DocumentStats   |
  +-------------------+
        |
        v
  JSON Response to Client
  {document_type, extracted_data,
   confidence, quality_score, ...}
""", title='Figure 12.1: Single Document Scan Flow')

    pdf.section_title('12.2 Batch Processing Flow')
    pdf.ascii_diagram("""
  User uploads N documents
        |
        v
  +-------------------+
  | POST /api/batch/  |
  | submit            |
  | - Create job      |
  | - Generate job_id |
  +-------------------+
        |
        | Return job_id immediately
        | (HTTP 202 Accepted)
        |
        v
  +-------------------+
  | Celery Task Queue |
  | (batch_processing)|
  +-------------------+
        |
        |  For each document:
        v
  +-------------------+     +-------------------+
  | Worker: Process   |     | WebSocket Update  |
  | - Preprocess      |---->| - progress %      |
  | - OCR             |     | - current doc     |
  | - Detect + Extract|     | - estimated time  |
  +-------------------+     +-------------------+
        |
        | All documents done
        v
  +-------------------+     +-------------------+
  | Aggregate Results |     | Webhook Callback  |
  | - Per-doc results |---->| POST to webhook   |
  | - Summary stats   |     | URL (if set)      |
  | - Export formats   |     +-------------------+
  +-------------------+
        |
        v
  +-------------------+
  | Update DB         |
  | - BatchJob status |
  | - ScanHistory x N |
  +-------------------+
        |
        v
  WebSocket: batch_complete
  GET /api/batch/results/{id}
""", title='Figure 12.2: Batch Processing Flow')

    pdf.section_title('12.3 AI Classification Flow')
    pdf.ascii_diagram("""
  Document Image
        |
        v
  +-------------------+
  | Cache Lookup      |
  | Key: SHA-256 hash |
  +-------------------+
        |
    +---+---+
    |       |
  Cache   Cache
  HIT     MISS
    |       |
    v       v
  Return  +-------------------+
  cached  | ML Classifier     |
  result  | (scikit-learn)    |
          | TF-IDF + SVM     |
          +-------------------+
                |
            +---+---+
            |       |
         >= 0.8  < 0.8
         conf.   conf.
            |       |
            v       v
          Use ML  +-------------------+
          result  | Claude Vision API |
                  | - Base64 encode   |
                  | - Classification  |
                  |   prompt          |
                  +-------------------+
                        |
                        v
                  +-------------------+
                  | Cross-validate    |
                  | ML vs Vision      |
                  | Merge results     |
                  +-------------------+
                        |
                        v
                  +-------------------+
                  | Cache Result      |
                  | TTL: 3600s        |
                  +-------------------+
                        |
                        v
                  Classification Result
""", title='Figure 12.3: AI Classification Flow')

    pdf.section_title('12.4 Authentication Flow')
    pdf.ascii_diagram("""
  +------------------+                    +------------------+
  |   React Client   |                    |   Flask Backend  |
  +------------------+                    +------------------+
         |                                        |
         |  1. POST /api/auth/login               |
         |  {username, password}                   |
         |--------------------------------------->|
         |                                        |
         |                    2. Validate credentials
         |                    3. Check lockout status
         |                    4. Hash password compare (bcrypt)
         |                                        |
         |  5. {access_token, refresh_token}      |
         |<---------------------------------------|
         |                                        |
         |  6. Store tokens in localStorage       |
         |                                        |
         |  7. API Request                        |
         |  Authorization: Bearer <access_token>  |
         |--------------------------------------->|
         |                    8. Verify JWT        |
         |                    9. Extract user_id   |
         |  10. Response                          |
         |<---------------------------------------|
         |                                        |
         |  11. Access token expires (24h)        |
         |  12. 401 Unauthorized                  |
         |<---------------------------------------|
         |                                        |
         |  13. POST /api/auth/refresh            |
         |  {refresh_token}                       |
         |--------------------------------------->|
         |                    14. Verify refresh   |
         |  15. {new_access_token}                |
         |<---------------------------------------|
         |                                        |
         |  16. Retry original request            |
         |  (Axios interceptor automatic)         |
         |--------------------------------------->|
""", title='Figure 12.4: Authentication Flow')


def build_ch13(pdf):
    """Chapter 13: Appendices"""
    pdf.chapter_title(13, 'Appendices')

    # Appendix A
    pdf.section_title('Appendix A: Supported Document Types')
    pdf.add_table(
        ['#', 'Document', 'Country', 'Key Fields Extracted'],
        [
            ['1', 'Aadhaar Card', 'India', 'Aadhaar number, name, DOB, gender, address'],
            ['2', 'Emirates ID', 'UAE', 'ID number, name (EN/AR), nationality, DOB, expiry'],
            ['3', 'Passport', 'Multi', 'Passport no., name, nationality, DOB, place of birth, MRZ'],
            ['4', 'Driving License', 'India', 'DL number, name, DOB, address, validity, vehicle class'],
            ['5', "US Driver's License", 'USA', 'DL number, name, DOB, address, expiry, class'],
            ['6', 'PAN Card', 'India', 'PAN number, name, DOB, father name'],
            ['7', 'Voter ID', 'India', 'EPIC number, name, DOB, address, father name'],
            ['8', 'Ration Card', 'India', 'Card number, head of family, members, address'],
            ['9', 'Birth Certificate', 'India', 'Certificate no., name, DOB, place, parents'],
            ['10', 'SSN Card', 'USA', 'SSN number, name'],
            ['11', 'Medicare Card', 'Australia', 'Medicare no., name, card number, expiry'],
            ['12', 'NHS Card', 'UK', 'NHS number, name, DOB'],
            ['13', 'EU ID Card', 'EU', 'ID number, name, nationality, DOB, expiry'],
            ['14', 'Canadian DL', 'Canada', 'License no., name, DOB, address, class, expiry'],
        ],
        col_widths=[8, 35, 18, 109]
    )

    # Appendix B
    pdf.section_title('Appendix B: Complete Environment Variable Reference')
    pdf.add_table(
        ['Variable', 'Required', 'Default', 'Description'],
        [
            ['SECRET_KEY', 'Prod', 'dev-secret-key', 'Flask session secret'],
            ['JWT_SECRET_KEY', 'Prod', 'jwt-secret-key', 'JWT signing secret'],
            ['DATABASE_URL', 'No', 'sqlite:///ocr_scanner.db', 'Database URL'],
            ['REDIS_URL', 'No', 'redis://localhost:6379/0', 'Redis URL'],
            ['CELERY_BROKER_URL', 'No', 'redis://localhost:6379/1', 'Celery broker'],
            ['CELERY_RESULT_BACKEND', 'No', 'redis://localhost:6379/2', 'Celery results'],
            ['ANTHROPIC_API_KEY', 'For AI', '(none)', 'Claude API key'],
            ['FLASK_ENV', 'No', 'development', 'Environment mode'],
            ['LOG_LEVEL', 'No', 'INFO', 'Logging level'],
            ['MAX_CONTENT_LENGTH', 'No', '16777216', 'Max upload bytes'],
            ['GUNICORN_WORKERS', 'No', '2', 'Worker count'],
            ['GUNICORN_TIMEOUT', 'No', '120', 'Request timeout (s)'],
            ['CORS_ORIGINS', 'No', '*', 'Allowed CORS origins'],
            ['RATE_LIMIT_PER_MINUTE', 'No', '100', 'Requests/minute'],
            ['RATE_LIMIT_PER_HOUR', 'No', '500', 'Requests/hour'],
            ['RATE_LIMIT_PER_DAY', 'No', '5000', 'Requests/day'],
        ],
        col_widths=[42, 16, 42, 70]
    )

    # Appendix C
    pdf.section_title('Appendix C: Glossary')
    pdf.add_table(
        ['Term', 'Definition'],
        [
            ['OCR', 'Optical Character Recognition - converting images of text to machine-readable text'],
            ['JWT', 'JSON Web Token - compact token format for stateless authentication'],
            ['MRZ', 'Machine Readable Zone - standardized text at bottom of passports/travel docs'],
            ['pHash', 'Perceptual Hash - image fingerprint that tolerates minor visual changes'],
            ['PWA', 'Progressive Web App - web app with native-like capabilities (offline, install)'],
            ['TF-IDF', 'Term Frequency-Inverse Document Frequency - text feature extraction method'],
            ['SVM', 'Support Vector Machine - ML classification algorithm'],
            ['WSGI', 'Web Server Gateway Interface - Python web server standard'],
            ['ORM', 'Object-Relational Mapping - database abstraction layer'],
            ['WebSocket', 'Full-duplex communication protocol over a single TCP connection'],
            ['Celery', 'Distributed task queue for async processing in Python'],
            ['Redis', 'In-memory data structure store used as cache and message broker'],
        ],
        col_widths=[25, 145]
    )


# ======================================================================
# Main entry point
# ======================================================================

def main():
    print("Generating OCR Document Scanner Technical Architecture PDF...")
    print("=" * 60)

    pdf = ArchitecturePDF()
    pdf.alias_nb_pages()
    pdf.set_title('OCR Document Scanner - Technical Architecture')
    pdf.set_author('OCR Document Scanner Team')
    pdf.set_subject('Technical Architecture Document')

    # Build all chapters
    steps = [
        ("Cover page", lambda: pdf.cover_page()),
        ("Table of Contents", lambda: pdf.build_toc()),
        ("Chapter 1: Executive Summary", lambda: build_ch01(pdf)),
        ("Chapter 2: System Architecture", lambda: build_ch02(pdf)),
        ("Chapter 3: Technology Stack", lambda: build_ch03(pdf)),
        ("Chapter 4: Backend Architecture", lambda: build_ch04(pdf)),
        ("Chapter 5: Frontend Architecture", lambda: build_ch05(pdf)),
        ("Chapter 6: Database Architecture", lambda: build_ch06(pdf)),
        ("Chapter 7: API Reference", lambda: build_ch07(pdf)),
        ("Chapter 8: Security Architecture", lambda: build_ch08(pdf)),
        ("Chapter 9: Infrastructure & Deployment", lambda: build_ch09(pdf)),
        ("Chapter 10: Monitoring & Observability", lambda: build_ch10(pdf)),
        ("Chapter 11: Performance Optimizations", lambda: build_ch11(pdf)),
        ("Chapter 12: Data Flow Diagrams", lambda: build_ch12(pdf)),
        ("Chapter 13: Appendices", lambda: build_ch13(pdf)),
    ]

    for i, (name, builder) in enumerate(steps):
        print(f"  [{i+1:2d}/{len(steps)}] Building {name}...")
        builder()

    # Output
    output_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(output_dir, 'OCR_Document_Scanner_Architecture.pdf')

    print(f"\nWriting PDF to: {output_path}")
    pdf.output(output_path)

    file_size = os.path.getsize(output_path) / 1024
    print(f"PDF generated successfully!")
    print(f"  File: {output_path}")
    print(f"  Size: {file_size:.1f} KB")
    print(f"  Pages: {pdf.page_no()}")
    print("=" * 60)


if __name__ == '__main__':
    main()

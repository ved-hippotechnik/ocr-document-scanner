# OCR Document Scanner

This application is designed to scan and extract information from various documents, particularly national IDs and passports. It uses OCR (Optical Character Recognition) technology to read text from documents and MRZ (Machine Readable Zone) parsing for passports and other travel documents.

## Features

- Document scanning and text extraction using OCR
- MRZ (Machine Readable Zone) reading for passports and ID cards
- Document type identification (passport, ID card, etc.)
- Nationality detection
- Dashboard with statistics and visualization
- Camera integration for capturing document images
- Responsive UI built with React and Material UI

## Project Structure

```
ocr-document-scanner/
├── frontend/                # React frontend
│   ├── public/              # Public assets
│   └── src/                 # Source files
│       ├── components/      # Reusable components
│       ├── pages/           # Page components
│       └── utils/           # Utility functions
└── backend/                 # Python Flask backend
    ├── app/                 # Flask application
    │   ├── __init__.py      # App initialization
    │   └── routes.py        # API routes
    ├── models/              # Data models
    ├── utils/               # Utility functions
    └── requirements.txt     # Python dependencies
```

## Prerequisites

- Node.js and npm
- Python 3.6+
- Tesseract OCR engine

### Installing Tesseract OCR

#### macOS
```
brew install tesseract
```

#### Linux
```
sudo apt-get install tesseract-ocr
```

#### Windows
Download and install from: https://github.com/UB-Mannheim/tesseract/wiki

## Installation

### Backend Setup

1. Navigate to the backend directory:
```
cd backend
```

2. Create a virtual environment (optional but recommended):
```
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```
pip install -r requirements.txt
```

4. Run the Flask server:
```
python run.py
```

The backend server will start at http://localhost:5000

### Frontend Setup

1. Navigate to the frontend directory:
```
cd frontend
```

2. Install dependencies:
```
npm install
```

3. Start the development server:
```
npm start
```

The frontend will be available at http://localhost:3000

## Usage

1. Open your browser and navigate to http://localhost:3000
2. Use the Scanner page to upload or capture document images
3. The application will process the image, extract information, and display the results
4. View statistics and scan history on the Dashboard page

## Technologies Used

- **Frontend**: React, Material UI, Chart.js
- **Backend**: Flask, Python
- **OCR**: Tesseract, OpenCV
- **MRZ Reading**: PassportEye

## License

MIT

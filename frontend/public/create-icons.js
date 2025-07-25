// Icon creation script for PWA
// This creates SVG icons that can be used for the PWA manifest
// In production, you would replace these with proper PNG/ICO files

const fs = require('fs');
const path = require('path');

// Create a simple OCR Scanner icon as SVG
const createSVGIcon = (size) => `
<svg width="${size}" height="${size}" viewBox="0 0 ${size} ${size}" xmlns="http://www.w3.org/2000/svg">
  <rect width="${size}" height="${size}" fill="#007AFF" rx="${size * 0.1}"/>
  <g fill="white">
    <!-- Document shape -->
    <rect x="${size * 0.2}" y="${size * 0.15}" width="${size * 0.6}" height="${size * 0.7}" rx="${size * 0.05}" fill="none" stroke="white" stroke-width="${size * 0.02}"/>
    
    <!-- Text lines -->
    <line x1="${size * 0.25}" y1="${size * 0.25}" x2="${size * 0.75}" y2="${size * 0.25}" stroke="white" stroke-width="${size * 0.015}"/>
    <line x1="${size * 0.25}" y1="${size * 0.35}" x2="${size * 0.65}" y2="${size * 0.35}" stroke="white" stroke-width="${size * 0.015}"/>
    <line x1="${size * 0.25}" y1="${size * 0.45}" x2="${size * 0.7}" y2="${size * 0.45}" stroke="white" stroke-width="${size * 0.015}"/>
    <line x1="${size * 0.25}" y1="${size * 0.55}" x2="${size * 0.6}" y2="${size * 0.55}" stroke="white" stroke-width="${size * 0.015}"/>
    
    <!-- Scan line -->
    <line x1="${size * 0.1}" y1="${size * 0.65}" x2="${size * 0.9}" y2="${size * 0.65}" stroke="#34C759" stroke-width="${size * 0.025}"/>
    
    <!-- Scanner beam -->
    <circle cx="${size * 0.5}" cy="${size * 0.65}" r="${size * 0.03}" fill="#34C759"/>
  </g>
</svg>
`;

// Create the HTML file to generate actual PNG icons
const createIconHTML = () => `
<!DOCTYPE html>
<html>
<head>
    <title>Icon Generator</title>
    <script>
        function generateIcon(size) {
            const canvas = document.createElement('canvas');
            canvas.width = size;
            canvas.height = size;
            const ctx = canvas.getContext('2d');
            
            // Background
            ctx.fillStyle = '#007AFF';
            ctx.roundRect(0, 0, size, size, size * 0.1);
            ctx.fill();
            
            // Document
            ctx.strokeStyle = 'white';
            ctx.lineWidth = size * 0.02;
            ctx.roundRect(size * 0.2, size * 0.15, size * 0.6, size * 0.7, size * 0.05);
            ctx.stroke();
            
            // Text lines
            ctx.strokeStyle = 'white';
            ctx.lineWidth = size * 0.015;
            ctx.beginPath();
            ctx.moveTo(size * 0.25, size * 0.25);
            ctx.lineTo(size * 0.75, size * 0.25);
            ctx.moveTo(size * 0.25, size * 0.35);
            ctx.lineTo(size * 0.65, size * 0.35);
            ctx.moveTo(size * 0.25, size * 0.45);
            ctx.lineTo(size * 0.7, size * 0.45);
            ctx.moveTo(size * 0.25, size * 0.55);
            ctx.lineTo(size * 0.6, size * 0.55);
            ctx.stroke();
            
            // Scan line
            ctx.strokeStyle = '#34C759';
            ctx.lineWidth = size * 0.025;
            ctx.beginPath();
            ctx.moveTo(size * 0.1, size * 0.65);
            ctx.lineTo(size * 0.9, size * 0.65);
            ctx.stroke();
            
            // Scanner dot
            ctx.fillStyle = '#34C759';
            ctx.beginPath();
            ctx.arc(size * 0.5, size * 0.65, size * 0.03, 0, 2 * Math.PI);
            ctx.fill();
            
            return canvas.toDataURL('image/png');
        }
        
        // Add roundRect method if it doesn't exist
        if (!CanvasRenderingContext2D.prototype.roundRect) {
            CanvasRenderingContext2D.prototype.roundRect = function(x, y, width, height, radius) {
                this.beginPath();
                this.moveTo(x + radius, y);
                this.arcTo(x + width, y, x + width, y + height, radius);
                this.arcTo(x + width, y + height, x, y + height, radius);
                this.arcTo(x, y + height, x, y, radius);
                this.arcTo(x, y, x + width, y, radius);
                this.closePath();
            };
        }
        
        function downloadIcon(size, filename) {
            const dataURL = generateIcon(size);
            const link = document.createElement('a');
            link.download = filename;
            link.href = dataURL;
            link.click();
        }
        
        window.onload = function() {
            // Generate and download icons
            downloadIcon(192, 'icon-192.png');
            downloadIcon(512, 'icon-512.png');
            
            // Generate favicon
            const canvas = document.createElement('canvas');
            canvas.width = 32;
            canvas.height = 32;
            const ctx = canvas.getContext('2d');
            
            ctx.fillStyle = '#007AFF';
            ctx.fillRect(0, 0, 32, 32);
            
            ctx.fillStyle = 'white';
            ctx.fillRect(6, 4, 20, 24);
            
            ctx.fillStyle = '#007AFF';
            ctx.fillRect(8, 6, 16, 2);
            ctx.fillRect(8, 10, 12, 2);
            ctx.fillRect(8, 14, 14, 2);
            ctx.fillRect(8, 18, 10, 2);
            
            ctx.fillStyle = '#34C759';
            ctx.fillRect(2, 20, 28, 2);
            
            canvas.toBlob(function(blob) {
                const url = URL.createObjectURL(blob);
                const link = document.createElement('a');
                link.download = 'favicon.ico';
                link.href = url;
                link.click();
            });
        };
    </script>
</head>
<body>
    <h1>OCR Scanner Icons</h1>
    <p>Icons will be generated and downloaded automatically.</p>
    <p>Please save the generated files to the public directory:</p>
    <ul>
        <li>icon-192.png</li>
        <li>icon-512.png</li>
        <li>favicon.ico</li>
    </ul>
</body>
</html>
`;

// Write the icon generator HTML
fs.writeFileSync(path.join(__dirname, 'generate-icons.html'), createIconHTML());

console.log('Icon generator created! Open generate-icons.html in a browser to create the icon files.');
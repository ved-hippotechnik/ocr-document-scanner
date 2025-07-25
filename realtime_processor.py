#!/usr/bin/env python3
"""
Real-time Document Processing System
Provides real-time OCR processing with WebSocket integration and live streaming capabilities
"""

import asyncio
import websockets
import json
import cv2
import numpy as np
import base64
import time
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
import queue
import threading
from concurrent.futures import ThreadPoolExecutor
import io
from PIL import Image

# OCR processing
import pytesseract

# WebSocket server
try:
    import websockets
    from websockets.server import serve
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ProcessingFrame:
    """Frame data for processing"""
    frame_id: str
    timestamp: float
    image_data: np.ndarray
    metadata: Dict[str, Any]

@dataclass
class ProcessingResult:
    """Result from real-time processing"""
    frame_id: str
    timestamp: float
    processing_time: float
    document_type: str
    confidence: float
    extracted_text: str
    extracted_fields: Dict[str, Any]
    quality_score: float
    status: str
    error_message: Optional[str] = None

@dataclass
class QualityMetrics:
    """Image quality metrics"""
    sharpness: float
    brightness: float
    contrast: float
    noise_level: float
    overall_quality: float

class LiveQualityAssessment:
    """Real-time quality assessment for incoming frames"""
    
    def __init__(self):
        self.quality_history = []
        self.quality_threshold = 0.6
        
    def assess_frame_quality(self, image: np.ndarray) -> QualityMetrics:
        """Assess quality of incoming frame"""
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
            
        # 1. Sharpness assessment using Laplacian variance
        sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()
        sharpness_score = min(sharpness / 1000, 1.0)  # Normalize
        
        # 2. Brightness assessment
        brightness = np.mean(gray)
        brightness_score = 1.0 - abs(brightness - 127) / 127  # Optimal around 127
        
        # 3. Contrast assessment
        contrast = np.std(gray)
        contrast_score = min(contrast / 64, 1.0)  # Normalize
        
        # 4. Noise level assessment
        noise_level = self._estimate_noise_level(gray)
        noise_score = max(0, 1.0 - noise_level / 20)  # Lower noise is better
        
        # 5. Overall quality score
        overall_quality = (sharpness_score + brightness_score + contrast_score + noise_score) / 4
        
        metrics = QualityMetrics(
            sharpness=sharpness_score,
            brightness=brightness_score,
            contrast=contrast_score,
            noise_level=noise_score,
            overall_quality=overall_quality
        )
        
        self.quality_history.append(metrics)
        if len(self.quality_history) > 100:  # Keep last 100 assessments
            self.quality_history.pop(0)
            
        return metrics
    
    def _estimate_noise_level(self, gray: np.ndarray) -> float:
        """Estimate noise level in image"""
        # Use difference between image and gaussian filtered version
        filtered = cv2.GaussianBlur(gray, (5, 5), 0)
        noise = np.abs(gray.astype(np.float32) - filtered.astype(np.float32))
        return np.mean(noise)
    
    def is_quality_acceptable(self, metrics: QualityMetrics) -> bool:
        """Check if quality is acceptable for processing"""
        return metrics.overall_quality >= self.quality_threshold
    
    def get_quality_feedback(self, metrics: QualityMetrics) -> Dict[str, Any]:
        """Generate quality feedback for user"""
        feedback = {
            'overall_score': metrics.overall_quality,
            'is_acceptable': self.is_quality_acceptable(metrics),
            'suggestions': []
        }
        
        if metrics.sharpness < 0.5:
            feedback['suggestions'].append("Hold camera steady - image is blurry")
        if metrics.brightness < 0.5:
            feedback['suggestions'].append("Increase lighting - image is too dark")
        if metrics.contrast < 0.5:
            feedback['suggestions'].append("Improve contrast - image lacks definition")
        if metrics.noise_level < 0.5:
            feedback['suggestions'].append("Reduce noise - improve image quality")
        
        if not feedback['suggestions']:
            feedback['suggestions'].append("Image quality is good")
            
        return feedback

class StreamingOCRProcessor:
    """Real-time OCR processing for video streams"""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.processing_queue = queue.Queue(maxsize=10)
        self.result_callbacks = []
        self.is_running = False
        self.stats = {
            'frames_processed': 0,
            'total_processing_time': 0,
            'successful_extractions': 0
        }
        
    def start_processing(self):
        """Start the real-time processing"""
        self.is_running = True
        self.processing_thread = threading.Thread(target=self._processing_loop)
        self.processing_thread.start()
        logger.info("Real-time OCR processing started")
        
    def stop_processing(self):
        """Stop the real-time processing"""
        self.is_running = False
        if hasattr(self, 'processing_thread'):
            self.processing_thread.join()
        self.executor.shutdown(wait=True)
        logger.info("Real-time OCR processing stopped")
        
    def add_frame(self, frame: ProcessingFrame) -> bool:
        """Add frame to processing queue"""
        try:
            self.processing_queue.put_nowait(frame)
            return True
        except queue.Full:
            logger.warning("Processing queue is full, dropping frame")
            return False
            
    def add_result_callback(self, callback: Callable[[ProcessingResult], None]):
        """Add callback for processing results"""
        self.result_callbacks.append(callback)
        
    def _processing_loop(self):
        """Main processing loop"""
        while self.is_running:
            try:
                frame = self.processing_queue.get(timeout=1.0)
                
                # Submit frame for processing
                future = self.executor.submit(self._process_frame, frame)
                
                # Handle result asynchronously
                future.add_done_callback(self._handle_result)
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error in processing loop: {e}")
                
    def _process_frame(self, frame: ProcessingFrame) -> ProcessingResult:
        """Process a single frame"""
        start_time = time.time()
        
        try:
            # Convert image for OCR
            if len(frame.image_data.shape) == 3:
                # Convert BGR to RGB for PIL
                rgb_image = cv2.cvtColor(frame.image_data, cv2.COLOR_BGR2RGB)
                pil_image = Image.fromarray(rgb_image)
            else:
                pil_image = Image.fromarray(frame.image_data)
            
            # Perform OCR
            extracted_text = pytesseract.image_to_string(pil_image)
            
            # Get confidence data
            try:
                data = pytesseract.image_to_data(pil_image, output_type=pytesseract.Output.DICT)
                confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            except:
                avg_confidence = 0.5
            
            # Basic document type detection
            document_type = self._detect_document_type(extracted_text)
            
            # Extract fields
            extracted_fields = self._extract_fields(extracted_text, document_type)
            
            # Calculate quality score
            quality_score = self._calculate_quality_score(frame.image_data, extracted_text)
            
            processing_time = time.time() - start_time
            
            # Update statistics
            self.stats['frames_processed'] += 1
            self.stats['total_processing_time'] += processing_time
            if extracted_text.strip():
                self.stats['successful_extractions'] += 1
            
            return ProcessingResult(
                frame_id=frame.frame_id,
                timestamp=frame.timestamp,
                processing_time=processing_time,
                document_type=document_type,
                confidence=avg_confidence / 100 if avg_confidence > 0 else 0.5,
                extracted_text=extracted_text,
                extracted_fields=extracted_fields,
                quality_score=quality_score,
                status="success"
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Error processing frame {frame.frame_id}: {e}")
            
            return ProcessingResult(
                frame_id=frame.frame_id,
                timestamp=frame.timestamp,
                processing_time=processing_time,
                document_type="unknown",
                confidence=0.0,
                extracted_text="",
                extracted_fields={},
                quality_score=0.0,
                status="error",
                error_message=str(e)
            )
    
    def _handle_result(self, future):
        """Handle processing result"""
        try:
            result = future.result()
            
            # Call all registered callbacks
            for callback in self.result_callbacks:
                try:
                    callback(result)
                except Exception as e:
                    logger.error(f"Error in result callback: {e}")
                    
        except Exception as e:
            logger.error(f"Error handling result: {e}")
    
    def _detect_document_type(self, text: str) -> str:
        """Basic document type detection"""
        text_lower = text.lower()
        
        if any(keyword in text_lower for keyword in ['aadhaar', 'aadhar', 'unique identification']):
            return "Aadhaar Card"
        elif any(keyword in text_lower for keyword in ['permanent account', 'pan', 'income tax']):
            return "PAN Card"
        elif any(keyword in text_lower for keyword in ['passport', 'republic of india']):
            return "Passport"
        elif any(keyword in text_lower for keyword in ['driving', 'license', 'transport']):
            return "Driving License"
        elif any(keyword in text_lower for keyword in ['voter', 'election', 'epic']):
            return "Voter ID"
        else:
            return "Unknown Document"
    
    def _extract_fields(self, text: str, document_type: str) -> Dict[str, Any]:
        """Extract fields based on document type"""
        import re
        fields = {}
        
        # Common fields
        # Name extraction
        name_match = re.search(r'(?:name|नाम)[:\s]*([A-Za-z\s]+)', text, re.IGNORECASE)
        if name_match:
            fields['name'] = name_match.group(1).strip()
        
        # Date extraction
        date_match = re.search(r'(?:dob|date.*birth|जन्म)[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', text, re.IGNORECASE)
        if date_match:
            fields['date_of_birth'] = date_match.group(1)
        
        # Document specific fields
        if document_type == "Aadhaar Card":
            aadhaar_match = re.search(r'\b\d{4}\s*\d{4}\s*\d{4}\b', text)
            if aadhaar_match:
                fields['aadhaar_number'] = aadhaar_match.group()
        
        elif document_type == "PAN Card":
            pan_match = re.search(r'\b[A-Z]{5}\d{4}[A-Z]\b', text)
            if pan_match:
                fields['pan_number'] = pan_match.group()
        
        return fields
    
    def _calculate_quality_score(self, image: np.ndarray, text: str) -> float:
        """Calculate overall quality score"""
        # Image quality (30%)
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
            
        sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()
        image_quality = min(sharpness / 1000, 1.0)
        
        # Text quality (70%)
        text_quality = 0.0
        if text.strip():
            # Length factor
            length_factor = min(len(text) / 100, 1.0)
            
            # Character diversity
            unique_chars = len(set(text))
            diversity_factor = min(unique_chars / 50, 1.0)
            
            text_quality = (length_factor + diversity_factor) / 2
        
        return (image_quality * 0.3 + text_quality * 0.7)
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        stats = self.stats.copy()
        if stats['frames_processed'] > 0:
            stats['average_processing_time'] = stats['total_processing_time'] / stats['frames_processed']
            stats['success_rate'] = stats['successful_extractions'] / stats['frames_processed'] * 100
        else:
            stats['average_processing_time'] = 0
            stats['success_rate'] = 0
        
        return stats

class WebSocketOCRServer:
    """WebSocket server for real-time OCR processing"""
    
    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
        self.clients = set()
        self.ocr_processor = StreamingOCRProcessor()
        self.quality_assessor = LiveQualityAssessment()
        
        # Add result callback
        self.ocr_processor.add_result_callback(self._broadcast_result)
        
    async def start_server(self):
        """Start the WebSocket server"""
        self.ocr_processor.start_processing()
        
        async with serve(self.handle_client, self.host, self.port):
            logger.info(f"WebSocket server started on {self.host}:{self.port}")
            await asyncio.Future()  # Run forever
            
    async def stop_server(self):
        """Stop the WebSocket server"""
        self.ocr_processor.stop_processing()
        
    async def handle_client(self, websocket, path):
        """Handle WebSocket client connection"""
        self.clients.add(websocket)
        logger.info(f"Client connected: {websocket.remote_address}")
        
        try:
            async for message in websocket:
                await self._handle_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client disconnected: {websocket.remote_address}")
        finally:
            self.clients.discard(websocket)
    
    async def _handle_message(self, websocket, message: str):
        """Handle incoming WebSocket message"""
        try:
            data = json.loads(message)
            message_type = data.get('type')
            
            if message_type == 'frame':
                await self._handle_frame_message(websocket, data)
            elif message_type == 'get_stats':
                await self._handle_stats_request(websocket)
            elif message_type == 'ping':
                await websocket.send(json.dumps({'type': 'pong', 'timestamp': time.time()}))
            else:
                await websocket.send(json.dumps({
                    'type': 'error',
                    'message': f'Unknown message type: {message_type}'
                }))
                
        except json.JSONDecodeError:
            await websocket.send(json.dumps({
                'type': 'error',
                'message': 'Invalid JSON message'
            }))
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            await websocket.send(json.dumps({
                'type': 'error',
                'message': str(e)
            }))
    
    async def _handle_frame_message(self, websocket, data: Dict[str, Any]):
        """Handle incoming frame data"""
        try:
            # Decode base64 image
            image_data = base64.b64decode(data['image'])
            
            # Convert to numpy array
            image_array = np.frombuffer(image_data, dtype=np.uint8)
            image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
            
            if image is None:
                await websocket.send(json.dumps({
                    'type': 'error',
                    'message': 'Invalid image data'
                }))
                return
            
            # Assess quality
            quality_metrics = self.quality_assessor.assess_frame_quality(image)
            quality_feedback = self.quality_assessor.get_quality_feedback(quality_metrics)
            
            # Send quality feedback immediately
            await websocket.send(json.dumps({
                'type': 'quality_feedback',
                'frame_id': data.get('frame_id'),
                'quality_metrics': asdict(quality_metrics),
                'feedback': quality_feedback
            }))
            
            # Process frame if quality is acceptable
            if self.quality_assessor.is_quality_acceptable(quality_metrics):
                frame = ProcessingFrame(
                    frame_id=data.get('frame_id', str(time.time())),
                    timestamp=time.time(),
                    image_data=image,
                    metadata=data.get('metadata', {})
                )
                
                success = self.ocr_processor.add_frame(frame)
                if not success:
                    await websocket.send(json.dumps({
                        'type': 'warning',
                        'message': 'Processing queue is full'
                    }))
            
        except Exception as e:
            logger.error(f"Error handling frame: {e}")
            await websocket.send(json.dumps({
                'type': 'error',
                'message': f'Error processing frame: {str(e)}'
            }))
    
    async def _handle_stats_request(self, websocket):
        """Handle statistics request"""
        stats = self.ocr_processor.get_processing_stats()
        await websocket.send(json.dumps({
            'type': 'stats',
            'data': stats
        }))
    
    def _broadcast_result(self, result: ProcessingResult):
        """Broadcast processing result to all clients"""
        message = {
            'type': 'ocr_result',
            'data': asdict(result)
        }
        
        # Send to all connected clients
        if self.clients:
            asyncio.create_task(self._send_to_all_clients(json.dumps(message)))
    
    async def _send_to_all_clients(self, message: str):
        """Send message to all connected clients"""
        if self.clients:
            await asyncio.gather(
                *[client.send(message) for client in self.clients],
                return_exceptions=True
            )

class RealTimeOCRProcessor:
    """Main real-time OCR processing coordinator"""
    
    def __init__(self):
        self.websocket_server = WebSocketOCRServer()
        self.is_running = False
        
    async def start(self):
        """Start the real-time processing system"""
        logger.info("Starting real-time OCR processing system...")
        self.is_running = True
        
        try:
            await self.websocket_server.start_server()
        except KeyboardInterrupt:
            logger.info("Shutting down real-time OCR processor...")
            await self.stop()
    
    async def stop(self):
        """Stop the real-time processing system"""
        self.is_running = False
        await self.websocket_server.stop_server()
        logger.info("Real-time OCR processor stopped")
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Get connection information"""
        return {
            'websocket_url': f'ws://{self.websocket_server.host}:{self.websocket_server.port}',
            'host': self.websocket_server.host,
            'port': self.websocket_server.port,
            'status': 'running' if self.is_running else 'stopped'
        }

# Usage example and testing
if __name__ == "__main__":
    print("⚡ REAL-TIME OCR PROCESSOR - INITIALIZATION")
    print("=" * 60)
    
    if not WEBSOCKETS_AVAILABLE:
        print("❌ WebSockets not available. Install with: pip install websockets")
        exit(1)
    
    # Initialize processor
    processor = RealTimeOCRProcessor()
    
    # Show connection info
    info = processor.get_connection_info()
    print(f"\n📡 CONNECTION INFORMATION:")
    print(f"   WebSocket URL: {info['websocket_url']}")
    print(f"   Host: {info['host']}")
    print(f"   Port: {info['port']}")
    print(f"   Status: {info['status']}")
    
    print(f"\n🚀 STARTING REAL-TIME OCR SERVER...")
    print("   • WebSocket server for real-time communication")
    print("   • Live quality assessment and feedback")
    print("   • Parallel OCR processing")
    print("   • Real-time result broadcasting")
    print("   • Processing statistics and monitoring")
    
    print(f"\n💡 USAGE:")
    print("   1. Connect to WebSocket server")
    print("   2. Send frames as base64-encoded images")
    print("   3. Receive real-time quality feedback")
    print("   4. Get OCR results as they're processed")
    print("   5. Monitor processing statistics")
    
    print(f"\n🔧 CLIENT EXAMPLE:")
    print("   const ws = new WebSocket('ws://localhost:8765');")
    print("   ws.send(JSON.stringify({")
    print("     type: 'frame',")
    print("     frame_id: 'frame_001',")
    print("     image: 'base64_encoded_image_data'")
    print("   }));")
    
    print(f"\n✅ PRESS CTRL+C TO STOP SERVER")
    
    # Start the server
    try:
        asyncio.run(processor.start())
    except KeyboardInterrupt:
        print(f"\n🛑 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Server error: {e}")

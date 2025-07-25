#!/bin/bash

# Enhanced OCR Document Scanner - Production Deployment Script
# This script builds and deploys the enhanced OCR system

set -e

echo "🚀 ENHANCED OCR DOCUMENT SCANNER - DEPLOYMENT SCRIPT"
echo "======================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}$1${NC}"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        print_error "Docker is not running. Please start Docker first."
        exit 1
    fi
    
    print_status "Docker is installed and running"
}

# Create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    
    mkdir -p uploads logs models analytics_charts
    
    print_success "Directories created successfully"
}

# Build the application
build_application() {
    print_header "Building Enhanced OCR Application..."
    
    # Build the Docker image
    print_status "Building Docker image..."
    docker build -t enhanced-ocr-scanner .
    
    if [ $? -eq 0 ]; then
        print_success "Docker image built successfully"
    else
        print_error "Failed to build Docker image"
        exit 1
    fi
}

# Deploy standalone container
deploy_standalone() {
    print_header "Deploying Standalone Container..."
    
    # Stop existing container if running
    print_status "Stopping existing container..."
    docker stop enhanced-ocr-scanner 2>/dev/null || true
    docker rm enhanced-ocr-scanner 2>/dev/null || true
    
    # Run the container
    print_status "Starting Enhanced OCR container..."
    docker run -d \
        --name enhanced-ocr-scanner \
        --restart unless-stopped \
        -p 5000:5000 \
        -v $(pwd)/uploads:/app/uploads \
        -v $(pwd)/logs:/app/logs \
        -v $(pwd)/models:/app/models \
        -v $(pwd)/analytics_charts:/app/analytics_charts \
        -e FLASK_ENV=production \
        -e TESSERACT_CMD=/usr/bin/tesseract \
        -e PYTHONPATH=/app \
        -e PYTHONUNBUFFERED=1 \
        enhanced-ocr-scanner
    
    if [ $? -eq 0 ]; then
        print_success "Container started successfully"
    else
        print_error "Failed to start container"
        exit 1
    fi
}

# Wait for application to be ready
wait_for_application() {
    print_status "Waiting for application to be ready..."
    
    for i in {1..30}; do
        if curl -f http://localhost:5000/health &> /dev/null; then
            print_success "Application is ready!"
            return 0
        fi
        print_status "Waiting... (attempt $i/30)"
        sleep 2
    done
    
    print_error "Application failed to start within 60 seconds"
    return 1
}

# Show deployment information
show_deployment_info() {
    print_header "🎉 Deployment Complete!"
    echo ""
    echo "🌐 Application URL: http://localhost:5000"
    echo "📊 Health Check: http://localhost:5000/health"
    echo "📈 Analytics: http://localhost:5000/api/analytics/dashboard"
    echo "📋 API Status: http://localhost:5000/api/status"
    echo ""
    echo "📁 Directories:"
    echo "   • Uploads: $(pwd)/uploads"
    echo "   • Logs: $(pwd)/logs"
    echo "   • Models: $(pwd)/models"
    echo "   • Analytics: $(pwd)/analytics_charts"
    echo ""
    echo "🔧 Management Commands:"
    echo "   • View logs: docker logs enhanced-ocr-scanner"
    echo "   • Stop app: docker stop enhanced-ocr-scanner"
    echo "   • Restart app: docker restart enhanced-ocr-scanner"
    echo "   • Update app: ./deploy.sh --rebuild"
    echo ""
    echo "✨ Features Available:"
    echo "   • Advanced OCR with machine learning classification"
    echo "   • Real-time document processing"
    echo "   • Security validation and encryption"
    echo "   • Analytics dashboard with comprehensive metrics"
    echo "   • Support for multiple document types"
    echo "   • Modern web interface with drag-and-drop upload"
    echo ""
}

# Show usage information
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --rebuild     Force rebuild of Docker image"
    echo "  --stop        Stop all services"
    echo "  --logs        Show application logs"
    echo "  --status      Show deployment status"
    echo "  --help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                    # Deploy the application"
    echo "  $0 --rebuild          # Rebuild and deploy"
    echo "  $0 --stop             # Stop the application"
    echo "  $0 --logs             # View application logs"
    echo "  $0 --status           # Check deployment status"
    echo ""
}

# Stop all services
stop_services() {
    print_header "Stopping Services..."
    
    # Stop standalone container
    docker stop enhanced-ocr-scanner 2>/dev/null || true
    docker rm enhanced-ocr-scanner 2>/dev/null || true
    
    print_success "All services stopped"
}

# Show logs
show_logs() {
    print_header "Application Logs"
    
    if docker ps | grep -q enhanced-ocr-scanner; then
        docker logs -f enhanced-ocr-scanner
    else
        print_error "No running containers found"
        exit 1
    fi
}

# Show status
show_status() {
    print_header "Deployment Status"
    echo ""
    
    echo "Docker Containers:"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep enhanced-ocr-scanner || echo "❌ No containers running"
    
    echo ""
    echo "Health Check:"
    if curl -f http://localhost:5000/health &> /dev/null; then
        echo "✅ Application is healthy"
        echo "✅ Available at: http://localhost:5000"
    else
        echo "❌ Application is not responding"
    fi
    
    echo ""
    echo "System Resources:"
    echo "Docker Images:"
    docker images | grep enhanced-ocr-scanner || echo "❌ No images found"
    
    echo ""
    echo "Disk Usage:"
    echo "Uploads: $(du -sh uploads 2>/dev/null || echo 'N/A')"
    echo "Logs: $(du -sh logs 2>/dev/null || echo 'N/A')"
    echo "Models: $(du -sh models 2>/dev/null || echo 'N/A')"
}

# Main deployment process
main() {
    local rebuild=false
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --rebuild)
                rebuild=true
                shift
                ;;
            --stop)
                stop_services
                exit 0
                ;;
            --logs)
                show_logs
                exit 0
                ;;
            --status)
                show_status
                exit 0
                ;;
            --help)
                show_usage
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    print_header "Starting Enhanced OCR Document Scanner Deployment"
    
    # Pre-deployment checks
    check_docker
    create_directories
    
    # Build application
    if [ "$rebuild" == true ] || ! docker images | grep -q enhanced-ocr-scanner; then
        build_application
    else
        print_status "Using existing Docker image (use --rebuild to force rebuild)"
    fi
    
    # Deploy the application
    deploy_standalone
    
    # Wait for application to be ready
    wait_for_application
    
    # Show deployment information
    show_deployment_info
    
    print_success "Your Enhanced OCR Document Scanner is now running at http://localhost:5000"
}

# Run main function with all arguments
main "$@"
    
    # Start infrastructure services first
    print_status "Starting infrastructure services (PostgreSQL, Redis)..."
    docker-compose up -d postgres redis
    
    # Wait for services to be healthy
    print_status "Waiting for database and Redis to be ready..."
    sleep 30
    
    # Check if services are healthy
    if ! docker-compose ps postgres | grep -q "healthy"; then
        print_error "PostgreSQL failed to start properly"
        docker-compose logs postgres
        exit 1
    fi
    
    if ! docker-compose ps redis | grep -q "healthy"; then
        print_error "Redis failed to start properly"
        docker-compose logs redis
        exit 1
    fi
    
    print_success "Infrastructure services are running"
    
    # Start application services
    print_status "Starting application services..."
    docker-compose up -d ocr-scanner celery-worker celery-beat
    
    # Wait for application to be ready
    print_status "Waiting for application to be ready..."
    sleep 45
    
    # Optional: Start monitoring
    print_status "Starting monitoring services..."
    docker-compose up -d flower
    
    print_success "All services deployed successfully"
}

# Initialize database
init_database() {
    print_status "Initializing database..."
    
    # Wait a bit more for the application to be fully ready
    sleep 15
    
    # Initialize database migrations
    print_status "Setting up database migrations..."
    docker-compose exec -T ocr-scanner flask db init || print_warning "Database already initialized"
    docker-compose exec -T ocr-scanner flask db migrate -m "Initial migration" || print_warning "Migration already exists"
    docker-compose exec -T ocr-scanner flask db upgrade
    
    print_success "Database initialized"
}

# Run health checks
health_checks() {
    print_status "Running health checks..."
    
    # Check main application
    if curl -f http://localhost:5000/health > /dev/null 2>&1; then
        print_success "Main application is healthy"
    else
        print_error "Main application health check failed"
        docker-compose logs ocr-scanner
        return 1
    fi
    
    # Check Flower monitoring
    if curl -f http://localhost:5555 > /dev/null 2>&1; then
        print_success "Flower monitoring is accessible"
    else
        print_warning "Flower monitoring is not accessible (this is optional)"
    fi
    
    # Check database connection
    if docker-compose exec -T postgres pg_isready -U postgres > /dev/null 2>&1; then
        print_success "PostgreSQL is ready"
    else
        print_error "PostgreSQL is not ready"
        return 1
    fi
    
    # Check Redis connection
    if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
        print_success "Redis is ready"
    else
        print_error "Redis is not ready"
        return 1
    fi
    
    print_success "All health checks passed"
}

# Display service information
show_service_info() {
    echo ""
    echo "🎉 Deployment Completed Successfully!"
    echo "====================================="
    echo ""
    echo "📊 Service URLs:"
    echo "• Main Application: http://localhost:5000"
    echo "• Health Check: http://localhost:5000/health"
    echo "• API v2: http://localhost:5000/api/v2/"
    echo "• Analytics: http://localhost:5000/analytics"
    echo "• Flower Monitoring: http://localhost:5555 (admin/admin)"
    echo ""
    echo "🗄️ Database Information:"
    echo "• PostgreSQL: localhost:5432"
    echo "• Database: ocr_scanner"
    echo "• Redis: localhost:6379"
    echo ""
    echo "📋 Useful Commands:"
    echo "• View logs: docker-compose logs -f [service_name]"
    echo "• Scale workers: docker-compose up -d --scale celery-worker=3"
    echo "• Stop services: docker-compose down"
    echo "• View status: docker-compose ps"
    echo ""
    echo "🔧 Next Steps:"
    echo "1. Test the API endpoints"
    echo "2. Upload a document to test processing"
    echo "3. Check analytics dashboard"
    echo "4. Monitor background tasks in Flower"
    echo ""
}

# Main deployment flow
main() {
    echo "Starting deployment at $(date)"
    
    check_dependencies
    setup_environment
    cleanup_containers
    deploy_services
    init_database
    health_checks
    show_service_info
    
    print_success "Deployment completed successfully! 🎉"
}

# Handle script arguments
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "stop")
        print_status "Stopping all services..."
        docker-compose down
        print_success "All services stopped"
        ;;
    "restart")
        print_status "Restarting services..."
        docker-compose down
        sleep 5
        docker-compose up -d
        print_success "Services restarted"
        ;;
    "logs")
        docker-compose logs -f
        ;;
    "status")
        docker-compose ps
        ;;
    "health")
        health_checks
        ;;
    *)
        echo "Usage: $0 {deploy|stop|restart|logs|status|health}"
        echo ""
        echo "Commands:"
        echo "  deploy  - Full deployment (default)"
        echo "  stop    - Stop all services" 
        echo "  restart - Restart all services"
        echo "  logs    - Show service logs"
        echo "  status  - Show service status"
        echo "  health  - Run health checks"
        exit 1
        ;;
esac

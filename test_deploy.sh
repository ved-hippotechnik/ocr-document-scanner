#!/bin/bash

# Single Container Deployment Script for Testing
# This script deploys just the main OCR application for testing when Docker Compose is not available

set -e

echo "🚀 OCR Document Scanner - Single Container Test Deployment"
echo "========================================================="

# Function to print colored output
print_status() {
    echo -e "\033[1;34m[INFO]\033[0m $1"
}

print_success() {
    echo -e "\033[1;32m[SUCCESS]\033[0m $1"
}

print_error() {
    echo -e "\033[1;31m[ERROR]\033[0m $1"
}

print_warning() {
    echo -e "\033[1;33m[WARNING]\033[0m $1"
}

# Check Docker
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    print_success "Docker is available"
}

# Clean up any existing containers
cleanup() {
    print_status "Cleaning up existing containers..."
    docker stop ocr-scanner-test 2>/dev/null || true
    docker rm ocr-scanner-test 2>/dev/null || true
    print_success "Cleanup completed"
}

# Build the image
build_image() {
    print_status "Building OCR Scanner Docker image..."
    
    if docker build -t ocr-scanner:test . ; then
        print_success "Image built successfully"
    else
        print_error "Failed to build Docker image"
        exit 1
    fi
}

# Run the container
run_container() {
    print_status "Starting OCR Scanner container..."
    
    # Create uploads directory
    mkdir -p ./uploads
    
    # Run container with basic configuration
    docker run -d \
        --name ocr-scanner-test \
        -p 5000:5000 \
        -v "$(pwd)/uploads:/app/uploads" \
        -e FLASK_ENV=development \
        -e SECRET_KEY=test-secret-key \
        -e SQLALCHEMY_DATABASE_URI=sqlite:///test_ocr.db \
        -e LOG_LEVEL=INFO \
        ocr-scanner:test
    
    if [ $? -eq 0 ]; then
        print_success "Container started successfully"
    else
        print_error "Failed to start container"
        exit 1
    fi
}

# Wait for service to be ready
wait_for_service() {
    print_status "Waiting for service to be ready..."
    
    max_attempts=30
    attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f -s http://localhost:5000/health > /dev/null; then
            print_success "Service is ready!"
            return 0
        fi
        
        echo "Attempt $attempt/$max_attempts - waiting..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    print_error "Service failed to start within timeout"
    print_status "Checking container logs..."
    docker logs ocr-scanner-test
    return 1
}

# Show service info
show_info() {
    echo ""
    echo "🎉 Single Container Deployment Completed!"
    echo "========================================"
    echo ""
    echo "📊 Service Information:"
    echo "• Application: http://localhost:5000"
    echo "• Health Check: http://localhost:5000/health"
    echo "• API Endpoints: http://localhost:5000/api/"
    echo ""
    echo "🔧 Useful Commands:"
    echo "• View logs: docker logs -f ocr-scanner-test"
    echo "• Stop service: docker stop ocr-scanner-test"
    echo "• Remove container: docker rm ocr-scanner-test"
    echo "• Shell access: docker exec -it ocr-scanner-test /bin/bash"
    echo ""
    echo "⚠️ Note: This is a simplified deployment without database persistence."
    echo "For full production deployment, install Docker Compose and use ./deploy.sh"
    echo ""
}

# Main execution
main() {
    check_docker
    cleanup
    build_image
    run_container
    
    if wait_for_service; then
        show_info
        print_success "Deployment completed successfully! 🎉"
        
        # Run basic test
        print_status "Running basic connectivity test..."
        if python3 test_comprehensive_api.py --timeout 30; then
            print_success "API tests passed!"
        else
            print_warning "Some API tests failed - check the logs"
        fi
    else
        print_error "Deployment failed"
        exit 1
    fi
}

# Handle arguments
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "stop")
        print_status "Stopping test container..."
        docker stop ocr-scanner-test
        print_success "Container stopped"
        ;;
    "logs")
        docker logs -f ocr-scanner-test
        ;;
    "status")
        if docker ps | grep -q ocr-scanner-test; then
            print_success "Container is running"
            docker ps | grep ocr-scanner-test
        else
            print_warning "Container is not running"
        fi
        ;;
    "clean")
        print_status "Cleaning up everything..."
        docker stop ocr-scanner-test 2>/dev/null || true
        docker rm ocr-scanner-test 2>/dev/null || true
        docker rmi ocr-scanner:test 2>/dev/null || true
        print_success "Cleanup completed"
        ;;
    *)
        echo "Usage: $0 {deploy|stop|logs|status|clean}"
        echo ""
        echo "Commands:"
        echo "  deploy - Deploy single container (default)"
        echo "  stop   - Stop the container"
        echo "  logs   - Show container logs"
        echo "  status - Show container status"
        echo "  clean  - Remove container and image"
        ;;
esac

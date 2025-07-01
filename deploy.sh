#!/bin/bash

# OCR Document Scanner Deployment Script
# This script handles the deployment and testing of the enhanced OCR system

set -e  # Exit on error

echo "🚀 Starting OCR Document Scanner Deployment"
echo "============================================="

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

# Check if Docker and Docker Compose are installed
check_dependencies() {
    print_status "Checking dependencies..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    print_success "Docker and Docker Compose are installed"
}

# Create environment file if it doesn't exist
setup_environment() {
    print_status "Setting up environment..."
    
    if [ ! -f .env ]; then
        print_warning ".env file not found. Creating from template..."
        cp .env.example .env
        
        # Generate secure random keys
        SECRET_KEY=$(openssl rand -hex 32)
        POSTGRES_PASSWORD=$(openssl rand -hex 16)
        REDIS_PASSWORD=$(openssl rand -hex 16)
        FLOWER_PASSWORD=$(openssl rand -hex 12)
        
        # Update .env file with secure values
        sed -i.bak "s/your-secret-key-here/$SECRET_KEY/" .env
        sed -i.bak "s/change-this-password/$POSTGRES_PASSWORD/" .env
        sed -i.bak "s/change-this-password/$REDIS_PASSWORD/" .env 2>/dev/null || true
        sed -i.bak "s/change-this-password/$FLOWER_PASSWORD/" .env 2>/dev/null || true
        
        rm .env.bak 2>/dev/null || true
        
        print_success "Environment file created with secure keys"
    else
        print_success "Environment file already exists"
    fi
}

# Stop any running containers
cleanup_containers() {
    print_status "Cleaning up existing containers..."
    
    docker-compose down --remove-orphans || true
    docker system prune -f --volumes || true
    
    print_success "Cleanup completed"
}

# Build and start services
deploy_services() {
    print_status "Building and starting services..."
    
    # Build images
    print_status "Building Docker images..."
    docker-compose build --no-cache
    
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

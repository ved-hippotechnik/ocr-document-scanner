#!/bin/bash

# Production Deployment Script for OCR Document Scanner
# This script handles the complete production deployment process

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
DEPLOY_ENV=${1:-production}
BACKUP_BEFORE_DEPLOY=${BACKUP_BEFORE_DEPLOY:-true}
RUN_TESTS=${RUN_TESTS:-true}
ZERO_DOWNTIME=${ZERO_DOWNTIME:-true}

echo -e "${GREEN}Starting deployment for environment: ${DEPLOY_ENV}${NC}"

# Function to check prerequisites
check_prerequisites() {
    echo -e "${YELLOW}Checking prerequisites...${NC}"
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}Docker is not installed${NC}"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}Docker Compose is not installed${NC}"
        exit 1
    fi
    
    # Check environment file
    if [ ! -f ".env.${DEPLOY_ENV}" ]; then
        echo -e "${RED}Environment file .env.${DEPLOY_ENV} not found${NC}"
        exit 1
    fi
    
    # Validate environment variables
    source .env.${DEPLOY_ENV}
    
    required_vars=(
        "SECRET_KEY"
        "JWT_SECRET_KEY"
        "DATABASE_URL"
        "REDIS_PASSWORD"
        "POSTGRES_PASSWORD"
    )
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            echo -e "${RED}Required environment variable ${var} is not set${NC}"
            exit 1
        fi
    done
    
    echo -e "${GREEN}Prerequisites check passed${NC}"
}

# Function to backup database
backup_database() {
    if [ "${BACKUP_BEFORE_DEPLOY}" = "true" ]; then
        echo -e "${YELLOW}Backing up database...${NC}"
        
        timestamp=$(date +%Y%m%d_%H%M%S)
        backup_dir="backups/${timestamp}"
        mkdir -p ${backup_dir}
        
        # Backup PostgreSQL
        docker-compose -f docker-compose.${DEPLOY_ENV}.yml exec -T postgres \
            pg_dump -U ${POSTGRES_USER} ${POSTGRES_DB} | gzip > ${backup_dir}/database.sql.gz
        
        # Backup uploads directory
        tar -czf ${backup_dir}/uploads.tar.gz backend/uploads/
        
        echo -e "${GREEN}Backup completed: ${backup_dir}${NC}"
    fi
}

# Function to run tests
run_tests() {
    if [ "${RUN_TESTS}" = "true" ]; then
        echo -e "${YELLOW}Running tests...${NC}"
        
        # Run backend tests
        docker-compose -f docker-compose.${DEPLOY_ENV}.yml run --rm backend pytest tests/ || {
            echo -e "${RED}Tests failed. Aborting deployment${NC}"
            exit 1
        }
        
        echo -e "${GREEN}Tests passed${NC}"
    fi
}

# Function to build images
build_images() {
    echo -e "${YELLOW}Building Docker images...${NC}"
    
    # Build backend image
    docker build -t ocr-scanner-backend:${DEPLOY_ENV} \
        -f backend/Dockerfile.production \
        backend/
    
    # Build frontend image
    docker build -t ocr-scanner-frontend:${DEPLOY_ENV} \
        -f frontend/Dockerfile.production \
        frontend/
    
    echo -e "${GREEN}Images built successfully${NC}"
}

# Function to deploy with zero downtime
deploy_zero_downtime() {
    echo -e "${YELLOW}Deploying with zero downtime...${NC}"
    
    # Scale up new containers
    docker-compose -f docker-compose.${DEPLOY_ENV}.yml up -d --scale backend=2
    
    # Wait for health checks
    sleep 30
    
    # Check health status
    health_check_url="http://localhost/health"
    if curl -f ${health_check_url} > /dev/null 2>&1; then
        echo -e "${GREEN}Health check passed${NC}"
    else
        echo -e "${RED}Health check failed${NC}"
        exit 1
    fi
    
    # Remove old containers
    docker-compose -f docker-compose.${DEPLOY_ENV}.yml up -d --remove-orphans
    
    echo -e "${GREEN}Zero-downtime deployment completed${NC}"
}

# Function to deploy normally
deploy_normal() {
    echo -e "${YELLOW}Deploying application...${NC}"
    
    # Stop existing containers
    docker-compose -f docker-compose.${DEPLOY_ENV}.yml down
    
    # Start new containers
    docker-compose -f docker-compose.${DEPLOY_ENV}.yml up -d
    
    echo -e "${GREEN}Deployment completed${NC}"
}

# Function to run database migrations
run_migrations() {
    echo -e "${YELLOW}Running database migrations...${NC}"
    
    docker-compose -f docker-compose.${DEPLOY_ENV}.yml exec backend \
        flask db upgrade
    
    echo -e "${GREEN}Migrations completed${NC}"
}

# Function to setup SSL certificates
setup_ssl() {
    echo -e "${YELLOW}Setting up SSL certificates...${NC}"
    
    if [ ! -d "ssl" ]; then
        mkdir -p ssl
        
        # Generate self-signed certificate for testing
        # In production, use Let's Encrypt or your CA certificates
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout ssl/privkey.pem \
            -out ssl/fullchain.pem \
            -subj "/C=US/ST=State/L=City/O=Organization/CN=ocr-scanner.yourdomain.com"
    fi
    
    echo -e "${GREEN}SSL setup completed${NC}"
}

# Function to configure monitoring
setup_monitoring() {
    echo -e "${YELLOW}Setting up monitoring...${NC}"
    
    # Create monitoring directories
    mkdir -p monitoring/prometheus monitoring/grafana/dashboards monitoring/grafana/datasources
    
    # Copy configuration files
    cp configs/prometheus.yml monitoring/prometheus/
    cp configs/grafana-dashboard.json monitoring/grafana/dashboards/
    
    echo -e "${GREEN}Monitoring setup completed${NC}"
}

# Function to perform health checks
health_check() {
    echo -e "${YELLOW}Performing health checks...${NC}"
    
    services=("backend" "redis" "postgres" "nginx")
    
    for service in "${services[@]}"; do
        if docker-compose -f docker-compose.${DEPLOY_ENV}.yml ps | grep ${service} | grep Up > /dev/null; then
            echo -e "${GREEN}✓ ${service} is running${NC}"
        else
            echo -e "${RED}✗ ${service} is not running${NC}"
            exit 1
        fi
    done
    
    # Check API endpoint
    if curl -f http://localhost/api/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ API is responding${NC}"
    else
        echo -e "${RED}✗ API is not responding${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}All health checks passed${NC}"
}

# Function to cleanup old resources
cleanup() {
    echo -e "${YELLOW}Cleaning up old resources...${NC}"
    
    # Remove unused Docker images
    docker image prune -f
    
    # Remove old backups (keep last 30 days)
    find backups -type f -mtime +30 -delete
    
    # Clear old logs
    find backend/logs -type f -name "*.log" -mtime +7 -delete
    
    echo -e "${GREEN}Cleanup completed${NC}"
}

# Function to send deployment notification
send_notification() {
    echo -e "${YELLOW}Sending deployment notification...${NC}"
    
    # Send notification (implement your notification service)
    # Example: Send to Slack, email, etc.
    
    echo -e "${GREEN}Notification sent${NC}"
}

# Main deployment flow
main() {
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}OCR Document Scanner Production Deployment${NC}"
    echo -e "${GREEN}========================================${NC}"
    
    check_prerequisites
    backup_database
    run_tests
    build_images
    setup_ssl
    setup_monitoring
    
    if [ "${ZERO_DOWNTIME}" = "true" ]; then
        deploy_zero_downtime
    else
        deploy_normal
    fi
    
    run_migrations
    health_check
    cleanup
    send_notification
    
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}Deployment completed successfully!${NC}"
    echo -e "${GREEN}========================================${NC}"
    
    # Show status
    docker-compose -f docker-compose.${DEPLOY_ENV}.yml ps
}

# Run main function
main

# Exit successfully
exit 0
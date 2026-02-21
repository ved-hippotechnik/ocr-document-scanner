#!/bin/bash

# Redis Production Setup Script
# OCR Document Scanner Application
# ===============================

set -e

echo "=================================="
echo "Redis Production Setup"
echo "=================================="
echo "$(date)"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Redis configuration from .env.production
REDIS_PASSWORD="8tOBE1%xUf6prQZu2yaJ9a97HtBsRrZL"
REDIS_PORT="6379"
REDIS_HOST="localhost"

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_redis_installed() {
    print_status "Checking Redis installation..."
    
    if command -v redis-server &> /dev/null; then
        print_success "Redis server is installed"
        redis-server --version
        return 0
    else
        print_warning "Redis not found"
        return 1
    fi
}

install_redis_macos() {
    print_status "Installing Redis on macOS using Homebrew..."
    
    # Check if Homebrew is installed
    if ! command -v brew &> /dev/null; then
        print_error "Homebrew is not installed. Please install Homebrew first:"
        echo "  /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
        exit 1
    fi
    
    # Install Redis
    print_status "Installing Redis..."
    brew install redis
    
    print_success "Redis installed"
}

install_redis_linux() {
    print_status "Installing Redis on Linux..."
    
    # Detect Linux distribution
    if [ -f /etc/debian_version ]; then
        # Debian/Ubuntu
        sudo apt update
        sudo apt install -y redis-server
    elif [ -f /etc/redhat-release ]; then
        # RedHat/CentOS/Fedora
        sudo dnf install -y redis
    else
        print_error "Unsupported Linux distribution"
        exit 1
    fi
    
    print_success "Redis installed"
}

setup_redis_directories() {
    print_status "Setting up Redis directories..."
    
    # Create necessary directories
    sudo mkdir -p /var/lib/redis
    sudo mkdir -p /var/log/redis
    sudo mkdir -p /var/run/redis
    
    # Set proper ownership and permissions
    if id "redis" &>/dev/null; then
        sudo chown redis:redis /var/lib/redis
        sudo chown redis:redis /var/log/redis
        sudo chown redis:redis /var/run/redis
    else
        print_warning "Redis user not found, using current user"
        sudo chown $USER:$USER /var/lib/redis
        sudo chown $USER:$USER /var/log/redis
        sudo chown $USER:$USER /var/run/redis
    fi
    
    sudo chmod 755 /var/lib/redis
    sudo chmod 755 /var/log/redis
    sudo chmod 755 /var/run/redis
    
    print_success "Redis directories created and configured"
}

configure_redis() {
    print_status "Configuring Redis for production..."
    
    # Copy production configuration
    if [ -f "redis.prod.conf" ]; then
        sudo cp redis.prod.conf /usr/local/etc/redis.conf
        print_success "Production configuration deployed to /usr/local/etc/redis.conf"
    else
        print_error "redis.prod.conf not found"
        exit 1
    fi
    
    # Create systemd service file for Linux
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo tee /etc/systemd/system/redis.service << EOF
[Unit]
Description=Advanced key-value store
After=network.target

[Service]
ExecStart=/usr/bin/redis-server /usr/local/etc/redis.conf
ExecStop=/usr/bin/redis-cli shutdown
Type=forking
User=redis
Group=redis
RuntimeDirectory=redis
RuntimeDirectoryMode=0755

[Install]
WantedBy=multi-user.target
EOF
        
        sudo systemctl daemon-reload
        print_success "Redis systemd service configured"
    fi
}

start_redis() {
    print_status "Starting Redis service..."
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS - start Redis with custom config
        redis-server /usr/local/etc/redis.conf &
        sleep 2
        print_success "Redis started with production configuration"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        sudo systemctl start redis
        sudo systemctl enable redis
        print_success "Redis service started and enabled"
    fi
}

test_redis_connection() {
    print_status "Testing Redis connection..."
    
    # Test connection without authentication first
    if redis-cli ping 2>/dev/null | grep -q PONG; then
        print_warning "Redis is running without authentication - this should not happen in production"
    fi
    
    # Test connection with authentication
    if redis-cli -a "${REDIS_PASSWORD}" ping 2>/dev/null | grep -q PONG; then
        print_success "Redis connection with authentication successful"
    else
        print_error "Redis authentication failed"
        exit 1
    fi
    
    # Test basic operations
    redis-cli -a "${REDIS_PASSWORD}" set test_key "production_test" > /dev/null
    RETRIEVED_VALUE=$(redis-cli -a "${REDIS_PASSWORD}" get test_key 2>/dev/null)
    
    if [ "$RETRIEVED_VALUE" = "production_test" ]; then
        print_success "Redis read/write operations working"
        redis-cli -a "${REDIS_PASSWORD}" del test_key > /dev/null
    else
        print_error "Redis read/write operations failed"
        exit 1
    fi
}

configure_redis_monitoring() {
    print_status "Configuring Redis monitoring..."
    
    # Create Redis monitoring script
    tee redis_monitor.sh << 'EOF'
#!/bin/bash
# Redis Monitoring Script

REDIS_PASSWORD="8tOBE1%xUf6prQZu2yaJ9a97HtBsRrZL"

echo "Redis Status: $(date)"
echo "=================================="

# Check if Redis is running
if ! pgrep redis-server > /dev/null; then
    echo "❌ Redis is not running"
    exit 1
fi

echo "✅ Redis is running"

# Get Redis info
redis-cli -a "${REDIS_PASSWORD}" info server | grep -E "(redis_version|uptime_in_seconds|used_memory_human)"
redis-cli -a "${REDIS_PASSWORD}" info clients | grep -E "(connected_clients|blocked_clients)"
redis-cli -a "${REDIS_PASSWORD}" info stats | grep -E "(total_commands_processed|keyspace_hits|keyspace_misses)"

# Check memory usage
echo ""
echo "Memory Usage:"
redis-cli -a "${REDIS_PASSWORD}" info memory | grep -E "(used_memory_human|used_memory_peak_human|mem_fragmentation_ratio)"

echo ""
echo "Database Keys:"
redis-cli -a "${REDIS_PASSWORD}" info keyspace
EOF
    
    chmod +x redis_monitor.sh
    print_success "Redis monitoring script created"
}

main() {
    print_status "Starting Redis production setup for OCR Document Scanner"
    
    # Check if Redis is already installed
    if ! check_redis_installed; then
        print_status "Redis not found. Installing..."
        
        if [[ "$OSTYPE" == "darwin"* ]]; then
            install_redis_macos
        elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
            install_redis_linux
        else
            print_error "Unsupported operating system: $OSTYPE"
            exit 1
        fi
    fi
    
    # Setup directories
    setup_redis_directories
    
    # Configure Redis
    configure_redis
    
    # Start Redis
    start_redis
    
    # Test connection
    test_redis_connection
    
    # Configure monitoring
    configure_redis_monitoring
    
    print_success "Redis production setup completed successfully!"
    echo ""
    echo "=================================="
    echo "Redis Configuration"
    echo "=================================="
    echo "Host: ${REDIS_HOST}"
    echo "Port: ${REDIS_PORT}"
    echo "Password: [CONFIGURED]"
    echo ""
    echo "Connection String:"
    echo "redis://:${REDIS_PASSWORD}@${REDIS_HOST}:${REDIS_PORT}/0"
    echo ""
    echo "Configuration file: /usr/local/etc/redis.conf"
    echo "Monitor script: ./redis_monitor.sh"
    echo ""
    echo "Next steps:"
    echo "1. Verify Redis is running with: ./redis_monitor.sh"
    echo "2. Test application connectivity"
    echo "3. Configure Redis backup strategy"
    echo "=================================="
}

# Run main function
main "$@"
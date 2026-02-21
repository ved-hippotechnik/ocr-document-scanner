#!/bin/bash

# PostgreSQL Production Setup Script
# OCR Document Scanner Application
# ================================

set -e

echo "=================================="
echo "PostgreSQL Production Setup"
echo "=================================="
echo "$(date)"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Database configuration from .env.production
DB_NAME="ocr_scanner_prod"
DB_USER="ocr_app_user"
DB_PASSWORD="yWpy4FI%nzfHMX1ORQwSrOzUUI5KhLnC"
DB_HOST="localhost"
DB_PORT="5432"

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

check_postgresql_installed() {
    print_status "Checking PostgreSQL installation..."
    
    if command -v psql &> /dev/null; then
        print_success "PostgreSQL client is installed"
        psql --version
        return 0
    else
        print_warning "PostgreSQL not found"
        return 1
    fi
}

install_postgresql_macos() {
    print_status "Installing PostgreSQL on macOS using Homebrew..."
    
    # Check if Homebrew is installed
    if ! command -v brew &> /dev/null; then
        print_error "Homebrew is not installed. Please install Homebrew first:"
        echo "  /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
        exit 1
    fi
    
    # Install PostgreSQL
    print_status "Installing PostgreSQL..."
    brew install postgresql@15
    
    # Start PostgreSQL service
    print_status "Starting PostgreSQL service..."
    brew services start postgresql@15
    
    # Add PostgreSQL to PATH
    echo 'export PATH="/usr/local/opt/postgresql@15/bin:$PATH"' >> ~/.zshrc
    export PATH="/usr/local/opt/postgresql@15/bin:$PATH"
    
    print_success "PostgreSQL installed and started"
}

install_postgresql_linux() {
    print_status "Installing PostgreSQL on Linux..."
    
    # Detect Linux distribution
    if [ -f /etc/debian_version ]; then
        # Debian/Ubuntu
        sudo apt update
        sudo apt install -y postgresql postgresql-contrib
        sudo systemctl start postgresql
        sudo systemctl enable postgresql
    elif [ -f /etc/redhat-release ]; then
        # RedHat/CentOS/Fedora
        sudo dnf install -y postgresql postgresql-server postgresql-contrib
        sudo postgresql-setup --initdb
        sudo systemctl start postgresql
        sudo systemctl enable postgresql
    else
        print_error "Unsupported Linux distribution"
        exit 1
    fi
    
    print_success "PostgreSQL installed and started"
}

create_database_and_user() {
    print_status "Creating database and user..."
    
    # Create user and database
    sudo -u postgres psql << EOF
-- Create user
CREATE USER ${DB_USER} WITH PASSWORD '${DB_PASSWORD}';

-- Create database
CREATE DATABASE ${DB_NAME} OWNER ${DB_USER};

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME} TO ${DB_USER};

-- Grant schema privileges
\c ${DB_NAME}
GRANT ALL ON SCHEMA public TO ${DB_USER};
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO ${DB_USER};
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO ${DB_USER};

-- Show created database and user
\l
\du

EOF

    print_success "Database '${DB_NAME}' and user '${DB_USER}' created"
}

test_database_connection() {
    print_status "Testing database connection..."
    
    # Test connection with new user
    PGPASSWORD="${DB_PASSWORD}" psql -h ${DB_HOST} -p ${DB_PORT} -U ${DB_USER} -d ${DB_NAME} -c "SELECT version();"
    
    if [ $? -eq 0 ]; then
        print_success "Database connection successful"
    else
        print_error "Database connection failed"
        exit 1
    fi
}

configure_postgresql() {
    print_status "Configuring PostgreSQL for production..."
    
    # Find PostgreSQL configuration directory
    PG_VERSION=$(psql --version | awk '{print $3}' | sed 's/\..*//')
    
    # Common configuration paths
    if [ -f "/usr/local/var/postgresql@15/postgresql.conf" ]; then
        PG_CONF_DIR="/usr/local/var/postgresql@15"
    elif [ -f "/var/lib/postgresql/${PG_VERSION}/main/postgresql.conf" ]; then
        PG_CONF_DIR="/var/lib/postgresql/${PG_VERSION}/main"
    elif [ -f "/etc/postgresql/${PG_VERSION}/main/postgresql.conf" ]; then
        PG_CONF_DIR="/etc/postgresql/${PG_VERSION}/main"
    else
        print_warning "PostgreSQL configuration directory not found automatically"
        print_status "Please locate postgresql.conf and pg_hba.conf manually"
        return
    fi
    
    print_status "Found PostgreSQL config at: ${PG_CONF_DIR}"
    
    # Backup original configuration
    sudo cp "${PG_CONF_DIR}/postgresql.conf" "${PG_CONF_DIR}/postgresql.conf.backup"
    sudo cp "${PG_CONF_DIR}/pg_hba.conf" "${PG_CONF_DIR}/pg_hba.conf.backup"
    
    # Update postgresql.conf for production
    sudo tee -a "${PG_CONF_DIR}/postgresql.conf" << EOF

# OCR Scanner Production Settings
# ==============================
max_connections = 200
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 4MB
min_wal_size = 1GB
max_wal_size = 4GB

# Logging
log_destination = 'stderr'
logging_collector = on
log_directory = 'log'
log_filename = 'postgresql-%Y-%m-%d_%H%M%S.log'
log_statement = 'ddl'
log_min_duration_statement = 1000

# Security
ssl = on
password_encryption = scram-sha-256
EOF

    # Update pg_hba.conf for authentication
    sudo sed -i.backup 's/#local   replication     all                                     peer/local   replication     all                                     md5/' "${PG_CONF_DIR}/pg_hba.conf"
    
    # Add application-specific entry
    echo "host    ${DB_NAME}    ${DB_USER}    127.0.0.1/32    scram-sha-256" | sudo tee -a "${PG_CONF_DIR}/pg_hba.conf"
    
    print_success "PostgreSQL configured for production"
}

restart_postgresql() {
    print_status "Restarting PostgreSQL service..."
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        brew services restart postgresql@15
    else
        # Linux
        sudo systemctl restart postgresql
    fi
    
    sleep 3
    print_success "PostgreSQL service restarted"
}

main() {
    print_status "Starting PostgreSQL setup for OCR Document Scanner"
    
    # Check if PostgreSQL is already installed
    if ! check_postgresql_installed; then
        print_status "PostgreSQL not found. Installing..."
        
        if [[ "$OSTYPE" == "darwin"* ]]; then
            install_postgresql_macos
        elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
            install_postgresql_linux
        else
            print_error "Unsupported operating system: $OSTYPE"
            exit 1
        fi
    fi
    
    # Create database and user
    create_database_and_user
    
    # Configure PostgreSQL
    configure_postgresql
    
    # Restart PostgreSQL
    restart_postgresql
    
    # Test connection
    test_database_connection
    
    print_success "PostgreSQL setup completed successfully!"
    echo ""
    echo "=================================="
    echo "Database Configuration"
    echo "=================================="
    echo "Database: ${DB_NAME}"
    echo "User: ${DB_USER}"
    echo "Host: ${DB_HOST}"
    echo "Port: ${DB_PORT}"
    echo ""
    echo "Connection String:"
    echo "postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}"
    echo ""
    echo "Next steps:"
    echo "1. Update your application's .env.production file"
    echo "2. Run database migrations"
    echo "3. Test application connectivity"
    echo "=================================="
}

# Run main function
main "$@"
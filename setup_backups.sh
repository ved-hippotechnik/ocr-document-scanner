#!/bin/bash

# Automated Backup and Log Rotation Setup
# OCR Document Scanner Application
# =====================================

set -e

echo "=========================================="
echo "Backup and Log Rotation Setup"
echo "=========================================="
echo "$(date)"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

BACKUP_BASE_DIR="/var/backups/ocr-scanner"
APP_DIR="/Users/vedthampi/CascadeProjects/ocr-document-scanner"

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

check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check for required commands
    local missing_commands=()
    
    for cmd in pg_dump redis-cli tar gzip crontab logrotate; do
        if ! command -v "$cmd" &> /dev/null; then
            missing_commands+=("$cmd")
        fi
    done
    
    if [ ${#missing_commands[@]} -gt 0 ]; then
        print_error "Missing required commands: ${missing_commands[*]}"
        print_status "Please install the missing commands and try again"
        return 1
    fi
    
    print_success "All prerequisites are installed"
}

create_backup_directories() {
    print_status "Creating backup directories..."
    
    # Create backup directory structure
    sudo mkdir -p "$BACKUP_BASE_DIR"/{daily,weekly,monthly,logs}
    sudo mkdir -p /var/log/ocr-scanner
    
    # Set proper permissions
    sudo chown -R $USER:$USER "$BACKUP_BASE_DIR"
    sudo chmod -R 755 "$BACKUP_BASE_DIR"
    
    # Create log directory for application
    mkdir -p "$APP_DIR/backend/logs"
    
    print_success "Backup directories created"
}

setup_logrotate() {
    print_status "Setting up log rotation..."
    
    # Create logrotate configuration for OCR Scanner
    sudo tee /etc/logrotate.d/ocr-scanner << EOF
# OCR Document Scanner Log Rotation Configuration
${APP_DIR}/backend/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 $USER $USER
    sharedscripts
    postrotate
        # Restart or reload the application if needed
        # systemctl reload ocr-scanner || true
    endscript
}

/var/log/ocr-scanner/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 $USER $USER
    sharedscripts
    postrotate
        # Send signal to application to reopen log files
        # pkill -HUP -f "ocr-scanner" || true
    endscript
}

# PostgreSQL logs
/var/log/postgresql/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 640 postgres postgres
    sharedscripts
    postrotate
        # Signal PostgreSQL to reopen log files
        # systemctl reload postgresql || true
    endscript
}

# Redis logs
/var/log/redis/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 640 redis redis
    sharedscripts
    postrotate
        # Signal Redis to reopen log files if needed
        # redis-cli DEBUG RESTART || true
    endscript
}
EOF

    # Test logrotate configuration
    if sudo logrotate -t /etc/logrotate.d/ocr-scanner; then
        print_success "Logrotate configuration created and tested"
    else
        print_error "Logrotate configuration test failed"
        return 1
    fi
}

setup_cron_jobs() {
    print_status "Setting up cron jobs for automated backups..."
    
    # Create cron job entries
    local cron_file="/tmp/ocr-scanner-cron"
    
    cat > "$cron_file" << EOF
# OCR Document Scanner Automated Backup Jobs
# ==========================================

# Daily backup at 2 AM
0 2 * * * $APP_DIR/backup_script.sh >> /var/log/ocr-scanner/backup.log 2>&1

# Weekly backup report (Sundays at 3 AM)
0 3 * * 0 $APP_DIR/backup_script.sh --report >> /var/log/ocr-scanner/backup-weekly.log 2>&1

# Log rotation check (daily at 1 AM)
0 1 * * * /usr/sbin/logrotate -f /etc/logrotate.d/ocr-scanner >> /var/log/ocr-scanner/logrotate.log 2>&1

# Database maintenance (weekly, Sundays at 4 AM)
0 4 * * 0 $APP_DIR/maintenance_script.sh >> /var/log/ocr-scanner/maintenance.log 2>&1

# Monitor disk space (hourly)
0 * * * * $APP_DIR/monitor_disk.sh >> /var/log/ocr-scanner/disk-monitor.log 2>&1
EOF

    # Install cron jobs
    crontab -l 2>/dev/null | cat - "$cron_file" | crontab -
    rm "$cron_file"
    
    print_success "Cron jobs installed"
}

create_maintenance_script() {
    print_status "Creating database maintenance script..."
    
    cat > "$APP_DIR/maintenance_script.sh" << 'EOF'
#!/bin/bash

# Database Maintenance Script
# OCR Document Scanner
# ===================

set -e

# Database connection settings
DB_USER="ocr_app_user"
DB_NAME="ocr_scanner_prod"
DB_HOST="localhost"
DB_PORT="5432"
export PGPASSWORD="yWpy4FI%nzfHMX1ORQwSrOzUUI5KhLnC"

echo "$(date): Starting database maintenance..."

# PostgreSQL maintenance
echo "Running VACUUM ANALYZE..."
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "VACUUM ANALYZE;"

echo "Updating table statistics..."
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "ANALYZE;"

# Redis maintenance
echo "Running Redis memory optimization..."
redis-cli -a "8tOBE1%xUf6prQZu2yaJ9a97HtBsRrZL" MEMORY PURGE 2>/dev/null || true

echo "$(date): Database maintenance completed"

unset PGPASSWORD
EOF

    chmod +x "$APP_DIR/maintenance_script.sh"
    print_success "Database maintenance script created"
}

create_disk_monitor() {
    print_status "Creating disk space monitoring script..."
    
    cat > "$APP_DIR/monitor_disk.sh" << 'EOF'
#!/bin/bash

# Disk Space Monitoring Script
# OCR Document Scanner
# ===========================

# Thresholds
WARNING_THRESHOLD=80
CRITICAL_THRESHOLD=90

# Check disk usage
DISK_USAGE=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')

if [ "$DISK_USAGE" -ge "$CRITICAL_THRESHOLD" ]; then
    echo "$(date): CRITICAL - Disk usage is ${DISK_USAGE}%"
    # Send alert (implement email/webhook notification here)
    exit 2
elif [ "$DISK_USAGE" -ge "$WARNING_THRESHOLD" ]; then
    echo "$(date): WARNING - Disk usage is ${DISK_USAGE}%"
    exit 1
else
    echo "$(date): OK - Disk usage is ${DISK_USAGE}%"
    exit 0
fi
EOF

    chmod +x "$APP_DIR/monitor_disk.sh"
    print_success "Disk space monitoring script created"
}

create_backup_restore_script() {
    print_status "Creating backup restore script..."
    
    cat > "$APP_DIR/restore_backup.sh" << 'EOF'
#!/bin/bash

# Backup Restore Script
# OCR Document Scanner
# ====================

set -e

BACKUP_BASE_DIR="/var/backups/ocr-scanner"
DB_USER="ocr_app_user"
DB_NAME="ocr_scanner_prod"
DB_HOST="localhost"
DB_PORT="5432"
export PGPASSWORD="yWpy4FI%nzfHMX1ORQwSrOzUUI5KhLnC"

print_usage() {
    echo "Usage: $0 <backup_date> [--postgres-only|--redis-only|--files-only]"
    echo ""
    echo "Examples:"
    echo "  $0 20241201_020000"
    echo "  $0 20241201_020000 --postgres-only"
    echo ""
    echo "Available backups:"
    ls -la "$BACKUP_BASE_DIR/daily/" 2>/dev/null | grep "^d" || echo "No backups found"
}

restore_postgresql() {
    local backup_file="$1"
    echo "Restoring PostgreSQL from: $backup_file"
    
    if [ -f "$backup_file" ]; then
        zcat "$backup_file" | psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME"
        echo "PostgreSQL restore completed"
    else
        echo "PostgreSQL backup file not found: $backup_file"
        exit 1
    fi
}

restore_redis() {
    local backup_file="$1"
    echo "Restoring Redis from: $backup_file"
    
    if [ -f "$backup_file" ]; then
        # Stop Redis, restore RDB file, restart Redis
        redis-cli -a "8tOBE1%xUf6prQZu2yaJ9a97HtBsRrZL" SHUTDOWN NOSAVE || true
        sleep 2
        
        zcat "$backup_file" > /var/lib/redis/dump.rdb
        
        # Restart Redis (method depends on system)
        redis-server /usr/local/etc/redis.conf &
        
        echo "Redis restore completed"
    else
        echo "Redis backup file not found: $backup_file"
        exit 1
    fi
}

restore_files() {
    local backup_file="$1"
    echo "Restoring application files from: $backup_file"
    
    if [ -f "$backup_file" ]; then
        tar -xzf "$backup_file" -C /tmp/
        echo "Files extracted to /tmp/ for manual review"
        echo "Please manually copy needed files to application directory"
    else
        echo "Files backup not found: $backup_file"
        exit 1
    fi
}

main() {
    if [ $# -lt 1 ]; then
        print_usage
        exit 1
    fi
    
    local backup_date="$1"
    local restore_type="${2:-all}"
    local backup_dir="${BACKUP_BASE_DIR}/daily/${backup_date}"
    
    if [ ! -d "$backup_dir" ]; then
        echo "Backup directory not found: $backup_dir"
        print_usage
        exit 1
    fi
    
    echo "Starting restore from backup: $backup_date"
    echo "Backup directory: $backup_dir"
    echo ""
    
    case "$restore_type" in
        --postgres-only)
            restore_postgresql "${backup_dir}/postgresql_backup_${backup_date}.sql.gz"
            ;;
        --redis-only)
            restore_redis "${backup_dir}/redis_backup_${backup_date}.rdb.gz"
            ;;
        --files-only)
            restore_files "${backup_dir}/app_files_${backup_date}.tar.gz"
            ;;
        *)
            echo "Performing full restore..."
            restore_postgresql "${backup_dir}/postgresql_backup_${backup_date}.sql.gz"
            restore_redis "${backup_dir}/redis_backup_${backup_date}.rdb.gz"
            restore_files "${backup_dir}/app_files_${backup_date}.tar.gz"
            ;;
    esac
    
    echo ""
    echo "Restore completed successfully!"
}

main "$@"
EOF

    chmod +x "$APP_DIR/restore_backup.sh"
    print_success "Backup restore script created"
}

test_backup_system() {
    print_status "Testing backup system..."
    
    # Run backup in test mode
    if "$APP_DIR/backup_script.sh" --test; then
        print_success "Backup test completed successfully"
    else
        print_error "Backup test failed"
        return 1
    fi
    
    # Test logrotate
    if sudo logrotate -f /etc/logrotate.d/ocr-scanner; then
        print_success "Log rotation test completed successfully"
    else
        print_error "Log rotation test failed"
        return 1
    fi
}

create_backup_monitoring() {
    print_status "Setting up backup monitoring..."
    
    # Create backup status script
    cat > "$APP_DIR/backup_status.sh" << 'EOF'
#!/bin/bash

# Backup Status Monitoring
# ========================

BACKUP_BASE_DIR="/var/backups/ocr-scanner"

echo "OCR Scanner Backup Status"
echo "========================"
echo "Date: $(date)"
echo ""

# Check recent backups
echo "Recent Daily Backups:"
ls -lt "$BACKUP_BASE_DIR/daily/" | head -5

echo ""
echo "Backup Sizes:"
du -sh "$BACKUP_BASE_DIR/daily/"* | tail -5

echo ""
echo "Disk Usage:"
df -h "$BACKUP_BASE_DIR"

echo ""
echo "Last Backup Log:"
tail -10 /var/log/ocr-scanner/backup.log 2>/dev/null || echo "No backup logs found"
EOF

    chmod +x "$APP_DIR/backup_status.sh"
    print_success "Backup monitoring script created"
}

main() {
    print_status "Setting up automated backups and log rotation for OCR Document Scanner"
    
    # Check prerequisites
    check_prerequisites
    
    # Create directories
    create_backup_directories
    
    # Setup log rotation
    setup_logrotate
    
    # Create maintenance and monitoring scripts
    create_maintenance_script
    create_disk_monitor
    create_backup_restore_script
    create_backup_monitoring
    
    # Setup cron jobs
    setup_cron_jobs
    
    # Test the system
    test_backup_system
    
    print_success "Backup and log rotation setup completed successfully!"
    echo ""
    echo "=========================================="
    echo "Backup Configuration Summary"
    echo "=========================================="
    echo "Backup Directory: $BACKUP_BASE_DIR"
    echo "Retention Period: 30 days"
    echo "Schedule: Daily at 2 AM"
    echo ""
    echo "Scripts Created:"
    echo "- $APP_DIR/backup_script.sh - Main backup script"
    echo "- $APP_DIR/restore_backup.sh - Restore script"
    echo "- $APP_DIR/maintenance_script.sh - Database maintenance"
    echo "- $APP_DIR/monitor_disk.sh - Disk space monitoring"
    echo "- $APP_DIR/backup_status.sh - Backup status checker"
    echo ""
    echo "Cron Jobs Installed:"
    echo "- Daily backup at 2 AM"
    echo "- Log rotation at 1 AM"
    echo "- Weekly maintenance on Sundays at 4 AM"
    echo "- Hourly disk space monitoring"
    echo ""
    echo "Log Files:"
    echo "- /var/log/ocr-scanner/backup.log"
    echo "- /var/log/ocr-scanner/logrotate.log"
    echo "- /var/log/ocr-scanner/maintenance.log"
    echo ""
    echo "Test Commands:"
    echo "- $APP_DIR/backup_script.sh --test"
    echo "- $APP_DIR/backup_status.sh"
    echo "- sudo logrotate -f /etc/logrotate.d/ocr-scanner"
    echo "=========================================="
}

# Run main function
main "$@"
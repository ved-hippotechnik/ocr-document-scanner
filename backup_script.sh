#!/bin/bash

# OCR Document Scanner - Production Backup Script
# ==============================================
# This script handles automated backups of database, files, and logs
# Supports PostgreSQL, Redis, application files, and log rotation

set -e

# Configuration (from .env.production)
BACKUP_BASE_DIR="/var/backups/ocr-scanner"
DATABASE_URL="postgresql://ocr_app_user:yWpy4FI%nzfHMX1ORQwSrOzUUI5KhLnC@localhost:5432/ocr_scanner_prod"
REDIS_PASSWORD="8tOBE1%xUf6prQZu2yaJ9a97HtBsRrZL"
APP_DIR="/Users/vedthampi/CascadeProjects/ocr-document-scanner"
LOG_DIR="${APP_DIR}/backend/logs"
UPLOAD_DIR="${APP_DIR}/uploads"

# Backup settings
RETENTION_DAYS=30
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
DAILY_BACKUP_DIR="${BACKUP_BASE_DIR}/daily/${BACKUP_DATE}"
WEEKLY_BACKUP_DIR="${BACKUP_BASE_DIR}/weekly"
MONTHLY_BACKUP_DIR="${BACKUP_BASE_DIR}/monthly"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] [INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] [SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] [WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] [ERROR]${NC} $1"
}

create_backup_directories() {
    print_status "Creating backup directories..."
    
    mkdir -p "$DAILY_BACKUP_DIR"
    mkdir -p "$WEEKLY_BACKUP_DIR"
    mkdir -p "$MONTHLY_BACKUP_DIR"
    mkdir -p "${BACKUP_BASE_DIR}/logs"
    
    print_success "Backup directories created"
}

backup_postgresql() {
    print_status "Starting PostgreSQL backup..."
    
    local backup_file="${DAILY_BACKUP_DIR}/postgresql_backup_${BACKUP_DATE}.sql"
    local compressed_file="${backup_file}.gz"
    
    # Extract connection details
    local db_user="ocr_app_user"
    local db_name="ocr_scanner_prod"
    local db_host="localhost"
    local db_port="5432"
    
    # Set password in environment
    export PGPASSWORD="yWpy4FI%nzfHMX1ORQwSrOzUUI5KhLnC"
    
    # Create backup
    if pg_dump -h "$db_host" -p "$db_port" -U "$db_user" -d "$db_name" \
               --verbose --clean --no-owner --no-acl \
               --format=plain > "$backup_file" 2>/dev/null; then
        
        # Compress backup
        gzip "$backup_file"
        
        # Calculate size
        local size=$(du -h "$compressed_file" | cut -f1)
        print_success "PostgreSQL backup completed: $compressed_file ($size)"
        
        # Create checksum
        sha256sum "$compressed_file" > "${compressed_file}.sha256"
        
    else
        print_error "PostgreSQL backup failed"
        return 1
    fi
    
    unset PGPASSWORD
}

backup_redis() {
    print_status "Starting Redis backup..."
    
    local backup_file="${DAILY_BACKUP_DIR}/redis_backup_${BACKUP_DATE}.rdb"
    local compressed_file="${backup_file}.gz"
    
    # Force Redis to save current state
    if redis-cli -a "$REDIS_PASSWORD" BGSAVE >/dev/null 2>&1; then
        
        # Wait for background save to complete
        while [ "$(redis-cli -a "$REDIS_PASSWORD" LASTSAVE 2>/dev/null)" = "$(redis-cli -a "$REDIS_PASSWORD" LASTSAVE 2>/dev/null)" ]; do
            sleep 1
        done
        
        # Find Redis data directory and copy RDB file
        local redis_dir="/usr/local/var/db/redis"
        if [ ! -d "$redis_dir" ]; then
            redis_dir="/var/lib/redis"
        fi
        
        if [ -f "${redis_dir}/dump.rdb" ]; then
            cp "${redis_dir}/dump.rdb" "$backup_file"
            gzip "$backup_file"
            
            local size=$(du -h "$compressed_file" | cut -f1)
            print_success "Redis backup completed: $compressed_file ($size)"
            
            # Create checksum
            sha256sum "$compressed_file" > "${compressed_file}.sha256"
        else
            print_warning "Redis RDB file not found at expected location"
        fi
    else
        print_error "Redis backup failed"
        return 1
    fi
}

backup_application_files() {
    print_status "Starting application files backup..."
    
    local backup_file="${DAILY_BACKUP_DIR}/app_files_${BACKUP_DATE}.tar.gz"
    
    # Create list of files/directories to backup
    local backup_list=(
        "backend/app"
        "frontend/src"
        "frontend/public"
        "backend/requirements.txt"
        "frontend/package.json"
        "docker-compose.yml"
        "docker-compose.production.yml"
        ".env.production"
        "setup_*.sh"
        "*.py"
        "*.yml"
        "*.conf"
    )
    
    # Change to app directory
    cd "$APP_DIR"
    
    # Create backup archive
    if tar -czf "$backup_file" "${backup_list[@]}" 2>/dev/null; then
        local size=$(du -h "$backup_file" | cut -f1)
        print_success "Application files backup completed: $backup_file ($size)"
        
        # Create checksum
        sha256sum "$backup_file" > "${backup_file}.sha256"
    else
        print_error "Application files backup failed"
        return 1
    fi
}

backup_uploads() {
    print_status "Starting uploads backup..."
    
    if [ -d "$UPLOAD_DIR" ] && [ "$(ls -A "$UPLOAD_DIR" 2>/dev/null)" ]; then
        local backup_file="${DAILY_BACKUP_DIR}/uploads_${BACKUP_DATE}.tar.gz"
        
        if tar -czf "$backup_file" -C "$(dirname "$UPLOAD_DIR")" "$(basename "$UPLOAD_DIR")" 2>/dev/null; then
            local size=$(du -h "$backup_file" | cut -f1)
            print_success "Uploads backup completed: $backup_file ($size)"
            
            # Create checksum
            sha256sum "$backup_file" > "${backup_file}.sha256"
        else
            print_error "Uploads backup failed"
            return 1
        fi
    else
        print_warning "No uploads directory found or directory is empty"
    fi
}

backup_logs() {
    print_status "Starting logs backup..."
    
    if [ -d "$LOG_DIR" ] && [ "$(ls -A "$LOG_DIR" 2>/dev/null)" ]; then
        local backup_file="${DAILY_BACKUP_DIR}/logs_${BACKUP_DATE}.tar.gz"
        
        # Backup logs older than 1 day
        find "$LOG_DIR" -name "*.log*" -type f -mtime +1 -print0 | \
            tar -czf "$backup_file" --null -T - 2>/dev/null || true
        
        if [ -f "$backup_file" ]; then
            local size=$(du -h "$backup_file" | cut -f1)
            print_success "Logs backup completed: $backup_file ($size)"
            
            # Create checksum
            sha256sum "$backup_file" > "${backup_file}.sha256"
        else
            print_warning "No old logs found for backup"
        fi
    else
        print_warning "No logs directory found or directory is empty"
    fi
}

rotate_logs() {
    print_status "Starting log rotation..."
    
    if [ -d "$LOG_DIR" ]; then
        cd "$LOG_DIR"
        
        # Rotate application logs
        for log_file in *.log; do
            if [ -f "$log_file" ] && [ -s "$log_file" ]; then
                # Create rotated log name
                local rotated_name="${log_file}.$(date +%Y%m%d)"
                
                # Move current log to rotated name
                mv "$log_file" "$rotated_name"
                
                # Compress rotated log
                gzip "$rotated_name"
                
                # Create new empty log file
                touch "$log_file"
                
                print_success "Rotated log: $log_file -> ${rotated_name}.gz"
            fi
        done
        
        # Remove old compressed logs (older than retention period)
        find . -name "*.log.*.gz" -type f -mtime +$RETENTION_DAYS -delete
        
        print_success "Log rotation completed"
    else
        print_warning "Logs directory not found"
    fi
}

cleanup_old_backups() {
    print_status "Cleaning up old backups..."
    
    # Remove daily backups older than retention period
    if [ -d "${BACKUP_BASE_DIR}/daily" ]; then
        find "${BACKUP_BASE_DIR}/daily" -type d -mtime +$RETENTION_DAYS -exec rm -rf {} \; 2>/dev/null || true
        print_success "Old daily backups cleaned up"
    fi
    
    # Keep only 4 weekly backups
    if [ -d "$WEEKLY_BACKUP_DIR" ]; then
        ls -t "$WEEKLY_BACKUP_DIR" | tail -n +5 | xargs -r rm -rf
        print_success "Old weekly backups cleaned up"
    fi
    
    # Keep only 12 monthly backups
    if [ -d "$MONTHLY_BACKUP_DIR" ]; then
        ls -t "$MONTHLY_BACKUP_DIR" | tail -n +13 | xargs -r rm -rf
        print_success "Old monthly backups cleaned up"
    fi
}

create_weekly_backup() {
    # Create weekly backup on Sundays
    if [ "$(date +%u)" -eq 7 ]; then
        print_status "Creating weekly backup..."
        local weekly_dir="${WEEKLY_BACKUP_DIR}/week_$(date +%Y_W%V)"
        cp -r "$DAILY_BACKUP_DIR" "$weekly_dir"
        print_success "Weekly backup created: $weekly_dir"
    fi
}

create_monthly_backup() {
    # Create monthly backup on the 1st of each month
    if [ "$(date +%d)" -eq 1 ]; then
        print_status "Creating monthly backup..."
        local monthly_dir="${MONTHLY_BACKUP_DIR}/month_$(date +%Y_%m)"
        cp -r "$DAILY_BACKUP_DIR" "$monthly_dir"
        print_success "Monthly backup created: $monthly_dir"
    fi
}

generate_backup_report() {
    print_status "Generating backup report..."
    
    local report_file="${DAILY_BACKUP_DIR}/backup_report_${BACKUP_DATE}.txt"
    
    cat > "$report_file" << EOF
OCR Document Scanner - Backup Report
=====================================
Date: $(date)
Backup Directory: $DAILY_BACKUP_DIR

Files Created:
$(ls -la "$DAILY_BACKUP_DIR")

Disk Usage:
$(du -sh "$DAILY_BACKUP_DIR")

Checksums:
$(find "$DAILY_BACKUP_DIR" -name "*.sha256" -exec cat {} \;)

System Information:
- Hostname: $(hostname)
- Uptime: $(uptime)
- Disk Space: $(df -h)

EOF
    
    print_success "Backup report generated: $report_file"
}

send_backup_notification() {
    local status=$1
    local log_file="${BACKUP_BASE_DIR}/logs/backup_$(date +%Y%m%d).log"
    
    if [ "$status" = "success" ]; then
        echo "$(date): Backup completed successfully" >> "$log_file"
        print_success "Backup notification logged"
    else
        echo "$(date): Backup failed" >> "$log_file"
        print_error "Backup failure logged"
    fi
    
    # Here you could add email notification or webhook call
    # curl -X POST -H 'Content-type: application/json' \
    #      --data '{"text":"Backup Status: '$status'"}' \
    #      YOUR_WEBHOOK_URL
}

main() {
    echo "=========================================="
    echo "OCR Scanner Production Backup"
    echo "=========================================="
    echo "Started: $(date)"
    echo ""
    
    # Initialize backup
    create_backup_directories
    
    # Track backup success
    local backup_success=true
    
    # Perform backups
    backup_postgresql || backup_success=false
    backup_redis || backup_success=false
    backup_application_files || backup_success=false
    backup_uploads || backup_success=false
    backup_logs || backup_success=false
    
    # Log rotation
    rotate_logs || backup_success=false
    
    # Cleanup
    cleanup_old_backups
    
    # Create periodic backups
    create_weekly_backup
    create_monthly_backup
    
    # Generate report
    generate_backup_report
    
    # Send notification
    if [ "$backup_success" = true ]; then
        send_backup_notification "success"
        print_success "All backup operations completed successfully!"
    else
        send_backup_notification "failure"
        print_error "Some backup operations failed. Check logs for details."
        exit 1
    fi
    
    echo ""
    echo "=========================================="
    echo "Backup Summary"
    echo "=========================================="
    echo "Backup Location: $DAILY_BACKUP_DIR"
    echo "Total Size: $(du -sh "$DAILY_BACKUP_DIR" | cut -f1)"
    echo "Files Created: $(ls -1 "$DAILY_BACKUP_DIR" | wc -l)"
    echo "Completed: $(date)"
    echo "=========================================="
}

# Handle command line options
case "$1" in
    --test)
        echo "Running backup in test mode..."
        BACKUP_BASE_DIR="/tmp/ocr-backup-test"
        main
        ;;
    --help)
        echo "OCR Scanner Backup Script"
        echo "Usage: $0 [--test|--help]"
        echo ""
        echo "Options:"
        echo "  --test    Run backup in test mode (uses /tmp directory)"
        echo "  --help    Show this help message"
        ;;
    *)
        main
        ;;
esac
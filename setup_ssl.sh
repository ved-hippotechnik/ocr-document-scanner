#!/bin/bash

# SSL Certificate Setup Script
# OCR Document Scanner Application
# ==============================

set -e

echo "=========================================="
echo "SSL Certificate Setup"
echo "=========================================="
echo "$(date)"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOMAIN="your-domain.com"
EMAIL="admin@your-domain.com"
SSL_DIR="/etc/ssl/ocr-scanner"
NGINX_SITES_DIR="/etc/nginx/sites-available"
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
    
    # Check if running as root for some operations
    if [[ $EUID -eq 0 ]]; then
        print_warning "Running as root. Some operations may need adjustment for security."
    fi
    
    # Check for openssl
    if ! command -v openssl &> /dev/null; then
        print_error "OpenSSL is not installed"
        exit 1
    fi
    
    print_success "Prerequisites checked"
}

create_ssl_directories() {
    print_status "Creating SSL directories..."
    
    # Create SSL directories
    sudo mkdir -p "$SSL_DIR"/{certs,private,csr}
    sudo mkdir -p /var/log/ssl
    
    # Set proper permissions
    sudo chmod 755 "$SSL_DIR"
    sudo chmod 700 "$SSL_DIR/private"
    sudo chmod 755 "$SSL_DIR/certs"
    sudo chmod 755 "$SSL_DIR/csr"
    
    print_success "SSL directories created"
}

generate_self_signed_certificate() {
    print_status "Generating self-signed certificate for development/testing..."
    
    local cert_file="$SSL_DIR/certs/ocr-scanner-selfsigned.crt"
    local key_file="$SSL_DIR/private/ocr-scanner-selfsigned.key"
    
    # Generate private key
    sudo openssl genrsa -out "$key_file" 4096
    sudo chmod 600 "$key_file"
    
    # Generate certificate
    sudo openssl req -new -x509 -key "$key_file" -out "$cert_file" -days 365 \
        -subj "/C=US/ST=State/L=City/O=OCR Scanner/OU=IT/CN=$DOMAIN/emailAddress=$EMAIL"
    
    sudo chmod 644 "$cert_file"
    
    print_success "Self-signed certificate generated"
    print_warning "Self-signed certificates should only be used for development/testing"
    print_status "Certificate: $cert_file"
    print_status "Private key: $key_file"
}

setup_lets_encrypt() {
    print_status "Setting up Let's Encrypt configuration..."
    
    # Check if certbot is installed
    if ! command -v certbot &> /dev/null; then
        print_status "Installing certbot..."
        
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            if command -v brew &> /dev/null; then
                brew install certbot
            else
                print_error "Homebrew not found. Please install certbot manually."
                exit 1
            fi
        elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
            # Linux
            if [ -f /etc/debian_version ]; then
                sudo apt update
                sudo apt install -y certbot python3-certbot-nginx
            elif [ -f /etc/redhat-release ]; then
                sudo dnf install -y certbot python3-certbot-nginx
            else
                print_error "Unsupported Linux distribution for automatic certbot installation"
                exit 1
            fi
        fi
    fi
    
    # Create certbot script for automated renewal
    cat > "$APP_DIR/renew_ssl.sh" << EOF
#!/bin/bash

# SSL Certificate Renewal Script
# ==============================

echo "Renewing SSL certificates..."

# Renew certificates
if certbot renew --quiet --no-self-upgrade; then
    echo "\$(date): SSL certificate renewal successful" >> /var/log/ssl/renewal.log
    
    # Reload services that use the certificates
    # systemctl reload nginx || true
    # systemctl reload ocr-scanner || true
    
    echo "SSL certificates renewed successfully"
else
    echo "\$(date): SSL certificate renewal failed" >> /var/log/ssl/renewal.log
    echo "SSL certificate renewal failed"
    exit 1
fi
EOF
    
    chmod +x "$APP_DIR/renew_ssl.sh"
    
    print_success "Let's Encrypt configuration prepared"
    print_status "To obtain certificates, run:"
    print_status "sudo certbot --nginx -d $DOMAIN -m $EMAIL --agree-tos --non-interactive"
}

create_nginx_ssl_config() {
    print_status "Creating Nginx SSL configuration..."
    
    # Create Nginx configuration for OCR Scanner
    local nginx_config="$APP_DIR/nginx-ssl.conf"
    
    cat > "$nginx_config" << EOF
# OCR Document Scanner - Nginx SSL Configuration
# ============================================

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name $DOMAIN;
    
    # Let's Encrypt challenge location
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }
    
    # Redirect everything else to HTTPS
    location / {
        return 301 https://\$server_name\$request_uri;
    }
}

# HTTPS Server Configuration
server {
    listen 443 ssl http2;
    server_name $DOMAIN;
    
    # SSL Configuration
    ssl_certificate $SSL_DIR/certs/ocr-scanner.crt;
    ssl_certificate_key $SSL_DIR/private/ocr-scanner.key;
    
    # SSL Settings (Mozilla Modern Configuration)
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 1d;
    ssl_session_tickets off;
    
    # OCSP Stapling
    ssl_stapling on;
    ssl_stapling_verify on;
    ssl_trusted_certificate $SSL_DIR/certs/chain.pem;
    resolver 8.8.8.8 8.8.4.4 valid=300s;
    resolver_timeout 5s;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=63072000" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
    
    # Logging
    access_log /var/log/nginx/ocr-scanner-access.log;
    error_log /var/log/nginx/ocr-scanner-error.log;
    
    # Root directory for static files
    root $APP_DIR/frontend/build;
    index index.html;
    
    # API Proxy to Flask Backend
    location /api/ {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header X-Forwarded-Host \$server_name;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # Buffer settings for file uploads
        proxy_request_buffering off;
        proxy_max_temp_file_size 0;
        client_max_body_size 50M;
    }
    
    # Health check endpoint
    location /health {
        proxy_pass http://127.0.0.1:5001/health;
        proxy_set_header Host \$host;
        access_log off;
    }
    
    # Metrics endpoint (restrict access)
    location /metrics {
        proxy_pass http://127.0.0.1:5001/metrics;
        proxy_set_header Host \$host;
        
        # Restrict access to monitoring systems
        allow 127.0.0.1;
        allow 10.0.0.0/8;
        allow 172.16.0.0/12;
        allow 192.168.0.0/16;
        deny all;
    }
    
    # Static files with caching
    location /static/ {
        expires 1y;
        add_header Cache-Control "public, immutable";
        try_files \$uri \$uri/ =404;
    }
    
    # Frontend routing (React Router)
    location / {
        try_files \$uri \$uri/ /index.html;
        
        # Security headers for HTML
        add_header X-Frame-Options DENY always;
        add_header X-Content-Type-Options nosniff always;
    }
    
    # Deny access to sensitive files
    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }
    
    location ~ \.(env|config|ini|log|sh|sql|bak)$ {
        deny all;
        access_log off;
        log_not_found off;
    }
}
EOF
    
    print_success "Nginx SSL configuration created: $nginx_config"
}

create_apache_ssl_config() {
    print_status "Creating Apache SSL configuration..."
    
    local apache_config="$APP_DIR/apache-ssl.conf"
    
    cat > "$apache_config" << EOF
# OCR Document Scanner - Apache SSL Configuration
# =============================================

<IfModule mod_ssl.c>
    # HTTP to HTTPS Redirect
    <VirtualHost *:80>
        ServerName $DOMAIN
        DocumentRoot $APP_DIR/frontend/build
        
        # Let's Encrypt challenge
        Alias /.well-known/acme-challenge/ /var/www/html/.well-known/acme-challenge/
        <Directory "/var/www/html/.well-known/acme-challenge/">
            Options None
            AllowOverride None
            Require all granted
        </Directory>
        
        # Redirect to HTTPS
        RewriteEngine On
        RewriteCond %{HTTPS} off
        RewriteRule ^(.*)$ https://%{HTTP_HOST}%{REQUEST_URI} [R=301,L]
    </VirtualHost>
    
    # HTTPS Virtual Host
    <VirtualHost *:443>
        ServerName $DOMAIN
        DocumentRoot $APP_DIR/frontend/build
        
        # SSL Configuration
        SSLEngine on
        SSLCertificateFile $SSL_DIR/certs/ocr-scanner.crt
        SSLCertificateKeyFile $SSL_DIR/private/ocr-scanner.key
        SSLCertificateChainFile $SSL_DIR/certs/chain.pem
        
        # SSL Security Settings
        SSLProtocol all -SSLv3 -TLSv1 -TLSv1.1
        SSLCipherSuite ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384
        SSLHonorCipherOrder off
        SSLSessionTickets off
        
        # OCSP Stapling
        SSLUseStapling on
        SSLStaplingCache "shmcb:/var/run/ocsp(128000)"
        
        # Security Headers
        Header always set Strict-Transport-Security "max-age=63072000"
        Header always set X-Frame-Options DENY
        Header always set X-Content-Type-Options nosniff
        Header always set X-XSS-Protection "1; mode=block"
        Header always set Referrer-Policy "no-referrer-when-downgrade"
        
        # Logging
        ErrorLog /var/log/apache2/ocr-scanner-ssl-error.log
        CustomLog /var/log/apache2/ocr-scanner-ssl-access.log combined
        
        # API Proxy
        ProxyPreserveHost On
        ProxyRequests Off
        ProxyPass /api/ http://127.0.0.1:5001/api/
        ProxyPassReverse /api/ http://127.0.0.1:5001/api/
        
        # Static files
        <Directory "$APP_DIR/frontend/build">
            Options -Indexes
            AllowOverride None
            Require all granted
            
            # Enable compression
            <IfModule mod_deflate.c>
                SetOutputFilter DEFLATE
                SetEnvIfNoCase Request_URI \.(?:gif|jpe?g|png)$ no-gzip dont-vary
            </IfModule>
            
            # Cache static resources
            <IfModule mod_expires.c>
                ExpiresActive on
                ExpiresByType text/css "access plus 1 year"
                ExpiresByType application/javascript "access plus 1 year"
                ExpiresByType image/png "access plus 1 year"
                ExpiresByType image/jpg "access plus 1 year"
                ExpiresByType image/jpeg "access plus 1 year"
            </IfModule>
        </Directory>
        
        # Deny access to sensitive files
        <Files ~ "\.(env|config|ini|log|sh|sql|bak)$">
            Require all denied
        </Files>
        
        <DirectoryMatch "^\.|/\.">
            Require all denied
        </DirectoryMatch>
    </VirtualHost>
</IfModule>
EOF
    
    print_success "Apache SSL configuration created: $apache_config"
}

create_ssl_test_script() {
    print_status "Creating SSL test script..."
    
    cat > "$APP_DIR/test_ssl.sh" << EOF
#!/bin/bash

# SSL Configuration Test Script
# =============================

echo "SSL Configuration Test"
echo "======================"
echo "Domain: $DOMAIN"
echo "Date: \$(date)"
echo ""

# Test certificate validity
echo "1. Certificate Validity Test:"
if [ -f "$SSL_DIR/certs/ocr-scanner.crt" ]; then
    echo "Certificate file exists"
    
    # Check certificate expiration
    openssl x509 -in "$SSL_DIR/certs/ocr-scanner.crt" -noout -dates
    
    # Check certificate details
    echo ""
    echo "Certificate Subject:"
    openssl x509 -in "$SSL_DIR/certs/ocr-scanner.crt" -noout -subject
    
    echo ""
    echo "Certificate Issuer:"
    openssl x509 -in "$SSL_DIR/certs/ocr-scanner.crt" -noout -issuer
else
    echo "❌ Certificate file not found"
fi

echo ""
echo "2. Private Key Test:"
if [ -f "$SSL_DIR/private/ocr-scanner.key" ]; then
    echo "✅ Private key file exists"
    
    # Verify key matches certificate
    cert_hash=\$(openssl x509 -noout -modulus -in "$SSL_DIR/certs/ocr-scanner.crt" | openssl md5)
    key_hash=\$(openssl rsa -noout -modulus -in "$SSL_DIR/private/ocr-scanner.key" | openssl md5)
    
    if [ "\$cert_hash" = "\$key_hash" ]; then
        echo "✅ Certificate and private key match"
    else
        echo "❌ Certificate and private key do not match"
    fi
else
    echo "❌ Private key file not found"
fi

echo ""
echo "3. SSL Connection Test:"
if command -v curl &> /dev/null; then
    if curl -I https://$DOMAIN 2>/dev/null | head -1 | grep -q "200 OK"; then
        echo "✅ HTTPS connection successful"
    else
        echo "❌ HTTPS connection failed"
    fi
else
    echo "⚠️ curl not available for connection test"
fi

echo ""
echo "4. SSL Grade Test (if SSL Labs API is available):"
if command -v curl &> /dev/null; then
    echo "You can test SSL configuration at:"
    echo "https://www.ssllabs.com/ssltest/analyze.html?d=$DOMAIN"
fi

echo ""
echo "5. Configuration Files:"
echo "Certificate: $SSL_DIR/certs/ocr-scanner.crt"
echo "Private Key: $SSL_DIR/private/ocr-scanner.key"
echo "Nginx Config: $APP_DIR/nginx-ssl.conf"
echo "Apache Config: $APP_DIR/apache-ssl.conf"
echo ""
echo "Test completed at: \$(date)"
EOF
    
    chmod +x "$APP_DIR/test_ssl.sh"
    print_success "SSL test script created"
}

setup_ssl_monitoring() {
    print_status "Setting up SSL certificate monitoring..."
    
    cat > "$APP_DIR/monitor_ssl.sh" << EOF
#!/bin/bash

# SSL Certificate Monitoring Script
# =================================

CERT_FILE="$SSL_DIR/certs/ocr-scanner.crt"
WARNING_DAYS=30
CRITICAL_DAYS=7

if [ ! -f "\$CERT_FILE" ]; then
    echo "CRITICAL: Certificate file not found: \$CERT_FILE"
    exit 2
fi

# Get certificate expiration date
EXPIRE_DATE=\$(openssl x509 -noout -dates -in "\$CERT_FILE" | grep "notAfter" | cut -d= -f2)
EXPIRE_TIMESTAMP=\$(date -d "\$EXPIRE_DATE" +%s)
CURRENT_TIMESTAMP=\$(date +%s)
DAYS_TO_EXPIRE=\$(( (EXPIRE_TIMESTAMP - CURRENT_TIMESTAMP) / 86400 ))

echo "Certificate expires on: \$EXPIRE_DATE"
echo "Days until expiration: \$DAYS_TO_EXPIRE"

if [ \$DAYS_TO_EXPIRE -le \$CRITICAL_DAYS ]; then
    echo "CRITICAL: Certificate expires in \$DAYS_TO_EXPIRE days"
    exit 2
elif [ \$DAYS_TO_EXPIRE -le \$WARNING_DAYS ]; then
    echo "WARNING: Certificate expires in \$DAYS_TO_EXPIRE days"
    exit 1
else
    echo "OK: Certificate is valid for \$DAYS_TO_EXPIRE days"
    exit 0
fi
EOF
    
    chmod +x "$APP_DIR/monitor_ssl.sh"
    
    # Add to cron for daily monitoring
    (crontab -l 2>/dev/null; echo "0 6 * * * $APP_DIR/monitor_ssl.sh >> /var/log/ssl/monitor.log 2>&1") | crontab -
    
    print_success "SSL certificate monitoring configured"
}

main() {
    print_status "Setting up SSL certificates for OCR Document Scanner"
    
    # Check prerequisites
    check_prerequisites
    
    # Create directories
    create_ssl_directories
    
    # Generate self-signed certificate for development
    generate_self_signed_certificate
    
    # Setup Let's Encrypt
    setup_lets_encrypt
    
    # Create web server configurations
    create_nginx_ssl_config
    create_apache_ssl_config
    
    # Create test and monitoring scripts
    create_ssl_test_script
    setup_ssl_monitoring
    
    print_success "SSL certificate setup completed!"
    echo ""
    echo "=========================================="
    echo "SSL Configuration Summary"
    echo "=========================================="
    echo "Domain: $DOMAIN"
    echo "SSL Directory: $SSL_DIR"
    echo ""
    echo "Certificates:"
    echo "- Self-signed (dev/test): $SSL_DIR/certs/ocr-scanner-selfsigned.crt"
    echo "- Production: $SSL_DIR/certs/ocr-scanner.crt"
    echo ""
    echo "Configuration Files:"
    echo "- Nginx: $APP_DIR/nginx-ssl.conf"
    echo "- Apache: $APP_DIR/apache-ssl.conf"
    echo ""
    echo "Scripts:"
    echo "- Test SSL: $APP_DIR/test_ssl.sh"
    echo "- Monitor SSL: $APP_DIR/monitor_ssl.sh"
    echo "- Renew SSL: $APP_DIR/renew_ssl.sh"
    echo ""
    echo "Next Steps:"
    echo "1. Update $DOMAIN in configuration files"
    echo "2. For production, obtain Let's Encrypt certificate:"
    echo "   sudo certbot --nginx -d $DOMAIN -m $EMAIL"
    echo "3. Copy nginx-ssl.conf to /etc/nginx/sites-available/"
    echo "4. Enable the site: sudo ln -s /etc/nginx/sites-available/ocr-scanner /etc/nginx/sites-enabled/"
    echo "5. Test configuration: sudo nginx -t"
    echo "6. Reload nginx: sudo systemctl reload nginx"
    echo "7. Test SSL: $APP_DIR/test_ssl.sh"
    echo "=========================================="
}

# Handle command line options
case "\$1" in
    --domain)
        DOMAIN="\$2"
        main
        ;;
    --help)
        echo "SSL Setup Script for OCR Document Scanner"
        echo "Usage: \$0 [--domain DOMAIN|--help]"
        echo ""
        echo "Options:"
        echo "  --domain DOMAIN  Set the domain name (default: $DOMAIN)"
        echo "  --help          Show this help message"
        ;;
    *)
        main
        ;;
esac
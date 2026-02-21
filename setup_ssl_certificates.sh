#!/bin/bash

# SSL/TLS Certificate Setup Script for OCR Document Scanner
# This script helps set up SSL certificates for production deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
DOMAIN=""
EMAIL=""
CERT_TYPE="letsencrypt"
NGINX_CONFIG=false

# Functions
print_header() {
    echo -e "${BLUE}=================================${NC}"
    echo -e "${BLUE}SSL/TLS CERTIFICATE SETUP${NC}"
    echo -e "${BLUE}=================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -d, --domain DOMAIN     Domain name for the certificate"
    echo "  -e, --email EMAIL       Email for certificate registration"
    echo "  -t, --type TYPE         Certificate type: letsencrypt, self-signed, or existing"
    echo "  -n, --nginx             Generate Nginx configuration"
    echo "  -h, --help              Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 --domain ocr.example.com --email admin@example.com --type letsencrypt"
    echo "  $0 --domain localhost --type self-signed"
    echo "  $0 --domain ocr.example.com --type existing"
}

check_dependencies() {
    echo "Checking dependencies..."
    
    if [ "$CERT_TYPE" = "letsencrypt" ]; then
        if ! command -v certbot &> /dev/null; then
            print_warning "Certbot not found. Installing..."
            if command -v apt-get &> /dev/null; then
                sudo apt-get update
                sudo apt-get install -y certbot python3-certbot-nginx
            elif command -v yum &> /dev/null; then
                sudo yum install -y certbot python3-certbot-nginx
            elif command -v brew &> /dev/null; then
                brew install certbot
            else
                print_error "Please install Certbot manually"
                exit 1
            fi
        fi
        print_success "Certbot is available"
    fi
    
    if [ "$CERT_TYPE" = "self-signed" ]; then
        if ! command -v openssl &> /dev/null; then
            print_error "OpenSSL not found. Please install OpenSSL."
            exit 1
        fi
        print_success "OpenSSL is available"
    fi
}

setup_letsencrypt() {
    echo "Setting up Let's Encrypt certificate for $DOMAIN..."
    
    # Check if domain is reachable
    if ! ping -c 1 "$DOMAIN" &> /dev/null; then
        print_warning "Domain $DOMAIN is not reachable. Make sure:"
        print_warning "1. DNS is configured to point to this server"
        print_warning "2. Port 80 and 443 are open"
        print_warning "3. No other service is running on port 80"
    fi
    
    # Stop any service running on port 80
    if command -v nginx &> /dev/null; then
        sudo nginx -t && sudo nginx -s stop || true
    fi
    
    if command -v apache2 &> /dev/null; then
        sudo systemctl stop apache2 || true
    fi
    
    # Request certificate
    sudo certbot certonly --standalone \
        --preferred-challenges http \
        --email "$EMAIL" \
        --agree-tos \
        --no-eff-email \
        -d "$DOMAIN"
    
    if [ $? -eq 0 ]; then
        print_success "Let's Encrypt certificate obtained successfully"
        
        # Set certificate paths in environment
        CERT_PATH="/etc/letsencrypt/live/$DOMAIN/fullchain.pem"
        KEY_PATH="/etc/letsencrypt/live/$DOMAIN/privkey.pem"
        
        echo ""
        print_success "Certificate files:"
        echo "SSL_CERT_PATH=$CERT_PATH"
        echo "SSL_KEY_PATH=$KEY_PATH"
        
        # Set up automatic renewal
        (crontab -l 2>/dev/null; echo "0 12 * * * /usr/bin/certbot renew --quiet") | crontab -
        print_success "Automatic renewal set up"
    else
        print_error "Failed to obtain Let's Encrypt certificate"
        return 1
    fi
}

setup_self_signed() {
    echo "Creating self-signed certificate for $DOMAIN..."
    
    # Create certificate directory
    CERT_DIR="./ssl_certificates"
    mkdir -p "$CERT_DIR"
    
    # Generate private key
    openssl genrsa -out "$CERT_DIR/private.key" 4096
    
    # Generate certificate signing request
    cat > "$CERT_DIR/cert.conf" << EOF
[req]
default_bits = 4096
prompt = no
default_md = sha256
distinguished_name = dn
req_extensions = v3_req

[dn]
C=US
ST=State
L=City
O=Organization
OU=OrgUnit
CN=$DOMAIN

[v3_req]
basicConstraints = CA:FALSE
keyUsage = nonRepudiation, digitalSignature, keyEncipherment
subjectAltName = @alt_names

[alt_names]
DNS.1 = $DOMAIN
DNS.2 = localhost
IP.1 = 127.0.0.1
EOF
    
    # Generate self-signed certificate
    openssl req -new -x509 -key "$CERT_DIR/private.key" \
        -out "$CERT_DIR/certificate.crt" \
        -days 365 \
        -config "$CERT_DIR/cert.conf" \
        -extensions v3_req
    
    print_success "Self-signed certificate created"
    
    CERT_PATH="$(pwd)/$CERT_DIR/certificate.crt"
    KEY_PATH="$(pwd)/$CERT_DIR/private.key"
    
    echo ""
    print_success "Certificate files:"
    echo "SSL_CERT_PATH=$CERT_PATH"
    echo "SSL_KEY_PATH=$KEY_PATH"
    
    print_warning "Self-signed certificates will show browser warnings"
    print_warning "Only use for development or internal services"
}

setup_existing_certificates() {
    echo "Setting up existing certificates..."
    
    echo "Please provide the paths to your existing certificate files:"
    read -p "Certificate file path (.crt or .pem): " CERT_PATH
    read -p "Private key file path (.key): " KEY_PATH
    
    # Validate certificate files
    if [ ! -f "$CERT_PATH" ]; then
        print_error "Certificate file not found: $CERT_PATH"
        return 1
    fi
    
    if [ ! -f "$KEY_PATH" ]; then
        print_error "Private key file not found: $KEY_PATH"
        return 1
    fi
    
    # Verify certificate
    if openssl x509 -in "$CERT_PATH" -text -noout &> /dev/null; then
        print_success "Certificate file is valid"
    else
        print_error "Invalid certificate file"
        return 1
    fi
    
    # Verify private key
    if openssl rsa -in "$KEY_PATH" -check -noout &> /dev/null; then
        print_success "Private key file is valid"
    else
        print_error "Invalid private key file"
        return 1
    fi
    
    # Check if certificate and key match
    cert_hash=$(openssl x509 -noout -modulus -in "$CERT_PATH" | openssl md5)
    key_hash=$(openssl rsa -noout -modulus -in "$KEY_PATH" | openssl md5)
    
    if [ "$cert_hash" = "$key_hash" ]; then
        print_success "Certificate and private key match"
    else
        print_error "Certificate and private key do not match"
        return 1
    fi
    
    echo ""
    print_success "Certificate files validated:"
    echo "SSL_CERT_PATH=$CERT_PATH"
    echo "SSL_KEY_PATH=$KEY_PATH"
}

generate_nginx_config() {
    if [ "$NGINX_CONFIG" = true ]; then
        echo "Generating Nginx configuration..."
        
        cat > "nginx_ssl_config.conf" << EOF
server {
    listen 80;
    server_name $DOMAIN;
    
    # Redirect HTTP to HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name $DOMAIN;
    
    # SSL Configuration
    ssl_certificate $CERT_PATH;
    ssl_certificate_key $KEY_PATH;
    
    # SSL Security Settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-SHA256:ECDHE-RSA-AES256-SHA384;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # Proxy to Flask application
    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header X-Forwarded-Host \$host;
        proxy_set_header X-Forwarded-Port \$server_port;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Static files (if any)
    location /static {
        alias /path/to/your/static/files;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Health check endpoint
    location /health {
        proxy_pass http://127.0.0.1:5001/health;
        access_log off;
    }
}
EOF
        
        print_success "Nginx configuration saved to nginx_ssl_config.conf"
        print_warning "Please review and customize the configuration before using it"
    fi
}

update_env_file() {
    echo ""
    echo "Updating .env.production with SSL certificate paths..."
    
    if [ -f ".env.production" ]; then
        # Update existing file
        sed -i.bak "s|^SSL_CERT_PATH=.*|SSL_CERT_PATH=$CERT_PATH|" .env.production
        sed -i.bak "s|^SSL_KEY_PATH=.*|SSL_KEY_PATH=$KEY_PATH|" .env.production
        print_success "Updated .env.production file"
    else
        # Create minimal SSL config
        cat >> ".env.production" << EOF

# SSL Configuration (generated by setup_ssl_certificates.sh)
SSL_CERT_PATH=$CERT_PATH
SSL_KEY_PATH=$KEY_PATH
EOF
        print_success "Added SSL configuration to .env.production"
    fi
}

show_next_steps() {
    echo ""
    print_header
    echo -e "${GREEN}SSL/TLS Setup Complete!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Update your .env.production file with the certificate paths shown above"
    echo "2. Configure your web server (Nginx/Apache) to use the certificates"
    echo "3. Test the SSL configuration with your domain"
    echo "4. Update your application to use HTTPS"
    echo "5. Set up automatic certificate renewal (if using Let's Encrypt)"
    echo ""
    
    if [ "$CERT_TYPE" = "letsencrypt" ]; then
        echo "Let's Encrypt specific:"
        echo "- Certificates will auto-renew via cron job"
        echo "- Test renewal: sudo certbot renew --dry-run"
    fi
    
    if [ "$CERT_TYPE" = "self-signed" ]; then
        echo "Self-signed certificate notes:"
        echo "- Browsers will show security warnings"
        echo "- Consider using Let's Encrypt for production"
        echo "- Certificate expires in 365 days"
    fi
    
    echo ""
    echo "Test your SSL setup:"
    echo "- https://www.ssllabs.com/ssltest/"
    echo "- curl -I https://$DOMAIN"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--domain)
            DOMAIN="$2"
            shift 2
            ;;
        -e|--email)
            EMAIL="$2"
            shift 2
            ;;
        -t|--type)
            CERT_TYPE="$2"
            shift 2
            ;;
        -n|--nginx)
            NGINX_CONFIG=true
            shift
            ;;
        -h|--help)
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

# Main execution
main() {
    print_header
    
    # Validate inputs
    if [ -z "$DOMAIN" ]; then
        print_error "Domain is required. Use -d or --domain"
        show_usage
        exit 1
    fi
    
    if [ "$CERT_TYPE" = "letsencrypt" ] && [ -z "$EMAIL" ]; then
        print_error "Email is required for Let's Encrypt. Use -e or --email"
        show_usage
        exit 1
    fi
    
    if [ "$CERT_TYPE" != "letsencrypt" ] && [ "$CERT_TYPE" != "self-signed" ] && [ "$CERT_TYPE" != "existing" ]; then
        print_error "Invalid certificate type. Use: letsencrypt, self-signed, or existing"
        exit 1
    fi
    
    echo "Configuration:"
    echo "Domain: $DOMAIN"
    echo "Certificate Type: $CERT_TYPE"
    [ -n "$EMAIL" ] && echo "Email: $EMAIL"
    echo ""
    
    # Check dependencies
    check_dependencies
    
    # Set up certificates based on type
    case "$CERT_TYPE" in
        "letsencrypt")
            setup_letsencrypt
            ;;
        "self-signed")
            setup_self_signed
            ;;
        "existing")
            setup_existing_certificates
            ;;
    esac
    
    # Generate additional configurations
    generate_nginx_config
    update_env_file
    
    # Show next steps
    show_next_steps
}

# Run main function
main
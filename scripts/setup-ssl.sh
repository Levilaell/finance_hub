#!/bin/bash
# SSL/HTTPS setup script for FinanceHub SaaS
# This script sets up Let's Encrypt SSL certificates and configures Nginx

set -e

# Configuration
DOMAIN="yourdomain.com"
EMAIL="admin@yourdomain.com"
NGINX_CONF_DIR="/etc/nginx/sites-available"
NGINX_ENABLED_DIR="/etc/nginx/sites-enabled"
SSL_DIR="/etc/ssl"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# Check if script is run as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "This script must be run as root"
        exit 1
    fi
}

# Install required packages
install_dependencies() {
    print_status "Installing dependencies..."
    
    # Update package list
    apt-get update
    
    # Install Nginx if not installed
    if ! command -v nginx &> /dev/null; then
        print_status "Installing Nginx..."
        apt-get install -y nginx
    fi
    
    # Install Certbot for Let's Encrypt
    if ! command -v certbot &> /dev/null; then
        print_status "Installing Certbot..."
        apt-get install -y certbot python3-certbot-nginx
    fi
    
    # Install other utilities
    apt-get install -y openssl curl
}

# Generate DH parameters for enhanced security
generate_dhparam() {
    print_status "Generating DH parameters (this may take a while)..."
    
    if [[ ! -f "$SSL_DIR/certs/dhparam.pem" ]]; then
        openssl dhparam -out "$SSL_DIR/certs/dhparam.pem" 2048
        print_status "DH parameters generated successfully"
    else
        print_status "DH parameters already exist"
    fi
}

# Configure basic Nginx for certificate verification
setup_basic_nginx() {
    print_status "Setting up basic Nginx configuration..."
    
    # Create basic configuration for certificate verification
    cat > "$NGINX_CONF_DIR/financeub-basic" << EOF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;
    
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }
    
    location / {
        return 301 https://\$server_name\$request_uri;
    }
}
EOF
    
    # Enable the configuration
    ln -sf "$NGINX_CONF_DIR/financeub-basic" "$NGINX_ENABLED_DIR/"
    
    # Remove default site if it exists
    rm -f "$NGINX_ENABLED_DIR/default"
    
    # Test and reload Nginx
    nginx -t && systemctl reload nginx
}

# Obtain Let's Encrypt SSL certificate
obtain_ssl_certificate() {
    print_status "Obtaining SSL certificate from Let's Encrypt..."
    
    # Check if certificate already exists
    if [[ -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]]; then
        print_warning "SSL certificate already exists for $DOMAIN"
        read -p "Do you want to renew it? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            return 0
        fi
    fi
    
    # Obtain certificate
    certbot certonly \
        --webroot \
        --webroot-path=/var/www/html \
        --email "$EMAIL" \
        --agree-tos \
        --no-eff-email \
        --domains "$DOMAIN,www.$DOMAIN" \
        --non-interactive
    
    if [[ $? -eq 0 ]]; then
        print_status "SSL certificate obtained successfully"
    else
        print_error "Failed to obtain SSL certificate"
        exit 1
    fi
}

# Setup production Nginx configuration with SSL
setup_production_nginx() {
    print_status "Setting up production Nginx configuration..."
    
    # Copy our production SSL configuration
    cp /app/nginx/nginx-ssl.conf "$NGINX_CONF_DIR/financeub-ssl"
    
    # Update domain placeholders
    sed -i "s/yourdomain.com/$DOMAIN/g" "$NGINX_CONF_DIR/financeub-ssl"
    
    # Update SSL certificate paths for Let's Encrypt
    sed -i "s|/etc/ssl/certs/yourdomain.crt|/etc/letsencrypt/live/$DOMAIN/fullchain.pem|g" "$NGINX_CONF_DIR/financeub-ssl"
    sed -i "s|/etc/ssl/private/yourdomain.key|/etc/letsencrypt/live/$DOMAIN/privkey.pem|g" "$NGINX_CONF_DIR/financeub-ssl"
    
    # Remove basic configuration and enable SSL configuration
    rm -f "$NGINX_ENABLED_DIR/financeub-basic"
    ln -sf "$NGINX_CONF_DIR/financeub-ssl" "$NGINX_ENABLED_DIR/"
    
    # Test and reload Nginx
    nginx -t && systemctl reload nginx
    
    print_status "Production Nginx configuration enabled"
}

# Setup automatic certificate renewal
setup_auto_renewal() {
    print_status "Setting up automatic certificate renewal..."
    
    # Create renewal script
    cat > /usr/local/bin/renew-ssl.sh << 'EOF'
#!/bin/bash
# SSL certificate renewal script

# Renew certificates
certbot renew --quiet

# Reload Nginx if renewal was successful
if [[ $? -eq 0 ]]; then
    systemctl reload nginx
    echo "$(date): SSL certificates renewed and Nginx reloaded" >> /var/log/ssl-renewal.log
fi
EOF
    
    chmod +x /usr/local/bin/renew-ssl.sh
    
    # Add cron job for automatic renewal (runs twice daily)
    cron_job="0 12,0 * * * /usr/local/bin/renew-ssl.sh"
    
    # Check if cron job already exists
    if ! crontab -l 2>/dev/null | grep -q "renew-ssl.sh"; then
        (crontab -l 2>/dev/null; echo "$cron_job") | crontab -
        print_status "Automatic renewal cron job added"
    else
        print_status "Automatic renewal cron job already exists"
    fi
}

# Setup security hardening
setup_security_hardening() {
    print_status "Applying security hardening..."
    
    # Enable and configure UFW firewall
    if command -v ufw &> /dev/null; then
        ufw --force enable
        ufw default deny incoming
        ufw default allow outgoing
        ufw allow ssh
        ufw allow 'Nginx Full'
        print_status "UFW firewall configured"
    fi
    
    # Setup fail2ban for Nginx
    if ! command -v fail2ban-server &> /dev/null; then
        apt-get install -y fail2ban
    fi
    
    # Create fail2ban configuration for Nginx
    cat > /etc/fail2ban/jail.d/nginx.local << 'EOF'
[nginx-http-auth]
enabled = true
port = http,https
logpath = /var/log/nginx/error.log

[nginx-noscript]
enabled = true
port = http,https
logpath = /var/log/nginx/access.log
maxretry = 6

[nginx-badbots]
enabled = true
port = http,https
logpath = /var/log/nginx/access.log
maxretry = 2

[nginx-noproxy]
enabled = true
port = http,https
logpath = /var/log/nginx/access.log
maxretry = 2
EOF
    
    systemctl enable fail2ban
    systemctl restart fail2ban
    
    print_status "Security hardening applied"
}

# Test SSL configuration
test_ssl_configuration() {
    print_status "Testing SSL configuration..."
    
    # Test SSL certificate
    echo | openssl s_client -servername "$DOMAIN" -connect "$DOMAIN:443" 2>/dev/null | openssl x509 -noout -dates
    
    # Test HTTP to HTTPS redirect
    response=$(curl -s -o /dev/null -w "%{http_code}" "http://$DOMAIN")
    if [[ "$response" == "301" ]]; then
        print_status "HTTP to HTTPS redirect working correctly"
    else
        print_warning "HTTP to HTTPS redirect may not be working (got $response)"
    fi
    
    # Test HTTPS
    response=$(curl -s -o /dev/null -w "%{http_code}" "https://$DOMAIN")
    if [[ "$response" == "200" ]]; then
        print_status "HTTPS is working correctly"
    else
        print_warning "HTTPS may not be working correctly (got $response)"
    fi
}

# Main function
main() {
    print_status "Starting SSL/HTTPS setup for FinanceHub SaaS"
    
    # Get domain and email from user if not set
    if [[ "$DOMAIN" == "yourdomain.com" ]]; then
        read -p "Enter your domain name: " DOMAIN
    fi
    
    if [[ "$EMAIL" == "admin@yourdomain.com" ]]; then
        read -p "Enter your email address: " EMAIL
    fi
    
    print_status "Domain: $DOMAIN"
    print_status "Email: $EMAIL"
    
    # Check if user wants to continue
    read -p "Continue with SSL setup? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 0
    fi
    
    # Run setup steps
    check_root
    install_dependencies
    generate_dhparam
    setup_basic_nginx
    obtain_ssl_certificate
    setup_production_nginx
    setup_auto_renewal
    setup_security_hardening
    test_ssl_configuration
    
    print_status "SSL/HTTPS setup completed successfully!"
    print_status "Your FinanceHub SaaS is now secured with HTTPS"
    print_status "Certificate will be automatically renewed"
    
    echo
    print_status "Next steps:"
    echo "1. Update your DNS records to point to this server"
    echo "2. Update environment variables with your domain"
    echo "3. Test all functionality over HTTPS"
    echo "4. Monitor logs for any issues"
}

# Run main function
main "$@"
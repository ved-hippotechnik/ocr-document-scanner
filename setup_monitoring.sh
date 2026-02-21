#!/bin/bash

# Monitoring Stack Setup Script
# OCR Document Scanner Application
# ===============================

set -e

echo "=========================================="
echo "Monitoring Stack Setup"
echo "=========================================="
echo "$(date)"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

check_docker() {
    print_status "Checking Docker installation..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Test Docker is running
    if ! docker info &> /dev/null; then
        print_error "Docker is not running. Please start Docker first."
        exit 1
    fi
    
    print_success "Docker and Docker Compose are installed and running"
}

create_monitoring_directories() {
    print_status "Creating monitoring directories..."
    
    # Create Grafana provisioning directories
    mkdir -p grafana/provisioning/datasources
    mkdir -p grafana/provisioning/dashboards
    mkdir -p grafana/dashboards
    
    # Create log directories
    mkdir -p logs/monitoring
    
    print_success "Monitoring directories created"
}

create_grafana_datasources() {
    print_status "Creating Grafana datasources configuration..."
    
    cat > grafana/provisioning/datasources/prometheus.yml << 'EOF'
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true
    jsonData:
      timeInterval: 15s

  - name: Loki
    type: loki
    access: proxy
    url: http://loki:3100
    editable: true
    jsonData:
      maxLines: 1000

  - name: AlertManager
    type: alertmanager
    access: proxy
    url: http://alertmanager:9093
    editable: true
EOF

    print_success "Grafana datasources configured"
}

create_grafana_dashboards_config() {
    print_status "Creating Grafana dashboards configuration..."
    
    cat > grafana/provisioning/dashboards/dashboards.yml << 'EOF'
apiVersion: 1

providers:
  - name: 'default'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    editable: true
    options:
      path: /var/lib/grafana/dashboards
EOF

    print_success "Grafana dashboards configuration created"
}

create_ocr_dashboard() {
    print_status "Creating OCR Scanner dashboard..."
    
    cat > grafana/dashboards/ocr-scanner-dashboard.json << 'EOF'
{
  "dashboard": {
    "id": null,
    "title": "OCR Document Scanner - Production Dashboard",
    "tags": ["ocr", "production"],
    "timezone": "browser",
    "refresh": "30s",
    "schemaVersion": 27,
    "version": 1,
    "panels": [
      {
        "id": 1,
        "title": "Application Status",
        "type": "stat",
        "targets": [
          {
            "expr": "up{job=\"ocr-scanner\"}",
            "legendFormat": "OCR Scanner"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "color": {
              "mode": "thresholds"
            },
            "mappings": [
              {
                "options": {
                  "0": {
                    "text": "DOWN"
                  },
                  "1": {
                    "text": "UP"
                  }
                },
                "type": "value"
              }
            ],
            "thresholds": {
              "steps": [
                {
                  "color": "red",
                  "value": null
                },
                {
                  "color": "green",
                  "value": 1
                }
              ]
            }
          }
        },
        "gridPos": {
          "h": 8,
          "w": 12,
          "x": 0,
          "y": 0
        }
      },
      {
        "id": 2,
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(flask_request_total[5m])",
            "legendFormat": "Requests/sec"
          }
        ],
        "gridPos": {
          "h": 8,
          "w": 12,
          "x": 12,
          "y": 0
        }
      },
      {
        "id": 3,
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "flask_request_duration_seconds{quantile=\"0.95\"}",
            "legendFormat": "95th percentile"
          },
          {
            "expr": "flask_request_duration_seconds{quantile=\"0.5\"}",
            "legendFormat": "Median"
          }
        ],
        "gridPos": {
          "h": 8,
          "w": 24,
          "x": 0,
          "y": 8
        }
      }
    ],
    "time": {
      "from": "now-1h",
      "to": "now"
    }
  }
}
EOF

    print_success "OCR Scanner dashboard created"
}

create_alertmanager_config() {
    print_status "Creating Alertmanager configuration..."
    
    cat > alertmanager.yml << 'EOF'
global:
  smtp_smarthost: 'localhost:587'
  smtp_from: 'alerts@your-domain.com'

route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'web.hook'

receivers:
- name: 'web.hook'
  email_configs:
  - to: 'admin@your-domain.com'
    subject: '[ALERT] {{ .GroupLabels.alertname }}'
    body: |
      {{ range .Alerts }}
      Alert: {{ .Annotations.summary }}
      Description: {{ .Annotations.description }}
      {{ end }}

inhibit_rules:
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'dev', 'instance']
EOF

    print_success "Alertmanager configuration created"
}

create_loki_config() {
    print_status "Creating Loki configuration..."
    
    cat > loki.yml << 'EOF'
auth_enabled: false

server:
  http_listen_port: 3100

ingester:
  lifecycler:
    address: 127.0.0.1
    ring:
      kvstore:
        store: inmemory
      replication_factor: 1
    final_sleep: 0s

schema_config:
  configs:
    - from: 2020-10-24
      store: boltdb-shipper
      object_store: filesystem
      schema: v11
      index:
        prefix: index_
        period: 24h

storage_config:
  boltdb_shipper:
    active_index_directory: /loki/boltdb-shipper-active
    cache_location: /loki/boltdb-shipper-cache
    shared_store: filesystem
  filesystem:
    directory: /loki/chunks

limits_config:
  enforce_metric_name: false
  reject_old_samples: true
  reject_old_samples_max_age: 168h

chunk_store_config:
  max_look_back_period: 0s

table_manager:
  retention_deletes_enabled: false
  retention_period: 0s
EOF

    print_success "Loki configuration created"
}

create_promtail_config() {
    print_status "Creating Promtail configuration..."
    
    cat > promtail.yml << 'EOF'
server:
  http_listen_port: 9080
  grpc_listen_port: 0

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
- job_name: system
  static_configs:
  - targets:
      - localhost
    labels:
      job: varlogs
      __path__: /var/log/*log

- job_name: ocr-application
  static_configs:
  - targets:
      - localhost
    labels:
      job: ocr-logs
      __path__: /app/logs/*.log
EOF

    print_success "Promtail configuration created"
}

start_monitoring_stack() {
    print_status "Starting monitoring stack..."
    
    # Start monitoring services
    docker-compose -f docker-compose.monitoring.yml up -d
    
    # Wait for services to start
    print_status "Waiting for services to start..."
    sleep 30
    
    # Check service health
    if curl -s http://localhost:9090/-/healthy | grep -q "Prometheus Server is Healthy"; then
        print_success "Prometheus is running and healthy"
    else
        print_warning "Prometheus health check failed"
    fi
    
    if curl -s http://localhost:3001/api/health | grep -q "ok"; then
        print_success "Grafana is running and healthy"
    else
        print_warning "Grafana health check may be pending"
    fi
    
    print_success "Monitoring stack started"
}

create_monitoring_scripts() {
    print_status "Creating monitoring utility scripts..."
    
    # Create monitoring status script
    cat > monitor_status.sh << 'EOF'
#!/bin/bash
echo "OCR Scanner Monitoring Status"
echo "============================"
echo "Date: $(date)"
echo ""

echo "Services Status:"
docker-compose -f docker-compose.monitoring.yml ps

echo ""
echo "Access URLs:"
echo "- Prometheus: http://localhost:9090"
echo "- Grafana: http://localhost:3001 (admin/admin123!@#)"
echo "- Alertmanager: http://localhost:9093"
echo "- cAdvisor: http://localhost:8080"
echo ""

echo "Quick Health Checks:"
curl -s http://localhost:9090/-/healthy && echo "✅ Prometheus: Healthy" || echo "❌ Prometheus: Unhealthy"
curl -s http://localhost:3001/api/health && echo "✅ Grafana: Healthy" || echo "❌ Grafana: Unhealthy"
curl -s http://localhost:9093/-/healthy && echo "✅ Alertmanager: Healthy" || echo "❌ Alertmanager: Unhealthy"
EOF
    
    chmod +x monitor_status.sh
    
    # Create monitoring cleanup script
    cat > cleanup_monitoring.sh << 'EOF'
#!/bin/bash
echo "Cleaning up monitoring stack..."
docker-compose -f docker-compose.monitoring.yml down -v
docker system prune -f
echo "Monitoring stack cleaned up"
EOF
    
    chmod +x cleanup_monitoring.sh
    
    print_success "Monitoring utility scripts created"
}

main() {
    print_status "Starting monitoring stack setup for OCR Document Scanner"
    
    # Check prerequisites
    check_docker
    
    # Create directories and configurations
    create_monitoring_directories
    create_grafana_datasources
    create_grafana_dashboards_config
    create_ocr_dashboard
    create_alertmanager_config
    create_loki_config
    create_promtail_config
    
    # Start monitoring stack
    start_monitoring_stack
    
    # Create utility scripts
    create_monitoring_scripts
    
    print_success "Monitoring stack setup completed successfully!"
    echo ""
    echo "=========================================="
    echo "Monitoring Stack Information"
    echo "=========================================="
    echo "Prometheus: http://localhost:9090"
    echo "Grafana: http://localhost:3001"
    echo "  - Username: admin"
    echo "  - Password: admin123!@#"
    echo "Alertmanager: http://localhost:9093"
    echo "cAdvisor: http://localhost:8080"
    echo ""
    echo "Utility Scripts:"
    echo "- ./monitor_status.sh - Check monitoring status"
    echo "- ./cleanup_monitoring.sh - Clean up monitoring stack"
    echo ""
    echo "Next steps:"
    echo "1. Access Grafana and configure dashboards"
    echo "2. Set up alert notification channels"
    echo "3. Configure log shipping from application"
    echo "4. Test alerting rules"
    echo "=========================================="
}

# Run main function
main "$@"
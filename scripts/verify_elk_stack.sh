#!/bin/bash

# =============================================================================
# ELK Stack Health Verification Script
# =============================================================================
# 
# This script verifies that the ELK stack is healthy and working normally.
# It checks all components and provides detailed status information.
#
# USAGE:
#   ./scripts/verify_elk_stack.sh                    # Full verification
#   ./scripts/verify_elk_stack.sh quick              # Quick health check
#   ./scripts/verify_elk_stack.sh logs               # Test log flow
#   ./scripts/verify_elk_stack.sh help               # Show help
#
# PREREQUISITES:
#   - Docker and docker compose installed
#   - ELK stack running: docker compose up -d elasticsearch logstash kibana filebeat
#
# OUTPUT:
#   - Service health status
#   - Elasticsearch cluster health
#   - Logstash pipeline status
#   - Kibana connectivity
#   - Filebeat log collection test
#   - Sample log ingestion test
#
# =============================================================================

set -e

# =============================================================================
# Configuration Variables
# =============================================================================

# Service names
ELASTICSEARCH_SERVICE="elasticsearch"
LOGSTASH_SERVICE="logstash"
KIBANA_SERVICE="kibana"
FILEBEAT_SERVICE="filebeat"

# Load env if present (for ELASTIC_PASSWORD)
if [ -f ./.env ]; then
    # shellcheck disable=SC2046
    export $(grep -E '^(ELASTIC_PASSWORD)=' ./.env | xargs -d '\n') || true
fi

# URLs
ELASTICSEARCH_URL="http://localhost:9200"
KIBANA_URL="http://localhost:5601"
LOGSTASH_URL="http://localhost:9600"

# Timeouts
HEALTH_CHECK_TIMEOUT=30
LOG_TEST_TIMEOUT=60

# =============================================================================
# Colors for output
# =============================================================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print section headers
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

# Function to print subsection headers
print_subheader() {
    echo -e "\n${CYAN}--- $1 ---${NC}"
}

# Function to print success messages
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Function to print warning messages
print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Function to print error messages
print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Function to print info messages
print_info() {
    echo -e "${PURPLE}ℹ $1${NC}"
}

# =============================================================================
# Helper Functions
# =============================================================================

# Check if docker compose is available
check_docker_compose() {
    if ! command -v docker compose &> /dev/null; then
        print_error "docker compose is not installed or not in PATH"
        exit 1
    fi
}

# Wait for service to be running (no health checks in docker-elk)
wait_for_service() {
    local service_name=$1
    local timeout=${2:-$HEALTH_CHECK_TIMEOUT}
    local start_time=$(date +%s)
    
    print_info "Waiting for $service_name to be running (timeout: ${timeout}s)..."
    
    while [ $(($(date +%s) - start_time)) -lt $timeout ]; do
        if docker compose ps $service_name | grep -q "Up"; then
            print_success "$service_name is running"
            return 0
        fi
        sleep 2
    done
    
    print_error "$service_name failed to start within ${timeout}s"
    return 1
}

# Check HTTP endpoint
check_http_endpoint() {
    local url=$1
    local service_name=$2
    local timeout=${3:-10}
    
    if curl -s --max-time $timeout "$url" > /dev/null 2>&1; then
        print_success "$service_name is responding at $url"
        return 0
    else
        print_error "$service_name is not responding at $url"
        return 1
    fi
}

# Wait for an HTTP endpoint to respond within a timeout (non-fatal status codes count as responding)
wait_for_endpoint() {
    local url=$1
    local service_name=$2
    local timeout=${3:-$HEALTH_CHECK_TIMEOUT}
    local start_time=$(date +%s)
    print_info "Waiting for $service_name to respond at $url (timeout: ${timeout}s)..."
    while [ $(($(date +%s) - start_time)) -lt $timeout ]; do
        if curl -s --max-time 2 "$url" > /dev/null 2>&1; then
            print_success "$service_name is responding at $url"
            return 0
        fi
        sleep 2
    done
    print_error "$service_name did not respond within ${timeout}s"
    return 1
}

# =============================================================================
# Service Health Checks
# =============================================================================

check_elasticsearch_health() {
    print_subheader "Elasticsearch Health Check"
    
    # Check if service is running
    if ! docker compose ps $ELASTICSEARCH_SERVICE | grep -q "Up"; then
        print_error "Elasticsearch service is not running"
        return 1
    fi
    
    # Wait for service to be healthy
    if ! wait_for_service $ELASTICSEARCH_SERVICE; then
        return 1
    fi
    
    # Check HTTP endpoint
    if ! check_http_endpoint "$ELASTICSEARCH_URL" "Elasticsearch"; then
        return 1
    fi
    
    # Check cluster health (with authentication)
    print_info "Checking cluster health..."
    local health_response=$(curl -s -u "elastic:${ELASTIC_PASSWORD:-}" "$ELASTICSEARCH_URL/_cluster/health" 2>/dev/null)
    
    if [ $? -eq 0 ]; then
        local status=$(echo "$health_response" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
        local nodes=$(echo "$health_response" | grep -o '"number_of_nodes":[0-9]*' | cut -d':' -f2)
        
        case $status in
            "green")
                print_success "Cluster status: GREEN (healthy)"
                ;;
            "yellow")
                print_warning "Cluster status: YELLOW (degraded but functional)"
                ;;
            "red")
                print_error "Cluster status: RED (unhealthy)"
                return 1
                ;;
        esac
        
        print_info "Number of nodes: $nodes"
    else
        print_error "Failed to get cluster health"
        return 1
    fi
    
    # Check indices
    print_info "Checking indices..."
    local indices_response=$(curl -s -u "elastic:${ELASTIC_PASSWORD:-}" "$ELASTICSEARCH_URL/_cat/indices?v" 2>/dev/null)
    if [ $? -eq 0 ]; then
        print_success "Indices accessible"
        echo "$indices_response" | head -5
    else
        print_warning "Could not retrieve indices information"
    fi
    
    return 0
}

check_logstash_health() {
    print_subheader "Logstash Health Check"
    
    # Check if service is running
    if ! docker compose ps $LOGSTASH_SERVICE | grep -q "Up"; then
        print_error "Logstash service is not running"
        return 1
    fi
    
    # Wait for service to be healthy
    if ! wait_for_service $LOGSTASH_SERVICE; then
        return 1
    fi
    
    # Check HTTP endpoint
    if ! check_http_endpoint "$LOGSTASH_URL" "Logstash"; then
        return 1
    fi
    
    # Check pipeline status
    print_info "Checking pipeline status..."
    local pipeline_response=$(curl -s "$LOGSTASH_URL/_node/pipelines" 2>/dev/null)
    
    if [ $? -eq 0 ]; then
        print_success "Logstash pipeline is accessible"
        
        # Check if main pipeline is running
        if echo "$pipeline_response" | grep -q "main"; then
            print_success "Main pipeline is running"
        else
            print_warning "Main pipeline status unclear"
        fi
    else
        print_warning "Could not retrieve pipeline information"
    fi
    
    return 0
}

check_kibana_health() {
    print_subheader "Kibana Health Check"
    
    # Check if service is running
    if ! docker compose ps $KIBANA_SERVICE | grep -q "Up"; then
        print_error "Kibana service is not running"
        return 1
    fi
    
    # Wait for service to be healthy
    if ! wait_for_service $KIBANA_SERVICE; then
        return 1
    fi
    
    # Check HTTP endpoint
    if ! check_http_endpoint "$KIBANA_URL" "Kibana"; then
        return 1
    fi
    
    # Check Kibana status
    print_info "Checking Kibana status..."
    local kibana_status=$(curl -s "$KIBANA_URL/api/status" 2>/dev/null)
    
    if [ $? -eq 0 ]; then
        print_success "Kibana API is accessible"
        
        # Check if Kibana can connect to Elasticsearch
        if echo "$kibana_status" | grep -q "green\|yellow"; then
            print_success "Kibana can connect to Elasticsearch"
        else
            print_warning "Kibana-Elasticsearch connection status unclear"
        fi
    else
        print_warning "Could not retrieve Kibana status"
    fi
    
    return 0
}

check_elk_setup() {
    print_subheader "ELK Setup Service Check"
    
    # Check if setup service has been run
    print_info "Checking if ELK setup has been completed..."
    
    # Check if users exist in Elasticsearch (with authentication)
    local users_response=$(curl -s -u "elastic:${ELASTIC_PASSWORD:-}" "$ELASTICSEARCH_URL/_security/user" 2>/dev/null)
    
    if [ $? -eq 0 ]; then
        if echo "$users_response" | grep -q "logstash_internal\|kibana_system"; then
            print_success "ELK users are configured"
        else
            print_warning "ELK users may not be configured. Run: docker compose --profile elk-setup up elk-setup"
        fi
    else
        print_warning "Could not check ELK user configuration"
    fi
    
    return 0
}

check_filebeat_health() {
    print_subheader "Filebeat Health Check"
    
    # Check if service is running
    if ! docker compose ps $FILEBEAT_SERVICE | grep -q "Up"; then
        print_error "Filebeat service is not running"
        return 1
    fi
    
    # Check Filebeat logs for errors
    print_info "Checking Filebeat logs for errors..."
    local filebeat_logs=$(docker compose logs --tail=20 $FILEBEAT_SERVICE 2>&1)
    
    if echo "$filebeat_logs" | grep -q "ERROR\|FATAL"; then
        print_warning "Filebeat has errors in logs:"
        echo "$filebeat_logs" | grep -i "error\|fatal" | head -3
    else
        print_success "No critical errors in Filebeat logs"
    fi
    
    # Check if Filebeat is collecting logs
    if echo "$filebeat_logs" | grep -q "Harvester started\|Input started"; then
        print_success "Filebeat is collecting logs"
    else
        print_warning "Filebeat log collection status unclear"
    fi
    
    return 0
}

# =============================================================================
# Log Flow Test
# =============================================================================

test_log_flow() {
    print_subheader "Testing Log Flow"
    
    # Generate a test log entry
    local test_message="ELK_STACK_TEST_$(date +%s)_$(uuidgen | cut -d'-' -f1)"
    local test_log="{\"timestamp\":\"$(date -Iseconds)\",\"level\":\"info\",\"service\":\"elk_test\",\"message\":\"$test_message\",\"test\":true}"
    
    print_info "Sending test log: $test_message"
    
    # Send test log to Logstash
    if echo "$test_log" | curl -s -X POST "$LOGSTASH_URL" -H "Content-Type: application/json" -d @- > /dev/null 2>&1; then
        print_success "Test log sent to Logstash"
    else
        print_error "Failed to send test log to Logstash"
        return 1
    fi
    
    # Wait for log to appear in Elasticsearch
    print_info "Waiting for log to appear in Elasticsearch..."
    local start_time=$(date +%s)
    local found=false
    
    while [ $(($(date +%s) - start_time)) -lt $LOG_TEST_TIMEOUT ]; do
        local search_response=$(curl -s "$ELASTICSEARCH_URL/logs-*/_search" -H "Content-Type: application/json" -d "{\"query\":{\"match\":{\"message\":\"$test_message\"}}}" 2>/dev/null)
        
        if echo "$search_response" | grep -q "$test_message"; then
            found=true
            break
        fi
        
        sleep 2
    done
    
    if [ "$found" = true ]; then
        print_success "Test log found in Elasticsearch"
        
        # Verify log structure
        local log_doc=$(curl -s "$ELASTICSEARCH_URL/logs-*/_search" -H "Content-Type: application/json" -d "{\"query\":{\"match\":{\"message\":\"$test_message\"}}}" 2>/dev/null | jq -r '.hits.hits[0]._source')
        
        if echo "$log_doc" | grep -q "service.*elk_test"; then
            print_success "Log structure is correct"
        else
            print_warning "Log structure may be incorrect"
        fi
        
        # Clean up test log
        print_info "Cleaning up test log..."
        curl -s -X DELETE "$ELASTICSEARCH_URL/logs-*/_query" -H "Content-Type: application/json" -d "{\"query\":{\"match\":{\"message\":\"$test_message\"}}}" > /dev/null 2>&1
        
    else
        print_error "Test log not found in Elasticsearch within ${LOG_TEST_TIMEOUT}s"
        return 1
    fi
    
    return 0
}

# =============================================================================
# Quick Health Check
# =============================================================================

quick_health_check() {
    print_header "Quick ELK Stack Health Check"
    
    local all_healthy=true
    
    # Check Elasticsearch (wait briefly to avoid flapping)
    if ! wait_for_endpoint "$ELASTICSEARCH_URL/_cluster/health" "Elasticsearch" 20; then
        all_healthy=false
        print_info "If Elasticsearch is slow to start, wait a bit longer and re-run: ./scripts/verify_elk_stack.sh quick"
        print_info "Troubleshoot: docker compose logs --tail=50 elasticsearch"
    fi
    
    # Check Logstash
    if ! wait_for_endpoint "$LOGSTASH_URL" "Logstash" 20; then
        all_healthy=false
        print_info "Troubleshoot: docker compose logs --tail=50 logstash"
        print_info "If needed, restart: docker compose --profile elk restart logstash"
    fi
    
    # Check Kibana
    if ! wait_for_endpoint "$KIBANA_URL" "Kibana" 30; then
        all_healthy=false
        print_info "Troubleshoot: docker compose logs --tail=50 kibana"
        print_info "If needed, restart: docker compose --profile elk restart kibana"
    fi
    
    # Check Filebeat
    if ! docker compose ps $FILEBEAT_SERVICE | grep -q "Up"; then
        print_error "Filebeat is not running"
        all_healthy=false
    fi
    
    if [ "$all_healthy" = true ]; then
        print_success "All ELK services are healthy!"
        return 0
    else
        print_error "Some ELK services are not healthy"
        echo ""
        echo "Next steps:"
        echo "  1) Re-run quick check after 20–30s: ./scripts/verify_elk_stack.sh quick"
        echo "  2) Inspect service logs: docker compose logs --tail=50 <service>"
        echo "  3) Restart ELK services if needed: docker compose --profile elk restart logstash kibana"
        echo "  4) Full verification with ingestion test: ./scripts/verify_elk_stack.sh"
        return 1
    fi
}

# =============================================================================
# Full Verification
# =============================================================================

full_verification() {
    print_header "ELK Stack Full Verification"
    
    local all_passed=true
    
    # Check ELK setup first
    check_elk_setup
    
    # Check all services
    if ! check_elasticsearch_health; then
        all_passed=false
    fi
    
    if ! check_logstash_health; then
        all_passed=false
    fi
    
    if ! check_kibana_health; then
        all_passed=false
    fi
    
    if ! check_filebeat_health; then
        all_passed=false
    fi
    
    # Test log flow
    if ! test_log_flow; then
        all_passed=false
    fi
    
    # Summary
    print_header "Verification Summary"
    
    if [ "$all_passed" = true ]; then
        print_success "✅ ELK Stack is fully operational!"
        print_info "🌐 Elasticsearch: $ELASTICSEARCH_URL"
        print_info "🌐 Kibana: $KIBANA_URL"
        print_info "🌐 Logstash: $LOGSTASH_URL"
        return 0
    else
        print_error "❌ ELK Stack has issues that need attention"
        return 1
    fi
}

# =============================================================================
# Help
# =============================================================================

show_help() {
    echo "ELK Stack Health Verification Script"
    echo "===================================="
    echo ""
    echo "This script verifies that the ELK stack is healthy and working normally."
    echo ""
    echo "USAGE:"
    echo "  $0                    # Full verification (default)"
    echo "  $0 quick              # Quick health check"
    echo "  $0 logs               # Test log flow only"
    echo "  $0 help               # Show this help message"
    echo ""
    echo "PREREQUISITES:"
    echo "  - Docker and docker compose installed"
    echo "  - ELK stack running: docker compose up -d elasticsearch logstash kibana filebeat"
    echo "  - ELK setup completed: docker compose --profile elk-setup up elk-setup"
    echo ""
    echo "OUTPUT:"
    echo "  - Service health status"
    echo "  - Elasticsearch cluster health"
    echo "  - Logstash pipeline status"
    echo "  - Kibana connectivity"
    echo "  - Filebeat log collection test"
    echo "  - Sample log ingestion test"
    echo ""
    echo "EXAMPLES:"
    echo "  # Quick check if everything is running"
    echo "  $0 quick"
    echo ""
    echo "  # Full verification with log flow test"
    echo "  $0"
    echo ""
    echo "  # Test only log ingestion"
    echo "  $0 logs"
}

# =============================================================================
# Main Execution
# =============================================================================

main() {
    echo -e "${BLUE}🔍 ELK Stack Health Verification Tool${NC}"
    echo -e "${BLUE}=====================================${NC}"
    
    # Check prerequisites
    check_docker_compose
    
    # Handle script arguments
    case "${1:-}" in
        "quick")
            quick_health_check
            ;;
        "logs")
            print_header "Testing Log Flow Only"
            test_log_flow
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        "")
            full_verification
            ;;
        *)
            print_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
}

# Run main function
main "$@"

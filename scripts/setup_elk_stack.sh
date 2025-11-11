#!/bin/bash

# =============================================================================
# ELK Stack Setup Script
# =============================================================================
# 
# This script sets up the ELK stack for the first time.
# It runs the setup service and then starts the ELK stack.
#
# USAGE:
#   ./scripts/setup_elk_stack.sh
#
# PREREQUISITES:
#   - Docker and docker compose installed
#   - Environment variables configured in .env
#
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print section headers
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
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
    echo -e "${BLUE}ℹ $1${NC}"
}

# Check if docker compose is available
check_docker_compose() {
    if ! command -v docker compose &> /dev/null; then
        print_error "docker compose is not installed or not in PATH"
        exit 1
    fi
}

# Check disk space
check_disk_space() {
    print_info "Checking available disk space..."
    # Extract available space (in human units) and numeric GB approximation
    local avail_raw=$(df -h . | awk 'NR==2 {print $4}')
    # Normalize to number by removing non-digits and non-dots
    local avail_num=$(echo "$avail_raw" | sed 's/[^0-9\.]*//g')
    # If value seems empty, skip check
    if [ -z "$avail_num" ]; then
        print_warning "Could not parse available disk space ($avail_raw)"
        return
    fi
    # Compare using awk to avoid bc dependency
    local is_low=$(awk -v v="$avail_num" 'BEGIN{if (v+0 < 5) print 1; else print 0}')
    if [ "$is_low" = "1" ]; then
        print_warning "Low disk space detected: $avail_raw available"
        print_warning "Elasticsearch may have issues with disk watermarks"
        print_info "Consider freeing up disk space or adjusting Elasticsearch settings"
    else
        print_success "Sufficient disk space available: $avail_raw"
    fi
}

# Check if .env file exists
check_env_file() {
    if [ ! -f ".env" ]; then
        print_error ".env file not found. Please create it from .env.example"
        exit 1
    fi
    
    # Check if ELK variables are set
    if ! grep -q "ELASTIC_PASSWORD" .env; then
        print_error "ELK environment variables not found in .env file"
        print_info "Please add ELK configuration to .env file"
        exit 1
    fi
    
    print_success "Environment file found and configured"
}

# Run ELK setup
run_elk_setup() {
    print_header "Running ELK Setup Service"
    
    print_info "Starting Elasticsearch..."
    docker compose --profile elk up -d elasticsearch
    
    print_info "Waiting for Elasticsearch to be healthy..."
    
    # Wait for Elasticsearch to be healthy with timeout
    local max_attempts=30
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        # Check if Elasticsearch is responding (no health check in docker-elk)
        # We expect a 401 error which means it's responding but needs auth
        if curl -s -f "http://localhost:9200" > /dev/null 2>&1 || curl -s "http://localhost:9200" | grep -q "security_exception"; then
            print_success "Elasticsearch is responding"
            break
        fi
        
        attempt=$((attempt + 1))
        print_info "Waiting for Elasticsearch... (attempt $attempt/$max_attempts)"
        sleep 10
    done
    
    if [ $attempt -eq $max_attempts ]; then
        print_error "Elasticsearch failed to become healthy within timeout"
        exit 1
    fi
    
    print_info "Running ELK setup service..."
    docker compose --profile elk --profile elk-setup up elk-setup
    
    if [ $? -eq 0 ]; then
        print_success "ELK setup completed successfully"
    else
        print_error "ELK setup failed"
        exit 1
    fi
}

# Start ELK stack
start_elk_stack() {
    print_header "Starting ELK Stack"
    
    print_info "Starting Logstash, Kibana, and Filebeat..."
    docker compose up -d logstash kibana filebeat
    
    print_info "Waiting for services to be healthy..."
    sleep 30
    
    print_success "ELK stack started"
}

# Verify setup
verify_setup() {
    print_header "Verifying ELK Stack Setup"
    
    if [ -f "./scripts/verify_elk_stack.sh" ]; then
        print_info "Running verification script..."
        ./scripts/verify_elk_stack.sh quick
        
        if [ $? -eq 0 ]; then
            print_success "ELK stack verification passed"
        else
            print_warning "ELK stack verification had issues"
        fi
    else
        print_warning "Verification script not found, skipping verification"
    fi
}

# Show next steps
show_next_steps() {
    print_header "Setup Complete - Next Steps"
    
    echo -e "${GREEN}✅ ELK Stack is now running!${NC}"
    echo ""
    echo -e "${BLUE}Access URLs:${NC}"
    echo -e "  🌐 Elasticsearch: http://localhost:9200"
    echo -e "  🌐 Kibana: http://localhost:5601"
    echo -e "  🌐 Logstash: http://localhost:9600"
    echo ""
    echo -e "${BLUE}Useful Commands:${NC}"
    echo -e "  📊 Check health: ./scripts/verify_elk_stack.sh"
    echo -e "  📈 Monitor logs: python scripts/elk_rag_monitor.py"
    echo -e "  🔍 View logs: docker compose logs -f [service]"
}

# Main execution
main() {
    echo -e "${BLUE}🔧 ELK Stack Setup Tool${NC}"
    echo -e "${BLUE}========================${NC}"
    
    # Check prerequisites
    check_docker_compose
    check_env_file
    check_disk_space
    
    # Run setup
    run_elk_setup
    start_elk_stack
    verify_setup
    show_next_steps
    
    echo -e "\n${GREEN}🎉 ELK Stack setup completed successfully!${NC}"
}

# Run main function
main "$@"

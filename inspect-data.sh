#!/bin/bash

# =============================================================================
# Data Inspection Script for Notebook LLM Stack
# =============================================================================
# 
# This script provides a comprehensive view of data state across all services:
# - PostgreSQL: Notebooks, sources, documents, users, and relationships
# - MinIO: File storage inspection and orphaned file detection
# - Qdrant: Vector database inspection and orphaned vector detection
# - Cross-service: Orphaned data detection across all services
#
# USAGE:
#   ./inspect-data.sh                    # Full inspection (default)
#   ./inspect-data.sh notebooks          # Inspect notebooks only
#   ./inspect-data.sh sources            # Inspect sources only
#   ./inspect-data.sh relationships      # Inspect notebook-source relationships
#   ./inspect-data.sh documents          # Inspect documents only
#   ./inspect-data.sh minio              # Inspect MinIO storage only
#   ./inspect-data.sh qdrant             # Inspect Qdrant vectors only
#   ./inspect-data.sh orphaned           # Find orphaned data only
#   ./inspect-data.sh summary            # Generate summary report only
#   ./inspect-data.sh help               # Show this help message
#
# PREREQUISITES:
#   - Docker and docker compose installed
#   - Stack running: docker compose up -d
#   - Services: postgres, minio, qdrant
#
# OUTPUT:
#   - Notebooks with source counts and owners
#   - Sources with notebook usage counts
#   - Document metadata and storage locations
#   - MinIO file listings and counts
#   - Qdrant vector counts and document mappings
#   - Orphaned data detection across all services
#   - Summary statistics
#
# EXAMPLES:
#   # Quick summary of all data
#   ./inspect-data.sh summary
#
#   # Check for data inconsistencies
#   ./inspect-data.sh orphaned
#
#   # Full audit of the system
#   ./inspect-data.sh
#
# =============================================================================

set -e

# =============================================================================
# Configuration Variables
# =============================================================================

# Service names (from docker-compose.yml)
DB_SERVICE="db"
MINIO_SERVICE="minio"
QDRANT_SERVICE="qdrant"

# Database configuration
DB_USER="postgres"
DB_NAME="app"

# MinIO configuration
MINIO_BUCKET="app-docs"

# Qdrant configuration
QDRANT_COLLECTION="documents"

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

# Helper function to execute database queries
execute_db_query() {
    local query="$1"
    docker compose exec -T $DB_SERVICE psql -U $DB_USER -d $DB_NAME -c "$query" 2>/dev/null
}

# Check if docker compose is available
check_docker_compose() {
    if ! command -v docker compose &> /dev/null; then
        print_error "docker compose is not installed or not in PATH"
        exit 1
    fi
}

# Check if services are running
check_services() {
    print_header "Checking Service Status"
    
    if ! docker compose ps | grep -q "Up"; then
        print_error "No services are running. Please start the stack first:"
        echo "  docker compose up -d"
        exit 1
    fi
    
    print_success "Services are running"
}

# Get database connection info
get_db_info() {
    print_subheader "Database Connection"
    
    # Get database container name
    DB_CONTAINER=$(docker compose ps -q $DB_SERVICE)
    if [ -z "$DB_CONTAINER" ]; then
        print_error "PostgreSQL container not found"
        return 1
    fi
    
    print_success "PostgreSQL container: $DB_CONTAINER"
}

# Inspect notebooks
inspect_notebooks() {
    print_header "Notebooks Inspection"
    
    print_subheader "All Notebooks"
    
    # Query all notebooks with their owners
    execute_db_query "
        SELECT 
            n.id,
            n.title,
            n.description,
            n.created_at,
            u.email as owner_email,
            COUNT(ns.source_id) as source_count
        FROM notebook n
        LEFT JOIN \"user\" u ON n.owner_id = u.id
        LEFT JOIN notebooksource ns ON n.id = ns.notebook_id
        GROUP BY n.id, n.title, n.description, n.created_at, u.email
        ORDER BY n.created_at DESC;
    " || print_error "Failed to query notebooks"
}

# Inspect sources
inspect_sources() {
    print_header "Sources Inspection"
    
    print_subheader "All Sources"
    
    # Query all sources with their types and owners
    execute_db_query "
        SELECT 
            s.id,
            s.title,
            s.source_type,
            s.created_at,
            u.email as owner_email,
            COUNT(ns.notebook_id) as notebook_count
        FROM source s
        LEFT JOIN \"user\" u ON s.owner_id = u.id
        LEFT JOIN notebooksource ns ON s.id = ns.source_id
        GROUP BY s.id, s.title, s.source_type, s.created_at, u.email
        ORDER BY s.created_at DESC;
    " || print_error "Failed to query sources"
}

# Inspect notebook-source relationships
inspect_notebook_sources() {
    print_header "Notebook-Source Relationships"
    
    print_subheader "Notebook to Sources Mapping"
    
    # Query notebook-source relationships
    execute_db_query "
        SELECT 
            n.title as notebook_title,
            n.id as notebook_id,
            s.title as source_title,
            s.source_type,
            s.id as source_id,
            ns.added_at
        FROM notebooksource ns
        JOIN notebook n ON ns.notebook_id = n.id
        JOIN source s ON ns.source_id = s.id
        ORDER BY n.title, ns.added_at;
    " || print_error "Failed to query notebook-source relationships"
}

# Inspect documents
inspect_documents() {
    print_header "Documents Inspection"
    
    print_subheader "All Documents"
    
    # Query all documents
    execute_db_query "
        SELECT 
            d.id,
            d.filename,
            d.mime_type,
            d.size,
            d.bucket,
            d.object_key,
            d.created_at,
            u.email as owner_email,
            s.id as source_id,
            s.title as source_title
        FROM document d
        LEFT JOIN \"user\" u ON d.owner_id = u.id
        LEFT JOIN source s ON d.source_id = s.id
        ORDER BY d.created_at DESC;
    " || print_error "Failed to query documents"
}

# Inspect MinIO files
inspect_minio() {
    print_header "MinIO Storage Inspection"
    
    print_subheader "MinIO Files"
    
    # List all objects in MinIO
    docker compose exec -T $MINIO_SERVICE mc ls minio/$MINIO_BUCKET/ --recursive 2>/dev/null || {
        print_warning "MinIO not accessible or no files found"
        return 1
    }
    
    print_subheader "MinIO File Count"
    FILE_COUNT=$(docker compose exec -T $MINIO_SERVICE mc ls minio/$MINIO_BUCKET/ --recursive 2>/dev/null | wc -l)
    print_info "Total files in MinIO: $FILE_COUNT"
}

# Inspect Qdrant vectors
inspect_qdrant() {
    print_header "Qdrant Vector Database Inspection"
    
    print_subheader "Qdrant Collections"
    
    # Get collection info
    COLLECTIONS_JSON=$(curl -s "http://localhost:6333/collections" 2>/dev/null)
    if [ -n "$COLLECTIONS_JSON" ]; then
        echo "$COLLECTIONS_JSON" | python3 -m json.tool 2>/dev/null || echo "$COLLECTIONS_JSON"
    else
        print_warning "Qdrant not accessible or no collections found"
        return 1
    fi
    
    print_subheader "Qdrant Points Count"
    
    # Get points count for documents collection
    COLLECTION_JSON=$(curl -s "http://localhost:6333/collections/$QDRANT_COLLECTION" 2>/dev/null)
    if [ -n "$COLLECTION_JSON" ]; then
        POINTS_COUNT=$(echo "$COLLECTION_JSON" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('result', {}).get('points_count', 0))" 2>/dev/null || echo "0")
    else
        POINTS_COUNT="0"
    fi
    print_info "Total vectors in Qdrant: $POINTS_COUNT"
    
    print_subheader "Qdrant Points by Document"
    
    # Get points grouped by document_id (if possible)
    POINTS_JSON=$(curl -s "http://localhost:6333/collections/$QDRANT_COLLECTION/points/scroll?limit=100&with_payload=true" 2>/dev/null)
    if [ -n "$POINTS_JSON" ]; then
        echo "$POINTS_JSON" | python3 -c "
import sys, json, collections
try:
    data = json.load(sys.stdin)
    doc_ids = [point['payload']['document_id'] for point in data.get('result', {}).get('points', [])]
    counter = collections.Counter(doc_ids)
    for doc_id, count in counter.most_common():
        print(f'{count} {doc_id}')
except:
    print('Could not parse Qdrant data')
" 2>/dev/null || print_warning "Could not retrieve detailed Qdrant data"
    else
        print_warning "Could not retrieve Qdrant data"
    fi
}

# Find orphaned data
find_orphaned_data() {
    print_header "Orphaned Data Detection"
    
    print_subheader "Orphaned MinIO Files (files without database records)"
    
    # Get all MinIO object keys
    MINIO_KEYS=$(docker compose exec -T $MINIO_SERVICE mc ls minio/$MINIO_BUCKET/ --recursive 2>/dev/null | awk '{print $5}' | grep -v "^$" || echo "")
    
    if [ -n "$MINIO_KEYS" ]; then
        for key in $MINIO_KEYS; do
            # Check if this object_key exists in database
            EXISTS=$(execute_db_query "SELECT COUNT(*) FROM document WHERE object_key = '$key';" | tr -d ' ')
            
            if [ "$EXISTS" = "0" ]; then
                print_warning "Orphaned MinIO file: $key"
            fi
        done
    else
        print_info "No MinIO files found"
    fi
    
    print_subheader "Orphaned Database Records (records without MinIO files)"
    
    # Get all database object keys
    DB_KEYS=$(execute_db_query "SELECT object_key FROM document WHERE object_key IS NOT NULL;" | tr -d ' ' | grep -v "^$" || echo "")
    
    if [ -n "$DB_KEYS" ]; then
        for key in $DB_KEYS; do
            # Check if this object_key exists in MinIO
            EXISTS=$(docker compose exec -T $MINIO_SERVICE mc ls "minio/$MINIO_BUCKET/$key" 2>/dev/null | wc -l)
            
            if [ "$EXISTS" = "0" ]; then
                print_warning "Orphaned database record: $key"
            fi
        done
    else
        print_info "No database records found"
    fi
    
    print_subheader "Orphaned Qdrant Vectors (vectors without database records)"
    
    # Get all document_ids from Qdrant
    QDRANT_POINTS_JSON=$(curl -s "http://localhost:6333/collections/$QDRANT_COLLECTION/points/scroll?limit=1000&with_payload=true" 2>/dev/null)
    if [ -n "$QDRANT_POINTS_JSON" ]; then
        QDRANT_DOC_IDS=$(echo "$QDRANT_POINTS_JSON" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    doc_ids = [point['payload']['document_id'] for point in data.get('result', {}).get('points', [])]
    print('\n'.join(sorted(set(doc_ids))))
except:
    print('')
" 2>/dev/null || echo "")
    else
        QDRANT_DOC_IDS=""
    fi
    
    if [ -n "$QDRANT_DOC_IDS" ]; then
        for doc_id in $QDRANT_DOC_IDS; do
            # Check if this document_id exists in database
            EXISTS=$(execute_db_query "SELECT COUNT(*) FROM document WHERE id = '$doc_id';" | tr -d ' ')
            
            if [ "$EXISTS" = "0" ]; then
                print_warning "Orphaned Qdrant vectors for document: $doc_id"
            fi
        done
    else
        print_info "No Qdrant vectors found"
    fi
}

# Generate summary report
generate_summary() {
    print_header "Summary Report"
    
    # Count notebooks
    NOTEBOOK_COUNT=$(execute_db_query "SELECT COUNT(*) FROM notebook;" | tr -d ' ' || echo "0")
    
    # Count sources
    SOURCE_COUNT=$(execute_db_query "SELECT COUNT(*) FROM source;" | tr -d ' ' || echo "0")
    
    # Count documents
    DOCUMENT_COUNT=$(execute_db_query "SELECT COUNT(*) FROM document;" | tr -d ' ' || echo "0")
    
    # Count users
    USER_COUNT=$(execute_db_query "SELECT COUNT(*) FROM \"user\";" | tr -d ' ' || echo "0")
    
    # Count MinIO files
    MINIO_COUNT=$(docker compose exec -T $MINIO_SERVICE mc ls minio/$MINIO_BUCKET/ --recursive 2>/dev/null | wc -l || echo "0")
    
    # Count Qdrant vectors
    QDRANT_JSON=$(curl -s "http://localhost:6333/collections/$QDRANT_COLLECTION" 2>/dev/null)
    if [ -n "$QDRANT_JSON" ]; then
        QDRANT_COUNT=$(echo "$QDRANT_JSON" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('result', {}).get('points_count', 0))" 2>/dev/null || echo "0")
    else
        QDRANT_COUNT="0"
    fi
    
    echo -e "${GREEN}📊 Data Summary:${NC}"
    echo -e "  Users: $USER_COUNT"
    echo -e "  Notebooks: $NOTEBOOK_COUNT"
    echo -e "  Sources: $SOURCE_COUNT"
    echo -e "  Documents: $DOCUMENT_COUNT"
    echo -e "  MinIO Files: $MINIO_COUNT"
    echo -e "  Qdrant Vectors: $QDRANT_COUNT"
}

# Main execution
main() {
    echo -e "${BLUE}🔍 Notebook LLM Data Inspection Tool${NC}"
    echo -e "${BLUE}========================================${NC}"
    
    # Check prerequisites
    check_docker_compose
    check_services
    get_db_info
    
    # Run inspections
    inspect_notebooks
    inspect_sources
    inspect_notebook_sources
    inspect_documents
    inspect_minio
    inspect_qdrant
    find_orphaned_data
    generate_summary
    
    echo -e "\n${GREEN}✅ Data inspection completed!${NC}"
}

# Handle script arguments
case "${1:-}" in
    "notebooks")
        check_docker_compose
        check_services
        inspect_notebooks
        ;;
    "sources")
        check_docker_compose
        check_services
        inspect_sources
        ;;
    "relationships")
        check_docker_compose
        check_services
        inspect_notebook_sources
        ;;
    "documents")
        check_docker_compose
        check_services
        inspect_documents
        ;;
    "minio")
        check_docker_compose
        check_services
        inspect_minio
        ;;
    "qdrant")
        check_docker_compose
        check_services
        inspect_qdrant
        ;;
    "orphaned")
        check_docker_compose
        check_services
        find_orphaned_data
        ;;
    "summary")
        check_docker_compose
        check_services
        generate_summary
        ;;
    "help"|"-h"|"--help")
        echo "============================================================================="
        echo "Data Inspection Script for Notebook LLM Stack"
        echo "============================================================================="
        echo ""
        echo "This script provides a comprehensive view of data state across all services:"
        echo "  - PostgreSQL: Notebooks, sources, documents, users, and relationships"
        echo "  - MinIO: File storage inspection and orphaned file detection"
        echo "  - Qdrant: Vector database inspection and orphaned vector detection"
        echo "  - Cross-service: Orphaned data detection across all services"
        echo ""
        echo "USAGE:"
        echo "  $0                    # Full inspection (default)"
        echo "  $0 notebooks          # Inspect notebooks only"
        echo "  $0 sources            # Inspect sources only"
        echo "  $0 relationships      # Inspect notebook-source relationships"
        echo "  $0 documents          # Inspect documents only"
        echo "  $0 minio              # Inspect MinIO storage only"
        echo "  $0 qdrant             # Inspect Qdrant vectors only"
        echo "  $0 orphaned           # Find orphaned data only"
        echo "  $0 summary            # Generate summary report only"
        echo "  $0 help               # Show this help message"
        echo ""
        echo "PREREQUISITES:"
        echo "  - Docker and docker compose installed"
        echo "  - Stack running: docker compose up -d"
        echo "  - Services: postgres, minio, qdrant"
        echo ""
        echo "OUTPUT:"
        echo "  - Notebooks with source counts and owners"
        echo "  - Sources with notebook usage counts"
        echo "  - Document metadata and storage locations"
        echo "  - MinIO file listings and counts"
        echo "  - Qdrant vector counts and document mappings"
        echo "  - Orphaned data detection across all services"
        echo "  - Summary statistics"
        echo ""
        echo "EXAMPLES:"
        echo "  # Quick summary of all data"
        echo "  $0 summary"
        echo ""
        echo "  # Check for data inconsistencies"
        echo "  $0 orphaned"
        echo ""
        echo "  # Full audit of the system"
        echo "  $0"
        echo ""
        echo "  # Inspect specific component"
        echo "  $0 notebooks"
        echo "  $0 minio"
        echo ""
        echo "============================================================================="
        exit 0
        ;;
    *)
        main
        ;;
esac 
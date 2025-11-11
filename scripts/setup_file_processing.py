#!/usr/bin/env python3
"""
Setup script for the file processing pipeline.

This script helps users set up the file processing pipeline with Kafka and Qdrant.
"""

import os
import sys
import subprocess
import json
from pathlib import Path


def check_docker():
    """Check if Docker is installed and running."""
    try:
        result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Docker is installed")
            return True
        else:
            print("❌ Docker is not installed or not running")
            return False
    except FileNotFoundError:
        print("❌ Docker is not installed")
        return False


def check_docker_compose():
    """Check if Docker Compose is available."""
    try:
        result = subprocess.run(['docker-compose', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Docker Compose is available")
            return True
        else:
            print("❌ Docker Compose is not available")
            return False
    except FileNotFoundError:
        print("❌ Docker Compose is not installed")
        return False


def create_env_file():
    """Create .env file from template if it doesn't exist."""
    env_file = Path('.env')
    env_example = Path('env.example')
    
    if env_file.exists():
        print("✅ .env file already exists")
        return True
    
    if not env_example.exists():
        print("❌ env.example file not found")
        return False
    
    try:
        # Copy env.example to .env
        subprocess.run(['cp', 'env.example', '.env'])
        print("✅ Created .env file from template")
        print("⚠️  Please edit .env file with your API keys:")
        print("   - OPENAI_API_KEY")
        print("   - TAVILY_API_KEY (for agent)")
        return True
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False


def check_services():
    """Check if all required services are running."""
    try:
        result = subprocess.run(['docker-compose', 'ps'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Docker Compose services are accessible")
            return True
        else:
            print("❌ Docker Compose services are not accessible")
            return False
    except Exception as e:
        print(f"❌ Failed to check services: {e}")
        return False


def run_migrations():
    """Run database migrations."""
    try:
        print("🔄 Running database migrations...")
        result = subprocess.run([
            'docker-compose', 'exec', '-T', 'backend', 
            'alembic', 'upgrade', 'head'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Database migrations completed")
            return True
        else:
            print(f"❌ Database migrations failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Failed to run migrations: {e}")
        return False


def check_kafka_topic():
    """Check if Kafka topic exists."""
    try:
        print("🔄 Checking Kafka topic...")
        result = subprocess.run([
            'docker-compose', 'exec', '-T', 'kafka',
            'kafka-topics', '--bootstrap-server', 'localhost:9092',
            '--list'
        ], capture_output=True, text=True)
        
        if result.returncode == 0 and 'source_changes' in result.stdout:
            print("✅ Kafka topic 'source_changes' exists")
            return True
        else:
            print("⚠️  Kafka topic 'source_changes' not found, will be created automatically")
            return True
    except Exception as e:
        print(f"⚠️  Could not check Kafka topic: {e}")
        return True


def check_qdrant_collection():
    """Check if Qdrant collection exists."""
    try:
        print("🔄 Checking Qdrant collection...")
        result = subprocess.run([
            'curl', '-s', 'http://localhost:6333/collections/documents'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Qdrant collection 'documents' exists")
            return True
        else:
            print("⚠️  Qdrant collection 'documents' not found, will be created automatically")
            return True
    except Exception as e:
        print(f"⚠️  Could not check Qdrant collection: {e}")
        return True


def print_service_urls():
    """Print service URLs for easy access."""
    print("\n🌐 Service URLs:")
    print("   Frontend: http://localhost:3000")
    print("   Backend API: http://localhost:8000/api/v1")
    print("   Kafka UI: http://localhost:8080")
    print("   MinIO Console: http://localhost:9001")
    print("   MailHog: http://localhost:8025")
    print("   Qdrant: http://localhost:6333")


def print_next_steps():
    """Print next steps for users."""
    print("\n📋 Next Steps:")
    print("1. Start all services: docker compose up -d")
    print("2. Check service health: docker compose ps")
    print("3. View logs: docker compose logs -f")
    print("4. Test file upload via the frontend")
    print("5. Test search functionality")
    print("\n📚 Documentation:")
    print("   - See FILE_PROCESSING_PIPELINE.md for detailed documentation")
    print("   - Check logs for any issues: docker-compose logs [service-name]")


def main():
    """Main setup function."""
    print("🚀 Setting up File Processing Pipeline with Kafka & Qdrant")
    print("=" * 60)
    
    # Check prerequisites
    if not check_docker():
        print("\n❌ Please install Docker first: https://docs.docker.com/get-docker/")
        sys.exit(1)
    
    if not check_docker_compose():
        print("\n❌ Please install Docker Compose first")
        sys.exit(1)
    
    # Create environment file
    if not create_env_file():
        print("\n❌ Failed to create environment file")
        sys.exit(1)
    
    # Check services
    if not check_services():
        print("\n⚠️  Services not running. Please start them with: docker compose up -d")
    
    # Run migrations if services are available
    if check_services():
        run_migrations()
        check_kafka_topic()
        check_qdrant_collection()
    
    # Print helpful information
    print_service_urls()
    print_next_steps()
    
    print("\n✅ Setup complete!")
    print("🎉 You're ready to use the file processing pipeline!")


if __name__ == "__main__":
    main() 
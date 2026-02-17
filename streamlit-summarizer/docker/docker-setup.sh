#!/bin/bash

# Text Summarizer Docker Setup Script

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# Get the project root (one level up from docker/)
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Change to project root to ensure all paths are correct relative to the project
cd "$PROJECT_ROOT" || exit 1

echo "🐳 Setting up Text Summarizer Docker Environment"
echo "📂 Working directory: $(pwd)"
echo "================================================"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not available. Please install Docker Compose."
    exit 1
fi

# Create data directory for persistent storage
echo "📁 Creating data directory..."
mkdir -p ./data

# Ensure keys directory exists
mkdir -p ./keys

# Check if config.yaml exists
if [ ! -f "config/config.yaml" ]; then
    echo "⚙️  Creating config.yaml from example..."
    if [ -f "config/config.yaml.example" ]; then
        cp config/config.yaml.example config/config.yaml
        echo "📝 Please edit config/config.yaml with your OCI compartment ID and profile:"
        echo "   - compartment_id: Your OCI compartment ID"
        echo "   - config_profile: Your OCI profile name (usually 'DEFAULT')"
        echo ""
        echo "⚠️  You MUST edit config/config.yaml before running the container!"
        read -p "Press Enter to continue after editing config.yaml..."
    else
        echo "❌ config/config.yaml.example not found. Please create config/config.yaml manually."
        exit 1
    fi
else
    echo "✅ config/config.yaml already exists"
fi

# Check for OCI configuration
echo "⚙️  Setting up OCI configuration..."

# Check if local OCI config exists
if [ ! -f "config/oci-config" ]; then
    echo "📝 Creating local OCI config from example..."
    if [ -f "config/oci-config.example" ]; then
        cp config/oci-config.example config/oci-config
        echo ""
        echo "🔑 Please edit the following files with your OCI credentials:"
        echo "   1. config/oci-config - Your OCI configuration"
        echo "   2. Place your OCI private key as 'keys/oci-private-key.pem'"
        echo ""
        echo "📋 You need to:"
        echo "   - Update user OCID in config/oci-config"
        echo "   - Update tenancy OCID in config/oci-config"
        echo "   - Update fingerprint in config/oci-config"
        echo "   - Update region in config/oci-config"
        echo "   - Copy your private key file as 'keys/oci-private-key.pem'"
        echo ""
        echo "⚠️  CRITICAL: In config/oci-config, set key_file to:"
        echo "   key_file=/home/appuser/.oci/oci-private-key.pem"
        echo "   (This is the Docker container path used by the Streamlit user, NOT a relative path)"
        echo ""
        echo "💡 Alternative: You can still use system OCI config by uncommenting"
        echo "   the line in docker-compose.yml and commenting out the local config lines"
        echo ""
        echo "⚠️  You MUST configure OCI credentials before running the container!"
        read -p "Press Enter to continue after setting up OCI credentials..."
    else
        echo "❌ config/oci-config.example not found."
        exit 1
    fi
fi

# Check if private key exists
if [ ! -f "keys/oci-private-key.pem" ]; then
    echo "⚠️  OCI private key file 'keys/oci-private-key.pem' not found."
    echo "   Please copy your OCI private key file as 'keys/oci-private-key.pem'"
    echo ""
fi

# Validate oci-config file
if [ -f "config/oci-config" ]; then
    if grep -q "key_file\s*=\s*\./oci-private-key.pem" config/oci-config; then
        echo "🔧 Fixing key_file path in config/oci-config for Docker compatibility..."
        sed -i.bak 's|key_file.*=.*|key_file=/home/appuser/.oci/oci-private-key.pem|g' config/oci-config
        echo "✅ Updated key_file path to Docker container path"
    elif grep -q "key_file\s*=\s*/home/appuser/.oci/oci-private-key.pem" config/oci-config; then
        echo "✅ OCI config key_file path is correctly set for Docker"
    else
        echo "⚠️  Please ensure key_file in config/oci-config is set to:"
        echo "   key_file=/home/appuser/.oci/oci-private-key.pem"
    fi
fi

echo "✅ Setup complete!"
echo ""

# Final validation
echo "🔍 Final Setup Validation:"
if [ -f "config/config.yaml" ]; then
    echo "   ✅ config/config.yaml exists"
else
    echo "   ❌ config/config.yaml missing"
fi

if [ -f "config/oci-config" ]; then
    echo "   ✅ config/oci-config exists"
    if grep -q "key_file\s*=\s*/root/.oci/oci-private-key.pem" config/oci-config; then
        echo "   ✅ config/oci-config has correct Docker path"
    else
        echo "   ⚠️  config/oci-config may need Docker path fix"
    fi
else
    echo "   ❌ config/oci-config missing"
fi

if [ -f "keys/oci-private-key.pem" ]; then
    echo "   ✅ keys/oci-private-key.pem exists"
else
    echo "   ❌ keys/oci-private-key.pem missing"
fi

echo ""
echo "🧪 Recommended: Test your OCI configuration first:"
echo "   python scripts/test-oci-config.py"
echo ""
echo "🚀 To build and run the application:"
echo "   docker-compose up --build"
echo ""
echo "🌐 The application will be available at:"
echo "   http://localhost:8501"
echo ""
echo "📋 Useful Docker commands:"
echo "   docker-compose up -d          # Run in background"
echo "   docker-compose down           # Stop and remove containers"
echo "   docker-compose logs -f        # View logs"
echo "   docker-compose restart        # Restart the service"
echo ""
echo "🆘 If you get 'Config file invalid' errors:"
echo "   Check that config/oci-config has: key_file=/root/.oci/oci-private-key.pem"

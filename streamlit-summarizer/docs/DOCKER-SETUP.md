# Docker Setup Guide

This guide explains how to set up and run the Text Summarizer app using Docker with local OCI configuration.

## Why Local OCI Configuration?

Using local OCI configuration (in the project directory) has several advantages:

- ✅ **Portable**: Everything needed is in one place
- ✅ **Version Control**: Can be included in your project (with proper .gitignore)
- ✅ **No System Dependencies**: Doesn't require system-wide OCI CLI setup
- ✅ **Easier Deployment**: Simpler to deploy to different environments
- ✅ **Team Sharing**: Easier to share project setup with team members

## Quick Setup

1. **Run the setup script:**

   ```bash
   ./docker-setup.sh
   ```

2. **Configure your OCI credentials:**

   The script will create `oci-config` from the example. Edit it with your values:

   ```ini
   [DEFAULT]
   user=ocid1.user.oc1..your_actual_user_ocid
   fingerprint=your_actual_key_fingerprint
   key_file=/home/appuser/.oci/oci-private-key.pem
   tenancy=ocid1.tenancy.oc1..your_actual_tenancy_ocid
   region=us-ashburn-1
   ```

   ⚠️ **Important**: The `key_file` path must be `/home/appuser/.oci/oci-private-key.pem` (the Streamlit user's home inside Docker), not a relative path.

3. **Add your private key:**

   ```bash
   # Copy your OCI private key to the project directory
   cp /path/to/your/oci-private-key.pem ./oci-private-key.pem
   ```

4. **Configure the app:**

   Edit `config.yaml` with your compartment ID:

   ```yaml
   compartment_id: "ocid1.compartment.oc1..your_compartment_id"
   config_profile: "DEFAULT"
   ```

5. **Run the application:**

   **Option A - From the docker directory:**

   ```bash
   cd docker
   docker-compose up --build
   ```

   **Option B - From the main project directory:**

   ```bash
   docker-compose -f docker/docker-compose.yml up --build
   ```

## File Structure

After setup, your directory should look like:

```
streamlit-summarizer/
├── app.py
├── config.yaml                 # App configuration
├── oci-config                  # OCI configuration (local)
├── oci-private-key.pem         # Your OCI private key (local)
├── docker-compose.yml          # Local OCI config setup
├── docker-compose-system-oci.yml # System OCI config alternative
├── Dockerfile
├── data/                       # Persistent app data
└── ...
```

## Security Notes

⚠️ **Important Security Considerations:**

1. **Never commit sensitive files to version control:**

   ```bash
   # Add to .gitignore:
   oci-config
   oci-private-key.pem
   *.pem
   config.yaml
   ```

2. **File permissions:**

   ```bash
   # Set proper permissions for security
   chmod 600 oci-private-key.pem
   chmod 600 oci-config
   ```

3. **Keep keys secure:**
   - Don't share your private key files
   - Use separate keys for different environments
   - Regularly rotate your keys

## Alternative: System OCI Configuration

If you prefer to use your system OCI configuration:

1. **Switch to system config:**

   ```bash
   cp docker-compose-system-oci.yml docker-compose.yml
   ```

2. **Ensure system OCI setup:**

   ```bash
   # Check if system config exists
   ls -la ~/.oci/
   ```

3. **Run setup and configure only app config:**
   ```bash
   ./docker-setup.sh
   # Only edit config.yaml when prompted
   ```

## Troubleshooting

### Common Issues

1. **"Config file invalid - key_file must be a valid file path":**

   This is the most common issue. Fix it by:

   ```bash
   # Edit oci-config and ensure key_file path is:
   key_file=/home/appuser/.oci/oci-private-key.pem
   # NOT: key_file=./oci-private-key.pem
   ```

2. **"Permission denied" errors:**

   ```bash
   chmod 600 oci-private-key.pem oci-config
   ```

3. **"Config file not found":**

   - Ensure `oci-config` exists and is properly formatted
   - Check file paths in the config file
   - Verify `oci-private-key.pem` exists in the project directory

4. **"Authentication failed":**

   - Verify your user OCID, tenancy OCID, and fingerprint
   - Ensure the private key matches the public key uploaded to OCI
   - Check that your private key file isn't corrupted

5. **"Compartment not found":**
   - Verify your compartment OCID in `config.yaml`
   - Ensure you have permissions for the compartment

### Validation Commands

Test your OCI configuration:

```bash
# Test OCI config before Docker (recommended)
python test-oci-config.py

# Build and run the container (from docker/ directory)
cd docker && docker-compose up --build
# OR from main directory:
# docker-compose -f docker/docker-compose.yml up --build

# Check logs for authentication issues
docker-compose logs -f  # (from docker/ directory)
# OR: docker-compose -f docker/docker-compose.yml logs -f

# Test OCI connectivity (if you have OCI CLI installed locally)
oci iam region list --config-file ./oci-config
```

### Step-by-Step Debugging

If you encounter issues, follow these steps:

1. **Verify files exist:**

   ```bash
   ls -la oci-config oci-private-key.pem config.yaml
   ```

2. **Check file contents:**

   ```bash
   # Verify oci-config has correct paths
   cat oci-config
   # Should show: key_file=/root/.oci/oci-private-key.pem
   ```

3. **Test locally first:**

   ```bash
   python test-oci-config.py
   ```

4. **Run Docker with verbose logging:**
   ```bash
   # From docker/ directory:
   cd docker && docker-compose up --build
   # OR from main directory:
   # docker-compose -f docker/docker-compose.yml up --build
   # Watch for specific error messages
   ```

## Docker Commands Reference

**From the docker/ directory:**

```bash
cd docker

# Start the application
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the application
docker-compose down

# Rebuild after changes
docker-compose up --build

# Check container status
docker-compose ps

# Access container shell (for debugging)
docker-compose exec streamlit-app bash
```

**From the main project directory:**

```bash
# Start the application
docker-compose -f docker/docker-compose.yml up -d

# View logs
docker-compose -f docker/docker-compose.yml logs -f

# Stop the application
docker-compose -f docker/docker-compose.yml down

# Rebuild after changes
docker-compose -f docker/docker-compose.yml up --build

# Check container status
docker-compose -f docker/docker-compose.yml ps

# Access container shell (for debugging)
docker-compose -f docker/docker-compose.yml exec streamlit-app bash
```

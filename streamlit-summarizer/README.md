# Text Summarizer Streamlit App

This is a Streamlit application that uses OCI Generative AI to summarize text content from uploaded files. The app provides a clean, modern interface with a copy-to-clipboard feature for easy sharing of summaries.

## Features

- 📝 Upload text files for summarization
- 🎨 Clean, modern UI with styled output panel
- 📋 Copy-to-clipboard functionality
- ⚡ Fast processing using OCI Generative AI
- 💾 Save up to 5 custom prompts for different use cases
- 📱 Responsive design that works on all devices

## Setup

### Prerequisites

1. Make sure you have Python 3.11+ installed (see `.python-version` file)
2. An active Oracle Cloud Infrastructure (OCI) account
3. OCI configuration setup locally (`~/.oci/config`)
4. A compartment ID where you have permissions to use Generative AI

### Installation

1. Install uv (a fast Python package installer):

   ```bash
   # macOS and Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Windows
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

2. Clone this repository and navigate to the `streamlit-summarizer` directory:

   ```bash
   cd streamlit-summarizer
   ```

3. Create a virtual environment using uv:

   ```bash
   uv venv
   ```

4. Activate the virtual environment:

   ```bash
   # macOS/Linux
   source .venv/bin/activate

   # Windows
   .venv\Scripts\activate
   ```

5. Install the required dependencies:

   ```bash
   # Using uv (recommended - 10-100x faster)
   uv pip install -r requirements.txt

   # Or using pyproject.toml (alternative)
   uv pip install -e .
   ```

### Configuration

1. Create a `config.yaml` file in the `streamlit-summarizer` directory using the provided example (remember that `config/` and `keys/` are **not** tracked in git—you must create them locally):

   ```bash
   cp config.yaml.example config.yaml
   ```

2. Edit the `config.yaml` file to include your OCI compartment ID and profile name:

   ```yaml
   compartment_id: "ocid1.compartment.oc1..yourcompartmentidhere"
   config_profile: "DEFAULT" # or your specific profile name from ~/.oci/config
   ```

3. Decide how you want to supply OCI credentials:
   - **Local (non-Docker) runs:** rely on your system `~/.oci/config`. No files under `streamlit-summarizer/keys/` are required; just ensure the profile referenced in `config.yaml` exists.
   - **Docker runs:** create `streamlit-summarizer/config/` and `streamlit-summarizer/keys/`, then place `config/oci-config` plus `keys/oci-private-key.pem` inside. Compose files mount these into the container, so secrets stay outside git.
4. Ensure the OCI configuration you chose (`~/.oci/config` or `config/oci-config`) references the correct private key path and has permissions for your compartment.

## Running the App

### Option 1: Using Docker (Recommended)

The easiest way to run the application is using Docker, which ensures consistent behavior across different environments. For the full Docker workflow, key path requirements, and troubleshooting, see [docs/DOCKER-SETUP.md](docs/DOCKER-SETUP.md).

#### Prerequisites for Docker

- Docker installed on your system
- Docker Compose (usually included with Docker Desktop)
- OCI credentials (see configuration options below)

#### OCI Configuration Options

**Option A: Local OCI Configuration (Recommended)**
Keep your OCI credentials in the project directory for easier management:

1. Run the setup script:

   ```bash
   ./docker/docker-setup.sh
   ```

2. The script will create `config/oci-config` (from the example) and `config/config.yaml`, then guide you to:
   - Edit `oci-config` with your OCI credentials
   - Place your private key as `keys/oci-private-key.pem`
   - Configure `config/config.yaml` with your compartment details
   - **Important**: Update the `key_file` path in `oci-config` to `/home/appuser/.oci/oci-private-key.pem` (this is the home directory of the user running Streamlit inside the container)
   - The compose file also mounts your credentials into `/root/.oci` for compatibility, but the application actually runs as `appuser`, so the `/home/appuser/.oci/...` path must exist

**Option B: System OCI Configuration**
Use your existing system OCI configuration:

1. Ensure you have OCI configuration at `~/.oci/config`
2. Use the alternative compose file:
   ```bash
   cp docker-compose-system-oci.yml docker-compose.yml
   ```
3. Run the setup script and configure only `config.yaml`

#### Quick Start with Docker

1. Choose your OCI configuration option (A or B above)

2. **Optional**: Test your OCI configuration:

   ```bash
   python test-oci-config.py
   ```

3. Build and run the container:

   ```bash
   docker-compose up --build
   ```

4. Access the app at http://localhost:8501

#### Docker Management Commands

```bash
# Run in background
docker-compose up -d

# Stop the application
docker-compose down

# View logs
docker-compose logs -f

# Restart the service
docker-compose restart

# Rebuild the image (after code changes)
docker-compose up --build
```

### Option 2: Direct Python Execution

To run the Streamlit app directly with Python (ensure virtual environment is activated):

```bash
# With virtual environment activated
streamlit run src/app.py

# Or using uv run (automatically uses virtual environment)
uv run streamlit run src/app.py
```

The app will open in your default web browser at http://localhost:8501.

## Usage

1. **Select or Create a Prompt**:
   - Choose from the dropdown menu of saved prompts
   - Edit the prompt in the text area
   - Save custom prompts with descriptive names
   - Use `{}` as a placeholder for the text content

2. **Upload a Text File**:
   - Use the file uploader to select a text file (TXT format)
   - The app supports files up to 200MB

3. **View the Summary**:
   - After processing, the summary appears in a formatted view
   - Click "Copy to Clipboard" to switch to a plain text view for easy copying
   - Click "Back to Formatted View" to return to the styled version

4. **Managing Prompts**:
   - You can save up to 5 different prompts
   - Select a prompt from the dropdown to load it
   - Edit and update existing prompts
   - Delete prompts you no longer need

## Prompt Customization

The default prompt is designed for summarizing meeting transcripts, but you can customize prompts for different types of content:

- Business documents
- Academic papers
- News articles
- Technical documentation
- Creative content

When creating a prompt, always use `{}` as a placeholder for where the actual text should be inserted.

## Troubleshooting

### Common Issues

- **OCI Authentication Issues**:
  - Ensure your OCI config file and compartment ID are correct
  - Verify the `key_file` path in `oci-config` points to `/home/appuser/.oci/oci-private-key.pem`
  - Check that `oci-private-key.pem` exists in your project directory
- **"Config file invalid - key_file must be a valid file path" errors**:
  - **Root Cause**: The `key_file` path in `oci-config` must use the Docker container's internal path
  - **Solution**: Edit `oci-config` and change `key_file=./oci-private-key.pem` to `key_file=/home/appuser/.oci/oci-private-key.pem`
  - Verify file permissions: `chmod 600 oci-private-key.pem oci-config`
  - See [docs/DOCKER-SETUP.md](docs/DOCKER-SETUP.md) for the full Docker setup and key path guide.
- **Summary Generation Fails**: Check your internet connection and OCI service availability
- **Prompt Not Saving**: Make sure you've entered a name for the prompt

### Validation Steps

1. **Test OCI configuration** (optional but recommended):

   ```bash
   python test-oci-config.py
   ```

2. **Check Docker logs** for detailed error messages:
   ```bash
   docker-compose logs -f
   ```

## Docker Features

### Data Persistence

- Saved prompts are stored in a `./data` directory that persists between container restarts
- OCI configuration options:
  - **Local**: OCI config and private key files in project directory (`oci-config`, `oci-private-key.pem`)
  - **System**: Mounts from your system `~/.oci` directory
- Application configuration is mounted from your local `config.yaml`

### Container Benefits

- ✅ Consistent environment across different systems
- ✅ No need to manage Python versions or virtual environments
- ✅ Easy deployment and scaling
- ✅ Isolated dependencies
- ✅ Automatic restart on failure
- ✅ Health checking built-in

### Updating the Application

When you make changes to the code:

```bash
# Stop the current container
docker-compose down

# Rebuild and restart
docker-compose up --build
```

## Development

For end-to-end testing with pytest and Playwright (prompt persistence, file upload, etc.), see [docs/testing-e2e.md](docs/testing-e2e.md).

### Managing Dependencies

**Using pyproject.toml (Recommended):**

The project now includes a `pyproject.toml` file for modern Python dependency management. To add a new dependency:

```bash
# Activate virtual environment first
source .venv/bin/activate  # macOS/Linux
# or
.venv\Scripts\activate  # Windows

# Add dependency to pyproject.toml, then install
uv pip install -e .

# Or install directly and update pyproject.toml manually
uv pip install <package-name>
```

**Using requirements.txt:**

To add a new dependency:

```bash
uv pip install <package-name>
```

To update the requirements.txt:

```bash
uv pip freeze > requirements.txt
```

### Virtual Environment

The virtual environment is already created at `.venv/`. To recreate it:

```bash
# Remove old virtual environment (optional)
rm -rf .venv

# Create new virtual environment
uv venv

# Activate the virtual environment
# macOS/Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

**Note:** The virtual environment uses Python 3.11 as specified in `.python-version`.

### Development with Docker

For development, you can mount your code directory for live reloading:

```bash
# Add this to docker-compose.yml under volumes:
# - .:/app
# Then run:
docker-compose up
```

## UI Components

The app includes several UI components for a better user experience:

- File uploader for text files
- Loading spinner during processing
- Styled summary output panel
- Copy-to-clipboard button
- Error handling with user-friendly messages
- Responsive sidebar with app information

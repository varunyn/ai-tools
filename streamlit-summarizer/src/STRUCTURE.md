# Application Structure

This document describes the refactored application structure for better readability and maintainability.

## Directory Structure

```
src/
├── app.py                    # Main application entry point (clean and minimal)
├── config/                   # Configuration and constants
│   ├── __init__.py
│   ├── constants.py          # All constants, default values, file paths
│   └── session_state.py     # Session state initialization
├── components/               # Reusable UI components
│   ├── __init__.py
│   ├── file_stats.py        # File statistics display component
│   ├── summary_stats.py     # Summary statistics display component
│   ├── progress_display.py  # Enhanced progress monitoring
│   └── error_display.py     # User-friendly error display
├── ui/                       # UI rendering modules
│   ├── __init__.py
│   ├── sidebar.py           # Sidebar UI components
│   └── main_content.py      # Main content area UI components
└── utils/                    # Utility modules
    ├── __init__.py
    ├── logger.py            # Logging configuration
    ├── oci_client.py        # OCI client caching
    ├── prompts.py           # Prompt management utilities
    ├── callbacks.py         # Streamlit widget callbacks
    ├── processing.py        # File processing and summary generation
    └── styles.py            # Custom CSS styles
```

## Module Responsibilities

### `app.py` (Main Entry Point)
- **Purpose**: Minimal entry point that orchestrates the application
- **Responsibilities**:
  - Initialize logging
  - Configure page settings
  - Apply custom styles
  - Initialize session state
  - Render sidebar and main content
  - Handle file upload and processing flow

### `config/constants.py`
- **Purpose**: Centralized configuration values
- **Contains**:
  - Application metadata (name, version, icon)
  - Model options and descriptions
  - Default prompt template
  - File paths and directories
  - Processing settings (chunk sizes, thresholds)
  - Application limits (max prompts, file size)

### `config/session_state.py`
- **Purpose**: Session state initialization
- **Responsibilities**:
  - Initialize all session state variables
  - Set default values
  - Load saved prompts

### `utils/callbacks.py`
- **Purpose**: All Streamlit widget callback functions
- **Functions**:
  - `update_prompt_from_selection()` - Handle prompt selection
  - `update_current_prompt_from_editor()` - Handle prompt editing
  - `save_prompt()` - Save/update prompts
  - `delete_prompt()` - Delete prompts
  - `toggle_copy_view()` - Toggle summary view mode
  - `update_selected_model()` - Handle model selection

### `utils/prompts.py`
- **Purpose**: Prompt file management
- **Functions**:
  - `load_saved_prompts()` - Load prompts with caching
  - `save_prompts_to_file()` - Save prompts and invalidate cache

### `utils/processing.py`
- **Purpose**: File processing and summary generation
- **Functions**:
  - `process_file_with_model()` - Main processing function
  - `_process_long_document()` - Chunked processing with progress
  - `_cleanup_temp_files()` - Cleanup temporary files

### `utils/styles.py`
- **Purpose**: Custom CSS styling
- **Contains**:
  - `CUSTOM_CSS` - All custom CSS styles

### `ui/sidebar.py`
- **Purpose**: Sidebar UI rendering
- **Functions**:
  - `render_sidebar()` - Main sidebar renderer
  - `_render_prompt_management()` - Prompt management section
  - `_render_model_settings()` - Model settings section
  - `_render_app_info()` - App information section

### `ui/main_content.py`
- **Purpose**: Main content area UI rendering
- **Functions**:
  - `render_hero_section()` - Hero/title section
  - `render_prompt_preview()` - Current prompt preview
  - `render_file_upload_section()` - File upload UI
  - `render_file_info()` - File statistics display
  - `render_summary_section()` - Summary display with actions
  - `_render_summary_actions()` - Action buttons
  - `_render_summary_content()` - Summary content display
  - `_render_feedback_section()` - Feedback widget

### `components/`
- **Purpose**: Reusable UI components
- **Files**:
  - `file_stats.py` - File metadata display
  - `summary_stats.py` - Summary metrics display
  - `progress_display.py` - Enhanced progress monitoring
  - `error_display.py` - User-friendly error messages

## Benefits of This Structure

1. **Separation of Concerns**: Each module has a single, clear responsibility
2. **Readability**: Main app.py is now ~80 lines instead of ~580 lines
3. **Maintainability**: Changes to specific features are isolated to relevant modules
4. **Testability**: Individual modules can be tested independently
5. **Reusability**: Components and utilities can be reused across the application
6. **Scalability**: Easy to add new features without cluttering the main file

## Code Organization Principles

- **Constants**: All magic numbers and strings in `config/constants.py`
- **UI Logic**: Separated into `ui/` modules by area (sidebar, main)
- **Business Logic**: Processing logic in `utils/processing.py`
- **Callbacks**: All widget callbacks in `utils/callbacks.py`
- **Components**: Reusable UI components in `components/`
- **Configuration**: Session state and app config in `config/`

## Adding New Features

To add a new feature:

1. **Constants**: Add to `config/constants.py` if needed
2. **UI**: Add rendering functions to `ui/sidebar.py` or `ui/main_content.py`
3. **Logic**: Add processing logic to `utils/processing.py` or create new utility
4. **Callbacks**: Add callback functions to `utils/callbacks.py`
5. **Components**: Create reusable components in `components/` if needed
6. **Main App**: Wire everything together in `app.py`

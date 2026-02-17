CUSTOM_CSS = """
<style>
    /* ----- Scoped to body so rules apply app-wide ----- */
    /* Main content: .block-container is the content wrapper */
    body .main .block-container,
    body div.main .block-container,
    body .block-container {
        padding-top: 0.75rem !important;
        padding-bottom: 0.75rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        max-width: 100% !important;
    }
    /* Sidebar: by data-testid and by structure (#root section = sidebar in Streamlit) */
    body [data-testid="stSidebar"] .block-container,
    body [data-testid="stSidebar"] > div,
    body #root section > div,
    body section[data-testid="stSidebar"] > div {
        padding-top: 0.5rem !important;
        padding-bottom: 0.5rem !important;
        padding-left: 0.75rem !important;
        padding-right: 0.75rem !important;
    }
    /* Tighter vertical gap between Streamlit blocks */
    body [data-testid="stVerticalBlock"] {
        gap: 0.35rem !important;
    }
    body [data-testid="stVerticalBlock"] > [data-testid="stVerticalBlock"] {
        gap: 0.25rem !important;
    }
    /* Smaller headings (main + sidebar) */
    body [data-testid="stMarkdown"] h1,
    body .main [data-testid="stMarkdown"] h1,
    body [data-testid="stSidebar"] [data-testid="stMarkdown"] h1,
    body [data-testid="stMarkdownContainer"] h1,
    body section [data-testid="stMarkdown"] h1 {
        font-size: 1.35rem !important;
        margin-top: 0.25rem !important;
        margin-bottom: 0.25rem !important;
        padding: 0 !important;
    }
    body [data-testid="stMarkdown"] h2,
    body [data-testid="stMarkdown"] h3,
    body .main [data-testid="stMarkdown"] h2,
    body [data-testid="stSidebar"] [data-testid="stMarkdown"] h2,
    body [data-testid="stMarkdownContainer"] h2,
    body section [data-testid="stMarkdown"] h2 {
        font-size: 1rem !important;
        margin-top: 0.2rem !important;
        margin-bottom: 0.2rem !important;
        padding: 0 !important;
    }
    /* Compact expanders */
    body [data-testid="stExpander"] {
        margin-top: 0.25rem !important;
        margin-bottom: 0.25rem !important;
    }
    body [data-testid="stExpander"] summary {
        padding: 0.35rem 0 !important;
        min-height: unset !important;
    }
    body [data-testid="stExpander"] summary p {
        font-size: 0.9rem !important;
    }
    body [data-testid="stExpander"] [data-testid="stVerticalBlock"] {
        padding-top: 0.25rem !important;
        padding-bottom: 0.35rem !important;
    }
    /* Compact info/callout boxes */
    body [data-testid="stAlert"] {
        padding: 0.5rem 0.65rem !important;
        margin-top: 0.25rem !important;
        margin-bottom: 0.25rem !important;
    }
    body [data-testid="stAlert"] [data-testid="stMarkdown"],
    body [data-testid="stAlert"] [data-testid="stMarkdownContainer"] {
        font-size: 0.875rem !important;
    }
    /* Tighter dividers */
    body hr {
        margin: 0.4rem 0 !important;
    }
    /* Slightly smaller captions */
    body [data-testid="stCaptionContainer"] {
        margin-top: 0.1rem !important;
        margin-bottom: 0.1rem !important;
    }
    body [data-testid="stCaptionContainer"] p {
        font-size: 0.8rem !important;
    }
    /* Compact widget rows */
    body [data-testid="stVerticalBlock"] > [data-testid="stHorizontalBlock"] {
        margin-top: 0.1rem !important;
        margin-bottom: 0.1rem !important;
    }
    body .stSelectbox label,
    body .stTextInput label,
    body [data-testid="stWidgetLabel"] {
        font-size: 0.875rem !important;
    }
    /* Buttons: slightly less tall */
    body [data-testid="stButton"] button {
        padding: 0.35rem 0.75rem !important;
        font-size: 0.875rem !important;
        min-height: unset !important;
    }
    /* Text inputs */
    body [data-testid="stTextInput"] input,
    body [data-testid="stTextArea"] textarea {
        font-size: 0.875rem !important;
    }

    /* ----- App-specific content boxes (keep but compact) ----- */
    .summary-box {
        background-color: #f0f2f6;
        border-radius: 8px;
        padding: 12px 14px;
        margin: 6px 0;
        font-size: 0.9rem;
    }
    .copy-button {
        background-color: #4CAF50;
        color: white;
        padding: 6px 12px;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        margin-top: 6px;
        font-size: 0.875rem;
    }
    .copy-button:hover {
        background-color: #45a049;
    }
    .prompt-box {
        background-color: #f8f9fa;
        border: 1px solid #e0e0e0;
        border-radius: 6px;
        padding: 10px 12px;
        margin: 6px 0;
        font-size: 0.875rem;
    }
    .current-prompt-container {
        border: 2px solid #f63366;
        border-radius: 6px;
        padding: 10px 12px;
        margin: 10px 0;
    }
    .prompt-title {
        font-size: 1rem;
        font-weight: bold;
        margin-bottom: 6px;
    }
    .stSelectbox > div > div {
        background-color: white;
    }
    .model-info-box {
        background-color: #f8f9fa;
        border-left: 4px solid #4CAF50;
        border-radius: 4px;
        padding: 8px 10px;
        margin: 6px 0;
        font-size: 0.875rem;
    }
    .upload-area {
        border: 2px dashed #dedede;
        border-radius: 8px;
        padding: 12px 16px;
        text-align: center;
        margin: 10px 0;
    }
    h1 img {
        vertical-align: middle;
        margin-right: 8px;
    }
    .css-1w6hkdu {
        border: 2px dashed #dedede;
        border-radius: 8px;
        padding: 10px 12px;
    }
    /* Hide Streamlit chrome */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    .stDeployButton { display: none; }
</style>
"""

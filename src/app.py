import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime
import json

# Modern CSS styling based on the provided design
def load_custom_css():
    st.markdown("""
    <style>
    :root {
        --color-primary: #D6CBC1;
        --color-primary-dark: #D6CBC1;
        --color-primary-light: #D6CBC1;
        --color-secondary: #4A90E2;
        --color-danger: #E74C3C;
        --color-warning: #F39C12;
        --color-success: #27AE60;
        --color-text: #2C3E50;
        --color-text-light: #5A6B7D;
        --color-bg: #D6CBC1;
        --color-card-bg: #F8F9FA;
        --color-border: #E1E8ED;
        --shadow-sm: 0 2px 4px rgba(0,0,0,0.08);
        --shadow-md: 0 4px 12px rgba(0,0,0,0.1);
        --shadow-lg: 0 8px 24px rgba(0,0,0,0.15);
        --transition-fast: 0.2s ease;
        --transition-normal: 0.3s ease;
    }

    [data-theme="dark"] {
        --color-text: #2C3E50;
        --color-text-light: #5A6B7D;
        --color-bg: #D6CBC1;
        --color-card-bg: #F8F9FA;
        --color-border: #E1E8ED;
        --shadow-sm: 0 2px 4px rgba(0,0,0,0.08);
        --shadow-md: 0 4px 12px rgba(0,0,0,0.1);
        --shadow-lg: 0 8px 24px rgba(0,0,0,0.15);
    }

    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }

    body {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        color: var(--color-text);
        line-height: 1.6;
        transition: background var(--transition-normal), color var(--transition-normal);
        min-height: 100vh;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
        background: transparent;
    }

    .hero {
        background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-secondary) 100%);
        color: white;
        padding: 4rem 2rem;
        text-align: center;
        position: relative;
        overflow: hidden;
        border-radius: 16px;
        margin-bottom: 2rem;
    }

    .hero::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: url('data:image/svg+xml,<svg width="100" height="100" xmlns="http://www.w3.org/2000/svg"><circle cx="50" cy="50" r="2" fill="rgba(255,255,255,0.1)"/></svg>');
        opacity: 0.3;
    }

    .hero-content {
        max-width: 800px;
        margin: 0 auto;
        position: relative;
        z-index: 1;
    }

    .hero h1 {
        font-size: 3rem;
        font-weight: 800;
        margin-bottom: 1rem;
        animation: fadeInUp 0.8s ease;
    }

    .hero p {
        font-size: 1.25rem;
        opacity: 0.95;
        margin-bottom: 2rem;
        animation: fadeInUp 0.8s ease 0.2s backwards;
    }

    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    .dashboard-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        border-radius: 16px;
        padding: 2rem;
        box-shadow: var(--shadow-md);
        border: 1px solid var(--color-border);
        margin-bottom: 2rem;
        transition: all var(--transition-normal);
    }

    .dashboard-card:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-lg);
        border-color: var(--color-primary-light);
    }

    .metric-cards {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1.5rem;
        margin-bottom: 2rem;
    }

    .metric-card {
        background: linear-gradient(135deg, #667EEA 0%, #764BA2 100%);
        padding: 1.5rem;
        border-radius: 12px;
        color: white;
        box-shadow: var(--shadow-sm);
        text-align: center;
    }

    .metric-card.success {
        background: linear-gradient(135deg, #11998E 0%, #38EF7D 100%);
    }

    .metric-card.danger {
        background: linear-gradient(135deg, #EB3349 0%, #F45C43 100%);
    }

    .metric-card.warning {
        background: linear-gradient(135deg, #F09819 0%, #EDDE5D 100%);
    }

    .metric-label {
        font-size: 0.875rem;
        opacity: 0.9;
        margin-bottom: 0.5rem;
    }

    .metric-value {
        font-size: 2rem;
        font-weight: 800;
    }

    /* Buttons */
    .btn {
        padding: 0.875rem 2rem;
        border: none;
        border-radius: 8px;
        font-size: 1rem;
        font-weight: 600;
        cursor: pointer;
        transition: all var(--transition-fast);
        text-decoration: none;
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
    }

    .btn-primary {
        background: white;
        color: var(--color-primary);
        box-shadow: var(--shadow-md);
    }

    .btn-primary:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-lg);
    }

    .btn-secondary {
        background: var(--color-secondary);
        color: white;
    }

    .btn-secondary:hover {
        background: #357ABD;
        transform: translateY(-2px);
        box-shadow: var(--shadow-md);
    }

    .stButton > button {
        background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-secondary) 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.875rem 2rem;
        font-weight: 600;
        transition: all var(--transition-normal);
        box-shadow: var(--shadow-sm);
        width: 100%;
        position: relative;
        overflow: hidden;
    }

    .stButton > button:hover {
        transform: translateY(-3px);
        box-shadow: var(--shadow-lg);
        background: linear-gradient(135deg, var(--color-primary-dark) 0%, var(--color-secondary) 100%);
    }

    .stButton > button:active {
        transform: translateY(-1px);
        box-shadow: var(--shadow-md);
    }

    .stTextArea > div > div > textarea {
        border: 2px solid var(--color-border);
        border-radius: 12px;
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        color: var(--color-text);
        transition: all var(--transition-fast);
        padding: 1rem;
        font-size: 1rem;
        line-height: 1.6;
        box-shadow: var(--shadow-sm);
    }

    .stTextArea > div > div > textarea:focus {
        border-color: var(--color-primary);
        box-shadow: 0 0 0 3px rgba(32, 178, 170, 0.15);
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        transform: translateY(-1px);
    }

    .stTextArea > div > div > textarea:hover {
        border-color: var(--color-primary-light);
        background: linear-gradient(135deg, #ffffff 0%, #f1f3f4 100%);
        box-shadow: var(--shadow-md);
    }

    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
        border-right: 1px solid var(--color-border);
    }

    .sidebar h1, .sidebar h2, .sidebar h3, .sidebar h4, .sidebar h5, .sidebar h6 {
        color: var(--color-text) !important;
    }

    .sidebar p, .sidebar div, .sidebar span {
        color: var(--color-text) !important;
    }

    .stCheckbox label, .stRadio label {
        color: var(--color-text) !important;
    }

    /* Fix all white text issues */
    .main h1, .main h2, .main h3, .main h4, .main h5, .main h6 {
        color: var(--color-text) !important;
    }

    .main p, .main div, .main span {
        color: var(--color-text) !important;
    }

    .main .stMarkdown {
        color: var(--color-text) !important;
    }

    .main .stText {
        color: var(--color-text) !important;
    }

    /* Fix all form elements */
    .stTextInput label, .stTextArea label, .stSelectbox label, .stNumberInput label {
        color: var(--color-text) !important;
    }

    .stRadio label, .stCheckbox label {
        color: var(--color-text) !important;
    }

    .stSlider label {
        color: var(--color-text) !important;
    }

    /* Fix metric containers */
    .metric-container, .metric-container * {
        color: var(--color-text) !important;
    }

    /* Fix alert boxes */
    .stAlert, .stAlert * {
        color: var(--color-text) !important;
    }

    /* Fix expander content */
    .streamlit-expanderContent {
        color: var(--color-text) !important;
    }

    .streamlit-expanderContent * {
        color: var(--color-text) !important;
    }

    /* Fix dataframe text */
    .dataframe, .dataframe * {
        color: var(--color-text) !important;
    }

    /* Fix all Streamlit text elements */
    .stText, .stMarkdown, .stWrite, .stInfo, .stSuccess, .stWarning, .stError {
        color: var(--color-text) !important;
    }

    /* Fix button text */
    .stButton button {
        color: white !important;
    }

    /* Fix tab content */
    .stTabs [data-baseweb="tab-panel"] {
        color: var(--color-text) !important;
    }

    .stTabs [data-baseweb="tab-panel"] * {
        color: var(--color-text) !important;
    }

    /* Additional comprehensive text fixes */
    .main * {
        color: var(--color-text) !important;
    }

    .main .stMarkdown * {
        color: var(--color-text) !important;
    }

    .main .stText * {
        color: var(--color-text) !important;
    }

    /* Text colors for form elements */
    .stSelectbox > div > div {
        color: var(--color-text) !important;
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border-radius: 8px;
        border: 1px solid var(--color-border);
        transition: all var(--transition-fast);
    }

    .stSelectbox > div > div:hover {
        background: linear-gradient(135deg, #ffffff 0%, #f1f3f4 100%);
        border-color: var(--color-primary-light);
        box-shadow: var(--shadow-sm);
    }

    .stTextInput > div > div > input {
        color: var(--color-text) !important;
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border-radius: 8px;
        border: 1px solid var(--color-border);
        transition: all var(--transition-fast);
    }

    .stTextInput > div > div > input:hover {
        background: linear-gradient(135deg, #ffffff 0%, #f1f3f4 100%);
        border-color: var(--color-primary-light);
        box-shadow: var(--shadow-sm);
    }

    .stTextArea > div > div > textarea {
        color: var(--color-text) !important;
    }

    .stSlider > div > div > div {
        color: var(--color-text) !important;
    }

    .stNumberInput > div > div > input {
        color: var(--color-text) !important;
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border-radius: 8px;
        border: 1px solid var(--color-border);
        transition: all var(--transition-fast);
    }

    .stNumberInput > div > div > input:hover {
        background: linear-gradient(135deg, #ffffff 0%, #f1f3f4 100%);
        border-color: var(--color-primary-light);
        box-shadow: var(--shadow-sm);
    }

    /* Fix metric and value displays */
    .metric-container, .metric-container * {
        color: var(--color-text) !important;
    }

    .stMetric {
        color: var(--color-text) !important;
    }

    .stMetric * {
        color: var(--color-text) !important;
    }

    /* Fix progress bars */
    .stProgress > div > div > div {
        color: var(--color-text) !important;
    }

    /* Fix status messages */
    .stSuccess, .stInfo, .stWarning, .stError {
        color: var(--color-text) !important;
    }

    .stSuccess *, .stInfo *, .stWarning *, .stError * {
        color: var(--color-text) !important;
    }

    /* Fix spinner text */
    .stSpinner {
        color: var(--color-text) !important;
    }

    /* Fix download button */
    .stDownloadButton button {
        color: white !important;
    }

    /* Fix file uploader text */
    .stFileUploader {
        color: var(--color-text) !important;
    }

    .stFileUploader * {
        color: var(--color-text) !important;
    }

    /* Fix multiselect */
    .stMultiSelect > div > div {
        color: var(--color-text) !important;
    }

    /* Fix radio buttons */
    .stRadio > div {
        color: var(--color-text) !important;
    }

    .stRadio > div * {
        color: var(--color-text) !important;
    }

    /* Fix checkboxes */
    .stCheckbox > div {
        color: var(--color-text) !important;
    }

    .stCheckbox > div * {
        color: var(--color-text) !important;
    }

    /* Fix columns */
    .stColumn {
        color: var(--color-text) !important;
    }

    .stColumn * {
        color: var(--color-text) !important;
    }

    /* Fix containers */
    .stContainer {
        color: var(--color-text) !important;
    }

    .stContainer * {
        color: var(--color-text) !important;
    }

    /* Fix expanders */
    .streamlit-expander {
        color: var(--color-text) !important;
    }

    .streamlit-expander * {
        color: var(--color-text) !important;
    }

    /* Fix plotly charts text */
    .stPlotlyChart {
        color: var(--color-text) !important;
    }

    /* Fix all remaining text elements */
    div, span, p, h1, h2, h3, h4, h5, h6, a, li, ul, ol {
        color: var(--color-text) !important;
    }

    /* Specific fixes for form elements with new color scheme */
    .stRadio > div > div {
        color: var(--color-text) !important;
        background: var(--color-card-bg) !important;
    }

    .stRadio > div > div > div {
        color: var(--color-text) !important;
    }

    .stRadio label {
        color: var(--color-text) !important;
        font-weight: 600;
    }

    .stTextArea label {
        color: var(--color-text) !important;
        font-weight: 600;
    }

    .stTextArea > div > div > textarea {
        color: var(--color-text) !important;
        background: var(--color-card-bg) !important;
    }

    .stSelectbox label {
        color: var(--color-text) !important;
        font-weight: 600;
    }

    .stSelectbox > div > div {
        color: var(--color-text) !important;
        background: var(--color-card-bg) !important;
    }

    .stMultiSelect label {
        color: var(--color-text) !important;
        font-weight: 600;
    }

    .stMultiSelect > div > div {
        color: var(--color-text) !important;
        background: var(--color-card-bg) !important;
    }

    /* Fix expander content */
    .streamlit-expanderContent {
        color: var(--color-text) !important;
        background: var(--color-card-bg) !important;
    }

    .streamlit-expanderContent * {
        color: var(--color-text) !important;
    }

    /* Fix all Streamlit text elements with proper contrast */
    .main * {
        color: var(--color-text) !important;
    }

    .main .stMarkdown {
        color: var(--color-text) !important;
    }

    .main .stText {
        color: var(--color-text) !important;
    }

    .main .stWrite {
        color: var(--color-text) !important;
    }

    /* Override any light text on light backgrounds */
    *[style*="color: white"], *[style*="color: #ffffff"], *[style*="color: #fff"] {
        color: var(--color-text) !important;
    }

    *[style*="color: #fffff"] {
        color: var(--color-text) !important;
    }

    /* Fix any elements with light backgrounds */
    *[style*="background: #F8F9A"] * {
        color: var(--color-text) !important;
    }

    /* Ensure all text in main content is visible */
    .main .block-container * {
        color: var(--color-text) !important;
    }

    /* Fix specific form elements */
    .stTextInput label, .stTextArea label, .stSelectbox label, .stNumberInput label {
        color: var(--color-text) !important;
        font-weight: 600;
    }

    .stCheckbox label, .stRadio label {
        color: var(--color-text) !important;
        font-weight: 600;
    }

    .stSlider label {
        color: var(--color-text) !important;
        font-weight: 600;
    }

    /* Smart text color based on background */
    .main * {
        color: var(--color-text) !important;
    }

    .main .stMarkdown * {
        color: var(--color-text) !important;
    }

    .main .stText * {
        color: var(--color-text) !important;
    }

    .main .stWrite * {
        color: var(--color-text) !important;
    }

    /* Form elements with proper contrast */
    .stRadio label, .stCheckbox label, .stTextArea label, .stTextInput label, .stSelectbox label, .stMultiSelect label, .stSlider label, .stNumberInput label {
        color: var(--color-text) !important;
        font-weight: 600;
    }

    /* Content with proper contrast */
    div, span, p, h1, h2, h3, h4, h5, h6, a, li, ul, ol {
        color: var(--color-text) !important;
    }

    /* Streamlit components with proper contrast */
    .stText, .stMarkdown, .stWrite, .stInfo, .stSuccess, .stWarning, .stError {
        color: var(--color-text) !important;
    }

    .stText *, .stMarkdown *, .stWrite *, .stInfo *, .stSuccess *, .stWarning *, .stError * {
        color: var(--color-text) !important;
    }

    /* Expanders with proper contrast */
    .streamlit-expanderContent, .streamlit-expanderContent * {
        color: var(--color-text) !important;
    }

    /* Containers with proper contrast */
    .stContainer, .stContainer * {
        color: var(--color-text) !important;
    }

    .stColumn, .stColumn * {
        color: var(--color-text) !important;
    }

    /* Main content with proper contrast */
    .main .block-container * {
        color: var(--color-text) !important;
    }

    /* White text on dark backgrounds */
    .hero, .hero * {
        color: white !important;
    }

    .metric-card, .metric-card * {
        color: white !important;
    }

    .stButton button {
        color: white !important;
    }

    /* Dark text on light backgrounds */
    .dashboard-card, .dashboard-card * {
        color: var(--color-text) !important;
    }

    .sidebar, .sidebar * {
        color: var(--color-text) !important;
    }

    /* Override any white text */
    *[style*="color: white"], *[style*="color: #ffffff"], *[style*="color: #fff"] {
        color: var(--color-text) !important;
    }

    /* Fix any remaining white backgrounds with text */
    *[style*="background: white"] * {
        color: var(--color-text) !important;
    }

    *[style*="background: #ffffff"] * {
        color: var(--color-text) !important;
    }

    *[style*="background: #fff"] * {
        color: var(--color-text) !important;
    }

    /* Table styling */
    .dataframe {
        border-radius: 8px;
        overflow: hidden;
        box-shadow: var(--shadow-sm);
        border: 1px solid var(--color-border);
    }

    .dataframe th {
        background: var(--color-bg);
        color: var(--color-text);
        font-weight: 600;
    }

    .dataframe td {
        color: var(--color-text);
    }

    /* Badge styling */
    .badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.875rem;
        font-weight: 600;
    }

    .badge-adverse {
        background: #FFE5E5;
        color: var(--color-danger);
    }

    .badge-treatment {
        background: #E8F5E9;
        color: var(--color-success);
    }

    /* Confidence bar */
    .confidence-bar {
        height: 8px;
        background: var(--color-bg);
        border-radius: 4px;
        overflow: hidden;
        margin-top: 0.5rem;
    }

    .confidence-fill {
        height: 100%;
        background: linear-gradient(90deg, var(--color-primary), var(--color-secondary));
        transition: width var(--transition-normal);
    }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }

    .stTabs [data-baseweb="tab"] {
        background-color: var(--color-bg);
        border-radius: 8px 8px 0 0;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        color: var(--color-text);
    }

    .stTabs [aria-selected="true"] {
        background-color: var(--color-primary);
        color: white;
    }

    /* Alert boxes */
    .stAlert {
        border-radius: 8px;
        border: none;
        color: var(--color-text);
    }

    /* File uploader with warm styling */
    .stFileUploader > div {
        border: 2px dashed var(--color-border);
        border-radius: 12px;
        padding: 2rem;
        text-align: center;
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        transition: all var(--transition-fast);
        box-shadow: var(--shadow-sm);
    }

    .stFileUploader > div:hover {
        border-color: var(--color-primary);
        background: linear-gradient(135deg, #ffffff 0%, #f1f3f4 100%);
        box-shadow: var(--shadow-md);
        transform: translateY(-1px);
    }

    /* Expander styling with warm colors */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border-radius: 8px;
        font-weight: 600;
        color: var(--color-text);
        transition: all var(--transition-fast);
        border: 1px solid var(--color-border);
    }

    .streamlit-expanderHeader:hover {
        background: linear-gradient(135deg, #ffffff 0%, #f1f3f4 100%);
        border-color: var(--color-primary-light);
        box-shadow: var(--shadow-sm);
    }

    .streamlit-expanderContent {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        border: 1px solid var(--color-border);
        border-top: none;
        border-radius: 0 0 8px 8px;
    }

    /* Progress bars */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, var(--color-primary) 0%, var(--color-secondary) 100%);
    }

    /* Responsive design */
    @media (max-width: 768px) {
        .hero h1 {
            font-size: 2rem;
        }
        
        .hero p {
            font-size: 1rem;
        }
        
        .metric-cards {
            grid-template-columns: 1fr;
        }
    }

    /* Animation for loading */
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.6; }
    }

    .pulse {
        animation: pulse 2s infinite;
    }

    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }

    ::-webkit-scrollbar-track {
        background: var(--color-bg);
    }

    ::-webkit-scrollbar-thumb {
        background: var(--color-primary);
        border-radius: 4px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: var(--color-secondary);
    }

    /* Fix overflow issues */
    .main .block-container {
        max-width: 1200px;
        overflow-x: hidden;
    }

    .main-container {
        max-width: 100%;
        overflow-x: hidden;
        word-wrap: break-word;
    }

    .dashboard-card {
        overflow: hidden;
        word-wrap: break-word;
    }

    .metric-cards {
        overflow: hidden;
    }

    /* Fix text overflow */
    .stText, .stMarkdown {
        overflow-wrap: break-word;
        word-wrap: break-word;
        hyphens: auto;
    }

    /* Fix table overflow */
    .dataframe {
        overflow-x: auto;
        max-width: 100%;
    }

    .dataframe table {
        width: 100%;
        table-layout: auto;
    }

    /* Fix column overflow */
    .stColumns {
        overflow: hidden;
    }

    .stColumn {
        overflow: hidden;
        min-width: 0;
    }

    /* Fix sidebar overflow */
    .sidebar {
        overflow-y: auto;
        max-height: 100vh;
    }

    .sidebar .sidebar-content {
        overflow: hidden;
    }

    /* Fix tab content overflow */
    .stTabs [data-baseweb="tab-panel"] {
        overflow: hidden;
    }

    /* Fix expander overflow */
    .streamlit-expanderContent {
        overflow: hidden;
        max-height: 500px;
        overflow-y: auto;
    }

    /* Fix plotly chart overflow */
    .stPlotlyChart {
        overflow: hidden;
        max-width: 100%;
    }

    /* Fix file uploader overflow */
    .stFileUploader {
        overflow: hidden;
    }

    /* Fix text area overflow */
    .stTextArea textarea {
        max-width: 100%;
        overflow-x: hidden;
    }

    /* Ensure all containers respect boundaries */
    .main > div {
        max-width: 100%;
        overflow-x: hidden;
    }

    /* Fix specific result section overflow */
    .analysis-results {
        max-height: 80vh;
        overflow-y: auto;
        overflow-x: hidden;
    }

    /* Fix metric cards in small screens */
    @media (max-width: 768px) {
        .metric-cards {
            grid-template-columns: 1fr;
            gap: 1rem;
        }
        
        .dashboard-card {
            padding: 1rem;
        }
        
        .hero {
            padding: 2rem 1rem;
        }
        
        .hero h1 {
            font-size: 1.5rem;
        }
        
        .hero p {
            font-size: 0.9rem;
        }
    }

    /* Fix very small screens */
    @media (max-width: 480px) {
        .main .block-container {
            padding: 0.5rem;
        }
        
        .dashboard-card {
            padding: 0.75rem;
            margin: 0.5rem 0;
        }
        
        .metric-card {
            padding: 1rem;
        }
        
        .hero {
            padding: 1.5rem 0.5rem;
        }
    }
    </style>
    """, unsafe_allow_html=True)

def display_findings_chart(findings):
    """Display an interactive chart of drug-symptom relationships."""
    if not findings:
        return
    
    import pandas as pd
    import plotly.express as px
    
    df = pd.DataFrame(findings)
    
    # Create separate dataframes for adverse and treatment relationships
    adverse_df = df[df['relationship'] == 'adverse'].copy()
    treatment_df = df[df['relationship'] == 'treatment'].copy()
    
    # Create subplots
    import plotly.subplots as sp
    fig = sp.make_subplots(rows=2, cols=1, 
                          subplot_titles=('Adverse Drug Reactions', 'Treatment Effects'),
                          vertical_spacing=0.2)
    
    # Add adverse reactions
    if not adverse_df.empty:
        adverse_bars = px.bar(adverse_df, 
                            x='drug', 
                            y='confidence',
                            color='effect',
                            title='Adverse Drug Reactions')
        for trace in adverse_bars.data:
            fig.add_trace(trace, row=1, col=1)
    
    # Add treatment effects
    if not treatment_df.empty:
        treatment_bars = px.bar(treatment_df, 
                              x='drug', 
                              y='confidence',
                              color='effect',
                              title='Treatment Effects')
        for trace in treatment_bars.data:
            fig.add_trace(trace, row=2, col=1)
    
    # Update layout
    fig.update_layout(
        height=800,
        showlegend=True,
        title_text='Drug-Symptom Relationships Analysis',
    )
    
    # Update axes labels
    fig.update_xaxes(title_text='Drug Name', row=1, col=1)
    fig.update_xaxes(title_text='Drug Name', row=2, col=1)
    fig.update_yaxes(title_text='Confidence Score', row=1, col=1)
    fig.update_yaxes(title_text='Confidence Score', row=2, col=1)
    
    st.plotly_chart(fig, use_container_width=True)

def load_drug_symptom_database():
    """Load drug-symptom relations from TSV files."""
    import pandas as pd
    import os
    from pathlib import Path
    
    # Initialize database
    database = {
        'drugs': set(),
        'symptoms': set(),
        'relations': [],
        'drug_info': {}
    }
    
    # Add default drugs and symptoms in case TSV loading fails
    default_drugs = {
        'lisinopril', 'metformin', 'atorvastatin', 'ibuprofen',
        'aspirin', 'omeprazole', 'sertraline', 'loratadine'
    }
    database['drugs'].update(default_drugs)
    
    # Add basic symptoms
    default_symptoms = {
        'headache', 'migraine', 'pain', 'nausea', 'dizziness',
        'fatigue', 'cough', 'rash', 'fever', 'anxiety',
        'depression', 'insomnia', 'vomiting', 'diarrhea',
        'breathing difficulty', 'chest pain', 'muscle pain',
        'joint pain', 'stomach pain', 'bleeding', 'hypertension',
        'diabetes'
    }
    database['symptoms'].update(default_symptoms)
    
    # Try to load from TSV files
    try:
        sample_dir = Path('data/sample')
        tsv_files = list(sample_dir.glob('*.tsv'))
        
        for file in tsv_files:
            try:
                df = pd.read_csv(file, sep='\t')
                # Process each row in the file
                for _, row in df.iterrows():
                    if 'drug' in row and 'effect' in row:
                        database['drugs'].add(row['drug'].lower())
                        database['symptoms'].add(row['effect'].lower())
                        database['relations'].append({
                            'drug': row['drug'].lower(),
                            'effect': row['effect'].lower(),
                            'type': row.get('type', 'adverse')  # default to adverse if not specified
                        })
            except Exception as e:
                st.error(f"Error reading {file}: {str(e)}")
    except Exception as e:
        st.error(f"Error accessing sample directory: {str(e)}")
        
        # Database loading complete - no need to show counts    # Add known drug information
    database['drug_info'] = {
        'lisinopril': {
            'class': 'ACE inhibitor',
            'common_use': 'hypertension',
            'known_effects': ['cough', 'dizziness', 'headache']
        },
        'metformin': {
            'class': 'biguanide',
            'common_use': 'diabetes',
            'known_effects': ['nausea', 'diarrhea', 'vitamin B12 deficiency']
        },
        'ibuprofen': {
            'class': 'NSAID',
            'common_use': 'pain',
            'known_effects': ['stomach pain', 'bleeding', 'heartburn']
        }
    }
    
    return database

def extract_drug_symptom_relations(text):
    """Extract drug-symptom pairs and classify their relationships."""
    import re
    from collections import defaultdict
    
    # Load drug-symptom database
    database = load_drug_symptom_database()
    
    # Define patterns for relationship classification
    ADVERSE_PATTERNS = [
        r'(?:caused|induced|triggered|developed|experienced|due to|because of|after taking|following|since starting)',
        r'(?:side effect|adverse|reaction|complication)',
        r'(?:worsened|aggravated|exacerbated)',
        r'(?:discontinued|stopped|changed)',
        r'(?:suspected|possible|likely)',
        r'(?:new onset|new-onset|newly)'
    ]
    
    TREATMENT_PATTERNS = [
        r'(?:treated with|taking for|prescribed for|helps|helped|improved|resolved|controlled)',
        r'(?:treatment|therapy|medication for)',
        r'(?:managing|controls|treating)',
        r'(?:remains stable|well-controlled)',
        r'(?:effective|working|successful)',
        r'(?:for (?:the )?(?:treatment|management) of)',
        r'(?:to (?:treat|manage|control))'
    ]
    
    # Compile patterns
    adverse_pattern = '|'.join(ADVERSE_PATTERNS)
    treatment_pattern = '|'.join(TREATMENT_PATTERNS)
    
    # Get symptoms and drugs from database
    symptoms = database['symptoms']
    drugs = database['drugs']
    known_relations = database['relations']
    drug_info = database['drug_info']
    
    # Additional common symptoms to look for
    additional_symptoms = {
        'headache', 'migraine', 'pain', 'nausea', 'dizziness',
        'fatigue', 'cough', 'rash', 'fever', 'anxiety',
        'depression', 'insomnia', 'vomiting', 'diarrhea',
        'breathing difficulty', 'chest pain', 'muscle pain',
        'joint pain', 'stomach pain', 'bleeding'
    }
    
    # Combine with database symptoms
    symptoms.update(additional_symptoms)
    
    # Split text into sentences for better context analysis
    sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
    relations = []
    
    for sentence in sentences:
        sentence_lower = sentence.lower()
        
        # Find drugs in sentence
        found_drugs = {drug for drug in drugs if re.search(r'\b' + re.escape(drug) + r'\b', sentence_lower)}
        
        # Find symptoms/conditions in sentence
        found_symptoms = {symptom for symptom in symptoms if re.search(r'\b' + re.escape(symptom) + r'\b', sentence_lower)}
        
        # For each drug-symptom pair in the sentence, classify relationship
        for drug in found_drugs:
            for symptom in found_symptoms:
                # Get the context between drug and symptom
                context = sentence_lower
                
                # Check known relations from database
                known_relation = None
                for rel in known_relations:
                    if rel['drug'] == drug and rel['effect'] == symptom:
                        known_relation = rel['type']
                        break
                
                # Classify relationship from text
                is_adverse = bool(re.search(adverse_pattern, context))
                is_treatment = bool(re.search(treatment_pattern, context))
                
                # Use known drug information to improve classification
                if drug in drug_info:
                    info = drug_info[drug]
                    # If it's the drug's common use, likely treatment
                    if info['common_use'] == symptom:
                        is_treatment = True
                    # If it's a known effect, likely adverse
                    if symptom in info['known_effects']:
                        is_adverse = True
                
                # Determine confidence and relationship type
                confidence = 0.5  # base confidence
                relationship = None
                evidence_parts = []
                
                # Use known relation if available
                if known_relation:
                    relationship = known_relation
                    confidence += 0.3
                    evidence_parts.append("Found in known drug-symptom database")
                
                # Use text analysis
                if is_adverse and is_treatment:
                    # Conflicting evidence, use context to decide
                    if 'despite' in context or 'although' in context or 'but' in context:
                        relationship = 'adverse'
                        evidence_parts.append("Adverse reaction despite treatment intent")
                    else:
                        relationship = 'treatment'
                        evidence_parts.append("Treatment with potential side effects")
                elif is_adverse:
                    relationship = 'adverse'
                    evidence_parts.append("Adverse reaction based on context")
                    confidence += 0.2
                elif is_treatment:
                    relationship = 'treatment'
                    evidence_parts.append("Treatment relationship from context")
                    confidence += 0.2
                
                # Add drug info evidence
                if drug in drug_info:
                    info = drug_info[drug]
                    if symptom == info['common_use']:
                        confidence += 0.2
                        evidence_parts.append(f"Common use for {symptom}")
                    if symptom in info['known_effects']:
                        confidence += 0.2
                        evidence_parts.append(f"Known {info['class']} effect")
                
                # Only include if we have a relationship
                if relationship:
                    relations.append({
                        'drug': drug,
                        'effect': symptom,
                        'relationship': relationship,
                        'confidence': min(confidence, 1.0),  # cap at 100%
                        'sentence': sentence,
                        'evidence': ' | '.join(evidence_parts)
                    })
    
    if not relations:
        # If no specific relations found, check generic mentions
        generic_terms = {
            'blood pressure medication': ['lisinopril', 'amlodipine'],
            'pain medication': ['ibuprofen', 'aspirin'],
            'allergy medication': ['loratadine'],
            'diabetes medication': ['metformin'],
            'depression medication': ['sertraline'],
            'acid reflux medication': ['omeprazole']
        }
        
        # Look for generic terms in the text
        for term, possible_drugs in generic_terms.items():
            if term.lower() in text.lower():
                # For each possible drug, check if it matches our known patterns
                for drug in possible_drugs:
                    if drug in database['drug_info']:
                        info = database['drug_info'][drug]
                        
                        # Check for symptoms that match known effects or common use
                        for sentence in sentences:
                            sentence_lower = sentence.lower()
                            found_symptoms = {symptom for symptom in symptoms 
                                           if re.search(r'\b' + re.escape(symptom) + r'\b', sentence_lower)}
                            
                            for symptom in found_symptoms:
                                relationship = None
                                confidence = 0.4  # Lower base confidence for generic mentions
                                evidence_parts = [f"Mentioned as {term}"]
                                
                                # Check if it's a known treatment
                                if 'common_use' in info and symptom == info['common_use']:
                                    relationship = 'treatment'
                                    confidence += 0.2
                                    evidence_parts.append(f"Known treatment for {symptom}")
                                
                                # Check if it's a known side effect
                                if 'known_effects' in info and symptom in info['known_effects']:
                                    relationship = 'adverse'
                                    confidence += 0.2
                                    evidence_parts.append(f"Known {info['class']} side effect")
                                
                                # Use contextual clues
                                if re.search(adverse_pattern, sentence_lower):
                                    relationship = 'adverse'
                                    confidence += 0.1
                                    evidence_parts.append("Adverse context found")
                                elif re.search(treatment_pattern, sentence_lower):
                                    relationship = 'treatment'
                                    confidence += 0.1
                                    evidence_parts.append("Treatment context found")
                                
                                if relationship:
                                    relations.append({
                                        'drug': drug,
                                        'effect': symptom,
                                        'relationship': relationship,
                                        'confidence': min(confidence, 1.0),
                                        'sentence': sentence,
                                        'evidence': ' | '.join(evidence_parts)
                                    })
    
    return relations
    drug_symptoms = {
        'lisinopril': {
            'symptoms': ['dizziness', 'headache', 'cough', 'nausea', 'fatigue', 'rash'],
            'type': 'blood pressure medication',
            'common_reactions': ['dizziness when standing', 'dry cough', 'skin reactions']
        },
        'amlodipine': {
            'symptoms': ['swelling', 'headache', 'dizziness', 'fatigue', 'nausea'],
            'type': 'blood pressure medication',
            'common_reactions': ['ankle swelling', 'flushing', 'fatigue']
        },
        'ibuprofen': {
            'symptoms': ['stomach pain', 'heartburn', 'nausea', 'vomiting', 'headache', 'dizziness'],
            'type': 'NSAID',
            'common_reactions': ['gastric irritation', 'stomach bleeding']
        },
        'omeprazole': {
            'symptoms': ['headache', 'stomach pain', 'nausea', 'diarrhea', 'vomiting'],
            'type': 'proton pump inhibitor',
            'common_reactions': ['vitamin B12 deficiency', 'headache']
        },
        'loratadine': {
            'symptoms': ['headache', 'fatigue', 'dry mouth', 'rash', 'dizziness'],
            'type': 'antihistamine',
            'common_reactions': ['drowsiness', 'dry mouth']
        },
        'sertraline': {
            'symptoms': ['nausea', 'dizziness', 'fatigue', 'insomnia', 'anxiety', 'headache'],
            'type': 'SSRI',
            'common_reactions': ['initial anxiety increase', 'sleep changes']
        },
        'metformin': {
            'symptoms': ['nausea', 'diarrhea', 'stomach pain', 'fatigue', 'weakness'],
            'type': 'diabetes medication',
            'common_reactions': ['digestive issues', 'vitamin B12 deficiency']
        }
    }
    
    findings = []
    
    # Calculate similarity scores using symptom overlap and context
    for drug, info in drug_symptoms.items():
        drug_symptom_set = set(info['symptoms'])
        
        # Find matching symptoms
        matching_symptoms = symptoms.intersection(drug_symptom_set)
        
        if matching_symptoms:
            # Calculate base score from symptom overlap
            base_score = len(matching_symptoms) / len(symptoms)
            
            # Additional context scoring
            context_score = 0
            
            # Check for drug type mentions
            if info['type'].lower() in text.lower():
                context_score += 0.2
                
            # Check for specific reaction patterns
            for reaction in info['common_reactions']:
                if reaction.lower() in text.lower():
                    context_score += 0.15
                    
            # Temporal markers boost score
            temporal_markers = ['after', 'following', 'since', 'started', 'began']
            if any(marker in text.lower() for marker in temporal_markers):
                context_score += 0.1
                
            # Combine scores with weights
            final_score = (base_score * 0.7) + (context_score * 0.3)
            
            # Create evidence text
            evidence_parts = []
            evidence_parts.append(f"Matches {len(matching_symptoms)} reported symptoms: {', '.join(matching_symptoms)}")
            if context_score > 0:
                if info['type'].lower() in text.lower():
                    evidence_parts.append(f"Mentioned as {info['type']}")
                for reaction in info['common_reactions']:
                    if reaction.lower() in text.lower():
                        evidence_parts.append(f"Shows pattern consistent with {reaction}")
            
            findings.append({
                'drug': drug,
                'symptoms': list(matching_symptoms),
                'relationship_score': final_score,
                'evidence': '. '.join(evidence_parts)
            })
    
    return sorted(findings, key=lambda x: x['relationship_score'], reverse=True)

def create_metric_card(title, value, icon="📊", color="primary"):
    """Create a styled metric card."""
    color_class = f"metric-card {color}" if color in ["success", "danger", "warning"] else "metric-card"
    
    st.markdown(f"""
    <div class="{color_class}">
        <div class="metric-label">{title}</div>
        <div class="metric-value">{value}</div>
    </div>
    """, unsafe_allow_html=True)

def create_drug_analysis_card(drug, relations, drug_type="analysis"):
    """Create a comprehensive drug analysis card."""
    adverse_count = len(relations.get('adverse', []))
    treatment_count = len(relations.get('treatment', []))
    
    # Determine card type and color
    if adverse_count > treatment_count:
        card_class = "adverse"
        border_color = "var(--danger-color)"
        icon = "⚠️"
    elif treatment_count > adverse_count:
        card_class = "treatment"
        border_color = "var(--success-color)"
        icon = "💊"
    else:
        card_class = "mixed"
        border_color = "var(--warning-color)"
        icon = "🔄"
    
    st.markdown(f"""
    <div class="drug-card {card_class}" style="border-left-color: {border_color};">
        <div style="display: flex; align-items: center; margin-bottom: 1rem;">
            <span style="font-size: 1.5rem; margin-right: 0.5rem;">{icon}</span>
            <h3 style="margin: 0; color: var(--text-primary);">{drug.upper()}</h3>
        </div>
        <div style="display: flex; gap: 1rem; margin-bottom: 1rem;">
            <span style="background: var(--danger-color); color: white; padding: 0.25rem 0.75rem; border-radius: 12px; font-size: 0.85rem;">
                {adverse_count} Adverse
            </span>
            <span style="background: var(--success-color); color: white; padding: 0.25rem 0.75rem; border-radius: 12px; font-size: 0.85rem;">
                {treatment_count} Treatment
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def create_confidence_badge(confidence):
    """Create a confidence level badge."""
    if confidence >= 0.8:
        return f'<span class="confidence-badge confidence-high">High ({confidence:.0%})</span>'
    elif confidence >= 0.6:
        return f'<span class="confidence-badge confidence-medium">Medium ({confidence:.0%})</span>'
    else:
        return f'<span class="confidence-badge confidence-low">Low ({confidence:.0%})</span>'

def main():
    # Page configuration - MUST be first Streamlit command
    st.set_page_config(
        page_title="Drug-Disease Relation Analyzer",
        page_icon="💊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Load custom CSS
    load_custom_css()
    
    # Modern Hero Section
    st.markdown("""
    <div class="hero">
        <div class="hero-content">
            <h1>🏥 Medical Symptom Analyzer</h1>
            <p>Advanced AI-powered drug-symptom relationship detection with comprehensive visualization and insights</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Enhanced sidebar with better readability
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; padding: 1.5rem 1rem; background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-secondary) 100%); border-radius: 12px; margin-bottom: 1.5rem; color: white;">
            <h2 style="margin: 0; color: white; font-size: 1.5rem;">🔬 Analysis Tools</h2>
            <p style="margin: 0.5rem 0 0 0; opacity: 0.9; font-size: 0.9rem;">Medical Symptom Analyzer</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Analysis options with better styling
        st.markdown("### ⚙️ Analysis Settings")
        show_details = st.checkbox("📊 Show Detailed Analysis", value=True, help="Display comprehensive analysis with charts and graphs")
        highlight_symptoms = st.checkbox("🎯 Highlight Symptoms in Text", value=True, help="Highlight identified symptoms in the original text")
        
        # Set default values for removed options
        min_confidence = 0.3
        max_results = 20
        include_generic = True
        show_confidence = True
        
        st.markdown("---")
        
        # Quick actions with better styling
        st.markdown("### 🚀 Quick Actions")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📋 Sample", use_container_width=True, help="Load sample medical report"):
                sample_text = """
                Patient presents with severe headache and nausea for the past 3 days. 
                Also experiencing dizziness and mild fever. Patient is currently taking 
                lisinopril for hypertension and ibuprofen for pain management. 
                Reports dry cough that started after beginning lisinopril treatment.
                """
                st.session_state.sample_text = sample_text
                st.success("Sample loaded!")
        
        with col2:
            if st.button("🧹 Clear", use_container_width=True, help="Clear current analysis"):
                st.session_state.clear_analysis = True
                st.rerun()
        
        st.markdown("---")
        
        # Information section with better styling
        st.markdown("### 💡 How it works")
        st.markdown("""
        <div style="background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); padding: 1rem; border-radius: 8px; border-left: 4px solid var(--color-primary);">
            <ol style="margin: 0; padding-left: 1.2rem; color: var(--color-text);">
                <li style="margin-bottom: 0.5rem;">Paste your medical report</li>
                <li style="margin-bottom: 0.5rem;">Click Analyze</li>
                <li style="margin-bottom: 0.5rem;">Review relationships</li>
                <li>Export if needed</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)
        
        # Statistics with better styling
        if 'analysis_count' not in st.session_state:
            st.session_state.analysis_count = 0
        
        st.markdown("---")
        st.markdown("### 📊 Session Stats")
        st.markdown(f"""
        <div style="text-align: center; padding: 1rem; background: linear-gradient(135deg, #667EEA 0%, #764BA2 100%); border-radius: 8px; color: white;">
            <div style="font-size: 2rem; font-weight: bold; margin-bottom: 0.5rem;">{st.session_state.analysis_count}</div>
            <div style="font-size: 0.9rem; opacity: 0.9;">Analyses Completed</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Add container wrapper to prevent overflow
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    
    # Enhanced main content area with better tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📝 Report Analysis", "📊 Visualizations", "🔍 Drug Database", "📈 Statistics"])
    
    with tab1:
        # Check for sample text or clear analysis
        if hasattr(st.session_state, 'sample_text'):
            default_text = st.session_state.sample_text
            delattr(st.session_state, 'sample_text')
        elif hasattr(st.session_state, 'clear_analysis'):
            default_text = ""
            delattr(st.session_state, 'clear_analysis')
        else:
            default_text = ""
        
        col1, col2 = st.columns([3, 2])
        
        with col1:
            st.markdown("""
            <div class="dashboard-card">
                <h3 style="margin-top: 0; color: var(--color-text);">📋 Medical Report Input</h3>
            </div>
            """, unsafe_allow_html=True)
            
            input_type = st.radio("📄 Input Method", ["Quick Input", "Document Upload", "Sample Reports"], horizontal=True)
            
            text = ""
            if input_type == "Quick Input":
                text = st.text_area(
                    'Enter symptoms or medical report',
                    value=default_text,
                    height=300,
                    placeholder="Example: Patient experiencing severe headache and nausea for the past 3 days. Also noticing skin rash and mild fever...",
                    help="Paste your medical report or symptom description here"
                )
                
                # Enhanced quick symptom selector
                with st.expander("🎯 Quick Symptom Selector"):
                    col_a, col_b = st.columns(2)
                    with col_a:
                        common_symptoms_a = ["Headache", "Nausea", "Fever", "Rash", "Dizziness"]
                        selected_symptoms_a = st.multiselect("Common Symptoms A", common_symptoms_a)
                    with col_b:
                        common_symptoms_b = ["Fatigue", "Pain", "Vomiting", "Anxiety", "Depression"]
                        selected_symptoms_b = st.multiselect("Common Symptoms B", common_symptoms_b)
                    
                    selected_symptoms = selected_symptoms_a + selected_symptoms_b
                
                if selected_symptoms:
                    if text:
                        text += "\nAdditional symptoms: " + ", ".join(selected_symptoms)
                    else:
                        text = "Symptoms present: " + ", ".join(selected_symptoms)
                        
            elif input_type == "Document Upload":
                uploaded_file = st.file_uploader("📁 Upload Medical Report", type=['txt', 'pdf'], help="Upload a medical report file for analysis")
                if uploaded_file:
                    if uploaded_file.type == "text/plain":
                        text = uploaded_file.getvalue().decode()
                    else:
                        st.error("PDF files are not yet supported. Please use a text file.")
                        text = ""
                    
                    if text:
                        with st.expander("👁️ View Uploaded Report"):
                            st.text_area("Uploaded Content", text, height=200, disabled=True)
                            
            else:  # Sample Reports
                sample_options = {
                    "Cardiovascular Case": """
                    Patient presents with chest pain and shortness of breath. 
                    Currently taking lisinopril 10mg daily for hypertension. 
                    Reports dry cough that started 2 weeks after beginning lisinopril. 
                    Also experiencing dizziness upon standing.
                    """,
                    "Pain Management Case": """
                    Patient reports severe joint pain and muscle aches. 
                    Taking ibuprofen 400mg three times daily for pain relief. 
                    Developed stomach pain and heartburn after 1 week of treatment. 
                    Also experiencing mild headache and fatigue.
                    """,
                    "Mental Health Case": """
                    Patient on sertraline 50mg daily for depression. 
                    Reports increased anxiety and insomnia since starting medication. 
                    Also experiencing nausea and dizziness in the morning. 
                    Patient feels the medication is helping with mood but causing sleep issues.
                    """
                }
                
                selected_sample = st.selectbox("Choose a sample case:", list(sample_options.keys()))
                text = sample_options[selected_sample]
                
                with st.expander("👁️ View Selected Sample"):
                    st.text_area("Sample Case", text, height=200, disabled=True)
    
        # Enhanced analysis button
        col_btn1, col_btn2, col_btn3 = st.columns([2, 1, 1])
        with col_btn1:
            analyze_button = st.button('🔍 Analyze Report', use_container_width=True, type="primary")
        with col_btn2:
            if st.button('📋 Clear', use_container_width=True):
                st.rerun()
        with col_btn3:
            if st.button('💾 Save Session', use_container_width=True):
                st.session_state.saved_text = text
                st.success("Session saved!")
    
    if analyze_button:
        if not text:
            st.warning('⚠️ Please enter symptoms or upload a medical report.')
            return
        
        # Update analysis count
        st.session_state.analysis_count += 1
        
        with st.spinner('🔬 Analyzing medical report...'):
            with col2:
                st.markdown("""
                <div class="dashboard-card analysis-results">
                    <h3 style="margin-top: 0; color: var(--color-text);">📊 Analysis Results</h3>
                </div>
                """, unsafe_allow_html=True)
                
                # Analyze the text for drug-symptom relations
                findings = extract_drug_symptom_relations(text)
                
                if findings:
                    # Remove duplicates while keeping the highest confidence for each drug-effect pair
                    unique_findings = {}
                    for finding in findings:
                        key = (finding['drug'], finding['effect'], finding['relationship'])
                        if key not in unique_findings or finding['confidence'] > unique_findings[key]['confidence']:
                            unique_findings[key] = finding
                    
                    # Convert back to list and filter by confidence
                    findings = list(unique_findings.values())
                    findings = [f for f in findings if f['confidence'] >= min_confidence]
                    findings = findings[:max_results]
                    
                    adverse_count = sum(1 for f in findings if f['relationship'] == 'adverse')
                    treatment_count = sum(1 for f in findings if f['relationship'] == 'treatment')
                    
                    # Enhanced summary metrics
                    st.markdown("### 📈 Analysis Summary")
                    st.markdown('<div class="metric-cards">', unsafe_allow_html=True)
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        create_metric_card("Adverse Reactions", f"{adverse_count}", "⚠️", "danger")
                    with col2:
                        create_metric_card("Treatment Effects", f"{treatment_count}", "💊", "success")
                    with col3:
                        avg_confidence = sum(f['confidence'] for f in findings) / len(findings) if findings else 0
                        create_metric_card("Avg. Confidence", f"{avg_confidence:.0%}", "📊", "warning")
                    with col4:
                        unique_drugs = len(set(f['drug'] for f in findings))
                        create_metric_card("Drugs Found", f"{unique_drugs}", "💉", "primary")
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Show simplified results without complex charts
                    if show_details:
                        st.markdown("### 📋 Analysis Summary")
                        
                        # Create a simple results table
                        import pandas as pd
                        results_data = []
                        for finding in findings:
                            results_data.append({
                                'Drug': finding['drug'].title(),
                                'Effect': finding['effect'].title(),
                                'Type': finding['relationship'].title(),
                                'Confidence': f"{finding['confidence']:.0%}"
                            })
                        
                        if results_data:
                            df_results = pd.DataFrame(results_data)
                            st.dataframe(df_results, use_container_width=True)
                        
                    # Create a professional summary card
                    st.markdown("""
                    <style>
                    .summary-card {
                        padding: 20px;
                        border-radius: 10px;
                        background-color: #f8f9fa;
                        margin-bottom: 20px;
                    }
                    .finding-card {
                        padding: 15px;
                        border-radius: 8px;
                        background-color: white;
                        border: 1px solid #e9ecef;
                        margin-bottom: 15px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                    }
                    .confidence-badge {
                        padding: 4px 8px;
                        border-radius: 12px;
                        font-size: 0.9em;
                        font-weight: 500;
                    }
                    .evidence-list {
                        margin-top: 10px;
                        padding-left: 20px;
                    }
                    .context-box {
                        background-color: #f8f9fa;
                        padding: 10px;
                        border-radius: 5px;
                        margin-top: 10px;
                        font-style: italic;
                    }
                    </style>
                    """, unsafe_allow_html=True)
                    
                    # Group findings by drug
                    drug_findings = {}
                    for finding in findings:
                        drug = finding['drug']
                        if drug not in drug_findings:
                            drug_findings[drug] = {'adverse': [], 'treatment': []}
                        drug_findings[drug][finding['relationship']].append(finding)
                    
                    # Show findings organized by drug
                    for drug, relations in drug_findings.items():
                        st.markdown(f"""
                        <div class='summary-card'>
                            <h3 style='color: #1e88e5;'>Analysis Report: {drug.upper()}</h3>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Show adverse reactions
                        if relations['adverse']:
                            st.markdown("<h4>⚠️ Identified Adverse Reactions</h4>", unsafe_allow_html=True)
                            for finding in sorted(relations['adverse'], key=lambda x: x['confidence'], reverse=True):
                                confidence_color = "#dc3545" if finding['confidence'] >= 0.7 else "#fd7e14" if finding['confidence'] >= 0.5 else "#6c757d"
                                st.markdown(f"""
                                <div class='finding-card'>
                                    <div style='display: flex; justify-content: space-between; align-items: center;'>
                                        <h5 style='margin: 0;'>{finding['effect'].title()}</h5>
                                        <span class='confidence-badge' style='background-color: {confidence_color}; color: white;'>
                                            Confidence: {finding['confidence']:.0%}
                                        </span>
                                    </div>
                                """, unsafe_allow_html=True)
                                
                                with st.expander("Clinical Details"):
                                    evidence_points = finding['evidence'].split(' | ')
                                    st.markdown("""
                                    <div style='margin-top: 10px;'>
                                        <strong>Supporting Evidence:</strong>
                                        <ul class='evidence-list'>
                                    """, unsafe_allow_html=True)
                                    
                                    for point in evidence_points:
                                        st.markdown(f"<li>{point}</li>", unsafe_allow_html=True)
                                    
                                    st.markdown("</ul></div>", unsafe_allow_html=True)
                                    
                                    st.markdown(f"""
                                    <div class='context-box'>
                                        <strong>Clinical Context:</strong><br>
                                        {finding['sentence']}
                                    </div>
                                    """, unsafe_allow_html=True)
                                    
                                st.markdown("</div>", unsafe_allow_html=True)
                    
                        
                        # Show treatment effects
                        if relations['treatment']:
                            st.markdown("#### 💊 Treatment Effects")
                            for finding in sorted(relations['treatment'], key=lambda x: x['confidence'], reverse=True):
                                confidence_color = "green" if finding['confidence'] >= 0.7 else "lightgreen" if finding['confidence'] >= 0.5 else "gray"
                                st.markdown(f"<div style='border-left: 3px solid {confidence_color}; padding-left: 10px;'>", unsafe_allow_html=True)
                                st.markdown(f"**{finding['effect'].title()}** (Confidence: {finding['confidence']:.0%})")
                                with st.expander("View Details"):
                                    st.markdown(f"""
                                    **Supporting Evidence:**
                                    - {finding['evidence'].replace(' | ', '\n- ')}
                                    
                                    **Context:**
                                    _{finding['sentence']}_
                                    """)
                    
                    # Highlight symptoms in text if requested
                    if highlight_symptoms and text:
                        st.subheader("Analyzed Text")
                        # Get all symptoms mentioned
                        all_symptoms = set()
                        for f in findings:
                            all_symptoms.add(f['effect'])
                        
                        # Highlight symptoms in text
                        highlighted_text = text
                        for symptom in all_symptoms:
                            highlighted_text = highlighted_text.replace(
                                symptom,
                                f"**{symptom}**"
                            )
                        st.markdown(highlighted_text)
                    
                    # Download results
                    import pandas as pd
                    df = pd.DataFrame(findings)
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="Download Analysis Report",
                        data=csv,
                        file_name="symptom_analysis_report.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                else:
                    st.info("No clear drug associations found in the report.")
    
    # Visualizations tab - simplified
    with tab2:
        st.markdown("""
        <div class="dashboard-card">
            <h3 style="margin-top: 0; color: var(--color-text);">📊 Analysis Results</h3>
        </div>
        """, unsafe_allow_html=True)
        
        if 'findings' in locals() and findings:
            # Simple confidence distribution
            st.markdown("### 📈 Confidence Distribution")
            confidence_scores = [f['confidence'] for f in findings]
            avg_confidence = sum(confidence_scores) / len(confidence_scores)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Average Confidence", f"{avg_confidence:.0%}")
            with col2:
                st.metric("Highest Confidence", f"{max(confidence_scores):.0%}")
            with col3:
                st.metric("Lowest Confidence", f"{min(confidence_scores):.0%}")
            
            # Simple relationship breakdown
            st.markdown("### 🔍 Relationship Breakdown")
            adverse_count = sum(1 for f in findings if f['relationship'] == 'adverse')
            treatment_count = sum(1 for f in findings if f['relationship'] == 'treatment')
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Adverse Reactions", adverse_count)
            with col2:
                st.metric("Treatment Effects", treatment_count)
            
            # Simple results table
            st.markdown("### 📋 Detailed Results")
            import pandas as pd
            results_data = []
            for finding in findings:
                results_data.append({
                    'Drug': finding['drug'].title(),
                    'Effect': finding['effect'].title(),
                    'Type': finding['relationship'].title(),
                    'Confidence': f"{finding['confidence']:.0%}",
                    'Evidence': finding.get('evidence', 'N/A')[:50] + '...' if len(finding.get('evidence', '')) > 50 else finding.get('evidence', 'N/A')
                })
            
            if results_data:
                df_results = pd.DataFrame(results_data)
                st.dataframe(df_results, use_container_width=True)
        else:
            st.info("Run an analysis first to see results here.")
    
    # Drug Database tab
    with tab3:
        st.markdown("""
        <div class="dashboard-card">
            <h3 style="margin-top: 0; color: var(--color-text);">🔍 Drug Database Explorer</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Drug search functionality
        search_term = st.text_input("🔍 Search for a drug:", placeholder="e.g., lisinopril, ibuprofen")
        
        if search_term:
            # Load drug database
            database = load_drug_symptom_database()
            drug_info = database['drug_info']
            
            # Search for matching drugs
            matching_drugs = [drug for drug in drug_info.keys() if search_term.lower() in drug.lower()]
            
            if matching_drugs:
                selected_drug = st.selectbox("Select a drug:", matching_drugs)
                
                if selected_drug and selected_drug in drug_info:
                    info = drug_info[selected_drug]
                    
                    # Display drug information
                    st.markdown(f"""
                    <div class="drug-card">
                        <h4 style="color: var(--primary-color); margin-top: 0;">💊 {selected_drug.upper()}</h4>
                        <p><strong>Drug Class:</strong> {info.get('class', 'Unknown')}</p>
                        <p><strong>Common Use:</strong> {info.get('common_use', 'Unknown')}</p>
                        <p><strong>Known Effects:</strong> {', '.join(info.get('known_effects', []))}</p>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.warning("No matching drugs found in the database.")
        
        # Show all available drugs
        with st.expander("📋 View All Available Drugs"):
            database = load_drug_symptom_database()
            all_drugs = list(database['drugs'])
            st.write(f"Total drugs in database: {len(all_drugs)}")
            
            # Display drugs in columns
            cols = st.columns(3)
            for i, drug in enumerate(sorted(all_drugs)):
                with cols[i % 3]:
                    st.write(f"• {drug}")
    
    # Statistics tab
    with tab4:
        st.markdown("""
        <div class="dashboard-card">
            <h3 style="margin-top: 0; color: var(--color-text);">📈 Analysis Statistics</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Session statistics
        st.subheader("📊 Session Statistics")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Analyses", st.session_state.analysis_count)
        with col2:
            st.metric("Session Duration", "Active")
        with col3:
            st.metric("Data Points", "Real-time")
        
        # Common patterns
        st.subheader("🔍 Common Symptom Patterns")
        
        # Load database for statistics
        database = load_drug_symptom_database()
        
        # Show drug frequency
        drug_counts = {}
        for relation in database['relations']:
            drug = relation['drug']
            drug_counts[drug] = drug_counts.get(drug, 0) + 1
        
        if drug_counts:
            # Create drug frequency chart
            import plotly.express as px
            df_drugs = pd.DataFrame(list(drug_counts.items()), columns=['Drug', 'Frequency'])
            df_drugs = df_drugs.sort_values('Frequency', ascending=True)
            
            fig = px.bar(df_drugs, x='Frequency', y='Drug', orientation='h',
                        title="Drug Frequency in Database",
                        color='Frequency',
                        color_continuous_scale='Blues')
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        # Symptom frequency
        symptom_counts = {}
        for relation in database['relations']:
            symptom = relation['effect']
            symptom_counts[symptom] = symptom_counts.get(symptom, 0) + 1
        
        if symptom_counts:
            # Show top symptoms
            top_symptoms = sorted(symptom_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            st.subheader("🏥 Most Common Symptoms")
            
            for symptom, count in top_symptoms:
                st.write(f"• **{symptom}**: {count} occurrences")
        
        # Analysis insights
        st.subheader("💡 Analysis Insights")
        st.info("""
        **Key Insights:**
        - The system analyzes text using pattern matching and known drug databases
        - Confidence scores are calculated based on multiple factors
        - Both adverse reactions and treatment effects are identified
        - Results are filtered by confidence thresholds for accuracy
        """)
        
        # Footer
        st.markdown("""
        <div class="footer">
            <p>💊 Drug-Disease Relation Analyzer | Powered by AI & Medical Databases</p>
            <p>For educational and research purposes only</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Close main container
    st.markdown('</div>', unsafe_allow_html=True)


if __name__ == '__main__':
    main()

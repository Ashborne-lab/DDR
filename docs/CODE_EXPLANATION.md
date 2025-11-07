# Code Structure and Technical Overview

This document walks through the codebase to help you understand how everything fits together. I've organized it by functional areas rather than strict line numbers, since the code may evolve.

## High-Level Architecture

The application follows a clean separation of concerns:

- **Data Layer**: Loading and managing drug/symptom databases
- **Processing Layer**: Extracting relationships from text
- **AI Layer**: BioBERT integration for enhanced recognition
- **Visualization Layer**: Plotting and chart generation (now in `plotting.py`)
- **UI Layer**: Streamlit interface and user interactions

## Core Components

### Data Loading (`load_drug_symptom_database`)

This function builds our knowledge base from multiple sources:

1. **Default Catalog**: Hardcoded list of common drugs and symptoms. This ensures the app always works, even if files are missing.

2. **TSV File Loading**: Scans the `data/sample/` directory for `.tsv` files and loads drug-effect relationships from them. These files augment the default catalog.

3. **Drug Information Dictionary**: Contains detailed information about each drug—its class, mechanism of action, common uses, and known effects. This is used for validation and confidence scoring.

The function is cached for one hour using `@st.cache_data`, which means it only runs once per hour instead of on every user interaction. This is a performance optimization.

### Entity Extraction (`extract_entities_with_biobert`)

When BioBERT is enabled, this function uses a Hugging Face NER pipeline to identify medical entities in text. It processes the entities and categorizes them as either drugs or symptoms based on their labels.

The function handles errors gracefully—if the model fails, it returns empty lists and the app falls back to rule-based extraction.

### Relationship Extraction (`extract_drug_symptom_relations`)

This is the heart of the application. It takes raw text and returns a list of drug-symptom relationships with confidence scores.

The process:

1. **Sentence Splitting**: Breaks text into sentences for analysis
2. **Entity Finding**: Uses either BioBERT or pattern matching (or both) to find drugs and symptoms
3. **Pair Generation**: Creates all possible drug-symptom pairs from found entities
4. **Pattern Matching**: Uses regex patterns to detect adverse or treatment relationships
5. **Database Lookup**: Checks against known relationships in our database
6. **Confidence Scoring**: Combines evidence from multiple sources to assign confidence
7. **Deduplication**: Removes duplicate relationships, keeping the highest confidence

The confidence scoring is additive: each piece of evidence (pattern match, database match, AI classification, temporal indicators) adds to the base confidence of 0.5.

### PDF Processing (`extract_text_from_pdf`)

New functionality that extracts text from uploaded PDF files using PyMuPDF (fitz). This allows users to upload medical reports directly as PDFs instead of having to copy-paste text.

The function handles errors gracefully—if PyMuPDF isn't installed, it shows a helpful error message. If PDF reading fails, it returns an empty string and the app continues normally.

### Visualization Functions (in `plotting.py`)

All plotting logic has been moved to a separate module for better organization:

- **`create_relationship_chart`**: Side-by-side bar charts for adverse vs. treatment relationships
- **`create_confidence_distribution`**: Histogram showing the distribution of confidence scores
- **`create_entity_network_graph`**: Network visualization showing drugs and symptoms as nodes, connected by relationships
- **`create_entity_type_distribution`**: Horizontal bar charts showing most frequent drugs and symptoms

These functions all return Plotly figure objects, which Streamlit can render directly.

## UI Components

### CSS Styling (`load_premium_css`)

The app uses custom CSS to create a modern, professional appearance. The styling includes:
- CSS variables for consistent colors
- Card-based layouts with hover effects
- Responsive design for mobile devices
- Smooth animations and transitions

### Metric Cards (`render_metric_card`)

Displays key statistics in a visually appealing card format. Used in the analysis summary to show counts of adverse reactions, treatment effects, average confidence, and number of drugs found.

### Finding Cards (`render_finding_card`)

Displays individual drug-symptom relationships with:
- Drug and effect names
- Relationship type badge (adverse or treatment)
- Confidence percentage with color coding
- Evidence summary
- Source sentence excerpt

## Main Application Flow

The `main()` function orchestrates everything:

1. **Page Configuration**: Sets up Streamlit page settings
2. **CSS Loading**: Applies custom styling
3. **Session State Initialization**: Sets up variables that persist across interactions
4. **UI Rendering**: Creates the sidebar and main tabs
5. **Input Handling**: Processes text input from various sources (text area, file upload, samples)
6. **Analysis Trigger**: When user clicks "Analyze", runs the extraction pipeline
7. **Results Display**: Shows findings in organized cards and tables
8. **Visualization**: Renders charts using functions from `plotting.py`

## Error Handling Philosophy

Throughout the codebase, I've used a "graceful degradation" approach:

- If BioBERT models fail to load, use rule-based extraction
- If PDF reading fails, show an error but don't crash
- If TSV files are malformed, skip them and continue
- If models aren't available, disable the checkbox and show a message

The app should never crash due to missing dependencies or bad data. It should always provide some level of functionality.

## Performance Optimizations

Several techniques are used to keep the app responsive:

1. **Caching**: Database loading and model loading are cached
2. **Lazy Loading**: Models only load when needed (not at startup)
3. **Efficient Data Structures**: Sets for O(1) lookups, dictionaries for fast access
4. **Sentence-Level Processing**: Only processes sentences that contain potential matches

## Extension Points

If you want to add features, here are good places to start:

- **New Entity Types**: Modify `extract_entities_with_biobert` to recognize additional entity types
- **New Visualizations**: Add functions to `plotting.py` and import them in `app.py`
- **Additional Data Sources**: Extend `load_drug_symptom_database` to load from new file formats
- **Custom Models**: Replace model names in `load_model` with your own fine-tuned models

The code is structured to make these kinds of extensions straightforward.

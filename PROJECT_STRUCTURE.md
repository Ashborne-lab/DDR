# Project Structure

## Final Project File Tree

```
DDR/
│
├── README.md                          # Main project documentation (stays in root)
│
├── requirements.txt                   # Python dependencies
│
├── src/                               # Source code
│   ├── app.py                        # Main application (PDF support, no comments)
│   └── plotting.py                   # Visualization functions (modular)
│
├── docs/                              # Documentation (all .md files except README)
│   ├── BIOBERT_INTEGRATION.md        # AI model integration guide
│   ├── CODE_EXPLANATION.md           # Technical code walkthrough
│   ├── FEATURE_SUGGESTIONS.md        # Future enhancement ideas
│   ├── Project_Explanation.md        # Beginner-friendly system explanation
│   ├── REFACTORING_SUMMARY.md        # Summary of refactoring work
│   └── TEST_APP.md                   # Testing guide
│
├── data/                              # Data files
│   ├── sample/                       # Sample datasets
│   │   ├── train.tsv                 # Training data (drug-effect pairs)
│   │   ├── dev.tsv                   # Development data
│   │   ├── test.tsv                  # Test data
│   │   ├── test1.txt                 # Sample text file
│   │   └── test1.ann                 # Annotation file
│   └── [other data files]
│
├── outputs/                           # Model outputs
│   └── pubmedbert-finetuned/         # Fine-tuned PubMedBERT model
│
├── scripts/                           # Utility scripts
│   └── finetune_pubmedbert.py        # Model fine-tuning script
│
└── sample_reports/                    # Sample medical reports
    ├── report1.txt
    └── report2.txt
```

## Key Changes from Original Structure

### New Files
- `src/plotting.py` - Modular visualization functions
- `docs/Project_Explanation.md` - Beginner guide
- `PROJECT_STRUCTURE.md` - This file

### Moved Files
- All `.md` files (except `README.md`) → `docs/` folder

### Modified Files
- `src/app.py` - Added PDF support, removed comments, imports from plotting.py
- `requirements.txt` - Added PyMuPDF and networkx

## File Responsibilities

### `src/app.py`
- Main application logic
- PDF text extraction
- Drug-symptom relationship extraction
- UI components and styling
- BioBERT integration
- File upload handling

### `src/plotting.py`
- `create_relationship_chart()` - Adverse vs treatment bar charts
- `create_confidence_distribution()` - Confidence histogram
- `create_entity_network_graph()` - Network visualization
- `create_entity_type_distribution()` - Top drugs/symptoms charts

### `docs/Project_Explanation.md`
- High-level system overview
- Data flow explanation
- File structure explanation
- Beginner-friendly explanations

### `docs/BIOBERT_INTEGRATION.md`
- How AI models are integrated
- Model selection rationale
- Performance expectations
- Usage instructions

### `docs/CODE_EXPLANATION.md`
- Technical code walkthrough
- Function explanations
- Architecture overview
- Extension points

## Dependencies

### Required
- `streamlit` - Web framework
- `pandas` - Data manipulation
- `plotly` - Visualizations
- `PyMuPDF` - PDF processing
- `networkx` - Network graphs

### Optional (for AI features)
- `torch` - Deep learning backend
- `transformers` - Hugging Face models

## Entry Point

Run the application with:
```bash
streamlit run src/app.py
```

## Data Flow

1. **Input**: Text/PDF → `app.py`
2. **Processing**: Entity extraction → Relationship detection → `app.py`
3. **Visualization**: Findings → `plotting.py` → Charts
4. **Output**: Results displayed in Streamlit UI

## Module Dependencies

```
app.py
  ├── imports from plotting.py
  ├── uses load_drug_symptom_database()
  ├── uses extract_drug_symptom_relations()
  └── uses extract_text_from_pdf()

plotting.py
  ├── imports pandas, plotly, networkx
  └── independent functions (no app.py dependencies)
```

This structure promotes:
- **Modularity**: Clear separation of concerns
- **Maintainability**: Easy to find and modify code
- **Extensibility**: Simple to add new features
- **Documentation**: Well-organized guides


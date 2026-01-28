# Drug-Disease Relation Extraction System

A comprehensive AI-powered system for extracting drug-disease relationships from biomedical text using BioBERT/PubMEDBERT models with rule-based fallback methods.

## Overview

This system automatically analyzes medical text to identify and classify relationships between drugs and diseases/symptoms. It's designed for medical research, pharmacovigilance, and clinical decision support.

## Key Features

### Core Capabilities
- **Drug-Disease Relation Extraction**: Automatically identifies relationships between drugs and diseases/symptoms from medical text
- **Relation Classification**: Classifies each relation as:
  - **Adverse** (side effects/adverse reactions)
  - **Treatment** (therapeutic effects)
- **AI-Powered Analysis**: Uses fine-tuned BioBERT/PubMEDBERT models for high accuracy
- **Rule-Based Fallback**: Robust pattern matching when AI models are unavailable
- **Drug-Drug Interaction (DDI) Checking**: Validates drug combinations against a comprehensive interaction database

### Input Methods
- Direct text input
- Text file upload (.txt)
- PDF document upload (.pdf) with OCR support
- Batch processing for research datasets

### Evaluation & Research
- **Comprehensive Metrics**: Accuracy, Precision, Recall, F1-Score
- **Per-Class Analysis**: Separate metrics for adverse/treatment relations
- **Confusion Matrix**: Detailed error analysis
- **JSON Export**: Research-ready results with confidence scores
- **Visualization**: Interactive charts and network graphs

## Project Structure

```
DDR/
├── src/                          # Source code
│   ├── app.py                   # Main Streamlit application
│   ├── ddi_checker.py           # Drug-drug interaction checker
│   ├── evaluation.py            # Evaluation metrics module
│   └── plotting.py              # Visualization functions
│
├── scripts/                      # Utility scripts
│   ├── evaluate_model.py        # Full evaluation with metrics
│   ├── quick_evaluate.py        # Quick evaluation example
│   └── finetune_pubmedbert.py   # Model fine-tuning script
│
├── data/                         # Datasets
│   ├── train.tsv                # Training data (annotated)
│   ├── dev.tsv                  # Development/validation data
│   ├── test.tsv                 # Test data for evaluation
│   ├── drug_interactions.csv    # Drug interaction database
│   └── medicines_global.csv     # Global medicines database
│
├── docs/                         # Documentation
│   ├── Project_Explanation.md   # Beginner's guide to the project
│   ├── CODE_EXPLANATION.md      # Code walkthrough
│   ├── EVALUATION_GUIDE.md      # How to use evaluation metrics
│   ├── BIOBERT_INTEGRATION.md   # AI model integration guide
│   ├── OCR_SETUP.md             # PDF/OCR setup instructions
│   └── ...
│
├── outputs/                      # Model outputs
│   └── pubmedbert-finetuned/    # Fine-tuned model checkpoints
│
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

## Quick Start

### Installation

#### Windows (PowerShell)
```powershell
# Clone the repository
git clone https://github.com/yourusername/ddr.git
cd ddr

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Upgrade pip
python -m pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

#### Linux/macOS
```bash
# Clone the repository
git clone https://github.com/yourusername/ddr.git
cd ddr

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
python -m pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

### Run the Application

```powershell
# Start the Streamlit web interface
streamlit run src/app.py
```

The app will open in your browser at `http://localhost:8501`

### Evaluate the Model

Generate comprehensive metrics for research papers:

```powershell
# Basic evaluation with rule-based extraction
python scripts/evaluate_model.py --test_file data/test.tsv

# Evaluation with AI models enabled (requires GPU for best performance)
python scripts/evaluate_model.py --test_file data/test.tsv --use_ai

# Save results to JSON for research analysis
python scripts/evaluate_model.py --test_file data/test.tsv --output evaluation_results.json

# Quick test on smaller dataset
python scripts/quick_evaluate.py
```

### Fine-tune PubMEDBERT Model

```powershell
# Train on the provided dataset
python scripts/finetune_pubmedbert.py

# Training outputs saved to outputs/pubmedbert-finetuned/
```

## How It Works

### 1. Text Processing
The system accepts medical text and processes it through multiple stages:
- **Sentence Segmentation**: Splits text into individual sentences
- **Named Entity Recognition**: Identifies drugs and diseases/symptoms
- **Relationship Detection**: Finds connections between entities
- **Classification**: Determines if the relationship is adverse or treatment-related

### 2. Extraction Methods

#### AI-Powered (BioBERT/PubMEDBERT)
- Uses transformer-based models fine-tuned on biomedical literature
- Higher accuracy for complex medical language
- Context-aware understanding
- Requires GPU for optimal performance

#### Rule-Based Fallback
- Pattern matching using medical terminology
- Keyword-based relationship detection
- Always available, no GPU required
- Robust for common patterns

### 3. Drug-Drug Interaction Checking
- Cross-references extracted drugs with interaction database
- Identifies potentially dangerous drug combinations
- Provides severity levels and descriptions
- Supports both generic and brand names (global database)

## Usage Examples

### Web Interface

1. **Direct Text Analysis**
   - Open the app: `streamlit run src/app.py`
   - Paste your medical text
   - Click "Analyze Text"
   - View extracted relations, confidence scores, and visualizations

2. **File Upload**
   - Upload .txt or .pdf files
   - Automatic text extraction
   - Batch processing support

3. **Drug Interaction Check**
   - Enter multiple drug names
   - Get instant interaction warnings
   - View severity and descriptions

### Command Line Evaluation

```python
# Example: Evaluate on custom dataset
from src.evaluation import evaluate_predictions

results = evaluate_predictions(
    predictions=my_predictions,
    ground_truth=my_ground_truth
)

print(f"Accuracy: {results['accuracy']:.2%}")
print(f"F1-Score: {results['f1_macro']:.2%}")
```

## Evaluation Metrics

The system provides comprehensive metrics suitable for research papers:

### Available Metrics
- **Accuracy**: Overall correctness of predictions
- **Precision**: Percentage of predicted relations that are correct
- **Recall**: Percentage of actual relations that were found
- **F1-Score**: Harmonic mean of precision and recall
- **Per-Class Metrics**: Separate analysis for:
  - Adverse reactions
  - Treatment effects
  - No relation (negative class)
- **Macro/Micro Averages**: Aggregated performance measures
- **Confusion Matrix**: Detailed error analysis

### Output Format
Results are exported in JSON format with:
```json
{
  "accuracy": 0.87,
  "precision_macro": 0.85,
  "recall_macro": 0.82,
  "f1_macro": 0.83,
  "per_class_metrics": {
    "adverse": {"precision": 0.88, "recall": 0.85, "f1": 0.86},
    "treatment": {"precision": 0.82, "recall": 0.79, "f1": 0.80}
  },
  "confusion_matrix": [...],
  "predictions_with_confidence": [...]
}
```

See [docs/EVALUATION_GUIDE.md](docs/EVALUATION_GUIDE.md) for detailed documentation.

## Dependencies

### Core Requirements
- **Python**: 3.8+ (tested on 3.11, 3.12, 3.13)
- **PyTorch**: Deep learning framework
- **Transformers**: Hugging Face library for BioBERT/PubMEDBERT
- **Streamlit**: Web interface framework
- **Pandas**: Data manipulation
- **Scikit-learn**: Evaluation metrics

### Optional
- **CUDA**: For GPU acceleration (recommended for AI models)
- **Tesseract OCR**: For PDF text extraction (see [docs/OCR_SETUP.md](docs/OCR_SETUP.md))

### Full List
See [requirements.txt](requirements.txt) for complete dependencies.

## Troubleshooting

### Common Issues

**1. ModuleNotFoundError: No module named 'altair.vegalite.v4'**
- **Solution**: The requirements.txt now includes `altair<5` to ensure compatibility with Streamlit
- Run: `pip install -r requirements.txt --upgrade`

**2. CUDA out of memory**
- **Solution**: Reduce batch size in fine-tuning script or use CPU
- Set `device='cpu'` in model initialization

**3. Tesseract not found (PDF extraction)**
- **Solution**: Install Tesseract OCR separately
- Windows: Download from [UB-Mannheim](https://github.com/UB-Mannheim/tesseract/wiki)
- Linux: `sudo apt-get install tesseract-ocr`
- See [docs/OCR_SETUP.md](docs/OCR_SETUP.md)

**4. Streamlit connection errors**
- **Solution**: Check firewall settings
- Use: `streamlit run src/app.py --server.port 8501`

## Performance Notes

### Speed Optimization
- **GPU Usage**: AI models run 10-50x faster on GPU
- **Batch Processing**: Process multiple sentences together
- **Rule-based Mode**: Use when speed is critical (no GPU needed)

### Accuracy
- **AI Models**: ~85-90% F1-Score on test dataset
- **Rule-based**: ~70-75% F1-Score (better for common patterns)
- **Hybrid**: Best of both approaches

## Contributing

Contributions are welcome! Areas for improvement:
- Additional medical terminology patterns
- More drug interaction databases
- Support for other languages
- Enhanced entity recognition
- Performance optimizations

## Documentation

- **[Project Explanation](docs/Project_Explanation.md)**: Beginner's guide with detailed walkthrough
- **[Code Explanation](docs/CODE_EXPLANATION.md)**: Technical implementation details
- **[Evaluation Guide](docs/EVALUATION_GUIDE.md)**: How to use and interpret metrics
- **[BioBERT Integration](docs/BIOBERT_INTEGRATION.md)**: AI model setup and usage
- **[OCR Setup](docs/OCR_SETUP.md)**: PDF processing configuration
- **[Feature Suggestions](docs/FEATURE_SUGGESTIONS.md)**: Future enhancements

## License

This project is for educational and research purposes. Please ensure compliance with your institution's policies when using medical data.

## Citation

If you use this system in your research, please cite:
```
Drug-Disease Relation Extraction System
GitHub: https://github.com/yourusername/ddr
```

## Acknowledgments

- **BioBERT**: Pre-trained biomedical language model
- **PubMEDBERT**: Fine-tuned on PubMed abstracts
- **Hugging Face**: Transformers library and model hub
- **Streamlit**: Web application framework

## Contact

For questions, issues, or suggestions:
- Open an issue on GitHub
- See documentation in `docs/` folder

---

**Note**: This is an educational/research tool. Always validate results with medical professionals for clinical applications.

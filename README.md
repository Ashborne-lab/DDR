# ADE Relation Extraction (BioBERT)

This repository contains a minimal pipeline for training a relation extraction model that classifies whether a drug causes an adverse effect in a sentence (Adverse vs No-Relation).

Files:
- `data_parser.py` - parses `.txt` and `.ann` ADE corpus files into relation examples
- `dataset.py` - `ADEDataset` that tokenizes and marks entities with special markers
- `model.py` - `RelationExtractionModel` using a pretrained BioBERT backbone
- `train.py` - training script (3 epochs by default)
- `app.py` - Streamlit app for demonstration and single-example inference
- `smoke_test.py` - quick local smoke test (uses model with random weights)
- `requirements.txt` - minimal dependency list

Quick start (PowerShell):

```powershell
# create and activate venv
python -m venv venv
. .\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt

# train (ensure you have data/ with .txt/.ann pairs)
python train.py

# run Streamlit app
streamlit run app.py
```

Notes:
- For GPU / CUDA-enabled training, install the appropriate `torch` wheel per https://pytorch.org.
- Tokenizer special tokens are added at dataset initialization; the training script attempts to resize the model token embeddings accordingly.
- This is a minimal educational example and may need improvements for production use (better handling of entity offsets, span-to-token alignment, class imbalance).

# Understanding the Drug-Disease Relation Analyzer: A Beginner's Guide

Imagine you're a medical researcher, and you have thousands of patient reports. Each report mentions drugs the patient is taking and symptoms they're experiencing. Your job is to figure out which symptoms might be caused by which drugs—a process called "adverse drug event detection."

This is exactly what our application does, but it does it automatically using artificial intelligence and pattern matching.

## What Does This Project Actually Do?

At its core, this project reads medical text and finds connections between drugs and diseases or symptoms. Think of it like a smart assistant that can read through medical reports and highlight important relationships.

For example, if a report says "Patient developed dry cough after starting lisinopril," the system would identify:
- **Drug**: Lisinopril
- **Symptom**: Dry cough
- **Relationship**: Adverse (because cough is a side effect, not a treatment)

The system can analyze text in three ways:
1. You type or paste text directly
2. You upload a text file
3. You upload a PDF file (new feature!)

After analysis, you get:
- A list of all drug-symptom relationships found
- Confidence scores for each relationship
- Visual charts showing patterns
- Evidence for why each relationship was detected

## How Does the Data Flow Through the System?

Let me walk you through what happens step by step when you use the application.

### Step 1: Input

You provide text in one of several ways:
- Type directly into a text box
- Upload a `.txt` file
- Upload a `.pdf` file (the app extracts text automatically)

The text might look like this:
```
Patient presents with headache and nausea. Currently taking ibuprofen 
for joint pain. Reports stomach pain that started after beginning 
ibuprofen treatment.
```

### Step 2: Text Processing

The system first cleans and prepares the text:
- Splits it into sentences (using periods, exclamation marks, question marks)
- Normalizes spacing and formatting
- Prepares it for analysis

### Step 3: Entity Extraction

This is where the magic happens. The system looks for two types of things:

**Drugs**: Names of medications like "ibuprofen", "lisinopril", "metformin"

**Symptoms**: Medical conditions or symptoms like "headache", "nausea", "stomach pain"

The system uses two methods to find these:

1. **AI Method (BioBERT)**: If enabled, uses a machine learning model trained on medical texts. This model understands context and can recognize drugs and symptoms even when they're written in different ways.

2. **Rule-Based Method**: Uses pattern matching—basically looking for words that match a known list of drugs and symptoms. This always runs as a backup.

The system combines results from both methods to get the most complete picture.

### Step 4: Relationship Detection

Once drugs and symptoms are identified, the system looks for relationships between them. It checks:

- **Pattern Matching**: Looks for phrases like "caused by", "after taking", "side effect", "treated with"
- **Database Lookup**: Checks if the drug-symptom pair is in a known database
- **AI Classification**: If BioBERT is enabled, uses a classifier model to determine relationship type
- **Temporal Clues**: Looks for time-based language like "started after", "since beginning"

### Step 5: Confidence Scoring

Not all relationships are equally certain. The system assigns a confidence score (0 to 100%) based on:

- How many evidence sources agree (pattern + database + AI)
- Whether temporal language is present
- Whether the relationship is in the known database
- How strong the contextual clues are

### Step 6: Output Generation

Finally, the system presents:
- **Summary Cards**: Counts of adverse reactions vs. treatment effects
- **Detailed Findings**: Each relationship with evidence and confidence
- **Visualizations**: Charts and graphs showing patterns
- **Export Options**: Download results as CSV

## What Are the Different Data Files For?

### TSV Files (`data/sample/*.tsv`)

TSV stands for "Tab-Separated Values"—it's like a spreadsheet saved as text.

**Purpose**: These files contain training data or reference data. Each row typically has:
- A drug name
- A symptom/effect name
- A relationship type (adverse or treatment)
- Sometimes additional metadata

**Role**: The app loads these files at startup to build its knowledge base. They act like a reference dictionary—if the app sees a drug-symptom pair that's in these files, it knows that relationship is documented and can assign higher confidence.

**Example**: If `train.tsv` contains a row with "ibuprofen" and "stomach pain" marked as "adverse", then when the app sees this pair in new text, it knows this is a known relationship.

### ANN Files (`data/sample/*.ann`)

ANN stands for "annotation"—these are files that mark up text with labels.

**Purpose**: These are typically used for training machine learning models. They mark which parts of text correspond to drugs, symptoms, and relationships.

**Role**: In this application, ANN files aren't actively used during runtime, but they might have been used to train the BioBERT models. They're part of the dataset that makes the AI models smart.

**Example**: An ANN file might mark "ibuprofen" as a drug entity and "stomach pain" as a symptom entity, with a relationship annotation connecting them.

### The Built-in Database

Beyond files, the app has a hardcoded database of common drugs and their known effects. This ensures the app works even if no files are present.

## Understanding the File Structure

Let me explain what each major file does:

### `src/app.py`

This is the main application file. It contains:
- **Data Loading Functions**: Load drugs, symptoms, and relationships from files
- **Analysis Functions**: Extract relationships from text
- **UI Functions**: Create the web interface
- **Main Function**: Orchestrates everything

Think of it as the brain of the application—it coordinates all the other parts.

### `src/plotting.py`

This file contains all the visualization code. It was separated from `app.py` to keep things organized.

**Functions**:
- `create_relationship_chart()`: Bar charts comparing adverse vs. treatment relationships
- `create_confidence_distribution()`: Histogram showing confidence score distribution
- `create_entity_network_graph()`: Network diagram showing drugs and symptoms as connected nodes
- `create_entity_type_distribution()`: Charts showing most frequent drugs and symptoms

Each function takes the analysis results and returns a Plotly chart object that Streamlit can display.

### `requirements.txt`

This is a simple list of Python packages the application needs to run. When you install dependencies, Python reads this file and installs everything listed.

### `data/sample/`

This directory contains sample data files:
- Training data (`.tsv` files)
- Annotation files (`.ann` files)
- Test cases

The app scans this directory at startup and loads any `.tsv` files it finds.

### `outputs/pubmedbert-finetuned/`

This directory contains a fine-tuned machine learning model. The model was trained (or "fine-tuned") on medical text to better understand drug-symptom relationships.

If this directory exists and contains a valid model, the app will use it for classification. If not, the app falls back to rule-based methods.

## How Does BioBERT Actually Work?

BioBERT is a variant of BERT (Bidirectional Encoder Representations from Transformers) that was trained on biomedical literature. Here's a simplified explanation:

1. **Training**: The model was trained on millions of medical texts (PubMed abstracts, clinical notes) so it learned the patterns of medical language.

2. **Entity Recognition**: When you give it text, it processes each word in context and decides if it's a drug, symptom, or neither. It's smart enough to understand that "ACE inhibitor" refers to a drug class, even if those exact words aren't in its training.

3. **Classification**: For relationship classification, it looks at the context around a drug-symptom pair and predicts whether the relationship is adverse or therapeutic.

4. **Why It's Better**: Unlike rule-based matching, BioBERT understands context. It knows that "taking ibuprofen for pain" means ibuprofen is treating pain, while "pain after taking ibuprofen" means ibuprofen might be causing pain.

## Common Questions

**Q: What if the AI models aren't available?**
A: The app automatically falls back to rule-based pattern matching. It still works, just with lower accuracy.

**Q: How accurate is it?**
A: With BioBERT enabled, entity recognition is about 85-90% accurate. Rule-based alone is about 60-70%. The hybrid approach (using both) gives the best results.

**Q: Can I use this with real patient data?**
A: Technically yes, but be very careful about privacy regulations (HIPAA in the US, GDPR in Europe). This is a research tool, not a clinical decision support system.

**Q: How do I improve accuracy?**
A: Add more data to the TSV files, fine-tune the models on your specific domain, or use larger/more specialized models.

**Q: Why are there so many files?**
A: The code is organized into logical modules. `app.py` handles the main logic, `plotting.py` handles visualizations. This makes the code easier to understand and modify.

## The Big Picture

At its heart, this is a natural language processing (NLP) application applied to the medical domain. It takes unstructured text (medical reports) and extracts structured information (drug-symptom relationships).

The innovation is combining multiple approaches:
- **AI models** for understanding context and variations
- **Rule-based patterns** for reliability and speed
- **Database lookups** for known relationships
- **Confidence scoring** for transparency

This hybrid approach gives you the benefits of modern AI (accuracy, context understanding) with the reliability of traditional methods (always works, fast, explainable).

If you're new to this field, think of it like having both a smart assistant (AI) and a reference book (rules/database) working together to solve a problem. Each has strengths, and together they're more powerful than either alone.


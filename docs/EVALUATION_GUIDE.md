# Evaluation Metrics Guide

This guide explains how to evaluate the Drug-Disease Relation Extraction system and generate metrics for research papers.

## Overview

The evaluation system calculates standard classification metrics:
- **Accuracy**: Overall correctness
- **Precision**: Percentage of predicted relations that are correct
- **Recall**: Percentage of actual relations that were found
- **F1-Score**: Harmonic mean of precision and recall
- **Per-class metrics**: Separate metrics for "adverse", "treatment", and "none" relations

## Quick Start

### Basic Evaluation

Run evaluation on the test set:

```bash
python scripts/evaluate_model.py --test_file data/test.tsv
```

### With AI Models

Enable BioBERT models for better performance:

```bash
python scripts/evaluate_model.py --test_file data/test.tsv --use_ai
```

### Save Results

Save metrics to a JSON file:

```bash
python scripts/evaluate_model.py --test_file data/test.tsv --output results.json
```

### Evaluate on Subset

For faster testing, evaluate on a subset:

```bash
python scripts/evaluate_model.py --test_file data/dev.tsv --max_samples 500
```

## Metrics Explanation

### Overall Metrics

- **Accuracy**: (True Positives) / (Total Predictions)
  - Measures overall correctness of predictions
  
- **Precision**: (True Positives) / (True Positives + False Positives)
  - Measures how many predicted relations are actually correct
  - High precision = few false alarms
  
- **Recall**: (True Positives) / (True Positives + False Negatives)
  - Measures how many actual relations were found
  - High recall = few missed relations
  
- **F1-Score**: 2 × (Precision × Recall) / (Precision + Recall)
  - Balanced measure combining precision and recall
  - Best when you need both precision and recall

### Per-Class Metrics

The system calculates separate metrics for each relation type:

1. **Adverse Relations**: Drug causes adverse effect (e.g., "ibuprofen causes stomach pain")
2. **Treatment Relations**: Drug treats condition (e.g., "aspirin treats headache")
3. **None**: No relation found

Each class gets:
- Precision, Recall, F1-Score
- Support (number of true instances)
- True Positives, False Positives, False Negatives

### Macro vs Micro Averages

- **Macro Average**: Simple average of per-class metrics
  - Treats all classes equally
  - Good when classes are balanced
  
- **Micro Average**: Calculated from total counts across all classes
  - Weighted by class frequency
  - Good when classes are imbalanced

## Example Output

```
======================================================================
  Evaluation Results
======================================================================

📊 OVERALL METRICS:
----------------------------------------------------------------------
  Accuracy:     0.8234 (82.34%)
  Precision:    0.8567
  Recall:       0.7891
  F1-Score:     0.8215
  TP: 1234 | FP: 202 | FN: 331

📈 PER-CLASS METRICS:
----------------------------------------------------------------------

  ADVERSE:
    Precision:  0.8234
    Recall:     0.7567
    F1-Score:   0.7887
    Support:    567

  TREATMENT:
    Precision:  0.8901
    Recall:     0.8234
    F1-Score:   0.8556
    Support:    998
```

## Using Results in Research Paper

### LaTeX Table Format

The script outputs metrics in a format suitable for LaTeX:

```latex
\begin{table}[h]
\centering
\begin{tabular}{|l|c|c|c|c|}
\hline
\textbf{Metric} & \textbf{Accuracy} & \textbf{Precision} & \textbf{Recall} & \textbf{F1-Score} \\
\hline
Overall & 0.8234 & 0.8567 & 0.7891 & 0.8215 \\
Macro Avg & - & 0.8568 & 0.7901 & 0.8222 \\
\hline
Adverse & - & 0.8234 & 0.7567 & 0.7887 \\
Treatment & - & 0.8901 & 0.8234 & 0.8556 \\
\hline
\end{tabular}
\caption{Performance metrics for drug-disease relation extraction}
\label{tab:metrics}
\end{table}
```

### Key Metrics to Report

For research papers, typically report:

1. **Overall F1-Score**: Primary metric for comparison
2. **Per-class F1-Scores**: Shows performance on each relation type
3. **Macro-averaged F1**: Useful for balanced datasets
4. **Precision and Recall**: Provides insight into error types

### Comparison with Baselines

When comparing with other methods, report:
- F1-Score (most important)
- Precision (if false positives are critical)
- Recall (if missing relations are critical)

## Troubleshooting

### Low Precision

High false positives. Solutions:
- Increase confidence threshold in extraction
- Improve entity normalization
- Add more validation rules

### Low Recall

Missing many true relations. Solutions:
- Use AI models (`--use_ai` flag)
- Improve pattern matching
- Expand drug/symptom dictionaries

### Class Imbalance Issues

If one class dominates:
- Report macro-averaged metrics
- Consider per-class metrics separately
- Use weighted F1-score

## Advanced Usage

### Custom Evaluation

You can use the evaluation module in your own scripts:

```python
from src.evaluation import (
    parse_tsv_ground_truth,
    calculate_metrics,
    print_metrics_report
)
from src.app import extract_drug_symptom_relations

# Load ground truth
ground_truth = parse_tsv_ground_truth('data/test.tsv')

# Get predictions
predictions = extract_drug_symptom_relations(text, use_ai=True)

# Calculate metrics
metrics = calculate_metrics(predictions, ground_truth)

# Print report
print_metrics_report(metrics)
```

### Batch Evaluation

Evaluate on multiple test sets:

```bash
for test_file in data/test*.tsv; do
    echo "Evaluating $test_file"
    python scripts/evaluate_model.py \
        --test_file "$test_file" \
        --output "results_$(basename $test_file .tsv).json"
done
```

## References

Standard evaluation metrics follow:
- Scikit-learn documentation: https://scikit-learn.org/stable/modules/model_evaluation.html
- Wikipedia: https://en.wikipedia.org/wiki/Precision_and_recall

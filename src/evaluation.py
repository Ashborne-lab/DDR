"""
Evaluation Metrics Module for Drug-Disease Relation Extraction

This module provides comprehensive evaluation metrics for research paper analysis:
- Accuracy, Precision, Recall, F1-Score
- Per-class metrics (Adverse, Treatment, None)
- Macro and Micro averages
- Confusion matrix generation
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Set
import re
from collections import defaultdict
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    classification_report, confusion_matrix
)


def clean_annotated_text(text: str) -> str:
    """Remove annotation markers from text for processing."""
    # Remove @EntityType$ ... @/EntityType$ patterns
    text = re.sub(r'@[^$]+\$\s*', '', text)
    text = re.sub(r'\s*@/[^$]+\$', '', text)
    return text.strip()


def parse_tsv_ground_truth(filepath: str) -> List[Dict]:
    """
    Parse TSV test files to extract ground truth drug-disease relationships.
    
    Args:
        filepath: Path to TSV file (test.tsv or dev.tsv)
        
    Returns:
        List of dictionaries with ground truth relations:
        [{
            'text': sentence (with annotations removed),
            'text_original': original sentence (with annotations),
            'drug': drug_name,
            'disease': disease_name,
            'relation': 'adverse'/'treatment'/'none'
        }]
    """
    ground_truth = []
    
    try:
        df = pd.read_csv(filepath, sep='\t', header=None, on_bad_lines='skip', engine='python')
        
        # Pattern to extract drug and disease entities
        chemical_pattern = re.compile(
            r'@(Chemical|Drug|ChemicalEntity)Src\$\s*(.*?)\s*@/(Chemical|Drug|ChemicalEntity)Src\$',
            re.IGNORECASE
        )
        disease_pattern = re.compile(
            r'@DiseaseOrPhenotypicFeatureTgt\$\s*(.*?)\s*@/DiseaseOrPhenotypicFeatureTgt\$',
            re.IGNORECASE
        )
        
        for row in df.itertuples(index=False, name=None):
            if len(row) < 8:
                continue
                
            text_content = str(row[7])
            
            # Extract drug and disease entities from annotated text
            chemical_matches = chemical_pattern.finditer(text_content)
            disease_matches = disease_pattern.finditer(text_content)
            
            chemicals = [m.group(2).strip().lower() for m in chemical_matches]
            diseases = [m.group(1).strip().lower() for m in disease_matches]
            
            # Get relation type (last column)
            relation_col = str(row[-1]).strip().lower() if len(row) > 7 else 'none'
            
            # Map relation types
            if 'positive' in relation_col:
                relation = 'adverse'  # Positive correlation often means adverse effect
            elif 'negative' in relation_col:
                relation = 'treatment'  # Negative correlation often means treatment
            elif 'association' in relation_col or 'associated' in relation_col:
                relation = 'treatment'  # Association often means treatment
            else:
                relation = 'none'
            
            # Only include if we have both drug and disease
            if chemicals and diseases:
                # Clean text (remove annotations for processing)
                clean_text = clean_annotated_text(text_content)
                
                # Create pairs
                for chemical in chemicals:
                    for disease in diseases:
                        if len(chemical) > 2 and len(disease) > 2:
                            ground_truth.append({
                                'text': clean_text,  # Use cleaned text for extraction
                                'text_original': text_content,  # Keep original for reference
                                'drug': chemical,
                                'disease': disease,
                                'relation': relation
                            })
                        
    except Exception as e:
        print(f"Error parsing {filepath}: {e}")
        import traceback
        traceback.print_exc()
        
    return ground_truth


def normalize_entity_name(name: str) -> str:
    """Normalize entity names for matching."""
    # Remove extra whitespace, lowercase, remove special chars at edges
    name = name.lower().strip()
    # Remove common prefixes/suffixes
    name = re.sub(r'\b(tablet|capsule|syrup|injection|drops|gel|ointment|cream|powder|mg|ml|g|mcg)\b', '', name)
    name = re.sub(r'[^\w\s]', '', name).strip()
    return name


def match_prediction_to_ground_truth(
    pred_drug: str,
    pred_disease: str,
    pred_relation: str,
    ground_truth_list: List[Dict],
    text_match: bool = False
) -> Tuple[bool, str]:
    """
    Match a prediction to ground truth.
    
    Args:
        pred_drug: Predicted drug name
        pred_disease: Predicted disease/symptom name
        pred_relation: Predicted relation type ('adverse', 'treatment', 'associated')
        ground_truth_list: List of ground truth relations
        text_match: If True, also match based on text context
        
    Returns:
        Tuple of (is_correct, matched_gt_relation)
    """
    norm_pred_drug = normalize_entity_name(pred_drug)
    norm_pred_disease = normalize_entity_name(pred_disease)
    
    # Normalize prediction relation
    pred_relation_norm = pred_relation.lower()
    if pred_relation_norm in ['adverse', 'side effect', 'adverse effect']:
        pred_relation_norm = 'adverse'
    elif pred_relation_norm in ['treatment', 'associated', 'treats']:
        pred_relation_norm = 'treatment'
    else:
        pred_relation_norm = 'none'
    
    # Try to find match
    for gt in ground_truth_list:
        norm_gt_drug = normalize_entity_name(gt['drug'])
        norm_gt_disease = normalize_entity_name(gt['disease'])
        
        # Fuzzy matching for entity names
        drug_match = (
            norm_pred_drug in norm_gt_drug or 
            norm_gt_drug in norm_pred_drug or
            norm_pred_drug == norm_gt_drug
        )
        disease_match = (
            norm_pred_disease in norm_gt_disease or 
            norm_gt_disease in norm_pred_disease or
            norm_pred_disease == norm_gt_disease
        )
        
        if drug_match and disease_match:
            gt_relation = gt['relation'].lower()
            
            # Check relation type match
            if pred_relation_norm == gt_relation:
                return True, gt_relation
            elif gt_relation != 'none':
                # Entity match but wrong relation type
                return False, gt_relation
    
    # No match found - could be false positive or true negative
    return False, 'none'


def calculate_metrics(
    predictions: List[Dict],
    ground_truth: List[Dict],
    relation_types: List[str] = ['adverse', 'treatment', 'none']
) -> Dict:
    """
    Calculate comprehensive evaluation metrics.
    
    Args:
        predictions: List of prediction dicts with 'drug', 'effect', 'relationship' keys
        ground_truth: List of ground truth dicts from parse_tsv_ground_truth
        relation_types: List of relation types to evaluate
        
    Returns:
        Dictionary with all metrics
    """
    # Build ground truth set for fast lookup
    gt_dict = defaultdict(list)
    for gt in ground_truth:
        key = (normalize_entity_name(gt['drug']), normalize_entity_name(gt['disease']))
        gt_dict[key].append(gt)
    
    # Initialize counters
    true_positives = defaultdict(int)
    false_positives = defaultdict(int)
    false_negatives = defaultdict(int)
    true_negatives = defaultdict(int)
    
    all_pred_labels = []
    all_true_labels = []
    
    # Process predictions
    matched_predictions = set()
    
    for pred in predictions:
        pred_drug = pred.get('drug', '').lower()
        pred_effect = pred.get('effect', '').lower()
        pred_relation = pred.get('relationship', 'none').lower()
        
        # Normalize prediction relation
        if pred_relation in ['adverse', 'side effect']:
            pred_relation = 'adverse'
        elif pred_relation in ['treatment', 'associated', 'treats']:
            pred_relation = 'treatment'
        else:
            pred_relation = 'none'
        
        # Try to match with ground truth
        matched = False
        for gt in ground_truth:
            is_correct, gt_relation = match_prediction_to_ground_truth(
                pred_drug, pred_effect, pred_relation, [gt]
            )
            
            if is_correct:
                true_positives[pred_relation] += 1
                all_pred_labels.append(pred_relation)
                all_true_labels.append(gt_relation)
                matched_predictions.add((pred_drug, pred_effect))
                matched = True
                break
            elif matched_prediction_to_ground_truth(pred_drug, pred_effect, pred_relation, [gt])[1] != 'none':
                # Entity match but wrong relation
                false_positives[pred_relation] += 1
                false_negatives[gt_relation] += 1
                all_pred_labels.append(pred_relation)
                all_true_labels.append(gt_relation)
                matched = True
                break
        
        if not matched:
            # False positive
            false_positives[pred_relation] += 1
            all_pred_labels.append(pred_relation)
            all_true_labels.append('none')
    
    # Process unmatched ground truth (false negatives)
    matched_gt = set()
    for gt in ground_truth:
        gt_drug = normalize_entity_name(gt['drug'])
        gt_disease = normalize_entity_name(gt['disease'])
        key = (gt_drug, gt_disease)
        
        found = False
        for pred in predictions:
            pred_drug = normalize_entity_name(pred.get('drug', ''))
            pred_effect = normalize_entity_name(pred.get('effect', ''))
            
            if (gt_drug in pred_drug or pred_drug in gt_drug) and \
               (gt_disease in pred_effect or pred_effect in gt_disease):
                found = True
                break
        
        if not found and gt['relation'] != 'none':
            false_negatives[gt['relation']] += 1
    
    # Calculate per-class metrics
    metrics = {
        'overall': {},
        'per_class': {},
        'macro_avg': {},
        'micro_avg': {}
    }
    
    # Per-class metrics
    for rel_type in relation_types:
        tp = true_positives.get(rel_type, 0)
        fp = false_positives.get(rel_type, 0)
        fn = false_negatives.get(rel_type, 0)
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        
        metrics['per_class'][rel_type] = {
            'precision': round(precision, 4),
            'recall': round(recall, 4),
            'f1_score': round(f1, 4),
            'support': tp + fn,
            'true_positives': tp,
            'false_positives': fp,
            'false_negatives': fn
        }
    
    # Overall accuracy
    total_tp = sum(true_positives.values())
    total_fp = sum(false_positives.values())
    total_fn = sum(false_negatives.values())
    total = total_tp + total_fp + total_fn
    
    accuracy = total_tp / total if total > 0 else 0.0
    overall_precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
    overall_recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0.0
    overall_f1 = 2 * (overall_precision * overall_recall) / (overall_precision + overall_recall) \
                 if (overall_precision + overall_recall) > 0 else 0.0
    
    metrics['overall'] = {
        'accuracy': round(accuracy, 4),
        'precision': round(overall_precision, 4),
        'recall': round(overall_recall, 4),
        'f1_score': round(overall_f1, 4),
        'total_predictions': len(predictions),
        'total_ground_truth': len(ground_truth),
        'true_positives': total_tp,
        'false_positives': total_fp,
        'false_negatives': total_fn
    }
    
    # Macro averages (average of per-class metrics)
    precisions = [m['precision'] for m in metrics['per_class'].values()]
    recalls = [m['recall'] for m in metrics['per_class'].values()]
    f1_scores = [m['f1_score'] for m in metrics['per_class'].values()]
    
    metrics['macro_avg'] = {
        'precision': round(np.mean(precisions), 4),
        'recall': round(np.mean(recalls), 4),
        'f1_score': round(np.mean(f1_scores), 4)
    }
    
    # Micro averages (calculated from total counts)
    metrics['micro_avg'] = {
        'precision': round(overall_precision, 4),
        'recall': round(overall_recall, 4),
        'f1_score': round(overall_f1, 4)
    }
    
    return metrics


def print_metrics_report(metrics: Dict, title: str = "Evaluation Results"):
    """Print a formatted metrics report."""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)
    
    print("\nOVERALL METRICS:")
    print("-" * 70)
    overall = metrics['overall']
    print(f"  Accuracy:     {overall['accuracy']:.4f} ({overall['accuracy']*100:.2f}%)")
    print(f"  Precision:    {overall['precision']:.4f}")
    print(f"  Recall:       {overall['recall']:.4f}")
    print(f"  F1-Score:     {overall['f1_score']:.4f}")
    print(f"  TP: {overall['true_positives']} | FP: {overall['false_positives']} | FN: {overall['false_negatives']}")
    
    print("\nPER-CLASS METRICS:")
    print("-" * 70)
    for rel_type, cls_metrics in metrics['per_class'].items():
        print(f"\n  {rel_type.upper()}:")
        print(f"    Precision:  {cls_metrics['precision']:.4f}")
        print(f"    Recall:     {cls_metrics['recall']:.4f}")
        print(f"    F1-Score:   {cls_metrics['f1_score']:.4f}")
        print(f"    Support:    {cls_metrics['support']}")
        print(f"    TP: {cls_metrics['true_positives']} | FP: {cls_metrics['false_positives']} | FN: {cls_metrics['false_negatives']}")
    
    print("\nAVERAGE METRICS:")
    print("-" * 70)
    print("  Macro Average:")
    macro = metrics['macro_avg']
    print(f"    Precision:  {macro['precision']:.4f}")
    print(f"    Recall:     {macro['recall']:.4f}")
    print(f"    F1-Score:   {macro['f1_score']:.4f}")
    
    print("\n  Micro Average:")
    micro = metrics['micro_avg']
    print(f"    Precision:  {micro['precision']:.4f}")
    print(f"    Recall:     {micro['recall']:.4f}")
    print(f"    F1-Score:   {micro['f1_score']:.4f}")
    
    print("\n" + "="*70 + "\n")


def evaluate_on_test_set(
    test_file: str,
    extract_function,
    extract_kwargs: Dict = None,
    max_samples: int = None,
    verbose: bool = False
) -> Dict:
    """
    Evaluate extraction function on test set.
    
    Args:
        test_file: Path to test TSV file
        extract_function: Function that takes text and returns list of relation dicts
        extract_kwargs: Additional kwargs to pass to extract_function
        max_samples: Maximum number of test samples to process (None for all)
        verbose: Print detailed progress information
        
    Returns:
        Metrics dictionary
    """
    print(f"Loading ground truth from {test_file}...")
    ground_truth = parse_tsv_ground_truth(test_file)
    
    if max_samples:
        ground_truth = ground_truth[:max_samples]
        print(f"  (Limited to {max_samples} samples)")
    
    print(f"Found {len(ground_truth)} ground truth relations")
    
    # Extract unique texts (use cleaned text for processing)
    unique_texts = {}
    text_to_gt = {}  # Map text to ground truth entries
    for gt in ground_truth:
        text_key = gt['text'][:200]  # Use first 200 chars as key
        if text_key not in unique_texts:
            unique_texts[text_key] = gt['text']
            text_to_gt[text_key] = []
        text_to_gt[text_key].append(gt)
    
    print(f"Processing {len(unique_texts)} unique texts...")
    
    # Get predictions
    predictions = []
    extract_kwargs = extract_kwargs or {}
    
    # Pre-load database once if possible (to avoid reloading)
    # Note: This depends on the extract_function implementation
    
    for i, (text_key, text) in enumerate(unique_texts.items()):
        if (i + 1) % 50 == 0 or verbose:
            print(f"  Processed {i + 1}/{len(unique_texts)} texts... (found {len(predictions)} relations so far)")
        
        try:
            preds = extract_function(text, **extract_kwargs)
            predictions.extend(preds)
            
            if verbose and preds:
                print(f"    Text {i+1}: Found {len(preds)} relations")
                if len(preds) > 0:
                    print(f"      Example: {preds[0].get('drug', 'N/A')} -> {preds[0].get('effect', 'N/A')}")
        except Exception as e:
            if verbose:
                print(f"  Error processing text {i+1}: {e}")
            continue
    
    print(f"\nGenerated {len(predictions)} predictions from {len(unique_texts)} texts")
    
    # Calculate metrics
    print("Calculating metrics...")
    metrics = calculate_metrics(predictions, ground_truth)
    
    return metrics

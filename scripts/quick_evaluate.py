"""
Quick Evaluation Script - Simple usage example

This is a simplified version for quick testing.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.evaluation import parse_tsv_ground_truth, calculate_metrics, print_metrics_report
from src.app import extract_drug_symptom_relations

def main():
    print("🔬 Quick Evaluation Test")
    print("=" * 60)
    
    # Use dev.tsv for quick test (smaller than test.tsv)
    test_file = "data/dev.tsv"
    
    print(f"Loading ground truth from {test_file}...")
    ground_truth = parse_tsv_ground_truth(test_file)
    print(f"✓ Found {len(ground_truth)} ground truth relations")
    
    # Limit to first 50 for quick test
    print("\nProcessing first 50 samples...")
    sample_gt = ground_truth[:50]
    
    # Get unique texts
    unique_texts = {}
    for gt in sample_gt:
        text_key = gt['text'][:200]
        if text_key not in unique_texts:
            unique_texts[text_key] = gt['text']
    
    print(f"✓ Processing {len(unique_texts)} unique texts...")
    
    # Extract predictions
    predictions = []
    for i, text in enumerate(unique_texts.values()):
        if (i + 1) % 10 == 0:
            print(f"  Progress: {i + 1}/{len(unique_texts)}")
        
        try:
            preds = extract_drug_symptom_relations(text, use_ai=False)
            predictions.extend(preds)
        except Exception as e:
            print(f"  Error: {e}")
            continue
    
    print(f"\n✓ Generated {len(predictions)} predictions")
    
    # Calculate metrics
    print("\nCalculating metrics...")
    metrics = calculate_metrics(predictions, sample_gt)
    
    # Print report
    print_metrics_report(metrics, "Quick Evaluation Results (50 samples)")
    
    print("\n✅ Evaluation complete!")
    print("\nTip: Use 'python scripts/evaluate_model.py' for full evaluation")

if __name__ == '__main__':
    main()

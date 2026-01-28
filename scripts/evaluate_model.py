"""
Evaluation Script for Drug-Disease Relation Extraction

This script evaluates the drug-disease relation extraction system on test data
and generates comprehensive metrics for research paper reporting.

Usage:
    python scripts/evaluate_model.py --test_file data/test.tsv --output results.json
    python scripts/evaluate_model.py --test_file data/dev.tsv --max_samples 500
"""

import sys
import os
import argparse
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.evaluation import (
    evaluate_on_test_set,
    print_metrics_report,
    calculate_metrics,
    parse_tsv_ground_truth
)
from src.app import extract_drug_symptom_relations


def main():
    parser = argparse.ArgumentParser(
        description='Evaluate Drug-Disease Relation Extraction Model',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Evaluate on test set
  python scripts/evaluate_model.py --test_file data/test.tsv
  
  # Evaluate with AI models enabled
  python scripts/evaluate_model.py --test_file data/test.tsv --use_ai
  
  # Evaluate on subset of data
  python scripts/evaluate_model.py --test_file data/dev.tsv --max_samples 1000
  
  # Save results to JSON
  python scripts/evaluate_model.py --test_file data/test.tsv --output results.json
        """
    )
    
    parser.add_argument(
        '--test_file',
        type=str,
        default='data/test.tsv',
        help='Path to test TSV file (default: data/test.tsv)'
    )
    
    parser.add_argument(
        '--use_ai',
        action='store_true',
        help='Use BioBERT AI models for extraction (default: False)'
    )
    
    parser.add_argument(
        '--max_samples',
        type=int,
        default=None,
        help='Maximum number of samples to evaluate (default: all)'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Output JSON file path to save results (default: print only)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Print detailed progress information'
    )
    
    args = parser.parse_args()
    
    # Check if test file exists
    if not os.path.exists(args.test_file):
        print(f"ERROR: Test file not found: {args.test_file}")
        print(f"   Current directory: {os.getcwd()}")
        sys.exit(1)
    
    print("Drug-Disease Relation Extraction Evaluation")
    print("="*70)
    print(f"Test file:    {args.test_file}")
    print(f"Use AI:       {args.use_ai}")
    print(f"Max samples:  {args.max_samples or 'All'}")
    print("="*70)
    
    # Create extraction function wrapper
    def extract_function(text, use_ai=False):
        """Wrapper for extraction function."""
        return extract_drug_symptom_relations(text, use_ai=use_ai)
    
    try:
        # Run evaluation
        metrics = evaluate_on_test_set(
            test_file=args.test_file,
            extract_function=extract_function,
            extract_kwargs={'use_ai': args.use_ai},
            max_samples=args.max_samples,
            verbose=args.verbose
        )
        
        # Print report
        title = "Drug-Disease Relation Extraction Evaluation Results"
        if args.use_ai:
            title += " (with BioBERT AI)"
        
        print_metrics_report(metrics, title=title)
        
        # Save to file if requested
        if args.output:
            # Convert numpy types to native Python types for JSON serialization
            def convert_types(obj):
                if isinstance(obj, dict):
                    return {k: convert_types(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_types(item) for item in obj]
                elif isinstance(obj, (np.integer, np.floating)):
                    return float(obj)
                elif isinstance(obj, np.ndarray):
                    return obj.tolist()
                return obj
            
            output_data = {
                'test_file': args.test_file,
                'use_ai': args.use_ai,
                'max_samples': args.max_samples,
                'metrics': convert_types(metrics)
            }
            
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            
            print(f"Results saved to: {args.output}")
        
        # Print summary for research paper
        print("\nMETRICS SUMMARY FOR RESEARCH PAPER:")
        print("-" * 70)
        overall = metrics['overall']
        macro = metrics['macro_avg']
        
        print(f"\\textbf{{Accuracy}}: {overall['accuracy']:.4f} ({overall['accuracy']*100:.2f}\\%)")
        print(f"\\textbf{{Precision}}: {overall['precision']:.4f}")
        print(f"\\textbf{{Recall}}: {overall['recall']:.4f}")
        print(f"\\textbf{{F1-Score}}: {overall['f1_score']:.4f}")
        print(f"\\textbf{{Macro F1}}: {macro['f1_score']:.4f}")
        
        print("\nPer-class Performance:")
        for rel_type, cls_metrics in metrics['per_class'].items():
            print(f"  {rel_type.capitalize()}: P={cls_metrics['precision']:.4f}, "
                  f"R={cls_metrics['recall']:.4f}, F1={cls_metrics['f1_score']:.4f}")
        
        print("\n" + "="*70)
        
    except KeyboardInterrupt:
        print("\n\nWARNING: Evaluation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR: Error during evaluation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    import numpy as np  # Needed for convert_types function
    main()

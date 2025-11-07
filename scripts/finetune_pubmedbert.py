#!/usr/bin/env python3
"""
Fine-tune microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract-fulltext
for text classification using Hugging Face Trainer API.

Usage example:
python scripts/finetune_pubmedbert.py \
  --train_file data/train.csv \
  --validation_file data/valid.csv \
  --text_column text --label_column label \
  --output_dir outputs/pubmedbert-finetuned \
  --epochs 3 --per_device_batch_size 8

The script will automatically use GPU if available.
"""
import argparse
import logging
import os
from typing import Dict, List

import numpy as np
import torch
from datasets import load_dataset, DatasetDict
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    DataCollatorWithPadding,
    Trainer,
    TrainingArguments,
)


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def parse_args():
    parser = argparse.ArgumentParser(description="Fine-tune PubMedBERT for text classification")
    parser.add_argument("--train_file", type=str, required=True, help="Path to training CSV/TSV file")
    parser.add_argument("--validation_file", type=str, required=False, help="Path to validation CSV/TSV file")
    parser.add_argument("--text_column", type=str, default="text", help="Name of the text column")
    parser.add_argument("--label_column", type=str, default="label", help="Name of the label column")
    parser.add_argument("--model_name_or_path", type=str, default="microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract-fulltext")
    parser.add_argument("--output_dir", type=str, default="outputs/pubmedbert-finetuned")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--per_device_batch_size", type=int, default=8)
    parser.add_argument("--lr", type=float, default=2e-5)
    parser.add_argument("--max_length", type=int, default=256)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--overwrite_output_dir", action="store_true")
    return parser.parse_args()


def compute_metrics(pred):
    labels = pred.label_ids
    preds = np.argmax(pred.predictions, axis=1)
    precision, recall, f1, _ = precision_recall_fscore_support(labels, preds, average="weighted", zero_division=0)
    acc = accuracy_score(labels, preds)
    return {"accuracy": acc, "f1": f1, "precision": precision, "recall": recall}


def main():
    args = parse_args()

    # Ensure output dir
    os.makedirs(args.output_dir, exist_ok=True)

    # Detect device
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"Using device: {device}")

    # Load datasets (auto-detect csv/tsv)
    data_files = {"train": args.train_file}
    if args.validation_file:
        data_files["validation"] = args.validation_file

    # Infer file format
    file_extension = os.path.splitext(args.train_file)[1].lower()
    if file_extension == ".csv":
        dataset = load_dataset("csv", data_files=data_files)
    else:
        # default to csv loader but allow TSV via delimiter
        dataset = load_dataset("csv", data_files=data_files, delimiter="\t")

    # If validation not provided, split train
    if "validation" not in dataset:
        dataset = dataset["train"].train_test_split(test_size=0.1, seed=args.seed)
        dataset = DatasetDict({"train": dataset["train"], "validation": dataset["test"]})

    # Normalize column names
    text_col = args.text_column
    label_col = args.label_column

    # Build label list
    labels = sorted(list(set(dataset["train"][label_col])))
    label2id = {l: i for i, l in enumerate(labels)}
    id2label = {i: l for l, i in label2id.items()}
    num_labels = len(labels)
    logger.info(f"Detected labels ({num_labels}): {labels}")

    # Load tokenizer and model
    tokenizer = AutoTokenizer.from_pretrained(args.model_name_or_path, use_fast=True)
    model = AutoModelForSequenceClassification.from_pretrained(
        args.model_name_or_path,
        num_labels=num_labels,
        id2label=id2label,
        label2id=label2id,
    )

    # Preprocessing: tokenize and map labels in one pass. We remove original
    # text/label columns and keep tokenized features + 'labels'.
    def preprocess_fn(examples):
        texts = examples[text_col]
        tokenized_batch = tokenizer(texts, truncation=True, padding=False, max_length=args.max_length)
        # Map labels to ids
        tokenized_batch["labels"] = [label2id[l] for l in examples[label_col]]
        return tokenized_batch

    tokenized = dataset.map(preprocess_fn, batched=True, remove_columns=dataset["train"].column_names)

    # Data collator
    data_collator = DataCollatorWithPadding(tokenizer=tokenizer)

    # Training args - try to use newer Trainer args; if transformers is old,
    # fall back to a minimal compatible set.
    try:
        training_args = TrainingArguments(
            output_dir=args.output_dir,
            evaluation_strategy="epoch",
            save_strategy="epoch",
            learning_rate=args.lr,
            per_device_train_batch_size=args.per_device_batch_size,
            per_device_eval_batch_size=args.per_device_batch_size,
            num_train_epochs=args.epochs,
            weight_decay=0.01,
            fp16=torch.cuda.is_available(),
            logging_dir=os.path.join(args.output_dir, "logs"),
            logging_steps=50,
            load_best_model_at_end=True,
            metric_for_best_model="f1",
            greater_is_better=True,
            seed=args.seed,
            remove_unused_columns=False,
            push_to_hub=False,
            overwrite_output_dir=args.overwrite_output_dir,
        )
    except TypeError:
        # Older transformers versions may not accept some kwargs; use a
        # minimal compatible TrainingArguments constructor.
        training_args = TrainingArguments(
            output_dir=args.output_dir,
            learning_rate=args.lr,
            per_device_train_batch_size=args.per_device_batch_size,
            num_train_epochs=args.epochs,
            weight_decay=0.01,
            fp16=torch.cuda.is_available(),
            logging_dir=os.path.join(args.output_dir, "logs"),
            logging_steps=50,
            seed=args.seed,
            remove_unused_columns=False,
            overwrite_output_dir=args.overwrite_output_dir,
        )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized["train"],
        eval_dataset=tokenized["validation"],
        tokenizer=tokenizer,
        data_collator=data_collator,
        compute_metrics=compute_metrics,
    )

    # Train
    trainer.train()

    # Evaluate
    eval_results = trainer.evaluate()
    logger.info(f"Evaluation results: {eval_results}")

    # Save final model and tokenizer
    trainer.save_model(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)


if __name__ == "__main__":
    main()

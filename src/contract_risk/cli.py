"""Command-line entrypoints for training and evaluation."""

from __future__ import annotations

import argparse
from pathlib import Path

from sklearn.model_selection import train_test_split

from contract_risk.config import ProjectConfig, resolve_training_csv
from contract_risk.data.loader import load_training_dataframe
from contract_risk.models.comparison import compare_baseline_models
from contract_risk.models.evaluation import evaluate_classifier
from contract_risk.models.pipeline import load_model, save_model, train_logreg_model


def _safe_split(
    texts: list[str],
    labels: list[str],
    test_size: float,
) -> tuple[list[str], list[str], list[str], list[str]]:
    """Split dataset while handling low-frequency labels."""
    label_counts: dict[str, int] = {}
    for label in labels:
        label_counts[label] = label_counts.get(label, 0) + 1

    stratify_labels = labels if all(count >= 2 for count in label_counts.values()) else None

    x_train, x_test, y_train, y_test = train_test_split(
        texts,
        labels,
        test_size=test_size,
        random_state=42,
        stratify=stratify_labels,
    )
    return x_train, x_test, y_train, y_test


def run_train(args: argparse.Namespace) -> None:
    """Train and save the baseline logistic regression model."""
    config = ProjectConfig()
    csv_path = resolve_training_csv(args.csv, config)
    dataset = load_training_dataframe(csv_path)

    model = train_logreg_model(dataset["text"].tolist(), dataset["label"].tolist())
    destination = save_model(model, Path(args.model_out) if args.model_out else config.model_path)

    print(f"Model trained on {len(dataset)} rows and saved to: {destination}")


def run_eval(args: argparse.Namespace) -> None:
    """Evaluate the trained model and compare baseline models."""
    config = ProjectConfig()
    csv_path = resolve_training_csv(args.csv, config)
    dataset = load_training_dataframe(csv_path)

    texts = dataset["text"].tolist()
    labels = dataset["label"].tolist()
    x_train, x_test, y_train, y_test = _safe_split(texts, labels, test_size=args.test_size)

    model_path = Path(args.model_path) if args.model_path else config.model_path
    model = load_model(model_path)

    metrics = evaluate_classifier(
        model=model,
        texts=x_test,
        labels=y_test,
        output_dir=args.reports_dir,
        prefix="logreg",
    )
    comparison_df = compare_baseline_models(
        train_texts=x_train,
        train_labels=y_train,
        test_texts=x_test,
        test_labels=y_test,
        output_dir=args.reports_dir,
    )

    print("Evaluation complete.")
    print(f"Weighted precision: {metrics['precision_weighted']:.4f}")
    print(f"Weighted recall: {metrics['recall_weighted']:.4f}")
    print(f"Weighted F1: {metrics['f1_weighted']:.4f}")
    print("Model comparison table:")
    print(comparison_df.to_string(index=False))


def build_parser() -> argparse.ArgumentParser:
    """Build CLI parser for project commands."""
    parser = argparse.ArgumentParser(description="Contract risk model tooling")
    subparsers = parser.add_subparsers(dest="command", required=True)

    train_parser = subparsers.add_parser("train", help="Train baseline model")
    train_parser.add_argument("--csv", type=str, default=None, help="Path to training CSV")
    train_parser.add_argument("--model-out", type=str, default=None, help="Model output path")
    train_parser.set_defaults(func=run_train)

    eval_parser = subparsers.add_parser("eval", help="Evaluate trained model")
    eval_parser.add_argument("--csv", type=str, default=None, help="Path to evaluation CSV")
    eval_parser.add_argument("--model-path", type=str, default=None, help="Path to model file")
    eval_parser.add_argument("--reports-dir", type=str, default="reports", help="Report output dir")
    eval_parser.add_argument("--test-size", type=float, default=0.2, help="Test split ratio")
    eval_parser.set_defaults(func=run_eval)

    return parser


def main() -> None:
    """CLI program entrypoint."""
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

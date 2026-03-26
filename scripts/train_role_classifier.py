#!/usr/bin/env python3
"""
Train the role type classifier from the jobs database.

Strategy:
  1. Pull all (id, title) pairs from jobs table
  2. Bootstrap labels using heuristic keyword matching
  3. Keep only high-confidence hits (>= --min-confidence)
  4. Add synthetic titles for under-represented classes (DESIGN, SALES)
  5. Train TF-IDF + LogisticRegression pipeline
  6. Evaluate on held-out test split
  7. Save model to models/role_classifier.joblib

Usage:
    python scripts/train_role_classifier.py
    python scripts/train_role_classifier.py --db data/job_tracker.db --test-split 0.2
"""

import sys
import json
import sqlite3
import argparse
import logging
from pathlib import Path
from collections import Counter
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent.parent / "data" / "job_tracker.db"
MODEL_DIR = Path(__file__).parent.parent / "models"
MODEL_PATH = MODEL_DIR / "role_classifier.joblib"
METADATA_PATH = MODEL_DIR / "role_classifier_metadata.json"

# ── Synthetic title augmentation ────────────────────────────────────────
# Extra labeled examples to compensate for rare classes in most job DBs.
SYNTHETIC_TITLES: list = [
    # ENGINEERING_IC
    ("Staff Software Engineer", "ENGINEERING_IC"),
    ("Senior Backend Engineer - Python", "ENGINEERING_IC"),
    ("Data Engineer III", "ENGINEERING_IC"),
    ("Principal Data Engineer", "ENGINEERING_IC"),
    ("ML Platform Engineer", "ENGINEERING_IC"),
    ("Cloud Infrastructure Engineer", "ENGINEERING_IC"),
    ("Senior Python Developer", "ENGINEERING_IC"),
    ("Data Engineering Lead", "ENGINEERING_IC"),
    ("Senior SRE", "ENGINEERING_IC"),
    ("Platform Engineer - Kubernetes", "ENGINEERING_IC"),
    ("Senior Analytics Engineer", "ENGINEERING_IC"),
    ("ETL Developer Senior", "ENGINEERING_IC"),
    ("AI / ML Engineer", "ENGINEERING_IC"),
    ("Senior Data Platform Engineer", "ENGINEERING_IC"),
    ("Fullstack Engineer - React / Python", "ENGINEERING_IC"),
    # SALES
    ("Account Executive - Enterprise", "SALES"),
    ("SDR - Outbound Sales", "SALES"),
    ("Business Development Representative", "SALES"),
    ("Sales Development Representative", "SALES"),
    ("Customer Success Manager - Enterprise", "SALES"),
    ("Senior Account Executive", "SALES"),
    ("Sr. Solutions Engineer (Pre-Sales)", "SALES"),
    ("Enterprise Sales Manager", "SALES"),
    ("Strategic Account Executive", "SALES"),
    ("Inside Sales Representative", "SALES"),
    ("Sales Engineer - Data Analytics", "SALES"),
    ("Growth Manager - PLG", "SALES"),
    ("Revenue Operations Manager", "SALES"),
    ("Partnerships Manager", "SALES"),
    ("Commercial Account Executive", "SALES"),
    # MANAGEMENT
    ("Engineering Manager - Data Platform", "MANAGEMENT"),
    ("Director of Engineering", "MANAGEMENT"),
    ("VP of Engineering", "MANAGEMENT"),
    ("Head of Data Engineering", "MANAGEMENT"),
    ("Senior Engineering Manager", "MANAGEMENT"),
    ("CTO", "MANAGEMENT"),
    ("Director, Platform Engineering", "MANAGEMENT"),
    ("Engineering Lead (Manager)", "MANAGEMENT"),
    ("VP Engineering - Growth", "MANAGEMENT"),
    ("Head of Software Engineering", "MANAGEMENT"),
    # DESIGN
    ("Senior UX Designer", "DESIGN"),
    ("Product Designer - Mobile", "DESIGN"),
    ("UX Researcher", "DESIGN"),
    ("Visual Designer", "DESIGN"),
    ("Senior Product Designer", "DESIGN"),
    ("Design Lead", "DESIGN"),
    ("UI / UX Designer", "DESIGN"),
    ("Interaction Designer", "DESIGN"),
    # OPERATIONS
    ("Product Manager - Data", "OPERATIONS"),
    ("Senior Product Manager", "OPERATIONS"),
    ("Technical Program Manager", "OPERATIONS"),
    ("Business Analyst - Finance", "OPERATIONS"),
    ("Data Analyst - Growth", "OPERATIONS"),
    ("Project Manager - Agile", "OPERATIONS"),
    ("Operations Manager - Revenue", "OPERATIONS"),
    ("HR Business Partner", "OPERATIONS"),
    ("Recruiter - Technical", "OPERATIONS"),
    ("Financial Analyst II", "OPERATIONS"),
    # Mobile/wrong-discipline IC roles
    ("Mobile Engineer", "OPERATIONS"),
    ("Senior Mobile Engineer", "OPERATIONS"),
    ("Mobile Architect", "OPERATIONS"),
    ("iOS Developer", "OPERATIONS"),
    ("Senior iOS Developer", "OPERATIONS"),
    ("Android Developer", "OPERATIONS"),
    ("Senior Android Developer", "OPERATIONS"),
    ("Mobile DevOps Engineer", "OPERATIONS"),
    ("Mobile Platform Engineer", "OPERATIONS"),
    ("React Native Developer", "OPERATIONS"),
    ("Flutter Developer", "OPERATIONS"),
]


def pull_titles_from_db(db_path: Path) -> list:
    """Pull (id, title) pairs from jobs table."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT id, title FROM jobs WHERE title IS NOT NULL AND title != ''")
    rows = [(r[0], r[1].strip()) for r in cur.fetchall() if r[1] and r[1].strip()]
    conn.close()
    logger.info("Pulled %d titles from database", len(rows))
    return rows


def bootstrap_labels(titles: list, min_confidence: float) -> list:
    """
    Assign heuristic labels to job titles.
    Returns list of (title, label) for high-confidence hits only.
    """
    from src.intelligence.role_classifier import RoleClassifier
    clf = RoleClassifier()

    labeled = []
    skipped = 0
    for _, title in titles:
        result = clf._heuristic_predict(title)
        if result.confidence >= min_confidence and result.label != "OTHER":
            labeled.append((title, result.label))
        else:
            skipped += 1

    logger.info(
        "Bootstrapped %d labeled examples (%d skipped below confidence %.2f)",
        len(labeled), skipped, min_confidence,
    )
    return labeled


def build_dataset(db_path: Path, min_confidence: float) -> list:
    """Combine DB-bootstrapped labels with synthetic titles."""
    titles = pull_titles_from_db(db_path)
    db_labeled = bootstrap_labels(titles, min_confidence)
    synthetic = [(t, l) for t, l in SYNTHETIC_TITLES]
    combined = db_labeled + synthetic

    # De-duplicate by (lowercase title, label)
    seen = set()
    deduped = []
    for title, label in combined:
        key = (title.lower().strip(), label)
        if key not in seen:
            seen.add(key)
            deduped.append((title, label))

    label_counts = Counter(l for _, l in deduped)
    logger.info("Dataset class distribution: %s", dict(label_counts))
    return deduped


def train_and_save(
    dataset: list,
    output_path: Path,
    test_split: float,
    metadata_path: Path,
) -> dict:
    """Train, evaluate, and save the sklearn pipeline."""
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression
        from sklearn.pipeline import Pipeline
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import classification_report, accuracy_score
        import joblib
    except ImportError:
        logger.error("scikit-learn not installed. Run: pip install scikit-learn joblib")
        sys.exit(1)

    texts = [t for t, _ in dataset]
    labels = [l for _, l in dataset]

    if len(set(labels)) < 2:
        logger.error("Need at least 2 classes to train. Got: %s", set(labels))
        sys.exit(1)

    x_train, x_test, y_train, y_test = train_test_split(
        texts, labels,
        test_size=test_split,
        random_state=42,
        stratify=labels,
    )

    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(
            analyzer="word",
            ngram_range=(1, 3),
            max_features=20_000,
            sublinear_tf=True,
            strip_accents="unicode",
            lowercase=True,
        )),
        ("clf", LogisticRegression(
            C=1.5,
            max_iter=1_000,
            solver="lbfgs",
            class_weight="balanced",
            random_state=42,
        )),
    ])

    logger.info("Training on %d examples, testing on %d...", len(x_train), len(x_test))
    pipeline.fit(x_train, y_train)

    y_pred = pipeline.predict(x_test)
    accuracy = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred, output_dict=True)

    logger.info("Test accuracy: %.3f", accuracy)
    logger.info("\n%s", classification_report(y_test, y_pred))

    # Save model
    output_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, output_path)
    logger.info("Model saved to %s", output_path)

    # Save metadata
    meta = {
        "trained_at": datetime.utcnow().isoformat(),
        "model_path": str(output_path),
        "training_examples": len(x_train),
        "test_examples": len(x_test),
        "test_accuracy": round(accuracy, 4),
        "labels": list(pipeline.classes_),
        "class_report": report,
        "dataset_distribution": dict(Counter(labels)),
    }
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(json.dumps(meta, indent=2))
    logger.info("Metadata saved to %s", metadata_path)

    return meta


def main():
    parser = argparse.ArgumentParser(description="Train role type classifier")
    parser.add_argument("--db", default=str(DB_PATH), help="Path to job_tracker.db")
    parser.add_argument("--output", default=str(MODEL_PATH), help="Output model path")
    parser.add_argument("--test-split", type=float, default=0.20, help="Test split ratio")
    parser.add_argument("--min-confidence", type=float, default=0.70,
                        help="Min heuristic confidence to include in training set")
    args = parser.parse_args()

    db_path = Path(args.db)
    if not db_path.exists():
        logger.error("Database not found: %s", db_path)
        sys.exit(1)

    dataset = build_dataset(db_path, args.min_confidence)
    if len(dataset) < 50:
        logger.error("Too few training examples (%d). Need at least 50.", len(dataset))
        sys.exit(1)

    metrics = train_and_save(
        dataset,
        output_path=Path(args.output),
        test_split=args.test_split,
        metadata_path=METADATA_PATH,
    )

    print(f"\n{'='*50}")
    print(f"  Training complete")
    print(f"  Test accuracy  : {metrics['test_accuracy']:.1%}")
    print(f"  Training set   : {metrics['training_examples']} examples")
    print(f"  Classes        : {', '.join(metrics['labels'])}")
    print(f"  Model saved to : {metrics['model_path']}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()

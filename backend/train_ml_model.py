#!/usr/bin/env python3
"""
Random Forest Model Training for Risk Assessment
Machine Learning Model yaratish va o'qitish
"""

import asyncio
import json
import pickle
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.models import (
    DiplomaStage,
    DiplomaTopic,
    RiskAssessment,
    StageStatus,
)


# Feature names
FEATURE_NAMES = [
    'progress_gap',          # Expected vs actual progress
    'stage_completion_rate', # Completed stages percentage
    'task_completion_rate',  # Completed tasks percentage
    'meeting_count',         # Number of meetings
    'days_passed',          # Days since topic creation
    'status_encoded',       # Topic status (draft=0, pending=1, approved=2)
    'progress',             # Current progress (0-100)
]

# Risk levels mapping
RISK_LEVELS = {
    'low': 0,
    'medium': 1,
    'high': 2,
    'critical': 3,
}

RISK_LABELS = {v: k for k, v in RISK_LEVELS.items()}


async def generate_training_data(db: AsyncSession):
    """
    Database-dan training data yig'ish
    Features va labels yaratish
    """
    print("📊 Training data yig'ilmoqda...")

    # Barcha topiclarni o'qish
    topics_res = await db.execute(select(DiplomaTopic))
    topics = topics_res.scalars().all()

    X = []  # Features
    y = []  # Risk levels

    now = datetime.now(timezone.utc)

    for topic in topics:
        if not topic.student_id:
            continue

        # Feature 1: Progress gap (expected vs actual)
        created_at = topic.created_at.replace(tzinfo=timezone.utc) if topic.created_at.tzinfo is None else topic.created_at
        defense_date = topic.defense_date.replace(tzinfo=timezone.utc) if topic.defense_date and topic.defense_date.tzinfo is None else topic.defense_date

        if defense_date and created_at:
            total_days = (defense_date - created_at).days
            passed_days = (now - created_at).days
            if total_days > 0:
                expected_progress = min(100.0, (passed_days / total_days) * 100)
                progress_gap = max(0, expected_progress - (topic.progress or 0))
            else:
                progress_gap = 0
        else:
            progress_gap = 0

        # Feature 2-3: Stage va task completion
        stages = topic.stages or []
        if stages:
            approved_stages = sum(1 for s in stages if s.status == StageStatus.APPROVED)
            stage_completion_rate = approved_stages / len(stages)
        else:
            stage_completion_rate = 0

        # Task completion
        tasks = topic.tasks or []
        if tasks:
            done_tasks = sum(1 for t in tasks if t.is_done)
            task_completion_rate = done_tasks / len(tasks)
        else:
            task_completion_rate = 0

        # Feature 4: Meeting count
        meetings = topic.meetings or []
        meeting_count = len(meetings)

        # Feature 5: Days passed
        days_passed = (now - created_at).days if created_at else 0

        # Feature 6: Status encoded
        status_map = {'draft': 0, 'pending': 1, 'approved': 2, 'rejected': -1}
        status_encoded = status_map.get(topic.status.value, 0)

        # Feature 7: Progress
        progress = topic.progress or 0

        # Create feature vector
        features = [
            progress_gap,
            stage_completion_rate,
            task_completion_rate,
            meeting_count,
            days_passed,
            status_encoded,
            progress,
        ]

        # Determine risk level (heuristic for training)
        if progress_gap > 30 and progress < 50:
            risk_level = RISK_LEVELS['critical']
        elif progress_gap > 15 or (days_passed > 90 and progress < 75):
            risk_level = RISK_LEVELS['high']
        elif progress_gap > 5 or stage_completion_rate < 0.25:
            risk_level = RISK_LEVELS['medium']
        else:
            risk_level = RISK_LEVELS['low']

        X.append(features)
        y.append(risk_level)

    return np.array(X), np.array(y)


async def train_model():
    """Random Forest model o'qitish"""
    print("\n🤖 RANDOM FOREST MODEL TRAINING")
    print("=" * 70)

    # Database session
    async with SessionLocal() as db:
        # Training data
        X, y = await generate_training_data(db)

        if len(X) < 5:
            print("❌ Yetarli ma'lumot yo'q (minimal 5 ta topic kerak)")
            print(f"⚠️  Topilgan: {len(X)} ta topic")
            return False

        print(f"✅ {len(X)} ta topic topildi")
        print(f"   Risk distribution:")
        unique, counts = np.unique(y, return_counts=True)
        for risk_id, count in zip(unique, counts):
            print(f"   - {RISK_LABELS[risk_id]}: {count} ta ({count/len(y)*100:.1f}%)")

        # Train-test split
        print("\n📈 Train-test split qilinmoqda (80-20)...")
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, shuffle=True
        )

        # Scaling
        print("🔧 Feature scaling (StandardScaler)...")
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        # Random Forest training
        print("🌲 Random Forest o'qitilmoqda (100 daraxti)...")
        model = RandomForestClassifier(
            n_estimators=100,
            max_depth=15,
            min_samples_split=3,
            min_samples_leaf=1,
            random_state=42,
            n_jobs=-1,
            class_weight='balanced',
        )
        model.fit(X_train_scaled, y_train)

        # Evaluation
        print("\n📊 Model Performance:")
        train_score = model.score(X_train_scaled, y_train)
        test_score = model.score(X_test_scaled, y_test)

        print(f"   Train Accuracy: {train_score:.1%}")
        print(f"   Test Accuracy:  {test_score:.1%}")

        # Feature importance
        print("\n📈 Feature Importance:")
        importances = sorted(zip(FEATURE_NAMES, model.feature_importances_),
                            key=lambda x: x[1], reverse=True)
        for fname, importance in importances:
            bar = "█" * int(importance * 50)
            print(f"   {fname:25} {bar} {importance:.4f}")

        # Cross-validation
        cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=5)
        print(f"\n✅ Cross-Validation (5-fold):")
        print(f"   Mean: {cv_scores.mean():.1%} ± {cv_scores.std():.1%}")

        # Model card
        model_card = {
            "model_name": "Risk Assessment Random Forest",
            "model_type": "RandomForestClassifier",
            "training_date": datetime.now().isoformat(),
            "features": FEATURE_NAMES,
            "risk_levels": RISK_LABELS,
            "training_samples": len(X_train),
            "test_samples": len(X_test),
            "train_accuracy": float(train_score),
            "test_accuracy": float(test_score),
            "cv_mean_accuracy": float(cv_scores.mean()),
            "cv_std_accuracy": float(cv_scores.std()),
            "feature_importances": {fname: float(imp) for fname, imp in importances},
            "hyperparameters": {
                "n_estimators": 100,
                "max_depth": 15,
                "min_samples_split": 3,
                "min_samples_leaf": 1,
            },
        }

        # Save model
        print("\n💾 Model saqlanimoqda...")
        model_dir = backend_dir / "models"
        model_dir.mkdir(exist_ok=True)

        with open(model_dir / "risk_rf_model.pkl", "wb") as f:
            pickle.dump(model, f)
        print(f"   ✅ Model: {model_dir / 'risk_rf_model.pkl'}")

        with open(model_dir / "risk_scaler.pkl", "wb") as f:
            pickle.dump(scaler, f)
        print(f"   ✅ Scaler: {model_dir / 'risk_scaler.pkl'}")

        with open(model_dir / "model_card.json", "w", encoding="utf-8") as f:
            json.dump(model_card, f, indent=2, ensure_ascii=False)
        print(f"   ✅ Model Card: {model_dir / 'model_card.json'}")

        print("\n" + "="*70)
        print("✨ MODEL TRAINING MUVAFFAQIYATLI YAKUNLANDI!")
        print("="*70)
        print(f"\n🎯 Hozir /api/v1/risk/assess/{{topic_id}} endpoint")
        print("   orqali ML model yordamida risk prediction qilinadi.")

        return True


if __name__ == "__main__":
    try:
        result = asyncio.run(train_model())
        sys.exit(0 if result else 1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
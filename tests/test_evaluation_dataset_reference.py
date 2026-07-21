from evaluation.generate_reference import generate
from pathlib import Path

def test_committed_dataset_reference_is_generated():
    assert Path("docs/EVALUATION_DATASET_REFERENCE.md").read_text(encoding="utf-8")==generate()

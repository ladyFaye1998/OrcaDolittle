from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_public_readme_has_neutral_claim_boundary() -> None:
    text = read("README.md")
    assert "does **not** claim translation" in text
    assert "response proxy" in text


def test_neutral_builder_exists() -> None:
    assert (ROOT / "scripts" / "build_validation_evidence_tables.py").exists()


def test_response_proxy_is_not_playback_claim() -> None:
    text = read("scripts/build_validation_evidence_tables.py")
    assert "natural_response_proxy_not_playback" in text
    assert "not a playback experiment" in text
    assert "not playback-response evidence or semantic decoding" in text


def test_h3_sequences_are_chronologically_sorted() -> None:
    text = read("scripts/run_h3_sequence_lm.py")
    assert "_metadata_start_seconds" in text
    assert "sorted(rows, key=lambda item: (item[0], item[1]))" in text

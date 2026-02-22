"""Tests for audio_engine.py — AudioFeatureExtractor and AudioClassifier."""

import json
import sys
from pathlib import Path

import numpy as np
import pytest

# Ensure the project root is on sys.path so we can import audio_engine
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from audio_engine import AudioFeatureExtractor, AudioClassifier
import audio_engine


# ---------------------------------------------------------------------------
# AudioFeatureExtractor tests
# ---------------------------------------------------------------------------

class TestAudioFeatureExtractor:

    def setup_method(self):
        self.extractor = AudioFeatureExtractor(sample_rate=44100)

    def test_extract_silence(self):
        """Extracting features from an all-zeros array should yield rms ~0 and peak ~0."""
        silence = np.zeros(44100, dtype=np.float64)
        features = self.extractor.extract(silence)
        assert features["rms"] == pytest.approx(0.0, abs=1e-10)
        assert features["peak"] == pytest.approx(0.0, abs=1e-10)

    def test_extract_sine_wave(self):
        """A 1 kHz sine wave should have spectral centroid near 1000 Hz and rms > 0."""
        t = np.arange(44100) / 44100.0
        sine = np.sin(2 * np.pi * 1000 * t)
        features = self.extractor.extract(sine)
        assert features["rms"] > 0
        # Spectral centroid should be close to 1000 Hz (allow some FFT bin error)
        assert features["spectral_centroid"] == pytest.approx(1000.0, abs=50.0)

    def test_extract_impulse(self):
        """A sharp spike in the middle of silence should give high crest_factor
        and a fast (low) rise_time."""
        impulse = np.zeros(4096, dtype=np.float64)
        impulse[2048] = 1.0
        features = self.extractor.extract(impulse)
        # Crest factor = peak / rms; for a single spike in 4096 samples this is very large
        assert features["crest_factor"] > 10.0
        # Rise time should be very small (spike goes from 0 to peak instantly)
        assert features["rise_time"] < 5

    def test_extract_empty(self):
        """An empty array should return all features as 0.0."""
        features = self.extractor.extract(np.array([], dtype=np.float64))
        for key, value in features.items():
            assert value == 0.0, f"Expected 0.0 for '{key}', got {value}"

    def test_extract_returns_all_keys(self):
        """Extract should return exactly the 12 documented feature keys."""
        expected_keys = {
            "rms", "peak", "crest_factor", "zcr",
            "spectral_centroid", "spectral_rolloff",
            "energy_0_500", "energy_500_2k", "energy_2k_6k", "energy_6k_plus",
            "impact_ratio", "rise_time",
        }
        features = self.extractor.extract(np.zeros(1024, dtype=np.float64))
        assert set(features.keys()) == expected_keys


# ---------------------------------------------------------------------------
# AudioClassifier tests
# ---------------------------------------------------------------------------

class TestAudioClassifier:

    def test_classifier_heuristic_mode(self):
        """A freshly created AudioClassifier should default to heuristic mode."""
        classifier = AudioClassifier()
        assert classifier.mode == "heuristic"

    def test_classifier_heuristic_low_for_silence(self):
        """Silence features should receive a low heuristic confidence (< 0.3)."""
        extractor = AudioFeatureExtractor(sample_rate=44100)
        silence = np.zeros(44100, dtype=np.float64)
        features = extractor.extract(silence)

        classifier = AudioClassifier()
        confidence = classifier.classify(features)
        assert confidence < 0.3

    def test_classifier_heuristic_scoring(self):
        """Crafted features mimicking a golf impact should score > 0.5."""
        impact_features = {
            "rms": 0.15,
            "peak": 0.95,
            "crest_factor": 8.0,       # > 6 -> +0.25
            "zcr": 0.15,               # between 0.05 and 0.35 -> +0.10
            "spectral_centroid": 3000,  # between 1500 and 5000 -> +0.15
            "spectral_rolloff": 6000,
            "energy_0_500": 0.1,        # not > 0.7, no penalty
            "energy_500_2k": 0.2,
            "energy_2k_6k": 0.5,
            "energy_6k_plus": 0.2,
            "impact_ratio": 0.35,       # > 0.3 -> +0.25
            "rise_time": 10,            # < 30 -> +0.20
        }

        classifier = AudioClassifier()
        confidence = classifier._classify_heuristic(impact_features)
        assert confidence > 0.5

    def test_classifier_retrain_insufficient_data(self, tmp_path, monkeypatch):
        """retrain() should return False when the training directory has < 10 samples."""
        monkeypatch.setattr(audio_engine, "TRAINING_DATA_DIR", tmp_path)
        # Also patch the module-level CLASSIFIER_PATH so it points inside tmp_path
        monkeypatch.setattr(audio_engine, "CLASSIFIER_PATH", tmp_path / "audio_classifier.pkl")

        # Create 3 meta files (fewer than the required 10)
        for i in range(3):
            meta = {
                "features": {k: 0.0 for k in AudioClassifier.FEATURE_KEYS},
                "label": 1,
            }
            meta_path = tmp_path / f"trigger_{i}_meta.json"
            meta_path.write_text(json.dumps(meta))

        classifier = AudioClassifier()
        result = classifier.retrain()
        assert result is False

    def test_training_sample_count(self, tmp_path, monkeypatch):
        """training_sample_count should match the number of trigger_*_meta.json files."""
        monkeypatch.setattr(audio_engine, "TRAINING_DATA_DIR", tmp_path)

        # Create 5 matching meta files
        for i in range(5):
            (tmp_path / f"trigger_{i}_meta.json").write_text("{}")

        # Create a non-matching file that should be ignored
        (tmp_path / "other_file.json").write_text("{}")

        classifier = AudioClassifier()
        assert classifier.training_sample_count == 5

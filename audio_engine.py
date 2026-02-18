"""
Audio detection engine with feature extraction and classification.
"""

import json
import logging
import pickle
import struct
import threading
import time
import wave
from collections import deque
from pathlib import Path
from typing import Optional, Dict, List

import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal

from config import AppConfig, TRAINING_DATA_DIR

logger = logging.getLogger(__name__)

try:
    import pyaudio
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False
    logger.warning("PyAudio not available. Audio triggering disabled.")

try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.info("scikit-learn not available. Using heuristic audio classifier only.")

CLASSIFIER_PATH = TRAINING_DATA_DIR / "audio_classifier.pkl"


# ============================================================================
# Audio Feature Extraction
# ============================================================================

class AudioFeatureExtractor:
    """Extracts 12 features from audio chunks using numpy FFT."""

    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate

    def extract(self, samples: np.ndarray) -> Dict[str, float]:
        """Extract features from a numpy array of audio samples (float, normalized -1 to 1)."""
        if len(samples) == 0:
            return self._empty_features()

        samples_f = samples.astype(np.float64)
        n = len(samples_f)

        # 1. RMS
        rms = np.sqrt(np.mean(samples_f ** 2))

        # 2. Peak amplitude
        peak = np.max(np.abs(samples_f))

        # 3. Crest factor (peak/RMS) - key for impulsive sounds
        crest_factor = peak / rms if rms > 1e-10 else 0.0

        # 4. Zero-crossing rate
        sign_changes = np.diff(np.sign(samples_f))
        zcr = np.sum(sign_changes != 0) / n

        # FFT for spectral features
        fft_vals = np.fft.rfft(samples_f)
        magnitudes = np.abs(fft_vals)
        freqs = np.fft.rfftfreq(n, d=1.0 / self.sample_rate)

        total_energy = np.sum(magnitudes ** 2)
        if total_energy < 1e-20:
            total_energy = 1e-20

        # 5. Spectral centroid
        if np.sum(magnitudes) > 1e-10:
            spectral_centroid = np.sum(freqs * magnitudes) / np.sum(magnitudes)
        else:
            spectral_centroid = 0.0

        # 6. Spectral rolloff (85% energy)
        cumulative = np.cumsum(magnitudes ** 2)
        rolloff_idx = np.searchsorted(cumulative, 0.85 * cumulative[-1]) if cumulative[-1] > 0 else 0
        spectral_rolloff = freqs[min(rolloff_idx, len(freqs) - 1)]

        # 7-10. Energy in frequency bands
        def band_energy(low, high):
            mask = (freqs >= low) & (freqs < high)
            return np.sum(magnitudes[mask] ** 2)

        e_0_500 = band_energy(0, 500)
        e_500_2k = band_energy(500, 2000)
        e_2k_6k = band_energy(2000, 6000)
        e_6k_plus = band_energy(6000, self.sample_rate / 2)

        # 11. Impact band ratio (2-6kHz / total)
        impact_ratio = e_2k_6k / total_energy

        # 12. Rise time (samples from 10% to 90% of peak)
        abs_samples = np.abs(samples_f)
        threshold_10 = peak * 0.1
        threshold_90 = peak * 0.9
        idx_10 = np.argmax(abs_samples >= threshold_10) if np.any(abs_samples >= threshold_10) else 0
        idx_90 = np.argmax(abs_samples >= threshold_90) if np.any(abs_samples >= threshold_90) else n
        rise_time = max(0, idx_90 - idx_10)

        return {
            "rms": rms,
            "peak": peak,
            "crest_factor": crest_factor,
            "zcr": zcr,
            "spectral_centroid": spectral_centroid,
            "spectral_rolloff": spectral_rolloff,
            "energy_0_500": e_0_500 / total_energy,
            "energy_500_2k": e_500_2k / total_energy,
            "energy_2k_6k": e_2k_6k / total_energy,
            "energy_6k_plus": e_6k_plus / total_energy,
            "impact_ratio": impact_ratio,
            "rise_time": rise_time,
        }

    def _empty_features(self) -> Dict[str, float]:
        return {k: 0.0 for k in [
            "rms", "peak", "crest_factor", "zcr",
            "spectral_centroid", "spectral_rolloff",
            "energy_0_500", "energy_500_2k", "energy_2k_6k", "energy_6k_plus",
            "impact_ratio", "rise_time",
        ]}


# ============================================================================
# Audio Classifier
# ============================================================================

class AudioClassifier:
    """Classifies audio as golf shot or not.

    Two modes:
    1. Heuristic (default) - hand-tuned rules
    2. Learned - RandomForest after 10+ labeled samples
    """

    FEATURE_KEYS = [
        "rms", "peak", "crest_factor", "zcr",
        "spectral_centroid", "spectral_rolloff",
        "energy_0_500", "energy_500_2k", "energy_2k_6k", "energy_6k_plus",
        "impact_ratio", "rise_time",
    ]

    def __init__(self):
        self.mode = "heuristic"
        self.model = None
        self.scaler = None
        self._load_model()

    def _load_model(self):
        if SKLEARN_AVAILABLE and CLASSIFIER_PATH.exists():
            try:
                with open(CLASSIFIER_PATH, "rb") as f:
                    data = pickle.load(f)
                self.model = data["model"]
                self.scaler = data["scaler"]
                self.mode = "learned"
                logger.info("Loaded learned audio classifier (%d samples)", data.get("n_samples", 0))
            except Exception as e:
                logger.warning("Failed to load audio classifier: %s", e)

    def classify(self, features: Dict[str, float]) -> float:
        """Return confidence 0.0 - 1.0 that this is a golf shot."""
        if self.mode == "learned" and self.model is not None:
            return self._classify_learned(features)
        return self._classify_heuristic(features)

    def _classify_heuristic(self, f: Dict[str, float]) -> float:
        """Score using hand-tuned rules. Threshold at 0.45."""
        score = 0.0

        # Crest factor: impulsive sounds have high crest factor (>4 is typical for impacts)
        cf = f.get("crest_factor", 0)
        if cf > 6:
            score += 0.25
        elif cf > 4:
            score += 0.15
        elif cf > 3:
            score += 0.05

        # Impact band ratio (2-6kHz): golf ball hit concentrates energy here
        ir = f.get("impact_ratio", 0)
        if ir > 0.3:
            score += 0.25
        elif ir > 0.15:
            score += 0.15
        elif ir > 0.08:
            score += 0.05

        # Rise time: impacts have very fast rise (<50 samples at 44.1kHz ~ <1.1ms)
        rt = f.get("rise_time", 9999)
        if rt < 30:
            score += 0.20
        elif rt < 80:
            score += 0.10
        elif rt < 150:
            score += 0.05

        # ZCR: moderate for impacts
        zcr = f.get("zcr", 0)
        if 0.05 < zcr < 0.35:
            score += 0.10

        # Spectral centroid: golf impacts typically 1.5-5kHz
        sc = f.get("spectral_centroid", 0)
        if 1500 < sc < 5000:
            score += 0.15
        elif 800 < sc < 7000:
            score += 0.05

        # Low-frequency dominance penalty (voices, wind)
        if f.get("energy_0_500", 0) > 0.7:
            score -= 0.15

        return max(0.0, min(1.0, score))

    def _classify_learned(self, features: Dict[str, float]) -> float:
        X = np.array([[features.get(k, 0.0) for k in self.FEATURE_KEYS]])
        X_scaled = self.scaler.transform(X)
        proba = self.model.predict_proba(X_scaled)
        # Return probability of class 1 (shot)
        return float(proba[0][1]) if proba.shape[1] > 1 else float(proba[0][0])

    def retrain(self) -> bool:
        """Retrain from labeled audio samples in training_data directory.

        Returns True if successfully retrained.
        """
        if not SKLEARN_AVAILABLE:
            logger.warning("Cannot retrain: scikit-learn not available")
            return False

        TRAINING_DATA_DIR.mkdir(parents=True, exist_ok=True)
        extractor = AudioFeatureExtractor()

        X_list = []
        y_list = []

        for meta_file in TRAINING_DATA_DIR.glob("trigger_*_meta.json"):
            try:
                with open(meta_file, "r") as f:
                    meta = json.load(f)

                label = meta.get("label")
                if label is None:
                    # Determine from paired wav filename
                    wav_shot = meta_file.with_name(meta_file.name.replace("_meta.json", "_shot.wav"))
                    wav_not = meta_file.with_name(meta_file.name.replace("_meta.json", "_not_shot.wav"))
                    if wav_shot.exists():
                        label = 1
                    elif wav_not.exists():
                        label = 0
                    else:
                        continue

                features = meta.get("features")
                if features:
                    X_list.append([features.get(k, 0.0) for k in self.FEATURE_KEYS])
                    y_list.append(label)
            except Exception:
                continue

        if len(X_list) < 10:
            logger.info("Not enough training samples (%d/10). Staying in heuristic mode.", len(X_list))
            return False

        X = np.array(X_list)
        y = np.array(y_list)

        # Need both classes
        if len(set(y)) < 2:
            logger.info("Need both shot and not-shot samples to train. Have only one class.")
            return False

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        model = RandomForestClassifier(n_estimators=50, random_state=42, max_depth=8)
        model.fit(X_scaled, y)

        # Save
        CLASSIFIER_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(CLASSIFIER_PATH, "wb") as f:
            pickle.dump({"model": model, "scaler": scaler, "n_samples": len(X_list)}, f)

        self.model = model
        self.scaler = scaler
        self.mode = "learned"
        logger.info("Audio classifier retrained with %d samples (mode: learned)", len(X_list))
        return True

    @property
    def training_sample_count(self) -> int:
        """Count available training samples."""
        if not TRAINING_DATA_DIR.exists():
            return 0
        return len(list(TRAINING_DATA_DIR.glob("trigger_*_meta.json")))


# ============================================================================
# Audio Detector Thread
# ============================================================================

class AudioDetector(QThread):
    """Thread for detecting audio triggers with feature-based classification."""

    trigger_detected = pyqtSignal(float, dict)  # confidence, features
    level_update = pyqtSignal(float)

    def __init__(self, config: AppConfig):
        super().__init__()
        self.config = config
        self.running = False
        self.threshold = config.audio_threshold
        self._lock = threading.Lock()

        self.extractor = AudioFeatureExtractor(config.audio_sample_rate)
        self.classifier = AudioClassifier()

        # Accumulate chunks for classification window (~93ms at 44.1kHz/1024)
        self._chunk_accumulator: List[np.ndarray] = []
        self._chunks_needed = 4

        # Rolling audio buffer (~1s) for saving snippets
        buffer_chunks = int(config.audio_sample_rate / config.audio_chunk_size)
        self._audio_ring = deque(maxlen=buffer_chunks)

    def set_threshold(self, value: float):
        with self._lock:
            self.threshold = value

    def set_device_index(self, index: Optional[int]):
        with self._lock:
            self.config.audio_device_index = index

    def run(self):
        if not AUDIO_AVAILABLE:
            return

        self.running = True
        p = pyaudio.PyAudio()

        try:
            kwargs = {
                "format": pyaudio.paInt16,
                "channels": 1,
                "rate": self.config.audio_sample_rate,
                "input": True,
                "frames_per_buffer": self.config.audio_chunk_size,
            }
            with self._lock:
                dev_idx = self.config.audio_device_index
            if dev_idx is not None:
                kwargs["input_device_index"] = dev_idx

            stream = p.open(**kwargs)
        except Exception as e:
            logger.error("Audio error: %s", e)
            p.terminate()
            return

        cooldown_time = 0
        cooldown_duration = 3.0

        while self.running:
            try:
                data = stream.read(self.config.audio_chunk_size, exception_on_overflow=False)
                samples_int = struct.unpack(f"{len(data) // 2}h", data)
                samples = np.array(samples_int, dtype=np.float32) / 32768.0

                # RMS for level meter
                rms = np.sqrt(np.mean(samples ** 2))
                level = min(1.0, rms * 10)
                self.level_update.emit(level)

                # Store in ring buffer
                self._audio_ring.append(data)

                # RMS gate - skip classification if too quiet
                with self._lock:
                    thresh = self.threshold
                if level < thresh * 0.5:
                    self._chunk_accumulator.clear()
                    continue

                # Accumulate chunks
                self._chunk_accumulator.append(samples)

                if len(self._chunk_accumulator) >= self._chunks_needed:
                    combined = np.concatenate(self._chunk_accumulator)
                    self._chunk_accumulator.clear()

                    features = self.extractor.extract(combined)
                    confidence = self.classifier.classify(features)

                    current_time = time.time()
                    if confidence >= 0.45 and level >= thresh and current_time > cooldown_time:
                        logger.info("Audio trigger: confidence=%.2f, rms=%.4f", confidence, rms)
                        self.trigger_detected.emit(confidence, features)
                        self._save_trigger_snippet(features, confidence)
                        cooldown_time = current_time + cooldown_duration

            except Exception as e:
                logger.error("Audio read error: %s", e)

        stream.stop_stream()
        stream.close()
        p.terminate()

    def _save_trigger_snippet(self, features: Dict, confidence: float):
        """Save audio snippet and metadata around trigger for training."""
        try:
            TRAINING_DATA_DIR.mkdir(parents=True, exist_ok=True)
            timestamp = int(time.time() * 1000)
            base_name = f"trigger_{timestamp}"

            # Save WAV (default label: shot)
            wav_path = TRAINING_DATA_DIR / f"{base_name}_shot.wav"
            audio_data = b"".join(self._audio_ring)
            if audio_data:
                with wave.open(str(wav_path), "wb") as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(self.config.audio_sample_rate)
                    wf.writeframes(audio_data)

            # Save metadata
            meta_path = TRAINING_DATA_DIR / f"{base_name}_meta.json"
            meta = {
                "timestamp": timestamp,
                "confidence": confidence,
                "features": {k: float(v) for k, v in features.items()},
                "label": 1,  # default: shot
                "threshold": self.threshold,
            }
            with open(meta_path, "w") as f:
                json.dump(meta, f, indent=2)

        except Exception as e:
            logger.warning("Failed to save trigger snippet: %s", e)

    def stop(self):
        self.running = False
        self.wait()


def enumerate_audio_devices() -> List[Dict]:
    """Return list of available audio input devices."""
    devices = []
    if not AUDIO_AVAILABLE:
        return devices
    try:
        p = pyaudio.PyAudio()
        for i in range(p.get_device_count()):
            info = p.get_device_info_by_index(i)
            if info.get("maxInputChannels", 0) > 0:
                devices.append({
                    "index": i,
                    "name": info.get("name", f"Device {i}"),
                    "channels": info.get("maxInputChannels", 0),
                    "sample_rate": int(info.get("defaultSampleRate", 44100)),
                })
        p.terminate()
    except Exception as e:
        logger.warning("Failed to enumerate audio devices: %s", e)
    return devices

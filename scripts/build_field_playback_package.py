#!/usr/bin/env python3
"""Build a review or field-release package for controlled killer-whale playback.

The public FEROP catalogue is useful for audition and representation analysis, but
it is not a target-specific, calibrated stimulus library. This builder therefore
has two modes:

* review: audit candidate audio and write a conspicuous non-broadcast package;
* field: refuse export unless provenance, experimental-design, permit, animal-
  welfare, calibration, and audio-quality gates all pass.

Field-mode source WAVs must be complete, naturally recorded sequences approved by
the field collaborator. The builder never assigns semantic meanings to calls and
never constructs a treatment by concatenating isolated catalogue exemplars.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
import re
import shutil
import tempfile
import wave
import zipfile
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = ROOT / "field_playback" / "field_config.example.json"
PROTOCOL = ROOT / "field_playback" / "SCIENTIFIC_PROTOCOL.md"
MANIFEST_FIELDS = [
    "stimulus_id",
    "condition",
    "package_file",
    "derived_from",
    "independent_exemplar_id",
    "pair_id",
    "source_session_id",
    "caller_or_group_id",
    "pod_id",
    "recording_date_utc",
    "recording_location",
    "behaviour_context",
    "context_annotation_source",
    "context_annotation_locked_before_playback",
    "rights_basis",
    "expert_reviewer",
    "natural_sequence",
    "expert_approved",
    "approval_reference",
    "method",
    "sha256",
    "sample_rate_hz",
    "channels",
    "bit_depth",
    "duration_s",
    "peak_dbfs",
    "rms_dbfs",
    "dc_offset",
    "clipped_samples",
]


@dataclass(frozen=True)
class Issue:
    severity: str
    code: str
    message: str
    subject: str = "package"


@dataclass(frozen=True)
class AudioInfo:
    path: str
    sha256: str
    sample_rate_hz: int
    channels: int
    bit_depth: int
    duration_s: float
    peak_dbfs: float
    rms_dbfs: float
    dc_offset: float
    clipped_samples: int


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _decode_pcm(raw: bytes, sample_width: int) -> np.ndarray:
    if sample_width == 1:
        return (np.frombuffer(raw, dtype=np.uint8).astype(np.float64) - 128.0) / 128.0
    if sample_width == 2:
        return np.frombuffer(raw, dtype="<i2").astype(np.float64) / 32768.0
    if sample_width == 3:
        b = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 3)
        values = b[:, 0].astype(np.int32)
        values |= b[:, 1].astype(np.int32) << 8
        values |= b[:, 2].astype(np.int32) << 16
        values = np.where(values & 0x800000, values | ~0xFFFFFF, values)
        return values.astype(np.float64) / 8388608.0
    if sample_width == 4:
        return np.frombuffer(raw, dtype="<i4").astype(np.float64) / 2147483648.0
    raise ValueError(f"unsupported PCM sample width: {sample_width} bytes")


def read_wav(path: Path) -> tuple[np.ndarray, int, int, int]:
    with wave.open(str(path), "rb") as wav:
        if wav.getcomptype() != "NONE":
            raise ValueError(f"compressed WAV is not supported: {wav.getcomptype()}")
        channels = wav.getnchannels()
        sample_rate = wav.getframerate()
        sample_width = wav.getsampwidth()
        data = _decode_pcm(wav.readframes(wav.getnframes()), sample_width)
    if channels > 1:
        data = data.reshape(-1, channels)
    return data, sample_rate, channels, sample_width * 8


def inspect_wav(path: Path) -> AudioInfo:
    samples, sample_rate, channels, bit_depth = read_wav(path)
    flat = np.asarray(samples, dtype=np.float64).reshape(-1)
    peak = float(np.max(np.abs(flat))) if flat.size else 0.0
    rms = float(np.sqrt(np.mean(np.square(flat)))) if flat.size else 0.0
    return AudioInfo(
        path=str(path),
        sha256=sha256_file(path),
        sample_rate_hz=sample_rate,
        channels=channels,
        bit_depth=bit_depth,
        duration_s=float(samples.shape[0] / sample_rate) if sample_rate else 0.0,
        peak_dbfs=20.0 * math.log10(max(peak, 1e-12)),
        rms_dbfs=20.0 * math.log10(max(rms, 1e-12)),
        dc_offset=float(np.mean(flat)) if flat.size else 0.0,
        clipped_samples=int(np.sum(np.abs(flat) >= 0.999969)),
    )


def _moving_rms(values: np.ndarray, window: int) -> np.ndarray:
    squared = np.square(values, dtype=np.float64)
    prefix = np.concatenate(([0.0], np.cumsum(squared)))
    left = np.maximum(0, np.arange(len(values)) - window // 2)
    right = np.minimum(len(values), left + window)
    left = np.maximum(0, right - window)
    return np.sqrt((prefix[right] - prefix[left]) / np.maximum(1, right - left))


def matched_noise_control(samples: np.ndarray, sample_rate: int, seed: int) -> np.ndarray:
    """Generate a spectrum- and envelope-matched negative control.

    Random Fourier phase removes the call waveform while preserving its global
    magnitude spectrum. A 100-ms moving-RMS correction then restores the original
    amplitude envelope. The output is still subject to acoustic-lead review.
    """
    x = np.asarray(samples, dtype=np.float64)
    if x.ndim != 1:
        raise ValueError("matched controls require mono source audio")
    rng = np.random.default_rng(seed)
    spectrum = np.fft.rfft(x)
    phase = rng.uniform(-np.pi, np.pi, len(spectrum))
    phase[0] = 0.0
    if len(x) % 2 == 0:
        phase[-1] = 0.0
    y = np.fft.irfft(np.abs(spectrum) * np.exp(1j * phase), n=len(x))
    window = max(16, int(round(sample_rate * 0.1)))
    source_env = _moving_rms(x, window)
    noise_env = _moving_rms(y, window)
    y *= source_env / np.maximum(noise_env, 1e-9)
    source_rms = float(np.sqrt(np.mean(x * x)))
    noise_rms = float(np.sqrt(np.mean(y * y)))
    if noise_rms:
        y *= source_rms / noise_rms
    fade = min(len(y) // 2, max(1, int(round(sample_rate * 0.02))))
    if fade:
        ramp = np.sin(np.linspace(0.0, np.pi / 2.0, fade)) ** 2
        y[:fade] *= ramp
        y[-fade:] *= ramp[::-1]
    peak = float(np.max(np.abs(y))) if len(y) else 0.0
    if peak >= 0.999:
        y *= 0.995 / peak
    return y


def write_pcm24(path: Path, samples: np.ndarray, sample_rate: int) -> None:
    values = np.clip(np.asarray(samples), -1.0, 1.0 - 1 / 8388608.0)
    integers = np.rint(values * 8388607.0).astype(np.int32)
    packed = np.empty((len(integers), 3), dtype=np.uint8)
    packed[:, 0] = integers & 0xFF
    packed[:, 1] = (integers >> 8) & 0xFF
    packed[:, 2] = (integers >> 16) & 0xFF
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(3)
        wav.setframerate(sample_rate)
        wav.writeframes(packed.tobytes())


def require_text(config: dict[str, Any], dotted: str, issues: list[Issue]) -> None:
    value: Any = config
    for key in dotted.split("."):
        value = value.get(key) if isinstance(value, dict) else None
    if not isinstance(value, str) or not value.strip():
        issues.append(Issue("error", "missing_required_field", f"Missing {dotted}"))


def validate_top_level(config: dict[str, Any]) -> list[Issue]:
    issues: list[Issue] = []
    mode = config.get("mode")
    if mode not in {"review", "field"}:
        issues.append(Issue("error", "invalid_mode", "mode must be review or field"))

    required = [
        "project.project_id",
        "project.principal_investigator",
        "project.institution",
        "project.field_partner",
        "project.target_population",
        "project.study_area",
        "project.field_season",
        "design.design_type",
        "design.experimental_unit",
        "design.primary_outcome",
        "design.sample_size_justification",
        "design.analysis_model",
        "design.randomization_seed",
        "design.observer_blinding_implementation",
        "approvals.jurisdiction",
        "approvals.marine_mammal_authorization_id",
        "approvals.animal_ethics_id",
        "approvals.stimulus_rights_approval_id",
        "approvals.verified_by",
        "calibration.playback_recorder_model",
        "calibration.transducer_model",
        "calibration.amplifier_model",
        "calibration.transducer_depth_m",
        "calibration.monitor_hydrophone_model",
        "calibration.monitor_hydrophone_certificate",
        "calibration.calibration_date",
        "calibration.calibration_distance_m",
        "calibration.permit_approved_source_level_db_re_1upa_at_1m",
        "calibration.nominal_source_level_db_re_1upa_at_1m",
        "calibration.fixed_player_gain_setting",
        "calibration.received_level_monitoring_method",
        "calibration.transducer_frequency_response_check",
        "calibration.calibration_recording_sha256",
        "safety.stop_rule_authority",
        "release.pi_signoff",
        "release.acoustic_lead_signoff",
        "release.animal_welfare_signoff",
    ]
    if mode == "field":
        for field in required:
            require_text(config, field, issues)
        if config.get("design", {}).get("generate_matched_noise_controls"):
            require_text(config, "release.matched_control_review_reference", issues)

    design = config.get("design", {})
    conditions = design.get("conditions", [])
    if (
        not isinstance(conditions, list)
        or not all(isinstance(condition, str) and condition for condition in conditions)
        or len(set(conditions)) < 2
    ):
        issues.append(
            Issue("error", "invalid_conditions", "At least two unique conditions are required")
        )
        conditions = []
    if design.get("design_type") == "content_controlled" and not {
        "CONTENT_A",
        "CONTENT_B",
    }.issubset(conditions):
        issues.append(
            Issue("error", "content_conditions_missing", "CONTENT_A and CONTENT_B are required")
        )
    generated_controls = bool(design.get("generate_matched_noise_controls"))
    if ("MATCHED_NOISE" in conditions) != generated_controls:
        issues.append(
            Issue(
                "error",
                "matched_control_configuration",
                "MATCHED_NOISE must be listed exactly when generated matched controls are enabled",
            )
        )
    if design.get("experimental_unit") not in {
        "identified_social_group_encounter",
        "individually_identified_whale",
    }:
        issues.append(
            Issue(
                "error",
                "invalid_experimental_unit",
                "Experimental unit must be an identified group encounter or individual whale",
            )
        )
    n_per = int(design.get("experimental_units_per_condition", 0) or 0)
    if n_per < 3:
        issues.append(
            Issue(
                "error", "sample_size_too_small", "Use at least 3 experimental units per condition"
            )
        )
    if not design.get("observer_blinded"):
        issues.append(
            Issue("error", "blinding_disabled", "Observer-blinded outcome scoring is required")
        )

    safety = config.get("safety", {})
    if int(safety.get("max_exposures_per_group_per_24h", 0) or 0) < 1:
        issues.append(Issue("error", "invalid_exposure_cap", "Set an approved exposure cap"))
    if int(safety.get("washout_minutes", 0) or 0) < 5:
        issues.append(Issue("error", "washout_too_short", "Washout must be at least 5 minutes"))
    stop_rules = safety.get("stop_rules", [])
    if not isinstance(stop_rules, list) or len(stop_rules) < 4:
        issues.append(
            Issue(
                "error", "stop_rules_incomplete", "At least four explicit stop rules are required"
            )
        )

    if mode == "field":
        expiry = config.get("approvals", {}).get("authorization_valid_through", "")
        try:
            if date.fromisoformat(expiry) < date.today():
                issues.append(
                    Issue(
                        "error", "authorization_expired", "Marine-mammal authorization has expired"
                    )
                )
        except (TypeError, ValueError):
            issues.append(
                Issue(
                    "error",
                    "invalid_authorization_date",
                    "Use YYYY-MM-DD for authorization_valid_through",
                )
            )
        calibration = config.get("calibration", {})
        try:
            calibration_date = date.fromisoformat(str(calibration.get("calibration_date", "")))
            if calibration_date > date.today():
                issues.append(
                    Issue(
                        "error",
                        "calibration_date_in_future",
                        "Calibration date cannot be in the future",
                    )
                )
        except ValueError:
            issues.append(
                Issue(
                    "error",
                    "invalid_calibration_date",
                    "Use YYYY-MM-DD for calibration.calibration_date",
                )
            )
        for key in (
            "transducer_depth_m",
            "calibration_distance_m",
            "permit_approved_source_level_db_re_1upa_at_1m",
            "nominal_source_level_db_re_1upa_at_1m",
            "source_level_tolerance_db",
        ):
            try:
                if float(calibration.get(key, 0)) <= 0:
                    raise ValueError
            except (TypeError, ValueError):
                issues.append(
                    Issue(
                        "error", "invalid_calibration_value", f"calibration.{key} must be positive"
                    )
                )
        try:
            nominal_level = float(calibration.get("nominal_source_level_db_re_1upa_at_1m", 0))
            authorized_maximum = float(
                calibration.get("permit_approved_source_level_db_re_1upa_at_1m", 0)
            )
            if nominal_level > authorized_maximum:
                issues.append(
                    Issue(
                        "error",
                        "nominal_level_exceeds_authorization",
                        "Nominal source level exceeds the authorization maximum",
                    )
                )
        except (TypeError, ValueError):
            pass
        calibration_hash = str(calibration.get("calibration_recording_sha256", ""))
        if not re.fullmatch(r"[0-9a-fA-F]{64}", calibration_hash):
            issues.append(
                Issue(
                    "error",
                    "invalid_calibration_recording_hash",
                    "calibration.calibration_recording_sha256 must be a 64-character SHA-256",
                )
            )
    return issues


def resolve_path(config_path: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (config_path.parent / path).resolve()


def validate_stimuli(
    config: dict[str, Any], config_path: Path
) -> tuple[list[dict[str, Any]], list[Issue]]:
    issues: list[Issue] = []
    rows: list[dict[str, Any]] = []
    audio_cfg = config.get("audio_requirements", {})
    min_rate = int(audio_cfg.get("minimum_sample_rate_hz", 48000))
    min_duration = float(audio_cfg.get("minimum_duration_s", 2.0))
    max_duration = float(audio_cfg.get("maximum_duration_s", 1200.0))
    ids: set[str] = set()
    exemplar_ids: set[str] = set()
    source_sessions: set[str] = set()
    files: set[Path] = set()
    hashes: dict[str, str] = {}
    required_metadata = [
        "stimulus_id",
        "condition",
        "file",
        "independent_exemplar_id",
        "source_session_id",
        "caller_or_group_id",
        "pod_id",
        "recording_date_utc",
        "recording_location",
        "behaviour_context",
        "context_annotation_source",
        "rights_basis",
        "expert_reviewer",
        "pair_id",
    ]

    for item in config.get("stimuli", []):
        sid = str(item.get("stimulus_id", "") or "")
        subject = sid or "unnamed stimulus"
        for key in required_metadata:
            if not str(item.get(key, "") or "").strip():
                issues.append(
                    Issue("error", "missing_stimulus_metadata", f"Missing {key}", subject)
                )
        normalized_sid = sid.casefold()
        if normalized_sid in ids:
            issues.append(Issue("error", "duplicate_stimulus_id", sid, subject))
        ids.add(normalized_sid)
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}", sid):
            issues.append(
                Issue(
                    "error",
                    "unsafe_stimulus_id",
                    "Use 1-80 letters, numbers, dots, underscores, or hyphens",
                    subject,
                )
            )
        reserved_name = sid.split(".", 1)[0].upper()
        if reserved_name in {"CON", "PRN", "AUX", "NUL"} or re.fullmatch(
            r"(?:COM|LPT)[1-9]", reserved_name
        ):
            issues.append(
                Issue(
                    "error", "reserved_stimulus_id", "Stimulus ID is a reserved filename", subject
                )
            )
        exemplar_id = str(item.get("independent_exemplar_id", ""))
        if exemplar_id in exemplar_ids:
            issues.append(Issue("error", "duplicate_exemplar_id", exemplar_id, subject))
        exemplar_ids.add(exemplar_id)
        source_session = str(item.get("source_session_id", ""))
        if source_session in source_sessions:
            issues.append(Issue("error", "source_session_reused", source_session, subject))
        source_sessions.add(source_session)
        path = resolve_path(config_path, str(item.get("file", "")))
        if path.suffix.casefold() != ".wav":
            issues.append(
                Issue("error", "audio_not_wav", "Field stimuli must use a .wav filename", subject)
            )
        if path in files:
            issues.append(Issue("error", "audio_reused_across_rows", str(path), subject))
        files.add(path)
        if not item.get("natural_sequence"):
            issues.append(
                Issue(
                    "error",
                    "not_natural_sequence",
                    "Isolated or concatenated catalogue calls are ineligible",
                    subject,
                )
            )
        if not item.get("expert_approved"):
            issues.append(
                Issue(
                    "error",
                    "expert_approval_missing",
                    "Field collaborator has not approved this sequence",
                    subject,
                )
            )
        if not item.get("context_annotation_locked_before_playback"):
            issues.append(
                Issue(
                    "error",
                    "context_annotation_not_locked",
                    "Context annotation must be locked before playback and outcome inspection",
                    subject,
                )
            )
        try:
            date.fromisoformat(str(item.get("recording_date_utc", ""))[:10])
        except ValueError:
            issues.append(
                Issue("error", "invalid_recording_date", "Use ISO 8601 recording_date_utc", subject)
            )
        if config.get("mode") == "field":
            rights_id = str(config.get("approvals", {}).get("stimulus_rights_approval_id", ""))
            if rights_id and rights_id not in str(item.get("rights_basis", "")):
                issues.append(
                    Issue(
                        "error",
                        "stimulus_rights_reference_mismatch",
                        f"rights_basis must reference {rights_id}",
                        subject,
                    )
                )
        if not path.exists():
            issues.append(Issue("error", "audio_missing", str(path), subject))
            continue
        try:
            info = inspect_wav(path)
        except (ValueError, wave.Error) as exc:
            issues.append(Issue("error", "audio_unreadable", str(exc), subject))
            continue
        if info.sample_rate_hz < min_rate:
            issues.append(
                Issue(
                    "error",
                    "sample_rate_too_low",
                    f"{info.sample_rate_hz} < {min_rate} Hz",
                    subject,
                )
            )
        if info.channels != 1:
            issues.append(Issue("error", "audio_not_mono", f"{info.channels} channels", subject))
        if info.bit_depth < 16:
            issues.append(Issue("error", "bit_depth_too_low", f"{info.bit_depth}-bit", subject))
        if not min_duration <= info.duration_s <= max_duration:
            issues.append(
                Issue(
                    "error",
                    "duration_out_of_range",
                    f"{info.duration_s:.2f}s not in [{min_duration}, {max_duration}]",
                    subject,
                )
            )
        if info.clipped_samples:
            issues.append(
                Issue("error", "audio_clipped", f"{info.clipped_samples} clipped samples", subject)
            )
        if abs(info.dc_offset) > float(audio_cfg.get("maximum_absolute_dc_offset", 0.01)):
            issues.append(Issue("error", "dc_offset_excessive", f"{info.dc_offset:.5f}", subject))
        if info.rms_dbfs < float(audio_cfg.get("minimum_rms_dbfs", -60.0)):
            issues.append(Issue("error", "audio_too_quiet", f"{info.rms_dbfs:.1f} dBFS", subject))
        if info.sha256 in hashes:
            issues.append(
                Issue(
                    "error",
                    "duplicate_audio_content",
                    f"Audio duplicates {hashes[info.sha256]}",
                    subject,
                )
            )
        else:
            hashes[info.sha256] = subject
        if item.get("condition") not in config.get("design", {}).get("conditions", []):
            issues.append(
                Issue("error", "condition_not_in_design", str(item.get("condition")), subject)
            )
        rows.append({**item, **asdict(info), "resolved_path": str(path)})

    if config.get("mode") == "field" and not rows:
        issues.append(
            Issue("error", "no_field_stimuli", "No eligible target-population sequences supplied")
        )

    design = config.get("design", {})
    min_exemplars = int(design.get("minimum_independent_stimuli_per_condition", 3))
    audio_conditions = [
        c for c in design.get("conditions", []) if c not in {"SILENCE", "MATCHED_NOISE"}
    ]
    for condition in audio_conditions:
        subset = [r for r in rows if r.get("condition") == condition]
        unique = {r.get("independent_exemplar_id") for r in subset}
        sessions = {r.get("source_session_id") for r in subset}
        if config.get("mode") == "field" and len(unique) < min_exemplars:
            issues.append(
                Issue(
                    "error",
                    "stimulus_pseudoreplication",
                    f"{condition} has {len(unique)} independent exemplars; require {min_exemplars}",
                    condition,
                )
            )
        if config.get("mode") == "field" and len(sessions) < min_exemplars:
            issues.append(
                Issue(
                    "error",
                    "source_session_pseudoreplication",
                    (
                        f"{condition} has {len(sessions)} independent source sessions; "
                        f"require {min_exemplars}"
                    ),
                    condition,
                )
            )

    if design.get("design_type") == "content_controlled" and {"CONTENT_A", "CONTENT_B"}.issubset(
        audio_conditions
    ):
        first, second = "CONTENT_A", "CONTENT_B"
        pairs: dict[str, dict[str, dict[str, Any]]] = {}
        for row in rows:
            if row.get("condition") in {first, second}:
                pair_id = str(row.get("pair_id"))
                condition = str(row.get("condition"))
                if condition in pairs.setdefault(pair_id, {}):
                    issues.append(
                        Issue(
                            "error",
                            "duplicate_pair_condition",
                            f"More than one {condition} row uses this pair ID",
                            pair_id,
                        )
                    )
                pairs[pair_id][condition] = row
        for pair_id, pair in pairs.items():
            if set(pair) != {first, second}:
                issues.append(
                    Issue("error", "incomplete_content_pair", f"Need {first} and {second}", pair_id)
                )
                continue
            a, b = pair[first], pair[second]
            if a.get("pod_id") != b.get("pod_id") or a.get("caller_or_group_id") != b.get(
                "caller_or_group_id"
            ):
                issues.append(
                    Issue(
                        "error",
                        "content_pair_identity_mismatch",
                        "Pair must hold pod/caller identity constant",
                        pair_id,
                    )
                )
            if a.get("source_session_id") == b.get("source_session_id"):
                issues.append(
                    Issue(
                        "error",
                        "content_pair_same_session",
                        "Paired contexts require independent source sessions",
                        pair_id,
                    )
                )
            if a.get("behaviour_context") == b.get("behaviour_context"):
                issues.append(
                    Issue(
                        "error",
                        "content_pair_same_context",
                        "Paired context labels must differ",
                        pair_id,
                    )
                )
            durations = (float(a.get("duration_s", 0)), float(b.get("duration_s", 0)))
            maximum_ratio = float(audio_cfg.get("maximum_pair_duration_ratio", 1.5))
            if min(durations) <= 0 or max(durations) / min(durations) > maximum_ratio:
                issues.append(
                    Issue(
                        "error",
                        "content_pair_duration_mismatch",
                        f"Pair duration ratio exceeds {maximum_ratio:.2f}",
                        pair_id,
                    )
                )
            maximum_rms_difference = float(audio_cfg.get("maximum_pair_rms_difference_db", 6.0))
            if (
                abs(float(a.get("rms_dbfs", 0)) - float(b.get("rms_dbfs", 0)))
                > maximum_rms_difference
            ):
                issues.append(
                    Issue(
                        "error",
                        "content_pair_level_mismatch",
                        f"Digital RMS difference exceeds {maximum_rms_difference:.1f} dB",
                        pair_id,
                    )
                )
    return rows, issues


def audit_catalogue(config: dict[str, Any], config_path: Path) -> list[dict[str, Any]]:
    value = config.get("catalogue_audit_dir")
    if not value:
        return []
    directory = resolve_path(config_path, str(value))
    output: list[dict[str, Any]] = []
    min_rate = int(config.get("audio_requirements", {}).get("minimum_sample_rate_hz", 48000))
    for path in sorted(directory.glob("*.wav")):
        try:
            info = inspect_wav(path)
            reasons = []
            if info.sample_rate_hz < min_rate:
                reasons.append(f"sample rate {info.sample_rate_hz} Hz below {min_rate} Hz")
            reasons.extend(["caller/pod provenance absent", "recording-chain calibration absent"])
            output.append({**asdict(info), "field_eligible": False, "reasons": "; ".join(reasons)})
        except (ValueError, wave.Error) as exc:
            output.append({"path": str(path), "field_eligible": False, "reasons": str(exc)})
    return output


def stable_blind_code(seed: str, condition: str, allocation_slot: int) -> str:
    return hashlib.sha256(f"{seed}|{condition}|{allocation_slot}".encode()).hexdigest()[:12].upper()


def randomized_allocations(
    config: dict[str, Any], stimuli: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    design = config["design"]
    conditions = list(design["conditions"])
    n_per = int(design["experimental_units_per_condition"])
    seed_text = str(design["randomization_seed"])
    rng = random.Random(hashlib.sha256(seed_text.encode()).digest())
    values = [condition for condition in conditions for _ in range(n_per)]
    for _ in range(5000):
        rng.shuffle(values)
        if all(values[i] != values[i - 1] for i in range(1, len(values))):
            break

    pools: dict[str, list[str]] = {}
    for condition in conditions:
        ids = [str(row["stimulus_id"]) for row in stimuli if row.get("condition") == condition]
        rng.shuffle(ids)
        pools[condition] = ids
    counters = {condition: 0 for condition in conditions}
    rows = []
    for index, condition in enumerate(values, 1):
        pool = pools.get(condition, [])
        stimulus_id = "none" if condition == "SILENCE" else "pending"
        if pool:
            stimulus_id = pool[counters[condition] % len(pool)]
            counters[condition] += 1
        rows.append(
            {
                "allocation_slot": index,
                "trial_id": f"{config['project']['project_id']}-{index:03d}",
                "condition": condition,
                "blind_code": stable_blind_code(seed_text, condition, index),
                "stimulus_id": stimulus_id,
                "experimental_unit_id": "",
                "encounter_date_utc": "",
                "operator_initials": "",
                "baseline_minutes": config["safety"]["baseline_minutes"],
                "response_minutes": config["safety"]["response_minutes"],
                "washout_minutes": config["safety"]["washout_minutes"],
            }
        )
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = list(rows[0]) if rows else []
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def matched_control_for_item(
    config: dict[str, Any], item: dict[str, Any]
) -> tuple[str, np.ndarray, int]:
    source = Path(item["resolved_path"])
    samples, rate, channels, _ = read_wav(source)
    if channels != 1:
        raise ValueError(f"matched controls require mono source audio: {source}")
    base_seed = str(config["design"]["randomization_seed"])
    seed = int.from_bytes(
        hashlib.sha256(f"{base_seed}|{item['stimulus_id']}".encode()).digest()[:8],
        "big",
    )
    return f"MN-{item['stimulus_id']}", matched_noise_control(samples, rate, seed), rate


def validate_matched_control_approvals(
    config: dict[str, Any], stimuli: list[dict[str, Any]]
) -> list[Issue]:
    if config.get("mode") != "field" or not config.get("design", {}).get(
        "generate_matched_noise_controls"
    ):
        return []
    issues: list[Issue] = []
    approved = config.get("release", {}).get("approved_matched_control_sha256", {})
    if not isinstance(approved, dict) or not approved:
        return [
            Issue(
                "error",
                "matched_control_hash_approvals_missing",
                "Run a review build, inspect every derived control, and add its approved SHA-256",
            )
        ]
    with tempfile.TemporaryDirectory(prefix="orca_matched_review_") as tmp:
        directory = Path(tmp)
        for item in stimuli:
            try:
                control_id, control, rate = matched_control_for_item(config, item)
                path = directory / f"{control_id}.wav"
                write_pcm24(path, control, rate)
                actual = sha256_file(path)
            except (OSError, ValueError, wave.Error) as exc:
                issues.append(
                    Issue(
                        "error",
                        "matched_control_generation_failed",
                        str(exc),
                        str(item.get("stimulus_id")),
                    )
                )
                continue
            expected = str(approved.get(control_id, "")).lower()
            if not expected:
                issues.append(
                    Issue(
                        "error",
                        "matched_control_hash_unapproved",
                        f"No approved SHA-256 for {control_id}; review hash is {actual}",
                        control_id,
                    )
                )
            elif expected != actual:
                issues.append(
                    Issue(
                        "error",
                        "matched_control_hash_mismatch",
                        f"Approved {expected}; generated {actual}",
                        control_id,
                    )
                )
    unused = sorted(set(approved) - {f"MN-{item['stimulus_id']}" for item in stimuli})
    if unused:
        issues.append(
            Issue(
                "error",
                "stale_matched_control_approvals",
                "Approved hashes do not map to current stimuli: " + ", ".join(unused),
            )
        )
    return issues


def validate_per_file_calibration(
    config: dict[str, Any], stimuli: list[dict[str, Any]]
) -> list[Issue]:
    if config.get("mode") != "field":
        return []
    calibration = config.get("calibration", {})
    values = calibration.get("per_file_source_level_db_re_1upa_at_1m", {})
    if not isinstance(values, dict) or not values:
        return [
            Issue(
                "error",
                "per_file_calibration_missing",
                (
                    "Calibrate every exact natural and matched-control file through "
                    "the locked playback chain"
                ),
            )
        ]
    expected_ids = {str(item["stimulus_id"]) for item in stimuli}
    if config.get("design", {}).get("generate_matched_noise_controls"):
        expected_ids |= {f"MN-{item['stimulus_id']}" for item in stimuli}
    issues: list[Issue] = []
    missing = sorted(expected_ids - set(values))
    stale = sorted(set(values) - expected_ids)
    if missing:
        issues.append(
            Issue(
                "error",
                "per_file_calibration_incomplete",
                "Missing source-level measurements: " + ", ".join(missing),
            )
        )
    if stale:
        issues.append(
            Issue(
                "error",
                "stale_per_file_calibration",
                "Measurements do not map to current files: " + ", ".join(stale),
            )
        )
    try:
        nominal = float(calibration["nominal_source_level_db_re_1upa_at_1m"])
        authorized_maximum = float(calibration["permit_approved_source_level_db_re_1upa_at_1m"])
        tolerance = float(calibration.get("source_level_tolerance_db", 0))
    except (KeyError, TypeError, ValueError):
        return issues
    if tolerance <= 0:
        issues.append(
            Issue(
                "error", "invalid_source_level_tolerance", "Source-level tolerance must be positive"
            )
        )
        return issues
    for stimulus_id in sorted(expected_ids & set(values)):
        try:
            measured = float(values[stimulus_id])
        except (TypeError, ValueError):
            issues.append(
                Issue(
                    "error",
                    "invalid_per_file_source_level",
                    "Source-level measurement must be numeric",
                    stimulus_id,
                )
            )
            continue
        if measured > authorized_maximum:
            issues.append(
                Issue(
                    "error",
                    "per_file_level_exceeds_authorization",
                    f"{measured:.2f} dB exceeds {authorized_maximum:.2f} dB",
                    stimulus_id,
                )
            )
        if abs(measured - nominal) > tolerance:
            issues.append(
                Issue(
                    "error",
                    "per_file_level_outside_tolerance",
                    (
                        f"{measured:.2f} dB differs from nominal {nominal:.2f} dB "
                        f"by more than {tolerance:.2f} dB"
                    ),
                    stimulus_id,
                )
            )
    return issues


def build_matched_controls(
    directory: Path, config: dict[str, Any], stimuli: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    if not config.get("design", {}).get("generate_matched_noise_controls"):
        return []
    rows = []
    for item in stimuli:
        try:
            cid, control, rate = matched_control_for_item(config, item)
        except (OSError, ValueError, wave.Error):
            continue
        out = directory / "audio" / "matched_noise" / f"{cid}.wav"
        write_pcm24(out, control, rate)
        info = inspect_wav(out)
        field_mode = config.get("mode") == "field"
        rows.append(
            {
                "stimulus_id": cid,
                "condition": "MATCHED_NOISE",
                "package_file": str(out.relative_to(directory)),
                "derived_from": item["stimulus_id"],
                "method": "Fourier phase randomization plus 100-ms moving-RMS envelope match",
                "expert_approved": field_mode,
                "approval_reference": config.get("release", {}).get(
                    "matched_control_review_reference", ""
                ),
                **asdict(info),
            }
        )
    return rows


def write_package(
    config: dict[str, Any],
    config_path: Path,
    output: Path,
    stimuli: list[dict[str, Any]],
    issues: list[Issue],
    catalogue: list[dict[str, Any]],
) -> None:
    if config.get("mode") == "field" and any(issue.severity == "error" for issue in issues):
        raise ValueError("Refusing to write a field-release package with validation errors")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="orca_field_package_") as tmp:
        package = Path(tmp) / "package"
        package.mkdir()
        field_mode = config.get("mode") == "field"
        status = (
            "FIELD CONFIGURATION PASS - HUMAN AUTHORIZATION STILL REQUIRED"
            if field_mode
            else "REVIEW ONLY - DO NOT BROADCAST"
        )
        (package / "README_FIRST.txt").write_text(
            f"{status}\n\n"
            "This package does not assign semantic meaning to any killer-whale call.\n"
            "A configuration pass is not a permit, welfare approval, or safety finding.\n"
            "Use is limited to the target population, dates, equipment, gain, mitigations,\n"
            "and actual authorizations recorded in and independently verified against\n"
            "field_config.json. Governing permits and the field principal investigator\n"
            "remain controlling.\n"
            "Browser audition files are never field stimuli.\n"
            "This master archive contains restricted condition and unblinding files.\n",
            encoding="utf-8",
        )
        if not field_mode:
            (package / "DO_NOT_BROADCAST.txt").write_text(
                "Current public catalogue clips fail target-specific provenance and "
                "calibration gates.\n"
                "Use this archive for collaborator review and protocol development only.\n",
                encoding="utf-8",
            )
        else:
            (package / "FIELD_AUTHORIZATION_NOTICE.txt").write_text(
                "MACHINE VALIDATION IS NOT AUTHORIZATION TO BROADCAST\n\n"
                "The builder checks configured metadata, file integrity, acoustic values,\n"
                "and release attestations for completeness and internal consistency. It\n"
                "does not authenticate permits, validate the truth of entered values,\n"
                "determine biological safety, or supersede permit conditions. Before every\n"
                "use, the principal investigator must verify the actual authorizations,\n"
                "approved equipment and gain, target identity, exclusion conditions, and\n"
                "real-time stop authority.\n",
                encoding="utf-8",
            )
        (package / "field_config.json").write_text(
            json.dumps(config, indent=2) + "\n", encoding="utf-8"
        )
        (package / "DISTRIBUTION_README.txt").write_text(
            "MASTER ARCHIVE - DATA MANAGER / PRINCIPAL INVESTIGATOR ONLY\n\n"
            "Blinded observers receive only the observer/ directory and approved neutral\n"
            "instructions. They must not receive restricted/, field_config.json, the audio\n"
            "directory, the stimulus manifest, or condition-bearing operator materials.\n"
            "The observer-blinding implementation in field_config.json governs physical\n"
            "separation, communications, and masking during sound and silence conditions.\n",
            encoding="utf-8",
        )
        has_errors = any(i.severity == "error" for i in issues)
        report = {
            "status": (
                "FIELD_CONFIG_PASS"
                if field_mode and not has_errors
                else "FIELD_BLOCKED"
                if field_mode
                else "REVIEW_ONLY"
            ),
            "mode": config.get("mode"),
            "errors": sum(i.severity == "error" for i in issues),
            "warnings": sum(i.severity == "warning" for i in issues),
            "issues": [asdict(issue) for issue in issues],
        }
        (package / "validation_report.json").write_text(
            json.dumps(report, indent=2) + "\n", encoding="utf-8"
        )
        if PROTOCOL.exists():
            shutil.copy2(PROTOCOL, package / "SCIENTIFIC_PROTOCOL.md")
        if catalogue:
            write_csv(package / "catalogue_audio_audit.csv", catalogue)

        copied_stimuli: list[dict[str, Any]] = []
        for item in stimuli:
            source = Path(item["resolved_path"])
            destination = (
                package
                / "audio"
                / "natural_sequences"
                / f"{item['stimulus_id']}{source.suffix.lower()}"
            )
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            copied_stimuli.append({**item, "package_file": str(destination.relative_to(package))})
        matched = build_matched_controls(package, config, copied_stimuli)
        manifest = [
            {k: v for k, v in row.items() if k != "resolved_path"} for row in copied_stimuli
        ] + matched
        write_csv(package / "stimulus_manifest.csv", manifest, MANIFEST_FIELDS)

        allocations = randomized_allocations(config, copied_stimuli + matched)
        operator_fields = [
            "allocation_slot",
            "trial_id",
            "condition",
            "stimulus_id",
            "experimental_unit_id",
            "encounter_date_utc",
            "operator_initials",
            "baseline_minutes",
            "response_minutes",
            "washout_minutes",
        ]
        write_csv(package / "restricted" / "operator_run_sheet.csv", allocations, operator_fields)
        key_rows = [
            {
                "trial_id": row["trial_id"],
                "blind_code": row["blind_code"],
                "condition": row["condition"],
                "stimulus_id": row["stimulus_id"],
            }
            for row in allocations
        ]
        write_csv(
            package / "restricted" / "analysis_unblinding_key.csv",
            key_rows,
            ["trial_id", "blind_code", "condition", "stimulus_id"],
        )
        score_fields = [
            "trial_id",
            "blind_code",
            "experimental_unit_id",
            "encounter_date_utc",
            "observer_id",
            "baseline_vocal_count",
            "response_vocal_count",
            "first_reply_latency_s",
            "heading_change_deg",
            "speed_change_mps",
            "group_spread_pre_m",
            "group_spread_post_m",
            "received_level_db_re_1upa",
            "behaviour_state_pre",
            "behaviour_state_post",
            "stop_rule_triggered",
            "notes",
        ]
        score_rows = [
            {
                "trial_id": row["trial_id"],
                "blind_code": row["blind_code"],
                **{key: "" for key in score_fields[2:]},
            }
            for row in allocations
        ]
        write_csv(package / "observer" / "observer_scoring_sheet.csv", score_rows, score_fields)
        (package / "calibration_gain_lock.json").write_text(
            json.dumps(config.get("calibration", {}), indent=2) + "\n", encoding="utf-8"
        )
        (package / "stop_rules.json").write_text(
            json.dumps(config.get("safety", {}), indent=2) + "\n", encoding="utf-8"
        )

        checksum_lines = []
        for path in sorted(
            p for p in package.rglob("*") if p.is_file() and p.name != "checksums.sha256"
        ):
            checksum_lines.append(f"{sha256_file(path)}  {path.relative_to(package).as_posix()}")
        (package / "checksums.sha256").write_text(
            "\n".join(checksum_lines) + "\n", encoding="ascii"
        )

        temporary_zip = Path(tmp) / "package.zip"
        with zipfile.ZipFile(temporary_zip, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(p for p in package.rglob("*") if p.is_file()):
                archive.write(path, path.relative_to(package).as_posix())
        shutil.copy2(temporary_zip, output)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    config_path = args.config.resolve()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    top_issues = validate_top_level(config)
    stimuli, stimulus_issues = validate_stimuli(config, config_path)
    control_issues = validate_matched_control_approvals(config, stimuli)
    calibration_issues = validate_per_file_calibration(config, stimuli)
    issues = top_issues + stimulus_issues + control_issues + calibration_issues
    catalogue = audit_catalogue(config, config_path)
    errors = [issue for issue in issues if issue.severity == "error"]
    if config.get("mode") == "field" and errors:
        print(f"Field export blocked: {len(errors)} error(s)")
        for issue in errors:
            print(f"  {issue.code}: {issue.subject}: {issue.message}")
        return 2
    write_package(config, config_path, args.output.resolve(), stimuli, issues, catalogue)
    state = (
        "FIELD CONFIGURATION PASS - HUMAN AUTHORIZATION REQUIRED"
        if config.get("mode") == "field"
        else "REVIEW ONLY"
    )
    print(f"Playback package written: {args.output.resolve()} ({state})")
    print(
        f"Validation: {len(errors)} errors, {sum(i.severity == 'warning' for i in issues)} warnings"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

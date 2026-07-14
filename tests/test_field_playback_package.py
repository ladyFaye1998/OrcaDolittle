import csv
import io
import json
import sys
import wave
import zipfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import build_field_playback_package as builder  # noqa: E402


def write_test_wav(path: Path, frequency_hz: float, phase: float = 0.0) -> None:
    sample_rate = 48_000
    duration_s = 2.5
    time = np.arange(int(sample_rate * duration_s), dtype=np.float64) / sample_rate
    envelope = np.sin(np.pi * np.clip(time / duration_s, 0.0, 1.0)) ** 2
    signal = 0.18 * envelope * np.sin(2 * np.pi * frequency_hz * time + phase)
    pcm = np.rint(signal * 32767.0).astype("<i2")
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(pcm.tobytes())


def field_config(tmp_path: Path) -> dict:
    config = json.loads(
        (ROOT / "field_playback" / "field_config.example.json").read_text(encoding="utf-8")
    )
    config["mode"] = "field"
    config.pop("catalogue_audit_dir", None)
    config["project"] = {
        "project_id": "TEST-PLAYBACK",
        "principal_investigator": "Test Principal Investigator",
        "institution": "Test Research Institution",
        "field_partner": "Target Population Research Partner",
        "target_population": "Test target population",
        "study_area": "Authorized test area",
        "field_season": "2026",
    }
    config["design"]["sample_size_justification"] = "Locked power-analysis report TEST-POWER-01"
    config["design"]["observer_blinding_implementation"] = (
        "Behaviour scorers work on a separate observation vessel, receive neutral "
        "trial-start cues, and cannot access playback audio, operator communications, "
        "conditions, or the master archive."
    )
    config["approvals"] = {
        "jurisdiction": "Test jurisdiction",
        "marine_mammal_authorization_id": "TEST-PERMIT-01",
        "authorization_valid_through": "2099-12-31",
        "animal_ethics_id": "TEST-WELFARE-01",
        "stimulus_rights_approval_id": "TEST-RIGHTS-01",
        "species_at_risk_authorization_id": "not applicable",
        "verified_by": "Test Permit Officer, 2026-07-01",
    }
    config["calibration"] = {
        "playback_recorder_model": "Test Recorder",
        "amplifier_model": "Test Amplifier",
        "transducer_model": "Test Underwater Transducer",
        "transducer_depth_m": "8",
        "monitor_hydrophone_model": "Test Calibrated Hydrophone",
        "monitor_hydrophone_certificate": "TEST-CAL-CERT-01",
        "calibration_date": "2026-07-01",
        "calibration_distance_m": "1",
        "permit_approved_source_level_db_re_1upa_at_1m": "145",
        "nominal_source_level_db_re_1upa_at_1m": "145",
        "source_level_tolerance_db": "0.5",
        "fixed_player_gain_setting": "locked-test-gain",
        "received_level_monitoring_method": "Calibrated monitor recording for every exposure",
        "transducer_frequency_response_check": "TEST-FREQUENCY-RESPONSE-01",
        "calibration_recording_sha256": "a" * 64,
        "per_file_source_level_db_re_1upa_at_1m": {},
    }
    config["safety"]["stop_rule_authority"] = "Test welfare observer and principal investigator"
    config["release"] = {
        "pi_signoff": "Test Principal Investigator, 2026-07-02",
        "acoustic_lead_signoff": "Test Acoustic Lead, 2026-07-02",
        "animal_welfare_signoff": "Test Welfare Lead, 2026-07-02",
        "matched_control_review_reference": "TEST-MATCHED-REVIEW-01",
        "approved_matched_control_sha256": {},
    }

    stimuli = []
    for index in range(3):
        pair_id = f"PAIR-{index + 1}"
        for condition, context, offset in (
            ("CONTENT_A", "context-a", 0.0),
            ("CONTENT_B", "context-b", 35.0),
        ):
            stimulus_id = f"{condition}-{index + 1}"
            audio = tmp_path / f"{stimulus_id}.wav"
            write_test_wav(audio, 700.0 + index * 90.0 + offset, phase=index * 0.2)
            stimuli.append(
                {
                    "stimulus_id": stimulus_id,
                    "condition": condition,
                    "file": audio.name,
                    "independent_exemplar_id": f"EX-{condition}-{index + 1}",
                    "source_session_id": f"SESSION-{condition}-{index + 1}",
                    "caller_or_group_id": "TEST-CALLER-GROUP",
                    "pod_id": "TEST-POD",
                    "recording_date_utc": (
                        f"2025-06-{index + 1 + (10 if condition == 'CONTENT_B' else 0):02d}"
                    ),
                    "recording_location": "Authorized archive location",
                    "behaviour_context": context,
                    "context_annotation_source": (
                        "Independent visual ethogram reviewed before playback"
                    ),
                    "context_annotation_locked_before_playback": True,
                    "rights_basis": "TEST-RIGHTS-01",
                    "expert_reviewer": "Target Population Expert",
                    "pair_id": pair_id,
                    "natural_sequence": True,
                    "expert_approved": True,
                }
            )
    config["stimuli"] = stimuli
    return config


def approve_matched_controls(config: dict, rows: list[dict], tmp_path: Path) -> None:
    approvals = {}
    for row in rows:
        control_id, samples, rate = builder.matched_control_for_item(config, row)
        path = tmp_path / f"approved-{control_id}.wav"
        builder.write_pcm24(path, samples, rate)
        approvals[control_id] = builder.sha256_file(path)
    config["release"]["approved_matched_control_sha256"] = approvals
    all_ids = {str(row["stimulus_id"]) for row in rows} | set(approvals)
    config["calibration"]["per_file_source_level_db_re_1upa_at_1m"] = {
        stimulus_id: 145.0 for stimulus_id in all_ids
    }


def test_review_package_is_explicitly_non_broadcast(tmp_path: Path) -> None:
    config_path = ROOT / "field_playback" / "field_config.example.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config["catalogue_audit_dir"] = "../data/playback/definitely_missing_ci_catalogue"
    issues = builder.validate_top_level(config)
    stimuli, stimulus_issues = builder.validate_stimuli(config, config_path)
    output = tmp_path / "review.zip"
    builder.write_package(
        config,
        config_path,
        output,
        stimuli,
        issues + stimulus_issues,
        builder.audit_catalogue(config, config_path),
    )

    with zipfile.ZipFile(output) as archive:
        names = set(archive.namelist())
        assert "DO_NOT_BROADCAST.txt" in names
        assert "catalogue_audio_audit.csv" in names
        audit_header = archive.read("catalogue_audio_audit.csv").decode("utf-8").splitlines()[0]
        assert audit_header.startswith("path,sha256,sample_rate_hz")
        assert not any(name.startswith("audio/") for name in names)
        report = json.loads(archive.read("validation_report.json"))
        assert report["status"] == "REVIEW_ONLY"
        manifest_header = archive.read("stimulus_manifest.csv").decode("utf-8").splitlines()[0]
        assert "stimulus_id" in manifest_header


def test_field_package_requires_hash_approval_and_preserves_blinding(tmp_path: Path) -> None:
    config = field_config(tmp_path)
    config_path = tmp_path / "field_config.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    rows, stimulus_issues = builder.validate_stimuli(config, config_path)
    assert not [issue for issue in stimulus_issues if issue.severity == "error"]
    missing = builder.validate_matched_control_approvals(config, rows)
    assert {issue.code for issue in missing} == {"matched_control_hash_approvals_missing"}

    approve_matched_controls(config, rows, tmp_path)
    config_path.write_text(json.dumps(config), encoding="utf-8")
    issues = (
        builder.validate_top_level(config)
        + stimulus_issues
        + builder.validate_matched_control_approvals(config, rows)
        + builder.validate_per_file_calibration(config, rows)
    )
    assert not [issue for issue in issues if issue.severity == "error"]

    output = tmp_path / "field.zip"
    builder.write_package(config, config_path, output, rows, issues, [])
    with zipfile.ZipFile(output) as archive:
        names = set(archive.namelist())
        assert "DO_NOT_BROADCAST.txt" not in names
        assert len([name for name in names if name.startswith("audio/natural_sequences/")]) == 6
        assert len([name for name in names if name.startswith("audio/matched_noise/")]) == 6
        assert json.loads(archive.read("validation_report.json"))["status"] == "FIELD_CONFIG_PASS"
        assert "FIELD_AUTHORIZATION_NOTICE.txt" in names
        notice = archive.read("FIELD_AUTHORIZATION_NOTICE.txt").decode("utf-8")
        assert "not authorization to broadcast" in notice.lower()

        observer_header = next(
            csv.reader(
                io.StringIO(archive.read("observer/observer_scoring_sheet.csv").decode("utf-8"))
            )
        )
        assert "blind_code" in observer_header
        assert "experimental_unit_id" in observer_header
        assert "condition" not in observer_header
        assert "stimulus_id" not in observer_header

        operator_header = next(
            csv.reader(
                io.StringIO(archive.read("restricted/operator_run_sheet.csv").decode("utf-8"))
            )
        )
        assert "condition" in operator_header
        assert "stimulus_id" in operator_header
        assert "DISTRIBUTION_README.txt" in names

        manifest = list(
            csv.DictReader(io.StringIO(archive.read("stimulus_manifest.csv").decode("utf-8")))
        )
        controls = [row for row in manifest if row["condition"] == "MATCHED_NOISE"]
        assert len(controls) == 6
        assert all(row["expert_approved"] == "True" for row in controls)
        assert all(row["approval_reference"] == "TEST-MATCHED-REVIEW-01" for row in controls)

        checksum_lines = archive.read("checksums.sha256").decode("ascii").splitlines()
        for line in checksum_lines:
            digest, name = line.split("  ", 1)
            assert builder.hashlib.sha256(archive.read(name)).hexdigest() == digest

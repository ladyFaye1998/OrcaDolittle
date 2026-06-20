#!/usr/bin/env python3
"""Local (Windows) DTAG audio -> communicative-call clip extractor, fully automated.

Why this exists: the killer-whale `.dtg` files in the Holt 2024 deposits are the
**DTAG-2** archive format (file magic `DTAG 2.0`). They are *not* the public X3
archive format (a byte scan finds no standard X3 frames), so the open `tagtools`
(Matlab/R/Octave) and the psiphi75 X3 toolbox cannot decode them — those tools only
read files *after* decompression. The only program that decodes a DTAG-2 `.dtg` is
the closed-source `ffsrdall.exe` (DTAG-3 `.dtg` use `d3read.exe`). Both are Windows
console programs that read the keyboard directly (conio), so they ignore pipes and
cannot be driven on a headless Colab VM. This script drives them automatically on
Windows by attaching to the program's console and injecting keystrokes (no typing),
then detects communicative calls and cuts the tiny clips the Colab notebook consumes.

The DTAG-2 extractor `ffsrdall.exe` (FFSRD v1.06, Mark Johnson, Jan 2008) lives in the
repo at `tools/ffsrdall.exe` (provenance in `tools/ffsrdall.PROVENANCE.txt`). This
script finds it there automatically, so no manual copy is needed. It has been verified
end to end on native Windows: it decodes a DTAG-2 `.dtg` to a 2-channel 192 kHz WAV
(plus a `.swv` sensor stream) with 0 bad chunks, driven with zero human keystrokes.

One-command run (downloads .dtg, decodes, clips, manifests):
  python scripts/dtag_local_extract.py --auto C:\\dtag\\oo09_237d --deployments oo09_237d
  # then upload C:\\dtag\\oo09_237d\\clips\\ to MyDrive/OrcaDolittle_context/clips/ and
  # clips_manifest.json to MyDrive/OrcaDolittle_context/detections/, and run the
  # notebook (Drive mounted, DOWNLOAD_DTG=False) from the ingest cell onward.

Staged alternative:
  python scripts/dtag_local_extract.py --fetch-dir C:\\dtag\\oo09_237d --deployments oo09_237d
  python scripts/dtag_local_extract.py --decode-dir C:\\dtag\\oo09_237d --deployments oo09_237d
  python scripts/dtag_local_extract.py --wav-dir C:\\dtag\\oo09_237d --out C:\\dtag\\oo09_237d\\clips --deployments oo09_237d

Detection is intentionally identical to the notebook's `detect_calls_wav`.
References: [@tennessen2019; @holt2024masking; @bergler2019orcaspot].
"""

from __future__ import annotations

import argparse
import glob
import io
import json
import os
import subprocess
import sys
import time
import urllib.request
import zipfile
from pathlib import Path

# Detection settings (keep in lock-step with the notebook's config cell).
CALL_BAND = (500, 10000)     # Hz; pulsed-call energy band
CLICK_BAND_HI = 12000        # Hz; >this dominating => echolocation click
DET_MIN_S, DET_MAX_S = 0.10, 8.0
DET_SNR_DB = 8.0
TARGET_SR = 16000

DEFAULT_DEPLOYMENTS = ["oo09_237d", "oo09_235a", "oo10_256a"]

# DTAG-3 tools (d3read.exe) come in this bundle; the browser UA bypasses the
# cookie-consent HTML page. The DTAG-2 ffsrdall.exe is NOT mirrored and must be
# supplied by the user (see the module docstring).
D3_URLS = ["https://soundtags.wp.st-andrews.ac.uk/files/2013/01/d3usb_6nov13.zip",
           "https://soundtags.wp.st-andrews.ac.uk/files/2013/01/d3usb.zip"]
ZEN_AUDIO = ["13333019", "13328931"]   # DTAG audio deposits (2009-10, 2011-14)
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
      "Referer": "https://soundtags.wp.st-andrews.ac.uk/dtags/dtag-2/", "Accept": "*/*"}

EXTRACTORS = ("ffsrdall.exe", "d3read.exe")  # preferred order (these files are DTAG-2)
# Repo-bundled extractor: ../../tools/ffsrdall.exe relative to this script.
REPO_TOOLS = Path(__file__).resolve().parent.parent.parent / "tools"


def find_extractor(work: Path) -> "Path | None":
    """Locate the DTAG-2 extractor. These killer-whale .dtg are DTAG-2, so we ALWAYS
    prefer ffsrdall.exe (a stray d3read.exe in the work dir is DTAG-3 and silently
    produces no WAV from these files). Order: ffsrdall in work dir -> repo-bundled
    ffsrdall (copied next to the .dtg, as FFSRD expects) -> d3read only as last resort."""
    if (work / "ffsrdall.exe").exists():
        return work / "ffsrdall.exe"
    bundled = REPO_TOOLS / "ffsrdall.exe"
    if bundled.exists():
        import shutil
        dest = work / "ffsrdall.exe"
        shutil.copy2(bundled, dest)
        return dest
    if (work / "d3read.exe").exists():
        return work / "d3read.exe"
    return None


def _get(url, timeout=600):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def fetch_d3read(dest_dir: Path) -> None:
    """Download d3read.exe (DTAG-3 only). DTAG-2 .dtg need ffsrdall.exe instead."""
    target = dest_dir / "d3read.exe"
    if target.exists():
        return
    for u in D3_URLS:
        try:
            data = _get(u, timeout=300)
        except Exception as e:
            print(f"  fetch error {u} -> {e}")
            continue
        if data[:2] != b"PK":
            continue
        z = zipfile.ZipFile(io.BytesIO(data))
        for want in ("d3read.exe", "libexpat.dll"):
            m = next((n for n in z.namelist() if n.lower().endswith(want)), None)
            if m:
                (dest_dir / want).write_bytes(z.read(m))
        if target.exists():
            print(f"  saved d3read.exe ({target.stat().st_size} B) [DTAG-3 only]")
            return


def _download_one(k, url, size, dest_dir: Path, log=print) -> bool:
    """Download one .dtg with HTTP-Range resume + retry. Zenodo throttles a single
    stream to a few hundred KB/s, so callers run several of these concurrently to lift
    aggregate throughput; each is independently resumable across retries and restarts."""
    dest = dest_dir / k
    if dest.exists() and dest.stat().st_size > 0 and (not size or dest.stat().st_size >= size):
        log(f"    cached {k}")
        return True
    tmp = dest.with_suffix(dest.suffix + ".part")
    for attempt in range(1, 9):
        have = tmp.stat().st_size if tmp.exists() else 0
        if size and have >= size:
            break
        hdr = dict(UA)
        if have:
            hdr["Range"] = f"bytes={have}-"
        try:
            req = urllib.request.Request(url, headers=hdr)
            with urllib.request.urlopen(req, timeout=90) as r, open(tmp, "ab" if have else "wb") as fh:
                while True:
                    chunk = r.read(1 << 20)
                    if not chunk:
                        break
                    fh.write(chunk)
            if not size or tmp.stat().st_size >= size:
                break
        except Exception as e:
            wait = min(30, 3 * attempt)
            log(f"    {k}: attempt {attempt} stalled ({type(e).__name__}); resume in {wait}s "
                f"(have {tmp.stat().st_size if tmp.exists() else 0}/{size} B)")
            time.sleep(wait)
    if tmp.exists() and (not size or tmp.stat().st_size >= size):
        tmp.replace(dest)
        log(f"    done {k} ({dest.stat().st_size} B)")
        return True
    log(f"    FAILED {k} after retries")
    return False


def fetch_dtg(dest_dir: Path, deployments, workers: int = 4) -> None:
    """Download every .dtg whose name starts with a selected deployment id, several at a
    time (Zenodo throttles each connection, so concurrency is what gives real speed)."""
    from concurrent.futures import ThreadPoolExecutor

    index = {}
    for rec in ZEN_AUDIO:
        meta = json.loads(_get(f"https://zenodo.org/api/records/{rec}", timeout=120))
        for f in meta.get("files", []):
            key = f.get("key") or f.get("filename")
            link = (f.get("links", {}) or {}).get("self") or f.get("download")
            index[key] = (link, f.get("size", 0))
    want = sorted(k for k in index if k.endswith(".dtg")
                  and any(k.startswith(d) for d in deployments))
    gb = sum(index[k][1] for k in want) / 1e9
    print(f"  {len(want)} .dtg to fetch (~{gb:.1f} GB), {workers} parallel")
    with ThreadPoolExecutor(max_workers=workers) as ex:
        list(ex.map(lambda k: _download_one(k, index[k][0], index[k][1], dest_dir, print), want))


# --------------------------------------------------------------------------- #
# Auto-driver: run an interactive console extractor with NO human keystrokes.
# Works only on Windows (uses kernel32 console APIs). Proven against d3read.exe;
# the prompt matcher also covers ffsrdall.exe's documented prompts.
# --------------------------------------------------------------------------- #
def _drive_extractor(exe: Path, work: Path, prefix: str, log) -> bool:
    import ctypes
    import ctypes.wintypes as wt

    k = ctypes.WinDLL("kernel32", use_last_error=True)
    CREATE_NEW_CONSOLE = 0x00000010
    GENERIC_READ, GENERIC_WRITE = 0x80000000, 0x40000000
    FILE_SHARE_RW = 0x1 | 0x2
    OPEN_EXISTING = 3
    INVALID = wt.HANDLE(-1).value
    # Proper restypes so 64-bit HANDLEs are not truncated to int.
    k.CreateFileW.restype = wt.HANDLE
    k.CreateFileW.argtypes = [wt.LPCWSTR, wt.DWORD, wt.DWORD, ctypes.c_void_p,
                              wt.DWORD, wt.DWORD, wt.HANDLE]

    # The console screen/input buffers of the *attached* child are read via CONOUT$
    # / CONIN$ opened AFTER AttachConsole. Relying on GetStdHandle here is wrong: when
    # this process's stdout is redirected to a file (as under CI or a redirected console), the std
    # handles point at that file, not the child console, and every read returns empty.
    con = {"in": None, "out": None}

    class COORD(ctypes.Structure):
        _fields_ = [("X", ctypes.c_short), ("Y", ctypes.c_short)]

    class SR(ctypes.Structure):
        _fields_ = [("L", ctypes.c_short), ("T", ctypes.c_short),
                    ("R", ctypes.c_short), ("B", ctypes.c_short)]

    class CSBI(ctypes.Structure):
        _fields_ = [("dwSize", COORD), ("dwCursorPosition", COORD),
                    ("wAttributes", ctypes.c_ushort), ("srWindow", SR),
                    ("dwMaximumWindowSize", COORD)]

    class CU(ctypes.Union):
        _fields_ = [("UnicodeChar", ctypes.c_wchar), ("AsciiChar", ctypes.c_char)]

    class KER(ctypes.Structure):
        _fields_ = [("bKeyDown", ctypes.c_int), ("wRepeatCount", ctypes.c_ushort),
                    ("wVirtualKeyCode", ctypes.c_ushort),
                    ("wVirtualScanCode", ctypes.c_ushort),
                    ("uChar", CU), ("dwControlKeyState", ctypes.c_uint)]

    class IEU(ctypes.Union):
        _fields_ = [("KeyEvent", KER)]

    class IR(ctypes.Structure):
        _fields_ = [("EventType", ctypes.c_ushort), ("Event", IEU)]

    def cursor_line():
        h = con["out"]
        if not h:
            return ""
        info = CSBI()
        if not k.GetConsoleScreenBufferInfo(h, ctypes.byref(info)):
            return ""
        w = info.dwSize.X
        cy = info.dwCursorPosition.Y
        buf = ctypes.create_unicode_buffer(w)
        n = wt.DWORD(0)
        k.ReadConsoleOutputCharacterW(h, buf, w, COORD(0, cy), ctypes.byref(n))
        return buf.value[:n.value].strip().lower()

    def send(text):
        h = con["in"]
        recs = (IR * (len(text) * 2))()
        i = 0
        for ch in text:
            for down in (1, 0):
                recs[i].EventType = 1
                ke = recs[i].Event.KeyEvent
                ke.bKeyDown = down
                ke.wRepeatCount = 1
                ke.wVirtualKeyCode = 0x0D if ch == "\r" else 0
                ke.uChar.UnicodeChar = ch
                i += 1
        n = wt.DWORD(0)
        k.WriteConsoleInputW(h, recs, len(text) * 2, ctypes.byref(n))

    for f in glob.glob(str(work / (prefix + "*.wav"))):
        try:
            os.remove(f)
        except OSError:
            pass

    p = subprocess.Popen([str(exe)], cwd=str(work), creationflags=CREATE_NEW_CONSOLE)
    log(f"  launched {exe.name} pid {p.pid}")
    time.sleep(3)
    k.FreeConsole()
    if not k.AttachConsole(p.pid):
        log("  AttachConsole failed", ctypes.get_last_error())
        return False
    con["out"] = k.CreateFileW("CONOUT$", GENERIC_READ | GENERIC_WRITE, FILE_SHARE_RW,
                               None, OPEN_EXISTING, 0, None)
    con["in"] = k.CreateFileW("CONIN$", GENERIC_READ | GENERIC_WRITE, FILE_SHARE_RW,
                              None, OPEN_EXISTING, 0, None)
    if not con["out"] or con["out"] == INVALID or not con["in"] or con["in"] == INVALID:
        log("  could not open CONOUT$/CONIN$", ctypes.get_last_error())
        return False
    # Clear any stray keystrokes left in the shared console input buffer; otherwise a
    # leftover char (seen as 'input filename base?  d') corrupts the base name -> "no
    # files found" -> re-prompt -> stall. Flushing makes the first answer authoritative.
    try:
        k.FlushConsoleInputBuffer(con["in"])
    except Exception:
        pass

    # Answer each distinct prompt once, keyed on the cursor (active-prompt) line.
    # Matchers verified live against FFSRD v1.06 prompts (Input filename base? ->
    # Which chips...convert...A for all -> Output filename base (default...)? ->
    # Extract all data (A for all, S for sensor, default is all)?). Order + the
    # `answered` set keep the "filename base"/"default" substrings in later prompts
    # from re-firing earlier branches. The wav-present branch is LAST so it only
    # ends the loop once decoding has actually started.
    answered = set()
    t0 = time.time()
    name_sent_at = 0.0
    _dbg = os.environ.get("DTAG_DEBUG")
    _last = None
    while time.time() - t0 < 120 and p.poll() is None:
        line = cursor_line()
        if _dbg and line != _last:
            log(f"  LINE {line!r}"); _last = line
        if ("change" in line and "y/n" in line) and "chg" not in answered:
            send("n"); answered.add("chg"); time.sleep(1.5)             # d3read: keep dir (single key)
        elif ("input filename base" in line or "name of the file" in line) and time.time() - name_sent_at > 4:
            # Keyed on the *input* prompt (not "output filename base"); re-answerable on a
            # cooldown so a "no files found, try again" re-prompt gets re-sent, not stalled.
            send(prefix + "\r"); answered.add("name"); name_sent_at = time.time(); time.sleep(2)
        elif ("which" in line or "chips" in line or "convert" in line) and "sel" not in answered:
            send("a\r"); answered.add("sel"); time.sleep(2)
        elif "output" in line and "out" not in answered:
            send("\r"); answered.add("out"); time.sleep(2)             # ffsrdall: default output name
        elif ("extract all data" in line or ("extract" in line and "sensor" in line)) and "ext" not in answered:
            send("\r"); answered.add("ext"); time.sleep(2)             # ffsrdall: extract all
        elif glob.glob(str(work / (prefix + "*.wav"))):
            break                                                       # decoding has started
        else:
            time.sleep(0.5)

    # Wait for the WAV to stop growing (or the process to exit), up to ~3 hours.
    # Guard against a stall: if no WAV has appeared within 90 s of finishing the
    # prompt phase, the prompts were not accepted (or it is the wrong tool) — bail
    # instead of blocking for hours.
    prev, stable, waited_no_wav = -1, 0, 0
    for _ in range(3600):
        time.sleep(3)
        wavs = glob.glob(str(work / (prefix + "*.wav")))
        sz = max((os.path.getsize(w) for w in wavs), default=0)
        done = p.poll() is not None
        stable = stable + 1 if (sz == prev and sz > 0) else 0
        prev = sz
        if (done and sz > 0) or stable >= 5:
            break
        if done and sz == 0:
            log("  extractor exited with no WAV — wrong tool for this .dtg generation?")
            return False
        if sz == 0:
            waited_no_wav += 1
            if waited_no_wav >= 30:        # ~90 s with no WAV and process alive
                log("  no WAV after prompt phase — extractor stalled at a prompt; aborting")
                try:
                    p.terminate()
                except Exception:
                    pass
                return False
    try:
        p.terminate()
    except Exception:
        pass
    produced = glob.glob(str(work / (prefix + "*.wav")))
    log(f"  produced {len(produced)} wav(s) for {prefix}")
    return bool(produced)


def decode_dir(work: Path, deployments, log=print) -> int:
    """Decode every deployment's .dtg in `work` to .wav using the local extractor."""
    if not sys.platform.startswith("win"):
        log("Auto-decode needs Windows (console-driving uses Win32 APIs). On other "
            "OSes, decode the .dtg with ffsrdall.exe, then use --wav-dir.")
        return 1
    exe = find_extractor(work)
    if exe is None:
        log(f"No extractor in {work} or {REPO_TOOLS}. Put ffsrdall.exe (DTAG-2) in "
            f"tools/. These killer-whale .dtg are DTAG-2; d3read.exe will NOT decode them.")
        return 1
    log(f"Using extractor: {exe.name}")
    ok = 0
    for dep in deployments:
        if glob.glob(str(work / (dep + "*.wav"))):
            log(f"  {dep}: wav already present, skipping")
            ok += 1
            continue
        if not glob.glob(str(work / (dep + "*.dtg"))):
            log(f"  {dep}: no .dtg found, skipping")
            continue
        if _drive_extractor(exe, work, dep, log):
            ok += 1
    log(f"Decoded {ok}/{len(deployments)} deployment(s).")
    return 0 if ok else 1


def detect_calls_wav(path, np, sf, librosa):
    """Energy detector in the pulsed-call band; rejects impulsive broadband
    clicks (too short) and segments where >12 kHz energy dominates (echolocation)."""
    info = sf.info(path)
    sr = info.samplerate
    dsr = min(sr, 32000)
    events, pos = [], 0
    for x in sf.blocks(path, blocksize=int(30 * sr), dtype="float32", always_2d=True):
        x = x.mean(axis=1)
        if sr != dsr:
            x = librosa.resample(x, orig_sr=sr, target_sr=dsr)
        hop, nfft = 256, 1024
        S = np.abs(librosa.stft(x, n_fft=nfft, hop_length=hop)) ** 2
        f = librosa.fft_frequencies(sr=dsr, n_fft=nfft)
        band = (f >= CALL_BAND[0]) & (f <= min(CALL_BAND[1], dsr / 2))
        hi = f >= min(CLICK_BAND_HI, dsr / 2 - 1)
        be, he = S[band].sum(0), S[hi].sum(0) + 1e-12
        thr = (np.median(be) + 1e-12) * 10 ** (DET_SNR_DB / 10)
        active = (be > thr) & (be > 3 * he)
        idx = np.flatnonzero(active)
        if len(idx):
            for s in np.split(idx, np.flatnonzero(np.diff(idx) > 4) + 1):
                t0 = pos / sr + s[0] * hop / dsr
                dur = (s[-1] - s[0] + 1) * hop / dsr
                if DET_MIN_S <= dur <= DET_MAX_S:
                    events.append((float(t0), float(dur)))
        pos += int(len(x) * sr / dsr)
    return events, info.frames / sr


def clip_dir(wav_dir: Path, out: Path, deployments) -> int:
    import numpy as np
    import soundfile as sf
    import librosa

    out.mkdir(parents=True, exist_ok=True)
    manifest_path = out / "clips_manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else []
    done_src = {m["src"] for m in manifest}

    def dep_of(name):
        return next((p for p in deployments if name.startswith(p)), None)

    wavs = sorted(wav_dir.glob("*.wav"))
    if not wavs:
        print(f"No WAVs in {wav_dir}. Decode the .dtg first (--decode-dir).")
        return 1

    by_dep = {}
    for w in wavs:
        dep = dep_of(w.name)
        if dep:
            by_dep.setdefault(dep, []).append(w)
        else:
            print(f"  (skip, no matching deployment prefix) {w.name}")

    total = 0
    for dep, ws in by_dep.items():
        offset = 0.0
        for w in sorted(ws):
            if w.name in done_src:
                offset += next((m.get("file_dur", 0.0) for m in manifest if m["src"] == w.name), 0.0)
                continue
            ev, fdur = detect_calls_wav(str(w), np, sf, librosa)
            for t0, dur in ev:
                clip = f"{dep}__{offset + t0:.3f}.wav"
                seg, _ = librosa.load(str(w), sr=TARGET_SR, offset=max(t0, 0.0),
                                      duration=max(dur, 1.0), mono=True)
                sf.write(str(out / clip), seg, TARGET_SR)
                manifest.append({"clip": clip, "deployment": dep,
                                 "abs_t": round(offset + t0, 3), "dur": round(dur, 3),
                                 "src": w.name, "file_dur": round(fdur, 2)})
            offset += fdur
            manifest_path.write_text(json.dumps(manifest))
            total += len(ev)
            print(f"  {w.name}: {len(ev)} calls clipped (offset {offset:.0f}s)")

    manifest_path.write_text(json.dumps(manifest))
    print(f"\nDone: {len(manifest)} clips ({total} new) -> {out}")
    print(f"Upload '{out}' to MyDrive/OrcaDolittle_context/clips/ and "
          f"'{manifest_path.name}' to MyDrive/OrcaDolittle_context/detections/, "
          f"then run the notebook from the ingest cell.")
    return 0


def process_streaming(work: Path, deployments, cleanup: bool, log=print) -> int:
    """Process ONE deployment end-to-end at a time (fetch -> decode -> clip), optionally
    deleting that deployment's raw .dtg/.wav/.swv before moving on. This bounds peak disk
    to a single deployment (tens of GB) instead of the whole ~250 GB of decoded WAVs, so
    all 23 usable deployments fit. Resumable: a `.done_<dep>` sentinel marks finished
    deployments, so a crash continues rather than restarts."""
    clips = work / "clips"
    clips.mkdir(parents=True, exist_ok=True)
    ok = 0
    for dep in deployments:
        sentinel = clips / f".done_{dep}"
        if sentinel.exists():
            log(f"== {dep}: already done, skipping ==")
            ok += 1
            continue
        log(f"== {dep}: fetch ==")
        try:
            fetch_dtg(work, [dep])
        except Exception as e:
            log(f"== {dep}: fetch error ({type(e).__name__}: {e}) — continuing ==")
            continue
        log(f"== {dep}: decode ==")
        if decode_dir(work, [dep], log) != 0:
            log(f"== {dep}: decode failed — leaving files for inspection, continuing ==")
            continue
        log(f"== {dep}: clip ==")
        clip_dir(work, clips, [dep])
        if cleanup:
            removed = 0
            for pat in (dep + "*.wav", dep + "*.swv", dep + "*.dtg"):
                for f in glob.glob(str(work / pat)):
                    try:
                        os.remove(f); removed += 1
                    except OSError:
                        pass
            log(f"== {dep}: cleaned {removed} raw file(s) ==")
        sentinel.write_text("ok")
        ok += 1
    log(f"Streaming complete: {ok}/{len(deployments)} deployment(s) -> {clips}")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--auto", help="one folder: download .dtg, auto-decode, clip, manifest")
    ap.add_argument("--cleanup", action="store_true",
                    help="with --auto: stream one deployment at a time and delete its raw "
                         ".dtg/.wav/.swv after clipping (keeps disk bounded for the full run)")
    ap.add_argument("--fetch-dir", help="download d3read.exe + the .dtg here, then stop")
    ap.add_argument("--decode-dir", help="auto-drive the local extractor on .dtg in this folder")
    ap.add_argument("--wav-dir", help="folder with decoded *.wav (clip mode)")
    ap.add_argument("--out", help="output folder for clips + manifest (clip mode)")
    ap.add_argument("--deployments", nargs="*", default=DEFAULT_DEPLOYMENTS,
                    help="deployment id prefixes (select .dtg / group WAVs / name clips)")
    args = ap.parse_args()

    if args.auto:
        d = Path(args.auto)
        d.mkdir(parents=True, exist_ok=True)
        if args.cleanup:
            return process_streaming(d, args.deployments, cleanup=True)
        print("Fetching .dtg ...")
        fetch_dtg(d, args.deployments)
        print("Auto-decoding .dtg -> wav ...")
        if decode_dir(d, args.deployments) != 0:
            return 1
        print("Cutting clips ...")
        return clip_dir(d, d / "clips", args.deployments)

    if args.fetch_dir:
        d = Path(args.fetch_dir)
        d.mkdir(parents=True, exist_ok=True)
        print("Fetching .dtg ...")
        fetch_dtg(d, args.deployments)
        print(f"\nNext: put ffsrdall.exe in {d} (these are DTAG-2), then:\n"
              f"  python scripts/dtag_local_extract.py --decode-dir \"{d}\" "
              f"--deployments {' '.join(args.deployments)}")
        return 0

    if args.decode_dir:
        return decode_dir(Path(args.decode_dir), args.deployments)

    if not args.wav_dir or not args.out:
        ap.error("use --auto, or --fetch-dir / --decode-dir / (--wav-dir + --out)")
    return clip_dir(Path(args.wav_dir), Path(args.out), args.deployments)


if __name__ == "__main__":
    raise SystemExit(main())

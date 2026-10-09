import collections
import json
import logging
import platform
import re
import subprocess
import sys
import threading
import traceback
from datetime import datetime
from pathlib import Path

'''
Bug reports, kept in the repository so they travel with git (same format as OpenDEP Control)

Each report is one Markdown file in bug_reports/ at the program folder, with a small YAML header
(status, commit, context, ...) followed by the tester's description, the last error and the recent output.
Testers save reports while testing and commit + push them with the code; nothing is sent anywhere.
After a fix, set "status" to "fixed" and "fixed_in" to the commit.

No Qt here: the window is ui/helpers/bug_report_widget_ui.py.
'''

# Program folder (next to the .exe when frozen). From source the reports go to bug_reports/ of the repository (commit
# them with the code); the installed program cannot write to its own folder (Program Files) and uses Documents
PROGRAM_FOLDER = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parents[2]
REPORTS_FOLDER = (Path.home() / "Documents" / "OpenDEP View" / "bug_reports" if getattr(sys, "frozen", False)
                  else PROGRAM_FOLDER / "bug_reports")
STATUSES = ("open", "fixed", "wont-fix")
LOG_LINES = 200
FRONT_MATTER = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n", re.DOTALL)

logger = logging.getLogger(__name__)


# Last lines written to the console (print) and to the log, kept in memory for the reports
class OutputBuffer:
    def __init__(self, capacity=LOG_LINES):
        self.lines = collections.deque(maxlen=capacity)
        self.partial = ""
        self.lock = threading.Lock()

    def add_text(self, text):
        with self.lock:
            text = self.partial + text
            *complete, self.partial = text.split("\n")
            stamp = datetime.now().strftime("%H:%M:%S")
            for line in complete:
                if line.strip():
                    self.lines.append(f"{stamp} {line}")

    def text(self):
        with self.lock:
            return "\n".join(list(self.lines) + ([self.partial] if self.partial.strip() else []))


# Stream that copies everything written to it into the buffer (stdout / stderr)
class TeeStream:
    def __init__(self, stream, buffer):
        self.stream = stream
        self.buffer = buffer

    def write(self, text):
        self.buffer.add_text(text)
        if self.stream is not None:                 # None in a windowed .exe
            try:
                return self.stream.write(text)
            except Exception:
                pass
        return len(text)

    def flush(self):
        if self.stream is not None:
            try:
                self.stream.flush()
            except Exception:
                pass

    def __getattr__(self, name):
        return getattr(self.stream, name)


class BufferHandler(logging.Handler):
    def __init__(self, buffer):
        logging.Handler.__init__(self)
        self.buffer = buffer
        self.setFormatter(logging.Formatter("[%(levelname)s] %(name)s: %(message)s"))

    def emit(self, record):
        try:
            self.buffer.add_text(self.format(record) + "\n")
        except Exception:
            pass


output_buffer = None
last_error_text = ""


# Keep the console output (print, warnings, errors) and the log records for the reports (call once, at start)
def install_output_buffer():
    global output_buffer
    if output_buffer is None:
        output_buffer = OutputBuffer()
        sys.stdout = TeeStream(sys.stdout, output_buffer)
        sys.stderr = TeeStream(sys.stderr, output_buffer)
        logging.getLogger().addHandler(BufferHandler(output_buffer))
    return output_buffer


def recent_output():
    return output_buffer.text() if output_buffer is not None else ""


# Remember the traceback of an unhandled error for the next report
def record_error(exc_type, exc_value, exc_tb):
    global last_error_text
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    last_error_text = f"[{stamp}]\n" + "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    return last_error_text


def last_error():
    return last_error_text


# Short commit of the working copy, "+ local changes" when modified ("unknown" without git)
def git_commit(folder=PROGRAM_FOLDER):
    try:
        commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=folder, capture_output=True,
                                text=True, timeout=5).stdout.strip()
        if not commit:
            return "unknown"
        dirty = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=folder,
                               capture_output=True, text=True, timeout=5).stdout.strip()
        return f"{commit} + local changes" if dirty else commit
    except (OSError, subprocess.SubprocessError):
        return "unknown"


def system_info():
    from src import __version__
    info = {"version": __version__, "os": f"{platform.system()} {platform.release()} ({platform.machine()})",
            "python": platform.python_version()}
    try:
        from PyQt6.QtCore import QT_VERSION_STR, PYQT_VERSION_STR
        info["qt"] = f"Qt {QT_VERSION_STR}, PyQt {PYQT_VERSION_STR}"
    except ImportError:
        pass
    for name in ("numpy", "matplotlib"):
        module = sys.modules.get(name)
        if module is not None:
            info[name] = str(getattr(module, "__version__", "?"))
    return info


# File-name-safe short version of a title
def slug(title, length=40):
    text = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return text[:length].rstrip("-") or "report"


# Fenced code block that survives backticks inside the text
def code_block(text):
    fence = "````" if "```" in text else "```"
    return f"{fence}text\n{text.rstrip()}\n{fence}"


# YAML header lines: strings are written as JSON strings (valid YAML), one level of nesting
def header_lines(header):
    lines = []
    for key, value in header.items():
        if isinstance(value, dict):
            lines.append(f"{key}:" if value else f"{key}: {{}}")
            lines += [f"  {k}: {json.dumps(str(v), ensure_ascii=False)}" for k, v in value.items()]
        else:
            lines.append(f"{key}: {json.dumps(str(value), ensure_ascii=False)}")
    return lines


# Save a report as <date>_<time>_<title>.md (+ .png) and return its path
# report: {"title", "steps", "expected", "actual", "error", "output", "context": {...}, "screenshot_png": bytes|None}
def save_report(report, folder=REPORTS_FOLDER, now=None):
    now = now or datetime.now()
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    stem = f"{now:%Y-%m-%d_%H%M%S}_{slug(report['title'])}"
    path = folder / f"{stem}.md"
    n = 2
    while path.exists():
        path = folder / f"{stem}-{n}.md"
        n += 1

    header = {"id": path.stem, "status": "open", "title": report["title"].strip(), "program": "OpenDEP View",
              "commit": git_commit(), "date": f"{now:%Y-%m-%d %H:%M:%S}", **system_info(),
              "context": report.get("context", {}), "fixed_in": ""}
    parts = ["---", *header_lines(header), "---", "", f"# {report['title'].strip()}", ""]
    for heading, key in (("What I did", "steps"), ("What I expected", "expected"),
                         ("What happened instead", "actual")):
        parts += [f"## {heading}", "", report.get(key, "").strip() or "_(not given)_", ""]
    if report.get("error", "").strip():
        parts += ["## Error", "", code_block(report["error"]), ""]
    if report.get("screenshot_png"):
        png = path.with_suffix(".png")
        png.write_bytes(report["screenshot_png"])
        parts += ["## Screenshot", "", f"![screenshot]({png.name})", ""]
    if report.get("output", "").strip():
        output = "\n".join(report["output"].splitlines()[-LOG_LINES:])
        parts += [f"## Console and log (last {LOG_LINES} lines)", "", code_block(output), ""]

    path.write_text("\n".join(parts), encoding="utf-8")
    logger.info("Bug report saved: %s", path)
    return path


# Top-level values of a report header ({} when missing); also reads headers written by PyYAML
def read_header(path):
    try:
        match = FRONT_MATTER.match(Path(path).read_text(encoding="utf-8"))
    except OSError:
        return {}
    if not match:
        return {}

    header = {}
    for line in match.group(1).splitlines():
        if line.startswith((" ", "\t")) or ":" not in line:
            continue
        key, value = line.split(":", 1)
        value = value.strip()
        try:
            value = json.loads(value) if value.startswith('"') else value.strip("'")
        except ValueError:
            pass
        header[key.strip()] = value
    return header


# All saved reports, newest first: [{"path", "id", "title", "status", "date"}]
def list_reports(folder=REPORTS_FOLDER):
    folder = Path(folder)
    if not folder.is_dir():
        return []

    entries = []
    for path in folder.glob("*.md"):
        header = read_header(path)
        if header:
            entries.append({"path": path, "id": str(header.get("id", path.stem)),
                            "title": str(header.get("title", path.stem)),
                            "status": str(header.get("status", "open")), "date": str(header.get("date", ""))})
    return sorted(entries, key=lambda e: e["id"], reverse=True)

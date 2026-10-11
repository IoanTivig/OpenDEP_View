import base64
import json
import os
import platform
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from src.func import bug_reports

'''
Send bug reports to the OpenDEP website (tester accounts only)

A tester signs in once with the account the OpenDEP team created for them. The website answers with a device token,
which the program keeps instead of the password. Reports are sent with that token; the website refuses and discards
everything else. The same client, with its own program key, is in every program of the suite (OpenDEP Control,
Compute, Neuralnet).

Only the standard library is used (urllib). Passwords travel only over https; plain http is accepted for a local copy
of the website (localhost) during development.

No Qt here: the window is ui/helpers/bug_report_widget_ui.py.
'''

PROGRAM_KEY = "view"                    # the website's name for this program
# The OpenDEP website. OPENDEP_BUG_SERVER overrides it (a local copy of the site, tests).
DEFAULT_SERVER = "https://opendep.org"
TIMEOUT_S = 30
LOCAL_HOSTS = ("localhost", "127.0.0.1", "::1")


# The website could not be reached or refused the request; the message is written for the tester
class UploadError(Exception):
    def __init__(self, message, status=0):
        Exception.__init__(self, message)
        self.status = status


# WEBSITE ADDRESS
def default_server():
    return os.environ.get("OPENDEP_BUG_SERVER", DEFAULT_SERVER).strip().rstrip("/")


# The address without a trailing slash; https is required except for a local copy (the password is sent)
def check_server(server):
    server = server.strip().rstrip("/")
    parts = urllib.parse.urlsplit(server)
    if parts.scheme not in ("http", "https") or not parts.hostname:
        raise UploadError("Give the address of the OpenDEP website, e.g. https://opendep.org.")
    if parts.scheme == "http" and parts.hostname not in LOCAL_HOSTS:
        raise UploadError("The website must be reached over https: your password is sent to it.")
    return server


# REQUESTS
# One JSON request; the website's own error message becomes the UploadError's
def request(method, url, data=None, token=""):
    from src import __version__
    req = urllib.request.Request(url, method=method, data=json.dumps(data).encode() if data is not None else None,
                                 headers={"Content-Type": "application/json", "Accept": "application/json",
                                          "User-Agent": f"OpenDEP-{PROGRAM_KEY}/{__version__}"})
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_S) as response:
            raw = response.read()
    except urllib.error.HTTPError as error:
        try:
            message = json.loads(error.read() or b"{}").get("error", "")
        except (ValueError, AttributeError):
            message = ""
        raise UploadError(message or f"The website answered with error {error.code}.", error.code) from error
    except (urllib.error.URLError, OSError) as error:
        raise UploadError(f"The website cannot be reached ({getattr(error, 'reason', error)}).") from error
    try:
        return json.loads(raw) if raw else {}
    except ValueError as error:
        raise UploadError("The website gave an answer this program does not understand.") from error


# How this installation appears in the team's list of tester devices
def device_name():
    from src import __version__
    return f"OpenDEP View {__version__} on {platform.node() or 'this computer'}"


# Sign in with a tester account; returns the device token to keep (the password is not kept)
def sign_in(server, username, password):
    answer = request("POST", f"{check_server(server)}/api/bugs/token",
                     {"username": username, "password": password, "device": device_name()})
    token = answer.get("token", "")
    if not token:
        raise UploadError("The website did not return a sign-in token.")
    return token


# Revoke the device token on the website (it is forgotten locally whatever happens)
def sign_out(server, token):
    try:
        request("DELETE", f"{check_server(server)}/api/bugs/token", token=token)
    except UploadError:
        pass


# The website's answer to a report: its number there, and whether it already had it (nothing stored again)
class Sent:
    def __init__(self, number, duplicate=False):
        self.number = number
        self.duplicate = duplicate

    def __eq__(self, other):
        return isinstance(other, Sent) and (self.number, self.duplicate) == (other.number, other.duplicate)

    def __repr__(self):
        return f"Sent({self.number}, {self.duplicate})"


# The website's report format from a report of the Report Bug window (the dict given to save_report), or one read
# back from its file (then with the id, version, commit and system of the program that saved it)
def report_payload(report):
    from src import __version__
    payload = {"program": PROGRAM_KEY,
               "client_id": report.get("id", ""),
               "version": report.get("version") or __version__,
               "commit": report.get("commit") or bug_reports.git_commit(),
               "title": report.get("title", "").strip(),
               "steps": report.get("steps", ""),
               "expected": report.get("expected", ""),
               "actual": report.get("actual", ""),
               "error": report.get("error", ""),
               "log": report.get("output", ""),
               "context": {str(k): str(v) for k, v in report.get("context", {}).items()},
               "system": report.get("system") or bug_reports.system_info()}
    if report.get("screenshot_png"):
        payload["screenshot"] = base64.b64encode(report["screenshot_png"]).decode("ascii")
    return payload


# Send one report. The website keeps no copy of a report it already has (the same saved file, or the same text): it
# answers with the existing number (Sent.duplicate)
def send_report(server, token, report):
    answer = request("POST", f"{check_server(server)}/api/bugs/reports", report_payload(report), token=token)
    return Sent(int(answer.get("id", 0)), bool(answer.get("duplicate")))


# Send saved reports one after the other; each one sent (or found on the website) gets its number in its header.
# Stops at a refusal that would repeat for the rest (sign-in needed, not allowed, too many reports).
# Returns per report: {"path", "title", "number", "duplicate", "error" ("" when sent), "status" (HTTP, 0 without)}
def send_saved(server, token, paths):
    results = []
    for path in paths:
        result = {"path": Path(path), "title": Path(path).stem, "number": 0, "duplicate": False, "error": "",
                  "status": 0}
        try:
            report = bug_reports.load_report(path)
            result["title"] = report["title"] or result["title"]
            sent = send_report(server, token, report)
            bug_reports.mark_sent(path, sent.number)
            result.update(number=sent.number, duplicate=sent.duplicate)
        except UploadError as e:
            result.update(error=str(e), status=e.status)
            results.append(result)
            if e.status in (401, 403, 429):
                break
            continue
        except (OSError, ValueError) as e:
            result["error"] = f"cannot read the file ({e})"
        results.append(result)
    return results


# "3 sent, 1 already on the website, 1 not sent: <reason>."
def summary(results):
    new = sum(1 for r in results if r["number"] and not r["duplicate"])
    old = sum(1 for r in results if r["duplicate"])
    failed = [r for r in results if r["error"]]
    parts = [f"{new} sent"] + ([f"{old} already on the website"] if old else [])
    if failed:
        parts.append(f"{len(failed)} not sent: {failed[-1]['error']}")
    return ", ".join(parts) + "."


# The reports this tester sent, newest first, with their status on the website
def my_reports(server, token):
    return list(request("GET", f"{check_server(server)}/api/bugs/reports", token=token).get("reports", []))

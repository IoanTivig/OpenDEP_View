import getpass
import json
import os
import re

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtNetwork import QLocalServer, QLocalSocket

'''
One OpenDEP View per user: files sent to a View that is already running

A running View listens on a local channel (QLocalServer: a named pipe on Windows, a socket file on Linux and macOS;
nothing leaves the computer). A second start of View with files (command line, double-click on a file, OpenDEP
Compute's Send to View) hands them to the running View and ends; without a running View it opens them itself.

Protocol (OpenDEP Compute uses the same, see its src/integration/view_link.py): one line of UTF-8 JSON
    {"open": ["<absolute path>", ...]}\\n
answered by the line
    {"ok": true}\\n
'''

PROTOCOL_VERSION = 1
TIMEOUT_MS = 2000


# Channel name, one per user (two users on one computer each have their own View). OPENDEP_VIEW_CHANNEL replaces
# it (tests: a channel of their own, not that of a View in use)
def server_name():
    if os.environ.get("OPENDEP_VIEW_CHANNEL"):
        return os.environ["OPENDEP_VIEW_CHANNEL"]
    try:
        user = getpass.getuser()
    except Exception:                                # no user name available: one channel for the computer
        user = "user"
    return "OpenDEP-View-" + (re.sub(r"[^A-Za-z0-9_-]", "_", user) or "user")


def encode(paths):
    return (json.dumps({"open": [str(p) for p in paths], "version": PROTOCOL_VERSION}) + "\n").encode("utf-8")


def decode(line):
    try:
        message = json.loads(line.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return []
    paths = message.get("open") if isinstance(message, dict) else None
    return [p for p in paths if isinstance(p, str)] if isinstance(paths, list) else []


# Hand files to a running View; True when one received them
def send_to_running(paths, name=None, timeout_ms=TIMEOUT_MS):
    socket = QLocalSocket()
    socket.connectToServer(name or server_name())
    if not socket.waitForConnected(timeout_ms):
        return False
    socket.write(encode(paths))
    socket.flush()
    socket.waitForBytesWritten(timeout_ms)       # False when flush() already wrote everything: only the answer counts
    ok = socket.waitForReadyRead(timeout_ms) and b'"ok": true' in bytes(socket.readAll())
    socket.disconnectFromServer()
    return ok


# The running View's end: emits files_received(list of paths) for every message
class InstanceServer(QObject):
    files_received = pyqtSignal(list)

    def __init__(self, parent=None, name=None):
        QObject.__init__(self, parent)
        self.name = name or server_name()
        self.server = QLocalServer(self)
        self.server.newConnection.connect(self.new_connection)
        self.buffers = {}

    # Start listening; a channel left over by a View that crashed is removed first. False when it fails.
    def start(self):
        if self.server.listen(self.name):
            return True
        QLocalServer.removeServer(self.name)
        return self.server.listen(self.name)

    def new_connection(self):
        while self.server.hasPendingConnections():
            socket = self.server.nextPendingConnection()
            self.buffers[socket] = b""
            socket.readyRead.connect(lambda s=socket: self.read(s))
            socket.disconnected.connect(lambda s=socket: self.closed(s))

    def closed(self, socket):
        self.buffers.pop(socket, None)
        socket.deleteLater()

    def read(self, socket):
        self.buffers[socket] = self.buffers.get(socket, b"") + bytes(socket.readAll())
        while b"\n" in self.buffers[socket]:
            line, self.buffers[socket] = self.buffers[socket].split(b"\n", 1)
            paths = decode(line)
            socket.write(b'{"ok": true}\n')
            socket.flush()
            if paths:
                self.files_received.emit(paths)

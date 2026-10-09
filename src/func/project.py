import json
import os
import re
import shutil
import zipfile
from datetime import datetime
from pathlib import Path

from src.classes.numpy_encoder import NumpyEncoder
from src.func.opendep_files import SPECTRUM_SUFFIX, CURVE_SUFFIX

'''
OpenDEP View projects

A project is ONE file, <name>.odvproject, made to be copied and sent between users (as in OpenDEP Compute, whose
projects are .odcproject files): a zip archive (any unzip tool opens it) holding
    project.json        name, order of the scatters and curves, the replicate groups (scatters with their
                        biological replicate), the links (curve -> scatter or group), view settings (graph content,
                        frequency range, styling, plots tab)
    scatters/*.odspec   one OpenDEP Spectrum file per scatter (same format as "Save scatter")
    curves/*.odcurve    one OpenDEP Curve file per curve (same format as "Save curve")
Saving writes a temporary file and then replaces the project, so an interrupted save never damages it; the previous
version is kept as <name>.odvproject.bak. A scatter or curve that cannot be read is listed in project["missing"] and
the rest opens.

Projects made before 2026-10-09 are folders with the same layout (project.json at the top; the oldest list .ods /
.odc files). They open as before; the first save writes <folder name>.odvproject next to the folder, which is left
as it is.
'''

PROJECT_SUFFIX = ".odvproject"
PROJECT_FILE = "project.json"                    # inside the archive (and at the top of an older project folder)
PROJECT_FORMAT = "OpenDEP View project"
PROJECT_VERSION = 2                              # 2: one file (zip); 1: a folder
SCATTER_FOLDER = "scatters"
CURVE_FOLDER = "curves"


class ProjectError(Exception):
    pass


# Folder of an older (folder) project, from the folder itself or its project.json; None for anything else
def project_folder(path):
    path = Path(path).absolute()
    folder = path.parent if path.name == PROJECT_FILE else path
    return folder if (folder / PROJECT_FILE).is_file() else None


# True when the path is a project file, or an older project folder
def is_project(path):
    path = Path(path)
    if path.suffix.lower() == PROJECT_SUFFIX:
        return path.is_file() and zipfile.is_zipfile(path)
    return project_folder(path) is not None


# The project file of a path: <name>.odvproject (the suffix is added when missing)
def project_file(path):
    path = Path(path).absolute()
    return path if path.suffix.lower() == PROJECT_SUFFIX else path.with_name(path.name + PROJECT_SUFFIX)


# Create a new, empty project file
def create_project(path, name=None):
    path = project_file(path)
    if path.exists():
        raise ProjectError(f"{path} exists already. Use Open project instead.")

    path.parent.mkdir(parents=True, exist_ok=True)
    project = {"name": name or path.stem, "path": str(path), "scatters": [], "curves": [], "groups": [],
               "links": [], "settings": {}}
    write_project(project)
    return project


# Read a project file, or an older project folder: its name, settings and the content of its scatter and curve
# files (in the saved order). project["converted_from"] is the folder of an older project (else None).
def read_project(path):
    folder = project_folder(path) if Path(path).suffix.lower() != PROJECT_SUFFIX else None
    if folder is not None:
        return parse_project(lambda name: (folder / name).read_bytes(), folder,
                             folder.parent / f"{folder.name}{PROJECT_SUFFIX}", converted=True)

    path = Path(path).absolute()
    if not path.is_file():
        raise ProjectError(f"{path} was not found.")
    if not zipfile.is_zipfile(path):
        raise ProjectError(f"{path.name} is not an OpenDEP View project.")
    with zipfile.ZipFile(path) as archive:
        return parse_project(archive.read, path, path, converted=False)


# The project from its parts; read(name) returns the bytes of a part ("project.json", "scatters/...")
def parse_project(read, where, path, converted):
    try:
        data = json.loads(read(PROJECT_FILE).decode("utf-8"))
    except (OSError, KeyError, ValueError) as e:
        raise ProjectError(f"{Path(where).name} is not an OpenDEP View project ({e}).")
    if data.get("format") != PROJECT_FORMAT:
        raise ProjectError(f"{Path(where).name} is not an OpenDEP View project.")

    project = {"name": data.get("name") or Path(path).stem, "path": str(path), "scatters": [], "curves": [],
               "links": [], "settings": data.get("settings", {}), "missing": [],
               "converted_from": str(where) if converted else None}
    new_index = {"scatters": {}, "curves": {}}           # saved position -> position among the parts read
    for key in ("scatters", "curves"):
        for saved_index, relative_path in enumerate(data.get(key, [])):
            try:
                project[key].append(json.loads(read(relative_path).decode("utf-8")))
                new_index[key][saved_index] = len(project[key]) - 1
            except (OSError, KeyError, ValueError):     # one damaged or missing part must not block the project
                project["missing"].append(relative_path)

    # Replicate groups: their scatters by position (missing ones are dropped)
    project["groups"] = []
    for group in data.get("groups", []):
        members = [{**m, "scatter": new_index["scatters"][m["scatter"]]} for m in group.get("members", [])
                   if m.get("scatter") in new_index["scatters"]]
        project["groups"].append({**group, "members": members})

    # Links of curves to scatters or groups, by position (those to missing parts are dropped)
    new_index["groups"] = {i: i for i in range(len(project["groups"]))}
    for link in data.get("links", []):
        if link.get("curve") not in new_index["curves"]:
            continue
        for kind, key in (("scatter", "scatters"), ("group", "groups")):
            if kind in link and link[kind] in new_index[key]:
                project["links"].append({**link, "curve": new_index["curves"][link["curve"]],
                                         kind: new_index[key][link[kind]]})
    return project


# Write the project file: a temporary archive next to it, then it replaces the project (the previous version is
# kept as .bak). An older project folder it was opened from is not touched.
# project: {"name", "path", "scatters": [scatter dict], "curves": [curve dict],
#           "groups": [{"name", "color", ..., "members": [{"scatter": index, "biological": label}]}],
#           "links": [{"curve": index, "scatter": index} or {"curve": index, "group": index}], "settings": {...}}
def write_project(project):
    path = Path(project["path"])
    parts = {}
    entries = {}
    for key, folder, suffix in (("scatters", SCATTER_FOLDER, SPECTRUM_SUFFIX), ("curves", CURVE_FOLDER, CURVE_SUFFIX)):
        entries[key] = []
        for index, item in enumerate(project[key]):
            relative_path = f"{folder}/{index + 1:03d}_{safe_file_name(item.get('name', ''))}{suffix}"
            parts[relative_path] = json.dumps(item, cls=NumpyEncoder)
            entries[key].append(relative_path)

    data = {"format": PROJECT_FORMAT,
            "version": PROJECT_VERSION,
            "name": project["name"],
            "saved": datetime.now().isoformat(timespec="seconds"),
            "scatters": entries["scatters"],
            "curves": entries["curves"],
            "groups": project.get("groups", []),
            "links": project.get("links", []),
            "settings": project.get("settings", {})}
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_file = path.with_name(path.name + ".tmp")
    with zipfile.ZipFile(temporary_file, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(PROJECT_FILE, json.dumps(data, indent=1, cls=NumpyEncoder))
        for name, text in parts.items():
            archive.writestr(name, text)
    if path.exists():
        shutil.copy2(path, path.with_name(path.name + ".bak"))
    os.replace(temporary_file, path)


# File name made from a scatter or curve name (characters Windows refuses are replaced)
def safe_file_name(name):
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", str(name)).strip(" .")
    return name[:60] or "untitled"


# Recent projects list: the new one first, no duplicates, only those that still exist (files, or older folders)
def update_recent(recent, path, max_items=8):
    items = [str(path)] + [p for p in recent if Path(p) != Path(path)]
    return [p for p in items if is_project(p)][:max_items]

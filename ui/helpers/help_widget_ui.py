import re
from pathlib import Path

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QColor, QDesktopServices, QKeySequence, QPalette, QShortcut, QTextCursor, QTextDocument
from PyQt6.QtWidgets import QWidget, QTreeWidgetItem
from PyQt6.uic import loadUi

'''
The user guide inside the program (as in OpenDEP Control)

The guide is the Markdown in docs/ (also readable on GitHub). Qt renders Markdown itself (QTextBrowser), so no build
step, browser or internet is needed: the same files work on Windows and Linux. Like ui/, docs/ is found relative to
the program's folder (the program is started from its own folder).

Help / F1 opens the page of the tab in use (HELP_PAGES, MainUI.help_page). Links between pages, "#section" links and
a full-text search work inside the window; web links open in the browser.
'''

DOCS_DIR = Path("docs")

# Table of contents: (section, [(title, page relative to docs/)])
CONTENTS = [
    ("Getting started", [
        ("Overview", "index.md"),
        ("Installation", "installation.md"),
        ("Quick start", "quickstart.md"),
    ]),
    ("User guide", [
        ("The window and projects", "user-guide/interface.md"),
        ("Curve plots", "user-guide/curve-plots.md"),
        ("Scatter plots", "user-guide/scatter-plots.md"),
        ("Group plots", "user-guide/group-plots.md"),
        ("Statistics report", "user-guide/statistics-report.md"),
        ("The graph and images", "user-guide/graph.md"),
        ("Files", "user-guide/files.md"),
    ]),
    ("Concepts", [
        ("CM factor and models", "concepts/cm-factor-and-models.md"),
        ("Replicates and averages", "concepts/replicates.md"),
        ("Separation of two populations", "concepts/separation.md"),
        ("Statistical tests", "concepts/statistics.md"),
    ]),
    ("Help", [
        ("Troubleshooting", "troubleshooting.md"),
    ]),
]

# Page for each place in the program (MainUI.help_page builds the key)
HELP_PAGES = {
    "welcome": "quickstart.md",
    "Curve plots": "user-guide/curve-plots.md",
    "Scatter plots": "user-guide/scatter-plots.md",
    "Group plots": "user-guide/group-plots.md",
}

# Markdown niceties Qt shows plainly: tables get borders and padding
_STYLE = """
h1 { font-size: 22px; font-weight: 600; }
h2 { font-size: 18px; font-weight: 600; margin-top: 16px; }
h3 { font-size: 15px; font-weight: 600; margin-top: 12px; }
table { border-collapse: collapse; margin: 6px 0; }
th, td { border: 1px solid #CBD5E1; padding: 4px 8px; }
th { background-color: #F1F5F9; }
code { background-color: #F1F5F9; }
blockquote { background-color: #F8FAFC; margin: 6px 0; }
a { color: #2563EB; }
"""


# GitHub-style heading anchor: "Start page and projects" -> "start-page-and-projects"
def slug(text):
    text = re.sub(r"[^\w\s-]", "", text.strip().lower())
    return re.sub(r"\s+", "-", text)


# User guide window: contents, search and the page. Not modal, so it can stay open next to the program.
class HelpWidgetUI(QWidget):
    def __init__(self, parent=None, docs_dir=DOCS_DIR):
        QWidget.__init__(self, parent, Qt.WindowType.Window)
        loadUi("ui/widgets/help_widget.ui", self)

        # Variables
        self.docs_dir = Path(docs_dir).resolve()
        self.search_terms = []
        self.items = {}

        # Initial setup
        self.fill_contents()
        self.qt_browser_help.document().setDefaultStyleSheet(_STYLE)
        palette = self.qt_browser_help.palette()
        palette.setColor(QPalette.ColorRole.Link, QColor("#2563EB"))
        palette.setColor(QPalette.ColorRole.LinkVisited, QColor("#2563EB"))
        self.qt_browser_help.setPalette(palette)
        self.qt_browser_help.setSearchPaths([str(self.docs_dir)])
        self.qt_splitter_help.setStretchFactor(1, 1)
        self.qt_splitter_help.setSizes([260, 840])
        self.qt_button_help_back.setEnabled(False)
        self.qt_button_help_forward.setEnabled(False)

        # Connect buttons
        self.connect_buttons()

    def connect_buttons(self):
        browser = self.qt_browser_help
        self.qt_button_help_back.clicked.connect(browser.backward)
        self.qt_button_help_forward.clicked.connect(browser.forward)
        self.qt_button_help_home.clicked.connect(lambda: self.open_page("index.md"))
        browser.backwardAvailable.connect(self.qt_button_help_back.setEnabled)
        browser.forwardAvailable.connect(self.qt_button_help_forward.setEnabled)
        browser.anchorClicked.connect(self.link_clicked)
        browser.sourceChanged.connect(self.source_changed)
        self.qt_tree_help_contents.itemClicked.connect(self.tree_item_clicked)
        self.qt_entry_help_search.textChanged.connect(self.search)
        self.qt_entry_help_search.returnPressed.connect(self.find_next)
        QShortcut(QKeySequence.StandardKey.Find, self, activated=self.qt_entry_help_search.setFocus)
        QShortcut(QKeySequence.StandardKey.FindNext, self, activated=self.find_next)
        QShortcut(QKeySequence("Alt+Left"), self, activated=browser.backward)
        QShortcut(QKeySequence("Alt+Right"), self, activated=browser.forward)

    def fill_contents(self):
        tree = self.qt_tree_help_contents
        for section, pages in CONTENTS:
            parent_item = QTreeWidgetItem([section])
            parent_item.setFlags(parent_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            font = parent_item.font(0)
            font.setBold(True)
            parent_item.setFont(0, font)
            tree.addTopLevelItem(parent_item)
            for title, page in pages:
                item = QTreeWidgetItem([title])
                item.setData(0, Qt.ItemDataRole.UserRole, page)
                parent_item.addChild(item)
                self.items[page] = item
        tree.expandAll()

    # NAVIGATION
    # Show a page ("user-guide/curve-plots.md", optionally with "#section"); the overview page when it does not exist.
    # Returns True when the page asked for was shown.
    def open_page(self, page):
        path_part, _, fragment = page.partition("#")
        path = self.docs_dir / path_part
        if not path.is_file():
            path, fragment = self.docs_dir / "index.md", ""
            if not path.is_file():
                self.qt_browser_help.setPlainText(f"The user guide was not found in {self.docs_dir}.")
                return False
        url = QUrl.fromLocalFile(str(path))
        if fragment:
            url.setFragment(fragment)
        self.qt_browser_help.setSource(url, QTextDocument.ResourceType.MarkdownResource)
        return path_part == str(path.relative_to(self.docs_dir)).replace("\\", "/")

    # Open the guide at a page and bring the window to the front
    def show_page(self, page):
        self.open_page(page)
        self.show()
        self.raise_()
        self.activateWindow()

    # Page shown now, relative to docs/ (e.g. "user-guide/curve-plots.md")
    def current_page(self):
        return self.page_of(self.qt_browser_help.source())

    def page_of(self, url):
        try:
            return str(Path(url.toLocalFile()).resolve().relative_to(self.docs_dir)).replace("\\", "/")
        except ValueError:
            return ""

    # Pages and anchors open here; web links in the browser; other files (images, examples) with their program
    def link_clicked(self, url):
        if url.scheme() in ("http", "https", "mailto"):
            QDesktopServices.openUrl(url)
            return
        if url.isRelative() and not url.path():                 # "#section" on this page
            self.scroll_to(url.fragment())
            return
        target = self.qt_browser_help.source().resolved(url)
        local = Path(target.toLocalFile())
        if local.suffix.lower() == ".md" and local.is_file():
            self.qt_browser_help.setSource(target, QTextDocument.ResourceType.MarkdownResource)
        elif local.is_file():
            QDesktopServices.openUrl(target)

    # Select the page in the contents, jump to the section, highlight the search words. Uses the URL of the signal:
    # while it is emitted, source() can still return the previous page.
    def source_changed(self, url):
        self.space_blocks()
        item = self.items.get(self.page_of(url))
        if item is not None:
            self.qt_tree_help_contents.setCurrentItem(item)
        if url.fragment():
            self.scroll_to(url.fragment())
        if self.search_terms:
            self.qt_browser_help.moveCursor(QTextCursor.MoveOperation.Start)
            self.find_next()

    # Space between paragraphs and above headings (Qt's Markdown import ignores the style sheet's margins)
    def space_blocks(self):
        cursor = QTextCursor(self.qt_browser_help.document())
        cursor.beginEditBlock()
        block = self.qt_browser_help.document().begin()
        while block.isValid():
            block_format = block.blockFormat()
            level = block_format.headingLevel()
            in_list = block.textList() is not None
            block_format.setTopMargin({1: 4, 2: 18, 3: 12}.get(level, 0 if in_list else 2))
            block_format.setBottomMargin(6 if level else 3 if in_list else 8)
            cursor.setPosition(block.position())
            cursor.setBlockFormat(block_format)
            # Links in the program's blue (the Markdown import colours them from the application palette)
            iterator = block.begin()
            while not iterator.atEnd():
                fragment = iterator.fragment()
                if fragment.isValid() and fragment.charFormat().isAnchor():
                    link_format = fragment.charFormat()
                    link_format.setForeground(QColor("#2563EB"))
                    cursor.setPosition(fragment.position())
                    cursor.setPosition(fragment.position() + fragment.length(), QTextCursor.MoveMode.KeepAnchor)
                    cursor.setCharFormat(link_format)
                iterator += 1
            block = block.next()
        cursor.endEditBlock()

    # Scroll to the heading whose GitHub-style anchor is fragment
    def scroll_to(self, fragment):
        browser = self.qt_browser_help
        block = browser.document().begin()
        while block.isValid():
            if block.blockFormat().headingLevel() > 0 and slug(block.text()) == fragment:
                browser.setTextCursor(QTextCursor(block))
                browser.verticalScrollBar().setValue(
                    int(browser.document().documentLayout().blockBoundingRect(block).top()))
                return
            block = block.next()

    def tree_item_clicked(self, item):
        page = item.data(0, Qt.ItemDataRole.UserRole)
        if page:
            self.open_page(page)

    # SEARCH
    def page_text(self, page):
        try:
            return (self.docs_dir / page).read_text(encoding="utf-8").lower()
        except OSError:
            return ""

    # Show only the pages containing every word; highlight the first match
    def search(self, text):
        self.search_terms = [word for word in text.lower().split() if word]
        matches = 0
        for page, item in self.items.items():
            hit = not self.search_terms or all(term in self.page_text(page) for term in self.search_terms)
            item.setHidden(not hit)
            matches += hit
        tree = self.qt_tree_help_contents
        for i in range(tree.topLevelItemCount()):
            section = tree.topLevelItem(i)
            section.setHidden(all(section.child(k).isHidden() for k in range(section.childCount())))
        self.qt_label_help_matches.setText(f"{matches} page{'s' if matches != 1 else ''}"
                                           if self.search_terms else "")
        current = self.items.get(self.current_page())
        if self.search_terms and current is not None and current.isHidden():
            first = next((page for page, item in self.items.items() if not item.isHidden()), None)
            if first:
                self.open_page(first)
                return
        if self.search_terms:
            self.qt_browser_help.moveCursor(QTextCursor.MoveOperation.Start)
            self.find_next()

    # Highlight the next occurrence of the first search word on the page (wraps)
    def find_next(self):
        if not self.search_terms:
            return
        word = self.search_terms[0]
        if not self.qt_browser_help.find(word):
            self.qt_browser_help.moveCursor(QTextCursor.MoveOperation.Start)
            self.qt_browser_help.find(word)

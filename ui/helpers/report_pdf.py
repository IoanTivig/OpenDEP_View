from PyQt6.QtCore import QMarginsF, QUrl
from PyQt6.QtGui import QImage, QPageLayout, QPageSize, QPdfWriter, QTextDocument


# Write an HTML report as a PDF (A4 landscape, page numbers), with its images: {resource name: PNG bytes}.
# Qt's own PDF writer: no external program, the same on Windows, Linux and macOS.
def write_pdf(html, path, images=None, title="", creator="OpenDEP View"):
    writer = QPdfWriter(str(path))
    writer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
    writer.setPageOrientation(QPageLayout.Orientation.Landscape)
    writer.setPageMargins(QMarginsF(12, 12, 12, 12), QPageLayout.Unit.Millimeter)
    writer.setResolution(150)
    writer.setTitle(title)
    writer.setCreator(creator)

    document = QTextDocument()
    document.setDocumentMargin(0)
    for name, data in (images or {}).items():
        document.addResource(QTextDocument.ResourceType.ImageResource.value, QUrl(name), QImage.fromData(data))
    document.setHtml(html)
    document.print(writer)

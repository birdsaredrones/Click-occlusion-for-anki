from aqt import mw, QFileDialog, QMessageBox
from aqt.qt import QWidget, QVBoxLayout, QLabel, QPushButton, QPixmap, QPainter, QColor, QRect, QMouseEvent
from aqt.utils import showInfo
import os
from PyQt6.QtWidgets import QLineEdit, QHBoxLayout  # Add at the top with your other imports
from PyQt6.QtGui import QKeySequence
from PyQt6.QtGui import QShortcut

class ImageOcclusionEditor(QWidget):
    def __init__(self, image_path):
        super().__init__()
        self.setWindowTitle("Click Image Occlusion Editor")
        self.image_path = image_path
        self.occlusion_boxes = []
        self.drawing = False
        self.start_point = None

        layout = QVBoxLayout()
        button_layout = QHBoxLayout()

        #undo button
        self.undo_button = QPushButton("Undo")
        self.undo_button.setToolTip("Ctrl+Z: Remove the last box you drew")
        self.undo_button.clicked.connect(self.undo_last_box)
        undo_shortcut = QShortcut(QKeySequence("Ctrl+Z"), self)
        undo_shortcut.activated.connect(self.undo_last_box)
        button_layout.addWidget(self.undo_button)

        # Header input
        self.header_input = QLineEdit()
        self.header_input.setPlaceholderText("Enter header text here...")
        self.header_input.setToolTip("This text appears at the top of the card.")
        layout.addWidget(self.header_input)

        # Extras input
        self.extra_input = QLineEdit()
        self.extra_input.setPlaceholderText("Enter answers/mnemonic here...")
        self.extra_input.setToolTip("only on the answer side")
        layout.addWidget(self.extra_input)

        #self.label = QLabel(f"Selected image: {os.path.basename(image_path)}")
        #layout.addWidget(self.label)

        self.image_label = QLabel()
        self.pixmap = QPixmap(image_path)
        self.image_label.setPixmap(self.pixmap)
        layout.addWidget(self.image_label)

        self.image_label.mousePressEvent = self.start_draw
        self.image_label.mouseMoveEvent = self.update_draw
        self.image_label.mouseReleaseEvent = self.end_draw

        #create button
        self.create_button = QPushButton("Create Card")
        self.create_button.clicked.connect(self.create_card)
        button_layout.addWidget(self.create_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)
        self.resize(self.pixmap.width() + 40, self.pixmap.height() + 140)

    def update_tooltip(self):
        self.create_button.setToolTip(f"Creates 1 card with {len(self.occlusion_boxes)} occlusions.")

    def undo_last_box(self):
        if self.occlusion_boxes:
            self.occlusion_boxes.pop()

            # Redraw pixmap with remaining boxes
            self.pixmap = QPixmap(self.image_path)
            painter = QPainter(self.pixmap)
            painter.setPen(QColor(255, 0, 0))
            fill_color = QColor(128, 128, 128, 180)  # Same grey as when drawing

            for rect in self.occlusion_boxes:
                painter.fillRect(rect, fill_color)
                painter.drawRect(rect)

            painter.end()
            self.image_label.setPixmap(self.pixmap)
            self.update_tooltip()

    def start_draw(self, event: QMouseEvent):
        self.drawing = True
        self.start_point = event.pos()

    def update_draw(self, event: QMouseEvent):
        if self.drawing:
            end_point = event.pos()
            temp_pixmap = self.pixmap.copy()
            painter = QPainter(temp_pixmap)
            painter.setPen(QColor(255, 0, 0))
            painter.setBrush(QColor(128, 128, 128, 150))  # semi-transparent grey
            painter.drawRect(QRect(self.start_point, end_point))
            painter.end()
            self.image_label.setPixmap(temp_pixmap)

    def end_draw(self, event: QMouseEvent):
        if self.drawing:
            end_point = event.pos()
            rect = QRect(self.start_point, end_point).normalized()
            self.occlusion_boxes.append(rect)
            painter = QPainter(self.pixmap)
            painter.setPen(QColor(255, 0, 0))
            painter.setBrush(QColor(128, 128, 128, 230))
            painter.drawRect(rect)
            painter.end()
            self.image_label.setPixmap(self.pixmap)
            self.drawing = False
            self.update_tooltip()

    def create_card(self):
        if not self.occlusion_boxes:
            QMessageBox.warning(self, "No Boxes", "Please draw at least one box.")
            return

        from anki.notes import Note
        from aqt import mw

        mm = mw.col.models
        model = mm.by_name("Click Occlusion")
        if not model:
            QMessageBox.critical(self, "Missing Note Type", "Click Occlusion note type not found.")
            return

        occlusion_html = ""
        for box in self.occlusion_boxes:
            x = box.x()
            y = box.y()
            w = box.width()
            h = box.height()
            occlusion_html += f'<div class="clickbox" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;"></div>\n'

        image_basename = os.path.basename(self.image_path)
        media_name = mw.col.media.add_file(self.image_path)

        image_html = f'<div class="occlusion-container" style="position:relative;">' \
                     f'<img src="{media_name}" style="max-width:100%;">\n' \
                     f'{occlusion_html}</div>'

        note = Note(mw.col, model)
        note["Image"] = image_html
        note["Answer"] = self.extra_input.text()
        note["Header"] = self.header_input.text()  # Set the header field

        deck_id = mw.col.decks.current()["id"]
        mw.col.add_note(note, deck_id)

        mw.col.autosave()
        mw.reset()

        showInfo(f"Created 1 card with {len(self.occlusion_boxes)} occlusions.")
        self.close()


from PyQt6.QtGui import QGuiApplication, QImage, QPixmap

def launch_editor():
    clipboard = QGuiApplication.clipboard()
    mime_data = clipboard.mimeData()

    if mime_data.hasImage():
        image = clipboard.image()
        if not image.isNull():
            # Save clipboard image to a temporary file
            from tempfile import NamedTemporaryFile
            temp_file = NamedTemporaryFile(delete=False, suffix=".png")
            image.save(temp_file.name, "PNG")
            editor = ImageOcclusionEditor(temp_file.name)
            editor.show()
            return

    # Fallback to file picker if no image in clipboard
    file_dialog = QFileDialog()
    file_path, _ = file_dialog.getOpenFileName(
        parent=mw,
        caption="Select an image",
        filter="Images (*.png *.jpg *.jpeg)"
    )
    if file_path:
        editor = ImageOcclusionEditor(file_path)
        editor.show()

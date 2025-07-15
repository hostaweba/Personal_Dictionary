import sys
import os
import json
import markdown
from datetime import datetime, timedelta
from collections import defaultdict
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QListWidget,
    QTextBrowser, QPushButton, QInputDialog, QMessageBox, QLineEdit,
    QDialog, QLabel, QTextEdit, QDialogButtonBox, QFileDialog, QGridLayout
)
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QFont, QTextCursor, QShortcut, QKeySequence, QIcon








DATA_FILE = "data/word_data.json"
PROGRESS_FILE = "data/progress_log.json"


def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def log_progress(action):
    log = defaultdict(lambda: {"added": 0, "viewed": 0})
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
            log.update(json.load(f))

    today = datetime.now().strftime("%Y-%m-%d")
    if today not in log:
        log[today] = {"added": 0, "viewed": 0}
    log[today][action] += 1

    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(log, f, indent=2)

def convert_to_html(md_text, dark=False):
    body = markdown.markdown(md_text, extensions=["tables", "fenced_code"])

    style = f"""
        body {{
            font-family: 'Segoe UI', sans-serif;
            font-size: 16px;
            line-height: 1.7;
            background-color: {'#121212' if dark else '#fdfdfd'};
            color: {'#e0e0e0' if dark else '#222'};
            padding: 16px;
        }}

        table {{
            border-collapse: separate;
            border-spacing: 0;
            width: 100%;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        }}
        th, td {{
            border: 1px solid {'#444' if dark else '#ccc'};
            padding: 10px;
            text-align: left;
            background-color: {'#222' if dark else '#ffffff88'};
        }}
        th {{
            background: linear-gradient(to right, {'#333' if dark else '#f5f5f5'}, {'#444' if dark else '#e0e0e0'});
            font-weight: bold;
            color: {'#fafafa' if dark else '#222'};
        }}

        code {{
            background-color: {'#2e2e2e' if dark else '#f0f0f0'};
            padding: 3px 6px;
            border-radius: 4px;
            color: {'#ffeb3b' if dark else '#d32f2f'};
        }}

        img {{
            max-width: 100%;
            height: auto;
            margin: 12px 0;
            border: 2px solid {'#555' if dark else '#ccc'};
            border-radius: 6px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
        }}

        h1, h2, h3 {{
            color: {'#90caf9' if dark else '#1565c0'};
            border-bottom: 1px solid {'#555' if dark else '#ccc'};
            padding-bottom: 6px;
            margin-top: 24px;
            text-shadow: 0px 1px 1px rgba(0,0,0,0.1);
        }}

        ul {{
            padding-left: 24px;
            margin-bottom: 10px;
        }}

        li {{
            margin-bottom: 6px;
            line-height: 1.5;
        }}

        blockquote {{
            border-left: 4px solid {'#66bb6a' if dark else '#4caf50'};
            padding-left: 12px;
            margin-left: 0;
            color: {'#a5d6a7' if dark else '#2e7d32'};
            background-color: {'#1b1b1b' if dark else '#f1f8e9'};
        }}

        strong {{
            color: {'#f48fb1' if dark else '#c2185b'};
        }}
    """

    return f"<html><head><style>{style}</style></head><body>{body}</body></html>"

class EditDialog(QDialog):
    def __init__(self, word, text="", parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"📝 Edit Explanation for '{word}'")
        self.resize(600, 450)
        self.setMinimumSize(500, 350)

        layout = QVBoxLayout(self)
        self.label = QLabel(f"Explanation for: <b>{word}</b>")
        self.editor = QTextEdit()
        self.editor.setText(text)
        self.editor.setFont(QFont("Consolas", 11))
        self.editor.setAcceptRichText(False)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        layout.addWidget(self.label)
        layout.addWidget(self.editor)
        layout.addWidget(self.buttons)

    def get_text(self):
        return self.editor.toPlainText()




class ProgressDialog(QDialog):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📊 Full Progress History")
        self.resize(600, 500)
        self.setMinimumSize(500, 400)

        layout = QVBoxLayout(self)

        text = QTextEdit()
        text.setReadOnly(True)
        text.setFont(QFont("Segoe UI", 11))

        # Detect dark mode from parent
        dark = getattr(parent, 'dark_mode', False)
        bg_color = "#1e1e1e" if dark else "#ffffff"
        text_color = "#e0e0e0" if dark else "#222"
        accent = "#90caf9" if dark else "#1565c0"

        text.setStyleSheet(f"""
            QTextEdit {{
                background: {bg_color};
                color: {text_color};
                border: none;
                padding: 12px;
            }}
        """)

        # Build HTML summary
        lines = [f"<h2 style='color:{accent}'>📘 Full Activity Log</h2><br>"]
        total_added = total_viewed = 0

        for date in sorted(data.keys()):
            stats = data[date]
            added = stats.get("added", 0)
            viewed = stats.get("viewed", 0)
            total_added += added
            total_viewed += viewed

            lines.append(
                f"<span style='color:{accent}'>{date}</span> → "
                f"<b style='color:#66bb6a'>Added:</b> {added} | "
                f"<b style='color:#f06292'>Viewed:</b> {viewed}<br>"
            )

        # Final totals
        lines.append("<br><hr>")
        lines.append(f"<p><b style='color:{accent}'>📊 Total Added:</b> {total_added}</p>")
        lines.append(f"<p><b style='color:{accent}'>👁️ Total Viewed:</b> {total_viewed}</p>")

        text.setHtml("".join(lines))
        layout.addWidget(text)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignRight)





class DictionaryApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Personal Dictionary")
        self.resize(950, 550)
        self.setMinimumSize(700, 500)
        
        # Set the icon (make sure the path is correct and the file exists)
        icon = QIcon("data/icon.png")
        self.setWindowIcon(icon)



        

        self.word_data = load_data()
        self.dark_mode = False

        self.init_ui()

    def init_ui(self):
    

    
        # --- Layouts ---
        main_layout = QHBoxLayout(self)
        left_layout = QVBoxLayout()
        right_layout = QVBoxLayout()

        # --- Search Box ---
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("🔍 Search word...")
        self.search_box.textChanged.connect(self.filter_words)

        # --- Word List ---
        self.word_list = QListWidget()
        self.word_list.itemClicked.connect(self.display_explanation)
        self.word_list.setFocusPolicy(Qt.StrongFocus)
        self.word_list.setCurrentRow(0)
        self.word_list.keyPressEvent = self.handle_key_press

        # --- Word Display Area ---
        self.text_browser = QTextBrowser()
        self.text_browser.setFont(QFont("Segoe UI", 12))
        self.text_browser.setOpenExternalLinks(True)
        self.text_browser.setOpenLinks(True)
        self.text_browser.setLineWrapMode(QTextBrowser.WidgetWidth)
        self.text_browser.keyPressEvent = self.text_browser_key_event

        # --- Buttons ---
        self.add_button = self.create_button("➕ Add Word", self.add_word, "➕ Add Word (Ctrl+N)")
        self.edit_button = self.create_button("✏️ Edit Word", self.edit_word, "✏️ Edit Word (Ctrl+E)")
        self.delete_button = self.create_button("🗑️ Delete Word", self.delete_word, "🗑️ Delete Word (Del)")
        self.dark_button = self.create_button("🌓 Toggle Dark Mode", self.toggle_dark_mode, "🌓 Toggle Dark Mode (Ctrl+D)")
        self.progress_button = self.create_button("📊 Show Progress", self.show_progress, "📊 Show Progress (Ctrl+P)")
        self.help_button = self.create_button("❓ Help", self.show_help, "❓ Show Help (F1 / Ctrl+H)")

        # --- Button Grid Layout (3 rows x 2 columns) ---
        button_grid = QGridLayout()
        button_grid.setSpacing(10)
        button_grid.addWidget(self.add_button,     0, 0)
        button_grid.addWidget(self.edit_button,    0, 1)
        button_grid.addWidget(self.delete_button,  1, 0)
        button_grid.addWidget(self.dark_button,    1, 1)
        button_grid.addWidget(self.progress_button,2, 0)
        button_grid.addWidget(self.help_button,    2, 1)

        button_widget = QWidget()
        button_widget.setLayout(button_grid)

        # --- Assemble Left Layout ---
        left_layout.addWidget(self.search_box)
        left_layout.addWidget(self.word_list)
        button_widget.setSizePolicy(QPushButton().sizePolicy())  # Ensures it's not stretched
        left_layout.addWidget(button_widget, alignment=Qt.AlignBottom)

        # --- Assemble Right Layout ---
        right_layout.addWidget(self.text_browser)

        # --- Combine Layouts ---
        main_layout.addLayout(left_layout, 2)
        main_layout.addLayout(right_layout, 5)
        self.setLayout(main_layout)

        # --- Shortcuts ---
        self.init_shortcuts()

        # --- Final Setup ---
        self.refresh_word_list()
        self.word_list.setFocus()

    def create_button(self, text, slot, tooltip):
        button = QPushButton(text)
        button.clicked.connect(slot)
        button.setToolTip(tooltip)
        return button

    def init_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+M"), self, self.text_browser.setFocus)   
        QShortcut(QKeySequence("Ctrl+F"), self, self.search_box.setFocus)
        QShortcut(QKeySequence("Ctrl+N"), self, self.add_word)
        QShortcut(QKeySequence("Ctrl+E"), self, self.edit_word)
        QShortcut(QKeySequence("Delete"), self, self.delete_word)
        QShortcut(QKeySequence("Ctrl+D"), self, self.toggle_dark_mode)
        QShortcut(QKeySequence("Ctrl+P"), self, self.show_progress)
        QShortcut(QKeySequence("Ctrl+Q"), self, self.close)
        QShortcut(QKeySequence("F1"), self, self.show_help)
        QShortcut(QKeySequence("Ctrl+H"), self, self.show_help)
        QShortcut(QKeySequence("Ctrl+L"), self, self.word_list.setFocus)


    def show_help(self):
        help_text = """
        <h2>Keyboard Shortcuts</h2>
        <ul>
          <li><b>Ctrl+F</b> – Focus search bar</li>
          <li><b>Ctrl+L</b> – Focus word list</li>
          <li><b>Ctrl+M</b> – Focus explanation view</li>
          <li><b>Enter</b> – Show explanation for selected word</li>
          <li><b>Backspace</b> – Focus search bar from explanation</li>
          <li><b>Ctrl+N</b> – Add new word</li>
          <li><b>Ctrl+E</b> – Edit selected word</li>
          <li><b>Delete</b> – Delete selected word</li>
          <li><b>Ctrl+D</b> – Toggle dark mode</li>
          <li><b>Ctrl+P</b> – Show progress</li>
          <li><b>Ctrl+Q</b> – Quit app</li>
          <li><b>F1 / Ctrl+H</b> – Show this help</li>
        </ul>
        """
        QMessageBox.information(self, "📘 Help", help_text)

        
    def handle_key_press(self, event):
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            item = self.word_list.currentItem()
            if item:
                self.display_explanation(item)
        else:
            QListWidget.keyPressEvent(self.word_list, event)
            
            
    def text_browser_key_event(self, event):
        if event.key() == Qt.Key_Backspace:
            self.search_box.setFocus()
        else:
            QTextBrowser.keyPressEvent(self.text_browser, event)
            
        
        

    def refresh_word_list(self):
        self.word_list.clear()
        for word in sorted(self.word_data.keys()):
            self.word_list.addItem(word)

    def filter_words(self):
        query = self.search_box.text().lower()
        self.word_list.clear()
        for word in sorted(self.word_data.keys()):
            if query in word.lower():
                self.word_list.addItem(word)

    def display_explanation(self, item):
        word = item.text()
        md = self.word_data.get(word, "")
        html = convert_to_html(md, dark=self.dark_mode)
        self.text_browser.setHtml(html)
        log_progress("viewed")

    def add_word(self):
        word, ok = QInputDialog.getText(self, "Add Word", "Enter the new word:")
        if not ok or not word.strip():
            return

        dialog = EditDialog(word)
        if dialog.exec():
            explanation = dialog.get_text()
            self.word_data[word] = explanation
            save_data(self.word_data)
            log_progress("added")
            self.refresh_word_list()

    def edit_word(self):
        item = self.word_list.currentItem()
        if not item:
            QMessageBox.warning(self, "No Word Selected", "Please select a word to edit.")
            return

        word = item.text()
        current_explanation = self.word_data.get(word, "")

        dialog = EditDialog(word, current_explanation)
        if dialog.exec():
            updated = dialog.get_text()
            self.word_data[word] = updated
            save_data(self.word_data)
            self.display_explanation(item)

    def delete_word(self):
        item = self.word_list.currentItem()
        if not item:
            QMessageBox.warning(self, "No Word Selected", "Please select a word to delete.")
            return

        word = item.text()
        confirm = QMessageBox.question(self, "Confirm Deletion", f"Delete '{word}'?", QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            del self.word_data[word]
            save_data(self.word_data)
            self.refresh_word_list()
            self.text_browser.clear()

    def toggle_dark_mode(self):
        self.dark_mode = not self.dark_mode
        if self.dark_mode:
            self.setStyleSheet("""
                QWidget { background-color: #1e1e1e; color: #f0f0f0; }
                QLineEdit, QListWidget {
                    background-color: #2e2e2e;
                    color: #f0f0f0;
                    border: 1px solid #555;
                }
                QPushButton {
                    background-color: #444;
                    color: white;
                    padding: 5px;
                }
                QPushButton:hover {
                    background-color: #666;
                }
            """)
        else:
            self.setStyleSheet("")
        item = self.word_list.currentItem()
        if item:
            self.display_explanation(item)

    def show_progress(self):
        if not os.path.exists(PROGRESS_FILE):
            QMessageBox.information(self, "No Data", "No progress has been logged yet.")
            return

        with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)

        dialog = ProgressDialog(data, self)
        dialog.exec()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DictionaryApp()
    window.show()
    sys.exit(app.exec())

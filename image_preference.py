import sys
import os
import json
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QFileDialog,
    QMessageBox,
    QTextEdit,
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt


class ImageComparer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Comparer")

        # Paths to Folder A and Folder B
        self.folder_a = ""
        self.folder_b = ""

        # List of image filenames (lowercase for matching)
        self.image_names = []

        # Current index in the image list
        self.current_index = 0

        # Annotations: { "image1.jpg": "A", "image2.png": "T", ... }
        self.annotations = {}

        # Path to the annotations JSON file
        self.annotations_file = ""

        # Prompts: { "image1.jpg": "Prompt text...", ... }
        self.prompts = {}

        # Initialize UI components
        self.init_ui()

    def init_ui(self):
        # Main layout
        main_layout = QVBoxLayout()

        # Folder selection buttons
        folder_layout = QHBoxLayout()
        self.btn_select_a = QPushButton("Select Folder A")
        self.btn_select_b = QPushButton("Select Folder B")
        folder_layout.addWidget(self.btn_select_a)
        folder_layout.addWidget(self.btn_select_b)
        main_layout.addLayout(folder_layout)

        # Image display labels
        images_layout = QHBoxLayout()
        self.label_a = QLabel("Folder A Image")
        self.label_b = QLabel("Folder B Image")
        self.label_a.setAlignment(Qt.AlignCenter)
        self.label_b.setAlignment(Qt.AlignCenter)
        images_layout.addWidget(self.label_a)
        images_layout.addWidget(self.label_b)
        main_layout.addLayout(images_layout)

        # Prompt display
        self.label_prompt = QLabel("Prompt:")
        self.text_prompt = QTextEdit()
        self.text_prompt.setReadOnly(True)
        self.text_prompt.setFixedHeight(100)
        main_layout.addWidget(self.label_prompt)
        main_layout.addWidget(self.text_prompt)

        # Choice buttons layout
        choices_layout = QHBoxLayout()
        self.btn_choose_a = QPushButton("Left")
        self.btn_no_preference = QPushButton("No Preference")
        self.btn_choose_b = QPushButton("Right")

        # Initially disable choice buttons until folders are selected
        self.btn_choose_a.setEnabled(False)
        self.btn_no_preference.setEnabled(False)
        self.btn_choose_b.setEnabled(False)

        # Add buttons to layout
        choices_layout.addWidget(self.btn_choose_a)
        choices_layout.addWidget(self.btn_no_preference)
        choices_layout.addWidget(self.btn_choose_b)
        main_layout.addLayout(choices_layout)

        # Navigation buttons layout
        navigation_layout = QHBoxLayout()
        self.btn_previous = QPushButton("Previous")
        self.btn_next = QPushButton("Next")

        # Initially disable navigation buttons
        self.btn_previous.setEnabled(False)
        self.btn_next.setEnabled(False)

        navigation_layout.addWidget(self.btn_previous)
        navigation_layout.addWidget(self.btn_next)
        main_layout.addLayout(navigation_layout)

        # Buttons to load existing annotations and prompts
        load_buttons_layout = QHBoxLayout()
        self.btn_load_annotations = QPushButton("Load Annotations")
        self.btn_load_prompts = QPushButton("Load Prompt File")
        load_buttons_layout.addWidget(self.btn_load_annotations)
        load_buttons_layout.addWidget(self.btn_load_prompts)
        main_layout.addLayout(load_buttons_layout)

        self.setLayout(main_layout)

        # Connect signals to slots
        self.btn_select_a.clicked.connect(self.select_folder_a)
        self.btn_select_b.clicked.connect(self.select_folder_b)
        self.btn_choose_a.clicked.connect(lambda: self.record_preference("A"))
        self.btn_choose_b.clicked.connect(lambda: self.record_preference("B"))
        self.btn_no_preference.clicked.connect(lambda: self.record_preference("T"))
        self.btn_load_annotations.clicked.connect(self.load_annotations)
        self.btn_load_prompts.clicked.connect(self.load_prompts)
        self.btn_previous.clicked.connect(self.go_previous)
        self.btn_next.clicked.connect(self.go_next)

    def select_folder_a(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder A")
        if folder:
            self.folder_a = folder
            self.btn_select_a.setText(os.path.basename(folder))
            self.check_folders_selected()

    def select_folder_b(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder B")
        if folder:
            self.folder_b = folder
            self.btn_select_b.setText(os.path.basename(folder))
            self.check_folders_selected()

    def check_folders_selected(self):
        if self.folder_a and self.folder_b:
            # Get image files from both folders (case-insensitive)
            a_images = set(
                f.lower()
                for f in os.listdir(self.folder_a)
                if f.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tiff", ".webp"))
            )
            b_images = set(
                f.lower()
                for f in os.listdir(self.folder_b)
                if f.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tiff", ".webp"))
            )

            # Find common images (case-insensitive)
            common_images_lower = a_images.intersection(b_images)

            if not common_images_lower:
                QMessageBox.warning(
                    self,
                    "No Matching Images",
                    "There are no common image files in the selected folders.",
                )
                return

            # Map lowercase filenames to actual filenames to preserve original casing
            a_mapping = {f.lower(): f for f in os.listdir(self.folder_a) if f.lower() in common_images_lower}
            b_mapping = {f.lower(): f for f in os.listdir(self.folder_b) if f.lower() in common_images_lower}

            # Assuming filenames are identical in both folders except for case
            self.image_names = sorted(a_mapping.keys())

            # After selecting folders, ask the user if they want to load existing annotations
            reply = QMessageBox.question(
                self,
                "Load Annotations",
                "Do you want to load an existing annotations JSON file?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply == QMessageBox.Yes:
                self.load_annotations()
            else:
                # Initialize annotations as empty
                self.annotations = {}
                self.annotations_file = ""
                # Enable choice and navigation buttons
                self.btn_choose_a.setEnabled(True)
                self.btn_no_preference.setEnabled(True)
                self.btn_choose_b.setEnabled(True)
                self.btn_next.setEnabled(True)
                self.btn_previous.setEnabled(False)
                # Show the first image pair
                self.show_image_pair()

    def load_annotations(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Annotations",
            "",
            "JSON Files (*.json);;All Files (*)",
            options=options,
        )
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    loaded_annotations = json.load(f)
                if not isinstance(loaded_annotations, dict):
                    raise ValueError("Annotations file must contain a dictionary.")

                # Ensure all keys and values are strings
                for key, value in loaded_annotations.items():
                    if not isinstance(key, str) or not isinstance(value, str):
                        raise ValueError("All keys and values in annotations must be strings.")

                # Normalize annotations to lowercase keys for matching
                normalized_annotations = {k.lower(): v for k, v in loaded_annotations.items()}

                # Update annotations by preserving original casing
                actual_annotations = {}
                for img_lower, pref in normalized_annotations.items():
                    a_actual = self.get_actual_filename(self.folder_a, img_lower)
                    b_actual = self.get_actual_filename(self.folder_b, img_lower)
                    if a_actual and b_actual:
                        # Ensure preference is one of "A", "B", or "T"
                        if pref in ["A", "B", "T"]:
                            actual_annotations[a_actual] = pref

                self.annotations.update(actual_annotations)
                QMessageBox.information(
                    self,
                    "Success",
                    f"Loaded {len(actual_annotations)} annotations from {file_path}",
                )
                self.annotations_file = file_path
                self.update_image_display()
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to load annotations: {e}",
                )
        else:
            # If the user cancels the file dialog, proceed without loading annotations
            if not self.annotations:
                self.annotations = {}
                self.annotations_file = ""
                self.show_image_pair()

    def load_prompts(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Prompt File",
            "",
            "JSON Files (*.json);;All Files (*)",
            options=options,
        )
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    loaded_prompts = json.load(f)
                if not isinstance(loaded_prompts, dict):
                    raise ValueError("Prompt file must contain a dictionary.")

                # Ensure all keys and values are strings
                for key, value in loaded_prompts.items():
                    if not isinstance(key, str) or not isinstance(value, str):
                        raise ValueError("All keys and values in prompts must be strings.")

                # Normalize prompts to lowercase keys for matching
                normalized_prompts = {k.lower(): v for k, v in loaded_prompts.items()}

                # Update prompts by preserving original casing
                for img_lower, prompt in normalized_prompts.items():
                    a_actual = self.get_actual_filename(self.folder_a, img_lower)
                    b_actual = self.get_actual_filename(self.folder_b, img_lower)
                    if a_actual and b_actual:
                        self.prompts[a_actual] = prompt

                QMessageBox.information(
                    self,
                    "Success",
                    f"Loaded prompts for {len(self.prompts)} images from {file_path}",
                )
                self.show_image_pair()  # Refresh to show prompt if available
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to load prompts: {e}",
                )

    def update_image_display(self):
        # Filter image_names to exclude already annotated images
        annotated = set(self.annotations.keys())
        original_image_names = self.image_names.copy()
        self.image_names = [img for img in self.image_names if img not in annotated]

        skipped = len(original_image_names) - len(self.image_names)
        if skipped > 0:
            print(f"Skipped {skipped} already annotated images.")

        if not self.image_names:
            QMessageBox.information(
                self,
                "All Annotated",
                "All image pairs have been annotated.",
            )
            self.save_annotations()
            sys.exit()

        # Enable choice and navigation buttons
        self.btn_choose_a.setEnabled(True)
        self.btn_no_preference.setEnabled(True)
        self.btn_choose_b.setEnabled(True)
        self.btn_next.setEnabled(True)
        self.btn_previous.setEnabled(False)

        # Show the first unannotated image pair
        self.current_index = 0
        self.show_image_pair()

    def show_image_pair(self):
        if not self.image_names:
            QMessageBox.information(
                self,
                "No Images",
                "No image pairs to display.",
            )
            return

        if self.current_index < 0 or self.current_index >= len(self.image_names):
            return

        image_key = self.image_names[self.current_index]  # Lowercase filename

        # Retrieve actual filenames with original casing
        a_actual = self.get_actual_filename(self.folder_a, image_key)
        b_actual = self.get_actual_filename(self.folder_b, image_key)

        a_image_path = os.path.join(self.folder_a, a_actual)
        b_image_path = os.path.join(self.folder_b, b_actual)

        # Load and display Folder A image
        pixmap_a = self.load_image(a_image_path)
        if pixmap_a:
            self.label_a.setPixmap(pixmap_a.scaled(400, 400, Qt.KeepAspectRatio))
        else:
            self.label_a.setText("Failed to load image")

        # Load and display Folder B image
        pixmap_b = self.load_image(b_image_path)
        if pixmap_b:
            self.label_b.setPixmap(pixmap_b.scaled(400, 400, Qt.KeepAspectRatio))
        else:
            self.label_b.setText("Failed to load image")

        # Display prompt if available
        prompt = self.prompts.get(a_actual, "No prompt available.")
        self.text_prompt.setText(prompt)

        # Update navigation buttons
        self.btn_previous.setEnabled(self.current_index > 0)
        self.btn_next.setEnabled(self.current_index < len(self.image_names) - 1)

    def get_actual_filename(self, folder, lowercase_filename):
        """
        Given a folder and a lowercase filename, return the actual filename with original casing.
        """
        for f in os.listdir(folder):
            if f.lower() == lowercase_filename:
                return f
        return lowercase_filename  # Fallback, should not happen

    def load_image(self, path):
        try:
            pixmap = QPixmap(path)
            if pixmap.isNull():
                raise ValueError("Pixmap is null")
            return pixmap
        except Exception as e:
            print(f"Failed to load image: {path}, Error: {e}")
            return None

    def record_preference(self, choice):
        image_key = self.image_names[self.current_index]  # Lowercase filename
        # Retrieve actual filename with original casing
        a_actual = self.get_actual_filename(self.folder_a, image_key)
        b_actual = self.get_actual_filename(self.folder_b, image_key)

        # Map choice to "A", "B", or "T"
        if choice == "A":
            preference = "A"
        elif choice == "B":
            preference = "B"
        else:
            preference = "T"

        # Record the annotation
        self.annotations[a_actual] = preference
        print(f"Annotated {a_actual}: {preference}")

        # Move to the next image
        if self.current_index < len(self.image_names) - 1:
            self.current_index += 1
            self.show_image_pair()
        else:
            QMessageBox.information(
                self,
                "Completed",
                "All image pairs have been annotated.",
            )
            self.save_annotations()

    def go_previous(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.show_image_pair()

    def go_next(self):
        if self.current_index < len(self.image_names) - 1:
            self.current_index += 1
            self.show_image_pair()

    def save_annotations(self):
        # Prepare data to save: only image names and preferences
        data = self.annotations

        if self.annotations_file:
            save_path = self.annotations_file
        else:
            options = QFileDialog.Options()
            save_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Annotations",
                "annotations.json",
                "JSON Files (*.json);;All Files (*)",
                options=options,
            )
            if not save_path:
                return

        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            QMessageBox.information(
                self,
                "Success",
                f"Annotations saved to {save_path}",
            )
            self.annotations_file = save_path
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to save annotations: {e}",
            )

    def closeEvent(self, event):
        # Prompt to save if there are annotations to save
        if self.annotations:
            reply = QMessageBox.question(
                self,
                "Save Annotations",
                "Do you want to save your annotations before exiting?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                QMessageBox.Yes,
            )
            if reply == QMessageBox.Yes:
                self.save_annotations()
                event.accept()
            elif reply == QMessageBox.No:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


def main():
    app = QApplication(sys.argv)
    comparer = ImageComparer()
    comparer.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()


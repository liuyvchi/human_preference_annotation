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
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt


class ImageComparer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Comparer")

        # Paths to the left and right folders
        self.left_folder = ""
        self.right_folder = ""

        # List of image filenames (lowercase for matching)
        self.image_names = []

        # Current index in the image list
        self.current_index = 0

        # Annotations: { "image1.jpg": "LeftFolderName", ... }
        self.annotations = {}

        # Path to the annotations JSON file
        self.annotations_file = ""

        # Initialize UI components
        self.init_ui()

    def init_ui(self):
        # Main layout
        main_layout = QVBoxLayout()

        # Folder selection buttons
        folder_layout = QHBoxLayout()
        self.btn_select_left = QPushButton("Select Left Folder")
        self.btn_select_right = QPushButton("Select Right Folder")
        folder_layout.addWidget(self.btn_select_left)
        folder_layout.addWidget(self.btn_select_right)
        main_layout.addLayout(folder_layout)

        # Image display labels
        images_layout = QHBoxLayout()
        self.label_left = QLabel("Left Image")
        self.label_right = QLabel("Right Image")
        self.label_left.setAlignment(Qt.AlignCenter)
        self.label_right.setAlignment(Qt.AlignCenter)
        images_layout.addWidget(self.label_left)
        images_layout.addWidget(self.label_right)
        main_layout.addLayout(images_layout)

        # Choice buttons layout
        choices_layout = QHBoxLayout()
        self.btn_choose_left = QPushButton("Left")
        self.btn_no_preference = QPushButton("No Preference")
        self.btn_choose_right = QPushButton("Right")

        # Initially disable choice buttons until folders are selected
        self.btn_choose_left.setEnabled(False)
        self.btn_no_preference.setEnabled(False)
        self.btn_choose_right.setEnabled(False)

        # Add buttons to layout with "No Preference" in the center
        choices_layout.addWidget(self.btn_choose_left)
        choices_layout.addWidget(self.btn_no_preference)
        choices_layout.addWidget(self.btn_choose_right)
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

        # Button to load existing annotations
        self.btn_load_annotations = QPushButton("Load Annotations")
        main_layout.addWidget(self.btn_load_annotations)

        self.setLayout(main_layout)

        # Connect signals to slots
        self.btn_select_left.clicked.connect(self.select_left_folder)
        self.btn_select_right.clicked.connect(self.select_right_folder)
        self.btn_choose_left.clicked.connect(lambda: self.record_preference("left"))
        self.btn_choose_right.clicked.connect(lambda: self.record_preference("right"))
        self.btn_no_preference.clicked.connect(lambda: self.record_preference("no preference"))
        self.btn_load_annotations.clicked.connect(self.load_annotations)
        self.btn_previous.clicked.connect(self.go_previous)
        self.btn_next.clicked.connect(self.go_next)

    def select_left_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Left Folder")
        if folder:
            self.left_folder = folder
            self.btn_select_left.setText(os.path.basename(folder))
            self.check_folders_selected()

    def select_right_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Right Folder")
        if folder:
            self.right_folder = folder
            self.btn_select_right.setText(os.path.basename(folder))
            self.check_folders_selected()

    def check_folders_selected(self):
        if self.left_folder and self.right_folder:
            # Get image files from both folders (case-insensitive)
            left_images = set(
                f.lower()
                for f in os.listdir(self.left_folder)
                if f.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tiff", ".webp"))
            )
            right_images = set(
                f.lower()
                for f in os.listdir(self.right_folder)
                if f.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tiff", ".webp"))
            )

            # Find common images (case-insensitive)
            common_images_lower = left_images.intersection(right_images)

            if not common_images_lower:
                QMessageBox.warning(
                    self,
                    "No Matching Images",
                    "There are no common image files in the selected folders.",
                )
                return

            # Map lowercase filenames to actual filenames to preserve original casing
            left_mapping = {f.lower(): f for f in os.listdir(self.left_folder) if f.lower() in common_images_lower}
            right_mapping = {f.lower(): f for f in os.listdir(self.right_folder) if f.lower() in common_images_lower}

            # Assuming filenames are identical in both folders except for case
            self.image_names = sorted(left_mapping.keys())

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
                self.btn_choose_left.setEnabled(True)
                self.btn_no_preference.setEnabled(True)
                self.btn_choose_right.setEnabled(True)
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
                    actual_filename = self.get_actual_filename(self.left_folder, img_lower)
                    if actual_filename:
                        actual_annotations[actual_filename] = pref

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
            self.annotations = {}
            self.annotations_file = ""
            self.show_image_pair()

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
        self.btn_choose_left.setEnabled(True)
        self.btn_no_preference.setEnabled(True)
        self.btn_choose_right.setEnabled(True)
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
        left_actual = self.get_actual_filename(self.left_folder, image_key)
        right_actual = self.get_actual_filename(self.right_folder, image_key)

        left_image_path = os.path.join(self.left_folder, left_actual)
        right_image_path = os.path.join(self.right_folder, right_actual)

        # Load and display left image
        pixmap_left = self.load_image(left_image_path)
        if pixmap_left:
            self.label_left.setPixmap(pixmap_left.scaled(400, 400, Qt.KeepAspectRatio))
        else:
            self.label_left.setText("Failed to load image")

        # Load and display right image
        pixmap_right = self.load_image(right_image_path)
        if pixmap_right:
            self.label_right.setPixmap(pixmap_right.scaled(400, 400, Qt.KeepAspectRatio))
        else:
            self.label_right.setText("Failed to load image")

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
        left_actual = self.get_actual_filename(self.left_folder, image_key)
        right_actual = self.get_actual_filename(self.right_folder, image_key)

        if choice == "left":
            preference = os.path.basename(self.left_folder)
        elif choice == "right":
            preference = os.path.basename(self.right_folder)
        else:
            preference = "No Preference"

        # Record the annotation
        self.annotations[left_actual] = preference
        print(f"Annotated {left_actual}: {preference}")

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

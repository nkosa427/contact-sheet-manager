import os
import shutil
import tkinter as tk
from pathlib import Path
from PIL import Image, ImageTk

class ContactSheetManager:
    def __init__(self, root, folder_path):
        self.root = root
        self.folder_path = Path(folder_path)
        self.keep_folder = self.folder_path / "Keep"
        self.delete_folder = self.folder_path / "Delete"
        self.keep_folder.mkdir(exist_ok=True)
        self.delete_folder.mkdir(exist_ok=True)

        # Get all contact sheets and videos
        images = list(self.folder_path.glob("*.jpg")) + list(self.folder_path.glob("*.png"))
        videos = list(self.folder_path.glob("*.mp4")) + list(self.folder_path.glob("*.mov"))
        
        # Pair files by stem (name without extension)
        self.pairs = []
        image_stems = {img.stem: img for img in images}
        for vid in videos:
            img = image_stems.get(vid.stem)
            if img: self.pairs.append((img, vid))
        
        self.pairs.sort(key=lambda x: x[0].name)  # Sort by filename
        self.current_idx = 0

        # GUI Setup
        self.root.title("Contact Sheet Manager")
        self.img_label = tk.Label(root)
        self.img_label.pack()
        self.status = tk.Label(root, text="", font=('Arial', 12))
        self.status.pack(pady=10)

        # Bind keys
        self.root.bind('<KeyPress>', self.handle_key)
        self.show_image()

    def show_image(self):
        if self.current_idx >= len(self.pairs):
            self.status.config(text="All files processed!")
            return

        img_path, vid_path = self.pairs[self.current_idx]
        img = Image.open(img_path)
        img.thumbnail((800, 800))  # Resize for display
        tk_img = ImageTk.PhotoImage(img)
        self.img_label.config(image=tk_img)
        self.img_label.image = tk_img
        self.update_status()

    def update_status(self):
        remaining = len(self.pairs) - self.current_idx
        self.status.config(text=f"Remaining: {remaining} | Current: {self.pairs[self.current_idx][0].name}")

    def handle_key(self, event):
        if event.char.lower() == 'k':  # Keep
            self.move_video(self.keep_folder)
            self.next()
        elif event.char.lower() == 'd':  # Delete
            self.move_video(self.delete_folder)
            self.next()
        elif event.keysym == 'Right':  # Next
            self.next()
        elif event.keysym == 'Left':  # Previous
            self.previous()
        elif event.char.lower() == 'q':  # Quit
            self.root.quit()

    def move_video(self, target_folder):
        _, vid_path = self.pairs[self.current_idx]
        try:
            shutil.move(str(vid_path), str(target_folder / vid_path.name))
        except Exception as e:
            print(f"Error moving {vid_path}: {e}")

    def next(self):
        if self.current_idx < len(self.pairs) - 1:
            self.current_idx += 1
            self.show_image()

    def previous(self):
        if self.current_idx > 0:
            self.current_idx -= 1
            self.show_image()

if __name__ == "__main__":
    folder = input("Enter the full path to your folder: ").strip()
    root = tk.Tk()
    app = ContactSheetManager(root, folder)
    root.mainloop()
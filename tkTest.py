import tkinter as tk
from PIL import Image, ImageTk
import os

class ImageViewer:
    def __init__(self, root, folder_path):
        self.root = root
        self.current_index = 0
        self.photos = []  # Store all processed images
        
        # Setup window
        self.root.title("Image Viewer")
        self.root.state('zoomed')
        self.root.minsize(800, 600)
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Create UI
        self.label = tk.Label(root, bg='black')
        self.label.grid(row=0, column=0, sticky='nsew')
        
        self.loading_label = tk.Label(
            root, 
            text="Loading images...", 
            font=('Arial', 12),
            bg='black',
            fg='white'
        )
        self.loading_label.grid(row=0, column=0, sticky='nsew')
        
        # Bind events
        self.root.bind('<MouseWheel>', self.on_mouse_wheel)
        self.root.bind('<Button-4>', self.on_mouse_wheel)
        self.root.bind('<Button-5>', self.on_mouse_wheel)
        self.root.bind('<Escape>', lambda e: self.root.quit())
        
        # Load all images at startup
        self.load_all_images(folder_path)

    def load_all_images(self, folder_path):
        """Load and process all images at startup"""
        image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp')
        files = sorted([
            os.path.join(folder_path, f) for f in os.listdir(folder_path)
            if f.lower().endswith(image_extensions)
        ])
        
        total = len(files)
        for i, path in enumerate(files):
            try:
                # Update loading progress
                self.loading_label.configure(text=f"Loading images... ({i+1}/{total})")
                self.root.update_idletasks()
                
                # Load and resize image
                img = Image.open(path)
                photo = self.prepare_image(img)
                if photo:
                    self.photos.append(photo)
                
            except Exception as e:
                print(f"Error loading {path}: {e}")
        
        # Show first image
        self.loading_label.grid_remove()
        if self.photos:
            self.show_image(0)

    def prepare_image(self, img):
        """Prepare single image at window size"""
        try:
            width = self.root.winfo_width() - 20
            height = self.root.winfo_height() - 20
            
            img_ratio = img.width / img.height
            window_ratio = width / height
            
            if window_ratio > img_ratio:
                new_height = height
                new_width = int(new_height * img_ratio)
            else:
                new_width = width
                new_height = int(new_width / img_ratio)
            
            return ImageTk.PhotoImage(
                img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            )
        except Exception as e:
            print(f"Error preparing image: {e}")
            return None

    def show_image(self, index):
        """Display image at given index"""
        if 0 <= index < len(self.photos):
            self.current_index = index
            self.label.configure(image=self.photos[index])
            self.label.image = self.photos[index]

    def on_mouse_wheel(self, event):
        """Handle mouse wheel navigation"""
        if event.num == 5 or event.delta < 0:      # Scroll down
            self.show_image(min(self.current_index + 1, len(self.photos) - 1))
        elif event.num == 4 or event.delta > 0:    # Scroll up
            self.show_image(max(self.current_index - 1, 0))

def main():
    try:
        root = tk.Tk()
        folder_path = r"X:\downloads\misc\notready_\jd2vpn\simpcity\sexyflowerwater\cmr_\360-over_\customScreens_"
        app = ImageViewer(root, folder_path)
        root.mainloop()
        return 0, app
    except Exception as e:
        print(f"Application error: {e}")
        return 1, None

if __name__ == "__main__":
    exit_code, viewer = main()
    exit(exit_code)

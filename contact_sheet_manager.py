import tkinter as tk
from PIL import Image, ImageTk
import os
import logging

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('viewer_debug.log')
    ]
)

def find_custom_screens_folder(base_path):
    """Find the customScreens_ folder in or below the given path"""
    logging.info(f"Searching for customScreens_ folder in: {base_path}")
    for root, dirs, _ in os.walk(base_path):
        if "customScreens_" in dirs:
            found_path = os.path.join(root, "customScreens_")
            logging.info(f"Found customScreens_ folder at: {found_path}")
            return found_path
    logging.error("customScreens_ folder not found!")
    return None

def get_matching_files(video_path, screens_path):
    """Match video files with their corresponding screen captures"""
    logging.info(f"Matching files between:\nVideos: {video_path}\nScreens: {screens_path}")
    
    video_extensions = ('.mp4', '.mkv', '.avi', '.wmv', '.flv', '.mov')
    image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp')
    
    # Log all files in directories
    try:
        video_files = os.listdir(video_path)
        screen_files = os.listdir(screens_path)
        logging.debug(f"Found {len(video_files)} files in video directory:")
        for f in video_files:
            logging.debug(f"  Video dir: {f}")
        logging.debug(f"Found {len(screen_files)} files in screens directory:")
        for f in screen_files:
            logging.debug(f"  Screen dir: {f}")
    except Exception as e:
        logging.error(f"Error reading directories: {e}")
        return []
    
    # Get all video files
    videos = []
    for f in video_files:
        if any(f.lower().endswith(ext) for ext in video_extensions):
            videos.append(f)
            logging.debug(f"Found video file: {f}")
    
    if not videos:
        logging.warning(f"No video files found with extensions: {video_extensions}")
    
    # Match with screenshots - now looking for full filename + image extension
    matched_files = []
    for video in videos:
        logging.debug(f"Looking for matches for video: {video}")
        
        # Look for video filename + image extension
        matched = False
        for img_ext in image_extensions:
            img_name = video + img_ext  # Use full video filename including extension
            img_path = os.path.join(screens_path, img_name)
            logging.debug(f"Checking for image: {img_name}")
            if os.path.exists(img_path):
                matched = True
                matched_files.append((
                    os.path.join(video_path, video),
                    img_path
                ))
                logging.debug(f"Found match: {img_name}")
                break
        
        if not matched:
            logging.warning(f"No matching image found for video: {video}")
    
    logging.info(f"Found {len(matched_files)} matching video-screenshot pairs")
    for video, screen in matched_files:
        logging.info(f"Matched: {os.path.basename(video)} -> {os.path.basename(screen)}")
    
    return sorted(matched_files)

class ImageViewer:
    def __init__(self, root, folder_path):
        logging.info("Initializing ImageViewer")
        self.root = root
        self.current_index = 0
        self.photos = []      # Store all processed images
        self.file_pairs = []  # Store (video_path, image_path) pairs
        
        # Setup window
        self.root.title("Contact Sheet Manager")
        self.root.state('zoomed')
        self.root.minsize(800, 600)
        
        # Configure grid
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=0)  # For file info
        self.root.grid_columnconfigure(0, weight=1)
        
        # Create UI
        self.label = tk.Label(root, bg='black')
        self.label.grid(row=0, column=0, sticky='nsew')
        
        # Add file info display
        self.info_label = tk.Label(
            root,
            text="",
            font=('Arial', 10),
            bg='black',
            fg='white',
            anchor='w',
            padx=10
        )
        self.info_label.grid(row=1, column=0, sticky='ew')
        
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
        
        # Find customScreens_ folder and load images
        screens_folder = find_custom_screens_folder(folder_path)
        if screens_folder:
            logging.info("Starting image loading process")
            self.load_all_images(folder_path, screens_folder)
        else:
            logging.error("No customScreens_ folder found, cannot proceed")
            self.loading_label.configure(text="Error: customScreens_ folder not found")

    def load_all_images(self, video_path, screens_path):
        """Load and process all matching images"""
        self.file_pairs = get_matching_files(video_path, screens_path)
        total = len(self.file_pairs)
        logging.info(f"Loading {total} images")
        
        for i, (video_path, image_path) in enumerate(self.file_pairs):
            try:
                progress_msg = f"Loading images... ({i+1}/{total})"
                logging.debug(f"Processing image {i+1}/{total}: {image_path}")
                self.loading_label.configure(text=progress_msg)
                self.root.update_idletasks()
                
                img = Image.open(image_path)
                logging.debug(f"Original image size: {img.size}")
                photo = self.prepare_image(img)
                if photo:
                    self.photos.append(photo)
                    logging.debug("Successfully processed and cached image")
                else:
                    logging.error(f"Failed to prepare image: {image_path}")
                
            except Exception as e:
                logging.error(f"Error loading {image_path}: {e}", exc_info=True)
        
        logging.info(f"Finished loading {len(self.photos)} images")
        self.loading_label.grid_remove()
        if self.photos:
            logging.info("Showing first image")
            self.show_image(0)
        else:
            logging.error("No images were successfully loaded!")

    def prepare_image(self, img):
        """Prepare single image at window size"""
        try:
            width = self.root.winfo_width() - 20
            height = self.root.winfo_height() - 20
            logging.debug(f"Window dimensions: {width}x{height}")
            
            if width <= 0 or height <= 0:
                logging.error(f"Invalid window dimensions: {width}x{height}")
                return None
            
            # Log original and calculated dimensions
            img_ratio = img.width / img.height
            window_ratio = width / height
            logging.debug(f"Image ratio: {img_ratio:.2f}, Window ratio: {window_ratio:.2f}")
            
            if window_ratio > img_ratio:
                new_height = height
                new_width = int(new_height * img_ratio)
            else:
                new_width = width
                new_height = int(new_width / img_ratio)
                
            logging.debug(f"Resizing to: {new_width}x{new_height}")
            
            photo = ImageTk.PhotoImage(
                img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            )
            logging.debug("Successfully created PhotoImage")
            return photo
            
        except Exception as e:
            logging.error(f"Error preparing image: {e}", exc_info=True)
            return None

    def show_image(self, index):
        """Display image and file info at given index"""
        logging.debug(f"Attempting to show image at index: {index}")
        if 0 <= index < len(self.photos):
            self.current_index = index
            logging.debug("Configuring label with new image")
            self.label.configure(image=self.photos[index])
            self.label.image = self.photos[index]
            
            # Update file info
            video_path, image_path = self.file_pairs[index]
            video_name = os.path.basename(video_path)
            image_name = os.path.basename(image_path)
            logging.debug(f"Showing file info for: {video_name} -> {image_name}")
            self.info_label.configure(
                text=f"Video: {video_name}\nScreen: {image_name}"
            )
        else:
            logging.error(f"Invalid image index: {index}")

    def on_mouse_wheel(self, event):
        """Handle mouse wheel navigation"""
        if event.num == 5 or event.delta < 0:      # Scroll down
            self.show_image(min(self.current_index + 1, len(self.photos) - 1))
        elif event.num == 4 or event.delta > 0:    # Scroll up
            self.show_image(max(self.current_index - 1, 0))

def main():
    try:
        logging.info("Starting application")
        root = tk.Tk()
        folder_path = r"X:\downloads\misc\notready_\jd2vpn\simpcity\sexysarabee\sexysarabee\30-60s_"
        
        # Verify paths exist
        if not os.path.exists(folder_path):
            logging.error(f"Base folder path does not exist: {folder_path}")
            raise FileNotFoundError(f"Folder not found: {folder_path}")
            
        logging.info(f"Using folder path: {folder_path}")
        app = ImageViewer(root, folder_path)
        root.mainloop()
        return 0, app
    except Exception as e:
        logging.error("Application error", exc_info=True)
        return 1, None

if __name__ == "__main__":
    exit_code, viewer = main()
    exit(exit_code)

import tkinter as tk
from tkinter import messagebox  # Add this import
from PIL import Image, ImageTk
import os
import logging
import subprocess  # Add this import
from tkinterdnd2 import DND_FILES, TkinterDnD  # Add this import

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
        self.base_path = folder_path  # Store base path for folder creation
        self.keep_folder = os.path.join(folder_path, 'keep')  # Just store path, don't create yet

        # Add space key state and moved files tracking
        self.space_pressed = False
        self.moved_files = set()  # Keep track of already moved files

        # Add reference to parent selector
        self.selector = None  # Will be set by FolderSelector

        # Setup window
        self.root.title("Contact Sheet Manager")
        self.root.state('zoomed')
        self.root.minsize(800, 600)
        
        # Configure grid with proper padding
        self.root.grid_rowconfigure(0, weight=1, pad=10)  # Add top padding
        self.root.grid_rowconfigure(1, weight=0)  # For file info
        self.root.grid_columnconfigure(0, weight=1, pad=10)  # Add side padding
        
        # Create main content frame with padding
        content_frame = tk.Frame(root, bg='black')
        content_frame.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)
        content_frame.grid_rowconfigure(0, weight=1)
        content_frame.grid_columnconfigure(0, weight=1)
        
        # Create UI in content frame instead of root
        self.label = tk.Label(content_frame, bg='black')
        self.label.grid(row=0, column=0, sticky='nsew')
        
        # Add file info display at bottom of root
        self.info_label = tk.Label(
            root,
            text="",
            font=('Arial', 10),
            bg='black',
            fg='white',
            anchor='w',
            padx=10
        )
        self.info_label.grid(row=1, column=0, sticky='ew', padx=10, pady=(0, 10))
        
        # Loading label in content frame
        self.loading_label = tk.Label(
            content_frame, 
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
        self.root.bind('<Escape>', self.confirm_exit)
        
        # Add keyboard bindings
        self.root.bind('<KeyPress-space>', self.space_pressed_handler)
        self.root.bind('<KeyRelease-space>', self.space_released_handler)
        self.root.bind('a', self.move_to_destination)
        self.root.bind('f', self.move_to_destination)
        self.root.bind('r', self.move_to_destination)
        self.root.bind('p', self.play_video)  # Add play video binding

        # Find customScreens_ folder and load images
        screens_folder = find_custom_screens_folder(folder_path)
        if screens_folder:
            logging.info("Starting image loading process")
            self.load_all_images(folder_path, screens_folder)
        else:
            logging.error("No customScreens_ folder found, cannot proceed")
            self.loading_label.configure(text="Error: customScreens_ folder not found")

    def confirm_exit(self, event=None):
        """Show confirmation dialog before returning to folder selection"""
        if tk.messagebox.askyesno("Confirm", "Return to folder selection?"):
            # Show selector window
            if self.selector:
                self.selector.root.deiconify()
            # Destroy viewer window
            self.root.destroy()

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
            # Account for padding in both directions
            width = self.root.winfo_width() - 40  # 20px padding on each side
            height = self.root.winfo_height() - 60  # Extra space for info label
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
        if not self.photos:  # Check if any photos left
            logging.info("No photos left to display")
            self.label.configure(image='')
            self.info_label.configure(text="No more images to process")
            return
            
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
        if not self.photos:  # Prevent navigation when no images left
            return
            
        if event.num == 5 or event.delta < 0:      # Scroll down
            self.show_image(min(self.current_index + 1, len(self.photos) - 1))
        elif event.num == 4 or event.delta > 0:    # Scroll up
            self.show_image(max(self.current_index - 1, 0))

    def verify_file_pair(self, video_path, image_path):
        """Verify that image filename matches video filename"""
        video_name = os.path.basename(video_path)
        image_name = os.path.basename(image_path)
        
        # Image name should be video name + image extension
        return image_name.startswith(video_name)

    def create_destination_folders(self, dest_key):
        """Create keep folder and destination folders only when needed"""
        # Create keep folder if it doesn't exist
        if not os.path.exists(self.keep_folder):
            logging.info(f"Creating keep folder at: {self.keep_folder}")
            os.makedirs(self.keep_folder)
        
        main_folder = os.path.join(self.keep_folder, dest_key)
        screens_folder = os.path.join(main_folder, 'customScreens_')
        
        if not os.path.exists(main_folder):
            logging.info(f"Creating {dest_key} folder at: {main_folder}")
            os.makedirs(main_folder)
        
        if not os.path.exists(screens_folder):
            logging.info(f"Creating customScreens_ folder at: {screens_folder}")
            os.makedirs(screens_folder)
            
        return main_folder, screens_folder

    def space_pressed_handler(self, event):
        """Handle space key press"""
        self.space_pressed = True

    def space_released_handler(self, event):
        """Handle space key release"""
        self.space_pressed = False

    def move_to_destination(self, event):
        """Move current video and image (and previous if space held) to specified destination folder"""
        dest_key = event.char.upper()
        if 0 <= self.current_index < len(self.file_pairs):
            try:
                # Determine range of files to move
                start_idx = 0 if self.space_pressed else self.current_index
                end_idx = self.current_index + 1
                
                moved_count = 0
                failed_count = 0
                
                for idx in range(start_idx, end_idx):
                    video_path, image_path = self.file_pairs[idx]
                    
                    # Skip if file was already moved
                    if video_path in self.moved_files:
                        continue
                        
                    # Verify filename match
                    if not self.verify_file_pair(video_path, image_path):
                        logging.error(f"Filename mismatch: {video_path} -> {image_path}")
                        failed_count += 1
                        continue
                    
                    # Create destination folders only when needed
                    main_folder, screens_folder = self.create_destination_folders(dest_key)
                    
                    # Move files to appropriate folders
                    video_name = os.path.basename(video_path)
                    image_name = os.path.basename(image_path)
                    
                    video_dest = os.path.join(main_folder, video_name)
                    image_dest = os.path.join(screens_folder, image_name)
                    
                    logging.info(f"Moving files to {dest_key}:\nVideo -> {video_dest}\nImage -> {image_dest}")
                    
                    os.rename(video_path, video_dest)
                    os.rename(image_path, image_dest)
                    
                    # Track moved files
                    self.moved_files.add(video_path)
                    moved_count += 1
                
                # Remove moved files from lists
                self.cleanup_moved_files()
                
                # Update UI with batch move results
                status = f"✓ Moved {moved_count} files to {dest_key}"
                if failed_count > 0:
                    status += f"\nFailed to move {failed_count} files"
                self.info_label.configure(text=status)
                
                # Update display
                if self.photos:
                    self.show_image(min(self.current_index, len(self.photos) - 1))
                else:
                    self.label.configure(image='')
                    self.info_label.configure(text="No more images to process")
                
            except Exception as e:
                logging.error(f"Error moving files: {e}")
                self.info_label.configure(text=f"Error moving files: {str(e)}")

    def cleanup_moved_files(self):
        """Remove moved files from tracking lists"""
        # Create list of indices to remove (in reverse order)
        to_remove = sorted([
            i for i, (video_path, _) in enumerate(self.file_pairs)
            if video_path in self.moved_files
        ], reverse=True)
        
        # Remove from both lists
        for idx in to_remove:
            self.photos.pop(idx)
            self.file_pairs.pop(idx)

    def play_video(self, event):
        """Play current video in MPC-HC"""
        if 0 <= self.current_index < len(self.file_pairs):
            video_path, _ = self.file_pairs[self.current_index]
            try:
                # Attempt to launch MPC-HC with the video file
                subprocess.Popen([
                    r"C:\Program Files\MPC-HC\mpc-hc64.exe",
                    video_path
                ])
                logging.info(f"Launched video in MPC-HC: {video_path}")
            except Exception as e:
                error_msg = f"Error playing video: {e}"
                logging.error(error_msg)
                self.info_label.configure(text=error_msg)

def cleanup_empty_dirs(base_path):
    """Remove empty directories in the given path"""
    logging.info(f"Cleaning up empty directories in: {base_path}")
    removed = 0
    
    for root, dirs, files in os.walk(base_path, topdown=False):
        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)
            try:
                # Check if directory is empty (no files and no subdirs)
                if not os.listdir(dir_path):
                    os.rmdir(dir_path)
                    removed += 1
                    logging.info(f"Removed empty directory: {dir_path}")
            except Exception as e:
                logging.error(f"Error removing directory {dir_path}: {e}")
    
    if removed > 0:
        logging.info(f"Removed {removed} empty directories")
    return removed

class FolderSelector:
    """Initial UI for folder path selection"""
    def __init__(self, root):
        self.root = root
        self.root.title("Select Folder")
        self.root.geometry("600x150")
        
        # Configure grid
        self.root.grid_columnconfigure(0, weight=1)
        
        # Create UI elements
        self.path_var = tk.StringVar()
        self.path_var.set(r"")
        
        # Path entry
        path_frame = tk.Frame(root)
        path_frame.grid(row=0, column=0, padx=10, pady=10, sticky='ew')
        path_frame.grid_columnconfigure(0, weight=1)
        
        path_entry = tk.Entry(path_frame, textvariable=self.path_var)
        path_entry.grid(row=0, column=0, sticky='ew')
        
        # Configure drag and drop
        path_entry.drop_target_register(DND_FILES)
        path_entry.dnd_bind('<<Drop>>', self.handle_drop)
        
        # Start button
        start_btn = tk.Button(root, text="Start Viewer", command=self.start_viewer)
        start_btn.grid(row=1, column=0, pady=10)
        
        # Status label
        self.status_label = tk.Label(root, text="", fg="red")
        self.status_label.grid(row=2, column=0, pady=5)
        
        # Bind enter key
        self.root.bind('<Return>', lambda e: self.start_viewer())
        
    def handle_drop(self, event):
        """Handle folder drop from Windows Explorer"""
        folder_path = event.data
        # Remove curly braces and quotes if present (Windows drag&drop artifact)
        folder_path = folder_path.strip('{}')
        if folder_path.startswith('"') and folder_path.endswith('"'):
            folder_path = folder_path[1:-1]
        
        # Check if it's a valid directory
        if os.path.isdir(folder_path):
            self.path_var.set(folder_path)
        else:
            self.status_label.configure(text="Please drop a folder, not a file")

    def start_viewer(self):
        """Validate path and start the image viewer"""
        folder_path = self.path_var.get().strip()
        
        if not os.path.exists(folder_path):
            self.status_label.configure(text="Error: Folder not found")
            return
            
        # Hide selector window
        self.root.withdraw()
        
        try:
            # Clean up empty directories
            cleanup_empty_dirs(folder_path)
            
            # Create new window for viewer
            viewer_window = tk.Toplevel()
            
            # Start viewer and give it reference to selector
            app = ImageViewer(viewer_window, folder_path)
            app.selector = self
            
            # Update protocol to use confirm_exit
            viewer_window.protocol("WM_DELETE_WINDOW", app.confirm_exit)
            
            # Close selector when viewer closes without confirmation
            viewer_window.bind('<Destroy>', self._on_viewer_closed)
            
        except Exception as e:
            logging.error(f"Error starting viewer: {e}")
            self.status_label.configure(text=f"Error: {str(e)}")
            self.root.deiconify()  # Show selector again on error

    def _on_viewer_closed(self, event):
        """Handle viewer window closing"""
        if not self.root.winfo_viewable():  # If selector is still hidden
            self.root.quit()

def main():
    """
    Main function to initialize and run the application
    """
    try:
        logging.info("Starting application")
        root = TkinterDnD.Tk()  # Use TkinterDnD.Tk instead of tk.Tk
        app = FolderSelector(root)
        root.mainloop()
        return 0
    except Exception as e:
        logging.error("Application error", exc_info=True)
        return 1

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)

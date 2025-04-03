import tkinter as tk
from tkinter import messagebox  # Add this import
from PIL import Image, ImageTk
import os
import logging
import subprocess
import threading
import queue
from tkinterdnd2 import DND_FILES, TkinterDnD

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
        # self.photos = []      # Store all processed images - Replaced by loaded_images
        self.loaded_images = {} # Store loaded PIL images {index: pil_image}
        self.image_queue = queue.Queue() # Queue for background loading
        self.loading_thread = None
        self.target_dimensions = (800, 600) # Default/initial dimensions
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
        # Keep loading_label, but manage visibility differently
        self.loading_label.grid(row=0, column=0, sticky='nsew')
        self.loading_label.grid_remove() # Hide initially

        # Bind events
        self.root.bind('<Configure>', self.on_resize) # Handle window resize
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
            self.loading_label.grid() # Show error

    def on_resize(self, event):
        """Handle window resize event."""
        # Update target dimensions based on new window size
        # Subtract padding/margins as needed
        width = event.width - 40
        height = event.height - 60 # Account for info label
        if width > 0 and height > 0:
            self.target_dimensions = (width, height)
            logging.debug(f"Window resized, new target dimensions: {self.target_dimensions}")
            # Re-display the current image to resize it
            if self.file_pairs: # Only if images are loaded/loading
                 # Clear the current PhotoImage cache for the index
                if self.current_index in self.loaded_images and isinstance(self.loaded_images[self.current_index], ImageTk.PhotoImage):
                    self.loaded_images[self.current_index] = self.loaded_images[self.current_index].pil_image # Revert to PIL image
                self.show_image(self.current_index, force_update=True)


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
        logging.info(f"Found {total} matching file pairs.")

        if not self.file_pairs:
            logging.error("No matching files found!")
            self.loading_label.configure(text="Error: No matching video/image files found.")
            self.loading_label.grid()
            return

        # Get initial dimensions for resizing
        self.root.update_idletasks() # Ensure window dimensions are available
        width = self.root.winfo_width() - 40
        height = self.root.winfo_height() - 60
        if width <= 0 or height <= 0:
             width, height = 800, 600 # Fallback dimensions
             logging.warning(f"Using fallback dimensions: {width}x{height}")
        self.target_dimensions = (width, height)
        logging.info(f"Initial target dimensions for loading: {self.target_dimensions}")

        # Show loading indicator
        self.loading_label.configure(text=f"Loading 0/{total} images...")
        self.loading_label.grid()

        # Start background loading thread
        self.loading_thread = threading.Thread(
            target=self._background_load_images,
            args=(list(self.file_pairs), self.image_queue, self.target_dimensions), # Pass a copy
            daemon=True
        )
        self.loading_thread.start()

        # Start processing the queue
        self.root.after(100, self._process_queue) # Check queue every 100ms

    def _background_load_images(self, file_pairs_copy, q, target_dims):
        """Load images in a background thread."""
        logging.info(f"[Thread] Starting background image loading for {len(file_pairs_copy)} images.")
        for i, (video_path, image_path) in enumerate(file_pairs_copy):
            try:
                logging.debug(f"[Thread] Loading image {i}: {image_path}")
                img = Image.open(image_path)
                resized_img = self.prepare_image(img, target_dims)
                if resized_img:
                    q.put((i, resized_img)) # Put index and PIL image on queue
                    logging.debug(f"[Thread] Queued image {i}")
                else:
                     logging.error(f"[Thread] Failed to prepare image {i}: {image_path}")

            except Exception as e:
                logging.error(f"[Thread] Error loading {image_path}: {e}", exc_info=True)
        q.put(None) # Signal completion
        logging.info("[Thread] Background image loading finished.")

    def _process_queue(self):
        """Process images from the background queue in the main thread."""
        try:
            while not self.image_queue.empty():
                item = self.image_queue.get_nowait()
                if item is None:
                    # Loading finished
                    logging.info("Finished processing image queue.")
                    self.loading_label.grid_remove()
                    if not self.loaded_images:
                         logging.error("No images were successfully loaded!")
                         self.info_label.configure(text="Error: Failed to load any images.")
                    elif 0 not in self.loaded_images:
                         logging.warning("First image (index 0) not loaded yet, waiting...")
                         # It might still be in the queue, check again soon
                         self.root.after(50, self._process_queue)
                         return # Don't stop checking yet
                    else:
                         # Ensure first image is shown if loading finished quickly
                         if self.label.image is None:
                              self.show_image(0)
                    return # Stop checking

                index, pil_image = item
                logging.debug(f"Processing queued image index {index}")
                self.loaded_images[index] = pil_image # Store PIL image

                # Update loading label
                total = len(self.file_pairs)
                loaded_count = len(self.loaded_images)
                self.loading_label.configure(text=f"Loading {loaded_count}/{total} images...")

                # Show the first image as soon as it's ready
                if index == 0 and self.label.image is None:
                    logging.info("First image loaded, displaying.")
                    self.show_image(0)

        except queue.Empty:
            pass # Queue is empty, check again later
        except Exception as e:
            logging.error(f"Error processing image queue: {e}", exc_info=True)

        # Schedule next check if loading is not finished
        if self.loading_thread and self.loading_thread.is_alive() or not self.image_queue.empty():
             self.root.after(100, self._process_queue)


    def prepare_image(self, img, target_dims):
        """Resize PIL image to fit target dimensions."""
        try:
            target_width, target_height = target_dims
            logging.debug(f"Preparing image with target dimensions: {target_width}x{target_height}")

            if target_width <= 0 or target_height <= 0:
                logging.error(f"Invalid target dimensions: {target_width}x{target_height}")
                return None

            img.thumbnail((target_width, target_height), Image.Resampling.LANCZOS)
            logging.debug(f"Resized image to: {img.size}")
            return img

        except Exception as e:
            logging.error(f"Error preparing image: {e}", exc_info=True)
            return None

    def show_image(self, index, force_update=False):
        """Display image and file info at given index from loaded_images."""
        logging.debug(f"Attempting to show image at index: {index}")

        # Check if file_pairs is populated
        if not self.file_pairs:
            logging.warning("show_image called before file_pairs are loaded.")
            self.label.configure(image='')
            self.info_label.configure(text="Loading file list...")
            return

        if not (0 <= index < len(self.file_pairs)):
            logging.error(f"Invalid image index: {index} for {len(self.file_pairs)} files")
            return # Invalid index

        self.current_index = index
        video_path, image_path = self.file_pairs[index]

        # Check if image is loaded
        loaded_item = self.loaded_images.get(index)

        if loaded_item is None:
            logging.warning(f"Image {index} not loaded yet.")
            # Optionally show a placeholder/loading text on the label
            self.label.configure(image='') # Clear previous image
            self.label.image = None
            self.info_label.configure(text=f"Loading image {index+1}...\nVideo: {os.path.basename(video_path)}\nScreen: {os.path.basename(image_path)}")
            return

        try:
            # If it's already a PhotoImage and we don't force update, use it
            if isinstance(loaded_item, ImageTk.PhotoImage) and not force_update:
                 photo = loaded_item
                 logging.debug(f"Using cached PhotoImage for index {index}")
            else:
                 # It's a PIL image, or we need to force update (resize)
                 pil_image = loaded_item if not isinstance(loaded_item, ImageTk.PhotoImage) else loaded_item.pil_image
                 # Resize based on current target dimensions
                 resized_pil_image = self.prepare_image(pil_image.copy(), self.target_dimensions) # Use copy
                 if not resized_pil_image:
                      raise ValueError("Failed to resize PIL image")

                 photo = ImageTk.PhotoImage(resized_pil_image)
                 photo.pil_image = resized_pil_image # Keep reference to PIL image if needed later
                 self.loaded_images[index] = photo # Cache the PhotoImage
                 logging.debug(f"Created and cached PhotoImage for index {index} with size {resized_pil_image.size}")

            self.label.configure(image=photo)
            self.label.image = photo # Keep reference

            # Update file info
            video_name = os.path.basename(video_path)
            image_name = os.path.basename(image_path)
            logging.debug(f"Showing file info for: {video_name} -> {image_name}")
            self.info_label.configure(
                text=f"Video: {video_name}\nScreen: {image_name}"
            )

        except Exception as e:
             logging.error(f"Error displaying image {index}: {e}", exc_info=True)
             self.label.configure(image='')
             self.label.image = None
             self.info_label.configure(text=f"Error loading image {index+1}")


    def on_mouse_wheel(self, event):
        """Handle mouse wheel navigation"""
        if not self.file_pairs: # Check file_pairs instead of photos
            return

        if event.num == 5 or event.delta < 0:      # Scroll down
            next_index = min(self.current_index + 1, len(self.file_pairs) - 1)
            if next_index != self.current_index:
                 self.show_image(next_index)
        elif event.num == 4 or event.delta > 0:    # Scroll up
            prev_index = max(self.current_index - 1, 0)
            if prev_index != self.current_index:
                 self.show_image(prev_index)

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
                
                # Remove moved files from lists and update index
                new_index = self.cleanup_moved_files()

                # Update UI with batch move results
                status = f"✓ Moved {moved_count} files to {dest_key}"
                if failed_count > 0:
                    status += f"\nFailed to move {failed_count} files"
                self.info_label.configure(text=status)

                # Update display
                if self.file_pairs: # Check file_pairs
                    self.show_image(new_index) # Show image at the adjusted index
                else:
                    self.label.configure(image='')
                    self.label.image = None
                    self.info_label.configure(text="No more images to process")

            except Exception as e:
                logging.error(f"Error moving files: {e}", exc_info=True)
                self.info_label.configure(text=f"Error moving files: {str(e)}")

    def cleanup_moved_files(self):
        """Remove moved files from tracking lists"""
        """Remove moved files and adjust loaded_images keys."""
        original_indices = {vp: i for i, (vp, _) in enumerate(self.file_pairs)}
        indices_to_remove = sorted([
            original_indices[vp] for vp in self.moved_files if vp in original_indices
        ], reverse=True)

        if not indices_to_remove:
            return self.current_index # No changes needed

        logging.debug(f"Indices to remove: {indices_to_remove}")

        # Remove from file_pairs
        for idx in indices_to_remove:
            if 0 <= idx < len(self.file_pairs):
                logging.debug(f"Removing file pair at index {idx}: {self.file_pairs[idx][0]}")
                del self.file_pairs[idx]
            else:
                 logging.warning(f"Attempted to remove out-of-bounds index {idx}")


        # Adjust loaded_images dictionary keys
        new_loaded_images = {}
        current_new_idx = 0
        for old_idx in sorted(self.loaded_images.keys()):
            # Find the original video path for this old index using the original_indices map reverse lookup (less efficient but needed)
            original_vp = None
            for vp, oi in original_indices.items():
                 if oi == old_idx:
                      original_vp = vp
                      break

            if original_vp and original_vp not in self.moved_files:
                # If the file corresponding to old_idx was NOT moved, keep it with the new index
                new_loaded_images[current_new_idx] = self.loaded_images[old_idx]
                current_new_idx += 1
            else:
                 logging.debug(f"Discarding loaded image data for moved index {old_idx}")


        self.loaded_images = new_loaded_images
        self.moved_files.clear() # Clear the set for the next batch

        # Calculate the new current_index
        # It should be the index of the *first file that was NOT removed* at or after the original current_index
        new_current_index = 0
        found_new_index = False
        temp_idx_map = {vp: i for i, (vp, _) in enumerate(self.file_pairs)} # Map of remaining files to their new indices
        for old_idx in range(self.current_index, len(original_indices)):
             original_vp = None
             for vp, oi in original_indices.items():
                  if oi == old_idx:
                       original_vp = vp
                       break
             if original_vp in temp_idx_map: # Check if this file still exists
                  new_current_index = temp_idx_map[original_vp]
                  found_new_index = True
                  break

        if not found_new_index:
             # If all files from current onwards were removed, point to the last remaining file or 0
             new_current_index = max(0, len(self.file_pairs) - 1) if self.file_pairs else 0


        logging.debug(f"Cleanup complete. New file_pairs count: {len(self.file_pairs)}. New loaded_images count: {len(self.loaded_images)}. New index: {new_current_index}")
        return new_current_index


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

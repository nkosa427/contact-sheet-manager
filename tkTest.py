# Standard library imports
import tkinter as tk
from PIL import Image, ImageTk  # Python Imaging Library for image processing
import os
from threading import Thread, Lock  # Threading for non-blocking operations
from queue import Queue  # Thread-safe queue for message passing
from concurrent.futures import ThreadPoolExecutor  # Managed thread pool for parallel tasks

class ImageViewer:
    """
    A full-featured image viewer with the following capabilities:
    - Preloads images in background for smooth navigation
    - Supports dynamic window resizing while maintaining aspect ratio
    - Uses thread pool for concurrent image processing
    - Provides progress feedback during loading
    - Memory-efficient with image caching
    - Responsive UI with non-blocking operations
    """
    def __init__(self, root, folder_path):
        # Core configuration
        self.PRELOAD_COUNT = 15  # Number of images to cache ahead/behind current image
        self.thread_pool = ThreadPoolExecutor(max_workers=4)  # Limit concurrent threads
        
        # Message passing and state tracking
        self.progress_queue = Queue()  # Thread-safe message queue for loading progress
        self.loading_complete = False   # Flag to track initial loading state
        self.preload_running = False    # Flag to prevent multiple preload operations
        
        # Storage and caching
        self.images = []                # List of image file paths
        self.image_cache = {}           # Cache of loaded PIL Image objects
        self.current_index = 0          # Currently displayed image index
        
        # Window setup and configuration
        self.root = root
        self.folder_path = folder_path
        self._setup_window()
        self._setup_ui()
        self._bind_events()
        
        # Initialize loading process
        self._start_loading()

    def _setup_window(self):
        """Configure the main window properties"""
        self.root.title("Image Viewer")
        self.root.state('zoomed')       # Start in maximized state
        self.root.minsize(800, 600)     # Prevent window from becoming too small
        
        # Configure grid system for dynamic resizing
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

    def _setup_ui(self):
        """Create and configure UI elements"""
        # Main image display with black background for better visibility
        self.label = tk.Label(self.root, bg='black')
        self.label.grid(row=0, column=0, sticky='nsew')  # Expand in all directions
        
        # Loading indicator with white text on black background
        self.loading_label = tk.Label(
            self.root, 
            text="Loading images...", 
            font=('Arial', 12),
            bg='black',
            fg='white'
        )
        self.loading_label.grid(row=0, column=0, sticky='nsew')

    def _bind_events(self):
        """Bind necessary events to the root window"""
        self.root.bind('<Configure>', self.on_window_resize)
        self.root.bind('<MouseWheel>', self.on_mouse_wheel)
        self.root.bind('<Button-4>', self.on_mouse_wheel)
        self.root.bind('<Button-5>', self.on_mouse_wheel)
        self.root.bind('<Escape>', lambda e: self.root.quit())

    def _start_loading(self):
        """Start the image loading process in a separate thread"""
        Thread(target=self.preload_images, daemon=True).start()
        self.root.after(100, self._check_progress)

    def on_window_resize(self, event=None):
        """Handle window resize events"""
        if self.loading_complete and hasattr(self, 'current_index'):
            self.load_image(self.current_index)

    def _prepare_image(self, img):
        """Prepare image for current window size"""
        # Get current window dimensions with padding
        width = self.root.winfo_width() - 20
        height = self.root.winfo_height() - 20
        
        if width <= 0 or height <= 0:
            return None
            
        # Calculate dimensions maintaining aspect ratio
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

    def load_image(self, index):
        """Load and display image"""
        if not 0 <= index < len(self.images) or not self.loading_complete:
            return
            
        try:
            self.current_index = index
            path = self.images[index]
            img = self.image_cache[path]
            photo = self._prepare_image(img)
            
            self.label.configure(image=photo)
            self.label.image = photo
            
        except Exception as e:
            print(f"Error loading image: {e}")
            self.label.configure(text=f"Error loading image: {e}")

    # Remove resize-related methods and keep only essential ones
    def preload_images(self):
        """Load all images"""
        try:
            image_paths = self.get_all_images()
            total = len(image_paths)
            
            for i, path in enumerate(image_paths):
                try:
                    img = Image.open(path)
                    self.image_cache[path] = img
                    self.images.append(path)
                    self.progress_queue.put(f"Loading images... ({i+1}/{total})")
                except Exception as e:
                    print(f"Error preloading {path}: {e}")
            
            self.root.after(1, self._finish_loading_safely)
            
        except Exception as e:
            print(f"Fatal error in preload_images: {e}")
            self.loading_complete = True

    def _check_progress(self):
        """Process progress updates from queue with timeout"""
        try:
            # Use timeout to prevent blocking
            message = self.progress_queue.get(timeout=0.1)
            self.loading_label.configure(text=message)
            self.root.update_idletasks()
        except (Queue.Empty, AttributeError):
            pass
        finally:
            if not self.loading_complete:
                self.root.after(100, self._check_progress)

    def _finish_loading_safely(self):
        """Safely finish loading in main thread"""
        try:
            self.loading_complete = True
            self.loading_label.grid_remove()
            if self.images:
                self.load_image(0)
                # Start background preloading after a delay
                self.root.after(500, lambda: self.thread_pool.submit(self._background_preload))
        except Exception as e:
            print(f"Error in finish_loading: {e}")

    def _background_preload(self):
        """Background preloading with state tracking"""
        if self.preload_running:
            return
            
        try:
            self.preload_running = True
            current = self.current_index
            start_idx = max(0, current - self.PRELOAD_COUNT)
            end_idx = min(len(self.images), current + self.PRELOAD_COUNT + 1)
            
            for idx in range(start_idx, end_idx):
                if idx != current and not self.loading_complete:
                    return
                if idx != current:
                    self._prepare_image(self.image_cache[self.images[idx]])
        except Exception as e:
            print(f"Error in background preload: {e}")
        finally:
            self.preload_running = False

    def get_all_images(self):
        """
        Scan folder for supported image files
        Returns: sorted list of image file paths
        """
        image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp')
        images = []
        try:
            for file in os.listdir(self.folder_path):
                if file.lower().endswith(image_extensions):
                    images.append(os.path.join(self.folder_path, file))
            return sorted(images)
        except Exception as e:
            print(f"Error accessing folder: {e}")
            return []

    def on_mouse_wheel(self, event):
        """
        Handle mouse wheel events for navigation
        Scroll down/wheel down: next image
        Scroll up/wheel up: previous image
        """
        if event.num == 5 or event.delta < 0:      # Scroll down
            self.load_image(self.current_index + 1)
        elif event.num == 4 or event.delta > 0:    # Scroll up
            self.load_image(self.current_index - 1)
    
    def __del__(self):
        """Cleanup resources"""
        try:
            self.thread_pool.shutdown(wait=False)
            self.image_cache.clear()
        except:
            pass

def main():
    """
    Main function to initialize and run the image viewer application
    Returns:
        tuple: (exit_code, app_instance) where exit_code is 0 for success
              and app_instance is the ImageViewer instance
    """
    try:
        root = tk.Tk()
        folder_path = r"X:\downloads\misc\notready_\jd2vpn\simpcity\MyaRyker\30-60s_\customScreens_"
        app = ImageViewer(root, folder_path)
        root.mainloop()
        return 0, app  # Return both exit code and app instance
    except Exception as e:
        print(f"Application error: {e}")
        return 1, None

if __name__ == "__main__":
    exit_code, viewer = main()
    exit(exit_code)

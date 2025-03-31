# System Patterns: Contact Sheet Manager

## Architecture Overview

The application follows a simple monolithic structure within a single main script (`contact_sheet_manager.py`) using the Tkinter GUI toolkit.

```mermaid
graph TD
    A[main()] --> B(FolderSelector Class);
    B -- User Selects Folder --> C(ImageViewer Class);
    C -- Displays Image --> D{Tkinter UI};
    D -- User Input (Keyboard/Mouse) --> C;
    C -- File Operations --> E[OS File System];
    C -- Play Video --> F[External Player (MPC-HC)];
    B -- Drag & Drop --> G[tkinterdnd2];
    C -- Image Loading/Resizing --> H[Pillow (PIL)];
    A -- Logging --> I[viewer_debug.log];
    C -- Logging --> I;
    B -- Logging --> I;
```

## Key Components & Patterns

1.  **GUI (Tkinter):**
    *   Uses standard Tkinter widgets (Frame, Label, Button, Entry).
    *   Employs `tkinterdnd2` for drag-and-drop support.
    *   Two main UI states managed by classes:
        *   `FolderSelector`: Initial window for path input.
        *   `ImageViewer`: Main window for viewing images and sorting files.
    *   Layout uses the `.grid()` geometry manager.
    *   Window state is managed (`zoomed`, `withdraw`, `deiconify`).

2.  **State Management:**
    *   Application state (current image index, selected folder path, moved files) is primarily managed within the `ImageViewer` and `FolderSelector` class instances.

3.  **File Handling:**
    *   Uses the `os` module for path manipulation (`os.path.join`, `os.path.basename`), directory listing (`os.listdir`), checking existence (`os.path.exists`), creating directories (`os.makedirs`), and moving files (`os.rename`).
    *   Relies on specific folder structure (`customScreens_` subfolder) and filename conventions (image name = video name + extension).
    *   Includes logic to find the `customScreens_` folder (`find_custom_screens_folder`).
    *   Includes logic to match video files with corresponding images (`get_matching_files`).
    *   Creates a `keep` directory and subdirectories ('A', 'F', 'R') for sorted files.
    *   Includes cleanup for empty directories (`cleanup_empty_dirs`).

4.  **Image Processing (Pillow):**
    *   Uses `PIL.Image.open()` to load images.
    *   Uses `PIL.Image.resize()` with `Image.Resampling.LANCZOS` for scaling images to fit the window.
    *   Uses `PIL.ImageTk.PhotoImage` to prepare images for display in Tkinter.
    *   *Note:* `image_utils.py` contains related functions (`get_supported_images`, `calculate_dimensions`) but they are not currently imported or used by `contact_sheet_manager.py`.

5.  **External Process Interaction:**
    *   Uses `subprocess.Popen` to launch an external video player (MPC-HC) with a hardcoded path.

6.  **Logging:**
    *   Uses the standard `logging` module.
    *   Configured to log to both the console (`StreamHandler`) and a file (`viewer_debug.log`).
    *   Logs informational messages, debug details, warnings, and errors.

7.  **Event Handling:**
    *   Uses Tkinter's `.bind()` method for keyboard events (`<KeyPress-space>`, `<KeyRelease-space>`, 'a', 'f', 'r', 'p', `<Escape>`) and mouse events (`<MouseWheel>`, `<Button-4>`, `<Button-5>`).

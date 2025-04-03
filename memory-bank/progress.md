# Progress: Contact Sheet Manager

## Current Status (Asynchronous Loading Implemented)

-   The core functionality described in `projectbrief.md` and `productContext.md` is implemented.
-   **Image loading is now asynchronous**, preventing the application from freezing when loading images. A background thread handles loading/resizing, and the main thread updates the UI via a queue.
-   The application can be launched, allows folder selection (including drag-and-drop), displays images progressively as they load, and handles sorting via keyboard shortcuts ('a', 'f', 'r') by moving files.
-   Window resizing is handled, re-rendering the current image to fit the new dimensions.
-   Video playback via 'p' key is implemented using a hardcoded path to MPC-HC.
-   Basic navigation (mouse wheel) and batch moving (space key) are present and work with the asynchronous loading model.
-   Logging to console and file (`viewer_debug.log`) is set up.
-   Memory Bank is updated to reflect the asynchronous loading implementation.

## What Works

-   Folder selection GUI (`FolderSelector`).
-   Image viewing GUI (`ImageViewer`).
-   **Asynchronous loading and progressive display** of images from the `customScreens_` folder, keeping the UI responsive.
-   Matching videos with corresponding images based on filename.
-   Keyboard shortcuts ('a', 'f', 'r') for categorizing files.
-   Moving categorized video and image files to `keep/[A|F|R]/` subdirectories.
-   Mouse wheel navigation between images.
-   Basic batch move functionality using the space key.
-   Playing associated video using 'p' (if MPC-HC is at the expected path).
-   Drag-and-drop folder selection.
-   Logging.
-   **Window resizing:** Images are re-rendered to fit the new window size.

## What's Left to Build / Potential Improvements

*(Based on initial review, no specific features are requested yet, but potential areas for improvement exist)*

-   **Error Handling:** Enhance robustness (e.g., what if `customScreens_` is missing, what if files are locked).
-   **Configuration:** Make the video player path configurable instead of hardcoded. Allow customization of sorting keys/folders.
-   **UI/UX:** Improve visual feedback during operations (loading indicator is present, but could be enhanced). Consider UI refinements.
-   **Code Quality:** Refactor potential redundancies (e.g., image handling in `contact_sheet_manager.py` vs. `image_utils.py`). Improve modularity. Add more comments/docstrings, especially around threading logic.
-   **Cross-Platform Compatibility:** Address Windows-specific elements (hardcoded path).
-   **Testing:** Implement unit or integration tests, particularly for the file moving and asynchronous loading logic.
-   **Concurrency Robustness:** While basic threading is implemented, further testing under edge conditions (e.g., very fast user actions during load, errors during background load) might reveal areas for improvement.

## Known Issues

-   Heavy reliance on a specific external application (MPC-HC) at a hardcoded path.
-   The functions in `image_utils.py` are not currently used.
-   Potential complexity introduced by threading (e.g., harder debugging if race conditions occur, though current implementation aims to minimize this).

## Project Decisions Evolution

-   **[Timestamp]** Initial Memory Bank setup based on existing code. Project structure and functionality documented.
-   **2025-04-03 08:53** Implemented asynchronous image loading using `threading` and `queue.Queue` to resolve GUI freezing issue. Refactored related image handling functions and added resize handling. Updated Memory Bank accordingly.

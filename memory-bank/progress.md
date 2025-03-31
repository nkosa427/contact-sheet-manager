# Progress: Contact Sheet Manager

## Current Status (Initialization)

-   The core functionality described in `projectbrief.md` and `productContext.md` appears to be implemented in the existing `contact_sheet_manager.py` script.
-   The application can be launched, allows folder selection (including drag-and-drop), displays images, and handles sorting via keyboard shortcuts ('a', 'f', 'r') by moving files.
-   Video playback via 'p' key is implemented using a hardcoded path to MPC-HC.
-   Basic navigation (mouse wheel) and batch moving (space key) are present.
-   Logging to console and file (`viewer_debug.log`) is set up.
-   Memory Bank has been initialized with core documentation files based on the initial code review.

## What Works

-   Folder selection GUI (`FolderSelector`).
-   Image viewing GUI (`ImageViewer`).
-   Loading and displaying images from the `customScreens_` folder.
-   Matching videos with corresponding images based on filename.
-   Keyboard shortcuts ('a', 'f', 'r') for categorizing files.
-   Moving categorized video and image files to `keep/[A|F|R]/` subdirectories.
-   Mouse wheel navigation between images.
-   Basic batch move functionality using the space key.
-   Playing associated video using 'p' (if MPC-HC is at the expected path).
-   Drag-and-drop folder selection.
-   Logging.

## What's Left to Build / Potential Improvements

*(Based on initial review, no specific features are requested yet, but potential areas for improvement exist)*

-   **Error Handling:** Enhance robustness (e.g., what if `customScreens_` is missing, what if files are locked).
-   **Configuration:** Make the video player path configurable instead of hardcoded. Allow customization of sorting keys/folders.
-   **UI/UX:** Improve visual feedback during operations. Add progress indicators for loading large numbers of images. Consider UI refinements.
-   **Code Quality:** Refactor potential redundancies (e.g., image handling in `contact_sheet_manager.py` vs. `image_utils.py`). Improve modularity. Add comments/docstrings.
-   **Cross-Platform Compatibility:** Address Windows-specific elements (hardcoded path).
-   **Testing:** Implement unit or integration tests.

## Known Issues (from initial review)

-   Heavy reliance on a specific external application (MPC-HC) at a hardcoded path.
-   Potential performance issues when loading a very large number of images (synchronous loading in the main thread).
-   The functions in `image_utils.py` are not currently used.

## Project Decisions Evolution

-   **[Timestamp]** Initial Memory Bank setup based on existing code. Project structure and functionality documented.

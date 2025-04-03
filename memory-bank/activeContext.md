# Active Context: Contact Sheet Manager

## Current Focus

-   Addressing the application freezing issue during image loading.

## Recent Changes

-   Implemented asynchronous image loading using `threading` and `queue.Queue` in `contact_sheet_manager.py` to prevent the GUI from freezing.
-   Refactored image loading logic (`load_all_images`, `prepare_image`, `show_image`) to support background processing and on-demand `PhotoImage` creation.
-   Added handling for window resizing (`on_resize`) to update target image dimensions.
-   Updated file cleanup logic (`cleanup_moved_files`) to work with the new `loaded_images` dictionary structure.

## Next Steps

-   Update `memory-bank/systemPatterns.md` to reflect the new asynchronous loading pattern.
-   Update `memory-bank/progress.md` to document the fix and any new potential issues/improvements.
-   Complete the task by presenting the result to the user.

## Active Decisions & Considerations

-   Used standard Python libraries (`threading`, `queue`) for concurrency to maintain simplicity and avoid external dependencies for this core feature.
-   Stored loaded images as PIL `Image` objects in `loaded_images` and convert to `PhotoImage` only when needed for display or resizing, improving memory efficiency slightly and simplifying thread safety (PIL Images are generally safer to pass between threads than Tkinter PhotoImages).
-   Added `on_resize` handler to ensure images are re-rendered correctly if the window size changes after initial load.

## Important Patterns & Preferences

-   Maintain clear, concise documentation in Markdown format.
-   Update Memory Bank files incrementally as tasks are performed or new information is discovered.

## Learnings & Insights

-   Asynchronous loading significantly improves GUI responsiveness, especially with many images.
-   Managing state between the background thread (loading/resizing) and the main thread (UI updates) requires careful use of thread-safe structures like `queue.Queue` and scheduling UI updates with `root.after`.
-   Handling window resizing requires recalculating target dimensions and potentially re-rendering the currently displayed image.
-   Cleaning up data structures (`file_pairs`, `loaded_images`) after file moves needs careful index management, especially when indices shift.
-   The project uses Tkinter for the GUI and Pillow for image handling.
-   There's a potential redundancy between image handling logic in `contact_sheet_manager.py` and the functions in `image_utils.py`.
-   File sorting logic relies on specific keyboard inputs ('a', 'f', 'r') and moves files into corresponding subdirectories within a `keep` folder.
-   Video playback relies on an external application (MPC-HC) at a hardcoded path.

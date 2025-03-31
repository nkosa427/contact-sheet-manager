# Active Context: Contact Sheet Manager

## Current Focus

-   Initializing the project's Memory Bank.
-   Documenting the existing codebase and project structure.

## Recent Changes

-   Created `memory-bank/projectbrief.md`.
-   Created `memory-bank/productContext.md`.

## Next Steps

-   Create `memory-bank/systemPatterns.md`.
-   Create `memory-bank/techContext.md`.
-   Create `memory-bank/progress.md`.
-   Populate these files with initial information derived from the existing code.

## Active Decisions & Considerations

-   The Memory Bank structure follows the standard defined in the custom instructions.
-   Initial content is based purely on the analysis of `contact_sheet_manager.py` and `image_utils.py`.

## Important Patterns & Preferences

-   Maintain clear, concise documentation in Markdown format.
-   Update Memory Bank files incrementally as tasks are performed or new information is discovered.

## Learnings & Insights

-   The project uses Tkinter for the GUI and Pillow for image handling.
-   There's a potential redundancy between image handling logic in `contact_sheet_manager.py` and the functions in `image_utils.py`.
-   File sorting logic relies on specific keyboard inputs ('a', 'f', 'r') and moves files into corresponding subdirectories within a `keep` folder.
-   Video playback relies on an external application (MPC-HC) at a hardcoded path.

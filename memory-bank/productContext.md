# Product Context: Contact Sheet Manager

## Problem Solved

Users often have large collections of video files accompanied by automatically generated contact sheets (screenshots). Manually reviewing and sorting these videos based on the content shown in the screenshots can be tedious and time-consuming. This tool aims to streamline this process.

## How It Works (User Workflow)

1.  **Launch:** The user starts the application.
2.  **Select Folder:** The user is prompted to select (or drag-and-drop) a root folder. This folder should contain the video files directly and have a subfolder named `customScreens_` containing the corresponding screenshot images. The image filename must match the video filename (e.g., `my_video.mp4` and `my_video.mp4.jpg`).
3.  **View & Sort:** The application displays the first screenshot image, scaled to fit the window.
    -   The user reviews the image.
    -   The user presses 'a', 'f', or 'r' on the keyboard to categorize the image and its associated video.
    -   The application moves both the video file and the image file to a newly created subfolder (`A`, `F`, or `R`) inside a `keep` folder within the original root directory.
    -   The application automatically displays the next image.
4.  **Navigation:** The user can navigate between images using the mouse wheel.
5.  **Batch Move:** Holding the `Space` key while pressing 'a', 'f', or 'r' moves all preceding images (since the last move or the beginning) along with the current one to the selected category.
6.  **Play Video:** The user can press 'p' to open the video file associated with the currently displayed image in MPC-HC (requires MPC-HC to be installed at the expected path).
7.  **Exit:** The user can press `Escape` to confirm and return to the folder selection screen or close the application.

## User Experience Goals

-   **Efficiency:** Significantly speed up the process of sorting videos based on visual content from screenshots.
-   **Simplicity:** Provide an intuitive interface focused on the core task of viewing and categorizing.
-   **Keyboard-Driven:** Optimize for keyboard shortcuts to minimize mouse usage during the sorting process.

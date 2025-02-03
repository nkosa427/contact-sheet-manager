import os
from PIL import Image, ImageTk

def get_supported_images(folder_path):
    """
    Scan a folder for supported image files.
    
    Arguments:
        folder_path (str): Path to folder containing images
        
    Returns:
        list: Sorted list of full image file paths
        
    Supported formats:
        - JPEG (.jpg, .jpeg)
        - PNG (.png)
        - GIF (.gif)
        - BMP (.bmp)
    
    Note: Uses case-insensitive extension matching
    """
    # Define supported image formats
    image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp')
    images = []
    
    try:
        # Scan directory for matching files
        for file in os.listdir(folder_path):
            if file.lower().endswith(image_extensions):
                # Build full path and add to list
                images.append(os.path.join(folder_path, file))
        return sorted(images)  # Sort for consistent ordering
    except Exception as e:
        print(f"Error accessing folder: {e}")
        return []

def calculate_dimensions(original_width, original_height, target_width, target_height):
    """
    Calculate new dimensions while maintaining aspect ratio.
    
    Arguments:
        original_width (int): Source image width
        original_height (int): Source image height
        target_width (int): Desired maximum width
        target_height (int): Desired maximum height
        
    Returns:
        tuple: (new_width, new_height) that fits within target dimensions
        while maintaining original aspect ratio
        
    Algorithm:
        1. Calculate aspect ratios of original and target
        2. Compare ratios to determine limiting dimension
        3. Scale other dimension proportionally
    """
    # Calculate aspect ratios
    original_ratio = original_width / original_height
    new_ratio = target_width / target_height
    
    if new_ratio > original_ratio:
        # Height is the limiting factor
        new_height = target_height
        new_width = int(new_height * original_ratio)
    else:
        # Width is the limiting factor
        new_width = target_width
        new_height = int(new_width / original_ratio)
    
    return new_width, new_height

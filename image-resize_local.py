import os
from pathlib import Path
from PIL import Image

# --- Core Resizing Function ---

def resize_image_and_save(input_path, output_path, target_width, target_height, resample_method='LANCZOS'):
    """
    Resize an image file to target resolution and save it to a new location.
    
    Args:
        input_path (str): Path to the source image file
        output_path (str): Path where the resized image will be saved
        target_width (int): Desired width in pixels
        target_height (int): Desired height in pixels
        resample_method (str): Resampling filter ('LANCZOS', 'BICUBIC', 'BILINEAR', 'NEAREST')
    
    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        # Open the image
        img = Image.open(input_path)
        original_size = img.size
        
        # Map string to PIL constant
        resample_filters = {
            'LANCZOS': Image.LANCZOS,
            'BICUBIC': Image.BICUBIC,
            'BILINEAR': Image.BILINEAR,
            'NEAREST': Image.NEAREST
        }
        
        # Get the resampling filter, defaulting to LANCZOS
        resample = resample_filters.get(resample_method.upper(), Image.LANCZOS)
        
        # Resize the image
        resized_img = img.resize((target_width, target_height), resample)
        
        # Ensure the output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Save the resized image
        # Use the original image's format if possible, otherwise default to JPEG
        image_format = img.format if img.format else 'JPEG'
        resized_img.save(output_path, format=image_format)
        
        return True, f"Resized from {original_size[0]}x{original_size[1]} to {target_width}x{target_height}"
        
    except FileNotFoundError:
        return False, "Input file not found."
    except Exception as e:
        return False, f"Resize error for {Path(input_path).name}: {str(e)}"

# --- Helper Functions for User Input ---

def get_folder_path(prompt):
    """Get a valid folder path from user input."""
    while True:
        folder_path = input(prompt).strip()
        
        # Remove surrounding quotes
        if folder_path.startswith(('"', "'")) and folder_path.endswith(('"', "'")):
            folder_path = folder_path[1:-1]
        
        if not folder_path:
            print("Please enter a path.")
            continue
        
        return folder_path

def get_target_resolution():
    """Get target width and height from user."""
    print("\nEnter target resolution:")
    
    while True:
        try:
            width = int(input("Width (pixels): ").strip())
            height = int(input("Height (pixels): ").strip())
            
            if width <= 0 or height <= 0:
                print("Width and height must be positive numbers.")
                continue
            
            return width, height
        except ValueError:
            print("Please enter valid numbers.")

def get_resample_method():
    """Get resampling method from user."""
    print("\nChoose resampling method:")
    print("1. LANCZOS (Highest quality, Recommended)")
    print("2. BICUBIC (High quality)")
    print("3. BILINEAR (Medium quality)")
    print("4. NEAREST (Lowest quality)")
    
    methods = {
        "1": "LANCZOS",
        "2": "BICUBIC",
        "3": "BILINEAR",
        "4": "NEAREST"
    }
    
    while True:
        method_choice = input("\nEnter choice (1-4, default=1): ").strip() or "1"
        
        if method_choice in methods:
            return methods[method_choice]
        else:
            print("Invalid choice. Please enter 1-4.")


# --- Main Logic ---

def process_folder():
    """Main function to handle folder-based image resizing."""
    print("=" * 70)
    print("          LOCAL FOLDER IMAGE RESIZER")
    print("=" * 70)

    # 1. Get input parameters
    input_folder = get_folder_path("Enter the path to the folder containing original images: ")
    output_folder = get_folder_path("Enter the path for the output folder (will be created if it doesn't exist): ")
    width, height = get_target_resolution()
    method = get_resample_method()

    # 2. Setup
    input_path = Path(input_folder)
    output_path_root = Path(output_folder)
    
    if not input_path.is_dir():
        print(f"\n❌ Error: Input folder not found at {input_folder}")
        return

    # Create output folder if it doesn't exist
    output_path_root.mkdir(parents=True, exist_ok=True)
    
    print(f"\n✓ Starting resize process...")
    print(f"  Input: {input_folder}")
    print(f"  Output: {output_folder}")
    print(f"  Target Resolution: {width}x{height} using {method}")
    print("-" * 50)
    
    supported_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff']
    file_count = 0
    success_count = 0
    
    # 3. Process images
    for item in input_path.iterdir():
        if item.is_file() and item.suffix.lower() in supported_extensions:
            file_count += 1
            input_file_path = str(item)
            output_file_path = str(output_path_root / item.name)
            
            print(f"[{file_count}] Processing: {item.name}...")
            
            success, message = resize_image_and_save(
                input_file_path, 
                output_file_path, 
                width, 
                height, 
                method
            )
            
            if success:
                success_count += 1
                print(f"    ✓ Success. {message}")
            else:
                print(f"    ❌ Failed. {message}")

    # 4. Final summary
    print("\n" + "=" * 50)
    print("✅ RESIZE PROCESS COMPLETE!")
    print(f"Total files found: {file_count}")
    print(f"Successful resizes: {success_count}")
    print(f"Failed resizes: {file_count - success_count}")
    print(f"Resized images saved to: {output_folder}")
    print("=" * 50)


if __name__ == "__main__":
    try:
        process_folder()
    except KeyboardInterrupt:
        print("\n\nProcess interrupted by user.")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {str(e)}")

    input("\nPress Enter to exit...")
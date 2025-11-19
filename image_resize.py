import pandas as pd
import requests
import os
import time
import re
from urllib.parse import urlparse, parse_qs
from pathlib import Path
from datetime import datetime
import keyboard
from PIL import Image

def clean_filename(filename):
    """
    Clean up a string to be safe for use as a filename.
    """
    # Remove or replace invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove extra spaces and replace with underscores
    filename = re.sub(r'\s+', '_', filename.strip())
    # Remove leading/trailing dots and underscores
    filename = filename.strip('._')
    # Limit length to avoid filesystem issues
    if len(filename) > 100:
        filename = filename[:100]
    # Ensure it's not empty
    if not filename:
        filename = "unnamed"
    return filename

def convert_dropbox_url(url):
    """
    Convert various Dropbox URL formats to direct download links.
    
    Handles:
    - dropbox.com/s/... (sharing links)
    - dropbox.com/scl/fi/... (new sharing format)
    - dropbox.com/sh/... (folder sharing)
    - dl.dropboxusercontent.com (already direct)
    """
    if not url or 'dropbox' not in url.lower():
        return url, False
    
    # If it's already a direct dropboxusercontent link, keep it
    if 'dropboxusercontent.com' in url:
        return url, True
    
    # Handle different Dropbox URL formats
    if 'dropbox.com' in url:
        if '?' in url:
            base_url = url.split('?')[0]
            query_params = url.split('?')[1]
            
            # Remove existing dl parameter and add dl=1
            params = []
            for param in query_params.split('&'):
                if not param.startswith('dl='):
                    params.append(param)
            params.append('dl=1')
            
            direct_url = f"{base_url}?{'&'.join(params)}"
        else:
            direct_url = f"{url}?dl=1"
        
        return direct_url, True
    
    return url, False

def get_file_extension_from_url(url, content_type=''):
    """  Extract file extension from URL or content type, with special handling for Dropbox."""
    # For Dropbox URLs, try to get extension from the original filename in the URL
    if 'dropbox' in url.lower():
        # Look for filename patterns in Dropbox URLs
        # Pattern: /filename.ext? or /filename.ext&
        match = re.search(r'/([^/]+\.[a-zA-Z0-9]+)[\?&]', url)
        if match:
            filename = match.group(1)
            extension = os.path.splitext(filename)[1]
            if extension:
                return extension.lower()
    
    # Try to get extension from URL path
    url_path = urlparse(url).path
    if url_path:
        original_filename = os.path.basename(url_path)
        if '.' in original_filename and not original_filename.endswith('.'):
            extension = os.path.splitext(original_filename)[1]
            if extension:
                return extension.lower()
    
    # Try to get extension from Content-Type header
    if content_type:
        content_type = content_type.lower()
        if 'jpeg' in content_type or 'jpg' in content_type:
            return '.jpg'
        elif 'png' in content_type:
            return '.png'
        elif 'webp' in content_type:
            return '.webp'
    
    return '.jpg'  # Default fallback

def resize_image(file_path, target_width, target_height, resample_method='LANCZOS'):
    """
    Resize an image file to target resolution.
    
    Args:
        file_path: Path to the image file
        target_width: Desired width in pixels
        target_height: Desired height in pixels
        resample_method: Resampling filter ('LANCZOS', 'BICUBIC', 'BILINEAR', 'NEAREST')
    
    Returns:
        tuple: (success: bool, message: str, original_size: tuple, new_size: tuple)
    """
    try:
        # Open the image
        img = Image.open(file_path)
        original_size = img.size
        
        # Map string to PIL constant
        resample_filters = {
            'LANCZOS': Image.LANCZOS,
            'BICUBIC': Image.BICUBIC,
            'BILINEAR': Image.BILINEAR,
            'NEAREST': Image.NEAREST
        }
        
        resample = resample_filters.get(resample_method.upper(), Image.LANCZOS)
        
        # Resize the image
        resized_img = img.resize((target_width, target_height), resample)
        
        # Save back to the same file
        resized_img.save(file_path)
        
        return True, f"Resized from {original_size[0]}x{original_size[1]} to {target_width}x{target_height}", original_size, (target_width, target_height)
        
    except Exception as e:
        return False, f"Resize error: {str(e)}", None, None

def download_image(url, folder_path, prefix="image", batch_id="", sequence_num=1, delimiter="_", timeout=30, resize_config=None):
    """
    Download an image from URL and save it with sequential numbering.
    
    Args:
        url (str): Image URL
        folder_path (str): Path to save the image
        prefix (str): Prefix for the filename (from Excel column)
        batch_id (str): Batch identifier (column name)
        sequence_num (int): Sequential number for this download
        delimiter (str): Character(s) to separate parts of filename
        timeout (int): Request timeout in seconds
        resize_config (dict): Optional resize configuration with 'width', 'height', 'method'
    
    Returns:
        tuple: (success: bool, message: str, filename: str)
    """
    try:
        # Convert Dropbox URLs to direct download links
        original_url = url
        url, is_dropbox = convert_dropbox_url(url)
        
        # Add headers to mimic a browser request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # For Dropbox, we might need to handle redirects
        response = requests.get(url, headers=headers, timeout=timeout, stream=True, allow_redirects=True)
        response.raise_for_status()
        
        # Check if we got HTML instead of an image (common Dropbox issue)
        content_type = response.headers.get('Content-Type', '').lower()
        
        if 'text/html' in content_type and is_dropbox:
            return False, "Dropbox link returned HTML page instead of image - link may be invalid or private", ""
        
        # Additional check: read first few bytes to verify it's actually an image
        first_chunk = next(response.iter_content(chunk_size=1024), b'')
        if first_chunk:
            # Check for common image file signatures
            image_signatures = [
                b'\xFF\xD8\xFF',  # JPEG
                b'\x89PNG\r\n\x1a\n',  # PNG
                b'GIF87a',  # GIF87a
                b'GIF89a',  # GIF89a
                b'RIFF',  # WebP (starts with RIFF)
                b'BM',  # BMP
                b'II*\x00',  # TIFF (little endian)
                b'MM\x00*',  # TIFF (big endian)
            ]
            
            is_image = any(first_chunk.startswith(sig) for sig in image_signatures)
            
            if not is_image and is_dropbox:
                return False, "Downloaded content doesn't appear to be an image file", ""
        
        # Get file extension
        extension = get_file_extension_from_url(original_url, content_type)
        
        # Clean the prefix and batch_id
        clean_prefix = clean_filename(str(prefix))
        clean_batch_id = clean_filename(batch_id)
        
        # Create filename with sequential numbering
        # Format: prefix_batchID_0001.jpg
        if batch_id:
            filename = f"{clean_prefix}{delimiter}{clean_batch_id}{delimiter}{sequence_num:04d}{extension}"
        else:
            filename = f"{clean_prefix}{delimiter}{sequence_num:04d}{extension}"

        # Handle potential duplicate filenames (shouldn't happen with sequential numbering, but just in case)
        file_path = os.path.join(folder_path, filename)
        counter = 1
        original_filename = filename
        while os.path.exists(file_path):
            name_part, ext = os.path.splitext(original_filename)
            filename = f"{name_part}_dup{counter}{ext}"
            file_path = os.path.join(folder_path, filename)
            counter += 1
        
        # Download and save the image
        with open(file_path, 'wb') as f:
            # Write the first chunk we already read
            f.write(first_chunk)
            # Write the rest
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        # Verify the downloaded file has content
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            os.remove(file_path)
            return False, "Downloaded file is empty", ""
        
        success_message = f"Downloaded: {filename}"
        if is_dropbox:
            success_message += f" (from Dropbox, {file_size:,} bytes)"
        
        # Resize if configured
        if resize_config:
            resize_success, resize_msg, orig_size, new_size = resize_image(
                file_path, 
                resize_config['width'], 
                resize_config['height'],
                resize_config.get('method', 'LANCZOS')
            )
            if resize_success:
                success_message += f" | {resize_msg}"
            else:
                success_message += f" | {resize_msg}"
        
        return True, success_message, filename
        
    except requests.exceptions.Timeout:
        return False, "Request timed out", ""
    except requests.exceptions.RequestException as e:
        error_msg = f"Request failed: {str(e)}"
        if is_dropbox:
            error_msg += " (Try checking if Dropbox link is public and accessible)"
        return False, error_msg, "Dropbox link inaccessible."
    except Exception as e:
        return False, f"Error: {str(e)}", ""

def get_file_path():
    """Get the Excel/CSV file path from user input."""
    while True:
        file_path = input("Enter the path to your Excel or CSV file: ").strip()
        
        # Remove quotes if user wrapped the path in quotes
        if file_path.startswith('"') and file_path.endswith('"'):
            file_path = file_path[1:-1]
        if file_path.startswith("'") and file_path.endswith("'"):
            file_path = file_path[1:-1]
        
        if not file_path:
            print("Please enter a file path.")
            continue
            
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            print("Please check the path and try again.")
            continue
            
        file_extension = Path(file_path).suffix.lower()
        if file_extension not in ['.xlsx', '.xls', '.csv']:
            print(f"Unsupported file format: {file_extension}")
            print("Please use .xlsx, .xls, or .csv files.")
            continue
            
        return file_path

def get_delimiter():
    """Get the delimiter to use between filename parts."""
    print("\nChoose delimiter to separate filename parts:")
    print("1. _ (underscore) - default")
    print("2. - (hyphen)")
    print("3. . (dot)")
    print("4. Custom delimiter")
    
    while True:
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == "1":
            return "_"
        elif choice == "2":
            return "-"
        elif choice == "3":
            return "."
        elif choice == "4":
            custom = input("Enter your custom delimiter: ")
            # Clean the delimiter to avoid filesystem issues
            custom = re.sub(r'[<>:"/\\|?*]', '_', custom)
            return custom
        else:
            print("Invalid choice. Please enter 1-4.")
            continue

def get_resize_config():
    """Ask user if they want to resize images and get configuration."""
    print("\n" + "="*50)
    print("IMAGE RESIZE OPTION")
    print("="*50)
    print("Do you want to resize all downloaded images to a specific resolution?")
    print("This is useful for standardizing image sizes for machine learning, web use, etc.")
    
    resize = input("\nResize images? (y/n): ").strip().lower()
    
    if resize not in ['y', 'yes']:
        return None
    
    print("\nEnter target resolution:")
    
    while True:
        try:
            width = int(input("Width (pixels): ").strip())
            height = int(input("Height (pixels): ").strip())
            
            if width <= 0 or height <= 0:
                print("Width and height must be positive numbers.")
                continue
            
            break
        except ValueError:
            print("Please enter valid numbers.")
    
    print("\nChoose resampling method:")
    print("1. LANCZOS (highest quality, slowest) - RECOMMENDED")
    print("2. BICUBIC (high quality, faster)")
    print("3. BILINEAR (medium quality, fast)")
    print("4. NEAREST (lowest quality, fastest)")
    
    while True:
        method_choice = input("\nEnter choice (1-4, default=1): ").strip()
        
        if not method_choice:
            method_choice = "1"
        
        methods = {
            "1": "LANCZOS",
            "2": "BICUBIC",
            "3": "BILINEAR",
            "4": "NEAREST"
        }
        
        if method_choice in methods:
            method = methods[method_choice]
            break
        else:
            print("Invalid choice. Please enter 1-4.")
    
    config = {
        'width': width,
        'height': height,
        'method': method
    }
    
    print(f"\n✓ Images will be resized to {width}x{height} using {method} method")
    
    return config

def load_and_show_columns(file_path):
    """Load the file and show available columns."""
    try:
        file_extension = Path(file_path).suffix.lower()
        
        print(f"\nReading file: {file_path}")
        
        if file_extension in ['.xlsx', '.xls']:
            df = pd.read_excel(file_path)
        else:  # .csv
            df = pd.read_csv(file_path)
        
        print(f"File loaded successfully! Found {len(df)} rows.")
        print("\nAvailable columns:")
        for i, col in enumerate(df.columns, 1):
            # Show a preview of the data in each column
            sample_values = df[col].dropna().head(2).tolist()
            sample_text = ", ".join(str(v)[:50] for v in sample_values)
            print(f"{i}. {col} (e.g., {sample_text})")
        
        return df
        
    except Exception as e:
        print(f"Error reading file: {str(e)}")
        return None

def get_column_choice(df, purpose=""):
    """Get user's column choice."""
    while True:
        choice = input(f"\nEnter the column name or number (1-{len(df.columns)}) {purpose}: ").strip()
        
        if choice.isdigit():
            col_index = int(choice) - 1
            if 0 <= col_index < len(df.columns):
                return df.columns[col_index]
            else:
                print(f"Invalid number. Please enter a number between 1 and {len(df.columns)}.")
                continue
        else:
            if choice in df.columns:
                return choice
            else:
                print(f"Column '{choice}' not found. Please try again.")
                continue

def create_batch_data(df, url_column, prefix_column):
    """Create clean batch data from the dataframe."""
    clean_data = []
    dropbox_count = 0
    
    for idx, row in df.iterrows():
        url = str(row[url_column]).strip()
        prefix = str(row[prefix_column]).strip()
        
        # Skip rows with missing or invalid data
        if url and url != 'nan' and prefix and prefix != 'nan':
            if 'dropbox' in url.lower():
                dropbox_count += 1
            clean_data.append({
                'url': url,
                'prefix': prefix,
                'row_number': idx + 2  # +2 because Excel is 1-indexed and has headers
            })
    
    if dropbox_count > 0:
        print(f"ℹ️  Detected {dropbox_count} Dropbox links - these will be automatically converted to direct download links")
    
    return clean_data

def format_time(seconds):
    """
    Formats a duration in seconds into a human-readable string (Hh Mm Ss).
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    
    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    parts.append(f"{seconds}s")
    
    return " ".join(parts)

def main():
    print("=" * 70)
    print("          BATCH IMAGE DOWNLOADER")
    print("      (with Dropbox support, sequential numbering & resize)")
    print("=" * 70)
    
    # Step 1: Get file path and load data
    file_path = get_file_path()
    df = load_and_show_columns(file_path)
    
    if df is None:
        print("Failed to load file. Exiting.")
        input("Press Enter to exit...")
        return
    
    # Step 2: Get delimiter choice
    delimiter = get_delimiter()
    
    # Step 2.5: Get resize configuration
    resize_config = get_resize_config()
    
    # Step 3: Get prefix column (this will be used for all batches)
    print(f"\nFirst, choose the column to use for filename prefixes (will be used for all batches):")
    print("Available columns:")
    for i, col in enumerate(df.columns, 1):
        sample_values = df[col].dropna().head(2).tolist()
        sample_text = ", ".join(str(v)[:50] for v in sample_values)
        print(f"{i}. {col} (e.g., {sample_text})")
    
    prefix_column = get_column_choice(df, "for filename prefixes")
    
    # Step 4: Set up output folder
    custom_folder_name = input("\nEnter a custom folder name for downloads (leave blank for default): ").strip()

    if custom_folder_name:
        base_folder_name = clean_filename(custom_folder_name)
    else:
        base_file_name = os.path.splitext(os.path.basename(file_path))[0]
        base_folder_name = f"{base_file_name}_downloaded_images"

    output_folder = base_folder_name
    counter = 1

    while os.path.exists(output_folder):
        output_folder = f"{base_folder_name}_{counter}"
        counter += 1

    os.makedirs(output_folder)
    
    # Set up logging
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_file_path = os.path.join(output_folder, f"download_log_{timestamp}.txt")
    
    batches = []  # Store all batch information
    
    try:
        log_file = open(log_file_path, "w", encoding="utf-8")

        def log_message(message, also_print=True):
            """Writes a message to the log file and optionally prints it."""
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"[{current_time}] {message}\n"
            log_file.write(log_entry)
            log_file.flush()  # Ensure immediate write
            
            if also_print:
                print(message)

        log_message(f"Batch Image Downloader Started (with Dropbox support & resize)")
        log_message(f"File: {file_path}")
        log_message(f"Output folder: {os.path.abspath(output_folder)}")
        log_message(f"Prefix column: {prefix_column}")
        log_message(f"Delimiter: '{delimiter}'")
        
        if resize_config:
            log_message(f"Resize: {resize_config['width']}x{resize_config['height']} ({resize_config['method']})")
        else:
            log_message(f"Resize: Disabled")
        
        # Step 5: Batch selection loop
        while True:
            print("\n" + "="*50)
            print("BATCH SETUP")
            print("="*50)
            
            # Show available URL columns (exclude already chosen prefix column and non-URL looking columns)
            print(f"\nChoose a column containing image URLs for this batch:")
            print("Available columns:")
            for i, col in enumerate(df.columns, 1):
                if col != prefix_column:  # Don't show the prefix column as URL option
                    sample_values = df[col].dropna().head(2).tolist()
                    sample_text = ", ".join(str(v)[:50] for v in sample_values)
                    print(f"{i}. {col} (e.g., {sample_text})")
            
            url_column = get_column_choice(df, "containing image URLs")
            
            # Create batch data
            batch_data = create_batch_data(df, url_column, prefix_column)
            
            if not batch_data:
                print(f"No valid data found in columns '{url_column}' and '{prefix_column}'.")
                continue
            
            # Clean column name for batch ID
            batch_id = clean_filename(url_column)
            
            print(f"\nBatch Preview:")
            print(f"- URL Column: '{url_column}'")
            print(f"- Batch ID: '{batch_id}'")
            print(f"- Found {len(batch_data)} valid entries")
            print(f"- Files will be named: prefix{delimiter}{batch_id}{delimiter}0001.jpg, etc.")
            
            # Show first few examples
            print(f"\nFirst few filenames will be:")
            for i, item in enumerate(batch_data[:3], 1):
                clean_prefix = clean_filename(item['prefix'])
                print(f"  {clean_prefix}{delimiter}{batch_id}{delimiter}{i:04d}.jpg")
            if len(batch_data) > 3:
                print(f"  ... and {len(batch_data) - 3} more")
            
            # Confirm this batch
            confirm = input(f"\nAdd this batch to download queue? (y/n): ").strip().lower()
            if confirm in ['y', 'yes']:
                batches.append({
                    'data': batch_data,
                    'url_column': url_column,
                    'batch_id': batch_id
                })
                print(f"✓ Batch '{batch_id}' added to queue!")
            
            # Ask for more batches
            more = input(f"\nAdd another batch? (y/n): ").strip().lower()
            if more not in ['y', 'yes']:
                break
        
        if not batches:
            print("No batches selected. Exiting.")
            log_message("No batches selected. Exiting.")
            return
        
        # Step 6: Show summary and confirm download
        print("\n" + "="*60)
        print("DOWNLOAD SUMMARY")
        print("="*60)
        
        total_files = sum(len(batch['data']) for batch in batches)
        print(f"Total batches: {len(batches)}")
        print(f"Total files to download: {total_files}")
        
        if resize_config:
            print(f"Resize: {resize_config['width']}x{resize_config['height']} ({resize_config['method']})")
        
        for i, batch in enumerate(batches, 1):
            print(f"  Batch {i}: {batch['batch_id']} ({len(batch['data'])} files)")
        
        log_message(f"\nDownload Summary:")
        log_message(f"Total batches: {len(batches)}")
        log_message(f"Total files: {total_files}")
        
        final_confirm = input(f"\nStart downloading all batches? (y/n): ").strip().lower()
        if final_confirm not in ['y', 'yes']:
            log_message("Download cancelled by user.")
            print("Download cancelled.")
            return
        
        # Step 7: Download all batches
        log_message("\n" + "=" * 60)
        log_message("STARTING BATCH DOWNLOADS")
        log_message("=" * 60)
        
        overall_start_time = time.time()
        total_successful = 0
        total_failed = 0
        all_downloaded_files = []
        
        interrupted = False  # Flag to track interruption
        
        for batch_num, batch in enumerate(batches, 1):
            if interrupted:
                break
                
            batch_start_time = time.time()
            log_message(f"\n{'='*40}")
            log_message(f"BATCH {batch_num}/{len(batches)}: {batch['batch_id']}")
            log_message(f"{'='*40}")
            
            batch_successful = 0
            batch_failed = 0
            
            for seq_num, item in enumerate(batch['data'], 1):
                # Check for 'Esc' keypress at the beginning of each loop iteration
                if keyboard.is_pressed('esc'):
                    print("\n\nESC key pressed. Stopping download...")
                    log_message("\nESC key pressed. Download interrupted by user.")
                    interrupted = True
                    break  # Exit the inner loop
                
                url = item['url']
                prefix = item['prefix']
                row_num = item['row_number']
                
                elapsed_time = time.time() - overall_start_time
                log_message(f"\n[Batch {batch_num}/{len(batches)}] [{seq_num}/{len(batch['data'])}] Row {row_num}: {prefix}")
                log_message(f"    Elapsed: {format_time(elapsed_time)}")
                log_message(f"    URL: {url}")
                
                success, message, filename = download_image(
                    url, output_folder, prefix, batch['batch_id'], seq_num, delimiter, resize_config=resize_config
                )
                
                if success:
                    batch_successful += 1
                    total_successful += 1
                    all_downloaded_files.append(filename)
                    log_message(f"    ✓ {message}")
                else:
                    batch_failed += 1
                    total_failed += 1
                    log_message(f"    ✗ {message}")
                
                # Add delay between downloads
                if seq_num < len(batch['data']) or batch_num < len(batches):
                    time.sleep(1)
            
            # Batch summary
            batch_time = time.time() - batch_start_time
            log_message(f"\nBatch {batch_num} Complete:")
            log_message(f"  Time: {format_time(batch_time)}")
            log_message(f"  Successful: {batch_successful}")
            log_message(f"  Failed: {batch_failed}")
        
        # Final summary
        total_time = time.time() - overall_start_time
        
        log_message("\n" + "=" * 70)
        if interrupted:
            log_message("DOWNLOAD INTERRUPTED BY USER!")
        else:
            log_message("ALL BATCHES COMPLETE!")
        log_message("=" * 70)
        log_message(f"Total time: {format_time(total_time)}")
        log_message(f"Total successful downloads: {total_successful}")
        log_message(f"Total failed downloads: {total_failed}")
        log_message(f"Images saved to: {os.path.abspath(output_folder)}")
        
        if resize_config:
            log_message(f"All images resized to: {resize_config['width']}x{resize_config['height']}")
        
        if all_downloaded_files:
            log_message(f"\nSample downloaded files:")
            for filename in all_downloaded_files[:10]:
                log_message(f"  - {filename}")
            if len(all_downloaded_files) > 10:
                log_message(f"  ... and {len(all_downloaded_files) - 10} more")
        
        print(f"\nAll downloads complete! Check the folder: {os.path.abspath(output_folder)}")
        print(f"Log file: {log_file_path}")
        
    finally:
        if 'log_file' in locals() and not log_file.closed:
            log_file.close()

    input("\nPress Enter to exit...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDownload interrupted by user.")
        input("Press Enter to exit...")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {str(e)}")
        input("Press Enter to exit...")

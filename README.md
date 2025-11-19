Setup Instructions
Before you can run the script, you need to install Python and the required libraries: Pandas and the Pillow (PIL) library.
1. Install Python (If Not Already Installed)
Ensure you have a recent version of Python (3.6 or newer) installed on your machine.
•	Check: Open your terminal (or Command Prompt) and type:
Bash
python --version
or
python3 --version
If you see a version number (e.g., Python 3.10.6), you're ready.
•	Install: If Python is not found, download and install it from the official Python website. Make sure to check the box that says "Add Python to PATH" during installation.
3. Install Required Libraries
You must install the Pillow (PIL) library, which handles the image resizing, and Pandas, which was used for data handling in the original script but is now included for structure.
•	Open your terminal/command prompt and run the following command:
Bash
pip install Pillow pandas
If you used python3 to check the version in step 1, you may need to use pip3 here:
Bash
pip3 install Pillow pandas
________________________________________

## Script Usage Instructions
Once Python and the libraries are installed, you can use the script to resize all images in a local folder.
### Prepare Your Environment
1.	Download the Script: Save the provided Python Script.
2.	Organize Images: Create a new folder or copy the path of an existing folder. This will be your Input Folder containing all the images you want to resize.

### Run the Script
Method 1: Double-Click (Easiest)
1.	Find image_resize.py in File Explorer
2.	Right-click → "Open with" → "Python"
3.	A Command Prompt window will open
Method 2: Command Prompt (Recommended)
1.	Open Command Prompt
2.	Navigate to script location: 
3.	cd C:\Users\YourName\Documents\ImageDownloader
4.	Run the script: 
5.	python image_resize.py

### Follow the Prompts
Resize Option
  IMAGE RESIZE OPTION
  Do you want to resize all downloaded images to a specific resolution?
  
  Resize images? (y/n):
  •	Press y if you want all images resized to the same dimensions
  •	Press n to keep original sizes
  •	When to resize: 
  o	Machine learning training (need uniform sizes)
  o	Web thumbnails
  o	Standardizing mixed-size images
  If you chose y:
  Enter target resolution:
  Width (pixels): 1024
  Height (pixels): 768
  
  Choose resampling method:
  1. LANCZOS (highest quality, slowest) - RECOMMENDED
  2. BICUBIC (high quality, faster)
  3. BILINEAR (medium quality, fast)
  4. NEAREST (lowest quality, fastest)
  
  Enter choice (1-4, default=1):
  •	Enter your desired width and height
  •	For quality, use option 1 (LANCZOS)
  •	For speed with large batches, use option 2 or 3

4. Review Results
•	Once the script finishes, it will print a summary of the successful and failed resizes.
•	The newly resized images will be available in the Output Folder you specified.
•	A log file (e.g., resize_log_2025-11-20_15-13-06.txt) will also be created in the output folder, detailing the processing outcome for every single file.


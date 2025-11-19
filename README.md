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
2. Install Required Libraries
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
The script will guide you through the process by asking for four pieces of information:
Prompt	                Example Input	                                                          Description
Input                   Folder Path	C:\Users\YourName\Desktop\Original_Photos	                  The path to the folder containing the images you want to resize.
Output                  Folder Path	C:\Users\YourName\Desktop\Resized_Photos_800x600	          The path where the new, resized images will be saved. The script will create this folder if it doesn't exist.
Width (pixels)	        800                                                                     The desired new width of the images.
Height (pixels)	        600                                                                     The desired new height of the images.

Resampling Choice	1 (for LANCZOS)	Select the quality/speed trade-off for the resizing algorithm. LANCZOS (option 1) is generally recommended for the best results.
4. Review Results
•	Once the script finishes, it will print a summary of the successful and failed resizes.
•	The newly resized images will be available in the Output Folder you specified.
•	A log file (e.g., resize_log_2025-11-20_15-13-06.txt) will also be created in the output folder, detailing the processing outcome for every single file.


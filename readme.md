# Download Scraper
Automatically navigates website, edits textboxes, downloads a file and uplods file over FTP

## Virtual display
The script uses Xvfb to initiate a virtual display to use on server environments. Use the config 'virtual_display' in masterconfig.ini to activate it. THIS FEATURE ONLY WORKS ON LINUX

## Configuration
Manual configuration is REQUIRED. Use the file masterconfig.ini to add configurations such as the ftp address, username, password and access token to get push notifications from Pushbullet

## How to install
1. Install python3.10-venv using the appropriate package manager in your distro
2. Install chromium using the appropriate package manager in your distro
3. Install xvfb using the appropriate package manager in your distro
4. Check if git is installed by running the command "git --version"
5. If you get no output, install git
6. Clone the repository using the command "git clone https://github.com/RedGlare96/DownloadScraper"
7. Change directory into cloned directory
8. Create a new virtual environment using the command "python -m venv <enter_name_here>"
7. Activate venv using the command "source <venv_name>/bin/activate"
9. Install dependencies with the command "pip install -r requirements.txt"
10. Open the file 'masterconfig.ini' with your favourite text editor and provide values for ftp, pushbullet token and browser settings
11. Save file
12. Run script with the command "python historic_scraper.py"

## Setting up cron jobs
The virtual environment can be activated automatically by using the python executable in the venv directory. Eg: "/path/to/cloned/direcotry/venv_name/python historic_scraper.py"
Using the python executable in the venv direcotry will automatically activate the virtual environemnt when the cron job is triggered

## Tracking updates
1. Cd into cloned direcotry
2. Use the command "git pull origin master"
This command will automatically update the files in the cloned direcotry to the new version tracked in Git


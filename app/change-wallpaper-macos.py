import argparse, subprocess, logging, os, requests
import getpass
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox
import sys
import glob
from PIL import Image, ImageTk

def create_plist_content(interval, script_path, username, city):
    """Create the launchd plist content"""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.theonlysinjin.ai-wallpaper</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Applications/AI Wallpaper.app/Contents/MacOS/AI Wallpaper</string>
        <string>change</string>
        <string>--city</string>
        <string>{city}</string>
    </array>
    <key>StartInterval</key>
    <integer>{interval}</integer>
    <key>RunAtLoad</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/Users/{username}/Library/Logs/wallpaper-changer.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/{username}/Library/Logs/wallpaper-changer.error.log</string>
</dict>
</plist>"""

def install_service(interval, city):
    """Install the wallpaper changer as a launchd service"""
    try:
        # Get username and script path
        username = getpass.getuser()
        script_path = os.path.abspath(__file__)
        
        # Create plist directory if it doesn't exist
        plist_dir = Path(f"/Users/{username}/Library/LaunchAgents")
        plist_dir.mkdir(parents=True, exist_ok=True)
        
        # Create plist file
        plist_path = plist_dir / "com.theonlysinjin.ai-wallpaper.plist"
        plist_content = create_plist_content(interval, script_path, username, city)
        
        with open(plist_path, 'w') as f:
            f.write(plist_content)
        
        # Load the service
        subprocess.run(['launchctl', 'unload', str(plist_path)], 
                      capture_output=True, check=False)
        subprocess.run(['launchctl', 'load', '-w', str(plist_path)], 
                      capture_output=True, check=True)
        
        print(f"Service installed successfully. Will change wallpaper every {interval} seconds.")
        print(f"Logs will be written to: ~/Library/Logs/wallpaper-changer.log")
        
    except Exception as e:
        print(f"Failed to install service: {e}")
        raise

def uninstall_service():
    """Uninstall the wallpaper changer service"""
    try:
        username = getpass.getuser()
        plist_path = Path(f"/Users/{username}/Library/LaunchAgents/com.theonlysinjin.ai-wallpaper.plist")
        
        if plist_path.exists():
            # Unload the service
            subprocess.run(['launchctl', 'unload', '-w', str(plist_path)], 
                         capture_output=True, check=True)
            # Remove the plist file
            plist_path.unlink()
            print("Service uninstalled successfully")
        else:
            print("Service is not installed")
            
    except Exception as e:
        print(f"Failed to uninstall service: {e}")
        raise

def fetch_available_cities():
    """Fetch available cities from the GitHub repository"""
    owner = "theonlysinjin"
    repo = "wallpaper-generator"
    api_url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
    
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        release_data = response.json()
        
        cities = set()
        for asset in release_data['assets']:
            if asset['name'].endswith('.png'):
                # Extract city name from the asset name and remove the .png extension
                city_name = asset['name'].replace(".png", "").split('_')[0].replace(".", " ")
                cities.add(city_name)
        
        return sorted(cities)
    except Exception as e:
        print(f"Error fetching cities: {str(e)}")
        return []

def create_gui():
    """Create a simple GUI for installing/uninstalling the service"""
    root = tk.Tk()
    root.title("Wallpaper Changer")
    
    # Set window size and position it in the center
    window_width = 350
    window_height = 350
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2
    root.geometry(f'{window_width}x{window_height}+{x}+{y}')
    
    # Create main frame
    frame = ttk.Frame(root, padding="20")
    frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
    
    # Interval selection
    ttk.Label(frame, text="Check every:").grid(row=0, column=0, pady=5)
    interval_var = tk.StringVar(value="600")
    interval_choices = [
        ("10 minutes", "600"),
        ("30 minutes", "1800"),
        ("1 hour", "3600"),
        ("2 hours", "7200")
    ]
    interval_menu = ttk.Combobox(frame, textvariable=interval_var, values=[f"{t[0]}" for t in interval_choices], state="readonly")
    interval_menu.grid(row=0, column=1, pady=5)
    interval_menu.set("10 minutes")
    
    # Moved description label closer to interval selection
    ttk.Label(frame, text="New images are generated every 2 hours.").grid(row=1, column=0, columnspan=2, pady=1)  # Adjusted padding
    
    # Create a listbox for available cities
    ttk.Label(frame, text="Available Cities:").grid(row=2, column=0, pady=5)
    city_listbox = tk.Listbox(frame, height=5)
    city_listbox.grid(row=2, column=1, pady=5)

    # Fetch and display available cities
    available_cities = fetch_available_cities()
    for city in available_cities:
        city_listbox.insert(tk.END, city)
    
    def handle_install():
        try:
            # Get the seconds value from the selected interval
            selected_text = interval_var.get()
            interval = next(int(t[1]) for t in interval_choices if t[0] == selected_text)
            
            # Get the selected city from the listbox
            selected_city = city_listbox.get(city_listbox.curselection())
            
            install_service(interval, selected_city)
            messagebox.showinfo("Success", f"Service installed successfully.\nWallpaper will change every {selected_text}.\nCity: {selected_city}.")
            root.quit()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to install service: {str(e)}")

    def handle_uninstall():
        try:
            uninstall_service()
            messagebox.showinfo("Success", "Service uninstalled successfully.")
            root.quit()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to uninstall service: {str(e)}")
    
    def handle_refresh():
        try:
            # Get the selected city from the listbox
            selected_city = city_listbox.get(city_listbox.curselection())
            directory_path = os.path.expanduser("~/Pictures/Wallpapers")  # Ensure the directory path is set
            
            # Fetch the latest wallpaper for the selected city
            new_wallpaper = fetch_latest_city_wallpaper(selected_city, directory_path)
            
            if new_wallpaper:
                messagebox.showinfo("Success", f"Successfully fetched wallpaper for {selected_city}.")
            else:
                messagebox.showerror("Error", f"Failed to fetch wallpaper for {selected_city}.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def handle_preview():
        try:
            # Get the selected city from the listbox
            selected_city = city_listbox.get(city_listbox.curselection())
            directory_path = os.path.expanduser("~/Pictures/Wallpapers")
            
            # Fetch the latest wallpaper for the selected city
            new_wallpaper = fetch_latest_city_wallpaper(selected_city, directory_path)
            
            if new_wallpaper:
                # Open the image and display it in a popup
                img = Image.open(new_wallpaper)
                img.show()  # This will open the default image viewer
            else:
                messagebox.showerror("Error", f"No wallpaper found for {selected_city}.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

    # Buttons
    ttk.Button(frame, text="Preview Wallpaper", command=handle_preview).grid(row=3, column=0, columnspan=2, pady=5)  # New preview button
    ttk.Button(frame, text="Refresh Wallpaper", command=handle_refresh).grid(row=4, column=0, columnspan=2, pady=5)  # New refresh button
    ttk.Button(frame, text="Install Service", command=handle_install).grid(row=5, column=0, columnspan=2, pady=5)
    ttk.Button(frame, text="Uninstall Service", command=handle_uninstall).grid(row=6, column=0, columnspan=2, pady=5)
    root.mainloop()

def fetch_current_wallpaper():
  try:
    script = 'tell app "finder" to get posix path of (get desktop picture as alias)'
    p = subprocess.check_output(['osascript', '-e', script])
    return(p.decode("utf-8").strip())
  except Exception:
    return("")

def change_wallpaper(wallpaper):
    cmd = f"osascript -e 'tell application \"System Events\" to tell every desktop to set picture to \"{wallpaper}\" as POSIX file'"
    output = os.popen(cmd).read()
    if output:
        logging.error(output)
        return False
    else:
        return True

def fetch_latest_city_wallpaper(city, directory_path):
    # GitHub API endpoint for latest release
    owner = "theonlysinjin"
    repo = "wallpaper-generator"
    api_url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
    
    try:
        # Get latest release info
        response = requests.get(api_url)
        response.raise_for_status()
        release_data = response.json()
        
        # Get the release tag name and normalise
        tag_name = release_data.get('tag_name', 'unknown').replace("generate/", "")
        city_name = city.replace(" ", ".")
        
        # Check for existing file with this tag
        existing_files = glob.glob(os.path.join(directory_path, f"*{city_name}*{tag_name}.png"))
        if existing_files:
            print(f"Found existing wallpaper for {city} with tag {tag_name}")
            return existing_files[0]
        
        for asset in release_data['assets']:
            if city_name in asset['name'] and asset['name'].endswith('.png'):
                # Download the asset
                download_url = asset['browser_download_url']
                image_response = requests.get(download_url)
                image_response.raise_for_status()
                
                # Modify filename to include tag name
                base_name = os.path.splitext(asset['name'])[0]
                new_filename = f"{base_name}_{tag_name}.png"
                
                # Save to local directory
                local_path = os.path.join(directory_path, new_filename)
                with open(local_path, 'wb') as f:
                    f.write(image_response.content)
                return local_path

        print(f"No wallpaper found for {city} in the latest release")
        return None
    except Exception as e:
        print(f"Error fetching wallpaper: {str(e)}")
        return None

def main():
    # Check if script is double-clicked or run from terminal
    if len(sys.argv) == 1:
        create_gui()
        return

    parser = argparse.ArgumentParser(description="MacOS Wallpaper Changer")
    parser.add_argument('command', choices=['change', 'install', 'uninstall'],
                       help='Command to execute')
    parser.add_argument('--interval', type=int, default=600,
                       help='Interval in seconds between wallpaper changes (default: 600)')
    parser.add_argument('--city', type=str, help='City for which to change the wallpaper')
    
    args = parser.parse_args()
    
    if args.command == 'install':
        install_service(args.interval)
    elif args.command == 'uninstall':
        uninstall_service()
    elif args.command == 'change':
        WALLPAPER_FOLDER = os.path.expanduser("~/Pictures/Wallpapers")
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                # logging.FileHandler('wallpaper_changer.log'),
                logging.StreamHandler()
            ]
        )
        
        # Ensure wallpaper directory exists
        os.makedirs(WALLPAPER_FOLDER, exist_ok=True)

        # Fetch new wallpaper for a specific city (you might want to make this configurable)
        city = args.city if args.city else "Cape Town"  # Default city
        new_wallpaper = fetch_latest_city_wallpaper(city, WALLPAPER_FOLDER)
        
        # Change the wallpaper if we successfully fetched one
        if new_wallpaper:
            if change_wallpaper(new_wallpaper):
                logging.info(f"Changed wallpaper to: {new_wallpaper}")
            else:
                logging.error("Failed to change wallpaper")
        else:
            logging.error(f"Failed to fetch new wallpaper for {city}")

if __name__ == "__main__":
    main()

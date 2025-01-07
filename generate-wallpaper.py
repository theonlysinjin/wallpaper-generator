#!env python3
import os, re, requests, sys, glob, random, subprocess, io, argparse, json, getpass
from PIL import Image, PngImagePlugin
from datetime import datetime
from openai import OpenAI
import weather_data

def rand_choice(current_item, items_list):
  if len(set(items_list)) <= 1:
    return current_item

  random_item = random.choice(items_list)
  if (random_item == current_item):
    return(rand_choice(current_item, items_list))
  else:
    return(random_item)

def fetch_current_wallpaper():
  try:
    script = 'tell app "finder" to get posix path of (get desktop picture as alias)'
    p = subprocess.check_output(['osascript', '-e', script])
    return(p.decode("utf-8").strip())
  except Exception:
    return("")

def change_wallpaper(wallpaper):
  cmd = f"""
osascript -e "tell application \\"System Events\\" to tell every desktop to set picture to \\"{wallpaper}\\" as POSIX file"
"""
  os.system(cmd)

def generate_filename(directory_path, prompt):
  safe_filename = re.sub(r'[^\w\s]', '', prompt.replace(' ', '_'))
  trimmed_filename = safe_filename[:220]
  timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
  filename = f"{directory_path}/{trimmed_filename}_{timestamp}"
  return(filename)

def generate_image(client, prompt, directory_path):
  print("Generating Image from prompt:")
  print(prompt)
  response = client.images.generate(
    model="dall-e-3",
    prompt=prompt,
    size="1792x1024",
    quality="hd",
    n=1
  )

  generatedImage = requests.get(response.data[0].url).content
  filename = generate_filename(directory_path, prompt)
  newImage = Image.open(io.BytesIO(generatedImage))

  pngMetaData = PngImagePlugin.PngInfo()
  pngMetaData.add_text('Image Prompt', prompt)
  pngMetaData.add_text('Revised Prompt', response.data[0].revised_prompt)

  image_filename = f"{filename}.png"
  newImage.save(image_filename, pnginfo=pngMetaData)
  # Create JSON file with extra information
  json_data = {
    "prompt": prompt,
    "filename": image_filename,
    "description": response.data[0].revised_prompt,
    "command": " ".join(sys.argv)
  }
  json_filename = f"{filename}.json"
  with open(json_filename, 'w') as json_file:
    json.dump(json_data, json_file, indent=2)

  return image_filename

def generate_prompts(client, count, prompt):
  response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
      {"role": "system", "content": "You are a creative assistant specialized in generating unique, special, random, and mesmerizing prompts for wallpaper creation using DALL-E 3."},
      {"role": "system", "content": "Each prompt should be a standalone idea for a wallpaper, with no additional text or empty spaces between prompts."},
      {"role": "system", "content": "Generate %s prompts for me. Ensure each prompt is unique, captivating, and suitable for creating stunning wallpapers." % (count)},
      {"role": "system", "content": "Consider various themes such as nature, abstract art, futuristic landscapes, and surreal scenes. Make sure the prompts are diverse and imaginative."},
      {"role": "user", "content": prompt}
    ]
  )
  return response.choices[0].message.content

def handle_city_based_generation(client, city, directory_path, generated_images):
    print(f"Fetching weather data for {city}...")
    current_data = weather_data.fetch_weather(city)
    if current_data:
        print("Weather data successfully fetched.")
        print("Generating prompt using GPT-4...")
        prompt = weather_data.generate_gpt4_prompt(client, current_data, "current")
        print("Generated Prompt:")
        print(prompt)
        image_path = generate_image(client, f"{prompt} Do not include any text in the image. Avoid using known landmarks or places.", directory_path)
        generated_images.append(image_path)
    else:
        print("Failed to generate prompt due to missing weather data.")

def handle_random_generation(client, count, directory_path, generated_images):
    print(f"Generating you {count} random image prompts.")
    input_prompt = "Create a visually stunning wallpaper that is both professional and captivating. The wallpaper should be versatile enough to be used in various settings, including work environments. Consider themes such as nature, abstract art, and futuristic landscapes."
    prompts = generate_prompts(client, count, input_prompt)
    generate_images_from_prompts(client, prompts, directory_path, generated_images)

def generate_images_from_prompts(client, prompts, directory_path, generated_images):
    for prompt in prompts.split("\n"):
        if prompt.strip():
            image_path = generate_image(client, prompt, directory_path)
            generated_images.append(image_path)

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

def handle_service_management(args):
    # Update list of possible plist files
    plist_files = ['generate-rotate.plist', 'generate-city.plist', 'fetch-city.plist']

    if args.command in ["uninstall", "reinstall"]:
        uninstall_services(plist_files)

    if args.command in ["install", "reinstall"]:
        install_service(args)

def uninstall_services(plist_files):
    for plist_file in plist_files:
        plist_path = os.path.join(os.path.dirname(__file__), plist_file)
        job_name = plist_file.split('.')[0]
        if is_service_installed(job_name):
            uninstall_service(plist_path, plist_file)
        else:
            print(f"The {job_name} job is not installed.")

def is_service_installed(job_name):
    check_cmd = f"launchctl list | grep 'com.wallpaper-generator.{job_name}'"
    check_result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)
    return check_result.returncode == 0

def uninstall_service(plist_path, plist_file):
    uninstall_cmd = f"launchctl unload -w {plist_path}"
    result = subprocess.run(uninstall_cmd, shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"{plist_file} uninstalled successfully.")
    else:
        print(f"Failed to uninstall {plist_file}. Error: {result.stderr.strip()}")
        print(f"Try running `sudo launchctl unload -w {plist_path}` for richer errors.")
def install_service(args):
    # Determine which plist file to use based on arguments
    if args.city:
        if getattr(args, 'generate', False):
            plist_file = 'generate-city.plist'
        else:
            plist_file = 'fetch-city.plist'
    else:
        plist_file = 'generate-rotate.plist'
    template_path = os.path.join(os.path.dirname(__file__), f"{plist_file}.template")
    plist_path = os.path.join(os.path.dirname(__file__), plist_file)

    with open(template_path, 'r') as file:
        plist_content = file.read()

    script_path = os.path.abspath(__file__)
    venv_python = os.path.join(os.path.dirname(script_path), 'venv', 'bin', 'python3')

    plist_content = plist_content.replace('{{INTERVAL}}', str(args.interval))
    plist_content = plist_content.replace('{{PYTHON_PATH}}', venv_python)
    plist_content = plist_content.replace('{{SCRIPT_PATH}}', script_path)
    if args.city:
        plist_content = plist_content.replace('{{CITY_NAME}}', args.city)
    plist_content = plist_content.replace('{{USERNAME}}', getpass.getuser())

    with open(plist_path, 'w') as file:
        file.write(plist_content)

    install_cmd = f"launchctl load -w {plist_path}"
    result = subprocess.run(install_cmd, shell=True, capture_output=True, text=True)

    if result.returncode == 0:
        print(f"{plist_file} {'re' if args.command == 'reinstall' else ''}installed with interval {args.interval} seconds and job loaded successfully.")
        if args.city:
            print(f"City set to {args.city}")
            if getattr(args, 'generate', False):
                print("Using generate mode for city-based wallpapers")
            else:
                print("Using fetch mode for city-based wallpapers")
    else:
        print(f"Failed to load {plist_file}. Error: {result.stderr.strip()}")
        print(f"Try running `sudo launchctl load -w {plist_path}` for richer errors.")

def rotate_wallpaper(directory_path):
    wallpapers = glob.glob(os.path.join(directory_path, "*.png"))
    wallpaper = rand_choice(fetch_current_wallpaper(), wallpapers)
    change_wallpaper(wallpaper)


def main():
    parser = argparse.ArgumentParser(description="Wallpaper Generator")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Generate command
    generate_parser = subparsers.add_parser("generate", help="Generate images based on prompts")
    generate_parser.add_argument("--count", type=int, default=1, help="Number of prompts to generate (default: 1)")
    generate_parser.add_argument("--prompt", type=str, help="Custom prompt for generating images")
    generate_parser.add_argument("--city", type=str, help="City name for weather-based prompt generation")
    generate_parser.add_argument("--rotate-now", action="store_true", help="Rotate wallpaper immediately after generation")

    # Fetch command
    fetch_parser = subparsers.add_parser("fetch", help="Fetch the most recent wallpaper for a city")
    fetch_parser.add_argument("--city", type=str, required=True, help="City name to fetch wallpaper for")
    fetch_parser.add_argument("--rotate-now", action="store_true", help="Rotate to the fetched wallpaper immediately")

    # Custom action to handle dynamic default intervals
    class IntervalAction(argparse.Action):
        def __call__(self, parser, namespace, values, option_string=None):
            setattr(namespace, self.dest, values)

    # Update install parser
    install_parser = subparsers.add_parser("install", help="Install the plist file for automatic wallpaper rotation")
    install_parser.add_argument("--generate", action="store_true", help="Generate new images instead of fetching them (only applies with --city)")
    install_parser.add_argument("--interval", 
                              action=IntervalAction,
                              type=int,
                              default=None,
                              help="Interval in seconds between wallpaper rotations (default: 3600 for generate, 600 for fetch)")
    install_parser.add_argument("--city", type=str, help="City name for weather-based prompt generation")

    # Uninstall command
    subparsers.add_parser("uninstall", help="Uninstall the plist files for automatic wallpaper rotation")

    # Update reinstall parser
    reinstall_parser = subparsers.add_parser("reinstall", help="Reinstall the plist file for automatic wallpaper rotation")
    reinstall_parser.add_argument("--generate", action="store_true", help="Generate new images instead of fetching them (only applies with --city)")
    reinstall_parser.add_argument("--interval", 
                                action=IntervalAction,
                                type=int,
                                default=None,
                                help="Interval in seconds between wallpaper rotations (default: 3600 for generate, 600 for fetch)")
    reinstall_parser.add_argument("--city", type=str, help="City name for weather-based prompt generation")

    # Rotate command (default behavior)
    subparsers.add_parser("rotate", help="Rotate wallpaper")

    args = parser.parse_args()

    directory_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "images")
    os.makedirs(directory_path, exist_ok=True)

    if args.command == "generate":
        client = OpenAI()
        count = args.count

        generated_images = []

        if not sys.stdin.isatty() and sys.stdin.read(1):
            sys.stdin.seek(0)
            for line in sys.stdin:
                prompt = line.strip()
                if prompt:
                    image_path = generate_image(client, prompt, directory_path)
                    generated_images.append(image_path)
        else:
            if args.city:
                handle_city_based_generation(client, args.city, directory_path, generated_images)
            elif args.prompt:
                prompts = generate_prompts(client, count, args.prompt)
                generate_images_from_prompts(client, prompts, directory_path, generated_images)
            else:
                handle_random_generation(client, count, directory_path, generated_images)

        if generated_images and args.rotate_now:
            new_wallpaper = generated_images[-1]
            change_wallpaper(new_wallpaper)
            print(f"Wallpaper changed to: {new_wallpaper}")
        elif generated_images:
            print(f"Generated {len(generated_images)} new image(s). Use the 'rotate' command to change the wallpaper.")
        else:
            print("No new images were generated.")

    elif args.command == "fetch":
        city_wallpaper_path = os.path.join(directory_path, "city")
        os.makedirs(city_wallpaper_path, exist_ok=True)
        latest_wallpaper = fetch_latest_city_wallpaper(args.city, city_wallpaper_path)

        if latest_wallpaper:
            if args.rotate_now:
                change_wallpaper(latest_wallpaper)
                print(f"Wallpaper changed to: {latest_wallpaper}")
            else:
                print(f"Most recent wallpaper for {args.city}: {latest_wallpaper}")
        else:
            print(f"Failed to fetch wallpaper for {args.city}")

    ## Installation / Uninstallation ##
    elif args.command in ["install", "uninstall", "reinstall"]:
        # Set default interval based on generate flag for install/reinstall
        if args.command in ['install', 'reinstall']:
            if args.interval is None:
                args.interval = 3600 if args.generate else 600
        
        handle_service_management(args)
    ##

    else:  # Default behavior (rotate)
        rotate_wallpaper(directory_path)

if __name__ == '__main__':
    import os

    if 'OPENAI_API_KEY' in os.environ:
        openai_api_key = os.environ['OPENAI_API_KEY']
    else:
        import configparser
        config = configparser.ConfigParser()
        config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
        try:
            config.read(config_path)
            openai_api_key = config['OpenAI']['api_key']
            os.environ['OPENAI_API_KEY'] = openai_api_key
        except (FileNotFoundError, KeyError):
            print("Error: OpenAI API key not found in environment or config.ini")
            sys.exit(1)

    main()

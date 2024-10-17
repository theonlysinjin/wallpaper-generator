#!env python3
import os, re, requests, sys, glob, random, subprocess, io, argparse, json
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
        prompt = weather_data.generate_gpt4_prompt(client, current_data)
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

def handle_service_management(args):
    plist_files = ['generate-rotate.plist', 'generate-city.plist']

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
    check_cmd = f"launchctl list | grep {job_name}"
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
    plist_file = 'generate-city.plist' if args.city else 'generate-rotate.plist'
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

    with open(plist_path, 'w') as file:
        file.write(plist_content)

    install_cmd = f"launchctl load -w {plist_path}"
    result = subprocess.run(install_cmd, shell=True, capture_output=True, text=True)

    if result.returncode == 0:
        print(f"{plist_file} {'re' if args.command == 'reinstall' else ''}installed with interval {args.interval} seconds and job loaded successfully.")
        if args.city:
            print(f"City set to {args.city}")
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

    # Install command
    install_parser = subparsers.add_parser("install", help="Install the plist file for automatic wallpaper rotation")
    install_parser.add_argument("--interval", type=int, default=3600, help="Interval in seconds between wallpaper rotations (default: 3600)")
    install_parser.add_argument("--city", type=str, help="City name for weather-based prompt generation")

    # Uninstall command
    subparsers.add_parser("uninstall", help="Uninstall the plist files for automatic wallpaper rotation")

    # Reinstall command
    reinstall_parser = subparsers.add_parser("reinstall", help="Reinstall the plist file for automatic wallpaper rotation")
    reinstall_parser.add_argument("--interval", type=int, default=3600, help="Interval in seconds between wallpaper rotations (default: 3600)")
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

    elif args.command in ["install", "uninstall", "reinstall"]:
        handle_service_management(args)
    else:  # Default behavior (rotate)
        rotate_wallpaper(directory_path)

if __name__ == '__main__':
    import configparser
    import os

    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
    config.read(config_path)

    openai_api_key = config['OpenAI']['api_key']
    os.environ['OPENAI_API_KEY'] = openai_api_key

    main()
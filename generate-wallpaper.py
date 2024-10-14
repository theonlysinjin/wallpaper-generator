#!env python3
"""
# Wallpaper Generator Script

This script generates images using DALL-E 3 and sets them as wallpapers on macOS. It can create images based on custom prompts and rotate wallpapers automatically.

## Features:
- Generate images using DALL-E 3 based on custom or random prompts.
- Set generated images as wallpapers on macOS.
- Rotate wallpapers from a directory of generated images.

## Setup:
1. Create a virtual environment:
  ```
  python3 -m venv venv
  source venv/bin/activate
  ```
2. Install required libraries from the requirements file:
  ```
  pip3 install -r requirements.txt
  ```
3. Ensure prompts exist in the `prompts` directory.
4. Export your OpenAI API key:
  ```
  export OPENAI_API_KEY="your_api_key_here"
  ```

## Usage:
- Generate images:
  ```
  python3 ./generate-wallpaper.py generate
  python3 ./generate-wallpaper.py generate 2
  python3 ./generate-wallpaper.py generate 3 "Peaceful landscapes from around the world. Something I can use across devices."
  cat examples/example1 | python3 ./generate-wallpaper.py generate
  ```
- Rotate your wallpaper:
  ```
  python3 ./generate-wallpaper.py
  ```
"""

import os, re, requests, sys, glob, random, subprocess, io
from PIL import Image, PngImagePlugin
from datetime import datetime
from openai import OpenAI

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
  filename = f"{directory_path}/{trimmed_filename}_{timestamp}.png"
  return(filename)

def generate_image(client, prompt):
  print("Generating Image")
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

  newImage.save(filename, pnginfo=pngMetaData)

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

# Run!
if (__name__ == '__main__'):
  directory_path = f"{os.path.realpath(os.path.dirname(__file__))}/images"
  if not os.path.exists(directory_path): os.makedirs(directory_path)

  if len(sys.argv) > 1:
    if sys.argv[1] in ["--help", "-h"]:
      print("""
Usage: python3 ./generate-wallpaper.py [command] [options]

Commands:
  generate [count] [prompt]  Generate images based on prompts.
                              - count: Number of prompts to generate (default: 1).
                              - prompt: Custom prompt for generating images.
  --install                  Install the plist file for automatic wallpaper rotation.

Examples:
  python3 ./generate-wallpaper.py generate
  python3 ./generate-wallpaper.py generate 2
  python3 ./generate-wallpaper.py generate 3 "Peaceful landscapes from around the world. Something I can use across devices."

Rotate your wallpaper with:
  python3 ./generate-wallpaper.py

Install the plist file with:
  python3 ./generate-wallpaper.py --install
      """)
      sys.exit(0)

    client = OpenAI()
    if sys.argv[1] == "generate":
      # Pass a list of prompts in via stdin
      if not sys.stdin.isatty():
        for line in sys.stdin:
          prompt = line.rstrip()
          generate_image(client, prompt)
      # Generate 1 prompt for generic wallpapers
      elif len(sys.argv) == 2:
        print("Generating you 1 random image prompts.")
        inputPrompt = "Create a visually stunning wallpaper that is both professional and captivating. The wallpaper should be versatile enough to be used in various settings, including work environments. Consider themes such as nature, abstract art, and futuristic landscapes."
        prompts = generate_prompts(client, 1, inputPrompt)
        for prompt in prompts.split("\n"):
          if len(prompt) > 0:
            generate_image(client, prompt)

      # Generate a [count] of prompts for generic wallpapers
      elif len(sys.argv) == 3:
        print("Generating you %s random image prompts." %(sys.argv[2]))
        inputPrompt = "Create a visually stunning wallpaper that is both professional and captivating. The wallpaper should be versatile enough to be used in various settings, including work environments. Consider themes such as nature, abstract art, and futuristic landscapes."
        prompts = generate_prompts(client, sys.argv[2], inputPrompt)
        for prompt in prompts.split("\n"):
          if len(prompt) > 0:
            generate_image(client, prompt)

      # Generate a [count] of prompts from a single prompt
      elif len(sys.argv) == 4:
        print("Generating you %s images of %s" %(sys.argv[2], sys.argv[3]))
        prompts = generate_prompts(client, sys.argv[2], sys.argv[3])
        for prompt in prompts.split("\n"):
          if len(prompt) > 0:
            generate_image(client, prompt)

    elif sys.argv[1] == "--install":
      plist_path = os.path.join(os.path.dirname(__file__), 'generate-rotate.plist')
      install_cmd = f"launchctl load -w {plist_path}"
      os.system(install_cmd)
      verify_cmd = "launchctl list | grep com.sswanepoel.wallpaperchanger"
      result = os.system(verify_cmd)
      if result == 0:
        print("Plist file installed and job loaded successfully.")
      else:
        print("Failed to load the plist file.")
  else:
    wallpapers = glob.glob(f"{directory_path}/*.png")
    wallpaper = rand_choice(fetch_current_wallpaper(), wallpapers)
    change_wallpaper(wallpaper)

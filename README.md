# Wallpaper Generator
This project generates images using DALL-E 3 and sets them as wallpapers on macOS. It can create images based on custom prompts and rotate wallpapers automatically.

|      Bamboo Forest      |      Mountain Landscape      |
| :----------------------: | :-----------------------: |
| ![Bamboo Forest](./examples/image_Lush_green_bamboo_forest_with_sunlight_filtering_through_20240517091955.png) | ![Mountain Landscape](./examples/image_serene_mountain_landscape_at_dawn_where_the_sky_is_a_vibrant_spectrum_of_pinks_purples_and_oranges_reflected_in_a_tranquil_mirrorlike_lake_The_scene_is_dotted_with_lush_green_pines_and_a_single_canoe_is_gently_glidin_20241014084325.png) |

## Features

- Generate images using DALL-E 3 based on custom or random prompts.
- Set generated images as wallpapers on macOS.
- Rotate wallpapers from a directory of generated images.

## Setup

1. Create a virtual environment:
  ```sh
  python3 -m venv venv
  source venv/bin/activate
  ```
2. Install required libraries from the requirements file:
  ```sh
  pip3 install -r requirements.txt
  ```
3. Export your OpenAI API key:
  ```sh
  export OPENAI_API_KEY="your_api_key_here"
  ```

## Usage

- Generate images:
  ```sh
  python3 ./generate-wallpaper.py generate
  python3 ./generate-wallpaper.py generate 2
  python3 ./generate-wallpaper.py generate 3 "Peaceful landscapes from around the world. Something I can use across devices."
  cat examples/example1 | python3 ./generate-wallpaper.py generate
  ```
- Rotate your wallpaper:
  ```sh
  python3 ./generate-wallpaper.py
  ```
- Install the plist file for automatic wallpaper rotation:
  ```sh
  python3 ./generate-wallpaper.py --install
  ```

## Files

- `generate-wallpaper.py`: Main script to generate and rotate wallpapers.
- `generate-rotate.plist`: Configuration file for scheduling wallpaper rotation.
- `requirements.txt`: List of required Python libraries.

## Dependencies

- `openai`
- `pillow`

## License

This project is licensed under the MIT License.

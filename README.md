# Wallpaper Generator

Welcome to the Wallpaper Generator project! This innovative tool harnesses the power of DALL-E 3 to create stunning, custom wallpapers for your macOS desktop. Whether you want images based on your own prompts, current weather conditions, or randomly generated ideas, this project has you covered.

|      Bamboo Forest      |      Mountain Landscape      |
| :----------------------: | :-----------------------: |
| ![Bamboo Forest](./examples/image_Lush_green_bamboo_forest_with_sunlight_filtering_through.png) | ![Mountain Landscape](./examples/image_serene_mountain_landscape_at_dawn.png) |

## Features

- Generate images using DALL-E 3 based on custom or random prompts.
- Generate images based on current weather conditions for a specified city.
- Set generated images as wallpapers on macOS.
- Rotate wallpapers from a directory of generated images.
- Install, uninstall, or reinstall automatic wallpaper rotation services.
- Support for reading prompts from standard input.
- Option to rotate wallpaper immediately after generation.

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
3. Create a `config.ini` file in the same directory as the script with your OpenAI API key and weather preferences:
  ```ini
  [OpenAI]
  api_key = your_api_key_here

  [Weather]
  # Options: current or forecast
  weather = forecast
  ```

4. Note: This project uses the DALL-E 3 model via the OpenAI API. Be aware of potential usage costs associated with generating images.

## Usage

- Generate images:
  ```sh
  python3 ./generate-wallpaper.py generate
  python3 ./generate-wallpaper.py generate --count 2
  python3 ./generate-wallpaper.py generate --count 3 --prompt "Peaceful landscapes from around the world."
  python3 ./generate-wallpaper.py generate --city "New York" --rotate-now
  cat examples/example1 | python3 ./generate-wallpaper.py generate
  ```
- Rotate your wallpaper from existing images:
  ```sh
  python3 ./generate-wallpaper.py rotate
  ```

## Installation

To set up automatic wallpaper rotation or city-based generation, you can use the following commands:

- Install the automatic wallpaper rotation service:
  ```sh
  python3 ./generate-wallpaper.py install --interval 3600
  ```

- Install the city-based wallpaper generation service:
  ```sh
  python3 ./generate-wallpaper.py install --interval 3600 --city "London"
  ```

- Uninstall the services:
  ```sh
  python3 ./generate-wallpaper.py uninstall
  ```

- Reinstall the services:
  ```sh
  python3 ./generate-wallpaper.py reinstall --interval 3600
  python3 ./generate-wallpaper.py reinstall --interval 3600 --city "Paris"
  ```

These commands manage launchd services for automatic wallpaper rotation and city-based generation on macOS.

## Files

- `generate-wallpaper.py`: Main script to generate and rotate wallpapers.
- `weather_data.py`: Module for fetching weather data and generating weather-based prompts.
- `generate-rotate.plist.template`: Template for scheduling wallpaper rotation.
- `generate-city.plist.template`: Template for scheduling city-based wallpaper generation.
- `requirements.txt`: List of required Python libraries.

## Dependencies

- `openai`
- `pillow`
- `bs4`
- `requests`

## Compatibility

This project is designed for macOS. It has been tested on macOS Monterey (12.0) and later versions. Compatibility with earlier versions is not guaranteed.  
_TODO_: Windows and Linux support.

## Contributing

Contributions to the Wallpaper Generator project are welcome! If you have suggestions for improvements or encounter any issues, please open an issue or submit a pull request on the project's GitHub repository.

## License

This project is licensed under the MIT License.

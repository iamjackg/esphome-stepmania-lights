# ESPHome Stepmania Lights

This is a bare bones project to turn your [ESPHome](https://esphome.io/) devices into lights for StepMania. It's not in a very polished state yet, so you'll fare better if you have a knowledge of Python + Linux.

This also targets a relatively niche intersection of the IoT and rhythm game community. If you feel right at home with all this stuff, we should probably hang out. :P

## ESPHome setup

When you configure a new device, create a [light component](https://esphome.io/#light-components) called `main_light`. This will be used to turn the light off completely when StepMania starts and exits.

You can then use other light components or [partition components](https://esphome.io/components/light/partition.html) to create individual lights. As long as you give them a name from the following list, they will be picked up automatically.

### Cabinet light names

- `marquee_upper_left`
- `marquee_upper_right`
- `marquee_lower_left`
- `marquee_lower_right`
- `bass_left`
- `bass_right`

### Player light names

- `player_1_menu_left`
- `player_1_menu_right`
- `player_1_menu_up`
- `player_1_menu_down`
- `player_1_start`
- `player_1_select`
- `player_1_back`
- `player_1_coin`
- `player_1_operator`
- `player_1_effect_up`
- `player_1_effect_down`
- `player_1_1`
- so on and so forth
- `player_1_19`

These repeat for `player_2`.

### Example

This is an example ESPHome configuration for a D1 Mini with the RGB Shield, which has 7 WS2812B LEDs in a circle. The center LED is set to blink with the start button on the cabinet, and the LEDs around it flash with the bass lights.

```yaml
esphome:
  name: itglights1
  platform: ESP8266
  board: d1_mini

wifi:
  ssid: "your_password"
  password: "your_password"

  # Enable fallback hotspot (captive portal) in case wifi connection fails
  ap:
    ssid: "Itglights Fallback Hotspot"
    password: "fallback_password"

captive_portal:

# Enable logging
logger:

# Enable Home Assistant API
api:
  password: "itglights"
  reboot_timeout: 0s # This is necessary so the device doesn't reboot when there is nothing controlling it

ota:
  password: "itglights"

light:
  - platform: partition
    name: "player_1_start"
    segments:
      - id: main_light
        from: 0
        to: 0
  - platform: partition
    name: "bass_right"
    segments:
      - id: main_light
        from: 1
        to: 6
  - platform: fastled_clockless
    chipset: WS2812B
    id: main_light
    pin: D6
    num_leds: 7
    rgb_order: GRB
    name: "main_light"
    gamma_correct: 1.8
    color_correct: [70%, 70%, 70%]

```

## StepMania setup

Edit your `Preferences.ini` file, and

- set the `LightsDriver=` line to `LightsDriver=SextetStreamToFile`.
- set the `SextetStreamOutputFilename=` line to a path StepMania can write to, e.g. `Save/StepMania-Lights-SextetStream.out`

If you're on Linux, create the named pipe.

```bash
mkfifo /path/to/stepmania-5.0/Save/StepMania-Lights-SextetStream.out
```

If you're not on Linux or want more info, check [the SextetStream lights documentation](https://github.com/stepmania/stepmania/blob/5_1-new/src/arch/Lights/LightsDriver_SextetStream.md).

## Running the script

Install the required dependencies.

```bash
pip3 install -r requirements.txt
```

Make a copy of the sample configuration file in the script's folder.

```bash
cp config.yml.sample config.yml
```

Open the configuration file, and set `stepmania_sextet_file` to the path of the SextetStream named pipe.

Under the `lights` section, add entries for each of your devices. `password` should correspond to the API password in the ESPHome device configuration.

Start the script. 

```bash
python3 main.py
```

**You have to start the script first in order for StepMania to run!** If nothing is reading the SextetStream file, StepMania will get stuck.

Now you can launch StepMania. Enjoy the light show!

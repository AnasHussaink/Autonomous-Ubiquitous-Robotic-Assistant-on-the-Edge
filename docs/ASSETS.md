# Documentation image provenance

| Asset | Origin and meaning |
| --- | --- |
| `images/dashboard-speaking.png` | Browser render of the supplied `src/gui/templates/index.html`, at a 1024×600 viewport. |
| `images/dashboard-standby.png`, `dashboard-listening.png`, `dashboard-thinking.png` | The same application page rendered in its other three states. |
| `images/dashboard-states.png` | Contact sheet of those four application renders. |
| `images/architecture.png` / `.svg` | Original documentation diagram derived from the supplied code's control flow. |
| `images/wiring-reference.png` / `.svg` | Original logical connection map for the owner's confirmed Pi 4, INMP441, and MAX98357A component types. |

The dashboard renders were produced with browser-only fixture data. No Raspberry Pi, microphone, speaker, live backend, or remote inference service was connected. CPU, RAM, temperature, clock, and captions shown are illustrative. The page's external Chart.js request was disabled because these screenshots do not show the chart. No generated hardware photograph is presented as evidence of the build.

The diagrams and screenshot compositions were added for this documentation update. Source SVGs are included for editing. The screenshot appearance comes from the existing project interface; retain the repository's existing code attribution and license.

Wiring references: [Raspberry Pi hardware](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html), [INMP441 datasheet](https://invensense.tdk.com/wp-content/uploads/2015/02/INMP441.pdf), [MAX98357A wiring](https://learn.adafruit.com/adafruit-max98357-i2s-class-d-mono-amp/raspberry-pi-wiring), and the [voiceHAT overlay source](https://github.com/raspberrypi/linux/blob/rpi-6.18.y/arch/arm/boot/dts/overlays/googlevoicehat-soundcard-overlay.dts).

These are connection references, not inspected as-built schematics. Confirm your breakout's labeling, enable/gain configuration, physical pin orientation, and power requirements before wiring.

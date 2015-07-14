# GT-I9505 Bootloader and Modem flashable tar creator

It extracts the bootloader and modem files from a firmware zip and create Odin flashable tars

## Usage

`bl_modem.py [-o OUTPUT_PATH] [-d] ZIPFILE`

* ZIPFILE: zip file of the firmware
* -o, --output-path: path to store the tar files
* -d, --delete-original: delete the original zip after creating the tar files

## Requirements

* Python 2 (>= 2.7) or Python 3 (>= 3.2)

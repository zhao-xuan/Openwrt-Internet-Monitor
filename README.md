# Openwrt-Internet-Monitor
Monitor Internet Usage on Linux-based system Openwrt.
Any open-sourced router/server with Openwrt system and nlbwmon installed can run this program.
This project is nearly finished, but may need further UI design and maintainence for use.
This project is built based on Python 3.7.

## Preconditions
1. Install Openwrt system on your router/server. See details on https://openwrt.org. Set a username(default username: root) and password(default empty) for logging in your Openwrt system

2. Type the following command to install the dependency:

    opkg install luci-app-nlbwmon

3. Install all python dependencies:

    pip3 install flask

## How to Use
1. Modify config.json file and fill the following information:
    **router_address** is the default address for entering Openwrt system(default `192.168.2.1`)
    **root_username** is the username for Openwrt system
    **root_password** is the password for Openwrt system
    **databse_name** is the name of the database under the same folder, or could be the relative path of the database

2. Run `python3 main.py` to collect data. 
Optional: You can use `screen` to maintain a persistent remote terminal session and run `main.py` on the router independently. See https://linux.die.net/man/1/screen for more details. See https://remysharp.com/2015/04/27/screen for a simple tutorial on how to use `screen`. To install screen on your router, run the following command:

    apt-get install screen
    ssh (username)@(your router address)
    screen *--This command will start a new terminal*
    ctrl-a d *--This will leave the session running and detach from the screen so you're back to your original terminal prompt.*
    screen -rd *--This could resume the terminal session from the outside*

3. Run `python3 fetch_data.py`. The listening port has already been set up in this file, so no need to configure FLASK_APP environment variable.

## Current Build
1. Added archived data functionality that will record data separately from the main database every 30 minutes
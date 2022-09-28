# Camera View Optimizer
![welcome](readme_media/welcome.jpg)
### About
Omniverse extensions that allows you quickly hide/delete objects that are not visible to the camera to save some performance and VRAM.

## Quick links

* [Installation](#installation)
* [How to use](#how-to-use)
* [Linking with an Omniverse app](#linking-with-an-omniverse-app)
* [Contributing](#contributing)
* [Changelog](CHANGELOG.md)

## Installation
To add a this extension to your Omniverse app:
### From Community tab (Not available at the moment)
1. Go to **Extension Manager** (Window - Extensions) — Community tab
2. Search for **Camera View Optimizer** extension and enable it
### Manual
1. Go to **Extension Manager** (Window - Extensions) — **Gear Icon** — **Extension Search Path**
2. Add this as a search path: `git://github.com/Vadim-Karpenko/omniverse-camera-view-optimizer?branch=main&dir=exts`
3. Search for **Camera View Optimizer** extension and enable it

A new window will appear alongside the Property tab:


![start window](readme_media/start_window.jpg)

## How to use
- Open a scene you want to optimize
- Open an extension window
- The current view in the viewport is used to scan for visible objects, so make sure your camera is positioned correctly.
- Make sure settings set correctly.
- Click **Optimize** button.

## Linking with an Omniverse app

For a better developer experience, it is recommended to create a folder link named `app` to the *Omniverse Kit* app installed from *Omniverse Launcher*. A convenience script to use is included.

Run:

```bash
> link_app.bat
```

There is also an analogous `link_app.sh` for Linux. If successful you should see `app` folder link in the root of this repo.

If multiple Omniverse apps is installed script will select recommended one. Or you can explicitly pass an app:

```bash
> link_app.bat --app code
```

You can also just pass a path to create link to:

```bash
> link_app.bat --path "C:/Users/bob/AppData/Local/ov/pkg/create-2022.1.3"
```


## Contributing
Feel free to create a new issue if you run into any problems. Pull requests are welcomed.

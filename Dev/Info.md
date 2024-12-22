# Dev Folder Information(Preview)

## Useful Stuff

### BakeLoader

> Easily open the non-build version of BakeLauncher.

**Command List:**

Load Launcher
```bash
./BakeLoader
```

Running ```git pull``` and load Launcher(main)
```bash
./BakeLoader -u
```


### Build Tutorial

To build the project, install the necessary tools depending on your operating system:

- **macOS:** Python3 and Homebrew are already installed.
- **Windows:** Python3 and scoop are already installed.
- **Linux:** Python3 are already installed(apt-get are available).

Ensure you have `gcc` installed as it's required for building.

**Build Command:**
```bash
gcc -o BakeLoader Dev/BakeLoader.c
```
After build, please copy BakeLauncherLoad to Launcher root directory!
# colcon-ui

A web dashboard for `colcon build` — replaces the wall of terminal text with a clean, live UI that shows per-package build status, extracts errors automatically, and lets you rebuild failed packages in one click.

## Why

Running `colcon build` on a ROS2 workspace gives you an unreadable stream of output. When something fails you have to scroll through hundreds of lines to find the error. colcon-ui fixes this.

**Before:** wall of text, no structure, hunt for errors manually  
**After:** per-package status, error surfaced instantly, rebuild failed in one click

## Features

- **Live per-package status** — building, done, failed, aborted with progress bars
- **Automatic error extraction** — CMake errors, C++ compiler errors surfaced instantly, no scrolling
- **Build from browser** — trigger `colcon build` without touching the terminal
- **Rebuild failed** — one click to retry only the failed packages using `--packages-select`
- **Configurable workspace** — works with any ROS2 workspace via `--workspace` flag
- **Live log** — color coded streaming build output
- **Multi-tab support** — open in multiple browser tabs, all update live
- **State replay** — refresh the browser and get the last build state back

## Requirements

- ROS2 (any distro — tested on Humble)
- Python 3.8+
- pip

## Install

```bash
git clone https://github.com/Supull/ColconUI.git
cd colcon-ui
pip install tornado
```

## Usage

```bash
python3 parser.py --workspace /path/to/your/ros2_ws
```

Then open your browser at `http://localhost:8888`.

### Example

```bash
# if your workspace is at ~/robot_ws
python3 parser.py --workspace ~/robot_ws

# with Docker, make sure port 8888 is exposed
docker run -p 8888:8888 ...
```

## How it works

colcon-ui runs `colcon build` as a subprocess, reads its output line by line, parses the structured log lines (`Starting >>>`, `Finished <<<`, `Failed <<<`) into events, and streams them to the browser over a websocket. The frontend is plain HTML/JS with no framework dependencies.

```
colcon build → python parser → tornado websocket → browser
```

## Tested error types

- CMake dependency errors (`find_package` failures)
- C++ compiler errors (type errors, missing symbols)
- Clean builds with multiple packages in parallel

## Contributing

PRs welcome. If you have a ROS2 workspace where colcon-ui doesn't parse errors correctly, open an issue with the raw colcon output and I'll add support for it.

## License

MIT

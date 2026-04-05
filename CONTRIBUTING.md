# contributing

PRs are welcome. A few things to know:

- the project is two files — `parser.py` and `index.html`
- `parser.py` handles the subprocess, parsing, and websocket server
- `index.html` is the entire frontend, no framework, plain JS

## good first contributions

- support for more error types (python, linker errors, etc)
- package selection checkboxes
- click package to view full log
- better error parsing edge cases

## to run locally
```bash
git clone https://github.com/Supull/colcon-ui.git
cd colcon-ui
pip install tornado
python3 parser.py --workspace /path/to/your/ros2_ws
```

if colcon-ui doesn't parse an error correctly on your workspace, open an issue with the raw colcon output and i'll add support for it.

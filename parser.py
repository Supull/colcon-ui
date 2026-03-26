import re
import json
import asyncio
import os
import argparse
import tornado.web
import tornado.websocket

arg_parser = argparse.ArgumentParser()
arg_parser.add_argument("--workspace", default="/root/lunabot", help="path to your ROS2 workspace")
args = arg_parser.parse_args()

WORKSPACE = args.workspace

if not os.path.isdir(WORKSPACE):
    print(f"error: workspace '{WORKSPACE}' does not exist")
    exit(1)

clients = []
package_states = {}
current_stderr_pkg = None
stderr_buffer = []
build_running = False

def parse_line(line):
    global current_stderr_pkg, stderr_buffer

    if line.startswith("--- stderr:"):
        current_stderr_pkg = line.split("--- stderr:")[1].strip()
        stderr_buffer = []
        return None

    if line == "---" and current_stderr_pkg:
        pkg = current_stderr_pkg
        error_text = "\n".join(stderr_buffer)
        current_stderr_pkg = None
        stderr_buffer = []
        return {"package": pkg, "status": "error_detail", "error": error_text}

    if current_stderr_pkg:
        stderr_buffer.append(line)
        return None

    if line.startswith("Starting >>>"):
        package = line.split(">>>")[1].strip()
        return {"package": package, "status": "building"}

    if line.startswith("Finished <<<"):
        match = re.search(r"Finished <<< (\S+) \[(.+)\]", line)
        if match:
            return {"package": match.group(1), "status": "done", "time": match.group(2)}

    if line.strip().startswith("Failed"):
        match = re.search(r"Failed\s+<<< (\S+)", line)
        if match:
            return {"package": match.group(1), "status": "failed"}

    if line.strip().startswith("Aborted"):
        match = re.search(r"Aborted\s+<<< (\S+)", line)
        if match:
            return {"package": match.group(1), "status": "aborted"}

    return None


class WSHandler(tornado.websocket.WebSocketHandler):
    def open(self):
        clients.append(self)
        print("browser connected")
        self.write_message(json.dumps({
            "status": "workspace",
            "path": WORKSPACE
        }))
        for state in package_states.values():
            self.write_message(json.dumps(state))
            if "error" in state:
                self.write_message(json.dumps({
                    "package": state["package"],
                    "status": "error_detail",
                    "error": state["error"]
                }))

    def on_message(self, message):
        data = json.loads(message)
        if data.get("action") == "build" and not build_running:
            package_states.clear()
            packages = data.get("packages", None)
            asyncio.create_task(run_build(packages))

    def on_close(self):
        clients.remove(self)
        print("browser disconnected")


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        index_path = os.path.join(os.path.dirname(__file__), "index.html")
        with open(index_path, "r") as f:
            self.set_header("Content-Type", "text/html")
            self.write(f.read())


async def run_build(packages=None):
    global build_running
    build_running = True

    for client in clients:
        client.write_message(json.dumps({"status": "build_started"}))

    cmd = ["colcon", "build"]
    if packages:
        cmd += ["--packages-select"] + packages

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=WORKSPACE
        )
    except Exception as e:
        for client in clients:
            client.write_message(json.dumps({
                "status": "error_detail",
                "package": "server",
                "error": str(e)
            }))
        build_running = False
        return

    async for line in process.stdout:
        line = line.decode().strip()
        print("RAW:", line)
        result = parse_line(line)
        if result:
            print("PARSED:", result)
            if result["status"] == "error_detail":
                if result["package"] in package_states:
                    package_states[result["package"]]["error"] = result["error"]
                else:
                    package_states[result["package"]] = result
                for client in clients:
                    client.write_message(json.dumps(result))
            elif result["status"] == "failed":
                if result["package"] in package_states:
                    package_states[result["package"]]["status"] = "failed"
                else:
                    package_states[result["package"]] = result
                for client in clients:
                    client.write_message(json.dumps(result))
            else:
                package_states[result["package"]] = result
                for client in clients:
                    client.write_message(json.dumps(result))

    build_running = False
    for client in clients:
        client.write_message(json.dumps({"status": "build_done"}))


def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/ws", WSHandler),
    ])


async def main():
    app = make_app()
    app.listen(8888)
    print(f"server running at http://localhost:8888")
    print(f"workspace: {WORKSPACE}")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
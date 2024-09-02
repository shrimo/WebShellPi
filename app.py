import os
import subprocess
from flask import Flask, request, jsonify, render_template, session

VERSION = "0.01a"
DATE = "Mon Sep  2 04:24:28 AM EEST 2024"

class WebShell:
    """
    WebShell class manages the current directory and executes shell commands.
    """

    def __init__(self):
        """Initialize with the current working directory."""
        self.current_dir = os.getcwd()

    def get_current_directory(self):
        """Return the current directory."""
        return self.current_dir

    def set_current_directory(self, path):
        """Set the current directory to the given path."""
        self.current_dir = path

    def execute_command(self, command):
        """
        Execute the given shell command.
        If the command is 'cd', change the directory; otherwise, run the command.
        """
        if command.startswith("cd"):
            return self.change_directory(command)
        else:
            return self.run_shell_command(command)

    def change_directory(self, command):
        """
        Change the current directory based on the 'cd' command.
        If no directory is specified, change to the user's home directory.
        """
        try:
            target_dir = (
                command.split(" ", 1)[1]
                if len(command.split(" ", 1)) > 1
                else os.path.expanduser("~")
            )
            new_dir = os.path.abspath(os.path.join(self.current_dir, target_dir))
            if os.path.isdir(new_dir):
                self.set_current_directory(new_dir)
                return f"Changed directory to {new_dir}"
            else:
                return f"{new_dir}: No such directory"
        except Exception as e:
            return str(e)

    def run_shell_command(self, command):
        """
        Run a non-'cd' shell command and capture its output.
        """
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=self.current_dir,
            )
            return result.stdout + result.stderr
        except Exception as e:
            return str(e)


class WebShellApp:
    """
    WebShellApp class manages the Flask web application and its routes.
    """

    def __init__(self, console_height=500, fixed_height=True):
        """
        Initialize the Flask app and set up routes.

        Parameters:
            console_height (int): Height of the console in pixels.
            fixed_height (bool): Whether the console should have a fixed height.
        """
        self.app = Flask(__name__)
        self.app.secret_key = "your_secret_key_here"
        self.shell = WebShell()
        self.console_height = console_height  # Set the console height
        self.fixed_height = fixed_height  # Control whether the console height is fixed

        # Define routes
        self.app.add_url_rule("/", view_func=self.index)
        self.app.add_url_rule("/run", view_func=self.run_command, methods=["POST"])

    def index(self):
        """
        Render the main page with the console.
        Pass the console height and fixed height status to the template.
        """
        if "current_dir" not in session:
            session["current_dir"] = self.shell.get_current_directory()
        return render_template(
            "index.html",
            console_height=self.console_height,
            fixed_height=self.fixed_height,
        )

    def run_command(self):
        """
        Handle the execution of a command sent from the front-end.
        Return the output as a JSON response.
        """
        try:
            command = request.json.get("command")
            if "current_dir" in session:
                self.shell.set_current_directory(session["current_dir"])

            if "clear" in command:
                # Clear the console
                output = ""
            elif "ver" in command:
                # app version
                output = f"WebShellPi {VERSION}, ({DATE})"
            elif "edit" in command:
                # edit file
                output = 'edit -> test'
                return jsonify({"output": output, "status": "success"})
            else:
                output = self.shell.execute_command(command)
            session["current_dir"] = self.shell.get_current_directory()

            return jsonify({"output": output, "status": "success"})
        except Exception as e:
            return jsonify({"output": str(e), "status": "error"})

    def run(self):
        """Run the Flask application."""
        self.app.run(host="0.0.0.0", debug=True)


if __name__ == "__main__":
    # Instantiate and run the WebShellApp with a fixed console height
    web_shell_app = WebShellApp(fixed_height=False)
    web_shell_app.run()

import os
from os.path import join

from setuptools import Command


class DocCommand(Command):
    description = "Generate autodoc and build documentation"
    user_options = [
        ("out-type=", "o", "Output documentation type, default : html")
    ]
    script_dir = join(
        "documentation", "_cache", "bat" if os.name == "nt" else "bash"
    )
    script_ext = "bat" if os.name == "nt" else "sh"

    def initialize_options(self):
        self.out_type = "html"

    def finalize_options(self):
        pass

    def run(self):
        self._run_command(
            [join(self.script_dir, "generate_doc.{}".format(self.script_ext))],
            "Generating automatic documentation",
        )

        self._run_command(
            [
                join(self.script_dir, "build_doc.{}".format(self.script_ext)),
                self.out_type,
            ],
            "Building documentation",
        )

        self.announce("Documentation available in documentation/_build/html")

    def _run_command(self, cmd, message):
        self.announce(message)
        self.spawn(cmd)

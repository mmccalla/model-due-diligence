"""Deliberately suspicious Python fixture for scanner tests.

This file is intentionally harmless but contains a static `os.system` call so
native text-pattern and AST scanners can detect shell-execution indicators.

It must not be copied into production code. The command only echoes a string and
is marked with `noqa` so repository quality gates can run without treating this
fixture as an accidental code-quality failure.
"""

import os

os.system("echo suspicious")

import subprocess
from typing import Optional, Tuple

class CommandExecutor:
    @staticmethod
    def execute_command(command: str, timeout: int = 30) -> Tuple[str, Optional[str]]:
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return "", "Command timed out"
        except Exception as e:
            return "", str(e)
from pathlib import Path
import os
import subprocess
import sys

from src.comm import project_root, queue_path


def pop_next_queue_item(file_path: Path) -> str | None:
    lines = file_path.read_text(encoding='utf-8').splitlines()
    non_empty_indexes = [index for index, line in enumerate(lines) if line.strip()]
    if not non_empty_indexes:
        return None

    first_index = non_empty_indexes[0]
    value = lines[first_index].strip().upper()
    del lines[first_index]
    file_path.write_text('\n'.join(lines) + ('\n' if lines else ''), encoding='utf-8')
    return value


if __name__ == '__main__':
    queue_file = Path(queue_path)
    queue_file.parent.mkdir(parents=True, exist_ok=True)
    queue_file.touch(exist_ok=True)

    while True:
        target = pop_next_queue_item(queue_file)
        if not target:
            print(f'No valid line found in {queue_file}')
            sys.exit(0)

        print(target)
        env = os.environ.copy()
        env['NASSAV_QUEUE_RUNNER'] = '1'
        command = [sys.executable, 'main.py', target]
        completed = subprocess.run(command, cwd=project_root, env=env)
        if completed.returncode != 0:
            print(f'Queue item failed: {target} (exit={completed.returncode})')

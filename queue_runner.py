from pathlib import Path
import subprocess
import sys

from src.comm import project_root, queue_path


def pop_last_queue_item(file_path: Path) -> str | None:
    lines = file_path.read_text(encoding='utf-8').splitlines()
    non_empty_indexes = [index for index, line in enumerate(lines) if line.strip()]
    if not non_empty_indexes:
        return None

    last_index = non_empty_indexes[-1]
    value = lines[last_index].strip().upper()
    del lines[last_index]
    file_path.write_text('\n'.join(lines) + ('\n' if lines else ''), encoding='utf-8')
    return value


if __name__ == '__main__':
    queue_file = Path(queue_path)
    queue_file.parent.mkdir(parents=True, exist_ok=True)
    queue_file.touch(exist_ok=True)

    target = pop_last_queue_item(queue_file)
    if not target:
        print(f'No valid line found in {queue_file}')
        sys.exit(1)

    print(target)
    command = [sys.executable, 'main.py', target]
    completed = subprocess.run(command, cwd=project_root)
    sys.exit(completed.returncode)

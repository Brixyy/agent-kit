#!/bin/sh
# Spustí Python skript hooku na Windows (Git Bash) i v Linuxu (cloud session).
dir=$(dirname "$0")
for py in python3 python; do
  if "$py" -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" >/dev/null 2>&1; then
    exec "$py" -I "$dir/$1"
  fi
done
echo "brixyy-kit: nenalezen Python 3 pro hook $1" >&2
exit 1

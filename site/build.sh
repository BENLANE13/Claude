#!/bin/sh
# Wraps the artifact-style fragment in a full HTML document for static hosting.
cd "$(dirname "$0")"
{
printf '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
cat lodge.html
printf '\n</html>\n'
} > ../index.html

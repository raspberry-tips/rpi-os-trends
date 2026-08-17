#!/usr/bin/env bash
# Fetch every Wayback snapshot of rpi-imager-stats.raspberrypi.com listed in cdx.txt.
# Polite: sequential, retries, skips files already downloaded.
set -u
mkdir -p wb
total=$(wc -l < cdx.txt)
i=0
ok=0
fail=0
while read -r ts status digest; do
  i=$((i + 1))
  out="wb/$ts.html"
  if [ -s "$out" ]; then
    ok=$((ok + 1))
    continue
  fi
  curl -sL --max-time 90 --retry 3 --retry-delay 8 --retry-all-errors \
    "https://web.archive.org/web/${ts}id_/https://rpi-imager-stats.raspberrypi.com/" -o "$out"
  if [ -s "$out" ] && grep -q '<caption>' "$out"; then
    ok=$((ok + 1))
  else
    fail=$((fail + 1))
    rm -f "$out"
    echo "FAIL $ts"
  fi
  if [ $((i % 10)) -eq 0 ]; then
    echo "[$i/$total] ok=$ok fail=$fail"
  fi
done < cdx.txt
echo "FERTIG: $i verarbeitet, ok=$ok, fail=$fail"

#!/bin/bash
# usage: render_all.sh BLEND OUTDIR W H SPP view1 view2 ...
BL=$1; OUT=$2; W=$3; H=$4; SPP=$5; shift 5
TOOLS=$(dirname "$0"); PY=/tmp/claude-0/-home-user-Thesis/39b1661f-97bb-543f-91db-c19f7b193371/scratchpad/bvenv/bin/python
for v in "$@"; do
  t0=$(date +%s)
  $PY $TOOLS/render_view.py $BL $v $OUT/raw_$v.png $W $H $SPP > $OUT/log_$v.txt 2>&1
  python3 $TOOLS/post.py $OUT/raw_$v.png $OUT/$v.jpg
  echo "$v done in $(( $(date +%s) - t0 ))s"
done

#!/bin/bash
# usage: render_interiors.sh BLEND MODEL OUTDIR W H SPP scene...
BL=$1; MD=$2; OUT=$3; W=$4; H=$5; SPP=$6; shift 6
TOOLS=$(dirname "$0"); PY=/tmp/claude-0/-home-user-Thesis/39b1661f-97bb-543f-91db-c19f7b193371/scratchpad/bvenv/bin/python
for s in "$@"; do
  t0=$(date +%s)
  $PY $TOOLS/build_interiors.py $BL $MD $s $OUT/raw_int_$s.png $W $H $SPP > $OUT/log_int_$s.txt 2>&1
  python3 $TOOLS/post.py $OUT/raw_int_$s.png $OUT/int_$s.jpg 1.0 1.0 0.18
  echo "int_$s done in $(( $(date +%s) - t0 ))s"
done

#!/bin/bash
# usage: render_depth.sh BLEND MODEL OUTDIR W H  ext:view... int:scene...
BL=$1; MD=$2; OUT=$3; W=$4; H=$5; shift 5
TOOLS=$(dirname "$0"); PY=/tmp/claude-0/-home-user-Thesis/39b1661f-97bb-543f-91db-c19f7b193371/scratchpad/bvenv/bin/python
mkdir -p $OUT
for item in "$@"; do
  kind=${item%%:*}; name=${item#*:}
  if [ "$kind" = ext ]; then JMD_DEPTH=1 $PY $TOOLS/render_view.py $BL $name $OUT/raw16_$name.png $W $H 8 > /dev/null 2>&1
  else JMD_DEPTH=1 $PY $TOOLS/build_interiors.py $BL $MD $name $OUT/raw16_$name.png $W $H 8 > /dev/null 2>&1; fi
  python3 $TOOLS/depth_post.py $OUT/raw16_$name.png $OUT/depth_$name.png && rm -f $OUT/raw16_$name.png
done

#!/usr/bin/env bash

# Config
PANES=8

# Create panes
tmux new-session -s "p4sec" -d
tmux set-option -g mouse on
tmux set -s escape-time 0
tmux set-option -g repeat-time 0

for (( I=0; I < ${PANES}-1; I++))
do
	tmux split-window -v
	tmux select-layout tiled
done

# pane 0
tmux send-keys -t 0 "cd example" C-m
tmux send-keys -t 0 "sudo ./run.py" C-m
tmux select-pane -t 0 -T "Mininet"

# pane 1
tmux send-keys -t 1 "./wan.py example/wan-config.json -i" C-m
tmux select-pane -t 1 -T "WC"

# pane 2
tmux send-keys -t 2 "sleep 0.2" C-m
tmux send-keys -t 2 "./global.py example/g1-config.json" C-m
tmux select-pane -t 2 -T "GC_1"

# pane 3
tmux send-keys -t 3 "sleep 0.2" C-m
tmux send-keys -t 3 "./global.py example/g2-config.json" C-m
tmux select-pane -t 3 -T "GC_2"

# pane 4
tmux send-keys -t 4 "sleep 0.4" C-m
tmux send-keys -t 4 "./local.py example/s1-config.json" C-m
tmux select-pane -t 4 -T "LC_{1, 1}"

# pane 5
tmux send-keys -t 5 "sleep 0.4" C-m
tmux send-keys -t 5 "./local.py example/s2-config.json" C-m
tmux select-pane -t 5 -T "LC_{1, 2}"

# pane 5
tmux send-keys -t 6 "sleep 0.4" C-m
tmux send-keys -t 6 "./local.py example/s3-config.json" C-m
tmux select-pane -t 6 -T "LC_{2, 1}"

tmux set -g pane-border-status bottom
tmux select-pane -t 0
tmux -2 attach-session -d

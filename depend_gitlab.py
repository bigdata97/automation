#!/bin/bash

GENERIC_FILE="generic_method.py"

# 1. Get all method names used as gm.method_name()
METHODS=$(grep -rl "from airflow import DAG" . --include="*.py" \
  | xargs grep -h "gm\." \
  | sed -nE 's/.*gm\.([a-zA-Z0-9_]+)\(.*/\1/p' \
  | sort -u)

# 2. For each method, extract self.var from cmds and map to path from __init__
for method in $METHODS; do
  # get variable name like self.xyz from cmds list in that method
  var=$(awk -v method="$method" '
    $0 ~ "def "method"\\(" {in_func=1}
    in_func && $0 ~ /cmds *= *\[/ {
      for (i=1; i<=NF; i++) {
        if ($i ~ /self\./) {
          match($i, /self\.([a-zA-Z0-9_]+)/, arr)
          if (arr[1] != "") {
            print arr[1]
            exit
          }
        }
      }
    }
    in_func && /def / && $0 !~ "def "method"\\(" {in_func=0}
  ' "$GENERIC_FILE")

  # get path of that self.var from __init__
  if [[ -n "$var" ]]; then
    path=$(awk -v var="$var" '
      $0 ~ "def __init__" {in_init=1}
      in_init && $0 ~ "self\\."var" *= *" {
        match($0, /"var"[ \t]*=[ \t]*"([^"]+)"/, m)
        if (m[1] != "") {
          print m[1]
          exit
        }
      }
    ' "$GENERIC_FILE")
    if [[ -n "$path" ]]; then
      echo "$method:$path"
    fi
  fi
done

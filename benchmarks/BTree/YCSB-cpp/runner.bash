#!/bin/bash
values=("1" "2" "4" "16" "64" "96")
for value in "${values[@]}"; do
  echo "running with $value threads and $ops operations"
  ops=$((1000000000 * value))
         16777216
  ./ycsb -run -db lmdb -P workloads/workloadc -P lmdb/lmdb.properties -p threadcount=$value -p operationcount=$ops -s > $value.txt
done

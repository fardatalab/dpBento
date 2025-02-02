for block in "64" "16K" "4M" "1G"
do
	for op in rnd seq
	do
		if [ $block="4M" -o $block="1G"]
		then
			echo "====== Measuring block = $block, op = $op, threads = 1 ======"
			sysbench memory --memory-block-size=$block --memory-total-size=10240G --memory-oper=write --memory-access-mode=$op --threads=1 --percentile=99 --histogram=off run
			sleep 10
		else
			for threads in 1 2 4 8 16 32
			do
				echo "====== Measuring block = $block, op = $op, threads = $threads ======"
				sysbench memory --memory-block-size=$block --memory-total-size=10240G --memory-oper=write --memory-access-mode=$op --threads=$threads --percentile=99 --histogram=off run
				sleep 10
			done
		fi
      done
done

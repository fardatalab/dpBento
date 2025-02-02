#!/usr/bin/env bash

# ---------------------------
# User-configurable parameters
# ---------------------------
SCALE=1          
DBGEN_DIR="/home/ubuntu/Chihan/dpBento/benchmarks/selection/tpch-dbgen"  
SCRIPT_DIR="$(pwd)" 
DUCKDB_CMD="${SCRIPT_DIR}/duckdb"         

# The TPC-H table names
TABLES=(customer lineitem nation orders partsupp part region supplier)

# First make sure duckdb exists
if [ ! -f "${DUCKDB_CMD}" ]; then
    echo "Error: ${DUCKDB_CMD} not found!"
    exit 1
fi

# -------------
# Main workflow
# -------------
for i in $(seq 1 10); do
    echo "===> Generating dataset #$i with scale factor $SCALE..."

    # Create dataset directory with absolute path
    DATASET_DIR="${SCRIPT_DIR}/dataset_$i"
    mkdir -p "${DATASET_DIR}"
    
    # Generate data from dbgen directory
    cd "${DBGEN_DIR}"
    

    for tbl in "${TABLES[@]}"; do
        case "$tbl" in
            "customer") ./dbgen -vf -s ${SCALE} -T c ;;
            "lineitem") ./dbgen -vf -s ${SCALE} -T L ;;
            "nation")   ./dbgen -vf -s ${SCALE} -T n ;;
            "orders")   ./dbgen -vf -s ${SCALE} -T O ;;
            "partsupp") ./dbgen -vf -s ${SCALE} -T S ;;
            "part")     ./dbgen -vf -s ${SCALE} -T P ;;
            "region")   ./dbgen -vf -s ${SCALE} -T r ;;
            "supplier") ./dbgen -vf -s ${SCALE} -T s ;;
        esac

        if [ -f "${tbl}.tbl" ]; then
            mv "${tbl}.tbl" "${DATASET_DIR}/"
        fi
    done
    

    cd "${SCRIPT_DIR}"
    
    # Convert each .tbl to Parquet using DuckDB
    for tbl in "${TABLES[@]}"; do
        TBL_FILE="${DATASET_DIR}/${tbl}.tbl"
        PARQUET_FILE="${DATASET_DIR}/${tbl}.parquet"
        if [ -f "${TBL_FILE}" ]; then
            echo "Converting ${TBL_FILE} to ${PARQUET_FILE} ..."
            SQL_SCRIPT="
            CREATE TABLE ${tbl} AS 
            SELECT * FROM read_csv_auto('${TBL_FILE}', delim='|');
            COPY ${tbl} TO '${PARQUET_FILE}' (FORMAT 'parquet');
            DROP TABLE ${tbl};
            "
            ${DUCKDB_CMD} << EOF
${SQL_SCRIPT}
EOF

            rm -f "${TBL_FILE}"
        else
            echo "WARNING: ${TBL_FILE} not found. Skipping."
        fi
    done

    echo "Done dataset #$i in directory: ${DATASET_DIR}"
    echo
done

echo "All done. Generated 10 datasets at scale factor ${SCALE}."

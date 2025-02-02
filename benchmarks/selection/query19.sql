SELECT
    SUM(l.l_extendedprice * (1 - l.l_discount)) AS revenue
FROM parquet_scan('./tpch/parquet/lineitem/*.parquet')l
JOIN parquet_scan('./tpch/parquet/part/*.parquet') p
    ON p.p_partkey = l.l_partkey
WHERE
    (
        p.p_brand = CAST('Brand#11' AS CHAR(10))
        AND p.p_container IN (
            CAST('SM CASE' AS CHAR(10)),
            CAST('SM BOX'  AS CHAR(10)),
            CAST('SM PACK' AS CHAR(10)),
            CAST('SM PKG'  AS CHAR(10))
        )
        AND l.l_quantity >= 3 
        AND l.l_quantity <= 3 + 10
        AND p.p_size BETWEEN 1 AND 5
        AND l.l_shipmode IN (
            CAST('AIR'     AS CHAR(10)),
            CAST('AIR REG' AS CHAR(10))
        )
        AND l.l_shipinstruct = CAST('DELIVER IN PERSON' AS CHAR(25))
    )
    OR
    (
        p.p_brand = CAST('Brand#44' AS CHAR(10))
        AND p.p_container IN (
            CAST('MED BAG' AS CHAR(10)),
            CAST('MED BOX' AS CHAR(10)),
            CAST('MED PKG' AS CHAR(10)),
            CAST('MED PACK'AS CHAR(10))
        )
        AND l.l_quantity >= 16
        AND l.l_quantity <= 16 + 10
        AND p.p_size BETWEEN 1 AND 10
        AND l.l_shipmode IN (
            CAST('AIR'     AS CHAR(10)),
            CAST('AIR REG' AS CHAR(10))
        )
        AND l.l_shipinstruct = CAST('DELIVER IN PERSON' AS CHAR(25))
    )
    OR
    (
        p.p_brand = CAST('Brand#53' AS CHAR(10))
        AND p.p_container IN (
            CAST('LG CASE' AS CHAR(10)),
            CAST('LG BOX'  AS CHAR(10)),
            CAST('LG PACK' AS CHAR(10)),
            CAST('LG PKG'  AS CHAR(10))
        )
        AND l.l_quantity >= 24
        AND l.l_quantity <= 24 + 10
        AND p.p_size BETWEEN 1 AND 15
        AND l.l_shipmode IN (
            CAST('AIR'     AS CHAR(10)),
            CAST('AIR REG' AS CHAR(10))
        )
        AND l.l_shipinstruct = CAST('DELIVER IN PERSON' AS CHAR(25))
    );

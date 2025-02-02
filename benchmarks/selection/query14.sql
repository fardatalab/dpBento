SELECT
    100.00 * SUM(
        CASE
            WHEN p.p_type LIKE 'PROMO%'
                THEN l.l_extendedprice * (1 - l.l_discount)
            ELSE 0
        END
    ) / SUM(l.l_extendedprice * (1 - l.l_discount)) AS promo_revenue
FROM parquet_scan('./tpch/parquet/lineitem/*.parquet')l
JOIN parquet_scan('./tpch/parquet/part/*.parquet') p
    ON l.l_partkey = p.p_partkey
WHERE
    l.l_shipdate >= DATE '1993-01-01'
    AND l.l_shipdate < DATE '1993-01-01' + INTERVAL '1' MONTH;

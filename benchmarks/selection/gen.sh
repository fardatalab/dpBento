#!/usr/bin/env python3

def main():

    query_template = """SELECT
    SUM(column05 * column06) AS revenue  -- column05 = l_extendedprice, column06 = l_discount
FROM parquet_scan('./dataset_{i}/lineitem.parquet')
WHERE
    column10 >= DATE '1995-01-01'  -- column10 = l_shipdate 
    AND column10 < DATE '1995-01-01' + INTERVAL '1' YEAR
    AND column06 BETWEEN 0.06 - 0.01 AND 0.06 + 0.01  -- column06 = l_discount
    AND column04 < 24;  -- column04 = l_quantity
"""


    for i in range(1, 11):
        filename = f"query6_{i}.sql"
        with open(filename, "w", encoding="utf-8") as f:

            query_text = query_template.format(i=i)
            f.write(query_text)

        print(f"Generated {filename}")

if __name__ == "__main__":
    main()

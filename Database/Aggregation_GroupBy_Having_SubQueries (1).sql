/* ============================================================================
   SQL CLASS FILE : AGGREGATION, GROUP BY, HAVING & SUBQUERIES
   Database       : BikeStores  (SQL Server)
   Schemas used   : sales.*  and  production.*

   HOW TO USE THIS FILE WHILE TEACHING
   -----------------------------------
   Do NOT press F5 on the whole file. Every demo is numbered.
   Select one demo block with the mouse and press F5 (Execute) so the class
   sees exactly one result grid at a time.

   ROADMAP
   -------
   PART 0 : Look at the raw data first
   PART 1 : Aggregate functions          (COUNT, SUM, AVG, MIN, MAX)
   PART 2 : GROUP BY                     (turn one big group into many groups)
   PART 3 : HAVING                       (filter the groups)
   PART 4 : WHERE vs HAVING + logical order of execution
   PART 5 : SUBQUERIES                   (a query inside a query)
   PART 6 : Subqueries in WHERE / SELECT / FROM
   PART 7 : Correlated subquery + EXISTS
   PART 8 : Putting it all together (aggregation + subquery in one query)
   PART 9 : Practice exercises for students
============================================================================ */

USE BikeStores;
GO


/* ============================================================================
   PART 0 : LOOK AT THE RAW DATA FIRST
   ----------------------------------------------------------------------------
   Rule for the class: never aggregate a table you have not looked at.
   First understand the grain of the table = what does ONE ROW mean?
============================================================================ */

-- DEMO 0.1 : one row = one order
SELECT * FROM sales.orders;

-- DEMO 0.2 : one row = ONE PRODUCT INSIDE an order (so an order can repeat)
SELECT * FROM sales.order_items;

-- DEMO 0.3 : one row = one customer
SELECT * FROM sales.customers;

-- DEMO 0.4 : one row = one product
SELECT * FROM production.products;

-- DEMO 0.5 : lookup tables (small, used later in subqueries)
SELECT * FROM production.brands;
SELECT * FROM production.categories;
SELECT * FROM production.stocks;


/* ============================================================================
   PART 1 : AGGREGATE FUNCTIONS
   ----------------------------------------------------------------------------
   An aggregate function takes MANY rows and returns ONE value.

        COUNT(*)      -> how many rows
        COUNT(col)    -> how many NON-NULL values in that column
        SUM(col)      -> total
        AVG(col)      -> average
        MIN(col)      -> smallest
        MAX(col)      -> largest

   With no GROUP BY, the WHOLE TABLE is treated as a single group,
   so you always get exactly ONE row back.
============================================================================ */

-- DEMO 1.1 : the whole table is one group -> one row of answers
SELECT
    COUNT(*)          AS total_orders,
    MIN(order_date)   AS first_order_date,
    MAX(order_date)   AS last_order_date
FROM sales.orders;

-- DEMO 1.2 : price statistics for all products
SELECT
    COUNT(*)          AS total_products,
    MIN(list_price)   AS cheapest,
    MAX(list_price)   AS most_expensive,
    AVG(list_price)   AS average_price,
    SUM(list_price)   AS sum_of_all_prices
FROM production.products;

-- DEMO 1.3 : COUNT(*) vs COUNT(column) -- the NULL lesson
-- shipped_date is NULL for orders that are not shipped yet,
-- and COUNT(column) simply SKIPS NULLs.
SELECT
    COUNT(*)            AS all_orders,
    COUNT(shipped_date) AS shipped_orders,
    COUNT(*) - COUNT(shipped_date) AS not_shipped_yet
FROM sales.orders;

-- DEMO 1.4 : COUNT(DISTINCT ...) -- count unique values, not rows
SELECT
    COUNT(*)                   AS order_rows,
    COUNT(DISTINCT customer_id) AS how_many_different_customers
FROM sales.orders;

-- DEMO 1.5 : aggregates ignore NULL in AVG too (important gotcha)
-- AVG divides by the COUNT OF NON-NULL values, not by the row count.
SELECT
    SUM(list_price)              AS total_price,
    COUNT(list_price)            AS rows_counted_by_avg,
    AVG(list_price)              AS avg_price,
    SUM(list_price)/COUNT(list_price) AS avg_proved_by_hand
FROM production.products;


/* ============================================================================
   PART 2 : GROUP BY
   ----------------------------------------------------------------------------
   GROUP BY splits the table into buckets of equal values, then runs the
   aggregate function ONCE PER BUCKET instead of once for the whole table.

   SYNTAX
        SELECT    <grouping columns> , <aggregate functions>
        FROM      <table>
        WHERE     <filter on rows>            -- optional, runs BEFORE grouping
        GROUP BY  <column list>
        ORDER BY  <anything>                  -- optional, runs LAST

   THE GOLDEN RULE
        Every column in the SELECT list must be EITHER
            (a) listed in GROUP BY, or
            (b) wrapped inside an aggregate function.
        Break this rule and SQL Server throws an error (see DEMO 2.7).
============================================================================ */

-- DEMO 2.1 : GROUP BY with no aggregate = just the distinct combinations
-- Read this as: "which customer ordered in which year"
SELECT
    customer_id,
    YEAR(order_date) AS order_year
FROM sales.orders
WHERE customer_id IN (1, 2)
GROUP BY
    customer_id,
    YEAR(order_date);

-- DEMO 2.2 : one grouping column -> one row per customer
SELECT customer_id
FROM sales.orders
WHERE customer_id IN (1, 2)
GROUP BY customer_id;

-- DEMO 2.3 : now add the aggregate -- this is the real GROUP BY
-- "How many orders did each customer place in each year?"
SELECT
    customer_id,
    YEAR(order_date)  AS order_year,
    COUNT(order_id)   AS order_count
FROM sales.orders
WHERE customer_id IN (1, 2, 115)
GROUP BY
    customer_id,
    YEAR(order_date)
ORDER BY
    customer_id,
    order_year;

/* TEACHING NOTE : DATE FUNCTIONS used for grouping
       YEAR(date), MONTH(date), DAY(date)
   Grouping by YEAR(order_date) turns hundreds of individual dates into a
   handful of year buckets. This is how every sales report is built. */

-- DEMO 2.4 : how many customers live in each city
SELECT
    city,
    COUNT(customer_id) AS customer_count
FROM sales.customers
GROUP BY city
ORDER BY customer_count DESC, city;

-- DEMO 2.5 : highest and lowest price in every category
SELECT
    category_id,
    MAX(list_price) AS max_price,
    MIN(list_price) AS min_price
FROM production.products
GROUP BY category_id
ORDER BY category_id;

-- DEMO 2.6 : net value of every order (the money formula)
/* Each order has several rows in order_items, one per product:
       Honda bike  qty 2  ->  2 * list_price
       Suzuki bike qty 1  ->  1 * list_price
       Toyota      qty 1  ->  1 * list_price
   Then the discount is applied.

   WHY (1 - discount) ?
       list_price 100, discount 0.30  -> 30% off, customer pays 70%
       100 * (1 - 0.30) = 70
       (100% - 30%) = 70% is the payable percentage.

   SUM() adds all the item lines of the same order into one order total. */
SELECT
    order_id,
    SUM(quantity * list_price * (1 - discount)) AS net_value
FROM sales.order_items
GROUP BY order_id
ORDER BY net_value DESC;

-- DEMO 2.7 : THE CLASSIC ERROR -- run it so the class sees the message
-- order_date is neither in GROUP BY nor inside an aggregate.
-- Expected error: "Column 'sales.orders.order_date' is invalid in the select
-- list because it is not contained in either an aggregate function or the
-- GROUP BY clause."
SELECT
    customer_id,
    order_date,
    COUNT(order_id) AS order_count
FROM sales.orders
GROUP BY customer_id;

-- DEMO 2.7 FIXED : either group by it, or aggregate it
SELECT
    customer_id,
    MAX(order_date) AS latest_order_date,   -- aggregated, so it is legal
    COUNT(order_id) AS order_count
FROM sales.orders
GROUP BY customer_id
ORDER BY customer_id;

-- DEMO 2.8 : grouping on more than one table (GROUP BY works with JOIN too)
SELECT
    c.category_name,
    COUNT(p.product_id) AS product_count,
    AVG(p.list_price)   AS avg_price
FROM production.products AS p
JOIN production.categories AS c
      ON c.category_id = p.category_id
GROUP BY c.category_name
ORDER BY product_count DESC;


/* ============================================================================
   PART 3 : HAVING
   ----------------------------------------------------------------------------
   WHERE  filters ROWS    (before grouping)
   HAVING filters GROUPS  (after grouping)

   HAVING is the only place where you are allowed to write a condition on an
   aggregate function such as COUNT(...) > 1 or AVG(...) > 1000.
============================================================================ */

-- DEMO 3.1 : only keep customers who ordered MORE THAN ONCE in a year
SELECT
    customer_id,
    YEAR(order_date) AS order_year,
    COUNT(order_id)  AS order_count
FROM sales.orders
WHERE customer_id IN (1, 2, 115)
GROUP BY
    customer_id,
    YEAR(order_date)
HAVING
    COUNT(order_id) > 1;

-- DEMO 3.2 : min/max per category, but only expensive categories
-- Note that AVG(list_price) is used in HAVING even though it is NOT selected.
-- That is perfectly legal.
SELECT
    category_id,
    MAX(list_price) AS max_price,
    MIN(list_price) AS min_price
FROM production.products
GROUP BY category_id
HAVING AVG(list_price) > 1000;

-- DEMO 3.3 : average price per category, keep only the 500-1000 band
SELECT
    category_id,
    AVG(list_price) AS avg_price
FROM production.products
GROUP BY category_id
HAVING AVG(list_price) BETWEEN 500 AND 1000;

-- DEMO 3.4 : cities that have at least 5 customers
SELECT
    city,
    COUNT(customer_id) AS customer_count
FROM sales.customers
GROUP BY city
HAVING COUNT(customer_id) >= 5
ORDER BY customer_count DESC;

-- DEMO 3.5 : big orders only -- HAVING on a SUM
SELECT
    order_id,
    SUM(quantity * list_price * (1 - discount)) AS net_value
FROM sales.order_items
GROUP BY order_id
HAVING SUM(quantity * list_price * (1 - discount)) > 10000
ORDER BY net_value DESC;


/* ============================================================================
   PART 4 : WHERE vs HAVING  +  LOGICAL ORDER OF EXECUTION
   ----------------------------------------------------------------------------
   SQL is NOT executed in the order you write it. The engine runs it like this:

        1. FROM      -> get the tables / joins
        2. WHERE     -> throw away unwanted ROWS
        3. GROUP BY  -> make the buckets
        4. HAVING    -> throw away unwanted GROUPS
        5. SELECT    -> calculate the output columns and the aliases
        6. ORDER BY  -> sort the final result
        7. TOP       -> cut the list

   Two consequences students must memorise:
     * You cannot use an aggregate in WHERE (step 2 happens before step 3).
     * You cannot use a SELECT alias in WHERE/GROUP BY/HAVING (step 5 is later),
       but you CAN use it in ORDER BY (step 6).
============================================================================ */

-- DEMO 4.1 : WHERE with an aggregate -- ERROR, run it on purpose
-- Expected: "An aggregate may not appear in the WHERE clause."
SELECT
    customer_id,
    COUNT(order_id) AS order_count
FROM sales.orders
WHERE COUNT(order_id) > 5
GROUP BY customer_id;

-- DEMO 4.1 FIXED : move the aggregate condition into HAVING
SELECT
    customer_id,
    COUNT(order_id) AS order_count
FROM sales.orders
GROUP BY customer_id
HAVING COUNT(order_id) > 5
ORDER BY order_count DESC;

-- DEMO 4.2 : both clauses in one query -- the standard shape of a report
-- WHERE trims rows FIRST (only 2017 orders),
-- HAVING trims groups AFTER (only customers with 2+ orders).
SELECT
    customer_id,
    COUNT(order_id) AS order_count_2017
FROM sales.orders
WHERE YEAR(order_date) = 2017
GROUP BY customer_id
HAVING COUNT(order_id) >= 2
ORDER BY order_count_2017 DESC;

-- DEMO 4.3 : alias rules in one screen
-- 'order_year' cannot be used in GROUP BY, but it CAN be used in ORDER BY.
SELECT
    YEAR(order_date) AS order_year,
    COUNT(*)         AS order_count
FROM sales.orders
GROUP BY YEAR(order_date)     -- must repeat the expression here
ORDER BY order_year;          -- alias is allowed here


/* ============================================================================
   PART 5 : SUBQUERIES  (also called NESTED QUERIES)
   ----------------------------------------------------------------------------
   A subquery is a SELECT written inside another SELECT.

        INNER QUERY  = runs first, produces a value or a list
        OUTER QUERY  = uses that result

   Why we need it: the value we want to filter by is not a constant -- it has
   to be CALCULATED or LOOKED UP from another table first.

   Three flavours by what the inner query returns:
        SCALAR      -> exactly one value        -> use with = < > >= <=
        MULTI-ROW   -> one column, many rows    -> use with IN / NOT IN / ANY / ALL
        TABLE       -> many columns and rows    -> use in the FROM clause
============================================================================ */

/* ---------------------------------------------------------------------------
   STEP-BY-STEP : build a subquery from two separate queries.
   Show the manual way first, then nest it. This is the best way to teach it.
--------------------------------------------------------------------------- */

-- DEMO 5.1 (step 1) : run the inner query alone and look at the id list
SELECT customer_id
FROM sales.customers
WHERE city = 'New York';

-- DEMO 5.2 (step 2) : the manual, hard-coded way -- copy/paste those ids
-- This works today, but breaks the moment a new New York customer is added.
SELECT *
FROM sales.orders
WHERE customer_id IN (16, 178, 327, 411, 854, 927, 1016);

-- DEMO 5.3 (step 3) : the same thing as ONE query -- the subquery
SELECT *                              -- OUTER QUERY
FROM sales.orders
WHERE customer_id IN (
        SELECT customer_id            -- INNER QUERY
        FROM sales.customers
        WHERE city = 'New York'
);

-- DEMO 5.4 : SCALAR subquery -- products more expensive than the average
-- The inner query returns exactly ONE number, so '>' is allowed.
SELECT
    product_name,
    list_price
FROM production.products
WHERE list_price > (SELECT AVG(list_price) FROM production.products)
ORDER BY list_price DESC;

-- DEMO 5.5 : subquery inside a subquery (2 levels deep)
-- Read it from the INSIDE OUT:
--   3rd: brand_id of 'Electra' and 'Trek'
--   2nd: average price of those brands' products
--   1st: products more expensive than that average
SELECT
    product_name,
    list_price
FROM production.products
WHERE list_price > (
        SELECT AVG(list_price)
        FROM production.products
        WHERE brand_id IN (
                SELECT brand_id
                FROM production.brands
                WHERE brand_name IN ('Electra', 'Trek')
        )
)
ORDER BY list_price DESC;

-- DEMO 5.6 : products of two named categories (lookup by name, filter by id)
SELECT *
FROM production.products
WHERE category_id IN (
        SELECT category_id
        FROM production.categories
        WHERE category_name IN ('Comfort Bicycles', 'Electric Bikes')
);

-- DEMO 5.7 : products that have more than 25 in stock somewhere
SELECT *
FROM production.products
WHERE product_id IN (
        SELECT product_id
        FROM production.stocks
        WHERE quantity > 25
);

-- DEMO 5.8 : NOT IN -- customers who never placed an order
SELECT
    customer_id,
    first_name,
    last_name,
    city
FROM sales.customers
WHERE customer_id NOT IN (
        SELECT customer_id
        FROM sales.orders
);

/* WARNING TO TEACH WITH DEMO 5.8
   NOT IN behaves badly if the inner list can contain NULL: the whole
   condition becomes UNKNOWN and you get ZERO rows back.
   Safe habits: add "WHERE col IS NOT NULL" to the inner query,
   or use NOT EXISTS (see PART 7). */


/* ============================================================================
   PART 6 : WHERE CAN A SUBQUERY LIVE?
   ----------------------------------------------------------------------------
   In WHERE   -> as a filter                      (most common)
   In SELECT  -> as an extra calculated column    (must be SCALAR)
   In FROM    -> as a derived table               (must be aliased)
============================================================================ */

-- DEMO 6.1 : subquery in SELECT -- compare each price to the global average
SELECT
    product_name,
    list_price,
    (SELECT AVG(list_price) FROM production.products) AS overall_avg,
    list_price - (SELECT AVG(list_price) FROM production.products) AS difference
FROM production.products
ORDER BY difference DESC;

-- DEMO 6.2 : subquery in FROM -- a "derived table"
-- The inner query builds a small result set; the outer query then queries it.
-- This is how you filter or aggregate an aggregate.
SELECT
    o.order_id,
    o.net_value
FROM (
        SELECT
            order_id,
            SUM(quantity * list_price * (1 - discount)) AS net_value
        FROM sales.order_items
        GROUP BY order_id
     ) AS o                     -- alias is COMPULSORY for a derived table
WHERE o.net_value > 5000
ORDER BY o.net_value DESC;

-- DEMO 6.3 : aggregate on top of an aggregate -- the average order value
-- You cannot write AVG(SUM(...)). You must aggregate in two stages.
SELECT
    COUNT(*)          AS orders_counted,
    AVG(net_value)    AS average_order_value,
    MAX(net_value)    AS biggest_order
FROM (
        SELECT
            order_id,
            SUM(quantity * list_price * (1 - discount)) AS net_value
        FROM sales.order_items
        GROUP BY order_id
     ) AS order_totals;


/* ============================================================================
   PART 7 : CORRELATED SUBQUERY  and  EXISTS
   ----------------------------------------------------------------------------
   A NORMAL subquery runs ONCE and is independent.
   A CORRELATED subquery mentions a column of the OUTER query, so it runs
   once FOR EVERY OUTER ROW -- like a loop.
============================================================================ */

-- DEMO 7.1 : correlated subquery in SELECT -- order count per customer
-- The inner query is glued to the outer row by  o.customer_id = c.customer_id
SELECT
    c.customer_id,
    c.first_name,
    c.last_name,
    (SELECT COUNT(*)
     FROM sales.orders AS o
     WHERE o.customer_id = c.customer_id) AS order_count
FROM sales.customers AS c
ORDER BY order_count DESC;

-- DEMO 7.2 : correlated subquery in WHERE
-- Products priced above the average OF THEIR OWN CATEGORY.
-- The average is recalculated for every row's category.
SELECT
    p.product_name,
    p.category_id,
    p.list_price
FROM production.products AS p
WHERE p.list_price > (
        SELECT AVG(p2.list_price)
        FROM production.products AS p2
        WHERE p2.category_id = p.category_id      -- the correlation
)
ORDER BY p.category_id, p.list_price DESC;

-- DEMO 7.3 : EXISTS -- "does at least one matching row exist?"
-- EXISTS returns TRUE/FALSE and stops at the first match, so it is fast.
SELECT
    c.customer_id,
    c.first_name,
    c.last_name
FROM sales.customers AS c
WHERE EXISTS (
        SELECT 1
        FROM sales.orders AS o
        WHERE o.customer_id = c.customer_id
);

-- DEMO 7.4 : NOT EXISTS -- the NULL-safe version of DEMO 5.8
SELECT
    c.customer_id,
    c.first_name,
    c.last_name
FROM sales.customers AS c
WHERE NOT EXISTS (
        SELECT 1
        FROM sales.orders AS o
        WHERE o.customer_id = c.customer_id
);


/* ============================================================================
   PART 8 : PUTTING IT ALL TOGETHER
   ----------------------------------------------------------------------------
   Real report queries mix aggregation and subqueries in the same statement.
============================================================================ */

-- DEMO 8.1 : subquery inside HAVING
-- Categories whose average price beats the OVERALL average price.
SELECT
    category_id,
    AVG(list_price) AS category_avg
FROM production.products
GROUP BY category_id
HAVING AVG(list_price) > (SELECT AVG(list_price) FROM production.products)
ORDER BY category_avg DESC;

-- DEMO 8.2 : WHERE (subquery) + GROUP BY + HAVING in one query
-- Read it in execution order:
--   FROM   -> all orders
--   WHERE  -> keep only New York customers  (subquery)
--   GROUP  -> one bucket per customer per year
--   HAVING -> keep buckets with 2 or more orders
--   ORDER  -> sort the final list
SELECT
    customer_id,
    YEAR(order_date) AS order_year,
    COUNT(order_id)  AS order_count
FROM sales.orders
WHERE customer_id IN (
        SELECT customer_id
        FROM sales.customers
        WHERE city = 'New York'
)
GROUP BY
    customer_id,
    YEAR(order_date)
HAVING COUNT(order_id) >= 2
ORDER BY order_count DESC;

-- DEMO 8.3 : full revenue report -- JOIN + GROUP BY + HAVING + ORDER BY
SELECT
    c.category_name,
    COUNT(DISTINCT oi.order_id) AS orders_involved,
    SUM(oi.quantity)            AS units_sold,
    SUM(oi.quantity * oi.list_price * (1 - oi.discount)) AS revenue
FROM sales.order_items AS oi
JOIN production.products   AS p ON p.product_id  = oi.product_id
JOIN production.categories AS c ON c.category_id = p.category_id
GROUP BY c.category_name
HAVING SUM(oi.quantity * oi.list_price * (1 - oi.discount)) > 100000
ORDER BY revenue DESC;

-- DEMO 8.4 : top spender found with a subquery over an aggregate
-- Stage 1 (derived table) : revenue per customer
-- Stage 2 (subquery)      : what is the maximum of those revenues
SELECT *
FROM (
        SELECT
            o.customer_id,
            SUM(oi.quantity * oi.list_price * (1 - oi.discount)) AS revenue
        FROM sales.orders AS o
        JOIN sales.order_items AS oi ON oi.order_id = o.order_id
        GROUP BY o.customer_id
     ) AS t
WHERE t.revenue = (
        SELECT MAX(rev)
        FROM (
                SELECT SUM(oi.quantity * oi.list_price * (1 - oi.discount)) AS rev
                FROM sales.orders AS o
                JOIN sales.order_items AS oi ON oi.order_id = o.order_id
                GROUP BY o.customer_id
             ) AS x
);


/* ============================================================================
   PART 9 : PRACTICE EXERCISES  (answers are commented out below each one)
   ----------------------------------------------------------------------------
   Give these to the class. Let them write the query, then reveal the answer.
============================================================================ */

-- Q1. How many products does each brand have? Sort from most to least.
/*
SELECT brand_id, COUNT(*) AS product_count
FROM production.products
GROUP BY brand_id
ORDER BY product_count DESC;
*/

-- Q2. Show every state with its customer count, but only states
--     that have more than 100 customers.
/*
SELECT state, COUNT(*) AS customer_count
FROM sales.customers
GROUP BY state
HAVING COUNT(*) > 100
ORDER BY customer_count DESC;
*/

-- Q3. Total quantity in stock for each store.
/*
SELECT store_id, SUM(quantity) AS total_units
FROM production.stocks
GROUP BY store_id;
*/

-- Q4. For each model_year, show the number of products and the average price.
--     Keep only years where the average price is above 1000.
/*
SELECT model_year, COUNT(*) AS product_count, AVG(list_price) AS avg_price
FROM production.products
GROUP BY model_year
HAVING AVG(list_price) > 1000
ORDER BY model_year;
*/

-- Q5. Using a subquery, list all products of the brand 'Trek'.
/*
SELECT product_name, list_price
FROM production.products
WHERE brand_id = (SELECT brand_id FROM production.brands WHERE brand_name = 'Trek');
*/

-- Q6. Using a subquery, find all orders placed by customers from 'California'.
/*
SELECT *
FROM sales.orders
WHERE customer_id IN (
        SELECT customer_id FROM sales.customers WHERE state = 'CA'
);
*/

-- Q7. Find the products that were never ordered.
/*
SELECT p.product_id, p.product_name
FROM production.products AS p
WHERE NOT EXISTS (
        SELECT 1 FROM sales.order_items AS oi WHERE oi.product_id = p.product_id
);
*/

-- Q8. Show each store's name with its total revenue,
--     keeping only stores above 1,000,000. (JOIN + GROUP BY + HAVING)
/*
SELECT s.store_name,
       SUM(oi.quantity * oi.list_price * (1 - oi.discount)) AS revenue
FROM sales.stores AS s
JOIN sales.orders      AS o  ON o.store_id = s.store_id
JOIN sales.order_items AS oi ON oi.order_id = o.order_id
GROUP BY s.store_name
HAVING SUM(oi.quantity * oi.list_price * (1 - oi.discount)) > 1000000
ORDER BY revenue DESC;
*/

-- Q9. Which categories have an average price BELOW the overall average price?
/*
SELECT category_id, AVG(list_price) AS category_avg
FROM production.products
GROUP BY category_id
HAVING AVG(list_price) < (SELECT AVG(list_price) FROM production.products)
ORDER BY category_avg;
*/

-- Q10. Using a derived table, show the number of orders whose
--      net value is greater than 5000.
/*
SELECT COUNT(*) AS big_orders
FROM (
        SELECT order_id, SUM(quantity * list_price * (1 - discount)) AS net_value
        FROM sales.order_items
        GROUP BY order_id
     ) AS t
WHERE t.net_value > 5000;
*/


/* ============================================================================
   ONE-SLIDE SUMMARY TO CLOSE THE CLASS
   ----------------------------------------------------------------------------
   AGGREGATE  : many rows in, one value out (COUNT SUM AVG MIN MAX).
   GROUP BY   : run that aggregate once per bucket instead of once per table.
   GOLDEN RULE: every SELECT column is either in GROUP BY or in an aggregate.
   WHERE      : filters rows   BEFORE grouping. No aggregates allowed here.
   HAVING     : filters groups AFTER  grouping. Aggregates belong here.
   ORDER      : FROM -> WHERE -> GROUP BY -> HAVING -> SELECT -> ORDER BY.
   SUBQUERY   : a query whose result feeds another query.
                scalar -> use with =, >, <
                list   -> use with IN / NOT IN / EXISTS
                table  -> use in FROM with an alias
   CORRELATED : mentions the outer row, so it runs once per outer row.
   NULL TRAPS : COUNT(col) skips NULL; NOT IN with NULL returns nothing.
============================================================================ */

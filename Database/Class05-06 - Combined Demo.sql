/* ============================================================================
   Class 05 + Class 06  —  Combined Demo
   Topics : Set Operators | CTEs | Constraints | CASE & COALESCE
   Database: BikeStores
   ============================================================================
   Run each block one at a time (select + F5) so students see one idea per run.
   ========================================================================== */

USE BikeStores;
GO

/* ============================================================================
   PART 1 — SET OPERATORS
   ----------------------------------------------------------------------------
   JOIN  = stitches tables side by side  -> adds COLUMNS
   UNION = stacks results on top of each other -> adds ROWS

   Rules for every set operator:
     1. Same number of columns in both queries
     2. Compatible data types, column by column (position matters, names don't)
     3. Column names come from the FIRST query
     4. One ORDER BY only, at the very end
   ========================================================================== */

-- 1.1 UNION -> stacks rows AND removes duplicates
SELECT first_name, last_name FROM sales.staffs      -- 10 rows
UNION
SELECT first_name, last_name FROM sales.customers;  -- 1445 rows
-- Result is 1454, not 1455 -> one name existed in both lists and got de-duplicated.

-- 1.2 UNION ALL -> stacks rows and KEEPS duplicates
SELECT first_name, last_name FROM sales.staffs
UNION ALL
SELECT first_name, last_name FROM sales.customers;
-- Result is 1455. UNION ALL is faster because it never sorts to find duplicates.
-- Rule of thumb: use UNION ALL unless you actually need de-duplication.

-- 1.3 Column names are taken from the first query only
SELECT first_name AS name FROM sales.staffs
UNION ALL
SELECT city FROM sales.customers;   -- header still says "name"

-- 1.4 Column COUNT must match -- this one fails on purpose
SELECT first_name, last_name, email FROM sales.staffs   -- 3 columns
UNION ALL
SELECT first_name, last_name FROM sales.customers;      -- 2 columns -> ERROR
-- Fix it by padding the short side with a literal:
SELECT first_name, last_name, email          FROM sales.staffs
UNION ALL
SELECT first_name, last_name, NULL AS email  FROM sales.customers;

-- 1.5 INTERSECT -> rows present in BOTH results
SELECT city FROM sales.customers
INTERSECT
SELECT city FROM sales.stores;
-- Cities where we have both a store and at least one customer.

-- 1.6 EXCEPT -> rows in the FIRST result that are NOT in the second
SELECT city FROM sales.customers
EXCEPT
SELECT city FROM sales.stores;
-- Customer cities with no store -> a real business question: where to expand.

-- EXCEPT is directional. Flip the queries and you get a different answer:
SELECT city FROM sales.stores
EXCEPT
SELECT city FROM sales.customers;

-- 1.7 ORDER BY belongs to the whole set, so it goes last (once)
SELECT city, 'customer' AS source FROM sales.customers
UNION
SELECT city, 'store'    AS source FROM sales.stores
ORDER BY city;


/* ============================================================================
   PART 2 — CTE  (Common Table Expression)
   ----------------------------------------------------------------------------
   A CTE is a named, temporary result set that lives only for ONE statement.

   Why we use it:
     - Readability : break one giant query into named steps
     - Reusability : reference the same block many times in that statement
     - Replaces messy nested sub-queries

   Syntax:
     WITH cte_name (col1, col2, ...)
     AS ( inner_query )
     SELECT ... FROM cte_name;          <-- must follow immediately

   The column list is optional; if you skip it, every column in the inner
   query needs its own alias.
   ========================================================================== */

-- 2.1 The problem: you cannot filter an aggregate by its alias
SELECT
    st.first_name + ' ' + st.last_name        AS full_name,
    YEAR(o.order_date)                        AS order_year,
    SUM(oi.quantity * oi.list_price * (1 - oi.discount)) AS net_sales
FROM sales.staffs st
JOIN sales.orders o       ON o.staff_id  = st.staff_id
JOIN sales.order_items oi ON oi.order_id = o.order_id
GROUP BY st.first_name + ' ' + st.last_name, YEAR(o.order_date);

-- 2.2 Same query wrapped in a CTE -> now the outer query filters it easily
WITH cte_sales_by_staff (full_name, order_year, net_sales)
AS
(
    SELECT
        st.first_name + ' ' + st.last_name,
        YEAR(o.order_date),
        SUM(oi.quantity * oi.list_price * (1 - oi.discount))
    FROM sales.staffs st
    JOIN sales.orders o       ON o.staff_id  = st.staff_id
    JOIN sales.order_items oi ON oi.order_id = o.order_id
    GROUP BY st.first_name + ' ' + st.last_name, YEAR(o.order_date)
)
SELECT *
FROM cte_sales_by_staff
WHERE order_year = 2016
ORDER BY net_sales DESC;

-- 2.3 Aggregating an aggregate -> "average orders handled per staff member"
WITH cte_staff_orders (staff_id, order_count)
AS
(
    SELECT staff_id, COUNT(*)
    FROM sales.orders
    GROUP BY staff_id
)
SELECT AVG(order_count) AS avg_orders_per_staff,
       MAX(order_count) AS busiest_staff_orders
FROM cte_staff_orders;

-- 2.4 A CTE can be referenced MORE THAN ONCE in the same statement
--     (a sub-query would have to be written out twice)
WITH cte_staff_orders (staff_id, order_count)
AS
(
    SELECT staff_id, COUNT(*) FROM sales.orders GROUP BY staff_id
)
SELECT s.staff_id, s.order_count, a.avg_order_count
FROM cte_staff_orders s
CROSS JOIN (SELECT AVG(order_count) AS avg_order_count FROM cte_staff_orders) a
WHERE s.order_count > a.avg_order_count;    -- above-average performers

-- 2.5 MULTIPLE CTEs -> one WITH, comma separated, then join them
--     Step 1: how many products per category
--     Step 2: how much money per category
--     Step 3: join the two steps
WITH cte_category_counts (category_id, category_name, product_count)
AS
(
    SELECT c.category_id, c.category_name, COUNT(p.product_id)
    FROM production.categories c
    JOIN production.products p ON p.category_id = c.category_id
    GROUP BY c.category_id, c.category_name
),
cte_category_sales (category_id, net_sales)
AS
(
    SELECT p.category_id,
           SUM(oi.quantity * oi.list_price * (1 - oi.discount))
    FROM production.products p
    JOIN sales.order_items oi ON oi.product_id = p.product_id
    GROUP BY p.category_id
)
SELECT cc.category_id, cc.category_name, cc.product_count, cs.net_sales
FROM cte_category_counts cc
JOIN cte_category_sales  cs ON cs.category_id = cc.category_id
ORDER BY cs.net_sales DESC;

-- NOTE: a CTE is NOT a table. This on its own fails -- the name is already gone:
-- SELECT * FROM cte_category_counts;


/* ============================================================================
   PART 3 — CONSTRAINTS
   ----------------------------------------------------------------------------
   Constraints are rules the database itself enforces, so bad data can never
   get in -- no matter which app or person is inserting it.

     PRIMARY KEY : unique + NOT NULL, identifies each row (one per table)
     FOREIGN KEY : value must exist in the parent table (referential integrity)
     NOT NULL    : column must always have a value
     UNIQUE      : no repeated values (allows one NULL); many per table
     CHECK       : value must satisfy a condition
   ========================================================================== */

-- 3.1 COMPOSITE PRIMARY KEY -> one key made of two columns together
--     order_id alone repeats, item_id alone repeats, the PAIR is unique.
DROP TABLE IF EXISTS demo_order_items;
CREATE TABLE demo_order_items (
    order_id INT,
    item_id  INT,
    quantity INT,
    PRIMARY KEY (order_id, item_id)
);

-- Adding the key later, with ALTER (same result, different timing)
DROP TABLE IF EXISTS demo_order_items_2;
CREATE TABLE demo_order_items_2 (order_id INT, item_id INT, quantity INT);
ALTER TABLE demo_order_items_2 ADD PRIMARY KEY (order_id, item_id);

-- 3.2 FOREIGN KEY + referential actions
DROP TABLE IF EXISTS demo_vendors;          -- child dropped first
DROP TABLE IF EXISTS demo_vendor_group;     -- then parent

CREATE TABLE demo_vendor_group (
    group_id   INT PRIMARY KEY,
    group_name VARCHAR(100) NOT NULL
);

CREATE TABLE demo_vendors (
    vendor_id   INT PRIMARY KEY,
    vendor_name VARCHAR(100) NOT NULL,
    group_id    INT,
    CONSTRAINT fk_vendor_group FOREIGN KEY (group_id)
        REFERENCES demo_vendor_group (group_id)
        ON UPDATE CASCADE      -- parent id changes -> child follows automatically
        ON DELETE SET NULL     -- parent deleted   -> child group_id becomes NULL
);
/*  Available actions for ON UPDATE / ON DELETE:
      NO ACTION   (default) block the change if children exist
      CASCADE     apply the same change to the children
      SET NULL    set the child column to NULL   (column must allow NULL)
      SET DEFAULT set the child column to its DEFAULT value              */

INSERT INTO demo_vendor_group (group_id, group_name)
VALUES (1, 'Mandi'), (2, 'Lucky'), (3, 'Kababjees');

INSERT INTO demo_vendors (vendor_id, vendor_name, group_id)
VALUES (14, 'Lucky One', 2), (15, 'KFC', 2), (16, 'Bakers', 3);

-- Orphan row -> group 99 does not exist in the parent -> FK error
INSERT INTO demo_vendors (vendor_id, vendor_name, group_id) VALUES (17, 'Ghost', 99);

-- Watch ON DELETE SET NULL do its job
DELETE FROM demo_vendor_group WHERE group_id = 3;
SELECT * FROM demo_vendors;     -- 'Bakers' now has group_id = NULL

-- 3.3 NOT NULL, UNIQUE and CHECK together
DROP TABLE IF EXISTS demo_products;
CREATE TABLE demo_products (
    product_id   INT PRIMARY KEY,
    product_name VARCHAR(255) NOT NULL UNIQUE,   -- required AND no duplicates
    email        VARCHAR(100),
    unit_price   DECIMAL(10,2) CHECK (unit_price > 0),
    CONSTRAINT uq_demo_products_email UNIQUE (email)   -- named constraint
);

INSERT INTO demo_products (product_id, product_name, email, unit_price)
VALUES (1, 'Bike', 'ayan@gmail.com', 1000.00);      -- OK

INSERT INTO demo_products (product_id, product_name, email, unit_price)
VALUES (2, 'Bike', 'other@gmail.com', 500.00);      -- UNIQUE violation (name)

INSERT INTO demo_products (product_id, product_name, email, unit_price)
VALUES (3, 'Bike 2', 'ayan@gmail.com', 500.00);     -- UNIQUE violation (email)

INSERT INTO demo_products (product_id, product_name, email, unit_price)
VALUES (4, 'Bike 3', 'b3@gmail.com', 0);            -- CHECK violation (price > 0)

INSERT INTO demo_products (product_id, product_name, email, unit_price)
VALUES (5, NULL, 'b5@gmail.com', 200);              -- NOT NULL violation

-- PRIMARY KEY vs UNIQUE:
--   PK -> one per table, never NULL, usually the clustered index
--   UNIQUE -> many per table, allows a single NULL


/* ============================================================================
   PART 4 — CASE  &  COALESCE
   ----------------------------------------------------------------------------
   CASE is IF/ELSE inside a query. It returns a VALUE, so it can sit in
   SELECT, WHERE, ORDER BY, GROUP BY or an aggregate.
   Two forms:
     Simple   : CASE column WHEN value THEN result ... END        (equality only)
     Searched : CASE WHEN condition THEN result ... END           (any condition)
   Evaluation stops at the FIRST match. No ELSE -> unmatched rows return NULL.
   ========================================================================== */

-- 4.1 The raw data is unreadable: status is stored as 1/2/3/4
SELECT order_status, COUNT(*) AS order_count
FROM sales.orders
GROUP BY order_status
ORDER BY order_status;

-- 4.2 SIMPLE CASE -> turn codes into labels
SELECT
    CASE order_status
        WHEN 1 THEN 'Pending'
        WHEN 2 THEN 'Processing'
        WHEN 3 THEN 'Rejected'
        WHEN 4 THEN 'Completed'
        ELSE 'Unknown'
    END              AS order_status,
    COUNT(order_id)  AS order_count
FROM sales.orders
GROUP BY order_status          -- group by the raw column, label it in SELECT
ORDER BY order_status;

-- 4.3 SEARCHED CASE -> bucketing by range (ranges need conditions, not equality)
SELECT
    order_id,
    SUM(quantity * list_price) AS order_value,
    CASE
        WHEN SUM(quantity * list_price) <= 1000 THEN 'Low'
        WHEN SUM(quantity * list_price) <= 5000 THEN 'Medium'
        ELSE 'High'
    END AS order_priority
FROM sales.order_items
GROUP BY order_id
ORDER BY order_value DESC;
-- Because CASE stops at the first true branch, the second WHEN already means
-- "> 1000 AND <= 5000". No need to repeat the lower bound.

-- 4.4 CASE inside an aggregate -> pivot rows into columns (conditional counting)
SELECT
    SUM(CASE WHEN order_status = 1 THEN 1 ELSE 0 END) AS pending,
    SUM(CASE WHEN order_status = 2 THEN 1 ELSE 0 END) AS processing,
    SUM(CASE WHEN order_status = 3 THEN 1 ELSE 0 END) AS rejected,
    SUM(CASE WHEN order_status = 4 THEN 1 ELSE 0 END) AS completed
FROM sales.orders;

-- 4.5 COALESCE -> returns the first non-NULL argument. Great for defaults.
SELECT
    customer_id,
    phone,
    COALESCE(phone, 'No phone on file') AS phone_display
FROM sales.customers
WHERE phone IS NULL;

-- Shipped date is NULL for orders not yet shipped -> show a fallback
SELECT order_id, order_status,
       COALESCE(CONVERT(VARCHAR(10), shipped_date, 120), 'Not shipped') AS shipped
FROM sales.orders
WHERE shipped_date IS NULL;

-- COALESCE is just a shortcut for a searched CASE:
--   COALESCE(a, b)  ==  CASE WHEN a IS NOT NULL THEN a ELSE b END
-- ISNULL(a, b) does the same but takes exactly 2 arguments (T-SQL only).


/* ============================================================================
   CLEANUP — drop the demo tables
   ========================================================================== */
DROP TABLE IF EXISTS demo_order_items;
DROP TABLE IF EXISTS demo_order_items_2;
DROP TABLE IF EXISTS demo_products;
DROP TABLE IF EXISTS demo_vendors;
DROP TABLE IF EXISTS demo_vendor_group;


/* ============================================================================
   PRACTICE QUESTIONS
   ============================================================================

   SET OPERATORS
   1. List every distinct city that appears in either sales.customers or
      sales.stores, with a column showing where it came from. Sort by city.
   2. Which product brands have never been sold? Use EXCEPT on brand_id
      (production.products vs the brands actually present in sales.order_items).
   3. Find the states that have BOTH customers and stores using INTERSECT.
      Then rewrite the same answer using an INNER JOIN and compare the results.
   4. Explain in one line why the UNION in demo 1.1 returned 1454 instead of 1455.

   CTEs
   5. Using a CTE, list the top 5 customers by total net sales
      (quantity * list_price * (1 - discount)).
   6. Build a CTE of net sales per store per year, then return only the
      store/year combinations above 500,000.
   7. Write two CTEs -- one for order count per customer, one for total spend
      per customer -- and join them to show customers with more than 2 orders.
   8. Rewrite the CTE from Q5 as a nested sub-query. Which version is easier
      to read, and why?
   9. Extend demo 2.5 so it only counts orders where order_status = 4
      (completed).

   CONSTRAINTS
   10. Create a table `student` with: student_id as PK, cnic as UNIQUE,
       name as NOT NULL, and age with a CHECK that it is between 5 and 100.
   11. Create `course` and `enrollment` where enrollment has a composite PK
       (student_id, course_id) and FKs to both parents with ON DELETE CASCADE.
       Insert rows, delete a student, and show what happened to enrollment.
   12. Try inserting two rows with NULL cnic into `student`. Does UNIQUE allow
       it? How many? Explain the difference from a PRIMARY KEY.
   13. What happens if you use ON DELETE SET NULL on a column defined as
       NOT NULL? Predict the answer first, then test it.

   CASE & COALESCE
   14. Label every product as 'Budget' (< 500), 'Standard' (500-1500) or
       'Premium' (> 1500) based on list_price, then count products per label.
   15. For each store, use CASE inside SUM() to show completed and rejected
       order counts as two side-by-side columns.
   16. Show customer full name, and a `contact` column that prefers phone but
       falls back to email, and to 'No contact' if both are NULL (COALESCE).
   17. Sort sales.orders so that all completed orders come first, then
       processing, then pending, then rejected -- using CASE in ORDER BY.
   18. Combine the concepts: build a CTE of net sales per staff member, then
       use CASE to rate each one as 'Star', 'Good' or 'Needs Improvement'.

   ========================================================================== */

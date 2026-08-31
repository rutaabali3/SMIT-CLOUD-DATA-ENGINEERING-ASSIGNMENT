-- ============================================================
--  ASSIGNMENT 01 — Querying, Sorting & Filtering (Review + New)
--  Database : BikeStores
--  Topics   : SELECT, WHERE, ORDER BY, TOP/OFFSET-FETCH, DISTINCT,
--             AND / OR, IN / NOT IN, BETWEEN, IS NULL, Aliases, LIKE
-- ============================================================


-- ============================================================
--  Question 1 — SELECT, WHERE & AND
--  The operations team wants a roster of active staff members
--  working at store_id = 1.
--  Retrieve the staff_id, first_name, last_name, and email of
--  every staff member where store_id = 1 AND active = 1.
-- ============================================================

-- Write your query below:
SELECT staff_id, first_name, last_name, email
FROM sales.staffs
WHERE store_id = 1
  AND active = 1;



-- ============================================================
--  Question 2 — ORDER BY (Multiple Columns)
--  Retrieve product_id, product_name, category_id, and list_price
--  for all products.
--  Sort the results by category_id ascending, and within the
--  same category sort by list_price descending.
-- ============================================================

-- Write your query below:
SELECT product_id, product_name, category_id, list_price
FROM production.products
ORDER BY category_id ASC,
         list_price DESC;



-- ============================================================
--  Question 3 — TOP N & TOP PERCENT
--  a) The logistics team wants to see the 3 most recently placed
--     orders. Return order_id, customer_id, and order_date for
--     the top 3 orders, most recent first.
--  b) Return the top 10 percent of products by list_price
--     (all columns). How many rows does that return? Add the
--     row count as a comment in your answer.
-- ============================================================

-- Part a:
SELECT TOP 3 order_id, customer_id, order_date
FROM sales.orders
ORDER BY order_date DESC;

-- Part b:
SELECT TOP 10 PERCENT *
FROM production.products
ORDER BY list_price DESC;

SELECT COUNT(*) AS total_products
FROM (
    SELECT TOP 10 PERCENT product_id
    FROM production.products
    ORDER BY list_price DESC
) AS top_products;
-- Answer: 33 rows

-- ============================================================
--  Question 4 — OFFSET & FETCH (Pagination)
--  Customer support is browsing the customer list alphabetically
--  by last name, 10 customers per page.
--  Write a single query that returns ONLY page 2 (rows 11-20).
-- ============================================================

SELECT customer_id, first_name, last_name, email
FROM sales.customers
ORDER BY last_name ASC,
         customer_id ASC
OFFSET 10 ROWS
FETCH NEXT 10 ROWS ONLY;


-- ============================================================
--  Question 5 — DISTINCT
--  a) The purchasing team wants to know which brands currently
--     have at least one product priced above $1,000.
--     List the distinct brand_id values that qualify.
--  b) List every distinct combination of category_id and
--     model_year that appears in production.products, sorted
--     by category_id then model_year.
-- ============================================================

-- Part a:
SELECT DISTINCT brand_id
FROM production.products
WHERE list_price > 1000;

-- Part b:
SELECT DISTINCT category_id, model_year
FROM production.products
ORDER BY category_id ASC,
         model_year ASC;


-- ============================================================
--  Question 6 — IN / NOT IN
--  a) Store managers for store_id 1 and 3 want a combined list
--     of every order placed at either store. Show order_id,
--     store_id, and order_date for orders where store_id IN (1, 3).
--  b) A different team wants every order that was NOT placed at
--     store_id 2. Show the same three columns.
-- ============================================================

-- Part a:
SELECT order_id, store_id, order_date
FROM sales.orders
WHERE store_id IN (1, 3);

-- Part b:
SELECT order_id, store_id, order_date
FROM sales.orders
WHERE store_id NOT IN (2);


-- ============================================================
--  Question 7 — BETWEEN combined with AND / OR
--  Find every product that meets ALL of the following:
--    - list_price is between $300 and $1,200 (inclusive)
--    - model_year is 2017 OR 2018
--  Show product_name, model_year, and list_price, sorted by
--  list_price ascending.
--  Hint: use parentheses to control the order of evaluation.
-- ============================================================

SELECT product_name, model_year, list_price
FROM production.products
WHERE list_price BETWEEN 300 AND 1200
  AND (model_year = 2017 OR model_year = 2018)
ORDER BY list_price ASC;


-- ============================================================
--  Question 8 — IS NULL / IS NOT NULL
--  HR is reviewing the staff reporting structure.
--  a) List every staff member who has NO manager (the top of
--     the org chart). Show staff_id, first_name, and last_name.
--  b) List every staff member who DOES have a manager on record.
--     Show staff_id, first_name, last_name, and manager_id.
-- ============================================================

-- Part a:
SELECT staff_id, first_name, last_name
FROM sales.staffs
WHERE manager_id IS NULL;

-- Part b:
SELECT staff_id, first_name, last_name, manager_id
FROM sales.staffs
WHERE manager_id IS NOT NULL;


-- ============================================================
--  Question 9 — Aliases & LIKE
--  Marketing wants a mailing list of every customer whose email
--  address is hosted on gmail.com.
--  Show the customer's full name as full_name (built from
--  first_name + last_name) and their email, using a table alias
--  for sales.customers. Sort by full_name ascending.
-- ============================================================

SELECT
    c.first_name + ' ' + c.last_name AS full_name,
    c.email
FROM sales.customers AS c
WHERE c.email LIKE '%@gmail.com'
ORDER BY full_name ASC;


-- ============================================================
--  END OF ASSIGNMENT 01
-- ============================================================

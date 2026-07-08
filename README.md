beanquery: Customizable lightweight SQL query tool
==================================================

beanquery is a customizable and extensible lightweight SQL query tool
that works on tabular data, including [`Beancount`][bc] ledger data.

[bc]: https://beancount.github.io/

This is a soft-fork. See the [main repository][bq] for the official version.


[bq]: https://github.com/beancount/beanquery

This version contains some additional features that I find useful. I try
my best to keep in sync and provide changes to upstream, if the community
accepts them.

There is an online documentation for BQL functions, which you can find at
https://mlell.github.io/beanquery.

## Branch status

Branches that are WIP in this fork:

| Name | Base Commit | Base Date | Merged | Description |
|------|-------------|-----------|--------|-------------|
| dev-function-help | `62b6abba7` | 2026-06-11 22:28:39 +0200 | ✓ | Group function help by type |
| dev-all-lhs | `62b6abba7` | 2026-06-11 22:28:39 +0200 | ✓ | ALL/ANY syntax with inverted operand order |
| dev-case-when | `62b6abba7` | 2026-06-11 22:28:39 +0200 | ✓ | Provide SQL equivalent of if/else |
| dev-date-cap | `62b6abba7` | 2026-06-11 22:28:39 +0200 | ✓ | Lump dates before/after some point in time |
| dev-union | `62b6abba7` | 2026-06-11 22:28:39 +0200 | ✓ | SQL UNION support |
| dev-grouping-sets | `62b6abba7` | 2026-06-11 22:28:39 +0200 | ✓ | SQL GROUPING SETS/ROLLUP/CUBE support |

## Branch `dev-union`: UNION queries in BQL

Status:

 - [x] Implemented
 - [x] Unit tests
 - [ ] Open Pull Request: beancount/beanquery#281

SQL UNION queries in BQL. This provides a new base for re-implementing 
GROUP BY ROLLUP/CUBE/GROUPING SETS

## Branch `dev-grouping-sets`: `GROUP BY ROLLUP`/`CUBE`

- [x] Re-implement using `EvalUnion` provided by `dev-union`
- [x] Unit tests
- [ ] Pull request: beancount/beanquery#265

Add rows that show a higher grouping level. This allows to add marginal columns
to `PIVOT BY` output:

```
beanquery> select yearmonth(date) as month, account, sum(position) where account !~ "Assets"  group by cube (account,month) 
pivot by account,month

  account/month      2024-02-01    2024-03-01    2024-04-01      (Total)   
------------------  ------------  ------------  ------------  -------------
Expenses:Dining                     120.50 USD     45.25 USD     165.75 USD
Expenses:Groceries    250.00 USD    310.75 USD    275.60 USD     836.35 USD
Income:Salary       -5000.00 USD  -5000.00 USD  -5000.00 USD  -15000.00 USD
(Total)             -4750.00 USD  -4568.75 USD  -4679.15 USD  -13997.90 USD
```

## Branch `dev-function-help`: Group function help by object type

Status:
 - [x] Implemented, no unit tests (only documentation)
 - [ ] Open Pull Request: beancount/beanquery#263

Provides the `.help functions` command. This is intended to help find relevant
functions easier. 

## Branch `dev-all-lhs`: Allow BQL Syntax `ALL(set) <op> <value>` (same for `ANY`),

Status:
 - [x] Implemented
 - [x] Unit tests
 - [ ] Open Pull request: beancount/beanquery#264

... in addition to `<value> <op> ALL(set)` as it is common in SQL dialects. This
allows for more intuitive syntax, especially using `~`. We now can do
`ALL(accounts) ~ 'Assets:.*'` instead of needing the operator `?~` that has
inverted operand order like `'Assets:.*' ?~ ANY(accounts)`


## Branch `dev-date-cap`: Add the BQL function `date_cap()`

Status:
 - [ ] Re-implement, use str return type to avoid complex result types (data or Sentinel value)
 - [ ] Unit tests

This replaces all dates before or after some point in time with a special value
`(before)`/`(after)`. This allows for example to display balances for the
recent months, while still displaying the overall balance on the account
using e.g. `SELECT date_cap(yearmonth(), <date>) as month , sum(position) GROUP BY month`

```bql
  SELECT date_cap(
      yearmonth(date),
      yearmonth(2025-11-10) - interval('6 months'),
      ''
    ) AS month,
      last(balance) as bal,
      sum(position) as sum
    WHERE account = 'Assets:Checking'
    GROUP BY month
```

```
   month        bal            sum
----------  ------------  -------------
(earlier)    1555.24 EUR    1555.24 EUR
2025-08-01   2102.21 EUR     546.97 EUR
2025-09-01   1677,02 EUR    -425.19 EUR
2025-10-01    919,03 EUR    -757.99 EUR
```

Without date_cap, you would need to use WHERE to filter for the last 6 months.
However, this would alter the balance column, showing only the accumulated
changes since the filtered time period began—not the actual account balance.



## Branch `dev-case-when` 

Status:

- [x] Implemented
- [ ] No Pull Request, yet.

Provide SQL CASE WHEN, for example

```
SELECT 
  account, 
  CASE WHEN abs(number) > 100 THEN 'high' ELSE 'low' END as amount
LIMIT 10
```

## Additional changes arising from combinations of features

`beanquery/parser/bql.ebnf` dev-all-lhs + dev-union:

```
(* This operator is special in that it has parentheses. Avoid double parentheses
with subquerys ALL( (SELECT ...) ) by &(...) look-ahead *)
any::Any
    =
    | left:sum op:op 'any' &('(' 'SELECT') right:subquery side:`rhs`
    | left:sum op:op 'any' '(' right:expression ')' side:`rhs`
    | 'any' &('(' 'SELECT' ) left:subquery op:op right:sum side:`lhs`
    | 'any' '(' left:expression ')' op:op right:sum side:`lhs`
    ;

(* This operator is special in that it has parentheses. Avoid double parentheses
with subquerys ALL( (SELECT ...) ) by &(...) look-ahead *)
all::All
    =
    | left:sum op:op 'all' &('(' 'SELECT') right:subquery side:`rhs`
    | left:sum op:op 'all' '(' right:expression ')' side:`rhs`
    | 'all' &('(' 'SELECT' ) left:subquery op:op right:sum side:`lhs`
    | 'all' '(' left:expression ')' op:op right:sum side:`lhs`
    ;
```

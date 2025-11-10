select count(*) from sample where sample.Mobile='Samsung' and Car='BMW' ;

select count(*) from sample where gender='Male' and Mobile='Nokia';

select sample.Car, count(sample.Car) as frequency from sample group by Car order by frequency DESC ;

Select count(id) from sample where gender = 'Female';

select DISTINCT count(sample.City)  from sample;

SELECT ROUND((COUNT(CASE WHEN Credit_Card is NULL THEN 1 END) * 100.0) / COUNT(*), 2) AS Percent_Without_Credit_Card FROM sample;

SELECT
  (SUM(CASE
         WHEN Credit_Card IS NULL OR TRIM(Credit_Card) = '' THEN 1
         ELSE 0
       END) * 100.0 / COUNT(*)) AS unfilled_percentage
FROM sample;


select * from emp LIMIT 5;

SELECT
  emp_bank,
  COUNT(*) AS frequency
FROM emp
where emp.emp_job = 'Pipelayer'
GROUP BY emp_bank
ORDER BY frequency DESC;

PRAGMA table_info(emp);

PRAGMA table_info(sample);

select count(emp.emp_job) from emp where emp.emp_role='Pipelayer' and emp.emp_bank='WELLS FARGO BANK';

select Car, count(Car) from sample natural join emp where emp.emp_role = 'Supervisor' group by Car;

select sample.Car, count(sample.Car) from sample natural join emp where emp.emp_job = 'Brickmason' group by sample.Car ;


SELECT count(first_name)
FROM sample
WHERE first_name LIKE 'A%';

select * from sample;

select count(*) from sample where Credit_Card is NULL;
select count(Car) from sample where Car='Volkswagen';

select distinct emp.emp_role from emp;

select count(*) from sample where Credit_Card = 'mastercard';

select Mobile, count(Mobile) from sample group by Mobile;

select * from emp LIMIT 10;

select * from sample;

select emp.emp_job, count(emp.emp_job) from emp where emp_role='Supervisor' group by emp.emp_job order by count(emp.emp_job) DESC;

select sample.Car, count(sample.Car) from sample natural join emp where emp.emp_role='Construction Worker' group by sample.Car ;

select sample.Car, count(sample.Car) from sample natural join emp where emp.emp_role='Construction Worker' and sample.Car='Ford';

select emp.emp_uni, count(emp.emp_uni) from emp group by emp.emp_uni order by count(emp_uni) DESC;

select sample.Credit_Card, count(sample.Credit_Card) from sample natural join emp where emp_bank='CITIBANK' group by sample.Credit_Card ;

select sample.Mobile, count(sample.Mobile) from sample group by sample.Mobile;

select Mobile, count(Mobile) from sample natural join emp where emp_job='Plasterers' group by Mobile ;

select emp.emp_job, count(emp.emp_job) from emp group by emp.emp_job;

select gender, count(gender) from sample where gender='Female';

select sum(id) from sample;

select sample.Car, count(sample.Car) from sample natural join emp where emp.emp_job = 'Brickmason' and sample.Car='Ford' ;

select name from sqlite_master where type='table';

select count(*) from sample;

select * from emp LIMIT 5;

select DISTINCT emp.emp_role from emp;

select gender, count(sample.gender) from sample where gender='Male';

select emp.emp_job, count(emp.emp_job) from emp group by emp.emp_job order by count(emp_job) DESC LIMIT 1;

select emp.emp_role from emp group by emp.emp_role;

select count(*) from emp where emp_uni is null;

select Car, count(*) from sample group by Car order by count(*) DESC;

select gender, count(*) from sample group by gender order by count(*) DESC;

select emp_job, count(emp_job) as freq from emp where emp_role='Supervisor' group by emp_job order by freq desc;

SELECT gender, ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM sample), 3) AS percentage FROM sample GROUP BY gender ORDER BY percentage DESC;

SELECT ROUND((SUM(CASE WHEN first_name LIKE 'A%' THEN 1 ELSE 0 END) * 1.0) /
             NULLIF(SUM(CASE WHEN first_name LIKE 'C%' THEN 1 ELSE 0 END), 0),2) AS ratio_A_to_C FROM sample;

select count(*) from sample where Credit_Card='jcb' and Car='BMW';

select count(*) from sample natural join emp where Mobile='BLU' and emp_bank='WELLS FARGO BANK' and emp_job='Landscaper';

select sample.Mobile, (count(sample.Mobile) * 100 / (select Count(*) from emp where emp_job='Boilermaker'))
    as mob_freq from sample natural join emp where emp_job='Boilermaker' group by sample.Mobile order by mob_freq desc;



select Car, COUNT(Car) from sample natural join emp where emp_job = 'Boilermaker'
                                                      and (Car='Kia' or car='BMW') group by Car ;





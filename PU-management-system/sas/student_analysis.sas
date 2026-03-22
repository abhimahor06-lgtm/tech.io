/*
student_analysis.sas
Student Analysis Report
Poornima University Management System
Generates comprehensive statistical analysis of student data
*/

LIBNAME unidb "/path/to/database";

/*
DATA IMPORT: Import student data from MySQL
Requires ODBC connection setup to university_db
*/
PROC SQL;
    CONNECT TO ODBC (DSN="university_db" USER="root" PASSWORD="password");
    
    CREATE TABLE work.students AS
    SELECT * FROM CONNECTION TO ODBC (
        SELECT 
            id as student_id,
            first_name,
            last_name,
            enrollment_number,
            program,
            department,
            semester,
            current_cgpa as cgpa,
            status
        FROM students
    );
    
    DISCONNECT FROM ODBC;
QUIT;

/*
STEP 1: Student Demographics Summary
Provides overview of student population
*/
TITLE "STUDENT DEMOGRAPHICS SUMMARY";
PROC FREQ DATA=work.students;
    TABLES department / OUT=dept_freq;
    TABLES program / OUT=program_freq;
    TABLES semester / OUT=semester_freq;
    TABLES status / OUT=status_freq;
RUN;

/*
STEP 2: CGPA Analysis by Department
Calculates distribution and statistics
*/
TITLE "CGPA ANALYSIS BY DEPARTMENT";
PROC MEANS DATA=work.students N MEAN STD MIN MAX;
    CLASS department;
    VAR cgpa;
    OUTPUT OUT=cgpa_by_dept MEAN=avg_cgpa STD=std_cgpa;
RUN;

/*
STEP 3: Student Distribution Analysis
*/
TITLE "STUDENT DISTRIBUTION";
PROC CHART DATA=work.students;
    VBAR department / ACROSS=semester SPACE=0;
RUN;

/*
STEP 4: Performance Categories
Classify students by CGPA ranges
*/
DATA student_performance;
    SET work.students;
    
    IF cgpa >= 3.5 THEN performance_category = 'Excellent';
    ELSE IF cgpa >= 3.0 THEN performance_category = 'Very Good';
    ELSE IF cgpa >= 2.5 THEN performance_category = 'Good';
    ELSE IF cgpa >= 2.0 THEN performance_category = 'Average';
    ELSE performance_category = 'Below Average';
RUN;

PROC FREQ DATA=student_performance;
    TABLES performance_category / OUT=perf_dist;
RUN;

/*
STEP 5: Export Results
*/
PROC EXPORT DATA=cgpa_by_dept
    OUTFILE="/output/cgpa_analysis.csv"
    DBMS=CSV REPLACE;
RUN;

PROC EXPORT DATA=student_performance
    OUTFILE="/output/student_performance.csv"
    DBMS=CSV REPLACE;
RUN;

/*
STEP 6: Create Summary Report
*/
ODS RTF FILE="/output/student_analysis_report.rtf";

TITLE "POORNIMA UNIVERSITY - STUDENT ANALYSIS REPORT";

PROC PRINT DATA=work.students (OBS=50);
    VAR student_id first_name last_name enrollment_number program semester cgpa status;
RUN;

/*
Summary Statistics
*/
PROC MEANS DATA=work.students SIMPLE ALPHA=0.05;
    VAR cgpa;
    OUTPUT OUT=summary MEAN=avg_cgpa STD=std_cgpa N=total_students;
RUN;

ODS RTF CLOSE;

/*
STEP 7: Correlation Analysis
Analyze relationship between semester and CGPA
*/
PROC CORR DATA=work.students PEARSON;
    VAR semester cgpa;
RUN;

TITLE "Student Analysis Complete";

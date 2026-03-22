/*
performance_report.sas
Academic Performance Report
Poornima University Management System
Analyzes student academic performance and predicts intervention needs
*/

LIBNAME unidb "/path/to/database";

/*
DATA IMPORT: Import marks data from MySQL
*/
PROC SQL;
    CONNECT TO ODBC (DSN="university_db" USER="root" PASSWORD="password");
    
    CREATE TABLE work.marks_data AS
    SELECT * FROM CONNECTION TO ODBC (
        SELECT 
            m.student_id,
            s.enrollment_number,
            CONCAT(s.first_name, ' ', s.last_name) as student_name,
            s.department,
            s.semester,
            m.internal,
            m.midterm,
            m.final,
            m.total,
            m.grade
        FROM marks m
        JOIN students s ON m.student_id = s.id
        WHERE m.total IS NOT NULL
    );
    
    DISCONNECT FROM ODBC;
QUIT;

/*
STEP 1: Overall Performance Statistics
*/
TITLE "ACADEMIC PERFORMANCE STATISTICS";
PROC MEANS DATA=work.marks_data N MEAN STD MIN MAX;
    VAR internal midterm final total;
    OUTPUT OUT=overall_performance;
RUN;

/*
STEP 2: Performance by Department
*/
TITLE "PERFORMANCE BY DEPARTMENT";
PROC MEANS DATA=work.marks_data MEAN;
    CLASS department;
    VAR total;
    OUTPUT OUT=dept_performance MEAN=avg_total;
RUN;

/*
STEP 3: Performance by Semester
*/
TITLE "PERFORMANCE BY SEMESTER";
PROC MEANS DATA=work.marks_data MEAN;
    CLASS semester;
    VAR total;
    OUTPUT OUT=semester_performance MEAN=avg_total;
RUN;

/*
STEP 4: Grade Distribution Analysis
*/
DATA grade_distribution;
    SET work.marks_data;
    
    IF total >= 90 THEN grade_level = 'A+ (90-100)';
    ELSE IF total >= 80 THEN grade_level = 'A (80-89)';
    ELSE IF total >= 70 THEN grade_level = 'B (70-79)';
    ELSE IF total >= 60 THEN grade_level = 'C (60-69)';
    ELSE IF total >= 50 THEN grade_level = 'D (50-59)';
    ELSE grade_level = 'F (<50)';
RUN;

PROC FREQ DATA=grade_distribution;
    TABLES grade_level / OUT=grade_freq;
RUN;

TITLE "GRADE DISTRIBUTION";
PROC CHART DATA=grade_distribution;
    VBAR grade_level / DISCRETE;
RUN;

/*
STEP 5: Student-Level Performance Summary
Aggregates all marks for each student
*/
DATA student_performance;
    SET work.marks_data;
    BY student_id;
    
    RETAIN total_exams 0 sum_marks 0 sum_internal 0 sum_midterm 0 sum_final 0;
    
    IF FIRST.student_id THEN DO;
        total_exams = 0;
        sum_marks = 0;
        sum_internal = 0;
        sum_midterm = 0;
        sum_final = 0;
    END;
    
    total_exams + 1;
    sum_marks + total;
    sum_internal + internal;
    sum_midterm + midterm;
    sum_final + final;
    
    IF LAST.student_id THEN DO;
        avg_total = sum_marks / total_exams;
        avg_internal = sum_internal / total_exams;
        avg_midterm = sum_midterm / total_exams;
        avg_final = sum_final / total_exams;
        OUTPUT;
    END;
RUN;

/*
STEP 6: Classify Performance Levels
*/
DATA student_classification;
    SET student_performance;
    
    IF avg_total >= 80 THEN performance_level = 'Excellent';
    ELSE IF avg_total >= 70 THEN performance_level = 'Good';
    ELSE IF avg_total >= 60 THEN performance_level = 'Average';
    ELSE IF avg_total >= 50 THEN performance_level = 'Below Average';
    ELSE performance_level = 'Needs Intervention';
    
    /*
    Intervention flags
    */
    IF avg_total >= 75 THEN intervention_needed = 0;
    ELSE intervention_needed = 1;
    
    IF avg_final < 50 THEN exam_at_risk = 1;
    ELSE exam_at_risk = 0;
RUN;

/*
STEP 7: Identify Students Needing Intervention
*/
DATA intervention_students;
    SET student_classification;
    WHERE intervention_needed = 1 OR exam_at_risk = 1;
RUN;

TITLE "STUDENTS NEEDING ACADEMIC INTERVENTION";
PROC PRINT DATA=intervention_students;
    VAR student_name enrollment_number department semester 
        avg_total performance_level;
RUN;

/*
STEP 8: Subject Performance Analysis
Identifies problematic subjects
*/
PROC SORT DATA=work.marks_data OUT=sorted_marks;
    BY total;
RUN;

PROC MEANS DATA=work.marks_data MEAN;
    OUTPUT OUT=subject_difficulty MEAN=avg_marks;
RUN;

/*
STEP 9: Performance Trend Analysis
*/
DATA performance_trends;
    SET student_classification;
    
    IF avg_internal < avg_midterm AND avg_midterm < avg_final THEN trend = 'Improving';
    ELSE IF avg_internal > avg_midterm AND avg_midterm > avg_final THEN trend = 'Declining';
    ELSE trend = 'Consistent';
RUN;

PROC FREQ DATA=performance_trends;
    TABLES trend / OUT=trend_frequency;
RUN;

/*
STEP 10: Export Results
*/
PROC EXPORT DATA=student_classification
    OUTFILE="/output/student_performance.csv"
    DBMS=CSV REPLACE;
RUN;

PROC EXPORT DATA=intervention_students
    OUTFILE="/output/intervention_required.csv"
    DBMS=CSV REPLACE;
RUN;

PROC EXPORT DATA=grade_distribution
    OUTFILE="/output/grade_analysis.csv"
    DBMS=CSV REPLACE;
RUN;

/*
STEP 11: Generate Comprehensive Report
*/
ODS RTF FILE="/output/performance_report.rtf";

TITLE "POORNIMA UNIVERSITY - ACADEMIC PERFORMANCE REPORT";
FOOTNOTE "Generated: %SYSFUNC(TODAY(),DDMMYY10.) | Report Period: Semester Data";

PROC PRINT DATA=overall_performance;
    TITLE2 "Overall Academic Statistics";
RUN;

/*
Department Performance Comparison
*/
PROC PRINT DATA=dept_performance;
    TITLE2 "Department-Wise Average Performance";
RUN;

/*
Grade Distribution Summary
*/
PROC FREQ DATA=grade_distribution;
    TABLES grade_level;
    TITLE2 "Grade Distribution Summary";
RUN;

/*
Intervention List
*/
PROC PRINT DATA=intervention_students;
    TITLE2 "Students Recommended for Academic Support";
    VAR student_name enrollment_number department avg_total performance_level;
RUN;

/*
Performance Trends
*/
PROC FREQ DATA=performance_trends;
    TABLES trend;
    TITLE2 "Student Performance Trends";
RUN;

/*
High Achievers List
*/
DATA high_achievers;
    SET student_classification;
    WHERE performance_level = 'Excellent' AND avg_total >= 85;
RUN;

PROC PRINT DATA=high_achievers;
    TITLE2 "High Achievers (Score >= 85)";
    VAR student_name enrollment_number department avg_total;
RUN;

ODS RTF CLOSE;

/*
STEP 12: Correlation Analysis
Analyze relationship between components
*/
PROC CORR DATA=work.marks_data PEARSON;
    VAR internal midterm final;
    TITLE "Correlation between Exam Components";
RUN;

/*
STEP 13: Generate Summary Statistics
*/
PROC MEANS DATA=student_performance SIMPLE;
    VAR avg_total avg_internal avg_midterm avg_final;
    TITLE "Performance Component Analysis";
RUN;

TITLE "Performance Analysis Complete";

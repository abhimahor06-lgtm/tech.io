/*
attendance_analysis.sas
Attendance Analysis Report
Poornima University Management System
Analyzes attendance patterns and generates alerts
*/

LIBNAME unidb "/path/to/database";

/*
DATA IMPORT: Import attendance data from MySQL
*/
PROC SQL;
    CONNECT TO ODBC (DSN="university_db" USER="root" PASSWORD="password");
    
    CREATE TABLE work.attendance AS
    SELECT * FROM CONNECTION TO ODBC (
        SELECT 
            a.student_id,
            s.enrollment_number,
            CONCAT(s.first_name, ' ', s.last_name) as student_name,
            s.semester,
            s.department,
            a.subject_id,
            a.date,
            a.status,
            CASE WHEN a.status = 'present' THEN 1 ELSE 0 END as present
        FROM attendance a
        JOIN students s ON a.student_id = s.id
        ORDER BY a.date DESC
    );
    
    DISCONNECT FROM ODBC;
QUIT;

/*
STEP 1: Overall Attendance Statistics
*/
TITLE "ATTENDANCE STATISTICS OVERVIEW";
PROC MEANS DATA=work.attendance N MEAN;
    VAR present;
    OUTPUT OUT=overall_stats MEAN=avg_attendance;
RUN;

/*
STEP 2: Attendance by Department
*/
TITLE "ATTENDANCE BY DEPARTMENT";
PROC MEANS DATA=work.attendance MEAN;
    CLASS department;
    VAR present;
    OUTPUT OUT=dept_attendance MEAN=avg_attendance;
RUN;

/*
STEP 3: Attendance by Semester
*/
TITLE "ATTENDANCE BY SEMESTER";
PROC MEANS DATA=work.attendance MEAN;
    CLASS semester;
    VAR present;
    OUTPUT OUT=semester_attendance MEAN=avg_attendance;
RUN;

/*
STEP 4: Student-Level Attendance Calculation
Calculates attendance percentage per student
*/
DATA student_attendance;
    SET work.attendance;
    BY student_id;
    
    RETAIN total_classes 0 days_present 0;
    
    IF FIRST.student_id THEN DO;
        total_classes = 0;
        days_present = 0;
    END;
    
    total_classes + 1;
    days_present + present;
    
    IF LAST.student_id THEN DO;
        attendance_percentage = (days_present / total_classes) * 100;
        OUTPUT;
    END;
RUN;

/*
STEP 5: Classify Attendance Status
*/
DATA attendance_status;
    SET student_attendance;
    
    IF attendance_percentage >= 75 THEN attendance_status = 'Excellent';
    ELSE IF attendance_percentage >= 60 THEN attendance_status = 'Good';
    ELSE IF attendance_percentage >= 50 THEN attendance_status = 'Fair';
    ELSE IF attendance_percentage >= 30 THEN attendance_status = 'Poor';
    ELSE attendance_status = 'Critical';
    
    /*
    Flag students with critical attendance
    */
    IF attendance_percentage < 50 THEN alert_flag = 1;
    ELSE alert_flag = 0;
RUN;

/*
STEP 6: Generate Alerts
Students with attendance < 50%
*/
DATA at_risk_students;
    SET attendance_status;
    WHERE alert_flag = 1;
RUN;

TITLE "AT-RISK STUDENTS (Attendance < 50%)";
PROC PRINT DATA=at_risk_students;
    VAR student_name enrollment_number semester department 
        attendance_percentage attendance_status;
RUN;

/*
STEP 7: Frequency Analysis
*/
TITLE "ATTENDANCE STATUS DISTRIBUTION";
PROC FREQ DATA=attendance_status;
    TABLES attendance_status / OUT=status_frequency;
RUN;

/*
STEP 8: Trend Analysis - Monthly Attendance
*/
DATA monthly_attendance;
    SET work.attendance;
    
    IF present = 1 THEN daily_attendance = 1;
    ELSE daily_attendance = 0;
    
    month = MONTH(date);
    year = YEAR(date);
RUN;

PROC MEANS DATA=monthly_attendance MEAN;
    CLASS year month;
    VAR daily_attendance;
    OUTPUT OUT=monthly_trend MEAN=monthly_attendance_rate;
RUN;

/*
STEP 9: Subject-Specific Attendance
*/
PROC MEANS DATA=work.attendance MEAN;
    CLASS subject_id;
    VAR present;
    OUTPUT OUT=subject_attendance MEAN=avg_attendance;
RUN;

/*
STEP 10: Export Analysis Results
*/
PROC EXPORT DATA=attendance_status
    OUTFILE="/output/attendance_analysis.csv"
    DBMS=CSV REPLACE;
RUN;

PROC EXPORT DATA=at_risk_students
    OUTFILE="/output/at_risk_students.csv"
    DBMS=CSV REPLACE;
RUN;

PROC EXPORT DATA=monthly_trend
    OUTFILE="/output/attendance_trend.csv"
    DBMS=CSV REPLACE;
RUN;

/*
STEP 11: Generate Comprehensive Report
*/
ODS RTF FILE="/output/attendance_report.rtf";

TITLE "POORNIMA UNIVERSITY - ATTENDANCE ANALYSIS REPORT";
FOOTNOTE "Generated: %SYSFUNC(TODAY(),DDMMYY.)";

/*
Executive Summary
*/
PROC PRINT DATA=overall_stats;
    TITLE2 "Executive Summary - Overall Attendance";
RUN;

/*
Department Analysis
*/
PROC PRINT DATA=dept_attendance;
    TITLE2 "Attendance by Department";
RUN;

/*
At-Risk Students Detail
*/
PROC PRINT DATA=at_risk_students;
    TITLE2 "Students with Critical Attendance Levels";
    VAR student_name enrollment_number semester attendance_percentage;
RUN;

/*
Trend Chart
*/
PROC GCHART DATA=monthly_trend;
    VBAR year * month / SUMVAR=monthly_attendance_rate TYPE=SUM;
    TITLE2 "Monthly Attendance Trend";
RUN;

ODS RTF CLOSE;

TITLE "Attendance Analysis Complete";

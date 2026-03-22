"""
predictor.py
AI/ML Module for Student Performance Predictions
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
import pickle
import os
from db_connect import db


# ==============================
# PERFORMANCE PREDICTOR
# ==============================
class PerformancePredictor:

    def __init__(self):
        self.model = None
        self.model_path = 'models/performance_model.pkl'

    def train(self):
        try:
            query = """
            SELECT 
                m.student_id,
                AVG(m.internal) AS avg_internal,
                AVG(m.midterm) AS avg_midterm,
                AVG(m.total) AS avg_total,
                SUM(CASE WHEN a.status='present' THEN 1 ELSE 0 END) AS attended_classes,
                COUNT(DISTINCT a.date) AS total_classes
            FROM marks m
            LEFT JOIN attendance a ON m.student_id = a.student_id
            WHERE m.total IS NOT NULL
            GROUP BY m.student_id
            """

            data = db.execute_query(query)

            if not data or len(data) < 10:
                print("✗ Insufficient data for training")
                return False

            df = pd.DataFrame(data).fillna(0)

            X = df[['avg_internal', 'avg_midterm',
                    'attended_classes', 'total_classes']]
            y = df['avg_total']

            self.model = RandomForestRegressor(
                n_estimators=100,
                random_state=42
            )
            self.model.fit(X, y)

            os.makedirs('models', exist_ok=True)
            with open(self.model_path, 'wb') as f:
                pickle.dump(self.model, f)

            return True

        except Exception as e:
            print(f"Error training performance model: {e}")
            return False

    def load_model(self):
        if os.path.exists(self.model_path):
            with open(self.model_path, 'rb') as f:
                self.model = pickle.load(f)

    def predict(self, internal, midterm, attended, total_classes):
        try:
            if self.model is None:
                self.load_model()

            if self.model is None:
                if not self.train():
                    return None

            features = np.array([[
                float(internal or 0),
                float(midterm or 0),
                float(attended or 0),
                float(total_classes or 1)
            ]])

            prediction = self.model.predict(features)[0]
            return round(max(0, min(100, prediction)), 2)

        except Exception as e:
            print(f"✗ Performance prediction error: {e}")
            return None


# ==============================
# DROPOUT PREDICTOR
# ==============================
class DropoutPredictor:

    def __init__(self):
        self.model = None
        self.model_path = 'models/dropout_model.pkl'

    def train(self):
        try:
            query = """
            SELECT 
                s.id,
                CASE WHEN s.status='suspended' THEN 1 ELSE 0 END AS dropout,
                COALESCE(AVG(CASE 
                    WHEN a.status='present' THEN 100
                    WHEN a.status='absent' THEN 0
                    ELSE 50 END),75) AS avg_attendance,
                COALESCE(AVG(m.total),60) AS avg_marks,
                COUNT(DISTINCT a.date) AS class_count
            FROM students s
            LEFT JOIN attendance a ON s.id = a.student_id
            LEFT JOIN marks m ON s.id = m.student_id
            GROUP BY s.id
            HAVING class_count > 5
            """

            data = db.execute_query(query)

            if not data or len(data) < 20:
                print("✗ Insufficient data for dropout training")
                return False

            df = pd.DataFrame(data).fillna(0)

            X = df[['avg_attendance', 'avg_marks', 'class_count']]
            y = df['dropout']

            if len(set(y)) < 2:
                print("✗ Dropout training needs at least 2 classes")
                return False

            self.model = RandomForestClassifier(
                n_estimators=100,
                random_state=42
            )
            self.model.fit(X, y)

            os.makedirs('models', exist_ok=True)
            with open(self.model_path, 'wb') as f:
                pickle.dump(self.model, f)

            return True

        except Exception as e:
            print(f"Error training dropout model: {e}")
            return False

    def load_model(self):
        if os.path.exists(self.model_path):
            with open(self.model_path, 'rb') as f:
                self.model = pickle.load(f)

    def predict(self, avg_attendance, avg_marks, class_count):
        try:
            if self.model is None:
                self.load_model()

            if self.model is None:
                if not self.train():
                    return {
                        'risk_percentage': 50,
                        'risk_level': 'Unknown'
                    }

            features = np.array([[
                float(avg_attendance or 75),
                float(avg_marks or 60),
                float(class_count or 0)
            ]])

            probability = self.model.predict_proba(features)[0][1]

            risk_level = (
                "High" if probability > 0.7
                else "Medium" if probability > 0.4
                else "Low"
            )

            return {
                'risk_percentage': round(probability * 100, 2),
                'risk_level': risk_level
            }

        except Exception as e:
            print(f"✗ Dropout prediction error: {e}")
            return {
                'risk_percentage': 50,
                'risk_level': 'Error'
            }


# ==============================
# ATTENDANCE ANALYZER
# ==============================
class AttendanceAnalyzer:

    @staticmethod
    def detect_anomalies(student_id):
        try:
            query = """
            SELECT 
                DATE(date) as attendance_date,
                COUNT(*) as classes,
                SUM(CASE WHEN status='present' THEN 1 ELSE 0 END) as present
            FROM attendance
            WHERE student_id = %s
            GROUP BY DATE(date)
            ORDER BY attendance_date DESC
            LIMIT 30
            """

            records = db.execute_query(query, (student_id,))

            if not records:
                return {'anomalies': [], 'alert': None, 'avgAttendance': 0}

            df = pd.DataFrame(records).fillna(0)

            df['attendance_rate'] = (
                df['present'].astype(float) /
                df['classes'].replace(0, 1).astype(float)
            ) * 100

            anomalies = df[df['attendance_rate'] < 50].to_dict('records')

            alert = None
            if len(anomalies) > 5:
                alert = "Critical: Frequent low attendance"
            elif len(anomalies) > 0:
                alert = "Warning: Irregular attendance"

            return {
                'anomalies': anomalies,
                'alert': alert,
                'avgAttendance': round(df['attendance_rate'].mean(), 2)
            }

        except Exception as e:
            print(f"Attendance analysis error: {e}")
            return {'anomalies': [], 'alert': None, 'avgAttendance': 0}
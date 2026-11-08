
from flask import Flask, render_template, request, redirect, url_for, session, send_file
import sqlite3
from io import BytesIO
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Border, Side, Alignment
from openpyxl.worksheet.table import Table, TableStyleInfo
from openpyxl.utils import get_column_letter

app = Flask(__name__)
print("STATIC FOLDER:", app.static_folder)
app.secret_key = "skillgap_demo_secret_2026"

# ADMIN LOGIN DETAILS
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "SkillGap@123"


# DATABASE CONNECTION
def get_db_connection():
    conn = sqlite3.connect("skillgap.db")
    conn.row_factory = sqlite3.Row
    return conn


# CREATE DATABASE
def create_database():
    conn = get_db_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_name TEXT,
            education TEXT,
            skills TEXT,
            languages TEXT,
            career TEXT,
            experience TEXT,
            skill_gap INTEGER,
            readiness_level TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


# CAREER SKILLS
CAREER_SKILLS = {
    "web development": [
        "HTML", "CSS", "JavaScript", "React",
        "Python", "SQL", "Git"
    ],

    "data science": [
        "Python", "SQL", "Statistics",
        "Machine Learning", "Pandas",
        "NumPy", "Data Visualization"
    ],

    "python developer": [
        "Python", "SQL", "Git", "Django",
        "Flask", "OOP", "Data Structures"
    ],

    "software developer": [
        "Python", "Java", "SQL", "Git",
        "Data Structures", "Algorithms", "OOP"
    ]
}


# SKILL DESCRIPTIONS
SKILL_DESCRIPTIONS = {
    "HTML": "Learn to create the structure of web pages.",
    "CSS": "Learn to design websites using colors and layouts.",
    "JavaScript": "Learn to make websites interactive.",
    "React": "Learn to build modern user interfaces.",
    "Python": "Learn Python programming fundamentals.",
    "SQL": "Learn to manage database information.",
    "Git": "Learn version control and project management.",
    "Statistics": "Learn data analysis and statistics.",
    "Machine Learning": "Learn algorithms that identify patterns.",
    "Pandas": "Learn to analyze and manipulate data.",
    "NumPy": "Learn numerical computing with Python.",
    "Data Visualization": "Learn to present data using charts.",
    "Django": "Learn web development using Django.",
    "Flask": "Learn web development using Flask.",
    "OOP": "Learn object-oriented programming.",
    "Data Structures": "Learn how to organize data.",
    "Algorithms": "Learn problem-solving techniques.",
    "Java": "Learn Java programming fundamentals."
}


# HOME PAGE
@app.route("/")
def home():
    return render_template("index.html")


# ASSESSMENT PAGE
@app.route("/assessment")
def assessment():
    return render_template("assessment.html")


# STUDENT SKILL GAP ANALYSIS
@app.route("/predict", methods=["POST"])
def predict():

    student_name = request.form["student_name"]
    education = request.form["education"]
    skills = request.form["skills"]
    languages = request.form["languages"]
    career = request.form["career"]
    experience = request.form["experience"]

    career_key = career.strip().lower()

    required_skills = CAREER_SKILLS.get(
        career_key,
        ["HTML", "CSS", "JavaScript", "Python", "SQL", "Git"]
    )

    student_skills = (skills + ", " + languages).lower()

    existing_skills = [
        skill for skill in required_skills
        if skill.lower() in student_skills
    ]

    missing_skills = [
        skill for skill in required_skills
        if skill.lower() not in student_skills
    ]

    skill_gap = round(
        (len(missing_skills) / len(required_skills)) * 100
    )

    learning_roadmap = []

    for skill in missing_skills:
        learning_roadmap.append({
            "skill": skill,
            "description": SKILL_DESCRIPTIONS.get(
                skill,
                "Learn the fundamentals of " + skill
            )
        })

    if skill_gap <= 25:
        readiness_level = "Job Ready"
        readiness_message = "Excellent! You have matched most required skills."

    elif skill_gap <= 60:
        readiness_level = "Intermediate"
        readiness_message = "Good progress! Improve your missing skills."

    else:
        readiness_level = "Beginner"
        readiness_message = "Keep learning and follow your roadmap."

    conn = get_db_connection()

    conn.execute("""
        INSERT INTO assessments
        (student_name, education, skills, languages,
         career, experience, skill_gap, readiness_level)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        student_name,
        education,
        skills,
        languages,
        career,
        experience,
        skill_gap,
        readiness_level
    ))

    conn.commit()
    conn.close()

    return render_template(
        "result.html",
        student_name=student_name,
        education=education,
        skills=skills,
        languages=languages,
        career=career,
        experience=experience,
        existing_skills=existing_skills,
        missing_skills=missing_skills,
        skill_gap=skill_gap,
        learning_roadmap=learning_roadmap,
        readiness_level=readiness_level,
        readiness_message=readiness_message
    )


# ADMIN LOGIN
@app.route("/login", methods=["GET", "POST"])
def login():

    error = None

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            return redirect(url_for("admin"))

        else:
            error = "Invalid username or password!"

    return render_template("login.html", error=error)


# ADMIN DASHBOARD WITH SEARCH
# # STUDENT DETAILED REPORT
@app.route("/student_report/<int:student_id>")
def student_report(student_id):

    if not session.get("admin_logged_in"):
        return redirect(url_for("login"))

    conn = get_db_connection()

    student = conn.execute(
        "SELECT * FROM assessments WHERE id = ?",
        (student_id,)
    ).fetchone()

    conn.close()

    if student is None:
        return "Student not found", 404

    career_key = student["career"].strip().lower()

    required_skills = CAREER_SKILLS.get(
        career_key,
        ["HTML", "CSS", "JavaScript", "Python", "SQL", "Git"]
    )

    student_skills = (
        (student["skills"] or "") + ", " +
        (student["languages"] or "")
    ).lower()

    existing_skills = [
        skill for skill in required_skills
        if skill.lower() in student_skills
    ]

    missing_skills = [
        skill for skill in required_skills
        if skill.lower() not in student_skills
    ]

    learning_roadmap = [
        {
            "skill": skill,
            "description": SKILL_DESCRIPTIONS.get(
                skill,
                "Learn the fundamentals of " + skill
            )
        }
        for skill in missing_skills
    ]

    return render_template(
        "student_report.html",
        student=student,
        existing_skills=existing_skills,
        missing_skills=missing_skills,
        learning_roadmap=learning_roadmap
    )

@app.route("/admin")
def admin():

    if not session.get("admin_logged_in"):
        return redirect(url_for("login"))

    search_query = request.args.get("search", "").strip()

    conn = get_db_connection()

    students = conn.execute("""
        SELECT * FROM assessments
        WHERE student_name LIKE ? OR career LIKE ?
        ORDER BY id DESC
    """, (
        "%" + search_query + "%",
        "%" + search_query + "%"
    )).fetchall()

    conn.close()

    return render_template(
        "admin.html",
        students=students,
        search_query=search_query
    )


# PROFESSIONAL EXCEL REPORT DOWNLOAD
@app.route("/download_excel")
def download_excel():

    if not session.get("admin_logged_in"):
        return redirect(url_for("login"))

    conn = get_db_connection()

    students = conn.execute("""
        SELECT * FROM assessments
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Student Records"

    headers = [
        "ID",
        "Student Name",
        "Education",
        "Technical Skills",
        "Programming Languages",
        "Dream Career",
        "Experience",
        "Skill Gap",
        "Readiness",
        "Date"
    ]

    # ADD HEADINGS
    sheet.append(headers)

    # HEADING STYLE
    header_fill = PatternFill(
        fill_type="solid",
        fgColor="4338CA"
    )

    header_font = Font(
        bold=True,
        color="FFFFFF",
        size=11
    )

    for cell in sheet[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(
            horizontal="center",
            vertical="center"
        )

    # ADD STUDENT DATA
    for student in students:

        sheet.append([
            student["id"],
            student["student_name"],
            student["education"],
            student["skills"],
            student["languages"],
            student["career"],
            student["experience"],
            str(student["skill_gap"]) + "%",
            student["readiness_level"],
            student["created_at"]
        ])

    # FORMAT DATA CELLS
    thin_border = Border(
        left=Side(style="thin", color="D1D5DB"),
        right=Side(style="thin", color="D1D5DB"),
        top=Side(style="thin", color="D1D5DB"),
        bottom=Side(style="thin", color="D1D5DB")
    )

    for row in sheet.iter_rows(
        min_row=2,
        max_row=sheet.max_row
    ):
        for cell in row:
            cell.border = thin_border
            cell.alignment = Alignment(
                horizontal="center",
                vertical="center"
            )

    # CREATE EXCEL TABLE ONLY WHEN RECORDS EXIST
    if students:

        table = Table(
            displayName="StudentRecords",
            ref=f"A1:J{sheet.max_row}"
        )

        style = TableStyleInfo(
            name="TableStyleMedium2",
            showFirstColumn=False,
            showLastColumn=False,
            showRowStripes=True,
            showColumnStripes=False
        )

        table.tableStyleInfo = style
        sheet.add_table(table)

    # AUTOMATIC COLUMN WIDTH
    for column in sheet.columns:

        max_length = 0
        column_letter = get_column_letter(column[0].column)

        for cell in column:
            if cell.value is not None:
                max_length = max(
                    max_length,
                    len(str(cell.value))
                )

        sheet.column_dimensions[column_letter].width = min(
            max_length + 4,
            35
        )

    # ROW HEIGHT
    sheet.row_dimensions[1].height = 30

    for row_number in range(2, sheet.max_row + 1):
        sheet.row_dimensions[row_number].height = 23

    # KEEP HEADINGS VISIBLE
    sheet.freeze_panes = "A2"

    # REMOVE GRIDLINES
    sheet.sheet_view.showGridLines = False

    # SAVE EXCEL FILE IN MEMORY
    output = BytesIO()
    workbook.save(output)
    output.seek(0)

    return send_file(
        output,
        as_attachment=True,
        download_name="SkillGap_Student_Records.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


# ADMIN LOGOUT
@app.route("/logout")
def logout():

    session.pop("admin_logged_in", None)

    return redirect(url_for("login"))


# CREATE DATABASE WHEN APP STARTS
create_database()

# RUN APPLICATION
if __name__ == "__main__":
    app.run(debug=True)

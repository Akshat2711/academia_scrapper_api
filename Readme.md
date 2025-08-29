# Academia Student Data Scraper

Scrapes student data from SRM Academia .

## Setup
1. Install dependencies:
```bash
pip install -r requirements.txt
playwright install




2. Create a .env file with your SRM credentials (see sample_env):
    SRM_ID=your_srm_id
    SRM_PASS=your_srm_pass


3. Run:
    python academia.py


4. Notes:
    requirements.txt has all required packages.

    .env keeps your SRM credentials safe (do not commit).

    For educational use only.


5. Sample Output:
```
    ==================================================
    COMPLETE STUDENT DATA
    ==================================================
    {
    "student_info": {
        "registration_number": "RA2311056010161",
        "name": "AKSHAT SRIVASTAVA",
        "program": "B.Tech",
        "department": "Computer Science and Engineering",
        "specialization": "CS Data Science",
        "semester": "5",
        "feedback_status": ":",
        "photo_url": "https://creatorexport.zoho.com/srm_university/academia-academic-services/Photo_Upload_Student_Report/Your_Photo/image/1704701740893_d073b4f1-7b8d-4522-a665-8ccdd124072c_Original.jpeg",
        "enrollment_status": "true",
        "enrollment_date": "21-Jul-25"
    },
    "attendance": {
        "courses": {
        "21CSC302JRegular": {
            "course_title": "Computer Networks",
            "category": "Practical",
            "faculty_name": "Dr. Arthy M (103045)",
            "slot": "LAB",
            "room_no": "TP2CLS414",
            "hours_conducted": 12,
            "hours_absent": 0,
            "attendance_percentage": 100.0
        },
        "21CSE216PRegular": {
            "course_title": "Linux and Container Technologies",
            "category": "Theory",
            "faculty_name": "Dr.M.Vimala Devi (102722)",
            "slot": "B",
            "room_no": "TP 202",
            "hours_conducted": 18,
            "hours_absent": 0,
            "attendance_percentage": 100.0
        },
        "21MAB302TRegular": {
            "course_title": "Discrete Mathematics",
            "category": "Theory",
            "faculty_name": "Dr. Abhishek Banerjee (103098)",
            "slot": "C",
            "room_no": "TP 1304",
            "hours_conducted": 22,
            "hours_absent": 1,
            "attendance_percentage": 95.45
        },
        "21CSC301TRegular": {
            "course_title": "Formal Language and Automata",
            "category": "Theory",
            "faculty_name": "Ms.K.Sornalakshmi (101094)",
            "slot": "D",
            "room_no": "TP 1304",
            "hours_conducted": 17,
            "hours_absent": 0,
            "attendance_percentage": 100.0
        },
        "21CSC307PRegular": {
            "course_title": "Machine Learning for Data Analytics",
            "category": "Theory",
            "faculty_name": "Dr D Hemavathi (100390)",
            "slot": "F",
            "room_no": "TP 1304",
            "hours_conducted": 17,
            "hours_absent": 1,
            "attendance_percentage": 94.12
        },
        "21MEO112TRegular": {
            "course_title": "Renewable Energy Sources and Application",
            "category": "Theory",
            "faculty_name": "Dr.D.Premnath (100763)",
            "slot": "G",
            "room_no": "B501",
            "hours_conducted": 18,
            "hours_absent": 1,
            "attendance_percentage": 94.44
        },
        "21GNP301LRegular": {
            "course_title": "Community Connect",
            "category": "Practical",
            "faculty_name": "Dr.S.Praveenkumar (103176)",
            "slot": "LAB",
            "room_no": "",
            "hours_conducted": 10,
            "hours_absent": 0,
            "attendance_percentage": 100.0
        },
        "21LEM301TRegular": {
            "course_title": "Indian Art Form",
            "category": "Practical",
            "faculty_name": "Dr.S.Praveenkumar (103176)",
            "slot": "LAB",
            "room_no": "",
            "hours_conducted": 10,
            "hours_absent": 0,
            "attendance_percentage": 100.0
        }
        },
        "overall_attendance": 96.48,
        "total_hours_conducted": 142,
        "total_hours_absent": 5
    },
    "marks": {
        "21MAB302T": {
        "course_type": "Theory",
        "tests": [
            {
            "test_name": "FT-I",
            "obtained_marks": 5.0,
            "max_marks": 5.0,
            "percentage": 100.0
            }
        ]
        },
        "21CSC301T": {
        "course_type": "Theory",
        "tests": [
            {
            "test_name": "FT-I",
            "obtained_marks": 5.0,
            "max_marks": 5.0,
            "percentage": 100.0
            }
        ]
        },
        "21CSC302J": {
        "course_type": "Practical",
        "tests": []
        },
        "21CSC307P": {
        "course_type": "Theory",
        "tests": []
        },
        "21GNP301L": {
        "course_type": "Practical",
        "tests": []
        },
        "21LEM301T": {
        "course_type": "Practical",
        "tests": []
        },
        "21CSE216P": {
        "course_type": "Theory",
        "tests": []
        },
        "21MEO112T": {
        "course_type": "Theory",
        "tests": [
            {
            "test_name": "FT-I",
            "obtained_marks": 3.4,
            "max_marks": 5.0,
            "percentage": 68.0
            }
        ]
        }
    },
    "summary": {}
    }

```
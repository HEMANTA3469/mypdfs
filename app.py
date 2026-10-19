# ==========================================================
# EDUCATION PDF SELL PROJECT
# app.py
# ==========================================================
import os
from datetime import datetime
from functools import wraps

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    send_from_directory,
    send_file
)

from werkzeug.utils import secure_filename

from database import (
    create_tables,

    # Users
    get_user_by_email,
    check_user_password,
    create_user,

    # PDFs
    get_all_pdfs,
    get_pdf,
    get_all_pdfs_admin,
    add_pdf,
    update_pdf,
    delete_pdf,

    # Purchases
    is_pdf_purchased,
    get_user_purchases,
    create_order,

    # Statistics
    get_statistics,

    # Database
    get_db,

    # Admissions
    add_admission,
    get_all_admissions,
    get_admission,
    update_admission_payment,
    delete_admission
)

# ==========================================================
# FLASK APP SETUP
# ==========================================================

app = Flask(__name__)

app.secret_key = "education_pdf_secret_2026"

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

UPLOAD_FOLDER = os.path.join(
    BASE_DIR,
    "static",
    "uploads",
    "pdfs"
)

THUMBNAIL_FOLDER = os.path.join(
    BASE_DIR,
    "static",
    "thumbnails"
)

RECEIPT_FOLDER = os.path.join(
    BASE_DIR,
    "static",
    "receipts"
)

STUDENT_PHOTO_FOLDER = os.path.join(
    BASE_DIR,
    "static",
    "uploads",
    "photos"
)

LOGO_FOLDER = os.path.join(
    BASE_DIR,
    "static",
    "logo"
)

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(THUMBNAIL_FOLDER, exist_ok=True)
os.makedirs(RECEIPT_FOLDER, exist_ok=True)
os.makedirs(STUDENT_PHOTO_FOLDER, exist_ok=True)
os.makedirs(LOGO_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["THUMBNAIL_FOLDER"] = THUMBNAIL_FOLDER
app.config["RECEIPT_FOLDER"] = RECEIPT_FOLDER
app.config["STUDENT_PHOTO_FOLDER"] = STUDENT_PHOTO_FOLDER
app.config["LOGO_FOLDER"] = LOGO_FOLDER

ALLOWED_PDF_EXTENSIONS = {"pdf"}

ALLOWED_IMAGE_EXTENSIONS = {
    "jpg",
    "jpeg",
    "png",
    "webp"
}

# Database
create_tables()

# ==========================================================
# HELPER FUNCTIONS
# ==========================================================

def allowed_file(filename, extensions):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in extensions
    )


def login_required(view):

    @wraps(view)
    def wrapped_view(*args, **kwargs):

        if "user_id" not in session:

            flash(
                "Please login first.",
                "warning"
            )

            return redirect(
                url_for("login")
            )

        return view(*args, **kwargs)

    return wrapped_view


def admin_required(view):

    @wraps(view)
    def wrapped_view(*args, **kwargs):

        if "user_id" not in session:

            flash(
                "Admin login required.",
                "warning"
            )

            return redirect(
                url_for("admin_login")
            )

        if session.get("role") != "admin":

            flash(
                "Admin access required.",
                "danger"
            )

            return redirect(
                url_for("index")
            )

        return view(*args, **kwargs)

    return wrapped_view


# ==========================================================
# PUBLIC HOME
# ==========================================================

@app.route("/")
def index():

    pdfs = get_all_pdfs()

    return render_template(
        "index.html",
        pdfs=pdfs
    )


# ==========================================================
# REGISTER
# ==========================================================

@app.route(
    "/register",
    methods=["GET", "POST"]
)
def register():

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        mobile = request.form.get(
            "mobile",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        confirm_password = request.form.get(
            "confirm_password",
            ""
        )

        # -----------------------------
        # VALIDATION
        # -----------------------------

        if not name or not email or not password:

            flash(
                "Please fill all required fields.",
                "danger"
            )

            return redirect(
                url_for("register")
            )

        if password != confirm_password:

            flash(
                "Passwords do not match.",
                "danger"
            )

            return redirect(
                url_for("register")
            )

        if get_user_by_email(email):

            flash(
                "Email already registered.",
                "warning"
            )

            return redirect(
                url_for("login")
            )

        # -----------------------------
        # CREATE USER
        # -----------------------------

        user_id = create_user(
            name,
            email,
            mobile,
            password
        )

        if not user_id:

            flash(
                "Registration failed.",
                "danger"
            )

            return redirect(
                url_for("register")
            )

        flash(
            "Registration successful. Please login.",
            "success"
        )

        return redirect(
            url_for("login")
        )

    return render_template(
        "register.html"
    )


# ==========================================================
# LOGIN
# ==========================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        user = get_user_by_email(email)

        if (
            not user
            or not check_user_password(
                user,
                password
            )
        ):

            flash(
                "Invalid email or password.",
                "danger"
            )

            return redirect(
                url_for("login")
            )

        session.clear()

        session["user_id"] = user["id"]
        session["name"] = user["name"]
        session["email"] = user["email"]
        session["role"] = user["role"]

        flash(
            "Login successful.",
            "success"
        )

        if user["role"] == "admin":

            return redirect(
                url_for("admin_dashboard")
            )

        return redirect(
            url_for("index")
        )

    return render_template(
        "login.html"
    )


# ==========================================================
# LOGOUT
# ==========================================================

@app.route("/logout")
def logout():

    session.clear()

    flash(
        "You have been logged out.",
        "success"
    )

    return redirect(
        url_for("index")
    )


# ==========================================================
# PDF DETAIL
# ==========================================================

@app.route("/pdf/<int:pdf_id>")
def pdf_detail(pdf_id):

    pdf = get_pdf(pdf_id)

    if not pdf:

        flash(
            "PDF not found.",
            "danger"
        )

        return redirect(
            url_for("index")
        )

    purchased = False

    if "user_id" in session:

        purchased = is_pdf_purchased(
            session["user_id"],
            pdf_id
        )

    return render_template(
        "pdf_detail.html",
        pdf=pdf,
        purchased=purchased
    )


# ==========================================================
# BUY PDF
# ==========================================================

@app.route(
    "/buy/<int:pdf_id>",
    methods=["GET", "POST"]
)
@login_required
def buy_pdf(pdf_id):

    pdf = get_pdf(pdf_id)

    if not pdf:

        flash(
            "PDF not found.",
            "danger"
        )

        return redirect(
            url_for("index")
        )

    user_id = session["user_id"]

    if is_pdf_purchased(
        user_id,
        pdf_id
    ):

        flash(
            "You already purchased this PDF.",
            "info"
        )

        return redirect(
            url_for("my_pdfs")
        )

    if request.method == "POST":

        order_id = create_order(
            user_id=user_id,
            pdf_id=pdf_id,
            amount=pdf["price"],
            payment_method="demo"
        )

        if order_id:

            flash(
                "Purchase successful!",
                "success"
            )

            return redirect(
                url_for("my_pdfs")
            )

        flash(
            "Purchase failed.",
            "danger"
        )

        return redirect(
            url_for(
                "pdf_detail",
                pdf_id=pdf_id
            )
        )

    return render_template(
        "checkout.html",
        pdf=pdf
    )


# ==========================================================
# MY PDFs
# ==========================================================

@app.route("/my-pdfs")
@login_required
def my_pdfs():

    purchases = get_user_purchases(
        session["user_id"]
    )

    return render_template(
        "my_pdfs.html",
        purchases=purchases
    )


# ==========================================================
# DOWNLOAD PDF
# ==========================================================

@app.route("/download/<int:pdf_id>")
@login_required
def download_pdf(pdf_id):

    user_id = session["user_id"]

    if not is_pdf_purchased(
        user_id,
        pdf_id
    ):

        flash(
            "Please purchase this PDF first.",
            "danger"
        )

        return redirect(
            url_for(
                "pdf_detail",
                pdf_id=pdf_id
            )
        )

    pdf = get_pdf(pdf_id)

    if not pdf:

        flash(
            "PDF not found.",
            "danger"
        )

        return redirect(
            url_for("index")
        )

    filename = pdf["pdf_file"]

    filepath = os.path.join(
        app.config["UPLOAD_FOLDER"],
        filename
    )

    if not os.path.exists(filepath):

        flash(
            "PDF file is missing.",
            "danger"
        )

        return redirect(
            url_for("my_pdfs")
        )

    return send_from_directory(
        app.config["UPLOAD_FOLDER"],
        filename,
        as_attachment=True
    )

# ==========================================================
# ADMISSION FORM
# SUBMIT -> SAVE -> PDF -> AUTOMATIC DOWNLOAD
# ==========================================================

@app.route(
    "/admission",
    methods=["GET", "POST"]
)
def admission():

    if request.method == "POST":

        # ------------------------------------------
        # ADMISSION FEE
        # ------------------------------------------

        try:

            admission_fee = float(
                request.form.get(
                    "admission_fee",
                    "0"
                ) or 0
            )

        except (ValueError, TypeError):

            admission_fee = 0


        # ------------------------------------------
        # PHOTO UPLOAD HANDLING
        # ------------------------------------------

        photo_filename = ""
        photo_file = request.files.get("photo")

        if photo_file and photo_file.filename:
            if allowed_file(photo_file.filename, ALLOWED_IMAGE_EXTENSIONS):
                photo_filename = secure_filename(photo_file.filename)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_")
                photo_filename = timestamp + photo_filename
                
                photo_file.save(
                    os.path.join(
                        app.config["STUDENT_PHOTO_FOLDER"],
                        photo_filename
                    )
                )


        # ------------------------------------------
        # FORM DATA
        # ------------------------------------------

        data = {

            "student_name":
                request.form.get(
                    "student_name",
                    ""
                ).strip(),

            "father_name":
                request.form.get(
                    "father_name",
                    ""
                ).strip(),

            "mother_name":
                request.form.get(
                    "mother_name",
                    ""
                ).strip(),

            "dob":
                request.form.get(
                    "dob",
                    ""
                ),

            "gender":
                request.form.get(
                    "gender",
                    ""
                ),

            "mobile":
                request.form.get(
                    "mobile",
                    ""
                ).strip(),

            "course":
                request.form.get(
                    "course",
                    ""
                ),

            "batch":
                request.form.get(
                    "batch",
                    ""
                ),

            "previous_class":
                request.form.get(
                    "previous_class",
                    ""
                ),

            "session":
                request.form.get(
                    "session",
                    "2026-27"
                ),

            "address":
                request.form.get(
                    "address",
                    ""
                ),

            "city":
                request.form.get(
                    "city",
                    ""
                ),

            "district":
                request.form.get(
                    "district",
                    ""
                ),

            "pincode":
                request.form.get(
                    "pincode",
                    ""
                ),

            "photo":
                photo_filename,

            "admission_fee":
                admission_fee,

            "payment_status":
                request.form.get(
                    "payment_status",
                    "Pending"
                )
        }


        # ------------------------------------------
        # VALIDATION
        # ------------------------------------------

        if not data["student_name"]:

            flash(
                "Student name is required.",
                "danger"
            )

            return redirect(
                url_for("admission")
            )


        if not data["father_name"]:

            flash(
                "Father name is required.",
                "danger"
            )

            return redirect(
                url_for("admission")
            )


        if not data["mobile"]:

            flash(
                "Mobile number is required.",
                "danger"
            )

            return redirect(
                url_for("admission")
            )


        # ------------------------------------------
        # SAVE DATABASE
        # ------------------------------------------

        admission_id = add_admission(data)


        if not admission_id:

            flash(
                "Admission could not be saved.",
                "danger"
            )

            return redirect(
                url_for("admission")
            )


        # ------------------------------------------
        # DIRECT PDF DOWNLOAD
        # ------------------------------------------

        return redirect(
            url_for(
                "download_admission_receipt",
                admission_id=admission_id
            )
        )


    # GET
    return render_template(
        "admission.html"
    )

# ==========================================================
# ADMISSION SUCCESS
# ==========================================================

@app.route(
    "/admission/success/<int:admission_id>"
)
def admission_success(admission_id):

    admission = get_admission(
        admission_id
    )

    if not admission:

        flash(
            "Admission record not found.",
            "danger"
        )

        return redirect(
            url_for("admission")
        )

    return render_template(
        "admission_success.html",
        admission=admission,
        admission_id=admission_id
    )

# ==========================================================
# ADMISSION RECEIPT PDF
# ==========================================================

@app.route(
    "/admission/receipt/<int:admission_id>"
)
def download_admission_receipt(admission_id):

    # ------------------------------------------
    # GET ADMISSION
    # ------------------------------------------

    admission = get_admission(
        admission_id
    )

    if not admission:

        flash(
            "Admission record not found.",
            "danger"
        )

        return redirect(
            url_for("admission")
        )


    # ------------------------------------------
    # REPORTLAB IMPORTS
    # ------------------------------------------

    try:

        from reportlab.lib.pagesizes import A4

        from reportlab.lib import colors

        from reportlab.lib.styles import (
            getSampleStyleSheet,
            ParagraphStyle
        )

        from reportlab.lib.enums import (
            TA_CENTER,
            TA_LEFT
        )

        from reportlab.platypus import (
            SimpleDocTemplate,
            Paragraph,
            Spacer,
            Table,
            TableStyle,
            HRFlowable,
            Image as RLImage
        )

        from reportlab.lib.units import mm

    except ImportError:

        flash(
            "ReportLab is not installed. Run: pip install reportlab",
            "danger"
        )

        return redirect(
            url_for(
                "admission_success",
                admission_id=admission_id
            )
        )


    # ------------------------------------------
    # RECEIPT FOLDER
    # ------------------------------------------

    receipt_folder = app.config[
        "RECEIPT_FOLDER"
    ]

    os.makedirs(
        receipt_folder,
        exist_ok=True
    )


    # ------------------------------------------
    # FILE NAME
    # ------------------------------------------

    filename = (
        f"Admission_Receipt_ADM"
        f"{admission_id:05d}.pdf"
    )

    filepath = os.path.join(
        receipt_folder,
        filename
    )


    # ------------------------------------------
    # DOCUMENT
    # ------------------------------------------

    doc = SimpleDocTemplate(

        filepath,

        pagesize=A4,

        rightMargin=18 * mm,

        leftMargin=18 * mm,

        topMargin=15 * mm,

        bottomMargin=15 * mm
    )


    styles = getSampleStyleSheet()


    title_style = ParagraphStyle(

        "ReceiptTitle",

        parent=styles["Title"],

        fontSize=18,

        leading=22,

        alignment=TA_LEFT,

        textColor=colors.HexColor("#1e293b"),

        spaceAfter=3
    )


    subtitle_style = ParagraphStyle(

        "ReceiptSubtitle",

        parent=styles["Normal"],

        fontSize=10,

        leading=14,

        alignment=TA_LEFT,

        textColor=colors.HexColor("#64748b")
    )

    center_subtitle_style = ParagraphStyle(

        "ReceiptSubtitleCenter",

        parent=styles["Normal"],

        fontSize=10,

        leading=14,

        alignment=TA_CENTER,

        textColor=colors.HexColor("#64748b")
    )


    normal_style = ParagraphStyle(

        "ReceiptNormal",

        parent=styles["Normal"],

        fontSize=9,

        leading=13
    )


    label_style = ParagraphStyle(

        "ReceiptLabel",

        parent=styles["Normal"],

        fontSize=9,

        leading=12,

        textColor=colors.HexColor(
            "#555555"
        )
    )


    value_style = ParagraphStyle(

        "ReceiptValue",

        parent=styles["Normal"],

        fontSize=9,

        leading=12
    )


    success_style = ParagraphStyle(

        "Success",

        parent=styles["Normal"],

        fontSize=11,

        leading=15,

        alignment=TA_CENTER,

        textColor=colors.HexColor(
            "#198754"
        )
    )


    story = []


    # ==================================================
    # HEADER WITH EDUCATION LOGO
    # ==================================================

    logo_file_path = None
    possible_logos = [
        os.path.join(app.config["LOGO_FOLDER"], "logo.png"),
        os.path.join(app.config["LOGO_FOLDER"], "logo.jpg"),
        os.path.join(app.config["LOGO_FOLDER"], "logo.jpeg"),
        os.path.join(BASE_DIR, "static", "logo.png")
    ]

    for logo in possible_logos:
        if os.path.exists(logo):
            logo_file_path = logo
            break

    if logo_file_path:
        logo_element = RLImage(logo_file_path, width=28 * mm, height=28 * mm)
    else:
        # Generic Education Badge Graphic if Logo file doesn't exist
        logo_element = Paragraph(
            "<b><font size=16 color='#4338ca'>🎓</font><br/><font size=8 color='#4338ca'>EDU CENTER</font></b>",
            center_subtitle_style
        )

    header_text_cell = [
        Paragraph("<b>EDUCATION PDF & COACHING CENTER</b>", title_style),
        Paragraph("<b>OFFICIAL ADMISSION RECEIPT</b>", subtitle_style)
    ]

    header_table = Table(
        [[logo_element, header_text_cell]],
        colWidths=[32 * mm, 138 * mm]
    )

    header_table.setStyle(
        TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (0, 0), (0, 0), "CENTER"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ])
    )

    story.append(header_table)

    story.append(
        Spacer(1, 10)
    )

    story.append(
        HRFlowable(
            width="100%",
            thickness=1.5,
            color=colors.HexColor(
                "#4338ca"
            )
        )
    )

    story.append(
        Spacer(1, 12)
    )


    # ==================================================
    # ADMISSION NUMBER + DATE
    # ==================================================

    admission_number = (
        f"ADM{admission_id:05d}"
    )

    admission_date = datetime.now().strftime(
        "%d-%m-%Y %I:%M %p"
    )


    receipt_info = [

        [

            Paragraph(
                "<b>Admission No.</b>",
                normal_style
            ),

            Paragraph(
                admission_number,
                normal_style
            ),

            Paragraph(
                "<b>Admission Date</b>",
                normal_style
            ),

            Paragraph(
                admission_date,
                normal_style
            )

        ]
    ]


    info_table = Table(

        receipt_info,

        colWidths=[
            35 * mm,
            50 * mm,
            35 * mm,
            50 * mm
        ]
    )


    info_table.setStyle(
        TableStyle([

            (
                "BACKGROUND",
                (0, 0),
                (0, 0),
                colors.HexColor("#f1f3f5")
            ),

            (
                "BACKGROUND",
                (2, 0),
                (2, 0),
                colors.HexColor("#f1f3f5")
            ),

            (
                "BOX",
                (0, 0),
                (-1, -1),
                0.5,
                colors.HexColor("#cccccc")
            ),

            (
                "INNERGRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.HexColor("#dddddd")
            ),

            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE"
            ),

            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                7
            ),

            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                7
            ),

            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                7
            ),

            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                7
            )
        ])
    )


    story.append(
        info_table
    )

    story.append(
        Spacer(1, 15)
    )


    # ==================================================
    # STUDENT DETAILS WITH PHOTO
    # ==================================================

    story.append(
        Paragraph(
            "<b>STUDENT DETAILS</b>",
            normal_style
        )
    )

    story.append(
        Spacer(1, 7)
    )

    photo_path = None
    if "photo" in admission.keys() and admission["photo"]:
        candidate_path = os.path.join(
            app.config["STUDENT_PHOTO_FOLDER"],
            admission["photo"]
        )
        if os.path.exists(candidate_path):
            photo_path = candidate_path

    if photo_path:
        student_photo_element = RLImage(photo_path, width=32*mm, height=40*mm)
    else:
        student_photo_element = Paragraph("<font color='#888888'>[ No Photo ]</font>", center_subtitle_style)


    student_fields_data = [

        [
            Paragraph("<b>Student Name</b>", label_style),
            Paragraph(str(admission["student_name"] if "student_name" in admission.keys() and admission["student_name"] else ""), value_style)
        ],

        [
            Paragraph("<b>Father Name</b>", label_style),
            Paragraph(str(admission["father_name"] if "father_name" in admission.keys() and admission["father_name"] else ""), value_style)
        ],

        [
            Paragraph("<b>Mother Name</b>", label_style),
            Paragraph(str(admission["mother_name"] if "mother_name" in admission.keys() and admission["mother_name"] else ""), value_style)
        ],

        [
            Paragraph("<b>Date of Birth</b>", label_style),
            Paragraph(str(admission["dob"] if "dob" in admission.keys() and admission["dob"] else ""), value_style)
        ],

        [
            Paragraph("<b>Gender</b>", label_style),
            Paragraph(str(admission["gender"] if "gender" in admission.keys() and admission["gender"] else ""), value_style)
        ],

        [
            Paragraph("<b>Mobile Number</b>", label_style),
            Paragraph(str(admission["mobile"] if "mobile" in admission.keys() and admission["mobile"] else ""), value_style)
        ],

        [
            Paragraph("<b>Previous Class</b>", label_style),
            Paragraph(str(admission["previous_class"] if "previous_class" in admission.keys() and admission["previous_class"] else ""), value_style)
        ]
    ]

    details_subtable = Table(
        student_fields_data,
        colWidths=[40 * mm, 95 * mm]
    )

    details_subtable.setStyle(
        TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f8f9fa")),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5)
        ])
    )

    photo_subtable = Table(
        [[student_photo_element]],
        colWidths=[35 * mm]
    )
    photo_subtable.setStyle(
        TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ])
    )

    student_table = Table(
        [[details_subtable, photo_subtable]],
        colWidths=[135 * mm, 35 * mm]
    )
    student_table.setStyle(
        TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0)
        ])
    )

    story.append(
        student_table
    )

    story.append(
        Spacer(1, 15)
    )


    # ==================================================
    # COURSE DETAILS
    # ==================================================

    story.append(
        Paragraph(
            "<b>COURSE DETAILS</b>",
            normal_style
        )
    )

    story.append(
        Spacer(1, 7)
    )


    def get_value(key):

        try:

            if key in admission.keys():

                return str(
                    admission[key]
                    if admission[key] is not None
                    else ""
                )

        except Exception:

            pass

        return ""


    course_data = [

        [
            Paragraph(
                "<b>Course</b>",
                label_style
            ),
            Paragraph(
                get_value("course"),
                value_style
            )
        ],

        [
            Paragraph(
                "<b>Batch</b>",
                label_style
            ),
            Paragraph(
                get_value("batch"),
                value_style
            )
        ],

        [
            Paragraph(
                "<b>Session</b>",
                label_style
            ),
            Paragraph(
                get_value("session"),
                value_style
            )
        ],

        [
            Paragraph(
                "<b>Address</b>",
                label_style
            ),
            Paragraph(
                get_value("address"),
                value_style
            )
        ],

        [
            Paragraph(
                "<b>City / District</b>",
                label_style
            ),
            Paragraph(
                get_value("city")
                + " / "
                + get_value("district"),
                value_style
            )
        ],

        [
            Paragraph(
                "<b>PIN Code</b>",
                label_style
            ),
            Paragraph(
                get_value("pincode"),
                value_style
            )
        ]
    ]


    course_table = Table(

        course_data,

        colWidths=[
            45 * mm,
            125 * mm
        ]
    )


    course_table.setStyle(
        TableStyle([

            (
                "BOX",
                (0, 0),
                (-1, -1),
                0.5,
                colors.HexColor("#cccccc")
            ),

            (
                "INNERGRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.HexColor("#dddddd")
            ),

            (
                "BACKGROUND",
                (0, 0),
                (0, -1),
                colors.HexColor("#f8f9fa")
            ),

            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE"
            ),

            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                7
            ),

            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                7
            ),

            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                7
            ),

            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                7
            )
        ])
    )


    story.append(
        course_table
    )

    story.append(
        Spacer(1, 15)
    )


    # ==================================================
    # PAYMENT DETAILS
    # ==================================================

    story.append(
        Paragraph(
            "<b>PAYMENT DETAILS</b>",
            normal_style
        )
    )

    story.append(
        Spacer(1, 7)
    )


    try:

        fee = float(
            admission["admission_fee"]
            if "admission_fee" in admission.keys()
            else 0
        )

    except (ValueError, TypeError):

        fee = 0


    payment_status = get_value(
        "payment_status"
    ) or "Pending"


    payment_data = [

        [
            Paragraph(
                "<b>Admission Fee</b>",
                label_style
            ),

            Paragraph(
                f"Rs. {fee:.2f}",
                value_style
            )
        ],

        [
            Paragraph(
                "<b>Payment Status</b>",
                label_style
            ),

            Paragraph(
                payment_status,
                value_style
            )
        ]
    ]


    payment_table = Table(

        payment_data,

        colWidths=[
            45 * mm,
            125 * mm
        ]
    )


    payment_table.setStyle(
        TableStyle([

            (
                "BOX",
                (0, 0),
                (-1, -1),
                0.5,
                colors.HexColor("#cccccc")
            ),

            (
                "INNERGRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.HexColor("#dddddd")
            ),

            (
                "BACKGROUND",
                (0, 0),
                (0, -1),
                colors.HexColor("#f8f9fa")
            ),

            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                7
            ),

            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                7
            ),

            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                8
            ),

            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                8
            )
        ])
    )


    story.append(
        payment_table
    )

    story.append(
        Spacer(1, 18)
    )


    # ==================================================
    # SUCCESS
    # ==================================================

    story.append(
        Paragraph(
            "ADMISSION RECEIVED SUCCESSFULLY",
            success_style
        )
    )

    story.append(
        Spacer(1, 8)
    )

    story.append(
        Paragraph(
            "Please keep this receipt safely for future reference.",
            center_subtitle_style
        )
    )

    story.append(
        Spacer(1, 30)
    )


    # ==================================================
    # SIGNATURE
    # ==================================================

    signature_data = [

        [
            Paragraph(
                "________________________",
                normal_style
            ),

            Paragraph(
                "________________________",
                normal_style
            )
        ],

        [
            Paragraph(
                "Student / Guardian",
                center_subtitle_style
            ),

            Paragraph(
                "Authorized Signature",
                center_subtitle_style
            )
        ]
    ]


    signature_table = Table(

        signature_data,

        colWidths=[
            85 * mm,
            85 * mm
        ]
    )


    signature_table.setStyle(
        TableStyle([

            (
                "ALIGN",
                (0, 0),
                (-1, -1),
                "CENTER"
            )
        ])
    )


    story.append(
        signature_table
    )

    story.append(
        Spacer(1, 20)
    )


    story.append(
        Paragraph(
            "This is a computer-generated admission receipt.",
            center_subtitle_style
        )
    )


    # ==================================================
    # BUILD PDF
    # ==================================================

    doc.build(story)


    # ==================================================
    # AUTOMATIC DOWNLOAD
    # ==================================================

    return send_file(

        filepath,

        as_attachment=True,

        download_name=filename,

        mimetype="application/pdf"
    )

# ==========================================================
# ADMIN LOGIN
# ==========================================================

@app.route(
    "/admin/login",
    methods=["GET", "POST"]
)
def admin_login():

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        user = get_user_by_email(email)

        if not user or not check_user_password(user, password) or user["role"] != "admin":

            flash(
                "Invalid admin credentials.",
                "danger"
            )

            return redirect(
                url_for("admin_login")
            )

        session.clear()

        session["user_id"] = user["id"]
        session["name"] = user["name"]
        session["email"] = user["email"]
        session["role"] = "admin"

        return redirect(
            url_for("admin_dashboard")
        )

    return render_template(
        "admin_login.html"
    )


# ==========================================================
# ADMIN DASHBOARD
# ==========================================================

@app.route("/admin")
@admin_required
def admin_dashboard():

    statistics = get_statistics()

    pdfs = get_all_pdfs_admin()

    return render_template(
        "admin_dashboard.html",
        statistics=statistics,
        pdfs=pdfs
    )


# ==========================================================
# ADMIN PDFs
# ==========================================================

@app.route("/admin/pdfs")
@admin_required
def admin_pdfs():

    pdfs = get_all_pdfs_admin()

    return render_template(
        "admin_pdfs.html",
        pdfs=pdfs
    )


# ==========================================================
# ADD PDF
# ==========================================================

@app.route(
    "/admin/pdf/add",
    methods=["GET", "POST"]
)
@admin_required
def admin_add_pdf():

    if request.method == "POST":

        title = request.form.get(
            "title",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        category = request.form.get(
            "category",
            ""
        ).strip()

        price = request.form.get(
            "price",
            "0"
        )

        pdf = request.files.get(
            "pdf_file"
        )

        thumbnail = request.files.get(
            "thumbnail"
        )


        if not title:

            flash(
                "PDF title is required.",
                "danger"
            )

            return redirect(
                url_for("admin_add_pdf")
            )


        if not pdf or not pdf.filename:

            flash(
                "Please select a PDF file.",
                "danger"
            )

            return redirect(
                url_for("admin_add_pdf")
            )


        if not allowed_file(
            pdf.filename,
            ALLOWED_PDF_EXTENSIONS
        ):

            flash(
                "Only PDF files are allowed.",
                "danger"
            )

            return redirect(
                url_for("admin_add_pdf")
            )


        try:

            price = float(price)

            if price < 0:
                price = 0

        except ValueError:

            price = 0


        pdf_filename = secure_filename(
            pdf.filename
        )

        pdf.save(
            os.path.join(
                app.config["UPLOAD_FOLDER"],
                pdf_filename
            )
        )


        thumbnail_filename = ""


        if thumbnail and thumbnail.filename:

            if allowed_file(
                thumbnail.filename,
                ALLOWED_IMAGE_EXTENSIONS
            ):

                thumbnail_filename = secure_filename(
                    thumbnail.filename
                )

                thumbnail.save(
                    os.path.join(
                        app.config[
                            "THUMBNAIL_FOLDER"
                        ],
                        thumbnail_filename
                    )
                )


        add_pdf(

            title=title,

            description=description,

            category=category,

            price=price,

            thumbnail=thumbnail_filename,

            pdf_file=pdf_filename
        )


        flash(
            "PDF added successfully.",
            "success"
        )

        return redirect(
            url_for("admin_pdfs")
        )


    return render_template(
        "add_pdf.html"
    )

# ==========================================================
# EDIT PDF
# ==========================================================

@app.route(
    "/admin/pdf/edit/<int:pdf_id>",
    methods=["GET", "POST"]
)
@admin_required
def admin_edit_pdf(pdf_id):

    pdf = get_pdf(pdf_id)

    if not pdf:

        flash(
            "PDF not found.",
            "danger"
        )

        return redirect(
            url_for("admin_pdfs")
        )


    if request.method == "POST":

        title = request.form.get(
            "title",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        category = request.form.get(
            "category",
            ""
        ).strip()


        try:

            price = float(
                request.form.get(
                    "price",
                    "0"
                ) or 0
            )

        except ValueError:

            price = 0


        if price < 0:
            price = 0


        if not title:

            flash(
                "PDF title is required.",
                "danger"
            )

            return redirect(
                url_for(
                    "admin_edit_pdf",
                    pdf_id=pdf_id
                )
            )


        pdf_filename = pdf["pdf_file"]

        thumbnail_filename = pdf["thumbnail"]


        # New PDF
        new_pdf = request.files.get(
            "pdf_file"
        )


        if new_pdf and new_pdf.filename:

            if not allowed_file(
                new_pdf.filename,
                ALLOWED_PDF_EXTENSIONS
            ):

                flash(
                    "Only PDF files are allowed.",
                    "danger"
                )

                return redirect(
                    url_for(
                        "admin_edit_pdf",
                        pdf_id=pdf_id
                    )
                )


            new_filename = secure_filename(
                new_pdf.filename
            )


            old_path = os.path.join(
                app.config["UPLOAD_FOLDER"],
                pdf_filename
            )


            if (
                pdf_filename
                and pdf_filename != new_filename
                and os.path.exists(old_path)
            ):

                os.remove(old_path)


            new_pdf.save(
                os.path.join(
                    app.config["UPLOAD_FOLDER"],
                    new_filename
                )
            )


            pdf_filename = new_filename


        # New thumbnail
        new_thumbnail = request.files.get(
            "thumbnail"
        )


        if new_thumbnail and new_thumbnail.filename:

            if not allowed_file(
                new_thumbnail.filename,
                ALLOWED_IMAGE_EXTENSIONS
            ):

                flash(
                    "Invalid thumbnail format.",
                    "danger"
                )

                return redirect(
                    url_for(
                        "admin_edit_pdf",
                        pdf_id=pdf_id
                    )
                )


            new_thumbnail_filename = secure_filename(
                new_thumbnail.filename
            )


            old_thumbnail_path = os.path.join(
                app.config["THUMBNAIL_FOLDER"],
                thumbnail_filename or ""
            )


            if (
                thumbnail_filename
                and os.path.exists(old_thumbnail_path)
            ):

                os.remove(old_thumbnail_path)


            new_thumbnail.save(
                os.path.join(
                    app.config["THUMBNAIL_FOLDER"],
                    new_thumbnail_filename
                )
            )


            thumbnail_filename = (
                new_thumbnail_filename
            )


        success = update_pdf(

            pdf_id,

            title,

            description,

            category,

            price,

            thumbnail_filename,

            pdf_filename
        )


        if success:

            flash(
                "PDF updated successfully!",
                "success"
            )

        else:

            flash(
                "PDF update failed.",
                "danger"
            )


        return redirect(
            url_for("admin_pdfs")
        )


    return render_template(
        "edit_pdf.html",
        pdf=pdf
    )


# ==========================================================
# DELETE PDF
# ==========================================================

@app.route(
    "/admin/pdf/delete/<int:pdf_id>",
    methods=["POST"]
)
@admin_required
def admin_delete_pdf(pdf_id):

    pdf = get_pdf(pdf_id)

    if not pdf:

        flash(
            "PDF not found.",
            "danger"
        )

        return redirect(
            url_for("admin_pdfs")
        )


    pdf_path = os.path.join(
        app.config["UPLOAD_FOLDER"],
        pdf["pdf_file"]
    )


    if os.path.exists(pdf_path):

        os.remove(pdf_path)


    if "thumbnail" in pdf.keys() and pdf["thumbnail"]:

        thumbnail_path = os.path.join(
            app.config["THUMBNAIL_FOLDER"],
            pdf["thumbnail"]
        )


        if os.path.exists(
            thumbnail_path
        ):

            os.remove(
                thumbnail_path
            )


    delete_pdf(pdf_id)


    flash(
        "PDF deleted successfully.",
        "success"
    )


    return redirect(
        url_for("admin_pdfs")
    )


# ==========================================================
# ADMIN ORDERS
# ==========================================================

@app.route("/admin/orders")
@admin_required
def admin_orders():

    conn = get_db()

    orders = conn.execute(
        """
        SELECT
            orders.*,
            users.name,
            users.email,
            pdfs.title
        FROM orders
        JOIN users
            ON orders.user_id = users.id
        JOIN pdfs
            ON orders.pdf_id = pdfs.id
        ORDER BY orders.id DESC
        """
    ).fetchall()

    conn.close()

    return render_template(
        "admin_orders.html",
        orders=orders
    )


# ==========================================================
# ADMIN ADMISSIONS
# ==========================================================

@app.route("/admin/admissions")
@admin_required
def admin_admissions():

    admissions = get_all_admissions()

    return render_template(
        "admin_admissions.html",
        admissions=admissions
    )


# ==========================================================
# VIEW ADMISSION
# ==========================================================

@app.route(
    "/admin/admission/<int:admission_id>"
)
@admin_required
def admin_admission_view(
    admission_id
):

    admission = get_admission(
        admission_id
    )

    if not admission:

        flash(
            "Admission not found.",
            "danger"
        )

        return redirect(
            url_for("admin_admissions")
        )


    return render_template(
        "admin_admission_view.html",
        admission=admission
    )


# ==========================================================
# CHANGE PAYMENT STATUS
# ==========================================================

@app.route(
    "/admin/admission/<int:admission_id>/payment/<status>"
)
@admin_required
def admin_admission_payment(
    admission_id,
    status
):

    if status not in [
        "Paid",
        "Pending"
    ]:

        flash(
            "Invalid payment status.",
            "danger"
        )

        return redirect(
            url_for("admin_admissions")
        )


    update_admission_payment(
        admission_id,
        status
    )


    flash(
        f"Payment status changed to {status}.",
        "success"
    )


    return redirect(
        url_for("admin_admissions")
    )


# ==========================================================
# DELETE ADMISSION
# ==========================================================

@app.route(
    "/admin/admission/<int:admission_id>/delete"
)
@admin_required
def admin_admission_delete(
    admission_id
):

    delete_admission(
        admission_id
    )


    flash(
        "Admission deleted successfully.",
        "success"
    )


    return redirect(
        url_for("admin_admissions")
    )

# ==========================================================
# MAIN
# ==========================================================

if __name__ == "__main__":

    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )
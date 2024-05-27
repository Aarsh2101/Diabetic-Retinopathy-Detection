import pdfkit
import os

def generate_report(date=None, prediction=None, description=None, uploaded_image=None, importance_image=None):
    html_template = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <style>
            @page {{
                size: A4;
                margin: 1cm;
            }}
            body {{
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 0;
            }}
            .container {{
                background: white;
                padding: 20px;
                text-align: center;
            }}
            .status {{
                font-size: 24px;
                margin: 10px 0;
            }}
            .exam-info {{
                font-size: 20px;
                margin: 20px 0;
            }}
            .eye-results {{
                text-align: center;
                margin: 20px 0;
            }}
            .eye-results div {{
                display: inline-block;
                margin: 0 10px;
                text-align: center;
                width: 45%;
            }}
            .eye-results img {{
                border-radius: 10px;
            }}
            .main-title {{
                font-size: 22px;
                margin: 20px 0;
                width: 65%; 
                display: inline-block;
            }}
            .date {{
                width: 25%; 
                display: inline-block;
                text-align: right;
            }}
            .prediction {{
                font-size: 32px;
                margin: 10px 0;
                color: #00ff33;
            }}
            .description {{
                font-size: 18px;
                margin: 20px 0;
                text-align: justify;
            }}
            .exam-info {{
                overflow: auto; /* To clear the float */
            }}
        
            .exam-info div {{
                width: 50%;
                float: left;
            }}
            .uploaded-img, .importance-img{{
                width: 300px;
                height: 300px;
            }}
            .disclaimer {{
                text-align: left;
                font-size: 12px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="title-date">
                <h1 class="main-title">Summary of Diabetic Retinopathy (DR) Exam Result</h1>
                <p class="date">Date:{}</p>
            </div>
            <p class="status">Detected Severity of Diabetic Retinopathy:</p>
            <p class="prediction">{}</p>
            <p class="description">{}</p>
            <div class="exam-info">
                <div>Repeat exam in: <strong>12 Months</strong></div>
                <div>Referral to Ophthalmologist: <strong>Required</strong></div>
            </div>
            <div class="eye-results">
                <div>
                    <p>Uploaded Fundus Image</p>
                    <img class="uploaded-img" src="data:image/png;base64,{}" alt="">
                </div>
                <div>
                    <p>Importance Image</p>
                    <img class="importance-img" src="data:image/png;base64,{}" alt="">
                </div>
            </div>
            <div class="footer">
                <p class="disclaimer">*The image resolutions have been reduced. Do not use these thumbnail images for diagnostic purposes.</p>
            </div>
        </div>
    </body>
    </html>
    """
    html = html_template.format(date, prediction, description, uploaded_image, importance_image)
    report = pdfkit.from_string(html, False)
    return report
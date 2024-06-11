import pdfkit
from datetime import datetime

def generate_report(prediction=None, uploaded_image=None, importance_image=None, patient_info=None, specialist_info=None):
    html_template = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
    <link href='https://fonts.googleapis.com/css?family=Cardo' rel='stylesheet'>
        <style>
            @page {{
                size: A4;
                margin: 1cm;
            }}
            body {{
                font-family: Arial;
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
                font-size: 40px;
                margin: 10px 0;
                color: {prediction_color};
            }}
            .description {{
                font-size: 18px;
                margin: 20px 0;
                text-align: justify;
            }}
            .exam-info {{
                overflow: auto; 
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
            .patient-specialist-info {{
                width: 100%;
                margin-top: 25px;
                text-align: left;
                border-collapse: collapse;
                border: none;
                font-size: 22px;
            }}
            .heading-row {{
                background-color: #D6954D;
            }}
            .prediction-table {{
                border-collapse: collapse;
                width: 100%;
                margin: 30px 0px;
            }}
            .prediction-table td, .prediction-table th {{
                border: 1px solid #000; 
                padding: 8px;
            }}
            tbody tr {{
                margin-top: 10px;
                margin-bottom: 10px;
            }}
            .prediction-title {{
                font-size: 32px;
            }}
            .recommendation-table .heading-row {{
                text-align: left;
                font-size: 30px;
                display: block;
                padding: 10px 0;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="title-date">
                <h1 class="main-title">Diabetic Retinopathy (DR) Exam Result</h1>
                <p class="date">Date: {date}</p>
            </div>
            <hr>
            <table class="patient-specialist-info">
                <thead>
                    <tr class="heading-row">
                        <th>Patient Information</th>
                        <th>Specialist Information</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>Name: {patient_name}</td>
                        <td>Name: {specialist_name}</td>
                    </tr>
                    <tr>
                        <td>Gender: {patient_gender}</td>
                        <td>Email: {specialist_email}</td>
                    </tr>
                    <tr>
                        <td>DOB: {patient_dob}</td>
                        <td>Affiliation: {affiliation}</td>
                    </tr>
                    <tr>
                        <td>Location: {patient_location}</td>
                    </tr>
                </tbody>
            </table>
            <table class="prediction-table">
                <tbody>
                    <tr class="prediction-title heading-row">
                        <td>Detected Severity of Diabetic Retinopathy </td>
                    </tr>
                    <tr class="prediction">
                        <td>{severity}</td>
                    </tr>
                </tbody>
            </table>
            <div class="exam-info">
                <div>Repeat exam in: <strong>{repeat_in}</strong></div>
                <div>Referral to Ophthalmologist: <strong>{referral}</strong></div>
            </div>
            
            
            <div class="eye-results">
                <div>
                    <p>Uploaded Fundus Image</p>
                    <img class="uploaded-img" src="data:image/png;base64,{uploaded_img}" alt="">
                </div>
                <div>
                    <p>Importance Image</p>
                    <img class="importance-img" src="data:image/png;base64,{importance_img}" alt="">
                </div>
            </div>
            <table class="recommendation-table">
                <tbody>
                    <tr class="heading-row">
                        <td>Plan and Recommendations</td>
                    </tr>
                    <tr class="description">
                        <td>{description}</td>
                    </tr>
                </tbody>
            </table>
            <hr>
            <div class="footer">
                <p class="disclaimer">*The image resolutions have been reduced. Do not use these thumbnail images for diagnostic purposes.</p>
            </div>
        </div>
    </body>
    </html>
    """
    date = datetime.now().date().strftime('%m-%d-%Y')
    labels = {
        0: 'No Diabetic Retinopathy',
        1: 'Mild Diabetic Retinopathy', 
        2: 'Moderate Diabetic Retinopathy',
        3: 'Severe Diabetic Retinopathy',
        4: 'Proliferative Diabetic Retinopathy'
        }
    description = {
                0: 'The retina is completely clear of any signs of diabetic retinopathy, indicating that the retinal vessels are healthy and undamaged by diabetes. This is an optimal outcome, and maintaining regular monitoring is recommended to ensure that the retina remains healthy. Lifestyle modifications and managing blood sugar levels are advised to continue preventing the onset of retinopathy.',
                1: '''Early signs of diabetic retinopathy are evident, characterized by microaneurysms - small areas of swelling in the blood vessels of the retina. At this stage, there typically aren't noticeable symptoms affecting vision, but it's crucial to monitor the condition closely. Yearly eye exams are recommended to track any changes and manage diabetes effectively to halt the progression.''',
                2: 'This stage shows moderate non-proliferative diabetic retinopathy with more pronounced changes, such as blocked blood vessels that can affect retinal nourishment. Patients might start experiencing slight vision issues. It is critical at this stage to manage diabetes rigorously and consult with an eye care professional every six months to monitor the condition closely and discuss potential interventions.',
                3: 'Marked by severe non-proliferative diabetic retinopathy, a significant number of retinal blood vessels are now blocked, severely reducing blood flow to various parts of the retina. This condition can lead to complications like DME (Diabetic Macular Edema). Close and immediate medical supervision is necessary, with treatment options evaluated to prevent the disease from advancing to the proliferative stage.',
                4: 'This is the proliferative stage of diabetic retinopathy, the most severe form, where new and abnormal blood vessels begin to develop on the retina and into the vitreous gel. These vessels are fragile and prone to bleeding, significantly threatening vision and potentially leading to retinal detachment or blindness. Immediate and aggressive medical treatment is essential to manage this stage and preserve as much vision as possible.'
                }
    repeat_exam = {
        0: '2 Years',
        1: '1 Year',
        2: '6 Months',
        3: '3 Month',
        4: '1 Month'
    }
    referral = {
        0: 'Not Required',
        1: 'Not Required',
        2: 'Required',
        3: 'Required',
        4: 'Required'
    }
    severity_color = {
        0: '#44ce1b',
        1: '#bbdb44',
        2: '#f7e379',
        3: '#f2a134',
        4: '#e51f1f'
    }
    
    html = html_template.format(date=date, 
        severity=labels[prediction], 
        description=description[prediction], 
        repeat_in=repeat_exam[prediction], 
        referral=referral[prediction], 
        uploaded_img=uploaded_image, 
        importance_img=importance_image, 
        prediction_color=severity_color[prediction], 
        patient_name=patient_info['name'],
        patient_gender=patient_info['gender'],
        patient_dob=patient_info['dob'], 
        patient_location=patient_info['location'], 
        specialist_name=specialist_info.first_name+" "+specialist_info.last_name, 
        affiliation=specialist_info.affiliation,
        specialist_email=specialist_info.email)
    report = pdfkit.from_string(html, False)
    return report
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files import File
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from .forms import RetinaPhotoForm, CorrectLabelForm
from .models import *
from accounts.models import *
from .DDRpredict import get_predicted_label_and_gradcam
from .report import generate_report
import numpy as np
from PIL import Image
import os, json, base64
from io import BytesIO
from datetime import datetime


def pil_image_to_django_file(pil_image, image_name):
    byte_arr = BytesIO()
    pil_image.save(byte_arr, format='PNG')
    return ContentFile(byte_arr.getvalue(), name=image_name)

def image_file_path_to_base64_string(filepath: str) -> str:
  '''
  Takes a filepath and converts the image saved there to its base64 encoding,
  then decodes that into a string.
  '''
  with open(filepath, 'rb') as f:
    return base64.b64encode(f.read()).decode()

# Create your views here.

def index(request):
    return render(request, 'index.html')

@login_required(login_url='/login/')
def predict(request):
    if request.method == 'POST':
        form = RetinaPhotoForm(request.POST, request.FILES)
        if form.is_valid():
            form.instance.user = request.user
            form.save()

            img = form.instance.image
            img = Image.open(img)
            img_name = os.path.basename(form.instance.image.name)
            request.session['img_name'] = img_name  # Store img_name in the session data
            # request.session['retina_photo_id'] = form.instance.id  # Store retina_photo_id in the session data
            # retina_gradcam_img_path = settings.MEDIA_URL + 'retina_gradcam_images/' + img_name
            cropped_img_path = settings.MEDIA_URL + 'cropped_images/' + img_name

            cropped_image, predicted_label, gradcam_image, legend_range = get_predicted_label_and_gradcam(img)
            
            labels = ['No Diabetic Retinopathy', 'Mild Diabetic Retinopathy', 'Moderate Diabetic Retinopathy', 'Severe Diabetic Retinopathy', 'Proliferative Diabetic Retinopathy']
            
            description = {
                0: 'The retina shows no signs of diabetic retinopathy. This indicates healthy retinal vessels without any damage due to diabetes. Regular monitoring is recommended to maintain eye health.',
                1: 'Early signs of diabetic retinopathy are present, characterized by small areas of swelling in the blood vessels of the retina. This stage generally does not affect vision but requires regular eye exams to monitor progression.',
                2: 'There are more noticeable changes in the retina, including blocked blood vessels that prevent proper blood flow. Vision may begin to be affected, and more frequent monitoring and management of diabetes are necessary to prevent further progression.',
                3: 'A significant portion of the blood vessels in the retina are blocked, leading to areas of the retina not receiving enough blood. This stage carries a higher risk of progressing to proliferative diabetic retinopathy, requiring closer medical supervision and possibly treatment.',
                4: 'The most advanced stage, where new, abnormal blood vessels begin to grow in the retina and vitreous. These vessels can bleed and cause severe vision loss or blindness. Immediate medical treatment is essential to manage and prevent further complications.'
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

            legend_values = [round(num, 3) for num in np.linspace(legend_range['min'], legend_range['max'], 5).tolist()]
            
            gradcam_image_django = pil_image_to_django_file(gradcam_image, img_name)
            gradcam_image = GradcamImage(image=gradcam_image_django, retina_photo=form.instance)
            gradcam_image.save()
            # gradcam_image.save(retina_gradcam_img_path[1:])
            cropped_image.save(cropped_img_path[1:])

            # REPORT GENERATION
            date = datetime.now().date().strftime('%m-%d-%Y')
            uploaded_img_str = image_file_path_to_base64_string(cropped_img_path[1:])
            gradcam_img_str = image_file_path_to_base64_string(gradcam_image.image.url[1:])
            report = generate_report(date=date, prediction=labels[predicted_label], description=description[predicted_label], uploaded_image=uploaded_img_str, importance_image=gradcam_img_str)
            report_io = BytesIO()
            report_io.write(report)
            report_io.seek(0)
            report = Report(file=File(report_io, name='report.pdf'), retina_photo=form.instance)
            report.save()

            correct_label_form = CorrectLabelForm()
            context = {
                'predicted_label': labels[predicted_label],
                'description': description[predicted_label],
                'cropped_img_path': cropped_img_path,
                'retina_img_path': form.instance.image.url,
                'retina_gradcam_img_path': gradcam_image.image.url,
                'correct_label_form': correct_label_form,
                'legend_values': legend_values,
            }
            return render(request, 'results.html', context)
    else:
        form = RetinaPhotoForm()
        sample_img_zip = ZipFile.objects.get(user=request.user)
        context = {
            'form': form,
            'sample_img_zip': sample_img_zip.file.url,
            }
    return render(request, 'predict.html', context)

def correct_prediction(request):
    if request.method == 'POST':
        correct_label_form = CorrectLabelForm(request.POST)
        img_name = request.session.get('img_name', 'default.png')
        retina_photo = RetinaPhoto.objects.get(image = 'retina_images/'+ img_name )
        correct_label_form.instance.retina_photo = retina_photo
        # correct_label.instance.retina_photo = request.session.get('img_name', 'default.png')
        # post_data = request.POST.copy()  # Make a mutable copy
        # post_data['image_name'] = request.session.get('img_name', 'default.png')  # Add image_name
        # form = CorrectLabelForm(post_data)  # Use the modified POST data

        if correct_label_form.is_valid():
            correct_label_form.save()
            return redirect('predict')
    else:
        form = CorrectLabelForm()
        return redirect('/')
    

def save_canvas_image(request):
    
    if request.method == 'POST':
        # print(request.data)
        data = json.loads(request.body)
        image_data_url = data['imageDataUrl']
        format, imgstr = image_data_url.split(';base64,') 
        ext = format.split('/')[-1] 
        img_name = request.session.get('img_name', 'default.png')
        retina_photo = RetinaPhoto.objects.get(image = 'retina_images/'+ img_name )
        data = ContentFile(base64.b64decode(imgstr), name=img_name)
        
        canvas_image = CanvasImage(image=data, created_by=request.user, retina_photo=retina_photo)
        canvas_image.save()
        
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})

def team(request):
    context = {
        'lead_team': [{
                'name': 'Anuj Tiwari',
                'description': 'Senior Research Associate',
                'img': 'anuj.jpeg'
        },
        {
                'name': 'Aarsh Patel',
                'description': 'Machine Learning Engineer',
                'img': 'aarsh.jpeg'
        }],
        'research_team': [{
                'name': 'John Doe',
                'description': 'Machine Learning Engineer',
                'img': 'default-profile.svg'
        },
        {
                'name': 'John Doe',
                'description': 'Machine Learning Engineer',
                'img': 'default-profile.svg'
        },
        {
                'name': 'John Doe',
                'description': 'Machine Learning Engineer',
                'img': 'default-profile.svg'
        },]
    }
    return render(request, 'team.html', context)

@login_required(login_url='/login/')
def dashboard(request):
    submissions = RetinaPhoto.objects.filter(user=request.user)
        
    context = {
        'submissions': submissions,
    }
    return render(request, 'dashboard.html', context)

def update_submission(request, submission_id):
    submission = get_object_or_404(RetinaPhoto, pk=submission_id)
    
    if request.method == 'POST':
        correct_label_form = CorrectLabelForm(request.POST, instance=submission.correct_label)
        if correct_label_form.is_valid():
            correct_label_form.save()
            return redirect('dashboard')

    else:
        correct_label_form = CorrectLabelForm()
        context = {
            'text': 'get',
            'retina_url': submission.image.url,
            'gradcam_url': submission.gradcam_image.image.url,
            'correct_label': submission.correct_label.correct_label,
            'correct_label_form': correct_label_form,
        }
        return render(request, 'update_submission.html', context)

def update_canvas_image(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        image_data_url = data['imageDataUrl']
        submission_id = data['submissionId']
        retina_photo = get_object_or_404(RetinaPhoto, pk=submission_id)
        format, imgstr = image_data_url.split(';base64,') 
        ext = format.split('/')[-1] 
        img_name = retina_photo.image.name.split('/')[-1]
        data = ContentFile(base64.b64decode(imgstr), name=img_name)
        
        canvas_image = CanvasImage.objects.get(retina_photo=retina_photo)
        canvas_image.image = data
        canvas_image.save()
        
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})


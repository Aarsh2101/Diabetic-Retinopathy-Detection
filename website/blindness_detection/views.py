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
                0: 'The retina is completely clear of any signs of diabetic retinopathy, indicating that the retinal vessels are healthy and undamaged by diabetes. This is an optimal outcome, and maintaining regular monitoring is recommended to ensure that the retina remains healthy. Lifestyle modifications and managing blood sugar levels are advised to continue preventing the onset of retinopathy.',
                1: '''Early signs of diabetic retinopathy are evident, characterized by microaneurysms — small areas of swelling in the blood vessels of the retina. At this stage, there typically aren't noticeable symptoms affecting vision, but it's crucial to monitor the condition closely. Yearly eye exams are recommended to track any changes and manage diabetes effectively to halt the progression.''',
                2: 'This stage shows moderate non-proliferative diabetic retinopathy with more pronounced changes, such as blocked blood vessels that can affect retinal nourishment. Patients might start experiencing slight vision issues. It is critical at this stage to manage diabetes rigorously and consult with an eye care professional every six months to monitor the condition closely and discuss potential interventions.',
                3: 'Marked by severe non-proliferative diabetic retinopathy, a significant number of retinal blood vessels are now blocked, severely reducing blood flow to various parts of the retina. This condition can lead to complications like DME (Diabetic Macular Edema). Close and immediate medical supervision is necessary, with treatment options evaluated to prevent the disease from advancing to the proliferative stage.',
                4: 'This is the proliferative stage of diabetic retinopathy, the most severe form, where new and abnormal blood vessels begin to develop on the retina and into the vitreous gel. These vessels are fragile and prone to bleeding, significantly threatening vision and potentially leading to retinal detachment or blindness. Immediate and aggressive medical treatment is essential to manage this stage and preserve as much vision as possible.'
                }
            

            legend_values = [round(num, 3) for num in np.linspace(legend_range['min'], legend_range['max'], 5).tolist()]
            
            gradcam_image_django = pil_image_to_django_file(gradcam_image, img_name)
            gradcam_image = GradcamImage(image=gradcam_image_django, retina_photo=form.instance)
            gradcam_image.save()
            # gradcam_image.save(retina_gradcam_img_path[1:])
            cropped_image.save(cropped_img_path[1:])

            # REPORT GENERATION
            uploaded_img_str = image_file_path_to_base64_string(cropped_img_path[1:])
            gradcam_img_str = image_file_path_to_base64_string(gradcam_image.image.url[1:])
            report = generate_report(prediction=predicted_label, uploaded_image=uploaded_img_str, importance_image=gradcam_img_str)
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
                'img': 'anuj.jpeg',
                'affiliation': 'Discovery Partners Institute'
        },
        {
                'name': 'Aarsh Patel',
                'description': 'Gratuade Student Researcher',
                'img': 'aarsh.jpeg',
                'affiliation': 'University of Illinois at Chicago'
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


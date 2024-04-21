from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.core.files.base import ContentFile
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from .forms import RetinaPhotoForm, CorrectLabelForm
from .models import *
from accounts.models import *
from .DDRpredict import get_predicted_label_and_gradcam
import numpy as np
from PIL import Image
import os, json, base64
from io import BytesIO


def pil_image_to_django_file(pil_image, image_name):
    byte_arr = BytesIO()
    pil_image.save(byte_arr, format='PNG')
    return ContentFile(byte_arr.getvalue(), name=image_name)


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
            labels = ['No DR', 'Mild DR', 'Moderate DR', 'Severe DR', 'Proliferative DR']

            legend_values = [round(num, 3) for num in np.linspace(legend_range['min'], legend_range['max'], 5).tolist()]
            
            gradcam_image_django = pil_image_to_django_file(gradcam_image, img_name)
            gradcam_image = GradcamImage(image=gradcam_image_django, retina_photo=form.instance)
            gradcam_image.save()
            # gradcam_image.save(retina_gradcam_img_path[1:])
            cropped_image.save(cropped_img_path[1:])

            correct_label_form = CorrectLabelForm()
            context = {
                'predicted_label': labels[predicted_label],
                'cropped_img_path': cropped_img_path,
                'retina_img_path': form.instance.image.url,
                'retina_gradcam_img_path': gradcam_image.image.url,
                'correct_label_form': correct_label_form,
                'legend_values': legend_values,
            }
            return render(request, 'results.html', context)
    else:
        form = RetinaPhotoForm()
        context = {
            'form': form,
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
                'description': 'Full Stack Developer',
                'img': 'anuj.jpeg'
        },
        {
                'name': 'Aarsh Patel',
                'description': 'Machine Learning Engineer',
                'img': 'aarsh.jpg'
        }],
        'research_team': [{
                'name': 'John Doe',
                'description': 'Machine Learning Engineer',
                'img': 'john-doe.jpeg'
        },
        {
                'name': 'John Doe',
                'description': 'Machine Learning Engineer',
                'img': 'john-doe.jpeg'
        },
        {
                'name': 'John Doe',
                'description': 'Machine Learning Engineer',
                'img': 'john-doe.jpeg'
        },]
    }
    return render(request, 'team.html', context)

@login_required(login_url='/login/')
def dashboard(request):
    submissions = RetinaPhoto.objects.filter(user=request.user)
    from django.core.exceptions import ObjectDoesNotExist
    try:
        sample_images = ZipFile.objects.get(user=request.user)
    except ZipFile.DoesNotExist:
        sample_images = None
        
    context = {
        'submissions': submissions,
        'sample_images': sample_images,
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


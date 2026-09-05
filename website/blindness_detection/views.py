from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files import File
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .forms import RetinaPhotoForm, CorrectLabelForm, PatientForm
from .models import *
from accounts.models import *
from .DDRpredict import get_predicted_label_and_gradcam
from .bvsegment import get_blood_vessels
from .hemorrhages import get_hemorrhages
from .softexudates import get_softexudates
from .hardexudates import get_hardexudates
from .optical_disk import get_optical_disk
from .report import generate_report
import numpy as np
from PIL import Image
import os, json, base64
from pathlib import Path
from io import BytesIO
from datetime import datetime


def pil_image_to_django_file(pil_image, image_name):
    byte_arr = BytesIO()
    pil_image.save(byte_arr, format='PNG')
    return ContentFile(byte_arr.getvalue(), name=image_name)

def image_file_path_to_base64_string(filepath: str) -> str:
    """Convert an image file to a base64 string."""
    with open(filepath, 'rb') as f:
        return base64.b64encode(f.read()).decode()


def generated_image_location(folder: str, image_name: str) -> tuple[Path, str]:
    """Create a media subdirectory and return its filesystem path and URL."""
    directory = Path(settings.MEDIA_ROOT) / folder
    directory.mkdir(parents=True, exist_ok=True)
    return directory / image_name, f'{settings.MEDIA_URL}{folder}/{image_name}'


def current_patient(request):
    patient_id = request.session.get('patient_submission_id')
    return get_object_or_404(Patient, pk=patient_id, user=request.user)


def sample_zip_url(user):
    zip_file = ZipFile.objects.filter(user=user).first()
    return zip_file.file.url if zip_file and zip_file.file else None

# Create your views here.

def index(request):
    return render(request, 'index.html')

@login_required(login_url='/login/')
def predict(request):
    if request.method == 'POST':
        patient_form = PatientForm(request.POST, request.FILES)
        if patient_form.is_valid():
            patient_form.instance.user = request.user
            patient_form.save()

            img = patient_form.instance.image
            img = Image.open(img)
            image_name = f'{patient_form.instance.pk}_{os.path.basename(patient_form.instance.image.name)}'
            request.session['patient_submission_id'] = patient_form.instance.pk
            cropped_image_file, cropped_img_path = generated_image_location('cropped_images', image_name)

            blood_vessels_file, blood_vessels_path = generated_image_location('blood_vessels', image_name)
            Image.fromarray(get_blood_vessels(img)).save(blood_vessels_file)
            hemorrhages_file, hemorrhages_path = generated_image_location('hemorrhages', image_name)
            Image.fromarray(get_hemorrhages(img)).save(hemorrhages_file)
            softexudates_file, softexudates_path = generated_image_location('softexudates', image_name)
            Image.fromarray(get_softexudates(img)).save(softexudates_file)
            hardexudates_file, hardexudates_path = generated_image_location('hardexudates', image_name)
            Image.fromarray(get_hardexudates(img)).save(hardexudates_file)
            optical_disk_file, optical_disk_path = generated_image_location('optical_disk', image_name)
            Image.fromarray(get_optical_disk(img)).save(optical_disk_file)

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
            
            # Save the correct label in the database
            correct_label_form = CorrectLabelForm()
            correct_label_form.instance.patient = patient_form.instance
            correct_label_form.instance.correct_label = labels[predicted_label]
            correct_label_form.instance.save()
     
            # Save the gradcam image in the database
            gradcam_image_django = pil_image_to_django_file(gradcam_image, image_name)
            gradcam_image = GradcamImage(image=gradcam_image_django, retina_photo=patient_form.instance)
            gradcam_image.save()

            cropped_image.save(cropped_image_file)

            # REPORT GENERATION
            uploaded_img_str = image_file_path_to_base64_string(cropped_image_file)
            gradcam_img_str = image_file_path_to_base64_string(gradcam_image.image.path)
            specialist = request.user
            report = generate_report(prediction=predicted_label, uploaded_image=uploaded_img_str, importance_image=gradcam_img_str, patient_info=patient_form.cleaned_data, specialist_info=specialist)
            report_io = BytesIO()
            report_io.write(report)
            report_io.seek(0)
            report = Report(file=File(report_io, name='report.pdf'), retina_photo=patient_form.instance)
            report.save()

            results_context = { 
                'predicted_label': labels[predicted_label],
                'cropped_img_path': cropped_img_path,
                'retina_gradcam_img_path': gradcam_image.image.url,
                'legend_values': legend_values,
            }
            request.session['results_context'] = results_context

        if not patient_form.is_valid():
            return render(request, 'predict.html', {
                'patient_form': patient_form,
                'sample_img_zip': sample_zip_url(request.user),
                'user_info': request.user,
            })

        context = {
            'patient_form': patient_form,
            'sample_img_zip': sample_zip_url(request.user),
            'user_info': request.user,
            'predicted_label': labels[predicted_label],
            'description': description[predicted_label],
            'blood_vessels_path': blood_vessels_path,
            'hemorrhages_path': hemorrhages_path,
            'softexudates_path': softexudates_path,
            'hardexudates_path': hardexudates_path,
            'optical_disk_path': optical_disk_path,
            'cropped_img_path': cropped_img_path,
            'retina_gradcam_img_path': gradcam_image.image.url,
            'report': report.file.url,
            }
        return render(request, 'predict.html', context)

    else:
        patient_form = PatientForm()
        retina_photo_form = RetinaPhotoForm()
        context = {
            'patient_form': patient_form,
            'retina_photo_form': retina_photo_form,
            'sample_img_zip': sample_zip_url(request.user),
            'user_info': request.user,
            }
    return render(request, 'predict.html', context)

@login_required(login_url='/login/')
def results(request):
    results_context = request.session.get('results_context')
    if not results_context:
        return redirect('predict')

    patient = current_patient(request)
    results_context['correct_label_form'] = CorrectLabelForm(instance=patient.correct_label)
    return render(request, 'results.html', results_context)


@login_required(login_url='/login/')
@require_POST
def correct_prediction(request):
    patient = current_patient(request)
    correct_label_form = CorrectLabelForm(request.POST, instance=patient.correct_label)
    if correct_label_form.is_valid():
        correct_label_form.save()
    return redirect('predict')


@login_required(login_url='/login/')
@require_POST
def save_canvas_image(request):
    payload = json.loads(request.body)
    _, image_data = payload['imageDataUrl'].split(';base64,', 1)
    patient = current_patient(request)
    image_name = patient.image.name.rsplit('/', 1)[-1]
    canvas_file = ContentFile(base64.b64decode(image_data), name=image_name)
    CanvasImage.objects.update_or_create(
        retina_photo=patient,
        defaults={'image': canvas_file, 'created_by': request.user},
    )
    return JsonResponse({'success': True})

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
            },
            {
                'name': 'Yoonseo Kim',
                'description': 'Highschool Summer Intern',
                'img': 'yoonseo.png',
                'affiliation': 'Illinois Mathematics and Science Academy​'
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
    submissions = Patient.objects.filter(user=request.user)   
    context = {
        'submissions': submissions,
    }
    return render(request, 'dashboard.html', context)

@login_required(login_url='/login/')
def update_submission(request, submission_id):
    submission = get_object_or_404(Patient, pk=submission_id, user=request.user)

    if request.method == 'POST':
        correct_label_form = CorrectLabelForm(request.POST, instance=submission.correct_label)
        if correct_label_form.is_valid():
            correct_label_form.save()
            return redirect('dashboard')
    else:
        correct_label_form = CorrectLabelForm(instance=submission.correct_label)

    context = {
        'retina_url': submission.image.url,
        'gradcam_url': submission.gradcam_image.image.url,
        'correct_label': submission.correct_label.correct_label,
        'correct_label_form': correct_label_form,
    }
    return render(request, 'update_submission.html', context)


@login_required(login_url='/login/')
@require_POST
def update_canvas_image(request):
    payload = json.loads(request.body)
    patient = get_object_or_404(Patient, pk=payload['submissionId'], user=request.user)
    _, image_data = payload['imageDataUrl'].split(';base64,', 1)
    image_name = patient.image.name.rsplit('/', 1)[-1]
    canvas_file = ContentFile(base64.b64decode(image_data), name=image_name)
    CanvasImage.objects.update_or_create(
        retina_photo=patient,
        defaults={'image': canvas_file, 'created_by': request.user},
    )
    return JsonResponse({'success': True})


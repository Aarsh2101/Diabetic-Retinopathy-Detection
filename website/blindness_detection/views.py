from django.shortcuts import render
from django.conf import settings
from django.core.files.base import ContentFile
from django.http import HttpResponse, JsonResponse
from .forms import RetinaPhotoForm, CorrectLabelForm
from .models import CanvasImage
from .predict import get_predicted_label_and_gradcam
from PIL import Image
import os, json, base64


# Create your views here.

def predict(request):
    if request.method == 'POST':
        form = RetinaPhotoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            img = form.instance.image
            img = Image.open(img)
            img_name = os.path.basename(form.instance.image.name)
            request.session['img_name'] = img_name  # Store img_name in the session data
            retina_gradcam_img_path = settings.MEDIA_URL + 'retina_gradcam_images/' + img_name
            predicted_label, gradcam_image = get_predicted_label_and_gradcam(img)
            gradcam_image.save(retina_gradcam_img_path[1:])

            correct_label_form = CorrectLabelForm()
            context = {'predicted_label': predicted_label,
            'retina_img_path': form.instance.image.url,
            'retina_gradcam_img_path': retina_gradcam_img_path,
            'correct_label_form': correct_label_form,
            }
            return render(request, 'results.html', context)
    else:
        form = RetinaPhotoForm()
        context = {'form': form}
    return render(request, 'predict.html', context)

def correct_prediction(request):
    if request.method == 'POST':
        form = CorrectLabelForm(request.POST)
        if form.is_valid():
            # Update the model with the correct label
            pass
    else:
        form = CorrectLabelForm()
        context = {'form': form}
    return HttpResponse('Correct prediction page')


def save_canvas_image(request):
    
    if request.method == 'POST':
        # print(request.data)
        data = json.loads(request.body)
        image_data_url = data['imageDataUrl']
        format, imgstr = image_data_url.split(';base64,') 
        ext = format.split('/')[-1] 
        data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        img_name = request.session.get('img_name', 'default.png')
        
        canvas_image = CanvasImage()  # Assuming your model has an ImageField named 'image'
        canvas_image.image.save(img_name, data, save=True)
        
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})
# Eyentify: Diabetic Retinopathy Detection

Eyentify is a research prototype for five-class diabetic-retinopathy grading from retinal fundus images. It combines a Django interface, a fine-tuned ResNet-50 classifier, Grad-CAM visualization, traditional image-processing overlays, and PDF report generation.

> **Medical and research disclaimer:** This project is not a medical device and must not be used for diagnosis, treatment, screening decisions, or clinical care. Any deployment handling patient images must be reviewed for privacy, security, consent, institutional, and regulatory requirements.

## Repository layout

- `website/` — Django application and image-processing pipeline.
- `models/` — research notebooks for preprocessing, training, and evaluation.
- `Paper 1/` — model-comparison notebooks and exported figures.
- `create_zip.ipynb` — helper notebook for dataset samples.

## What is intentionally excluded

This public repository does **not** include retinal images, patient records, SQLite databases, generated reports, session data, model checkpoints, or collected static files. The DDR dataset and model artifacts must be obtained and used only under their applicable terms and permissions.

## Local setup

Prerequisites: Python 3.9+ and `wkhtmltopdf` (required by `pdfkit` to generate reports).

```bash
git clone https://github.com/Aarsh2101/Diabetic-Retinopathy-Detection.git
cd Diabetic-Retinopathy-Detection
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Export the values from `.env` in your shell or configure them through your deployment platform. `DJANGO_SECRET_KEY` must be a new, private, randomly generated value. Do not commit `.env`.

Provide the separately distributed five-class ResNet-50 checkpoint and set `DR_MODEL_PATH` to its absolute filesystem path:

```bash
export DJANGO_SECRET_KEY='a-new-random-value'
export DR_MODEL_PATH='/absolute/path/to/DDRresnet50_best_acc_final.pth'
cd website
python manage.py migrate
python manage.py runserver
```

For production, keep `DJANGO_DEBUG=false`, configure an explicit `DJANGO_ALLOWED_HOSTS` list and `DJANGO_CSRF_TRUSTED_ORIGINS`, use a production database, serve static files with `collectstatic`, and store uploaded media in access-controlled storage. Do not expose patient media through a public static-file server.

## Model pipeline

`website/blindness_detection/DDRpredict.py`:

1. crops the fundus region;
2. applies resizing, CLAHE contrast enhancement, and denoising;
3. grades one of five diabetic-retinopathy severity classes with ResNet-50 + GeM pooling; and
4. produces a Grad-CAM overlay.

The app also produces non-diagnostic blood-vessel, hemorrhage, soft-exudate, hard-exudate, and optical-disk processing overlays.

## Data, privacy, and security

- Never commit real patient data, images, reports, databases, credentials, or model artifacts whose distribution is restricted.
- Confirm data consent and dataset/model licenses before use or redistribution.
- Authentication protects application routes, but an actual clinical deployment requires a dedicated privacy/security review, audit controls, encryption, retention policies, and protected media storage.

## License

The source code is available under the [MIT License](LICENSE). Third-party packages, datasets, model weights, images, and web assets remain subject to their own licenses and terms.

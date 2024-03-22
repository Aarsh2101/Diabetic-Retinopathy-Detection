echo "BUILD START"
python3.9 -m -pip install -r requirements.txt
python3.9 website/manage.py collectstatic --noinput --clear
echo "BUILD END"

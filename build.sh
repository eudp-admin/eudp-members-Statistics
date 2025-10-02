#!/usr/bin/env bash
# exit on error
set -o errexit

# 1. አስፈላጊ ፓኬጆችን ይጫኑ
pip install -r requirements.txt

# 2. Static ፋይሎችን ይሰብስቡ
python manage.py collectstatic --no-input

# 3. የዳታቤዝ ለውጦችን ይተግብሩ
python manage.py migrate
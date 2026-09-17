Kairozen AI — គម្រោងធំ + Grok API
================================

មុខងារ:
- បង្កើតគម្រោងច្រើន
- Mode: កសាង / ផែនការ / Code / ពិនិត្យ
- AI បង្កើត file ច្រើន (parse ពី ```path/file)
- រក្សាទុក messages + files ក្នុង DATA_DIR

Env:
  GROK_API_KEY=...
  GROK_MODEL=grok-3
  DATA_DIR=/var/data   (Render Disk)

Run local:
  export GROK_API_KEY=xai-...
  pip install -r requirements.txt
  python app.py

Render Disk:
  Mount /var/data  →  DATA_DIR=/var/data

# Gunicorn config untuk deploy Render (dipakai via Start Command di dashboard:
#   gunicorn -c gunicorn.conf.py app:app)
#
# Alasan: request /analysis/dataset (N citra x 3 payload + histogram + JPEG)
# wajar memakan waktu puluhan detik sampai >1 menit. Timeout default gunicorn
# (30 detik) membunuh worker di tengah jalan -> 500 WORKER TIMEOUT.

timeout = 300  # bunuh worker hanya jika satu request > 5 menit
workers = 2  # hemat RAM instance kecil (512MB); jangan lebih
worker_tmp_dir = "/dev/shm"  # heartbeat worker di RAM, hindari I/O disk
loglevel = "info"

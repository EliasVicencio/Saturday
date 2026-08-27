#!/bin/bash
set -e

REPO_DIR=/home/ubuntu/Saturday
LOG=/home/ubuntu/deploy.log

echo "========================================" >> $LOG
echo "Despliegue iniciado: $(date)" >> $LOG

cd $REPO_DIR

echo "[1/6] git pull..." >> $LOG
git pull origin main >> $LOG 2>&1

echo "[2/6] Instalando ffmpeg (si no existe)..." >> $LOG
if ! command -v ffmpeg &> /dev/null; then
    sudo apt-get update -qq >> $LOG 2>&1
    sudo apt-get install -y ffmpeg >> $LOG 2>&1
    echo "✅ ffmpeg instalado" >> $LOG
else
    echo "✅ ffmpeg ya instalado" >> $LOG
fi

echo "[3/6] Instalando dependencias backend..." >> $LOG
cd backend
source venv/bin/activate
pip install -r requirements.txt -q >> $LOG 2>&1

echo "[4/6] Buildeando frontend..." >> $LOG
cd ../frontend
sudo chown -R ubuntu:ubuntu dist 2>/dev/null || true
npm install --silent >> $LOG 2>&1
npm run build >> $LOG 2>&1
sudo chown -R www-data:www-data dist
cd ..

echo "[5/6] Actualizando config nginx..." >> $LOG
sudo cp $REPO_DIR/config/saturday.nginx /etc/nginx/sites-available/saturday
sudo nginx -t >> $LOG 2>&1 && sudo systemctl reload nginx || echo "⚠️ Error en config nginx" >> $LOG

echo "[6/6] Reiniciando servicios..." >> $LOG
sudo systemctl restart saturday
sudo systemctl restart saturday-telegram

echo "Despliegue completado: $(date)" >> $LOG
echo "========================================" >> $LOG

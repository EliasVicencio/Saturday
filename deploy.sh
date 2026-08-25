#!/bin/bash
set -e

REPO_DIR=/home/ubuntu/Saturday
LOG=/home/ubuntu/deploy.log

echo "========================================" >> $LOG
echo "Despliegue iniciado: $(date)" >> $LOG

cd $REPO_DIR

echo "[1/4] git pull..." >> $LOG
git pull origin main >> $LOG 2>&1

echo "[2/4] Instalando dependencias backend..." >> $LOG
cd backend
source venv/bin/activate
pip install -r requirements.txt -q >> $LOG 2>&1

echo "[3/4] Buildeando frontend..." >> $LOG
cd ../frontend
sudo chown -R ubuntu:ubuntu dist 2>/dev/null || true
npm install --silent >> $LOG 2>&1
npm run build >> $LOG 2>&1
sudo chown -R www-data:www-data dist
cd ..

echo "[4/4] Reiniciando backend..." >> $LOG
sudo systemctl restart saturday

echo "Despliegue completado: $(date)" >> $LOG
echo "========================================" >> $LOG

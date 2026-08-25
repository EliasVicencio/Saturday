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
npm install --silent >> $LOG 2>&1
npm run build >> $LOG 2>&1
cd ..

echo "[4/4] Ajustando permisos y reiniciando..." >> $LOG
sudo chown -R www-data:www-data frontend/dist
sudo systemctl restart saturday

echo "Despliegue completado: $(date)" >> $LOG
echo "========================================" >> $LOG

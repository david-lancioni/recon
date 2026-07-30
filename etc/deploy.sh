#!/bin/bash
clear

#
# Colocar esse arquivo no diretorio /home/dlancioni/www
#
set -e

# Configuração dos caminhos
DATE_TIME=$(date +%Y%m%d_%H%M) # Formato YYYYMMDD_HHMM
BACKUP_SOURCE="/home/dlancioni/www/recon"
BACKUP_DIR="/home/dlancioni/www/bkp"
BACKUP_TARGET="${BACKUP_DIR}/recon_${DATE_TIME}"
BACKUP_KEEP=3

echo "📂 Create target folder..."
mkdir -p "$BACKUP_TARGET"

echo "📋 Copying '$BACKUP_SOURCE' to '$BACKUP_TARGET'..."
cp -r "$BACKUP_SOURCE" "$BACKUP_TARGET"

echo "🧹 Keeping only the $BACKUP_KEEP most recent backups..."
ls -1dt "${BACKUP_DIR}"/recon_*/ 2>/dev/null | tail -n +$((BACKUP_KEEP + 1)) | xargs -r rm -rf --

echo "🔄 Executing git pull in the repository..."
git -C "$BACKUP_SOURCE" pull

echo "🗑️ Removing 'etc' folder from the repository..."
rm -rf "${BACKUP_SOURCE}/etc"

echo "🗑️ Removing '__pycache__' folders from the repository..."
find "$BACKUP_SOURCE" -type d -name "__pycache__" -exec rm -rf {} +

echo "🚀 Restarting application (touch wsgi)..."
touch /var/www/www_recon_app_br_wsgi.py

echo "✅ Process completed successfully!"
#!/bin/bash
clear

# Colocar esse arquivo no diretorio /home/dlancioni/
# Interrompe o script se ocorrer qualquer erro
set -e

# Configuração dos caminhos
DATE_TIME=$(date +%Y%m%d_%H%M) # Formato YYYYMMDD_HHMM
BACKUP_SOURCE="/home/dlancioni/www/recon"
BACKUP_TARGET="/home/dlancioni/bkp"
BACKUP_TARGET="${BACKUP_TARGET}/recon_${DATE_TIME}"

echo "📂 Create target folder..."
mkdir -p "$BACKUP_TARGET"

echo "📋 Copying '$BACKUP_SOURCE' to '$BACKUP_TARGET'..."
cp -r "$BACKUP_SOURCE" "$BACKUP_TARGET"

echo "🔄 Executing git pull in the repository..."
git -C "$BACKUP_SOURCE" pull

echo "🗑️ Removing 'etc' folder from the repository..."
rm -rf "${BACKUP_SOURCE}/etc"

echo "🗑️ Removing '__pycache__' folders from the repository..."
find "$BACKUP_SOURCE" -type d -name "__pycache__" -exec rm -rf {} +

echo "✅ Process completed successfully!"
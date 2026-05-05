#!/bin/bash
echo "🚀 Spúšťam manuálne nasadenie platformy CongoLang na Firebase Hosting..."
# Vyžaduje prihlásenie (firebase login)
firebase deploy --only hosting
echo "✅ Nasadenie úspešné!"

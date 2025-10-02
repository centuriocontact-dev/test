#!/usr/bin/env python3
"""
frontend/serve.py
Serveur de développement simple pour tester l'interface
"""

import http.server
import socketserver
import os
import sys
from urllib.parse import urlparse
import json

PORT = 3000
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class SPAHandler(http.server.SimpleHTTPRequestHandler):
    """Handler pour Single Page Application"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)
    
    def do_GET(self):
        """Gérer les requêtes GET - toujours retourner index.html pour le routing SPA"""
        parsed_path = urlparse(self.path)
        
        # Si c'est un fichier statique qui existe, le servir
        file_path = os.path.join(DIRECTORY, parsed_path.path[1:])
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return http.server.SimpleHTTPRequestHandler.do_GET(self)
        
        # Sinon, servir index.html pour le routing SPA
        self.path = '/index.html'
        return http.server.SimpleHTTPRequestHandler.do_GET(self)
    
    def end_headers(self):
        """Ajouter les headers CORS pour le développement"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

def main():
    """Démarrer le serveur"""
    os.chdir(DIRECTORY)
    
    with socketserver.TCPServer(("", PORT), SPAHandler) as httpd:
        print(f"""
╔════════════════════════════════════════════════╗
║       Matching Intérim Pro - Interface Web      ║
╚════════════════════════════════════════════════╝

📱 Serveur démarré sur:
   
   • Local:    http://localhost:{PORT}
   • Réseau:   http://{get_ip()}:{PORT}
   
🎯 Endpoints disponibles:
   • /              → Page de login
   • /#dashboard    → Tableau de bord
   • /#upload       → Upload fichiers
   • /#matching     → Configuration matching
   • /#results      → Résultats

📝 Comptes de test:
   • Email: user@client1.com
   • Pass:  User123!

⌨️  Appuyez sur Ctrl+C pour arrêter le serveur
        """)
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n👋 Serveur arrêté")
            sys.exit(0)

def get_ip():
    """Obtenir l'IP locale"""
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

if __name__ == "__main__":
    main()
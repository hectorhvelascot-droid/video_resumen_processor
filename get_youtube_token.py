import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow

# The exact scopes we need to view and manage YouTube playlists
SCOPES = ['https://www.googleapis.com/auth/youtube']

def main():
    # Expects client_secret.json in the same directory
    if not os.path.exists('client_secret.json'):
        print("❌ Error: No se encontró 'client_secret.json'.")
        print("Por favor descarga tus credenciales de Google Cloud Console y nómbralas 'client_secret.json'.")
        return

    print("🚀 Iniciando el proceso de autenticación de Google...")
    
    flow = InstalledAppFlow.from_client_secrets_file(
        'client_secret.json', SCOPES)
    
    # Run the local server flow with prompt='consent' to ensure we get a refresh_token
    creds = flow.run_local_server(
        port=0, 
        authorization_prompt_service_parameters={'prompt': 'consent', 'access_type': 'offline'}
    )

    print("\n✅ Autenticación exitosa!\n")
    print("Guarda este Refresh Token en las variables de entorno de Render como YT_REFRESH_TOKEN:")
    print("=" * 60)
    print(creds.refresh_token)
    print("=" * 60)
    
    # We will also print the Client ID and Client Secret in case they don't have them handy
    client_config = json.load(open('client_secret.json'))
    try:
        web_or_installed = "web" if "web" in client_config else "installed"
        print("\nTambién necesitarás estos en Render (ya los tienes en el JSON pero aquí están a la mano):")
        print(f"YT_CLIENT_ID:     {client_config[web_or_installed]['client_id']}")
        print(f"YT_CLIENT_SECRET: {client_config[web_or_installed]['client_secret']}")
    except Exception as e:
         pass


if __name__ == '__main__':
    main()

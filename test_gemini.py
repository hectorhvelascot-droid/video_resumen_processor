"""
Test rápido de la API key de Gemini
Ejecutar: python test_gemini.py TU_API_KEY
"""
import sys
import requests
import json

def test_gemini_key(api_key):
    print("=" * 60)
    print("🔍 DIAGNÓSTICO DE API KEY DE GEMINI")
    print("=" * 60)
    
    # Test 1: Listar modelos disponibles (endpoint más básico)
    print("\n📋 Test 1: Listando modelos disponibles...")
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
        response = requests.get(url, timeout=15)
        print(f"   Status HTTP: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            models = [m['name'] for m in data.get('models', []) if 'gemini' in m['name'].lower()]
            print(f"   ✅ API Key VÁLIDA - {len(models)} modelos Gemini disponibles")
            for m in models[:5]:
                print(f"      - {m}")
            if len(models) > 5:
                print(f"      ... y {len(models) - 5} más")
        else:
            error = response.json()
            print(f"   ❌ Error: {json.dumps(error, indent=2)}")
            return False
    except Exception as e:
        print(f"   ❌ Error de conexión: {e}")
        return False
    
    # Test 2: Generar contenido simple con v1beta
    print("\n🤖 Test 2: Generando contenido con v1beta/gemini-2.0-flash...")
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": "Responde solo con: Hola, funciono correctamente."}]}]
        }
        response = requests.post(url, json=payload, timeout=30)
        print(f"   Status HTTP: {response.status_code}")
        data = response.json()
        
        if response.status_code == 200 and 'candidates' in data:
            text = data['candidates'][0]['content']['parts'][0]['text']
            print(f"   ✅ Respuesta: {text.strip()}")
        else:
            print(f"   ❌ Error: {json.dumps(data, indent=2)}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Generar contenido con v1 (endpoint original)
    print("\n🤖 Test 3: Generando contenido con v1/gemini-2.0-flash...")
    try:
        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": "Responde solo con: Hola, funciono correctamente."}]}]
        }
        response = requests.post(url, json=payload, timeout=30)
        print(f"   Status HTTP: {response.status_code}")
        data = response.json()
        
        if response.status_code == 200 and 'candidates' in data:
            text = data['candidates'][0]['content']['parts'][0]['text']
            print(f"   ✅ Respuesta: {text.strip()}")
        else:
            print(f"   ❌ Error: {json.dumps(data, indent=2)}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 4: Probar gemini-1.5-flash como alternativa
    print("\n🤖 Test 4: Probando gemini-1.5-flash como alternativa...")
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": "Responde solo con: Hola, funciono correctamente."}]}]
        }
        response = requests.post(url, json=payload, timeout=30)
        print(f"   Status HTTP: {response.status_code}")
        data = response.json()
        
        if response.status_code == 200 and 'candidates' in data:
            text = data['candidates'][0]['content']['parts'][0]['text']
            print(f"   ✅ Respuesta: {text.strip()}")
        else:
            print(f"   ❌ Error: {json.dumps(data, indent=2)}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Resumen
    print("\n" + "=" * 60)
    print("📊 RESUMEN")
    print("=" * 60)
    print(f"   API Key (primeros 10 chars): {api_key[:10]}...")
    print(f"   Longitud: {len(api_key)} caracteres")
    print()
    print("Si todos los tests pasaron ✅: Tu API key funciona desde tu ubicación.")
    print("Si falló con 'location not supported': El problema es tu ubicación/IP.")
    print("Si falló con 'API key not valid': Necesitas generar una nueva API key.")
    print()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        api_key = input("Ingresa tu GEMINI API KEY: ").strip()
    else:
        api_key = sys.argv[1].strip()
    
    if not api_key:
        print("❌ No se proporcionó API key")
        sys.exit(1)
    
    test_gemini_key(api_key)

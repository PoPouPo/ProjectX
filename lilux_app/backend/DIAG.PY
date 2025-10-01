def diagnostic_complet():
    """Test complet de diagnostic"""
    import requests
    import time
    import hmac
    import hashlib
    import urllib.parse
    from config import Config
    
    print("🩺 DIAGNOSTIC COMPLET BINANCE API")
    print("=" * 50)
    
    # 1. Test de connectivité basique
    print("1. 🔌 Test connectivité réseau...")
    try:
        response = requests.get("https://api.binance.com/api/v3/ping", timeout=10)
        print(f"   ✅ Ping: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Erreur réseau: {e}")
        return False
    
    # 2. Test endpoint public
    print("2. 📡 Test endpoint public...")
    try:
        response = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Prix BTC: {data.get('price')}")
        else:
            print(f"   ❌ Erreur: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    # 3. Vérification clés
    print("3. 🔑 Vérification clés API...")
    print(f"   API Key: {Config.BINANCE_API_KEY[:20]}... ({len(Config.BINANCE_API_KEY)} chars)")
    print(f"   Secret: {Config.BINANCE_API_SECRET[:20]}... ({len(Config.BINANCE_API_SECRET)} chars)")
    
    # 4. Test signature manuelle
    print("4. 🖋️ Test signature manuelle...")
    try:
        timestamp = int(time.time() * 1000)
        query_string = f"timestamp={timestamp}"
        
        signature = hmac.new(
            Config.BINANCE_API_SECRET.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        print(f"   ✅ Signature générée: {signature[:20]}...")
        
        # Test avec la requête la plus simple
        url = f"https://api.binance.com/api/v3/account?{query_string}&signature={signature}"
        headers = {'X-MBX-APIKEY': Config.BINANCE_API_KEY}
        
        response = requests.get(url, headers=headers, timeout=10)
        print(f"   📡 Response: {response.status_code} - {response.text}")
        
        if response.status_code == 200:
            print("   🎉 SUCCÈS! Les clés fonctionnent!")
            return True
        else:
            print("   ❌ ÉCHEC! Les clés sont invalides")
            return False
            
    except Exception as e:
        print(f"   ❌ Erreur test: {e}")
        return False

# Exécutez ce test
diagnostic_complet()
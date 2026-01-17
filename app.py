def limpiar_monto_argentino(texto):
    """Lógica agresiva para formatos contables argentinos"""
    if pd.isna(texto): return 0.0
    s = str(texto).strip()
    
    # Si el número viene como '1.079.532.901,33'
    # 1. Quitamos los puntos de miles
    s = s.replace('.', '')
    # 2. Cambiamos la coma decimal por punto
    s = s.replace(',', '.')
    
    # 3. Limpieza final de cualquier otro símbolo ($ o espacios)
    s = re.sub(r'[^0-9.]', '', s)
    
    try:
        return float(s)
    except:
        return 0.0

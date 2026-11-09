from pathlib import Path
import pandas as pd


RAIZ = Path(__file__).resolve().parents[2]


def corregir_datos():
    # Leer como texto conserva identificadores y el resto de valores del CSV.
    original = pd.read_csv(RAIZ / "datos_completos.csv", dtype=str, keep_default_na=False)
    hu5 = pd.read_csv(RAIZ / "datos_completos_clusters.csv", dtype=str, keep_default_na=False)
    datos = hu5.copy()
    assert len(original) == len(datos) == 392
    assert original.nregistro.is_unique and original.nregistro.ne("").all()
    assert original.nregistro.str.lstrip("0").equals(datos.nregistro.str.lstrip("0"))
    assert datos.cluster.value_counts().to_dict() == {"0": 108, "1": 9, "2": 275}
    otras = [c for c in original.columns if c not in ["nregistro", "estado_aut", "estado_rev"]]
    pd.testing.assert_frame_equal(original[otras], datos[otras])

    datos["nregistro"] = original["nregistro"]
    for columna in ["estado_aut", "estado_rev"]:
        valores = original[columna].replace("", None)
        fechas = pd.to_datetime(pd.to_numeric(valores, errors="raise"), unit="ms", utc=True)
        assert fechas.notna().equals(valores.notna())
        datos[columna] = fechas.dt.tz_convert("Europe/Madrid").dt.strftime("%Y-%m-%d %H:%M:%S").fillna("")

    pd.testing.assert_frame_equal(hu5[otras + ["cluster"]], datos[otras + ["cluster"]])
    destino = RAIZ / "datos_completos_clusters_corregido.csv"
    datos.to_csv(destino, index=False)
    pd.testing.assert_frame_equal(datos, pd.read_csv(destino, dtype=str, keep_default_na=False))
    print("CSV corregido y verificado: 392 medicamentos; clusters 108, 9 y 275.")
    return datos


if __name__ == "__main__":
    corregir_datos()

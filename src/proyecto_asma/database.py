import os
from pathlib import Path

import mysql.connector
import pandas as pd
from dotenv import load_dotenv
from corregir_datos import corregir_datos

RAIZ = Path(__file__).resolve().parents[2]

# Generar el CSV con fechas e identificadores corregidos.
corregir_datos()

df = pd.read_csv(
    RAIZ / "datos_completos_clusters_corregido.csv",
    dtype={"nregistro": str, "cn": str}
)

# Conectar con MySQL.
load_dotenv(RAIZ / ".env")

conexion = mysql.connector.connect(
    host="127.0.0.1",
    port=3306,
    user="root",
    password=os.getenv("DB_PASSWORD"),
    connection_timeout=10
)

cursor = conexion.cursor()

try:
    cursor.execute("CREATE DATABASE IF NOT EXISTS medicamentos_asma")
    cursor.execute("USE medicamentos_asma")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS medicamentos (
            nregistro VARCHAR(20) PRIMARY KEY,
            nombre VARCHAR(500),
            pactivos VARCHAR(500),
            labtitular VARCHAR(255),
            labcomercializador VARCHAR(255),
            cn VARCHAR(20),
            dosis VARCHAR(255),
            formaFarmaceuticaSimplificada VARCHAR(100),
            estado_aut DATETIME,
            estado_rev DATETIME NULL,
            viasAdministracion VARCHAR(255),
            comerc BOOLEAN,
            receta BOOLEAN,
            generico BOOLEAN,
            conduc BOOLEAN,
            triangulo BOOLEAN,
            huerfano BOOLEAN,
            biosimilar BOOLEAN,
            url_html_ficha_tecnica VARCHAR(500),
            url_foto_materiales VARCHAR(500),
            num_registros_atc INT,
            num_principios_activos INT,
            n_palabras INT,
            n_tablas INT,
            n_graves INT,
            estado_nomenclator VARCHAR(100),
            pvp_iva DECIMAL(10,2),
            precio_referencia DECIMAL(10,2),
            tratamiento_larga_duracion VARCHAR(10),
            especial_control_medico VARCHAR(10),
            cluster INT
        )
    """)

    # Verificar el tipo del identificador en tablas existentes.
    cursor.execute("SHOW COLUMNS FROM medicamentos LIKE 'nregistro'")
    if cursor.fetchone()[1].lower() != "varchar(20)":
        raise ValueError("nregistro debe ser VARCHAR(20)")

    # Columnas que vamos a importar.
    columnas = [
        "nregistro",
        "nombre",
        "pactivos",
        "labtitular",
        "labcomercializador",
        "cn",
        "dosis",
        "formaFarmaceuticaSimplificada",
        "estado_aut",
        "estado_rev",
        "viasAdministracion",
        "comerc",
        "receta",
        "generico",
        "conduc",
        "triangulo",
        "huerfano",
        "biosimilar",
        "url_html_ficha_tecnica",
        "url_foto_materiales",
        "num_registros_atc",
        "num_principios_activos",
        "n_palabras",
        "n_tablas",
        "n_graves",
        "estado_nomenclator",
        "pvp_iva",
        "precio_referencia",
        "tratamiento_larga_duracion",
        "especial_control_medico",
        "cluster"
    ]

    datos = df[columnas].astype(object)
    datos = datos.where(pd.notna(datos), None).values.tolist()

    nombres = ", ".join(columnas)
    valores = ", ".join(["%s"] * len(columnas))

    # Actualizar registros existentes sin duplicarlos.
    actualizaciones = ", ".join(
        f"{c} = VALUES({c})"
        for c in columnas
        if c != "nregistro"
    )

    consulta = f"""
        INSERT INTO medicamentos ({nombres})
        VALUES ({valores})
        ON DUPLICATE KEY UPDATE {actualizaciones}
    """

    cursor.executemany(consulta, datos)

    # Comprobar que se mantienen los 392 medicamentos.
    cursor.execute("SELECT COUNT(*) FROM medicamentos")

    if cursor.fetchone()[0] != 392:
        raise ValueError("La tabla debe contener 392 medicamentos")

    conexion.commit()

    # Crear o actualizar la vista con los KPI.
    sql = (
        RAIZ / "src/proyecto_asma/sql/KPIs.sql"
    ).read_text(encoding="utf-8")

    cursor.execute(sql)

    cursor.execute("SELECT COUNT(*) FROM vista_kpis")

    if cursor.fetchone()[0] != 392:
        raise ValueError("La vista debe contener 392 medicamentos")

    print("HU6 completada: 392 medicamentos y vista_kpis actualizada.")

except Exception:
    conexion.rollback()
    raise

finally:
    cursor.close()
    conexion.close()

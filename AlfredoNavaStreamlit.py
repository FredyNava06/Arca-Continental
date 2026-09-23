import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt


# =========================================================
# CONFIGURACIÓN GENERAL
# =========================================================

st.title("Reporte de Merma")


# =========================================================
# CARGA DEL ARCHIVO
# =========================================================

uploaded_file = st.file_uploader(
    "Selecciona archivo Excel",
    type=["xlsx"]
)


# El resto de la aplicación solo aparece si existe un archivo
if uploaded_file is not None:

    # Leer únicamente la estructura del archivo
    xls = pd.ExcelFile(uploaded_file)
    hojas = xls.sheet_names

    st.success(f"Archivo cargado: {uploaded_file.name}")

    st.write("### Hojas encontradas")

    for h in hojas:
        st.write(f"• {h}")


    # =====================================================
    # VALORES SUGERIDOS PARA LAS HOJAS
    # =====================================================

    default_merma = (
        "Base de Datos"
        if "Base de Datos" in hojas
        else hojas[0]
    )

    default_produccion = (
        "Produccion"
        if "Produccion" in hojas
        else hojas[0]
    )


    # =====================================================
    # PARÁMETROS
    # =====================================================

    Hoja_Merma = st.selectbox(
        "Hoja Merma",
        hojas,
        index=hojas.index(default_merma)
    )

    Hoja_Produccion = st.selectbox(
        "Hoja Producción",
        hojas,
        index=hojas.index(default_produccion)
    )

    Año = st.number_input(
        "Año",
        value=2026,
        step=1
    )

    Semana = st.text_input(
        "Semana",
        value="",
        placeholder="Ejemplo: 28"
    )

    generar = st.button(
        "Generar Reporte",
        type="primary"
    )


    # =====================================================
    # GENERACIÓN DEL REPORTE
    # =====================================================

    if generar:

        # -------------------------------------------------
        # VALIDACIÓN DE SEMANA
        # -------------------------------------------------

        if Semana.strip() == "":
            st.error("Debes capturar una semana.")
            st.stop()

        try:
            Semana = int(Semana)
        except ValueError:
            st.error("La semana debe ser un número entero.")
            st.stop()

        if Semana < 1 or Semana > 53:
            st.error("La semana debe estar entre 1 y 53.")
            st.stop()


        # -------------------------------------------------
        # PARÁMETROS SELECCIONADOS
        # -------------------------------------------------

        st.write("### Parámetros seleccionados")
        st.write(f"Archivo: {uploaded_file.name}")
        st.write(f"Hoja merma: {Hoja_Merma}")
        st.write(f"Hoja producción: {Hoja_Produccion}")
        st.write(f"Año: {Año}")
        st.write(f"Semana: {Semana}")


        # =================================================
        # LECTURA Y LIMPIEZA DE PRODUCCIÓN
        # =================================================

        uploaded_file.seek(0)

        ds = pd.read_excel(
            uploaded_file,
            sheet_name=Hoja_Produccion
        )

        ds["Kg merma"] = pd.to_numeric(
            ds["Kg merma"],
            errors="coerce"
        )

        ds["Kg produccion"] = pd.to_numeric(
            ds["Kg produccion"],
            errors="coerce"
        )

        list_lineas_produccion = list(
            ds["Linea"].dropna().unique()
        )

        ds.drop_duplicates(
            inplace=True,
            ignore_index=True
        )


        # =================================================
        # LECTURA Y LIMPIEZA DE MERMA
        # =================================================

        uploaded_file.seek(0)

        df = pd.read_excel(
            uploaded_file,
            sheet_name=Hoja_Merma
        )

        df["Fecha"] = pd.to_datetime(
            df["Fecha"],
            format="%d/%m/%Y",
            errors="coerce"
        )

        df["Kg merma"] = pd.to_numeric(
            df["Kg merma"],
            errors="coerce"
        )

        df["Costo"] = pd.to_numeric(
            df["Costo"],
            errors="coerce"
        )

        df["Estacion"] = (
            df["Estacion"]
            .str.strip()
            .str.normalize("NFKD")
            .str.encode("ascii", errors="ignore")
            .str.decode("utf-8")
            .str.title()
        )

        df["Motivo merma"] = (
            df["Motivo merma"]
            .str.strip()
            .str.normalize("NFKD")
            .str.encode("ascii", errors="ignore")
            .str.decode("utf-8")
            .str.title()
        )

        list_lineas_merma = list(
            df["Linea"].dropna().unique()
        )

        df.drop_duplicates(
            inplace=True,
            ignore_index=True
        )


        # =================================================
        # RESUMEN POR LÍNEA
        # =================================================

        st.header("Resumen por línea")

        for linea in list_lineas_produccion:

            # ---------------------------------------------
            # SECCIÓN 1: RESUMEN DE PRODUCCIÓN
            # ---------------------------------------------

            p = ds[
                (ds["Año"] == Año) &
                (ds["Semana"] == Semana) &
                (ds["Linea"] == linea)
            ]

            kg_prod = p["Kg produccion"].sum()
            kg_merma_prod = p["Kg merma"].sum()

            proporcion = round(
                (
                    kg_merma_prod
                    / kg_prod
                    * 100
                )
                if kg_prod > 0
                else 0,
                2
            )

            costo = round(
                (kg_merma_prod / 0.07) * 4.20,
                2
            )


            # ---------------------------------------------
            # SECCIÓN 2: TOP 3 ESTACIONES
            # ---------------------------------------------

            m = df[
                (df["Año"] == Año) &
                (df["Semana"] == Semana) &
                (df["Linea"] == linea)
            ]

            top_estaciones = (
                m.groupby("Estacion")["Kg merma"]
                .sum()
                .nlargest(3)
            )

            sin_clasificar_est = (
                m[m["Estacion"].isna()]
                ["Kg merma"]
                .sum()
            )


            # ---------------------------------------------
            # SECCIÓN 3: TOP 3 MOTIVOS
            # ---------------------------------------------

            top_motivos = (
                m.groupby("Motivo merma")["Kg merma"]
                .sum()
                .nlargest(3)
            )

            sin_clasificar_mot = (
                m[m["Motivo merma"].isna()]
                ["Kg merma"]
                .sum()
            )


            # ---------------------------------------------
            # PRESENTACIÓN DEL RESUMEN
            # ---------------------------------------------

            st.markdown("---")
            st.subheader(str(linea).upper())

            st.write("### RESUMEN")
            st.write(f"Kg producidos: {kg_prod:,.2f} kg")
            st.write(f"Kg merma: {kg_merma_prod:,.2f} kg")
            st.write(f"Proporción: {proporcion}%")
            st.write(f"Costo: ${costo:,.2f} pesos")

            st.write("### PRINCIPAL ESTACIÓN (Top 3)")

            for est, kg in top_estaciones.items():
                st.write(f"{est}: {kg:,.2f} kg")

            st.write(
                f"Sin clasificar: "
                f"{sin_clasificar_est:,.2f} kg"
            )

            st.write("### PRINCIPAL MOTIVO (Top 3)")

            for mot, kg in top_motivos.items():
                st.write(f"{mot}: {kg:,.2f} kg")

            st.write(
                f"Sin clasificar: "
                f"{sin_clasificar_mot:,.2f} kg"
            )


        # =================================================
        # CONFIGURACIÓN DE GRÁFICAS
        # =================================================

        plt.rcParams.update({
            "font.family": "DejaVu Sans",
            "font.size": 11,
            "axes.spines.top": False,
            "axes.spines.right": False,
        })

        COLOR_AC = "#C31F39"
        COLOR_CAFE = "#6A2E1F"
        COLOR_GRIS = "#CCCCCC"


        # =================================================
        # GRÁFICAS POR LÍNEA
        # =================================================

        st.header("Gráficas por línea")

        for linea in list_lineas_produccion:

            m = df[
                (df["Año"] == Año) &
                (df["Semana"] == Semana) &
                (df["Linea"] == linea)
            ]

            if m.empty:
                st.warning(
                    f"{linea}: sin datos de merma, se omite."
                )
                continue

            st.markdown("---")
            st.subheader(str(linea).upper())

            # ─────────────────────────────────────────────
            # GRÁFICO 1:
            # MERMA POR ESTACIÓN — TOP 7
            # ─────────────────────────────────────────────

            data_est = (
                m.groupby("Estacion")["Kg merma"]
                .sum()
                .nlargest(7)
                .sort_values(ascending=True)
            )

            fig, ax = plt.subplots(figsize=(10, 6))

            bars = ax.barh(
                data_est.index,
                data_est.values,
                color=COLOR_AC,
                height=0.6
            )

            for bar in bars:
                w = bar.get_width()

                ax.text(
                    w + 5,
                    bar.get_y() + bar.get_height() / 2,
                    f"{w:,.1f} kg",
                    va="center",
                    fontsize=10,
                    color="#333333"
                )

            ax.set_title(
                (
                    f"{str(linea).upper()} — "
                    f"Merma por Estación "
                    f"(Semana {Semana})"
                ),
                fontsize=14,
                fontweight="bold",
                color="#222222"
            )

            ax.set_xlabel(
                "Kg merma",
                fontsize=11,
                color="#555555"
            )

            ax.set_facecolor("white")
            fig.tight_layout()

            st.pyplot(fig)

            plt.close(fig)

            # ─────────────────────────────────────────────
            # GRÁFICO 2:
            # MERMA POR MOTIVO — TOP 5
            # ─────────────────────────────────────────────

            data_mot = (
                m.groupby("Motivo merma")["Kg merma"]
                .sum()
                .nlargest(5)
                .sort_values(ascending=True)
            )

            fig, ax = plt.subplots(figsize=(10, 6))

            bars = ax.barh(
                data_mot.index,
                data_mot.values,
                color=COLOR_CAFE,
                height=0.6
            )

            for bar in bars:
                w = bar.get_width()

                ax.text(
                    w + 5,
                    bar.get_y() + bar.get_height() / 2,
                    f"{w:,.1f} kg",
                    va="center",
                    fontsize=10,
                    color="#333333"
                )

            ax.set_title(
                (
                    f"{str(linea).upper()} — "
                    f"Merma por Motivo "
                    f"(Semana {Semana})"
                ),
                fontsize=14,
                fontweight="bold",
                color="#222222"
            )

            ax.set_xlabel(
                "Kg merma",
                fontsize=11,
                color="#555555"
            )

            ax.set_facecolor("white")
            fig.tight_layout()

            st.pyplot(fig)

            plt.close(fig)
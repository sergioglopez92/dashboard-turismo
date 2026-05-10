import pandas as pd
import altair as alt

# 1. Configuración Inicial
alt.data_transformers.disable_max_rows()

# Cargar datos
df = pd.read_excel('Resultados_Airbnb.xlsx')

# Limpiar datos ciudad 
df['city'] = df['city'].str.strip()

# Asegurar formato fecha
df['checkin_date'] = pd.to_datetime(df['checkin_date'])


# REDUCCIÓN DE PESO PARA PODER SUBIR A GITHUB
# 1. Solo columnas usadas en la visualización
columnas_necesarias = [
    'city', 'price', 'checkin_date', 'days_ahead', 
    'dist_centro_km', 'guests', 'tiene_piscina', 
    'tiene_parking', 'tiene_vistas', 'tiene_terraza_balcon'
]

# Optimización (redondeo)
df = df[columnas_necesarias].copy()
df['price'] = df['price'].round(2)
df['dist_centro_km'] = df['dist_centro_km'].round(3)


# ---------------------------------------------------------
# PALETAS DE COLORES
# ---------------------------------------------------------
# Colores fijos: Toledo (Azul oscuro), San Sebastian (Naranja), Valencia (Verde), Malaga (Rojo)
escala_ciudades = alt.Scale(
    domain=['Toledo', 'San Sebastian', 'Valencia', 'Malaga'],
    range=['#2A4B7C', '#E27602', '#448D65', '#C43B4B']
)
escala_extras = alt.Scale(domain=['Con', 'Sin'], range=['#66c2a5', '#fc8d62']) 

def cabecera(titulo, subtitulo):
    return alt.Chart().mark_text().encode().properties(
        title=alt.TitleParams(
            text=titulo,
            subtitle=subtitulo,
            fontSize=28,
            subtitleFontSize=16,
            anchor='start',
            color="#723B00", 
            subtitleColor='#555555',
            offset=20
        )
    )

############################################################
# A.ANÁLISIS TEMPORAL
############################################################

# ---------------------------------------------------------
# A1. Dinámica de Precios: Antelación vs. Estacionalidad
# ---------------------------------------------------------

heatmap_temporal = alt.Chart(df).mark_rect().encode(
    x=alt.X('yearmonth(checkin_date):O', title='Mes de Check-in', axis=alt.Axis(labelAngle=-45)),
    y=alt.Y('days_ahead:O', title='Días de Antelación', sort='descending'),
    color=alt.Color('mean(price):Q', title='Precio Medio (€)', scale=alt.Scale(range=['#fee6ce', '#fc8d62', '#d94801'])),
    tooltip=[
        alt.Tooltip('yearmonth(checkin_date):O', title='Fecha'),
        alt.Tooltip('days_ahead:O', title='Antelación (días)'),
        alt.Tooltip('mean(price):Q', title='Precio Medio (€)', format='.2f')
    ]
).properties(
    title=alt.TitleParams(
        text='Dinámica de Precios: Antelación vs. Estacionalidad',
        subtitle='Análisis del impacto de la ventana de reserva en el coste medio por noche',
        anchor='start',
        dx=30      
    ),
    width=600,
    height=300
)

heatmap_temporal.save('A1_analisis_temporal.html')

# ---------------------------------------------------------
# A2. Evolución Tarifaria según Ventana de Reserva
# ---------------------------------------------------------

mis_ciudades = ['Toledo', 'San Sebastian', 'Valencia', 'Malaga']

# Se crea un dataframe manual para el menú
df_menu_manual = pd.DataFrame({'city': mis_ciudades})

selector_ciudad = alt.selection_point(
    fields=['city'], 
    name='filtro_mercado',
    empty='all'
)

menu_ciudades = alt.Chart(df_menu_manual).mark_rect(cornerRadius=5).encode(
    y=alt.Y('city:N', title=None, axis=alt.Axis(orient='right')),
    color=alt.condition(
        selector_ciudad, 
        alt.Color('city:N', scale=escala_ciudades, legend=None), 
        alt.value('#e6e6e6')
    )
).properties(width=40, height=160).add_params(selector_ciudad)

columnas_agrupadas = alt.Chart(df).mark_bar().encode(
    x=alt.X('yearmonth(checkin_date):O', title='Mes de Check-in', axis=alt.Axis(labelAngle=-45)),
    y=alt.Y('mean(price):Q', title='Precio Medio (€)'),
    xOffset=alt.XOffset('days_ahead:N', sort=[60, 30, 14]),
    color=alt.Color('days_ahead:N', title='Antelación', scale=alt.Scale(range=['#fee6ce', '#fc8d62', '#d94801']), sort=[60, 30, 14]),
    tooltip=['city', 'days_ahead:N', alt.Tooltip('mean(price):Q', format='.2f')]
).properties(width=500, height=300).transform_filter(selector_ciudad)

bloque_a2_interactivo = alt.hconcat(columnas_agrupadas, menu_ciudades).resolve_scale(
    color='independent'
).properties(
    title=alt.TitleParams(
        text='Evolución Tarifaria según Ventana de Reserva',
        subtitle='Desglose mensual del precio medio para antelaciones de 60, 30 y 14 días',
        anchor='start'     
    )
)

bloque_a2_interactivo.save('A2_analisis_temporal_columnas.html')

############################################################
# B.ANÁLISIS ESPACIAL
############################################################

# ---------------------------------------------------------
# B1. Análisis del Núcleo Urbano: Proximidad y Coste
# ---------------------------------------------------------
df_nucleo_b1 = df[(df['guests'].isin([2, 4])) & (df['dist_centro_km'] <= 2.0)]

# Se definen los puntos exactos donde se quiere que aparezcan las marcas
marcas_distancia = [0, 0.5, 1, 1.5, 2]

seleccion_leyenda = alt.selection_point(fields=['guests'], bind='legend', name='filtro_capacidad')

scatter_ciudades = alt.Chart(df_nucleo_b1).mark_circle(size=40).encode(
    x=alt.X('dist_centro_km:Q', 
            title='Distancia al Centro',
            scale=alt.Scale(domain=[0, 2]),
            axis=alt.Axis(
                values=marcas_distancia, 
                labelExpr="datum.value + ' km'",
                grid=True
            )), 
    y=alt.Y('price:Q', 
            title='Precio (€)',
            scale=alt.Scale(domain=[0, 1200], clamp=True)),
    color=alt.Color('guests:N', title='Huéspedes', scale=alt.Scale(scheme='set2')),
    opacity=alt.condition(seleccion_leyenda, alt.value(0.7), alt.value(0.1)),
    tooltip=['city', 'price', 'dist_centro_km', 'guests']
).add_params(
    seleccion_leyenda
).properties(
    width=250, height=250
).facet(
    facet=alt.Facet('city:N', title='Ciudad'),
    columns=2
).resolve_axis(
    x='independent' 
).properties(
    title=alt.TitleParams(
        text='Análisis del Núcleo Urbano: Proximidad y Coste',
        subtitle='Correlación entre la distancia al centro histórico y el precio (radio 0-2 km)',
        anchor='start',
        dx=40
    )
)

scatter_ciudades.save('B1_tendencia_nucleo_urbano.html')


# ---------------------------------------------------------
# B2. Curva de Decaimiento de Precios (Modelo LOESS)
# ---------------------------------------------------------

# 1. Filtrado: Alojamientos comparables (2 y 4 huéspedes) en el radio urbano (<= 2 km)
df_nucleo = df[(df['guests'].isin([2, 4])) & (df['dist_centro_km'] <= 2.0)]

# 2. Se generan únicamente las líneas de tendencia suavizadas (sin puntos base)
linea_tendencia_nucleo = alt.Chart(df_nucleo).mark_line(size=3).encode(
    x=alt.X('dist_centro_km:Q', 
            title='Distancia al Centro (km)',
            scale=alt.Scale(domain=[0, 2])), # Marco visual de 0 a 2 km
    y=alt.Y('price:Q', 
            title='Precio Medio (€)', 
            scale=alt.Scale(zero=True)),     
    color=alt.Color('city:N', title='Ciudad', scale=escala_ciudades)
).transform_loess(
    # Modelo LOESS aplicado sobre el subconjunto urbano
    'dist_centro_km', 'price', groupby=['city', 'guests'], bandwidth=0.4
).properties(
    width=350,
    height=300
).facet(
    column=alt.Column('guests:N', title='Capacidad (Huéspedes)')
).properties(
    title=alt.TitleParams(
        text='Curva de Decaimiento de Precios (Modelo LOESS)',
        subtitle='Tendencia suavizada del valor del alojamiento en el primer radio urbano (0-2 km)',
        anchor='start'
    )
)

linea_tendencia_nucleo.save('B2_tendencia_nucleo_urbano.html')


############################################################
# C. IMPACTO CUALITATIVO
############################################################

# ---------------------------------------------------------
# C1. Matriz de Impacto (Centrado y Espaciado Totalmente Corregidos)
# ---------------------------------------------------------

# 1. Se filtra para mantener la coherencia analítica (2 y 4 huéspedes)
df_cualitativo = df[df['guests'].isin([2, 4])]

# 2. Diccionario de variables
variables_extras = {
    'tiene_piscina': 'Piscina', 
    'tiene_parking': 'Parking', 
    'tiene_vistas': 'Vistas', 
    'tiene_terraza_balcon': ['Terraza/', 'Balcón'] 
}

escala_extras = alt.Scale(domain=['Con', 'Sin'], range=['#66c2a5', '#fc8d62']) 

graficos_extras = []

for var, nombre_limpio in variables_extras.items():
    
    # Condicionales para mantener la gráfica limpia
    es_primero = (len(graficos_extras) == 0)
    
    eje_y = alt.Y('price:Q', 
                  title='Precio (€)' if es_primero else None, 
                  scale=alt.Scale(domain=[0, 400], clamp=True),
                  axis=alt.Axis(labels=es_primero, ticks=es_primero, tickMinStep=50))
    
    config_fila = alt.Row('city:N', 
                          title=None, # Se elimina el título "Ciudad" redundante
                          header=alt.Header(
                              title=nombre_limpio,  
                              titleAnchor='middle', 
                              titleOrient='top',   
                              titlePadding=20,     
                              titleFontSize=14,
                              
                              # Control de etiquetas de ciudad (Toledo, etc.)
                              labels=es_primero,
                              labelAngle=0, 
                              labelAlign='left', 
                              labelPadding=15
                          ))

    caja_base = alt.Chart(df_cualitativo).transform_calculate(
        Etiqueta=f"datum.{var} == 1 ? 'Con' : 'Sin'"
    ).mark_boxplot(
        size=30,
        outliers=alt.MarkConfig(opacity=0.2, size=10)
    ).encode(
        x=alt.X('Etiqueta:N', title=None, sort=['Sin', 'Con']),
        y=eje_y,
        color=alt.Color('Etiqueta:N', legend=None, scale=escala_extras)
    ).properties(
        width=90,  
        height=130 
    )
    
    caja_facetada = caja_base.facet(
        row=config_fila 
    )
    
    graficos_extras.append(caja_facetada)

# 3. Se concatenan horizontalmente las columnas facetadas
matriz_cualitativa = alt.hconcat(*graficos_extras, spacing=15).resolve_scale(
    y='shared', color='shared'
).properties(
    title=alt.TitleParams(
        text='Matriz de Impacto Monetario de Servicios Extra',
        subtitle='Comparativa de precios por ciudad para alojamientos de 2 y 4 huéspedes',
        anchor='start',
        offset=30, 
        dx=110
    )
)

matriz_cualitativa.save('C1_matriz_cualitativa_ciudades.html')

# ---------------------------------------------------------
# C2. Extras por Ciudad 
# ---------------------------------------------------------

extras_dict = {
    'tiene_piscina': 'Piscina',
    'tiene_parking': 'Parking',
    'tiene_terraza_balcon': 'Terraza balcón',
    'tiene_vistas': 'Vistas'
}

graficos_d3 = []

for i, (var, nombre) in enumerate(extras_dict.items()):

    es_primero = (i == 0)
    es_ultimo = (i == len(extras_dict) - 1)

    g = alt.Chart(df).transform_calculate(
        Estado=f"datum.{var} == 1 ? 'Con' : 'Sin'"
    ).mark_bar().encode(

        x=alt.X(
            'Estado:N',
            title=None,
            sort=['Sin', 'Con'],
            axis=alt.Axis(
                labels=False,
                ticks=False,
                domain=False
            )
        ),

        y=alt.Y(
            'mean(price):Q',
            title='Precio Medio (€)' if es_primero else None,
            scale=alt.Scale(domain=[0, 350]),
            axis=alt.Axis(
                labels=es_primero,
                ticks=es_primero
            )
        ),

        column=alt.Column(
            'city:N',
            title=None,
            spacing=5,
            header=alt.Header(
                labelOrient='bottom',
                labelAngle=0,
                labelPadding=5,
                labelBaseline='top'
            )
        ),

        color=alt.Color(
            'Estado:N',
            scale=escala_extras,
           legend= None
        ),

        tooltip=[
            'city',
            'Estado:N',
            alt.Tooltip('mean(price):Q', format='.2f')
        ]

    ).properties(
        title=nombre,
        width=55,
        height=180
    )

    graficos_d3.append(g)

leyenda_extras = alt.Chart(pd.DataFrame({'Estado': ['Con', 'Sin']})).mark_rect().encode(
    y=alt.Y('Estado:N', title='Estado', axis=alt.Axis(orient='right')),
    color=alt.Color('Estado:N', scale=escala_extras, legend=None)
).properties(width=30, height=50)

panel_d3 = alt.hconcat(*graficos_d3, leyenda_extras).resolve_scale(
    y='shared', 
    color='independent'
).properties(
    title=alt.TitleParams(
        text='Prima Económica Absoluta de Servicios Extra',
        subtitle='Incremento del precio medio asociado a amenidades de valor añadido por mercado',
        anchor='start',
        dx=50,      
        offset=30
    )
)

panel_d3.save('C2_valor_geografico.html')


############################################################
# D.ANÁLISIS ECONÓMICO
############################################################

# ---------------------------------------------------------
# D1. Distribución de precios por ciudad (Gráfico Único)
# ---------------------------------------------------------

boxplot_ciudades = alt.Chart(df).mark_boxplot(
    outliers=False, 
    size=50 
).encode(
    x=alt.X('city:N', 
            title=None, 
            axis=alt.Axis(labels=True, labelAngle=0)), 
    
    y=alt.Y('price:Q', title='Precio (€)'),
    
    color=alt.Color('city:N', scale=escala_ciudades, legend=None)
).properties(
    title=alt.TitleParams(
        text='Distribución Macroeconómica del Mercado',
        subtitle='Dispersión tarifaria y medianas globales por destino turístico',
        anchor='start',
        dx=30
    ),
    width=300,  
    height=300
)

boxplot_ciudades.save('D1_distribucion_ciudades.html')

# ---------------------------------------------------------
# D2. Estacionalidad + Periodos Vacacionales
# ---------------------------------------------------------

# Se crea un dataframe con periodos aproximados
vacaciones = pd.DataFrame({
    'inicio': pd.to_datetime([
        # --- Festividades Nacionales / Generales ---
        '2026-07-01', # Verano (General)
        '2026-12-20', # Navidad
        '2026-03-27', # Semana Santa (Desde el Viernes de Dolores)
        '2026-02-13', # Carnaval
        
        # --- Hitos Locales Específicos ---
        '2026-06-01', # Corpus Christi (Especialmente crítico en Toledo - Jueves 4 de junio)
        '2026-03-14', # Fallas (Valencia - Días grandes)
        '2026-08-14', # Feria de Málaga (Mediados de agosto)
        '2026-08-08', # Semana Grande / Aste Nagusia (San Sebastián)
        '2026-01-19'  # Tamborrada (San Sebastián - 20 de enero)
    ]),
    'fin': pd.to_datetime([
        '2026-08-31', # Verano
        '2027-01-07', # Navidad
        '2026-04-06', # Semana Santa (Hasta el Lunes de Pascua, festivo en Valencia y País Vasco)
        '2026-02-18', # Carnaval
        '2026-06-07', # Corpus Christi (Fin de semana)
        '2026-03-20', # Fallas
        '2026-08-23', # Feria de Málaga
        '2026-08-16', # Semana Grande (San Sebastián)
        '2026-01-21'  # Tamborrada (San Sebastián)
    ]),
    'evento': [
        'Verano', 
        'Navidad', 
        'Semana Santa', 
        'Carnaval', 
        'Corpus Christi (Toledo)', 
        'Fallas (Valencia)', 
        'Feria de Málaga', 
        'Semana Grande (Sn. Sebastián)',
        'Tamborrada (Sn. Sebastián)'
    ],
    # Se añade una columna para categorizar (opcional, muy útil para dar distinto color en Altair)
    'tipo_evento': [
        'Nacional', 'Nacional', 'Nacional', 'Nacional',
        'Local', 'Local', 'Local', 'Local', 'Local'
    ]
})


# Definición explícita de colores
color_bandas = alt.Color('tipo_evento:N', 
                         scale=alt.Scale(domain=['Nacional', 'Local'], 
                                         range=["#b6b6b6", "#858585"]), 
                         title='Tipo de Evento')

color_ciudades = alt.Color('city:N', 
                           title='Ciudad', 
                           scale=escala_ciudades)

brush = alt.selection_interval(encodings=['x'], name='pincel_temporal')

# Gráficos Base (PANORÁMICA)
lineas_base = alt.Chart(df).mark_line(size=2).encode(
    x=alt.X('checkin_date:T', title='Fecha de Check-in'),
    y=alt.Y('mean(price):Q', title='Precio Medio (€)', scale=alt.Scale(zero=False)),
    color=color_ciudades,
    tooltip=['city', 'checkin_date', alt.Tooltip('mean(price):Q', format='.2f')]
)

bandas_base = alt.Chart(vacaciones).mark_rect(opacity=0.15).encode(
    x='inicio:T',
    x2='fin:T',
    color=color_bandas,
    tooltip=['evento:N', 'tipo_evento:N']
)

panoramica = alt.layer(
    bandas_base, 
    lineas_base
).add_params(
    brush
).resolve_scale(
    color='independent'
).properties(
    title=alt.TitleParams(
        text='Contexto Estacional Anual e Hitos Festivos',
        subtitle='Evolución macroscópica de precios frente al calendario vacacional nacional',
        anchor='start',
        dx=30
    ),
    width=750,
    height=200
)

# Gráficos para el ZOOM (ABRIL - JULIO)
lineas_zoom = alt.Chart(df).mark_line(size=2).encode(
    x=alt.X('checkin_date:T', 
            title='Detalle Temporal',
            scale=alt.Scale(domain=brush)), 
    y=alt.Y('mean(price):Q', title='Precio Medio (€)', scale=alt.Scale(zero=False)),
    color=color_ciudades,
    tooltip=['city', 'checkin_date', alt.Tooltip('mean(price):Q', format='.2f')]
)

bandas_zoom = alt.Chart(vacaciones).mark_rect(opacity=0.15).encode(
    x=alt.X('inicio:T', scale=alt.Scale(domain=brush)), 
    x2='fin:T',
    color=color_bandas,
    tooltip=['evento:N', 'tipo_evento:N']
)

zoom_detalle = alt.layer(
    bandas_zoom, 
    lineas_zoom
).resolve_scale(
    color='independent'
).properties(
    width=750,
    height=400
)

# Texto para el usuario
instruccion_zoom = alt.Chart().mark_text(
    text='👆 Arrastre el cursor sobre el gráfico superior para seleccionar la región temporal que desea ver con zoom',
    size=13,
    color='#666666',
    fontStyle='italic'
).properties(
    width=750,
    height=20 
)

# Concatenación Vertical Final
grafico_final_d2 = alt.vconcat(
    panoramica, 
    instruccion_zoom, 
    zoom_detalle,
    spacing=15 
).resolve_scale(
    x='independent'
)

grafico_final_d2.save('D2_estacionalidad_con_zoom_limpio.html')


############################################################
# MAQUETACIÓN FINAL DEL DASHBOARD (DISEÑO PREMIUM)
############################################################

# --- BLOQUE A: TEMPORAL ---
seccion_a = alt.vconcat(
    cabecera("A. Análisis Temporal", "Impacto de la estacionalidad y la antelación en la formación de precios"),
    alt.hconcat(heatmap_temporal, bloque_a2_interactivo).resolve_scale(color='independent'),
    spacing=40
).resolve_scale(x='independent')

# --- BLOQUE B: ESPACIAL ---
seccion_b = alt.vconcat(
    cabecera("B. Análisis Espacial", "Relación entre la distancia al centro histórico y el valor del inmueble"),
    alt.hconcat(scatter_ciudades, linea_tendencia_nucleo).resolve_scale(color='independent'),
    spacing=40
).resolve_scale(x='independent')

# --- BLOQUE C: CUALITATIVO ---
seccion_c = alt.vconcat(
    cabecera("C. Impacto Cualitativo", "Valoración monetaria de servicios extra y características del alojamiento"),
    matriz_cualitativa,
    panel_d3,
    spacing=50
).resolve_scale(
    color='independent',
    x='independent', 
    y='independent'
)

# --- BLOQUE D: ECONÓMICO ---
seccion_d = alt.vconcat(
    cabecera("D. Análisis Económico", "Distribución interurbana, eventos de alta demanda y comparativa de tipos"),
    boxplot_ciudades,
    grafico_final_d2,
    spacing=50
).resolve_scale(
    color='independent',
    x='independent',
    y='independent'
)

# --- COMPOSICIÓN FINAL DEL CUADRO DE MANDO ---
dashboard_final = alt.vconcat(
    seccion_a,
    seccion_b,
    seccion_c,
    seccion_d,
    spacing=120 
).resolve_scale(
    x='independent', 
    y='independent',
    color='independent'
).configure(
    padding=30
).configure_view(
    stroke=None,
    continuousWidth=160,
    continuousHeight=200
).configure_axis(
    gridColor='#f0f0f0',
    domainColor='#dcdcdc',
    labelFont='Segoe UI, sans-serif',
    titleFont='Segoe UI, sans-serif'
).configure_title(
    font='Segoe UI, sans-serif',
    subtitleColor='#666666'
).configure_legend(
    titleFontSize=12,
    labelFontSize=11,
    symbolSize=100
)

# Guardar el resultado final
dashboard_final.save('DASHBOARD_PROFESIONAL_CIUDADES.html')
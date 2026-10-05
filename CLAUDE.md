# Kaiken Propiedades: área inmobiliaria

Dashboard de estado y proyección del área inmobiliaria de Kaiken (sociedad Importadora Hevia SpA, RUT 76.872.717-1). El área compra activos en oportunidades (remates), los hipoteca y los arrienda. El objetivo es asignarle un valor al área según los flujos que ha generado y generará, con horizonte variable (10, 12, 15 años u otro) y plusvalía variable (1%, 2%, 3% u otra).

## Dónde está cada cosa

- `dashboard/index.html`: fuente del dashboard. Publicado como artifact en https://claude.ai/artifact/PUUrGKBHiGBSbwPUK7sE5W (republicar sobre esa URL, no crear uno nuevo).
- `data/creditos.json`: calendario anual de dividendos y amortización de cada crédito, desde oct 2026 (año 1 = oct 2026 a sep 2027).
- `data/registro_propiedades_v2.xlsx`: registro de propiedades v2 (el que se subió a Drive). Se genera con `scripts/build_registro_v2.py`.
- `scripts/parse_creditos.py`: parser de las pestañas de crédito del Sheet "Detalle propiedades Kaiken".

### Google Drive

- Carpeta del área: `Kaiken - Área Inmobiliaria` (id `1kzy7SUykoKnS6HmL1EQKu2RCt_BABYRR`).
- Subcarpeta `Tasaciones` (id `1-jZyaVEl3PbzgVZexLhEl4UGh5R2oOw6`): PDFs de tasación.
- Sheet fuente del usuario: "Detalle propiedades Kaiken" (id `1ZR8nS2xPH-HojJ_BuwJgkegkpm8lSKQlBtJhOo99eb4`). Ignorar la pestaña "Detalle Arriendo La Portada".
- Subcarpeta `Créditos` (id `1C3mrVrepiUF_qCoEYiLalBSDnW34RXxi`): tablas de desarrollo y documentos de crédito.
- Subcarpeta `Contratos de arriendo` (id `1zTqHt0DKwjYC1884BOZPYSDnvkX7H_1R`): contratos de arriendo.
- **Registro vigente:** "Kaiken - Registro de propiedades v2" (id `1ezX6xGVffS_LXbUzxv2EWGWZQMaUVqDuckcXTJhtxVs`). Reemplaza a "Kaiken - Registro de propiedades (pre-llenado)" (id `1kKxUN4E_M8MisCy3Oaq5ifPBeztmOaeLjDRDjHDtLgE`) y al registro vacío original (id `1qCx9htpnIu7g-rl1xTP1soHZY5UPYuTPYm11iaVg3xU`), que quedaron obsoletos.
- Conector de Google Sheets activo desde el 5 oct 2026: editar el Registro v2 en el mismo archivo (mismo link), no crear copias nuevas. Fuente de datos para el dashboard: el Registro v2 (arriendos, créditos, tipo de financiamiento).

## Criterios acordados con el usuario

1. **Valor de tasación:** usar el valor comercial del tasador, no el valor banco. Si un activo tiene más de una tasación, usar siempre la **mayor**.
2. **Mostrar dos columnas:** "Valor comercial" (el mayor, el que usa la proyección) y "Valor banco" (visado para garantía). Si hay un solo valor, las dos muestran lo mismo.
3. **Recoleta** (4 deptos Edificio Ilumina) va **incluida** por defecto, aunque sigue en compra.
4. Montos en UF reales. UF de referencia: 40.875 CLP (planilla, 1 sep 2026).
5. Tabla de propiedades ordenable por cualquier columna.
6. **Registro de propiedades v2 (decisiones del usuario):**
   - Sin columnas Origen, Precio de compra, Costos de adquisición, Reparaciones iniciales: solo "Costo total (UF)".
   - Sin Seguros, Mantención ni Administración (los seguros van dentro del dividendo del crédito).
   - "Tipo de financiamiento" con lista de validación: Leaseback / Compra con banco. "Capital propio aportado" solo se acepta si es Compra con banco (validación personalizada; gris si no aplica, amarillo si falta).
   - "Saldo insoluto hoy" se calcula solo con TODAY(), por fórmula de anuidad sobre monto, tasa, plazo y fecha del primer dividendo. Difiere 0,5% o menos de las tablas de los bancos. Terrazas 401 usa 12.296,05 UF (capital con 4 meses de gracia capitalizados).

## Propiedades (valor comercial / banco en UF)

| N° | Activo | Comercial | Banco | Fuente | Crédito |
|---|---|---|---|---|---|
| 11 | La Portada, Independencia (locales) | 18.050 | 18.050 | Perito judicial nov 2024 ($685,5 MM) | Sin crédito |
| 5 | Terrazas 401, Huechuraba | 16.635 | 16.635 | CGDV / Banco de Chile may 2024 | Banco de Chile 12.100 UF, 4,94%, 15 años |
| 3 | Terrazas 202, Huechuraba | 14.100 | 14.100 | N. Latorre / Itaú jun 2025 | Itaú 9.761,98 UF, 12 años |
| 9 | Nueva York 25 piso 3, Santiago | 8.225 | 8.225 | Propiteq online ene 2026 | Santander 3.990 UF, 12 años |
| 7 | Ñuñoa, Los Talaveras 120 | 8.030 | 8.030 | BancoEstado ago 2026 | Sin crédito |
| 1 | Moneda 812 Of. 705, Santiago | 9.800 | 7.840 | Itaú TMA251378 jul 2025 (también BancoEstado 6.509) | Crédito en cuotas 6.166,24 UF, 4,32% (4,41% efectiva), 96 cuotas de 76,34 UF desde 5 oct 2026; banco por confirmar |
| 10 | Huérfanos 1294 Of. 51, Santiago | 7.657 | 7.657 | Propiteq online jul 2026 | Sin crédito |
| 4 | Work Center Miraflores, Renca | 7.545 | 7.545 | Banco de Chile (correo) nov 2025 | Banco de Chile 5.000 UF, 4,5%, 12 años |
| 6 | Europa 401, Huechuraba | 5.367 | 5.367 | BancoEstado may 2023 | BancoEstado 3.971,25 UF, 3,97%, 12 años |
| 2 | Patio Mayor 331, Huechuraba | 4.440 | 4.440 | N. Latorre / Itaú dic 2024 | Itaú 3.552 UF, 12 años |
| 8 | Recoleta, Edificio Ilumina (deptos 25, 27, 85, 105) | 18.200 | 15.268 | Roberto Nieto / Banco de Chile sep 2026 | Supuesto: $360 MM, 4,5%, 20 años |

Arriendos tomados de las tasaciones (UF/mes, estimaciones del tasador, no contratos): La Portada 118,6 (renta neta), Terrazas 401 77,5, Terrazas 202 85, Moneda 54, Huérfanos 46,7, Patio Mayor 32, Recoleta 57,85. El resto usa una renta supuesta de 6,5% anual sobre la tasación.

## Modelo del dashboard

- Valor = tasación × (1 + plusvalía)^año.
- Renta neta = arriendo × 12 × (1 − vacancia 5%) × (1 − gastos 12%). Nueva York y Huérfanos: 6 meses sin renta por remodelación.
- Dividendos y saldos desde las tablas de desarrollo reales (`data/creditos.json`).
- Valor del área = VPN de flujos netos + (valor final × (1 − 2% costo de venta) − saldo de deuda), descontado al 8% real.
- TIR y múltiplo sobre el patrimonio actual a valor de tasación.
- Plusvalía histórica: contra el valor libro del balance (columna "A que valor?"), hasta tener precios de compra. Recoleta se excluye de esa comparación (su valor libro es solo el pie de 10%).
- El estado del navegador se guarda en localStorage con la clave `kaiken-inmo-v5`. Subir la versión cuando cambien los valores por defecto.

## Pendientes

- Crédito de Moneda (Itaú, ya en el registro v2): confirmar destino de los fondos (el dashboard suma la deuda pero no la caja recibida).
- Sincronizar el dashboard con los arriendos reales del registro v2. Falta definir: renta de Nueva York y Huérfanos mientras estén vacantes, y arriendo de Recoleta.

- Precios de compra y costos de adquisición de todas las propiedades.
- Arriendos reales y contratos (hoy 4 estimados: Ñuñoa, Renca, Europa, Nueva York).
- Monto y tasa real del crédito de Recoleta.
- Rol de La Portada: PDF dice 288-11, planilla 248-11.
- Posible error de rol en la tasación del depto 27 de Recoleta (2371-68 aparece también en el depto 85).

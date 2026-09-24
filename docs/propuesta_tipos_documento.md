# Propuesta: Tipos de Documento para Estimados (Annual / Standard)

**Preparado para:** Cliente
**Servicio:** Generación de propuestas en Word (DOCX)
**Estado:** Propuesta para revisión y aprobación

---

## 1. Resumen

Se propone ampliar el sistema de generación de estimados para soportar **dos tipos de documento**:

| Opción | Tipo | Orientado a |
|--------|------|-------------|
| Opción 1 | **Annual** | Propuestas de carácter anual |
| Opción 2 | **Standard** | Propuestas específicas |

Hoy el sistema produce un único formato de documento por cada modalidad de estimado. Con este cambio, cada estimado podrá emitirse en el formato que corresponda al tipo de relación comercial con el cliente, manteniendo la información y los cálculos intactos.

---

## 2. Alcance

El cambio aplica a las **dos modalidades de estimado** existentes:

- Estimado por evento (total).
- Estimado por día (per day).

En ambos casos, el usuario definirá el tipo de documento (**Annual** o **Standard**) al momento de generarlo, y el sistema producirá la versión correspondiente.

---

## 3. Qué cambia y qué no

**Cambia**

- La **presentación final del documento**: la última página se adapta a cada tipo de propuesta.
- El sistema queda preparado para asociar cada tipo de documento con su formato correspondiente.

**No cambia**

- El contenido de menús, servicios de alimentos, personal, extras y resumen de costos.
- El motor de cálculo (subtotales, impuestos, cargos por servicio, tarjeta y saldo final).
- La información del cliente, evento y representante.
- La modalidad de estimado (evento total o por día).

---

## 4. Flujo de trabajo propuesto

El flujo se mantiene simple para el usuario y centralizado en el sistema:

1. El usuario prepara la propuesta desde AppSheet, como lo hace actualmente.
2. AppSheet envía, junto con la información habitual, el **tipo de documento** a generar.
3. El sistema identifica automáticamente:
   - La modalidad del estimado (evento total o por día).
   - El tipo de documento (Annual o Standard).
4. El sistema genera el archivo Word correspondiente y lo deja disponible en Drive con su enlace, igual que hoy.

Para garantizar la continuidad operativa, si no se especifica un tipo de documento, el sistema mantiene el formato de estimado actual. Esto evita interrupciones en los procesos existentes.

---

## 5. Diseño funcional

### 5.1 Nuevo campo en la solicitud

Se incorpora un campo opcional al conjunto de datos que envía AppSheet:

| Campo | Valores válidos | Valor por defecto | Obligatorio |
|-------|-----------------|-------------------|-------------|
| `proposal_type` | `Annual`, `Standard` | Formato actual | No |

### 5.2 Matriz de formatos

| Modalidad de estimado | Tipo de documento | Formato de salida |
|----------------------|-------------------|-------------------|
| Evento total | Annual | Estimado (Annual) |
| Evento total | Standard | Estimado (Standard) |
| Por día | Annual | Estimado por día (Annual) |
| Por día | Standard | Estimado por día (Standard) |

El sistema valida el tipo recibido y, ante un valor no reconocido, mantiene el formato actual para no detener la generación.

---

## 6. Consideraciones técnicas

- El campo se integra respetando el esquema de datos actual, sin afectar los envíos existentes.
- La selección del formato es responsabilidad del servicio; AppSheet solo lo indica.
- Se recomienda nombrar los formatos de manera consistente para simplificar su mantenimiento futuro.
- Se mantiene el registro en el historial de propuestas y la actualización de enlaces en AppSheet tal como funciona hoy.

---

## 7. Validación y pruebas

Antes de la entrega se verificará:

- Generación correcta en las **cuatro combinaciones** (modalidad × tipo de documento).
- Retrocompatibilidad: solicitudes sin el campo `proposal_type` siguen generando el documento en el formato actual.
- Continuidad del motor de cálculo en todas las combinaciones.
- Correcta carga del archivo en Drive y actualización del enlace correspondiente.

---

## 8. Tiempo estimado

2 horas de desarrollo



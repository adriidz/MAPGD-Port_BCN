# Sistema Intel·ligent de Monitoratge del Port de Barcelona

Aquest projecte implementa un sistema avançat de monitoratge al Port de Barcelona utilitzant càmeres existents, xarxa 5G i models d'IA. La solució detecta, segueix i analitza vehicles en temps real, generant dades estructurades per al control operatiu, la seguretat i l'anàlisi històrica.

El sistema inclou detecció amb YOLO, tracking propi amb recompte de vehicles, integració amb AWS i un dashboard interactiu en Streamlit.

## 1. Objectiu del projecte

L'objectiu és proporcionar una eina de monitoratge capaç de:

- Detectar vehicles en temps real.
- Fer seguiment robust amb ID persistent.
- Comptar entrades, sortides i direccions de moviment.
- Exportar dades per anàlisi posterior.
- Mostrar informació en un dashboard centralitzat.
- Escalar a múltiples càmeres i zones del port.

## 2. Arquitectura general

**Pipeline complet:**

- **Entrada**: vídeos del port.
- **YOLOv11**: detecció cada N frames (optimitzat per temps real).
- **Tracker**: seguiment amb predicció per mantenir IDs consistents.
- **Recompte**: línies horitzontals i verticals per detectar entrades/sortides i moviments.
- **Generació d'events**: JSON amb dades d'aforament, trajectòries i metadades.

**Exportació al núvol:**

- Vídeos processats → AWS S3
- JSON d'events → DynamoDB
- Dashboard Streamlit: visualització del trànsit, aforament i vídeos.

## 3. Implementació del tracker

### Detecció (YOLOv11)

- Execució configurable cada X frames (`--skip`) per garantir temps real.
- Filtrat per classe (només cotxes).
- Deteccions convertides a bounding boxes per al tracker.

### Tracker propi

El tracker manté identificadors persistents utilitzant:

- Associació de deteccions consecutives
- Predicció de moviment
- Gestió d'oclusions
- Actualització contínua de trajectòries

Funciona amb el mòdul `Tracker` i `Tracker_prediction`.

### Recompte multi-línia

Utilitzem la classe `VehicleCounter` amb tres línies configurades:

- **Línia horitzontal**: forward / backward
- **Línia vertical esquerra**: entry
- **Línia vertical dreta**: exit

Cada creuament genera un `event_*.json` amb:

```
camera_id, timestamp, direction, zone, counter_type, track_id, video_file
```

Els JSON es guarden a `/datos/`.

## 4. Integració amb AWS

El sistema permet exportar:

### 📤 Vídeos → S3

Els vídeos anotats generats a `runs/cars_video/` es pugen al bucket S3 corresponent.

### 📤 Events JSON → DynamoDB

Els JSON generats es poden inserir a DynamoDB per consultes escalables i integració amb altres serveis.

Aquesta versió inclou la infraestructura i el codi preparat, però l'execució pot mantenir-se en mode local si es desitja.

## 5. Dashboard interactiu (Streamlit)

El dashboard està implementat a `visu.py` i funciona 100% en local.

**Només necessita:**

- JSON a `/datos/`
- Vídeos a `/runs/cars_video/`

### Funcionalitats principals

**✔️ Filtres**

- Per càmera
- Per rang de dates
- Descarrega CSV complet o filtrat

**✔️ Mètriques generals**

- Aforament global i per càmera
- Nombre total d'esdeveniments
- Forward / backward
- Entrades / sortides

**✔️ Evolució temporal**

- Gràfiques resamplejades cada 45s
- Aforament acumulat
- Segments per direcció

**✔️ Taula d'esdeveniments**

- Fins a 500 events visibles
- Ordenats per data
- Descarregable en CSV

**✔️ Reproducció de vídeo**

- Selecció de vídeo processat
- Visualització de trajectòries i contadors
- Taula d'esdeveniments associada al vídeo

### Executar dashboard

```bash
streamlit run visu.py
```

**Accés:** http://localhost:8501

## 6. Execució del processador de vídeo

Per processar un vídeo amb YOLO, tracking i generació de JSON:

```bash
python main.py --video videos/output2.mp4 --camera-id camara_1
```

**Paràmetres principals:**

- `--video`: Ruta del vídeo a processar (per defecte: `videos/output2.mp4`)
- `--camera-id`: Identificador de la càmera (per defecte: `camara_1`)

**Paràmetres opcionals:**

- `--weights`: Model YOLO a utilitzar (per defecte: `weights/yolo11n.pt`)
- `--conf`: Confiança mínima per deteccions (per defecte: `0.5`)
- `--skip`: Processar cada N frames (per defecte: `3`)
- `--display`: Mostrar finestra de visualització en temps real

**Exemple:**

```bash
python main.py --video videos/mon_video.mp4 --camera-id camara_principal --skip 5
```

**Sortides generades:**

- Vídeos processats → `runs/cars_video/`
- Events JSON → `datos/`

## 7. Estat actual i futur del projecte

**✔️ Completat:**

- Tracking robust i estable
- Recompte multi-direccional
- Exportació al núvol preparada
- Dashboard complet

**⏳ Pendent:**

- Integració total amb serveis AWS Lambda / API Gateway
- Detecció de matrícules
- Detecció d'emissions i anàlisi ambiental

## 8. Autors

- Adrià Fraile
- Adrián Díaz
- Amina Aasifar
- Lian Bagué
- Pol Guil

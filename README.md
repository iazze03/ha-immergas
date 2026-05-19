# Immergas Smartech Plus — Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

Integrazione non ufficiale per caldaie **Immergas** con gateway **Smartech Plus** per Home Assistant.

Permette di controllare la caldaia tramite Home Assistant e Apple HomeKit **senza** utilizzare l'app ufficiale Immergas, comunicando direttamente con il cloud `smartechplus.immergas.com`.

## Funzionalità

- 🌡️ **Temperatura ambiente** in tempo reale
- 🌤️ **Temperatura esterna** rilevata dal gateway
- 🎯 **Setpoint** — imposta la temperatura desiderata
- 🔥 **Stato riscaldamento** (fiamma accesa/spenta)
- 🔄 **Modalità termostato** — Manuale / Automatico (segue programma)
- 🏠 **Modalità caldaia** — Inverno / Estate / Spento / Raffrescamento (preset)
- ✅ **Compatibile con Apple HomeKit** tramite HomeKit Bridge

## Installazione tramite HACS

1. Apri HACS in Home Assistant
2. Vai su **Integrazioni** → menu `⋮` → **Repository personalizzati**
3. Aggiungi `https://github.com/tuousername/ha-immergas` come tipo **Integrazione**
4. Cerca "Immergas" e installa
5. Riavvia Home Assistant

## Installazione manuale

Copia la cartella `custom_components/immergas/` nella directory `/config/custom_components/` di Home Assistant e riavvia.

## Configurazione

1. Vai su **Impostazioni → Dispositivi e servizi → Aggiungi integrazione**
2. Cerca **Immergas Smartech Plus**
3. Inserisci email e password del portale `smartechplus.immergas.com`
4. L'integrazione rileva automaticamente il gateway e crea le entità

## Entità create

| Entità | Tipo | Descrizione |
|--------|------|-------------|
| `climate.immergas_*` | Climate | Termostato principale con controllo setpoint e modalità |
| `sensor.immergas_*_temperatura_ambiente` | Sensor | Temperatura ambiente in °C |
| `sensor.immergas_*_temperatura_esterna` | Sensor | Temperatura esterna in °C |
| `binary_sensor.immergas_*_riscaldamento_attivo` | Binary Sensor | Fiamma accesa/spenta |

## Integrazione con Apple HomeKit

Dopo aver installato l'integrazione, aggiungi le entità `climate.immergas_*` all'integrazione **HomeKit Bridge** di Home Assistant. Il termostato apparirà in Apple Casa con:
- Temperatura attuale e soglia
- Controllo modalità (Riscaldamento / Automatico)
- Preset (Inverno / Estate / Spento)

## Note tecniche

- L'integrazione usa le stesse API del portale web `smartechplus.immergas.com`
- Il protocollo di autenticazione usa cookie `tokenA` e `tokenB` ottenuti al login
- Il polling predefinito è ogni **30 secondi** (configurabile tra 15 e 300)
- Non richiede accesso diretto alla rete locale della caldaia
- Non richiede AppDaemon o MQTT

## Compatibilità

Testato con:
- Immergas Victrix Tera (con gateway Smartech Plus)
- Home Assistant OS 2026.x su HA Green

## Disclaimer

Questa è un'integrazione non ufficiale, non affiliata né supportata da Immergas. Usala a tuo rischio.

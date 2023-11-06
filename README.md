# Truenas Integration 
### (Fork of the Tomaae Repository)
![GitHub release (latest by date)](https://img.shields.io/github/v/release/cyr-ius/hass-truenas?style=plastic)
![Project Stage](https://img.shields.io/badge/project%20stage-development-yellow.svg?style=plastic)
![GitHub all releases](https://img.shields.io/github/downloads/cyr-ius/hass-truenas/total?style=plastic)

![GitHub commits since latest release](https://img.shields.io/github/commits-since/cyr-ius/hass-truenas/latest?style=plastic)
![GitHub commit activity](https://img.shields.io/github/commit-activity/m/cyr-ius/hass-truenas?style=plastic)
![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/cyr-ius/hass-truenas/ci.yml?style=plastic)

![Truenas Logo](https://raw.githubusercontent.com/cyr-ius/hass-truenas/master/docs/assets/images/ui/header.png)

Monitor and control your Truenas CORE/SCALE device from Home Assistant.
 * Monitor System (Cpu, Load, Memory, Temperature, Network, ARC/L2ARC, Uptime)
 * Monitor Disks
 * Monitor Pools (including boot-pool)
 * Monitor Datasets
 * Monitor Replication Tasks
 * Monitor Snapshot Tasks
 * Control and Monitor Services
 * Control and Monitor Virtual Machines
 * Control and Monitor Jails (TrueNAS CORE only)
 * Control and Monitor Cloudsync
 * Create a Dataset Snapshot
 * Update Sensor
 * Reboot and Shutdown TrueNAS system
 

# Features
## Pools
Monitor status for each TrueNAS pool.

![Pools Health](https://raw.githubusercontent.com/cyr-ius/hass-truenas/master/docs/assets/images/ui/pool_healthy.png)
![Pools Free Space](https://raw.githubusercontent.com/cyr-ius/hass-truenas/master/docs/assets/images/ui/pool_free.png)

## Datasets
Monitor usage and attributes for each TrueNAS dataset.

![Datasets](https://raw.githubusercontent.com/cyr-ius/hass-truenas/master/docs/assets/images/ui/dataset.png)

## Disks
Monitor temperature and attributes for each TrueNAS disk.

![Disks](https://raw.githubusercontent.com/cyr-ius/hass-truenas/master/docs/assets/images/ui/disk.png)

## Virtual Machines
Control and monitor status and attributes for each TrueNAS Virtual Machines.
Virtual Machines control is available through services.

![Virtual Machines](https://raw.githubusercontent.com/cyr-ius/hass-truenas/master/docs/assets/images/ui/vm.png)

## Jails
*TrueNAS CORE only*

Control and monitor status and attributes for each TrueNAS jail.
Jail control is available through services.

![Jails](https://raw.githubusercontent.com/cyr-ius/hass-truenas/master/docs/assets/images/ui/jail.png)

## Cloudsync
Control and monitor status and attributes for each TrueNAS cloudsync task.
Jail control is available through services.

![Cloudsync](https://raw.githubusercontent.com/cyr-ius/hass-truenas/master/docs/assets/images/ui/cloudsync.png)

## Replication Tasks
Monitor status and attributes for each TrueNAS replication task.

![Replication Tasks](https://raw.githubusercontent.com/cyr-ius/hass-truenas/master/docs/assets/images/ui/replication.png)

## Snapshot Tasks
Monitor status and attributes for each TrueNAS snapshot task.

![Snapshot Tasks](https://raw.githubusercontent.com/cyr-ius/hass-truenas/master/docs/assets/images/ui/snapshottask.png)

## Dataset Snapshot
Create a Dataset Snapshot using Homeassistant service.
Snapshot name will be automatically generated using datetime iso format with microseconds and "custom" prefix. 

![Snapshot UI](https://raw.githubusercontent.com/cyr-ius/hass-truenas/master/docs/assets/images/ui/snapshot_ui.png)
![Snapshot YAML](https://raw.githubusercontent.com/cyr-ius/hass-truenas/master/docs/assets/images/ui/snapshot_yaml.png)

## Services
Control and monitor status and attributes for each TrueNAS service.
Service control is available through services.

![Services](https://raw.githubusercontent.com/cyr-ius/hass-truenas/master/docs/assets/images/ui/service.png)

## Reboot and Shutdown
Reboot or Shutdown a TrueNAS system.
Service control is available through services.
Target system uptime sensor.

![image](https://user-images.githubusercontent.com/36953052/221521930-f8f789e6-deec-4cc2-b11e-740caa056e44.png)

# Install integration
This integration is distributed using [HACS](https://hacs.xyz/).

You can find it under "Integrations", named "TrueNAS"

Minimum requirements:
* TrueNAS Core 12.0 or TrueNAS Scale (Any version)
* Home Assistant 2022.2.0

## Using TrueNAS development branch
If you are using development branch for TrueNAS, some features may stop working.

## Setup integration
1. Create an API key for Home Assistant on your TrueNAS system.

![Setup step 1](https://raw.githubusercontent.com/cyr-ius/hass-truenas/master/docs/assets/images/ui/setup_1.png)
![Setup step 2](https://raw.githubusercontent.com/cyr-ius/hass-truenas/master/docs/assets/images/ui/setup_2.png)
![Setup step 3](https://raw.githubusercontent.com/cyr-ius/hass-truenas/master/docs/assets/images/ui/setup_3.png)

2. Setup this integration for your TrueNAS device in Home Assistant via `Configuration -> Integrations -> Add -> TrueNAS`.
You can add this integration several times for different devices.

NOTES: 
- If you dont see "TrueNAS" integration, clear your browser cache.

![Add Integration](https://raw.githubusercontent.com/cyr-ius/hass-truenas/master/docs/assets/images/ui/setup_integration.png)
* "Name of the integration" - Friendly name for this router
* "Host" - Use hostname or IP
* "API key" - TrueNAS API key for Home Assistant 

# Development

## Translation
To help out with the translation you need an account on Lokalise, the easiest way to get one is to [click here](https://lokalise.com/login/) then select "Log in with GitHub".
After you have created your account [click here to join TrueNAS Integrations project on Lokalise](https://app.lokalise.com/public/9252786762290237258f09.36273104/).

If you want to add translations for a language that is not listed please [open a Feature request](https://github.com/cyr-ius/hass-truenas/issues/new?labels=enhancement&title=%5BLokalise%5D%20Add%20new%20translations%20language).

## Enabling debug
To enable debug for TrueNAS integration, add following to your configuration.yaml:
```
logger:
  default: info
  logs:
    custom_components.truenas: debug
```

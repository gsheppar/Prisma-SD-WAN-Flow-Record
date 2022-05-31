# Prisma SD-WAN Flow Records (Preview)
The purpose is to grab the flow records for a site and optional for a circuit over a period of days

#### License
MIT

#### Requirements
* Active CloudGenix Account - Please generate your API token and add it to cloudgenix_settings.py
* Python >=3.7

#### Installation:
 Scripts directory. 
 - **Github:** Download files to a local directory, manually run the scripts. 
 - pip install -r requirements.txt
 
### Examples of usage:
 Please generate your API token and add it to cloudgenix_settings.py
 
 - Gets flows for past day on specific site
 - ./flows.py -S Test-LAB
 
 - Gets flows for past day on specific site and circuit 
 - ./flows.py -S Test-LAB -W "Circuit Name"
 
 - Gets flows for past 7 days on specific site
 - ./flows.py -S Test-LAB -T 7
 
### Caveats and known issues:
 - This is a PREVIEW release, hiccups to be expected. Please file issues on Github for any problems.

#### Version
| Version | Build | Changes |
| ------- | ----- | ------- |
| **1.0.0** | **b1** | Initial Release. |


#### For more info
 * Get help and additional Prisma SD-WAN Documentation at <https://docs.paloaltonetworks.com/prisma/cloudgenix-sd-wan.html>

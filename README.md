## Description
Parameters and variables are specified in the settings.ini file.  
The script parses Cloudflare DNS A records by zone from your account.  
For IP found in A records, changes will be made in the netbox.  
A custom field is created in netbox. The values are in json format so that several DNS records can be specified for one IP.  
There is no cache in the script, so the custom field is deleted every time it is run (to clear all the values from it) and recreated and updated data is entered.  
## !! Important
If you have many zones, then most likely you will have a problem with Clouflare limits. They can be increased on an enterprise account. Therefore, in settings.ini you can locally specify the zones that need to be checked.  
In netbox we add only entries for IP that have already been created in netbox. We do NOT create new IP.  
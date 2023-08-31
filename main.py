import CloudFlare
import time
import json
from configparser import ConfigParser
import os
import  pynetbox

# initial objects which will be completed with parameters in functions
all_A_records   = {}
zones_list      = {}

# read configuration file
config = ConfigParser()
config.read("settings.ini")

# CF parameters from settings.ini
cf_email                    = config["clouflare"]["cf_email"]
cf_token                    = config["clouflare"]["cf_token"]
cf_zone_source              = config["clouflare"]["cf_zone_source"]
cf_local_zones              = config["clouflare"]["cf_local_zones"].split(",")
cf_zone_exclude             = config["clouflare"]["cf_zone_exclude"].split(",")

# netbox parameters from settings.ini
netbox_url                  = config["netbox"]["netbox_url"]
netbox_token                = config["netbox"]["netbox_token"]
netbox_custom_field_name    = config["netbox"]["netbox_custom_field_name"]
nb                          = pynetbox.api(url=netbox_url , token=netbox_token)


# get all zones from cloudflere account. use if you have chosen the cloudflare source parameter
def get_all_zones_cloudflare():

    page_number = 0

    while True:
        # page need if you have many zones
        cf          = CloudFlare.CloudFlare(email=cf_email, token=cf_token, raw=True)
        page_number += 1
        raw_results = cf.zones.get(params={'per_page':5,'page':page_number})
        zones       = raw_results['result']

        # add parameters to initial object zones_list
        for zone in zones:
            zone_id     = zone['id']
            zone_name   = zone['name']
            zones_list[zone_name] = zone_id

        total_pages = raw_results['result_info']['total_pages']

        if page_number == total_pages:
            break

# get zones id for zones_name from settings.ini . use if you have chosen the local source parameter
def get_local_zones_id_in_clouflare(cf_local_zones):

    cf = CloudFlare.CloudFlare(email=cf_email, token=cf_token)

    # add parameters to initial object zones_list
    for zone_name in cf_local_zones:
        try:
            zones = cf.zones.get(params = {"name": zone_name, "per_page" : 1})
        except:
            print(f"Problem get local_zone {zone_name} from cloudflare")
            continue

        zone_id = zones[0]['id']
        zones_list[zone_name] = zone_id


# get DNS A records from zones
def get_all_A_records_cloudflare(zones):
    
    for zone_name, zone_id in zones.items():
        
        # skip zones from exclude parameters in settings.ini
        if zone_name in cf_zone_exclude:
            continue
        else:
            # sleep to reduce the possibility of falling into limits cloudflare
            time.sleep(1)
            
            # request the DNS records from zone
            try:
                cf = CloudFlare.CloudFlare(email=cf_email, token=cf_token)
                dns_records = cf.zones.dns_records.get(zone_id)

            # stop "for" in this zone if problem with dns records
            except:
                print(f"NOT work  zone {zone_name}")
                continue


            # then all the DNS records for zone
            for dns_record in dns_records:
                r_name  = dns_record['name']
                r_type  = dns_record['type']
                ip_addr = dns_record['content']

                # find A records and IP
                if r_type == "A":
                    if ip_addr in all_A_records:
                        all_A_records[ip_addr].append(r_name)
                    else:
                        all_A_records[ip_addr] = [r_name]

                else:
                    continue

# add dns name to netbox
def netbox_update(all_A_records):
    # delete custom field so that the old dns records are deleted
    if nb.extras.custom_fields.filter(name= netbox_custom_field_name):
        custom_field        = nb.extras.custom_fields.get(name = netbox_custom_field_name)
        custom_field.delete()

    # create custom field
    custom_field = nb.extras.custom_fields.create({     "name": netbox_custom_field_name,
                                                        "content_types": ["ipam.ipaddress"],
                                                        "type" : "json"})
    custom_field_id = custom_field.id

    # if IP in netbox then add dns records in custom field
    for ip, dns in all_A_records.items():
        try:
            if nb.ipam.ip_addresses.filter(address = ip):
                ip_nb               = nb.ipam.ip_addresses.get(address = ip)
                ip_nb.custom_fields = {netbox_custom_field_name : dns}
                ip_nb.save()
            else:       
                continue
        except:
            print(f"Problem get IP {ip} from netbox")


def main():
    if cf_zone_source == "cloudflare":
        get_all_zones_cloudflare()
    elif cf_zone_source == "local":
        get_local_zones_id_in_clouflare(cf_local_zones)

    get_all_A_records_cloudflare(zones_list)
    netbox_update(all_A_records)

if __name__ == '__main__':
    main()

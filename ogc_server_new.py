import pandas as pd
import json
import requests
import re

GLOBAL_SUBSYSTEMS = []

def update_subsystems(name):
     if name not in GLOBAL_SUBSYSTEMS:
          GLOBAL_SUBSYSTEMS.append(name)

def setup_ogc_server(cloud_access,normal_values,
                     fr_config,uav_config,movement_config):
    # Create a dictionary maping first responder names to the firstresponderOgcThing object
    f = open(movement_config)
    movement_data = json.load(f)
    fr_things_config = {}
    uav_things_config = {}

    fr_config_df = pd.read_csv(fr_config,na_filter= False)
    uav_config_df = pd.read_csv(uav_config)

    headers = cloud_access.general_api.fetch_headers()
    for index,row in fr_config_df.iterrows():
        name = row["name"]
        try:
            team = row["team"]
        except KeyError:
            team = "Vikings"
        fr_id = row["fr_id"]
        identifier = row["identifier"]
        cds_id = row["cds_id"]
        ams_id = row["ams_id"]
        vsas_id = row["vsas_id"]
        coils_id = row["coils_id"]
        trigger_at = row["trigger_at"]
        role = row["role"]
        organization = row["organization"]
        subrole = row["subrole"]
        call_sign = row["call_sign"]
        fr_things_config[name] = FirstResponderOgcThing(name,fr_id,identifier,organization,
                                                        role,subrole,team,call_sign,cds_id,ams_id,vsas_id,
                                                        coils_id,trigger_at,headers,movement_data['first_responders'][name],
                                                        cloud_access.general_api.url_create_thing())
        
    for index,row in uav_config_df.iterrows():
        name = row["name"]
        uav_id = row["uav_id"]
        cds_id = row["cds_id"]
        ads_id = row["ads_id"]
        vsas_id = row["vsas_id"]
        ims_id = row["ims_id"]
        trigger_at = row["trigger_at"]
        organization = row["organization"]
        call_sign = row["call_sign"]
        uav_things_config[name] = UavOgcThing(name,uav_id,organization,call_sign,cds_id,ads_id,vsas_id,
                                             ims_id,trigger_at,headers,movement_data['uavs'][name],
                                             cloud_access.general_api.url_create_thing())
    
    for fr_name in fr_things_config:
        for system in fr_things_config[fr_name].systems:
            update_subsystems(system)

    for uav_name in uav_things_config:
        for system in uav_things_config[uav_name].systems:
            update_subsystems(system)
    print()
    print("Global list of available subsystems: {}".format(GLOBAL_SUBSYSTEMS))
    print()

    # Create a dictionary mapping the system name to ogcSensor object
    sensors = {}

    # dictionary of dictionaries
    # create a dictionary mapping the system name to the dictionary of objectproperties which 
    # mappes the name of the observed property to the ogcObservedProperty object 
    observed_properties = {}
    datastreams = {}
    #! create if conditions for remaining systems belonging to UAVs
    print(".......setting up sensors and observed properties........")
    for system in GLOBAL_SUBSYSTEMS:
        normal_observation = normal_values[system]
        if system == "VSAS_FR":
            api = cloud_access.vsas_api
            headers = cloud_access.vsas_token.get_headers()
            #! add VSAS observed properties from the new postmann
            sensors[system] = ogcSensor(system,headers,api.url_create_sensor())
            temp_properties = {}
            temp_properties["Location"] = ogcObservedProperty("Location",headers,api.url_create_observed_property(),normal_observation,
                                                              unit_of_measurement_name="Geo coordinates",unit_of_measurement_symbol="Geo coordinates",
                                                              unit_of_measurement_definition="Geo coordinates",datastream_name="Location",datastream_desc="Location")
            temp_properties["Object detected"] = ogcObservedProperty("Object detected",headers,api.url_create_observed_property(),normal_observation,
                                                              unit_of_measurement_name="Object class",unit_of_measurement_symbol="Object class",
                                                              unit_of_measurement_definition="Object class",datastream_name="Object detected",datastream_desc="Object detected")
            temp_properties["Videostream"] = ogcObservedProperty("Videostream",headers,api.url_create_observed_property(),normal_observation,
                                                                unit_of_measurement_name="URL",unit_of_measurement_symbol="URL",
                                                                unit_of_measurement_definition="URL",datastream_name="Videostream",datastream_desc="Videostream")
            temp_properties["Safe exit"] = ogcObservedProperty("Safe exit",headers,api.url_create_observed_property(),normal_observation,
                                                               unit_of_measurement_name="Geo coordinates",unit_of_measurement_symbol="Geo coordinates",
                                                              unit_of_measurement_definition="Geo coordinates",datastream_name="Safe exit",datastream_desc="Safe exit")
            observed_properties[system] = temp_properties

        elif system == "AMS":
            api = cloud_access.ams_api
            headers = cloud_access.ams_token.get_headers()
            sensors[system] = ogcSensor(system,headers,api.url_create_sensor())
            temp_properties = {}
            temp_properties["Activity"] = ogcObservedProperty("Activity",headers,api.url_create_observed_property(),normal_observation,
                                                              unit_of_measurement_name="Activity class",unit_of_measurement_symbol="Activity class",
                                                              unit_of_measurement_definition="Activity class",datastream_name="Activity",datastream_desc="Activity")
            temp_properties["Heartrate"] = ogcObservedProperty("Heartrate",headers,api.url_create_observed_property(),normal_observation,
                                                                unit_of_measurement_name="Beats per minute",unit_of_measurement_symbol="BPM",
                                                                unit_of_measurement_definition="BPM",datastream_name="Heartrate",datastream_desc="Heartrate")
            temp_properties["Spo2"] = ogcObservedProperty("Spo2",headers,api.url_create_observed_property(),normal_observation,
                                                          unit_of_measurement_name="Percentage",unit_of_measurement_symbol="%",
                                                          unit_of_measurement_definition="ucum:%",datastream_name="Spo2",datastream_desc="Spo2")
            temp_properties["Skin temperature"] = ogcObservedProperty("Skin temperature",headers,api.url_create_observed_property(),normal_observation,
                                                                        unit_of_measurement_name="Degree Celsius",unit_of_measurement_symbol="°C",
                                                                        unit_of_measurement_definition="ucum:Cel",datastream_name="Skin temperature",datastream_desc="Skin temperature")
            temp_properties["Fall detection"] = ogcObservedProperty("Fall detection",headers,api.url_create_observed_property(),normal_observation,
                                                                   unit_of_measurement_name="Bool",unit_of_measurement_symbol="Bool",
                                                                   unit_of_measurement_definition="Bool",datastream_name="Fall detection",datastream_desc="Fall detection")
            observed_properties[system] = temp_properties

        elif system == "CDS":
            api = cloud_access.cds_api
            headers = cloud_access.cds_token.get_headers()
            sensors[system] = ogcSensor(system,headers,api.url_create_sensor())
            temp_properties = {}
            temp_properties["Ammonia"] = ogcObservedProperty("Ammonia",headers,api.url_create_observed_property(),normal_observation,
                                                             unit_of_measurement_name="ppm",unit_of_measurement_symbol="ppm",
                                                             unit_of_measurement_definition="ucum:ppm",datastream_name="Ammonia",
                                                             datastream_desc="Ammonia")
            temp_properties["Carbon monoxide"] = ogcObservedProperty("Carbon monoxide",headers,api.url_create_observed_property(),normal_observation,
                                                                      unit_of_measurement_name="ppm",unit_of_measurement_symbol="ppm",
                                                                      unit_of_measurement_definition="ucum:ppm",datastream_name="Carbon monoxide",
                                                                      datastream_desc="Carbon monoxide")
            temp_properties["Oxygen"] = ogcObservedProperty("Oxygen",headers,api.url_create_observed_property(),normal_observation,
                                                            unit_of_measurement_name="ppm",unit_of_measurement_symbol="ppm",
                                                             unit_of_measurement_definition="ucum:ppm",datastream_name="Oxygen",
                                                             datastream_desc="Oxygen")
            temp_properties["Hydrogen"] = ogcObservedProperty("Hydrogen",headers,api.url_create_observed_property(),normal_observation,
                                                              unit_of_measurement_name="ppm",unit_of_measurement_symbol="ppm",
                                                             unit_of_measurement_definition="ucum:ppm",datastream_name="Hydrogen",
                                                             datastream_desc="Hydrogen")
            temp_properties["Chlorine"] = ogcObservedProperty("Chlorine",headers,api.url_create_observed_property(),normal_observation,
                                                              unit_of_measurement_name="ppm",unit_of_measurement_symbol="ppm",
                                                             unit_of_measurement_definition="ucum:ppm",datastream_name="Chlorine",
                                                             datastream_desc="Chlorine")
            temp_properties["Florine"] = ogcObservedProperty("Florine",headers,api.url_create_observed_property(),normal_observation,
                                                             unit_of_measurement_name="ppm",unit_of_measurement_symbol="ppm",
                                                             unit_of_measurement_definition="ucum:ppm",datastream_name="Florine",
                                                             datastream_desc="Florine")
            temp_properties["Hydrogen cyanide"] = ogcObservedProperty("Hydrogen cyanide",headers,api.url_create_observed_property(),normal_observation,
                                                                     unit_of_measurement_name="ppm",unit_of_measurement_symbol="ppm",
                                                             unit_of_measurement_definition="ucum:ppm",datastream_name="Hydrogen cyanide",
                                                             datastream_desc="Hydrogen cyanide")
            temp_properties["Sulfur dioxide"] = ogcObservedProperty("Sulfur dioxide",headers,api.url_create_observed_property(),normal_observation,
                                                                    unit_of_measurement_name="ppm",unit_of_measurement_symbol="ppm",
                                                             unit_of_measurement_definition="ucum:ppm",datastream_name="Sulfur dioxide",
                                                             datastream_desc="Sulfur dioxide")
            temp_properties["Phosphine"] = ogcObservedProperty("Phosphine",headers,api.url_create_observed_property(),normal_observation,
                                                                    unit_of_measurement_name="ppm",unit_of_measurement_symbol="ppm",
                                                             unit_of_measurement_definition="ucum:ppm",datastream_name="Phosphine",
                                                             datastream_desc="Phosphine")
            observed_properties[system] = temp_properties

        elif system == "COILS":
            api = cloud_access.coils_api
            headers = cloud_access.coils_token.get_headers()
            sensors[system] = ogcSensor(system,headers,api.url_create_sensor())
            temp_properties = {}
            temp_properties["Position_Data"] = ogcObservedProperty("Position_Data",headers,api.url_create_observed_property(),normal_observation,
                                                              unit_of_measurement_name="Geo coordinates",unit_of_measurement_symbol="Geo coordinates",
                                                              unit_of_measurement_definition="Geo coordinates",datastream_name="Position_Data",datastream_desc="Position_Data")
            observed_properties[system] = temp_properties
        
        elif system == "VSAS_UAV":
            api = cloud_access.vsas_api
            headers = cloud_access.vsas_token.get_headers()
            sensors[system] = ogcSensor(system,headers,api.url_create_sensor())
            temp_properties = {}
            temp_properties["Location"] = ogcObservedProperty("Location",headers,api.url_create_observed_property(),normal_observation,
                                                              unit_of_measurement_name="Geo coordinates",unit_of_measurement_symbol="Geo coordinates",
                                                              unit_of_measurement_definition="Geo coordinates",datastream_name="Location",datastream_desc="Location")
            temp_properties["Object detected"] = ogcObservedProperty("Object detected",headers,api.url_create_observed_property(),normal_observation,
                                                              unit_of_measurement_name="Object class",unit_of_measurement_symbol="Object class",
                                                              unit_of_measurement_definition="Object class",datastream_name="Object detected",datastream_desc="Object detected")
            temp_properties["Videostream"] = ogcObservedProperty("Videostream",headers,api.url_create_observed_property(),normal_observation,
                                                                unit_of_measurement_name="URL",unit_of_measurement_symbol="URL",
                                                                unit_of_measurement_definition="URL",datastream_name="Videostream",datastream_desc="Videostream")
            observed_properties[system] = temp_properties

        elif system == "ADS":
            api = cloud_access.ads_api
            headers = cloud_access.ads_token.get_headers()
            sensors[system] = ogcSensor(system,headers,api.url_create_sensor())
            temp_properties = {}
            temp_properties["ADS"] = ogcObservedProperty("ADS",headers,api.url_create_observed_property(),
                                                            normal_observation,unit_of_measurement_name="Audio class",
                                                            unit_of_measurement_symbol="Audio class",
                                                            unit_of_measurement_definition="Audio class",
                                                            datastream_name="ADS",datastream_desc="ADS")
            observed_properties[system] = temp_properties
        else: # IMS
            api = cloud_access.ims_api
            headers = cloud_access.ims_token.get_headers()
            sensors[system] = ogcSensor(system,headers,api.url_create_sensor())
            temp_properties = {}

    print(".......Setting up datastreams........")
    datastreams = {}
    for fr_name in fr_things_config:
        temp_thing_id = fr_things_config[fr_name].thing_id
        temp_thing_call_sign = fr_things_config[fr_name].call_sign
        temp_subsystems_name = fr_things_config[fr_name].systems
        sensor_datastream_map = {}
        for system_name in temp_subsystems_name:
            temp_sensor_id = sensors[system_name].id
            temp_sensor_name = sensors[system_name].name
            temp_obs_properties = observed_properties[system_name]
            temp_datastreams = {}
            headers,url = get_create_datastream_header_url(cloud_access,system_name)
            for op_name in temp_obs_properties:
                temp_op_id = temp_obs_properties[op_name].id
                temp_datastreams[op_name] = dataStream(temp_thing_id, temp_sensor_id, temp_sensor_name, temp_op_id, fr_name, temp_thing_call_sign, temp_obs_properties[op_name], headers, url)
            sensor_datastream_map[system_name] = temp_datastreams
        datastreams[fr_name] = sensor_datastream_map

    for uav_name in uav_things_config:
        temp_thing_id = uav_things_config[uav_name].thing_id
        temp_thing_call_sign = uav_things_config[uav_name].call_sign
        temp_subsystems_name = uav_things_config[uav_name].systems
        sensor_datastream_map = {}
        for system_name in temp_subsystems_name:
            temp_sensor_id = sensors[system_name].id
            temp_sensor_name = sensors[system_name].name
            temp_obs_properties = observed_properties[system_name]
            temp_datastreams = {}
            headers,url = get_create_datastream_header_url(cloud_access,system_name)
            for op_name in temp_obs_properties:
                temp_op_id = temp_obs_properties[op_name].id
                temp_datastreams[op_name] = dataStream(temp_thing_id, temp_sensor_id, temp_sensor_name,temp_op_id, uav_name,temp_thing_call_sign,temp_obs_properties[op_name], headers, url)
            sensor_datastream_map[system_name] = temp_datastreams
        datastreams[uav_name] = sensor_datastream_map

    return fr_things_config,uav_things_config,sensors,observed_properties,datastreams

class dataStream():
    def __init__(self,thing_id, sensor_id,sensor_name,observation_property_id, thing_name,thing_call_sign, observation_property, headers, url):
        self.thing_name = thing_name
        self.datastream_name = observation_property.datastream_name + "-" + sensor_name + "-"+ thing_call_sign
        self.datastream_desc = observation_property.datastream_desc + " " + thing_name
        self.datastream_observationtype = "http://www.opengis.net/def/observationType/OGC-OM/2.0/OM_Measurement"
        self.unit_of_measurement_name = observation_property.unit_of_measurement_name
        self.unit_of_measurement_symbol = observation_property.unit_of_measurement_symbol
        self.unit_of_measurement_definition = observation_property.unit_of_measurement_definition
        self.id = self.create_datastream(thing_id,sensor_id,sensor_name,observation_property_id,observation_property.name,headers,url)
    
    def create_datastream(self,thing_id,sensor_id,sensor_name,observation_property_id, observation_property_name,headers,url):
        payload = json.dumps({"name": self.datastream_name,
                                "description": self.datastream_desc,
                                "observationType": "http://www.opengis.net/def/observationType/OGC-OM/2.0/OM_Measurement",
                                "unitOfMeasurement": {
                                    "name": self.unit_of_measurement_name,
                                    "symbol": self.unit_of_measurement_symbol,
                                    "definition": self.unit_of_measurement_definition
                                },
                                "Thing": {
                                    "@iot.id": thing_id
                                },
                                "Sensor": {
                                    "@iot.id": sensor_id
                                },
                                "ObservedProperty": {
                                    "@iot.id": observation_property_id
                                }
                                })
        response = requests.request("POST", url, headers=headers, data=payload, verify=False)
        ds_url = response.headers["Location"]
        ds_id  = re.split("[()]",ds_url)[-2]
        print("................... Datastream  {} created: Thing = {}  Sensor_name = {}  OP = {}".format(ds_id, self.thing_name, sensor_name, observation_property_name))
        return int(ds_id)

class UavOgcThing():
    def __init__(self,name,uav_id,organization,call_sign,cds_id,ads_id,vsas_id,ims_id,trigger_at,headers,movement_data,url):
        self.name = name
        self.type = "UAV"
        self.uav_id = uav_id
        self.organization = organization
        self.call_sign = call_sign
        self.cds_id = cds_id
        self.ads_id = ads_id
        self.vsas_id = vsas_id
        self.ims_id = ims_id
        self.systems, self.lower_case_system = self.get_subsystems()
        self.trigger_at = trigger_at
        self.description = "The thing description for the person "+ self.name
        self.start_lat = movement_data["start"][0]
        self.start_lon = movement_data["start"][1]
        self.speed = movement_data["speed"]
        self.waypoints_delay = movement_data["waypoints_delay"]
        self.close_loop = movement_data["close_loop"]
        self.thing_id = self.create_thing(headers,url)
    
    def get_subsystems(self):
        systems = []
        lower_case_systems = []
        if self.vsas_id != 0:
            systems.append("VSAS_UAV")
            lower_case_systems.append("vsas")
            
        if self.ads_id != 0:
            systems.append("ADS")
            lower_case_systems.append("ads")

        if self.cds_id != 0:
            systems.append("CDS")
            lower_case_systems.append("cds")

        if self.ims_id != 0:
            systems.append("IMS")
            lower_case_systems.append("ims")   
        return systems, lower_case_systems
    
    def create_thing(self,headers,url):
        payload = json.dumps({"name": self.name,
                              "description":self.description,
                              "properties":{"type":self.type,
                                            #"uav_id":self.uav_id,
                                            "organization":self.organization,
                                            "callsign":self.call_sign,
                                            "systems":self.lower_case_system}})
        response = requests.request("POST", url, headers=headers, data=payload, verify=False)
        thing_url = response.headers["Location"]
        thing_id  = re.split("[()]",thing_url)[-2]
        print("{} UAV thing is created with ID {}".format(self.name,thing_id))
        return int(thing_id)
    
    def delete_thing(self,delete_url,delete_headers):
        payload = json.dumps({})
        response = requests.request("DELETE", delete_url, headers=delete_headers, data=payload, verify=False)
        print(response)

class FirstResponderOgcThing():
    def __init__(self,name,fr_id,identifier,organization,role,subrole,team,call_sign,cds_id,ams_id,vsas_id,coils_id,trigger_at,headers,movement_data,url):
        self.name = name
        self.type = "person"
        self.fr_id = fr_id
        self.identifier = identifier
        self.organization = organization
        self.role = role
        self.subrole = subrole
        self.team = team
        self.call_sign = call_sign
        self.cds_id = cds_id
        self.ams_id = ams_id
        self.vsas_id = vsas_id
        self.coils_id = coils_id
        self.systems, self.lower_case_system = self.get_subsystems()
        self.trigger_at = trigger_at
        self.description = "The thing description for the "+ self.name
        self.start_lat = movement_data["start"][0]
        self.start_lon = movement_data["start"][1]
        self.speed = movement_data["speed"]
        self.waypoints_delay = movement_data["waypoints_delay"]
        self.close_loop = movement_data["close_loop"]
        self.thing_id = self.create_thing(headers,url)

    def create_thing(self,headers,url):
        payload = json.dumps({"name": self.name,
                              "description":self.description,
                              "properties":{"type":self.type,
                                            "role":self.role,
                                            "organization":self.organization,
                                            "subrole":self.subrole,
                                            "callsign":self.call_sign,
                                            "systems":self.lower_case_system,
                                            "team":self.team}})
        response = requests.request("POST", url, headers=headers, data=payload, verify=False)
        thing_url = response.headers["Location"]
        thing_id  = re.split("[()]",thing_url)[-2]
        print("{} FR thing is created with ID {}".format(self.name,thing_id))
        return int(thing_id)
    
    def delete_thing(self,delete_url,delete_headers):
        payload = json.dumps({})
        response = requests.request("DELETE", delete_url, headers=delete_headers, data=payload, verify=False)
        print(response)

    def get_subsystems(self):
        systems = []
        lower_case_systems = []

        if self.vsas_id != 0:
            systems.append("VSAS_FR")
            lower_case_systems.append("vsas")
            
        if self.ams_id != 0:
            systems.append("AMS")
            lower_case_systems.append("ams")

        if self.cds_id != 0:
            systems.append("CDS")
            lower_case_systems.append("cds")

        if self.coils_id != 0:
            systems.append("COILS")
            lower_case_systems.append("coils")   
        return systems, lower_case_systems

class ogcSensor():
    def __init__(self,name,headers,url):
        self.name = name
        self.description = self.name + " Sensor"
        self.encoding_type = "application/pdf"
        self.metadata = self.name + " description pdf comes here"
        self.headers = headers
        self.id = self.create_sensor(headers,url)

    def create_sensor(self,headers,url):
        # create sensor in here and return sensor id
        payload = json.dumps({"name": self.name,
                              "description":self.description,
                              "encodingType":self.encoding_type,
                              "metadata":self.metadata})
        
        response = requests.request("POST", url, headers=headers, data=payload, verify=False)
        sensor_url = response.headers["Location"]
        sensor_id  = re.split("[()]",sensor_url)[-2]
        print("{} is created with ID {}".format(self.name,sensor_id))
        return int(sensor_id)
    
    def delete_sensor(self,headers,url):
        payload = json.dumps({})
        
        response = requests.request("DELETE", url, headers=headers, data=payload, verify=False)
        print(response)
    
class ogcObservedProperty():
    def __init__(self,name,headers,url,normal_observations,unit_of_measurement_name=None,unit_of_measurement_symbol=None,unit_of_measurement_definition=None,datastream_name=None,datastream_desc=None):
        self.name = name
        self.description = name
        self.definition = name
        self.unit_of_measurement_name = unit_of_measurement_name
        self.unit_of_measurement_symbol = unit_of_measurement_symbol
        self.unit_of_measurement_definition = unit_of_measurement_definition
        self.datastream_name = datastream_name
        self.datastream_desc = datastream_desc
        self.is_categorical,self.normal_values = self.get_normal_values(normal_observations)   # is_categorical is False when its a regresson feature and Ture if its a categorical feature

        self.id = self.create_observed_property(headers,url)
    
    def create_observed_property(self,headers,url):
        payload = json.dumps({"name": self.name,
                              "description":self.description,
                              "definition":self.definition})
        response = requests.request("POST", url, headers=headers, data=payload, verify=False)
        op_url = response.headers["Location"]
        op_id  = re.split("[()]",op_url)[-2]
        print("..... {} Observed property is created with ID {}".format(self.name,op_id))
        return int(op_id)
    
    def get_normal_values(self,normal_observations):
        try:
            is_categorical = False
            temp = normal_observations[self.name]
            if temp[0] == "C":
                is_categorical = True
            return is_categorical, temp[1:]
        except KeyError:
            return None,None
##################################################################
    
def get_create_datastream_header_url(cloud_access,sensor_name):
    if sensor_name == "AMS":
        headers = cloud_access.ams_token.get_headers()
        url = cloud_access.ams_api.url_create_datastream()
        return headers,url
    elif sensor_name == "CDS":
        headers = cloud_access.cds_token.get_headers()
        url = cloud_access.cds_api.url_create_datastream()
        return headers,url
    elif sensor_name == "COILS":
        headers = cloud_access.coils_token.get_headers()
        url = cloud_access.coils_api.url_create_datastream()
        return headers,url
    elif sensor_name == "ADS":
        headers = cloud_access.ads_token.get_headers()
        url = cloud_access.ads_api.url_create_datastream()
        return headers,url
    elif sensor_name == "IMS":
        headers = cloud_access.ims_token.get_headers()
        url = cloud_access.ims_api.url_create_datastream()
        return headers,url
    else:
        headers = cloud_access.vsas_token.get_headers()
        url = cloud_access.vsas_api.url_create_datastream()
        return headers,url
    
    
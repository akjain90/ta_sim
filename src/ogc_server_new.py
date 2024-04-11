import json
# import requests
import re
import pandas as pd

GLOBAL_SUBSYSTEMS = []

def update_subsystems(name):
    """
    Update the global list of available subsystems.
    List is used to instantiate OGC sensors and observedPrperties
    """
    if name not in GLOBAL_SUBSYSTEMS:
        GLOBAL_SUBSYSTEMS.append(name)

def setup_ogc_server(api,normal_values,
                     fr_config,uav_config,movement_config):
    """
    Creates the OGC environment for all the entities.
    Things (FRs and UAVs), sensors (all subsystems),
    Observed properties (observation parameter of all sensors),
    Datastreams
    """
    # Create a dictionary maping first responder names to the firstresponderOgcThing object
    with open(movement_config) as f:
        movement_data = json.load(f)
    fr_things_config = {}
    uav_things_config = {}

    fr_config_df = pd.read_csv(fr_config,na_filter= False)
    uav_config_df = pd.read_csv(uav_config)

    for _index,row in fr_config_df.iterrows():
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
        fr_things_config[name] = FirstResponderOgcThing(name,fr_id,identifier,organization,role,
                                                        subrole,team,call_sign,cds_id,ams_id,
                                                        vsas_id,coils_id,trigger_at,
                                                        movement_data['first_responders'][name],
                                                        api)

    for _index,row in uav_config_df.iterrows():
        name = row["name"]
        uav_id = row["uav_id"]
        cds_id = row["cds_id"]
        ads_id = row["ads_id"]
        vsas_id = row["vsas_id"]
        ims_id = row["ims_id"]
        trigger_at = row["trigger_at"]
        organization = row["organization"]
        call_sign = row["call_sign"]
        uav_things_config[name] = UavOgcThing(name,uav_id,organization,call_sign,cds_id,ads_id,
                                              vsas_id,ims_id,trigger_at,
                                              movement_data['uavs'][name],api)

    for name,thing_config in fr_things_config.items():
        for system in thing_config.systems:
            update_subsystems(system)
    for name,thing_config in uav_things_config.items():
        for system in thing_config.systems:
            update_subsystems(system)
    print()
    print(f"Global list of available subsystems: {GLOBAL_SUBSYSTEMS}")
    print()

    sensors = {}

    # dictionary of dictionaries
    # create a dictionary mapping the system name to the dictionary of objectproperties which
    # mappes the name of the observed property to the OgcObservedProperty object
    observed_properties = {}
    datastreams = {}
    print(".......setting up sensors and observed properties........")
    for system in GLOBAL_SUBSYSTEMS:
        normal_observation = normal_values[system]
        if system == "VSAS_FR":
            sensors[system] = OgcSensor(system,api)
            temp_properties = {}
            temp_properties["Location"] = OgcObservedProperty("Location",normal_observation,api,
                                                              "Geo coordinates","Geo coordinates",
                                                              "Geo coordinates","Location",
                                                              "Location")
            temp_properties["Object detected"] = OgcObservedProperty("Object detected",
                                                                     normal_observation,api,
                                                                     "Object class","Object class",
                                                                     "Object class",
                                                                     "Object detected",
                                                                     "Object detected")
            temp_properties["Videostream"] = OgcObservedProperty("Videostream",normal_observation,
                                                                 api,"URL","URL","URL",
                                                                 "Videostream","Videostream")
            temp_properties["Safe exit"] = OgcObservedProperty("Safe exit",normal_observation,api,
                                                               "Geo coordinates","Geo coordinates",
                                                               "Geo coordinates","Safe exit",
                                                               "Safe exit")
            observed_properties[system] = temp_properties

        elif system == "AMS":
            sensors[system] = OgcSensor(system,api)
            temp_properties = {}
            temp_properties["Activity"] = OgcObservedProperty("Activity",normal_observation,api,
                                                              "Activity class","Activity class",
                                                              "Activity class","Activity",
                                                              "Activity")
            temp_properties["Heartrate"] = OgcObservedProperty("Heartrate",normal_observation,api,
                                                               "Beats per minute","BPM","BPM",
                                                               "Heartrate","Heartrate")
            temp_properties["Spo2"] = OgcObservedProperty("Spo2",normal_observation,api,
                                                          "Percentage","%","ucum:%","Spo2",
                                                          "Spo2")
            temp_properties["Skin temperature"] = OgcObservedProperty("Skin temperature",
                                                                      normal_observation,api,
                                                                      "Degree Celsius","°C",
                                                                      "ucum:Cel",
                                                                      "Skin temperature",
                                                                      "Skin temperature")
            temp_properties["Fall detection"] = OgcObservedProperty("Fall detection",
                                                                    normal_observation,api,"Bool",
                                                                    "Bool","Bool","Fall detection",
                                                                    "Fall detection")
            observed_properties[system] = temp_properties

        elif system == "CDS":
            sensors[system] = OgcSensor(system,api)
            temp_properties = {}
            temp_properties["Ammonia"] = OgcObservedProperty("Ammonia",normal_observation,api,
                                                             "ppm","ppm","ucum:ppm","Ammonia",
                                                             "Ammonia")
            temp_properties["Carbon monoxide"] = OgcObservedProperty("Carbon monoxide",
                                                                     normal_observation,api,"ppm",
                                                                     "ppm","ucum:ppm",
                                                                     "Carbon monoxide",
                                                                     "Carbon monoxide")
            temp_properties["Oxygen"] = OgcObservedProperty("Oxygen",normal_observation,api,"ppm",
                                                            "ppm","ucum:ppm","Oxygen","Oxygen")
            temp_properties["Hydrogen"] = OgcObservedProperty("Hydrogen",normal_observation,api,
                                                              "ppm","ppm","ucum:ppm","Hydrogen",
                                                              "Hydrogen")
            temp_properties["Chlorine"] = OgcObservedProperty("Chlorine",normal_observation,api,
                                                              "ppm","ppm","ucum:ppm","Chlorine",
                                                              "Chlorine")
            temp_properties["Florine"] = OgcObservedProperty("Florine",normal_observation,api,
                                                             "ppm","ppm","ucum:ppm","Florine",
                                                             "Florine")
            temp_properties["Hydrogen cyanide"] = OgcObservedProperty("Hydrogen cyanide",
                                                                      normal_observation,api,"ppm",
                                                                      "ppm","ucum:ppm",
                                                                      "Hydrogen cyanide",
                                                                      "Hydrogen cyanide")
            temp_properties["Sulfur dioxide"] = OgcObservedProperty("Sulfur dioxide",
                                                                    normal_observation,api,"ppm",
                                                                    "ppm","ucum:ppm",
                                                                    "Sulfur dioxide",
                                                                    "Sulfur dioxide")
            temp_properties["Phosphine"] = OgcObservedProperty("Phosphine",normal_observation,api,
                                                               "ppm","ppm","ucum:ppm","Phosphine",
                                                               "Phosphine")
            observed_properties[system] = temp_properties

        elif system == "COILS":
            sensors[system] = OgcSensor(system,api)
            temp_properties = {}
            temp_properties["Position_Data"] = OgcObservedProperty("Position_Data",
                                                                   normal_observation,api,
                                                                   "Geo coordinates",
                                                                   "Geo coordinates",
                                                                   "Geo coordinates",
                                                                   "Position_Data","Position_Data")
            observed_properties[system] = temp_properties

        elif system == "VSAS_UAV":
            sensors[system] = OgcSensor(system,api)
            temp_properties = {}
            temp_properties["Location"] = OgcObservedProperty("Location",normal_observation,api,
                                                              "Geo coordinates","Geo coordinates",
                                                              "Geo coordinates","Location",
                                                              "Location")
            temp_properties["Object detected"] = OgcObservedProperty("Object detected",
                                                                     normal_observation,api,
                                                                     "Object class","Object class",
                                                                     "Object class",
                                                                     "Object detected",
                                                                     "Object detected")
            temp_properties["Videostream"] = OgcObservedProperty("Videostream",normal_observation,
                                                                 api,"URL","URL","URL",
                                                                 "Videostream","Videostream")
            observed_properties[system] = temp_properties

        elif system == "ADS":
            sensors[system] = OgcSensor(system,api)
            temp_properties = {}
            temp_properties["ADS"] = OgcObservedProperty("ADS",normal_observation,api,
                                                         "Audio class","Audio class","Audio class",
                                                         "ADS","ADS")
            observed_properties[system] = temp_properties
        else: # IMS
            sensors[system] = OgcSensor(system,api)
            temp_properties = {}

    print(".......Setting up datastreams........")
    datastreams = {}
    for fr_name,thing_config in fr_things_config.items():
        temp_thing_id = thing_config.iot_id
        temp_thing_call_sign = thing_config.call_sign
        # temp_subsystems_name = thing_config.systems
        sensor_datastream_map = {}
        for system_name in thing_config.systems:
            temp_sensor_id = sensors[system_name].iot_id
            temp_sensor_name = sensors[system_name].name
            temp_obs_properties = observed_properties[system_name]
            temp_datastreams = {}
            # headers,url = get_create_datastream_header_url(cloud_access,system_name)
            for op_name,op in temp_obs_properties.items():
                temp_op_id = op.iot_id
                temp_datastreams[op_name] = DataStream(temp_thing_id, temp_sensor_id,
                                                       temp_sensor_name, temp_op_id, fr_name,
                                                         temp_thing_call_sign,
                                                         temp_obs_properties[op_name],api)
            sensor_datastream_map[system_name] = temp_datastreams
        datastreams[fr_name] = sensor_datastream_map

    for uav_name,thing_config in uav_things_config.items():
        temp_thing_id = uav_things_config[uav_name].iot_id
        temp_thing_call_sign = uav_things_config[uav_name].call_sign
        sensor_datastream_map = {}
        for system_name in uav_things_config[uav_name].systems:
            temp_sensor_id = sensors[system_name].iot_id
            temp_sensor_name = sensors[system_name].name
            temp_obs_properties = observed_properties[system_name]
            temp_datastreams = {}
            for op_name,op in temp_obs_properties.items():
                temp_op_id = op.iot_id
                temp_datastreams[op_name] = DataStream(temp_thing_id, temp_sensor_id,
                                                       temp_sensor_name,temp_op_id, uav_name,
                                                       temp_thing_call_sign,
                                                       temp_obs_properties[op_name],api)
            sensor_datastream_map[system_name] = temp_datastreams
        datastreams[uav_name] = sensor_datastream_map

    return fr_things_config,uav_things_config,sensors,observed_properties,datastreams

class DataStream():
    """
    Object to store data streams.
    Each OGC-datastream in an instance of calss dataStream
    """
    def __init__(self,thing_id, sensor_id,sensor_name,observation_property_id, thing_name,
                 thing_call_sign, observation_property, api):
        self.thing_name = thing_name
        self.datastream_name = observation_property.datastream_name + "-" +\
                                sensor_name + "-"+ thing_call_sign
        self.datastream_desc = observation_property.datastream_desc + " " + thing_name
        self.datastream_observationtype = "http://www.opengis.net/def/observationType/OGC-OM/2.0/OM_Measurement"
        self.unit_of_measurement_name = observation_property.unit_of_measurement_name
        self.unit_of_measurement_symbol = observation_property.unit_of_measurement_symbol
        self.unit_of_measurement_definition = observation_property.unit_of_measurement_definition
        self.iot_id = self.create_ogc_datastream(thing_id,sensor_id,sensor_name,
                                                 observation_property_id,observation_property.name,
                                                 api)

    def create_ogc_datastream(self,thing_id,sensor_id,sensor_name,observation_property_id,
                               observation_property_name,api):
        """
        create physical datastream on OGC server
        Return: datastream ID
        """
        payload = json.dumps({"name": self.datastream_name,
                                "description": self.datastream_desc,
                                "observationType": self.datastream_observationtype,
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
        response = api.create_datastream(payload)
        ds_url = response.headers["Location"]
        ds_id  = re.split("[()]",ds_url)[-2]
        print(f"................... Datastream  {ds_id} created: Thing = {self.thing_name}  \
                Sensor_name = {sensor_name}  OP = {observation_property_name}")
        return int(ds_id)

class UavOgcThing():
    """
    Thing definition for the UAV
    """
    def __init__(self,name,uav_id,organization,call_sign,cds_id,ads_id,vsas_id,ims_id,trigger_at,
                 movement_data,api):
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
        self.description = "The thing description for the uav "+ self.name
        self.start_lat = movement_data["start"][0]
        self.start_lon = movement_data["start"][1]
        self.speed = movement_data["speed"]
        self.waypoints_delay = movement_data["waypoints_delay"]
        self.close_loop = movement_data["close_loop"]
        self.api = api
        self.iot_id = self.create_ogc_thing()

    def get_subsystems(self):
        """
        Return a list of subsystm names attached to the thing
        Return: List of Str
        """
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

    def create_ogc_thing(self):
        """
        create physical Thing for UAV on OGC server
        Return: Int (Thing ID)
        """
        payload = json.dumps({"name": self.name,
                              "description":self.description,
                              "properties":{"type":self.type,
                                            #"uav_id":self.uav_id,
                                            "organization":self.organization,
                                            "callsign":self.call_sign,
                                            "systems":self.lower_case_system}})
        response = self.api.create_thing(payload)
        thing_url = response.headers["Location"]
        thing_id  = re.split("[()]",thing_url)[-2]
        print(f"{self.name} UAV thing is created with ID {thing_id}")
        return int(thing_id)

    def delete_ogc_thing(self):
        """
        Delete the thing definition on the OGC server
        """
        response = self.api.delete_thing(self.iot_id)
        print(response)

class FirstResponderOgcThing():
    """
    Thing definition for the FR
    """
    def __init__(self,name,fr_id,identifier,organization,role,subrole,team,call_sign,cds_id,ams_id,
                 vsas_id,coils_id,trigger_at,movement_data,api):
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
        self.api = api
        self.iot_id = self.create_ogc_thing()

    def create_ogc_thing(self):
        """
        create physical Thing for FR on OGC server
        Return: Int (Thing ID)
        """
        payload = json.dumps({"name": self.name,
                              "description":self.description,
                              "properties":{"type":self.type,
                                            "role":self.role,
                                            "organization":self.organization,
                                            "subrole":self.subrole,
                                            "callsign":self.call_sign,
                                            "systems":self.lower_case_system,
                                            "team":self.team}})
        response = self.api.create_thing(payload)
        thing_url = response.headers["Location"]
        thing_id  = re.split("[()]",thing_url)[-2]
        print(f"{self.name} FR thing is created with ID {thing_id}")
        return int(thing_id)

    def delete_ogc_thing(self):
        """
        Delete the thing definition on the OGC server
        """
        response = self.api.delete_thing(self.iot_id)
        print(response)

    def get_subsystems(self):
        """
        Return a list of subsystm names attached to the thing
        Return: List of Str
        """
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

class OgcSensor():
    """
    OGC sensor definition for each sensor
    """
    def __init__(self,name,api):
        self.name = name
        self.description = self.name + " Sensor"
        self.encoding_type = "application/pdf"
        self.metadata = self.name + " description pdf comes here"
        self.api = api
        self.iot_id = self.create_ogc_sensor()

    def create_ogc_sensor(self):
        """
        create physical Thing for FR on OGC server
        Return: Int (Sensor ID)
        """
        # create sensor in here and return sensor id
        payload = json.dumps({"name": self.name,
                              "description":self.description,
                              "encodingType":self.encoding_type,
                              "metadata":self.metadata})

        response = self.api.create_sensor(payload)
        sensor_url = response.headers["Location"]
        sensor_id  = re.split("[()]",sensor_url)[-2]
        print(f"{self.name} is created with ID {sensor_id}")
        return int(sensor_id)

    def delete_ogc_sensor(self):
        """
        Delete the sensor definition on the OGC server
        """
        response = self.api.delete_sensor(self.iot_id)
        print(response)

class OgcObservedProperty():
    """
    OGC Observed property definition for each observed property
    """
    def __init__(self,name,normal_observations,api,unit_of_measurement_name=None,
                 unit_of_measurement_symbol=None,unit_of_measurement_definition=None,
                 datastream_name=None,datastream_desc=None):
        self.name = name
        self.description = name
        self.definition = name
        self.unit_of_measurement_name = unit_of_measurement_name
        self.unit_of_measurement_symbol = unit_of_measurement_symbol
        self.unit_of_measurement_definition = unit_of_measurement_definition
        self.datastream_name = datastream_name
        self.datastream_desc = datastream_desc
        # is_categorical is False when its a regression feat and True if a categorical feature
        self.is_categorical,self.normal_values = self.get_normal_values(normal_observations)
        self.api = api
        self.iot_id = self.create_ogc_observed_property()

    def create_ogc_observed_property(self):
        """
        create physical definition of Observed property on OGC server
        Return: Int (Thing ID)
        """
        payload = json.dumps({"name": self.name,
                              "description":self.description,
                              "definition":self.definition})
        response = self.api.create_observed_property(payload)
        op_url = response.headers["Location"]
        op_id  = re.split("[()]",op_url)[-2]
        print(f"..... {self.name} Observed property is created with ID {op_id}")
        return int(op_id)

    def get_normal_values(self,normal_observations):
        """
        Return is_categorical (bool) and normal destribution of the observed property
        normal distributin format:
            category: [list of labels,probability of each label]
            gaussion: [mean,variance]
        Return: bool, list 
        """
        try:
            is_categorical = False
            temp = normal_observations[self.name]
            if temp[0] == "C":
                is_categorical = True
            return is_categorical, temp[1:]
        except KeyError:
            return None,None
    def delete_ogc_observed_property(self):
        """
        Delete the observed property definition on the OGC server
        """
        response = self.api.delete_observed_property(self.iot_id)
        print(response)
    
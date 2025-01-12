import requests
import json
import re
import random
import numpy as np
from turfpy import measurement
from geojson import Point, Feature
from sensors_new import ActivityMonitoringSubsystem, ChemicalDetectionSubsystem, ContIndoOutLocSubsystem, VisualSceneAnalysisHelmetSubsystem
#! update these imports with the UAV based subsystems
from sensors_new import AcousticsDetectionSubsystem, VisualSceneAnalysisSubsystemUav, InfraMonitoringSubsystem
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class FirstResponder():
    def __init__(self,env,thing,sensors,observed_properties,datastreams,cloud_access,events):
        self.env = env
        self.thing = thing
        self.sensors = sensors
        self.observed_properties = observed_properties
        self.cloud_access = cloud_access
        self.datastreams = datastreams
        self.current_lat = self.thing.start_lat
        self.current_lon = self.thing.start_lon
        self.current_alt = 0
        self.events = events
        self.subsystems = []
        self.env.process(self.trigger_thing())
        self.env.process(self.send_thing_location())
    
    def trigger_thing(self):
        yield self.env.timeout(self.thing.trigger_at) 
        # send the initial location
        data = self.get_location_payload()

        url = self.cloud_access.general_api.url_create_location_for_thing(self.thing.thing_id)
        headers = self.cloud_access.general_api.fetch_headers()
        response = requests.request("POST", url,
                                    headers=headers,
                                    data=data,
                                    verify=False) 
        # update the location with very high frequency 
        print("Posted first location for FR {} at time {}".format(self.thing.name,self.env.now)) 
        self.env.process(self.update_3d_location())
        self.start_subsystems()
    
    def update_3d_location(self):
        delta_t = 0.5 # refresh rate to calculate the location
        i = 0
        while True:
            current_loc = Feature(geometry=Point((self.current_lat,self.current_lon)))
            w_t = Feature(geometry=Point((self.thing.waypoints_delay[i][0],self.thing.waypoints_delay[i][1])))
            dist_w_t = measurement.distance(current_loc,w_t,units="m")
            bearing = measurement.bearing(current_loc,w_t) + 0 if dist_w_t > 4 else np.random.uniform(-0.1,0.1)
            travel_dist = self.thing.speed * delta_t
            destination = measurement.destination(current_loc, travel_dist, bearing, {"units" : "m"})
            self.write_current_loc(destination)
            current_loc = destination["geometry"]
            if measurement.distance(current_loc,w_t,units="m") < 6:
                yield self.env.timeout(self.thing.waypoints_delay[i][2])
                i += 1
                if i >= len(self.thing.waypoints_delay):
                    if self.thing.close_loop:
                        # this condition takes care of redirecting to the first location
                        i = 0
                    else:
                        break
            else:
                yield self.env.timeout(delta_t)
        while True:
            yield self.env.timeout(1)

    def write_current_loc(self,destination):
        self.current_lat = destination["geometry"]["coordinates"][0]
        self.current_lon = destination["geometry"]["coordinates"][1]

    def send_thing_location(self):
        yield self.env.timeout(self.thing.trigger_at)
        while True:
            yield self.env.timeout(self.get_delay())
            data=self.get_location_payload()
            response = requests.request("POST", self.cloud_access.general_api.url_create_location_for_thing(self.thing.thing_id),
                                        headers=self.cloud_access.general_api.fetch_headers(),#get_headers(),
                                        data=data,
                                        verify=False)
            
    def get_location_payload(self):
        # latitude, longitude, altitude = self.get_location()
        payload = json.dumps({"name": "Carrier {} Location".format(self.thing.name),
                              "description": "Carrier {} Location".format(self.thing.name),
                              "encodingType": "application/geo+json",
                              "location": {
                                  "type": "Feature",
                                  "geometry": {"coordinates": [self.current_lat, self.current_lon],#, self.current_alt],
                                                "type": "Point"}
                                                }
                            })
        return payload

    def get_location(self):
        return self.current_lat, self.current_lon, self.current_alt
    
    def get_delay(self):
        return random.randint(1, 2)
        
    def start_subsystems(self):
        for sensor_name in self.thing.systems:
            self.subsystems.append(self.get_subsystem(sensor_name,self.sensors[sensor_name],self.observed_properties[sensor_name],self.datastreams[sensor_name]))

    def get_subsystem(self,sensor_name,sensor,sel_obs_prop,sel_datastreams):
        if sensor_name == "AMS":
            return ActivityMonitoringSubsystem(self.env, self.thing,sensor,sel_obs_prop,sel_datastreams,
                                                self.cloud_access.ams_api,self.events.fr_health_events, self.get_location)
        elif sensor_name == "VSAS_FR":
            return VisualSceneAnalysisHelmetSubsystem(self.env, self.thing,sensor,sel_obs_prop,sel_datastreams,
                                                self.cloud_access.vsas_api,self.events.victims, self.get_location)
        elif sensor_name == "CDS":
            return ChemicalDetectionSubsystem(self.env, self.thing,sensor,sel_obs_prop,sel_datastreams,
                                                self.cloud_access.cds_api,self.events.chem_events, self.get_location)
        else:
            return ContIndoOutLocSubsystem(self.env, self.thing,sensor,sel_obs_prop,sel_datastreams,
                                            self.cloud_access.coils_api, self.get_location)
        
class UAV():
    def __init__(self,env,thing,sensors,observed_properties,datastreams,cloud_access,events):
        self.env = env
        self.thing = thing
        self.sensors = sensors
        self.observed_properties = observed_properties
        self.cloud_access = cloud_access
        self.datastreams = datastreams
        self.current_lat = self.thing.start_lat
        self.current_lon = self.thing.start_lon
        self.current_alt = 0
        self.events = events
        self.subsystems = []
        # this 
        self.env.process(self.trigger_thing())
        self.env.process(self.send_thing_location())

    def trigger_thing(self):
        yield self.env.timeout(self.thing.trigger_at) 
        url = self.cloud_access.general_api.url_create_location_for_thing(self.thing.thing_id)
        headers = self.cloud_access.general_api.fetch_headers()
        data = self.get_location_payload()
        response = requests.request("POST", url,
                                    headers=headers,
                                    data=data,
                                    verify=False) 
        # update the location with very high frequency 
        print("Posted first location for UAV {} at time {}".format(self.thing.name,self.env.now)) 
        self.env.process(self.update_3d_location())
        self.start_subsystems()

    def update_3d_location(self):
        delta_t = 0.1 # refresh rate to calculate the location
        i = 0
        while True:
            current_loc = Feature(geometry=Point((self.current_lat,self.current_lon)))
            w_t = Feature(geometry=Point((self.thing.waypoints_delay[i][0],self.thing.waypoints_delay[i][1])))
            dist_w_t = measurement.distance(current_loc,w_t,units="m")
            bearing = measurement.bearing(current_loc,w_t) + 0 if dist_w_t > 4 else np.random.uniform(-0.1,0.1)
            travel_dist = self.thing.speed * delta_t
            destination = measurement.destination(current_loc, travel_dist, bearing, {"units" : "m"})
            self.write_current_loc(destination)
            current_loc = destination["geometry"]
            if measurement.distance(current_loc,w_t,units="m") < 6:
                yield self.env.timeout(self.thing.waypoints_delay[i][3])
                i += 1
                if i >= len(self.thing.waypoints_delay):
                    if self.thing.close_loop:
                        # this condition takes care of redirecting to the first location
                        i = 0
                    else:
                        break
            else:
                yield self.env.timeout(delta_t)
        while True:
            yield self.env.timeout(1)
        
    def send_thing_location(self):
        yield self.env.timeout(self.thing.trigger_at)
        while True:
            yield self.env.timeout(self.get_delay())
            response = requests.request("POST", self.cloud_access.general_api.url_create_location_for_thing(self.thing.thing_id),
                                        headers=self.cloud_access.general_api.fetch_headers(),#get_headers(),
                                        data=self.get_location_payload(),
                                        verify=False)

    def write_current_loc(self,destination):
        self.current_lat = destination["geometry"]["coordinates"][0]
        self.current_lon = destination["geometry"]["coordinates"][1]

    def get_location_payload(self):
        # latitude, longitude, altitude = self.get_location()
        payload = json.dumps({"name": "Carrier {} Location".format(self.thing.name),
                              "description": "Carrier {} Location".format(self.thing.name),
                              "encodingType": "application/geo+json",
                              "location": {
                                  "type": "Feature",
                                  "geometry": {"coordinates": [self.current_lat, self.current_lon, self.current_alt],
                                                "type": "Point"}
                                                }
                            })
        return payload

    def get_location(self):
        return self.current_lat, self.current_lon, self.current_alt
    
    def get_delay(self):
        return random.randint(1, 2)
        
    def start_subsystems(self):
        for sensor_name in self.thing.systems:
            self.subsystems.append(self.get_subsystem(sensor_name,self.sensors[sensor_name],self.observed_properties[sensor_name],self.datastreams[sensor_name]))

    def get_subsystem(self,sensor_name,sensor,sel_obs_prop,sel_datastreams):
        if sensor_name == "ADS":
            return AcousticsDetectionSubsystem(self.env, self.thing,sensor,sel_obs_prop,sel_datastreams,
                                                self.cloud_access.ads_api,self.events.audio_events, self.get_location)
        if sensor_name == "VSAS_UAV":
            return VisualSceneAnalysisSubsystemUav(self.env, self.thing,sensor,sel_obs_prop,sel_datastreams,
                                                self.cloud_access.vsas_api,self.events.victims, self.get_location)
        elif sensor_name == "CDS":
            return ChemicalDetectionSubsystem(self.env, self.thing,sensor,sel_obs_prop,sel_datastreams,
                                                self.cloud_access.cds_api,self.events.chem_events, self.get_location)
        else:
            return InfraMonitoringSubsystem(self.env, self.thing,sensor,sel_obs_prop,sel_datastreams,
                                            self.cloud_access.ims_api,self.events.infrastructure_events, self.get_location)
import random
import json
import numpy as np
from turfpy import measurement
from geojson import Point, Feature
import urllib3
from sensors_new import ActivityMonitoringSubsystem, ChemicalDetectionSubsystem
from sensors_new import ContIndoOutLocSubsystem, VisualSceneAnalysisHelmetSubsystem
from sensors_new import AcousticsDetectionSubsystem, VisualSceneAnalysisSubsystemUav
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class FirstResponder():
    """
    Instance of physical representation of first responder in the simulation
    """
    def __init__(self,env,thing,sensors,observed_properties,datastreams,events):
        self.env = env
        self.thing = thing
        self.sensors = sensors
        self.observed_properties = observed_properties
        self.datastreams = datastreams
        self.current_lat = self.thing.start_lat
        self.current_lon = self.thing.start_lon
        self.current_alt = 0
        self.events = events
        self.subsystems = []
        self.env.process(self.trigger_thing())
        self.env.process(self.send_thing_location())

    def trigger_thing(self):
        """
        Send first location of the thing to OGC server
        Function call to initiate all the associated sensors
        """
        yield self.env.timeout(self.thing.trigger_at)
        # send the initial location
        data = self.get_location_payload()
        response = self.thing.api.send_thing_location(data)
        print(response)
        # update the location with very high frequency
        print(f"Posted first location for FR {self.thing.name} at time {self.env.now}")
        print(self.env.now)
        self.env.process(self.update_3d_location())
        self.start_subsystems()

    def update_3d_location(self):
        """
        Calculate the 3D location of FR with high refresh rate.
        """
        delta_t = 0.5 # refresh rate to calculate the location
        i = 0
        while True:
            current_loc = Feature(geometry=Point((self.current_lat,self.current_lon)))
            w_t = Feature(geometry=Point((self.thing.waypoints_delay[i][0],
                                          self.thing.waypoints_delay[i][1])))
            dist_w_t = measurement.distance(current_loc,w_t,units="m")
            bearing = measurement.bearing(current_loc,w_t) + 0 \
                                        if dist_w_t > 4 else np.random.uniform(-0.1,0.1)
            travel_dist = self.thing.speed * delta_t
            destination = measurement.destination(current_loc,
                                                  travel_dist, bearing, {"units" : "m"})
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
        """
        Update the instance variable for current location
        """
        self.current_lat = destination["geometry"]["coordinates"][0]
        self.current_lon = destination["geometry"]["coordinates"][1]

    def send_thing_location(self):
        """
        Send thing location to the OGC server
        """
        yield self.env.timeout(self.thing.trigger_at)
        while True:
            yield self.env.timeout(self.get_delay())
            data=self.get_location_payload()
            _response = self.thing.api.send_thing_location(data)
            # print(response)

    def get_location_payload(self):
        """
        Return the location payload prepared in accordnce with the OGC standards
        """
        # latitude, longitude, altitude = self.get_location()
        payload = json.dumps({"name": f"Carrier {self.thing.name} Location",
                              "description": f"Carrier {self.thing.name} Location",
                              "encodingType": "application/geo+json",
                              "location": {
                                  "type": "Feature",
                                  "geometry": {"coordinates": [self.current_lat, self.current_lon],
                                                "type": "Point"}
                                            },
                                "Things":[{"@iot.id":self.thing.iot_id}]
                            })
        return payload

    def get_location(self):
        """
        Public function to return the current location of thing
        """
        return self.current_lat, self.current_lon, self.current_alt

    def get_delay(self):
        """
        Return delay time to send the next message to the OGC server
        """
        return random.randint(1, 2)

    def start_subsystems(self):
        """
        Fetch and start all the sensors
        """
        for sensor_name in self.thing.systems:
            self.subsystems.append(self.get_subsystem(sensor_name,self.sensors[sensor_name],
                                                      self.observed_properties[sensor_name],
                                                      self.datastreams[sensor_name]))

    def get_subsystem(self,sensor_name,sensor,sel_obs_prop,sel_datastreams):
        """
        Return associated object representatin of physical sensor
        While calling also triggers them 
        """
        send_observation = self.thing.api.send_observation
        if sensor_name == "AMS":
            return ActivityMonitoringSubsystem(self.env, self.thing,sensor,sel_obs_prop,
                                               sel_datastreams,send_observation,
                                               self.events.fr_health_events, self.get_location)
        if sensor_name == "VSAS_FR":
            return VisualSceneAnalysisHelmetSubsystem(self.env, self.thing,sensor,sel_obs_prop,
                                                      sel_datastreams,send_observation,
                                                      self.events.victims, self.get_location)
        if sensor_name == "CDS":
            return ChemicalDetectionSubsystem(self.env, self.thing,sensor,sel_obs_prop,
                                              sel_datastreams,send_observation,
                                              self.events.chem_events, self.get_location)
        else:
            return ContIndoOutLocSubsystem(self.env, self.thing,sensor,sel_obs_prop,
                                           sel_datastreams,send_observation, self.get_location)

class UAV():
    """
    Instance of physical representation of UAV in the simulation
    """
    def __init__(self,env,thing,sensors,observed_properties,datastreams,events):
        self.env = env
        self.thing = thing
        self.sensors = sensors
        self.observed_properties = observed_properties
        self.datastreams = datastreams
        self.current_lat = self.thing.start_lat
        self.current_lon = self.thing.start_lon
        self.current_alt = 0
        self.events = events
        self.subsystems = []
        self.env.process(self.trigger_thing())
        self.env.process(self.send_thing_location())

    def trigger_thing(self):
        """
        Send first location of the thing to OGC server
        Function call to initiate all the associated sensors
        """
        yield self.env.timeout(self.thing.trigger_at)
        data = self.get_location_payload()
        response = self.thing.api.send_thing_location(data)
        print(response)
        # update the location with very high frequency
        print(f"Posted first location for UAV {self.thing.name} at time {self.env.now}")
        self.env.process(self.update_3d_location())
        self.start_subsystems()

    def update_3d_location(self):
        """
        Calculate the 3D location of FR with high refresh rate.
        """
        delta_t = 0.1 # refresh rate to calculate the location
        i = 0
        while True:
            current_loc = Feature(geometry=Point((self.current_lat,self.current_lon)))
            w_t = Feature(geometry=Point((self.thing.waypoints_delay[i][0],
                                          self.thing.waypoints_delay[i][1])))
            dist_w_t = measurement.distance(current_loc,w_t,units="m")
            bearing = measurement.bearing(current_loc,w_t) + 0 \
                                        if dist_w_t > 4 else np.random.uniform(-0.1,0.1)
            travel_dist = self.thing.speed * delta_t
            destination = measurement.destination(current_loc, travel_dist,
                                                  bearing, {"units" : "m"})
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
        """
        Send thing location to the OGC server
        """
        yield self.env.timeout(self.thing.trigger_at)
        while True:
            yield self.env.timeout(self.get_delay())
            data=self.get_location_payload()
            _response = self.thing.api.send_thing_location(data)
            # print(response)

    def write_current_loc(self,destination):
        """
        Update the instance variable for current location
        """
        self.current_lat = destination["geometry"]["coordinates"][0]
        self.current_lon = destination["geometry"]["coordinates"][1]

    def get_location_payload(self):
        """
        Return the location payload prepared in accordnce with the OGC standards
        """
        # latitude, longitude, altitude = self.get_location()
        payload = json.dumps({"name": f"Carrier {self.thing.name} Location",
                              "description": f"Carrier {self.thing.name} Location",
                              "encodingType": "application/geo+json",
                              "location": {
                                  "type": "Feature",
                                  "geometry": {"coordinates": [self.current_lat,
                                                               self.current_lon,
                                                               self.current_alt],
                                                "type": "Point"}
                                                },
                                "Things":[{"@iot.id":self.thing.iot_id}]
                            })
        return payload

    def get_location(self):
        """
        Public function to return the current location of thing
        """
        return self.current_lat, self.current_lon, self.current_alt

    def get_delay(self):
        """
        Return delay time to send the next message to the OGC server
        """
        return random.randint(1, 2)

    def start_subsystems(self):
        """
        Fetch and start all the sensors
        """
        for sensor_name in self.thing.systems:
            self.subsystems.append(self.get_subsystem(sensor_name,self.sensors[sensor_name],
                                                      self.observed_properties[sensor_name],
                                                      self.datastreams[sensor_name]))

    def get_subsystem(self,sensor_name,sensor,sel_obs_prop,sel_datastreams):
        """
        Return associated object representatin of physical sensor
        While calling also triggers them 
        """
        send_observation = self.thing.api.send_observation
        if sensor_name == "ADS":
            return AcousticsDetectionSubsystem(self.env, self.thing,sensor,sel_obs_prop,
                                               sel_datastreams,send_observation,
                                               self.events.audio_events, self.get_location)
        if sensor_name == "VSAS_UAV":
            return VisualSceneAnalysisSubsystemUav(self.env, self.thing,sensor,sel_obs_prop,
                                                   sel_datastreams,send_observation,
                                                   self.events.victims, self.get_location)
        if sensor_name == "CDS":
            return ChemicalDetectionSubsystem(self.env, self.thing,sensor,sel_obs_prop,
                                              sel_datastreams,send_observation,
                                              self.events.chem_events, self.get_location)

import requests
import json
import re
import random
import numpy as np
from turfpy import measurement
from geojson import Point, Feature
from datetime import datetime

# Completed
class GeneralSensor():
    def __init__(self,env,thing,sensor,observed_properties,datastreams,cloud_api,location_finder):
        self.env = env
        self.thing = thing
        self.sensor = sensor
        self.observed_properties = observed_properties
        self.cloud_api = cloud_api
        self.location_finder = location_finder
        self.datastreams = datastreams

    def send_message(self,payload,headers,url):
        response = requests.request("POST", url, headers=headers, data=payload, verify=False)
        # print()

    def get_location_payload(self):
        latitude, longitude, altitude = self.location_finder()
        payload = json.dumps({"name": "Carrier {} Location".format(self.carrier_name),
                              "description": "Carrier {} Location".format(self.carrier_name),
                              "encodingType": "application/geo+json",
                              "location": {
                                  "type": "Feature",
                                  "geometry": {"coordinates": [latitude, longitude, altitude],
                                                "type": "Point"}
                                                }
                            })
        return payload
    
    def get_observ_ideantfiers(self):
        # return a list of names of all the observed properties for this sensor
        observ_identifiers = []
        for observ in self.observed_properties:
            observ_identifiers.append(self.observed_properties[observ])
        return observ_identifiers

class ActivityMonitoringSubsystem(GeneralSensor):
    def __init__(self,env,thing,sensor,observed_properties,datastreams,cloud_api,fr_health_events,location_finder):
        super().__init__(env,thing,sensor,observed_properties,datastreams,cloud_api,location_finder)
        self.observation_identifiers = self.get_observ_ideantfiers()
        self.events = fr_health_events
        self.env.process(self.start_subsystem())

    def start_subsystem(self):
        url = self.cloud_api.url_send_observation()
        while True:
            yield self.env.timeout(self.get_delay())
            headers = self.cloud_api.fetch_headers()
            event_observations = self.check_health_events()
            #! figure out how to prepare the observation for message sending
            for observation in self.observation_identifiers:
                payload = self.prepare_payload(observation.name,event_observations)
                if payload:
                    self.send_message(payload,headers,url)  

    def check_health_events(self):
        event_observations = {}
        for event in self.events:
            if event.event.triggered:
                if event.name == self.thing.name:
                    event_observations[event.signal] = event.value
        return event_observations

    def prepare_payload(self,observation_name,event_observations):
        if observation_name == "Activity":
            payload = self.get_activity_payload(observation_name,self.datastreams[observation_name].id)
            return payload
        elif observation_name == "Heartrate":
            payload = self.get_heart_rate_payload(observation_name,self.datastreams[observation_name].id,event_observations)
            return payload
        elif observation_name == "Spo2":
            payload = self.get_blood_oxygen_sat_payload(observation_name,self.datastreams[observation_name].id,event_observations)
            return payload
        elif observation_name == "Skin temperature":
            payload = self.get_skin_temp_payload(observation_name,self.datastreams[observation_name].id,event_observations)
            return payload
        else: #observation_name == "Fall detection":
            payload = self.get_fall_det_payload(observation_name,self.datastreams[observation_name].id,event_observations)
            return payload

    def get_activity_payload(self,observation_name,datastream_id):
        confidence = np.random.uniform(0,1)
        fatigue = np.random.uniform(0,5)
        stress = np.random.uniform(0,5)
        activity_class = self.observed_properties[observation_name].normal_values[0]
        prob = self.observed_properties[observation_name].normal_values[1]
        result = np.random.choice(activity_class,p=prob)
        result_time = datetime.utcnow().isoformat()
        payload = json.dumps({"parameters": {"confidence": confidence, "fatigue": fatigue, "stress": stress},
                            "result": result,
                            "resultTime": result_time,
                            "Datastream": {"@iot.id": datastream_id}
                            })
        return payload

    def get_heart_rate_payload(self,observation_name,datastream_id,event_observations):
        confidence = np.random.uniform(0,1)
        try:
            result = event_observations[observation_name]
        except KeyError:
            mean_sd = self.observed_properties[observation_name].normal_values
            result = np.random.normal(mean_sd[0],mean_sd[1])

        result_time = datetime.utcnow().isoformat()
        status = "NORMAL"
        if result >=100:
            status = "HIGH"        
        payload = json.dumps({"parameters": {"confidence": confidence, "status":status},
                            "result": result,
                            "resultTime": result_time,
                            "Datastream": {"@iot.id": datastream_id}
                            })
        return payload

    def get_blood_oxygen_sat_payload(self,observation_name,datastream_id,event_observations):
        confidence = np.random.uniform(0,1)
        try:
            result = event_observations[observation_name]
        except KeyError:
            mean_sd = self.observed_properties[observation_name].normal_values
            result = np.random.normal(mean_sd[0],mean_sd[1])
        result_time = datetime.utcnow().isoformat()
        status = "NORMAL"
        if result < 92:
            status = "LOW" 
        payload = json.dumps({"parameters": {"confidence": confidence, "status":status},
                            "result": result,
                            "resultTime": result_time,
                            "Datastream": {"@iot.id": datastream_id}
                            })
        # return payload
        return payload
    
    def get_skin_temp_payload(self,observation_name,datastream_id,event_observations):
        confidence = np.random.uniform(0,1)
        try:
            result = event_observations[observation_name]
        except KeyError:
            mean_sd = self.observed_properties[observation_name].normal_values
            result = np.random.normal(mean_sd[0],mean_sd[1])
        result_time = datetime.utcnow().isoformat()
        status = "NORMAL"
        if result >= 40:
            status = "HIGH" 
        payload = json.dumps({"parameters": {"confidence": confidence,"status":status},
                            "result": result,
                            "resultTime": result_time,
                            "Datastream": {"@iot.id": datastream_id}
                            })
        # return payload
        return payload

    def get_fall_det_payload(self,observation_name,datastream_id,event_observations):
        confidence = np.random.uniform(0,1)
        try:
            fall_detected = event_observations[observation_name]
        except KeyError:
            fall_detection_labels = self.observed_properties[observation_name].normal_values[0]
            prob = self.observed_properties[observation_name].normal_values[1]
            fall_detected = np.random.choice(fall_detection_labels,p=prob)
        if fall_detected:
            result  = "Fall_Detected"
            result_time = datetime.utcnow().isoformat()
            payload = json.dumps({"parameters": {"confidence": confidence},
                                "result": result,
                                "resultTime": result_time,
                                "Datastream": {"@iot.id": datastream_id}
                                })
            return payload
        return None

    def get_no_motion_det_payload(self,observation_name,datastream_id):
        confidence = np.random.uniform(0,1)
        no_motion_labels = self.observed_properties[observation_name].normal_values[0]
        prob = self.observed_properties[observation_name].normal_values[1]
        no_motion_detected = np.random.choice(no_motion_labels,p=prob)
        if no_motion_detected:
            result  = "No_Motion_Detected"
            result_time = datetime.utcnow().isoformat()
            payload = json.dumps({"parameters": {"confidence": confidence},
                                "result": result,
                                "resultTime": result_time,
                                "Datastream": {"@iot.id": datastream_id}
                                })
            return payload
        return None
        
    def get_delay(self):
        return random.randint(1, 3)
class ChemicalDetectionSubsystem(GeneralSensor):
    def __init__(self,env,thing,sensor,observed_properties,datastreams,cloud_api,chem_events,location_finder):
        super().__init__(env,thing,sensor,observed_properties,datastreams,cloud_api,location_finder)
        self.observation_identifiers = self.get_observ_ideantfiers()
        self.events = chem_events
        self.env.process(self.start_subsystem())

    def start_subsystem(self):
        url = self.cloud_api.url_send_observation()
        while True:
            yield self.env.timeout(self.get_delay())
            headers = self.cloud_api.fetch_headers()
            event_observations = self.check_chem_events()
            #! figure out how to prepare the observation for message sending
            for observation in self.observation_identifiers:
                payload = self.prepare_payload(observation.name, event_observations)
                if payload:
                    self.send_message(payload,headers,url)
    def check_chem_events(self):
        event_observations = {}
        for event in self.events:
            if event.event.triggered:
                if self.in_range(event.latitude, event.longitude, event.range):
                    event_observations[event.name] = event.ppm
        return event_observations
    
    def in_range(self,event_lat, event_long, event_range):
        event_loc = Feature(geometry=Point((event_lat, event_long)))
        latitude, longitude, altitude = self.location_finder()
        current_loc = Feature(geometry=Point((latitude, longitude)))
        if measurement.distance(event_loc,current_loc,units="m") < event_range:
            return True
        else:
            return False
    
    def prepare_payload(self,observation_name, event_observations):
        try:
            result = event_observations[observation_name]
        except KeyError:
            mean_sd = self.observed_properties[observation_name].normal_values
            result = np.random.normal(mean_sd[0],mean_sd[1])

        result_time = datetime.utcnow().isoformat()
        location = self.location_finder()
        HR = np.random.normal(50,20)
        TP = np.random.normal(30,2)
        SP = np.random.uniform(0,5)
        LT = location[0]
        LG = location[1]
        AT = location[2]
        datastream_id = self.datastreams[observation_name].id
        payload = json.dumps({"parameters": {"humidity": HR, "temperature":TP, "speed":SP, "latitude":LT, "longitude":LG, "altidude":AT},
                            "result": result,
                            "resultTime": result_time,
                            "Datastream": {"@iot.id": datastream_id}
                            })
        return payload
        
    def get_delay(self):
        return random.randint(1, 3)
class VisualSceneAnalysisHelmetSubsystem(GeneralSensor):
    def __init__(self,env,thing,sensor,observed_properties,datastreams,cloud_api,victims,location_finder):
        super().__init__(env,thing,sensor,observed_properties,datastreams,cloud_api,location_finder)
        self.observation_identifiers = self.get_observ_ideantfiers()
        self.events = victims
        self.env.process(self.start_subsystem())

    def start_subsystem(self):
        url = self.cloud_api.url_send_observation()
        headers = self.cloud_api.fetch_headers()
        payload = self.get_video_url_payload(self.datastreams["Videostream"].id)
        self.send_message(payload,headers,url)
        while True:
            yield self.env.timeout(self.get_delay())
            headers = self.cloud_api.fetch_headers()
            event_observations = self.check_victims()
            #! figure out how to prepare the observation for message sending
            for observation in self.observation_identifiers:
                # prepare observation based on name of the observation

                # prepare payload so that its None if no message is supposed to be transmitted
                # here the payload is prepared as a list to handle multiple observations at once
                payloads = self.prepare_payload(observation.name,event_observations)
                if payloads:
                    for payload in payloads:
                        self.send_message(payload,headers,url)  

    def check_victims(self):
        event_observations = []
        for event in self.events:
            if event.event.triggered:
                if self.in_range(event.latitude, event.longitude):
                    event_observations.append(event)
        return event_observations 
    
    def in_range(self,event_lat, event_long, detection_range = 100):
        event_loc = Feature(geometry=Point((event_lat, event_long)))
        latitude, longitude, altitude = self.location_finder()
        current_loc = Feature(geometry=Point((latitude, longitude)))
        if measurement.distance(event_loc,current_loc,units="m") <= detection_range:
            return True
        else:
            return False

    def prepare_payload(self,observation_name,victims):
        if observation_name == "Location":
            payload = self.get_location_payload(self.datastreams[observation_name].id)
            return payload
        elif observation_name == "Object detected":
            payload = self.get_obj_det_payload(observation_name,
                                               self.datastreams[observation_name].id,
                                               victims)
            return payload
        elif observation_name == "Safe exit":
            payload = self.get_safe_exit_payload(observation_name,self.datastreams[observation_name].id)
            return payload
        else:
            return None
    
    def get_delay(self):
        return random.randint(1, 3)
    
    def get_video_url_payload(self,datastream_id):
        result_time = datetime.utcnow().isoformat()
        payload = json.dumps({"result": {"visible_stream": "rtsp://127.0.0.1:6000/visible",
                                        "infrared_stream": "rtsp://127.0.0.1:6000/infrared"},
                                "parameters": {},
                                "resultTime": result_time,
                                "Datastream": {"@iot.id": datastream_id}
                                })
        return payload
    
    def get_location_payload(self,datastream_id):
        result_time = datetime.utcnow().isoformat()
        location = self.location_finder()
        latitude = location[0]
        longitude = location[1]
        payload = json.dumps({"parameters": {},
                            "result": {"latitude": latitude, "longitude": longitude},
                            "resultTime": result_time,
                            "Datastream": {"@iot.id": datastream_id}
                            })
        return [payload]
    
    def get_obj_det_payload(self,observation_name,datastream_id,victims):
        objects = self.observed_properties[observation_name].normal_values[0]
        prob = self.observed_properties[observation_name].normal_values[1]
        num_obj_detected = 1
        detected_obj = np.random.choice(objects,p=prob,size=num_obj_detected)
        result_time = datetime.utcnow().isoformat()
        location = self.location_finder()
        latitude = location[0]
        longitude = location[1]
        relative_altitude = 1.0
        payloads = []
        for vi in victims:
            print("Victim {} found by {}".format(vi.number,self.thing.name))
            result = {"relative_altitude": relative_altitude,
                        "confidence":np.random.uniform(0.7,1.0),
                        "latitude": vi.latitude,
                        "longitude":vi.longitude,
                        "label":"person"}
            payload = json.dumps({"result":result,
                                "parameters":{},
                                "Datastream": {"@iot.id": datastream_id},
                                "resultTime": result_time})
            payloads.append(payload)
        for obj in detected_obj:
            result = {"relative_altitude": relative_altitude,
                        "confidence":np.random.uniform(0.6,1.0),
                        "latitude": latitude + np.random.uniform(-0.01,0.01),
                        "longitude":longitude + np.random.uniform(-0.01,0.01),
                        "label":obj}
            payload = json.dumps({"result":result,
                                "parameters":{},
                                "Datastream": {"@iot.id": datastream_id},
                                "resultTime": result_time})
            payloads.append(payload)
        return payloads
    
    def get_safe_exit_payload(self,observation_name,datastream_id):
        result_time = datetime.utcnow().isoformat()
        location = self.location_finder()
        latitude = location[0]
        longitude = location[1]
        relative_altitude = 1.0
        payloads = []
        num_coord_update = np.random.randint(0,5)
        update_delta = np.random.uniform(-0.01,0.01)
        for update in range(num_coord_update):
            result = {"relative_altitude": relative_altitude,
                      "latitude": latitude - (update+1)*update_delta,
                      "longitude":longitude - (update+1)*update_delta}
            payload = json.dumps({"result":result,
                                "parameters":{},
                                "Datastream": {"@iot.id": datastream_id},
                                "resultTime": result_time})
            payloads.append(payload)
        return payloads
class ContIndoOutLocSubsystem(GeneralSensor):
    def __init__(self,env,thing,sensor,observed_properties,datastreams,cloud_api,location_finder):
        super().__init__(env,thing,sensor,observed_properties,datastreams,cloud_api,location_finder)
        self.observation_identifiers = self.get_observ_ideantfiers()
        self.env.process(self.start_subsystem())

    def start_subsystem(self):
        url = self.cloud_api.url_send_observation()
        while True:
            yield self.env.timeout(self.get_delay())
            headers = self.cloud_api.fetch_headers()
            #! figure out how to prepare the observation for message sending
            for observation in self.observation_identifiers:
                # prepare observation based on name of the observation

                # prepare payload so that its None if no message is supposed to be transmitted
                payload = self.prepare_payload(observation.name)
                if payload:
                    self.send_message(payload,headers,url)

    def prepare_payload(self,observation_name):
        result_time = datetime.utcnow().isoformat()
        location = self.location_finder()
        LT = location[0]
        LG = location[1]
        AT = location[2]
        try:
            datastream_id = self.datastreams[observation_name].id
        except KeyError:
            print("error appeared")
        payload = json.dumps({"parameters": {"StepCounter": np.random.randint(1,1000),
                                            "DeviceId": np.random.randint(1,10),
                                            "BatteryStatus": np.random.uniform(0,100),
                                            "ExtraInfo": "#60059C025900090002FFFFEFFFFFC00027FCD1FECB000000000000000000CDDDFF0F7E37",
                                            "Flag": np.random.randint(1,100)},
                            "result": {"Lat": LT, "Long":LG, "MagBy": np.random.uniform(1,100), "MagBz": np.random.uniform(1,100),
                                        "EstAltiZ": np.random.uniform(1,100),"MagBx": np.random.uniform(1,100), "EstInertZ":np.random.uniform(1,100),
                                        "EstInertY": np.random.uniform(1,100),"EstInertX": np.random.uniform(1,100),"Matrix1x1": np.random.uniform(1,100),
                                        "Matrix1x3": np.random.uniform(1,100),"Matrix2x2": np.random.uniform(1,100),"Matrix3x1": np.random.uniform(1,100),
                                        "Matrix1x2": np.random.uniform(1,100),"Matrix2x1": np.random.uniform(1,100),"Matrix3x3": np.random.uniform(1,100),
                                        "Matrix2x3": np.random.uniform(1,100),"Matrix3x2": np.random.uniform(1,100)},
                            "resultTime": result_time,
                            "Datastream": {"@iot.id": datastream_id}})
        return payload
    
    def get_delay(self):
        return random.randint(1, 3)
    
class CitizenInvolCityIntegSubsystem():
    def __init__(self,env,events):
        self.env = env
        self.events = events
        self.env.process(self.send_messages())

    def send_messages(self):
        while True:
            for event in self.events:
                if event.event.triggered:
                    event.event = event.env.event()
            yield self.env.timeout(1)
class VisualSceneAnalysisSubsystemUav(GeneralSensor):
    def __init__(self,env,thing,sensor,observed_properties,datastreams,cloud_api,victims,location_finder):
        super().__init__(env,thing,sensor,observed_properties,datastreams,cloud_api,location_finder)
        self.observation_identifiers = self.get_observ_ideantfiers()
        self.events = victims
        self.env.process(self.start_subsystem())

    def start_subsystem(self):
        url = self.cloud_api.url_send_observation()
        headers = self.cloud_api.fetch_headers()
        payload = self.get_video_url_payload(self.datastreams["Videostream"].id)
        self.send_message(payload,headers,url)
        while True:
            yield self.env.timeout(self.get_delay())
            headers = self.cloud_api.fetch_headers()
            event_observations = self.check_victims()
            #! figure out how to prepare the observation for message sending
            for observation in self.observation_identifiers:
                # prepare observation based on name of the observation

                # prepare payload so that its None if no message is supposed to be transmitted
                # here the payload is prepared as a list to handle multiple observations at once
                payloads = self.prepare_payload(observation.name,event_observations)
                if payloads:
                    for payload in payloads:
                        self.send_message(payload,headers,url)  

    def check_victims(self):
        event_observations = []
        for event in self.events:
            if event.event.triggered:
                if self.in_range(event.latitude, event.longitude):
                    event_observations.append(event)
        return event_observations
    
    def in_range(self,event_lat, event_long, detection_range = 1000):
        event_loc = Feature(geometry=Point((event_lat, event_long)))
        latitude, longitude, altitude = self.location_finder()
        current_loc = Feature(geometry=Point((latitude, longitude)))
        if measurement.distance(event_loc,current_loc,units="m") <= detection_range:
            return True
        else:
            return False

    def prepare_payload(self,observation_name,victims):
        if observation_name == "Location":
            return self.get_location_payload(self.datastreams[observation_name].id)
        elif observation_name == "Object_Detection":
            return self.get_obj_det_payload(observation_name,
                                            self.datastreams[observation_name].id,
                                            victims)
        else:
            return None
    
    def get_delay(self):
        return random.randint(1, 3)
    
    def get_video_url_payload(self,datastream_id):
        result_time = datetime.utcnow().isoformat()
        payload = json.dumps({"result": {"visible_stream": "rtsp://127.0.0.1:6000/visible",
                                        "infrared_stream": "rtsp://127.0.0.1:6000/infrared"},
                                "parameters": {},
                                "resultTime": result_time,
                                "Datastream": {"@iot.id": datastream_id}
                                })
        return payload
    
    def get_location_payload(self,datastream_id):
        result_time = datetime.utcnow().isoformat()
        location = self.location_finder()
        latitude = location[0]
        longitude = location[1]
        payload = json.dumps({"parameters": {},
                            "result": {"latitude": latitude, "longitude": longitude},
                            "resultTime": result_time,
                            "Datastream": {"@iot.id": datastream_id}
                            })
        return [payload]
    
    def get_obj_det_payload(self,observation_name,datastream_id,victims):
        objects = self.observed_properties[observation_name].normal_values[0]
        prob = self.observed_properties[observation_name].normal_values[1]
        num_obj_detected = 1
        detected_obj = np.random.choice(objects,p=prob,size=num_obj_detected)
        result_time = datetime.utcnow().isoformat()
        location = self.location_finder()
        latitude = location[0]
        longitude = location[1]
        relative_altitude = 1.0
        payloads = []
        for vi in victims:
            print("Victim {} found by {}".format(vi.number,self.thing.name))
            result = {"relative_altitude": relative_altitude,
                        "confidence":np.random.uniform(0.7,1.0),
                        "latitude": vi.latitude,
                        "longitude":vi.longitude,
                        "label":"person"}
            payload = json.dumps({"result":result,
                                "parameters":{},
                                "Datastream": {"@iot.id": datastream_id},
                                "resultTime": result_time})
            payloads.append(payload)
        for obj in detected_obj:
            result = {"relative_altitude": relative_altitude,
                        "confidence":np.random.uniform(0.6,1.0),
                        "latitude": latitude + np.random.uniform(-0.01,0.01),
                        "longitude":longitude + np.random.uniform(-0.01,0.01),
                        "label":obj}
            payload = json.dumps({"result":result,
                                "parameters":{},
                                "Datastream": {"@iot.id": datastream_id},
                                "resultTime": result_time})
            payloads.append(payload)
        return payloads        
class AcousticsDetectionSubsystem(GeneralSensor):
    def __init__(self,env,thing,sensor,observed_properties,datastreams,cloud_api,audio_events,location_finder):
        super().__init__(env,thing,sensor,observed_properties,datastreams,cloud_api,location_finder)
        self.observation_identifiers = self.get_observ_ideantfiers()
        self.events = audio_events
        self.msgid = 1
        self.detection_map = {1:"primarydetection",
                              2:"secondarydetection"}
        self.env.process(self.start_subsystem())

    def start_subsystem(self):
        url = self.cloud_api.url_send_observation()
        while True:
            yield self.env.timeout(self.get_delay())
            headers = self.cloud_api.fetch_headers()
            event_observations = self.check_acoustic_events()
            #! figure out how to prepare the observation for message sending
            for observation in self.observation_identifiers:
                # prepare observation based on name of the observation

                # prepare payload so that its None if no message is supposed to be transmitted
                payload = self.prepare_payload(observation.name, event_observations)
                if payload:
                    self.send_message(payload,headers,url) 

    def check_acoustic_events(self):
        # check that this list will not exceed 2 and the pending events will not bleed out
        # of system without recording
        event_observations = []
        for event in self.events:
            # if event.event_triggered:
            if event.event.triggered:
                event_observations.append(event)
                event.reset_event()
                if len(event_observations) == 2:
                    break
        return event_observations
                    
    def get_delay(self):
        return random.randint(1, 3)
    
    def prepare_payload(self,observation_name, event_observations):
        num_audio_detected = 2
        tag_counter = 0
        parameters = {}
        for ev in event_observations:
            print("Acoustic event {} detected by {}".format(ev.label,self.thing.name))
            tag = ev.label
            confidence = ev.confidence
            azimuth = ev.azimuth
            elevation = ev.elevation
            parameters["elevation"+str(tag_counter+1)] = elevation
            parameters["azimuth"+str(tag_counter+1)] = azimuth
            parameters["confidence"+str(tag_counter+1)] = confidence
            parameters[self.detection_map[tag_counter+1]] = tag
            tag_counter += 1
        
        for i in range(num_audio_detected-tag_counter):
            audio_tags = self.observed_properties[observation_name].normal_values[0]
            prob = self.observed_properties[observation_name].normal_values[1]
            tag = np.random.choice(audio_tags,p=prob)
            confidence = np.random.uniform(0,1)
            relative_loc = np.random.uniform(-100,100,2)

            parameters["elevation"+str(tag_counter+1)] = relative_loc[0]
            parameters["azimuth"+str(tag_counter+1)] = relative_loc[1]
            parameters["confidence"+str(tag_counter+1)] = confidence
            parameters[self.detection_map[tag_counter+1]] = tag
            tag_counter += 1
        result_time = datetime.utcnow().isoformat()
        datastream_id = self.datastreams[observation_name].id
        location = self.location_finder()
        latitude = location[0]
        longitude = location[1]
        relative_altitude = np.random.uniform(10,100)
        result = {"droneModel": "DJI Matrice 300 RTK",
                  "Long": longitude,
                  "Alt": relative_altitude,
                  "msgid": self.msgid,
                  "Lat": latitude}
        payload = json.dumps({"result":result,
                            "parameters":parameters,
                            "Datastream": {"@iot.id": datastream_id},
                            "resultTime": result_time})
        self.msgid += 1
        return payload

class InfraMonitoringSubsystem(GeneralSensor):
    def __init__(self,env,carrier_identifier,subsystem_identifier,carrier_name,carrier_description,attached_systems,cloud_access,location_finder):
        super().__init__(env,carrier_identifier,subsystem_identifier,carrier_name,carrier_description,attached_systems,cloud_access,location_finder)
        self.subsystem_name = "IMS_UAV"
        self.carrier_type = "uav"
        self.thing_id = self.create_thing()
        self.env.process(self.start_subsystem())

    def get_headers(self):
        # header is same for all endpoints except for the "Get access token" which is already handled in authorization script
        authorization = self.cloud_access.ims_token.response_dict["token_type"] + " " + self.cloud_access.ims_token.response_dict["access_token"]
        headers = {'Content-Type': 'application/json',
                    'Authorization': authorization,
                    }# 'Cookie': 'JSESSIONID=72092BB6E428C04F5E0A51D0A451633C'}
        return headers
    
    def create_thing(self):
        headers = self.get_headers()
        payload = json.dumps({"name":self.carrier_name,
                              "description":self.carrier_description,
                              "properties": {"type": self.carrier_type,
                                             "role": "",
                                             "systems": self.attached_systems}})
        url = self.cloud_access.url_ims_create_thing_for_uav()
        response = requests.request("POST", url, headers=headers, data=payload, verify=False)
        thing_url = response.headers["Location"]
        thing_id  = re.split("[()]",thing_url)[-2]
        print (self.carrier_name,"  ",thing_id,"  ",self.attached_systems)
        return thing_id
    
    def start_subsystem(self):
        while True:
            yield self.env.timeout(self.get_delay())
            self.send_message(self.get_location_payload(), self.get_headers(), self.cloud_access.url_ims_create_location_for_uav(self.thing_id))
        
    def get_delay(self):
        return random.randint(1, 3)
    
    def delete_thing(self):
        headers = {'Authorization':self.get_headers()['Authorization']}
        payload = json.dumps({})
        url = self.cloud_access.url_ims_delete_thing_for_uav(self.thing_id)
        response = requests.request("DELETE", url, headers=headers, data=payload, verify=False)

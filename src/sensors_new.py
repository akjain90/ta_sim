import json
import random
from datetime import datetime
import numpy as np
from turfpy import measurement
from geojson import Point, Feature

# Completed
class GeneralSensor():
    """
    Parent class for all sensors.
    """
    def __init__(self,env,thing,sensor,observed_properties,datastreams,send_observation,
                 location_finder):
        self.env = env
        self.thing = thing
        self.sensor = sensor
        self.observed_properties = observed_properties
        self.send_observation = send_observation
        self.location_finder = location_finder
        self.datastreams = datastreams

    def get_observ_ideantfiers(self):
        """
        Return a list of OGC observed properties objects for this sensor
        """
        observ_identifiers = []
        for observ in self.observed_properties:
            observ_identifiers.append(self.observed_properties[observ])
        return observ_identifiers

class ActivityMonitoringSubsystem(GeneralSensor):
    """
    Class representation of Activity moniroring system
    """
    def __init__(self,env,thing,sensor,observed_properties,datastreams,send_observation,
                 fr_health_events,location_finder):
        super().__init__(env,thing,sensor,observed_properties,datastreams,
                         send_observation,location_finder)
        self.observation_identifiers = self.get_observ_ideantfiers()
        self.events = fr_health_events
        self.env.process(self.start_subsystem())

    def start_subsystem(self):
        """
        Triggers the operation of the sensor
        """
        while True:
            yield self.env.timeout(self.get_delay())
            event_observations = self.check_health_events()
            #! figure out how to prepare the observation for message sending
            for observation in self.observation_identifiers:
                payload = self.prepare_payload(observation.name,event_observations)
                if payload:
                    _response = self.send_observation(payload)

    def check_health_events(self):
        """
        Check if health event for thing is observed.
        Returns all the health active event observations of the associated thing at a given time
        """
        event_observations = {}
        for event in self.events:
            if event.event.triggered:
                if event.name == self.thing.name:
                    event_observations[event.signal] = event.value
        return event_observations

    def prepare_payload(self,observation_name,event_observations):
        """
        Prepare sensor payload as per OGC standard and sensor definition
        """
        if observation_name == "Activity":
            payload = self.get_activity_payload(observation_name,
            self.datastreams[observation_name].iot_id)
            # return payload
        elif observation_name == "Heartrate":
            payload = self.get_heart_rate_payload(observation_name,
                                                  self.datastreams[observation_name].iot_id,
                                                  event_observations)
            # return payload
        elif observation_name == "Spo2":
            payload = self.get_blood_oxygen_sat_payload(observation_name,
                                                        self.datastreams[observation_name].iot_id,
                                                        event_observations)
            # return payload
        elif observation_name == "Skin temperature":
            payload = self.get_skin_temp_payload(observation_name,
                                                 self.datastreams[observation_name].iot_id,
                                                 event_observations)
            # return payload
        #observation_name == "Fall detection":
        else:
            payload = self.get_fall_det_payload(observation_name,
                                                self.datastreams[observation_name].iot_id,
                                                event_observations)
        return payload

    def get_activity_payload(self,observation_name,datastream_id):
        """
        Returns payload for "Activity" ObservedProperty
        """
        confidence = np.random.uniform(0,1)
        fatigue = np.random.uniform(0,5)
        stress = np.random.uniform(0,5)
        activity_class = self.observed_properties[observation_name].normal_values[0]
        prob = self.observed_properties[observation_name].normal_values[1]
        result = np.random.choice(activity_class,p=prob)
        _result_time = datetime.now().isoformat()
        payload = json.dumps({"parameters": {"confidence": confidence,
                                              "fatigue": fatigue, 
                                              "stress": stress},
                            "result": result,
                            # "resultTime": result_time,
                            "Datastream": {"@iot.id": datastream_id}
                            })
        return payload

    def get_heart_rate_payload(self,observation_name,datastream_id,event_observations):
        """
        Returns payload for "Heartrate" ObservedProperty
        """
        confidence = np.random.uniform(0,1)
        try:
            result = event_observations[observation_name]
        except KeyError:
            mean_sd = self.observed_properties[observation_name].normal_values
            result = np.random.normal(mean_sd[0],mean_sd[1])

        _result_time = datetime.now().isoformat()
        status = "NORMAL"
        if result >=100:
            status = "HIGH"
        payload = json.dumps({"parameters": {"confidence": confidence, "status":status},
                            "result": result,
                            # "resultTime": result_time,
                            "Datastream": {"@iot.id": datastream_id}
                            })
        return payload

    def get_blood_oxygen_sat_payload(self,observation_name,datastream_id,event_observations):
        """
        Returns payload for "Spo2" ObservedProperty
        """
        confidence = np.random.uniform(0,1)
        try:
            result = event_observations[observation_name]
        except KeyError:
            mean_sd = self.observed_properties[observation_name].normal_values
            result = np.random.normal(mean_sd[0],mean_sd[1])
        _result_time = datetime.now().isoformat()
        status = "NORMAL"
        if result < 92:
            status = "LOW"
        payload = json.dumps({"parameters": {"confidence": confidence, "status":status},
                            "result": result,
                            # "resultTime": result_time,
                            "Datastream": {"@iot.id": datastream_id}
                            })
        # return payload
        return payload

    def get_skin_temp_payload(self,observation_name,datastream_id,event_observations):
        """
        Returns payload for "Skin temperature" ObservedProperty
        """
        confidence = np.random.uniform(0,1)
        try:
            result = event_observations[observation_name]
        except KeyError:
            mean_sd = self.observed_properties[observation_name].normal_values
            result = np.random.normal(mean_sd[0],mean_sd[1])
        _result_time = datetime.now().isoformat()
        status = "NORMAL"
        if result >= 40:
            status = "HIGH"
        payload = json.dumps({"parameters": {"confidence": confidence,"status":status},
                            "result": result,
                            # "resultTime": result_time,
                            "Datastream": {"@iot.id": datastream_id}
                            })
        # return payload
        return payload

    def get_fall_det_payload(self,observation_name,datastream_id,event_observations):
        """
        Returns payload for "Fall detection" ObservedProperty
        """
        confidence = np.random.uniform(0,1)
        try:
            fall_detected = event_observations[observation_name]
        except KeyError:
            fall_detection_labels = self.observed_properties[observation_name].normal_values[0]
            prob = self.observed_properties[observation_name].normal_values[1]
            fall_detected = np.random.choice(fall_detection_labels,p=prob)
        if fall_detected:
            result  = "Fall_Detected"
            _result_time = datetime.now().isoformat()
            payload = json.dumps({"parameters": {"confidence": confidence},
                                "result": result,
                                # "resultTime": result_time,
                                "Datastream": {"@iot.id": datastream_id}
                                })
            return payload
        return None

    # def get_no_motion_det_payload(self,observation_name,datastream_id):
    #     """
    #     Returns payload for "Heartrate" ObservedProperty
    #     """
    #     confidence = np.random.uniform(0,1)
    #     no_motion_labels = self.observed_properties[observation_name].normal_values[0]
    #     prob = self.observed_properties[observation_name].normal_values[1]
    #     no_motion_detected = np.random.choice(no_motion_labels,p=prob)
    #     if no_motion_detected:
    #         result  = "No_Motion_Detected"
    #         result_time = datetime.now().isoformat()
    #         payload = json.dumps({"parameters": {"confidence": confidence},
    #                             "result": result,
    #                             # "resultTime": result_time,
    #                             "Datastream": {"@iot.id": datastream_id}
    #                             })
    #         return payload
    #     return None

    def get_delay(self):
        """
        Return delay time to send the next message to the OGC server
        """
        return random.randint(1, 3)
class ChemicalDetectionSubsystem(GeneralSensor):
    """
    Class representation of Chemical detection system
    """
    def __init__(self,env,thing,sensor,observed_properties,
                 datastreams,send_observation,chem_events,location_finder):
        super().__init__(env,thing,sensor,observed_properties,
                         datastreams,send_observation,location_finder)
        self.observation_identifiers = self.get_observ_ideantfiers()
        self.events = chem_events
        self.env.process(self.start_subsystem())

    def start_subsystem(self):
        """
        Triggers the operation of the sensor
        """
        while True:
            yield self.env.timeout(self.get_delay())
            event_observations = self.check_chem_events()
            for observation in self.observation_identifiers:
                payload = self.prepare_payload(observation.name, event_observations)
                if payload:
                    _response = self.send_observation(payload)

    def check_chem_events(self):
        """
        Check if chemical event in the thing's location is observed.
        Return all the chemical event observations of the associated thing location at a given time
        """
        event_observations = {}
        for event in self.events:
            if event.event.triggered:
                if self.in_range(event.latitude, event.longitude, event.spread_range):
                    event_observations[event.name] = event.ppm
        return event_observations

    def in_range(self,event_lat, event_long, event_range):
        """
        Check if the chemical event is in definied range of thing
        Return: Bool
        """
        event_loc = Feature(geometry=Point((event_lat, event_long)))
        latitude, longitude, _altitude = self.location_finder()
        current_loc = Feature(geometry=Point((latitude, longitude)))
        if measurement.distance(event_loc,current_loc,units="m") < event_range:
            return True
        return False

    def prepare_payload(self,observation_name, event_observations):
        """
        Prepare sensor payload as per OGC standard and sensor definition
        """
        try:
            result = event_observations[observation_name]
        except KeyError:
            mean_sd = self.observed_properties[observation_name].normal_values
            result = np.random.normal(mean_sd[0],mean_sd[1])

        _result_time = datetime.now().isoformat()
        location = self.location_finder()
        hr = np.random.normal(50,20)
        tp = np.random.normal(30,2)
        sp = np.random.uniform(0,5)
        lt = location[0]
        lg = location[1]
        at = location[2]
        datastream_id = self.datastreams[observation_name].iot_id
        payload = json.dumps({"parameters": {"humidity": hr, "temperature":tp, "speed":sp,
                                              "latitude":lt, "longitude":lg, "altidude":at},
                            "result": result,
                            # "resultTime": result_time,
                            "Datastream": {"@iot.id": datastream_id}
                            })
        return payload

    def get_delay(self):
        """
        Return delay time to send the next message to the OGC server
        """
        return random.randint(1, 3)
class VisualSceneAnalysisHelmetSubsystem(GeneralSensor):
    """
    Class representation of Visual scene analysis system (Helmet)
    """
    def __init__(self,env,thing,sensor,observed_properties,
                 datastreams,send_observation,victims,location_finder):
        super().__init__(env,thing,sensor,observed_properties,
                         datastreams,send_observation,location_finder)
        self.observation_identifiers = self.get_observ_ideantfiers()
        self.events = victims
        self.env.process(self.start_subsystem())

    def start_subsystem(self):
        """
        Triggers the operation of the sensor
        """
        payload = self.get_video_url_payload(self.datastreams["Videostream"].iot_id)
        _response = self.send_observation(payload)
        while True:
            yield self.env.timeout(self.get_delay())
            event_observations = self.check_victims()
            #! figure out how to prepare the observation for message sending
            for observation in self.observation_identifiers:
                # prepare observation based on name of the observation

                # prepare payload so that its None if no message is supposed to be transmitted
                # here the payload is prepared as a list to handle multiple observations at once
                payloads = self.prepare_payload(observation.name,event_observations)
                if payloads:
                    for payload in payloads:
                        _response = self.send_observation(payload)

    def check_victims(self):
        """
        Check if victims in proximity of the thing are observed.
        Returns all the victims in proximity of the associated thing at a given time
        """
        event_observations = []
        for event in self.events:
            if event.event.triggered:
                if self.in_range(event.latitude, event.longitude):
                    event_observations.append(event)
        return event_observations

    def in_range(self,event_lat, event_long, detection_range = 100):
        """
        Check if the victim is in detection range of thing
        Return: Bool
        """
        event_loc = Feature(geometry=Point((event_lat, event_long)))
        latitude, longitude, _altitude = self.location_finder()
        current_loc = Feature(geometry=Point((latitude, longitude)))
        if measurement.distance(event_loc,current_loc,units="m") <= detection_range:
            return True
        return False

    def prepare_payload(self,observation_name,victims):
        """
        Prepare sensor payload as per OGC standard and sensor definition
        """
        if observation_name == "Location":
            payload = self.get_location_payload(self.datastreams[observation_name].iot_id)
            # return payload
        if observation_name == "Object detected":
            payload = self.get_obj_det_payload(observation_name,
                                               self.datastreams[observation_name].iot_id,
                                               victims)
            # return payload
        if observation_name == "Safe exit":
            payload = self.get_safe_exit_payload(self.datastreams[observation_name].iot_id)
            # return payload
        else:
            payload = None
        return payload

    def get_delay(self):
        """
        Return delay time to send the next message to the OGC server
        """
        return random.randint(1, 3)

    def get_video_url_payload(self,datastream_id):
        """
        Returns payload for "Videostream" ObservedProperty
        """
        _result_time = datetime.now().isoformat()
        payload = json.dumps({"result": {"visible_stream": "rtsp://127.0.0.1:6000/visible",
                                        "infrared_stream": "rtsp://127.0.0.1:6000/infrared"},
                                "parameters": {},
                                # "resultTime": result_time,
                                "Datastream": {"@iot.id": datastream_id}
                                })
        return payload

    def get_location_payload(self,datastream_id):
        """
        Returns payload for "Location" ObservedProperty
        """
        _result_time = datetime.now().isoformat()
        location = self.location_finder()
        latitude = location[0]
        longitude = location[1]
        payload = json.dumps({"parameters": {},
                            "result": {"latitude": latitude, "longitude": longitude},
                            #"resultTime": result_time,
                            "Datastream": {"@iot.id": datastream_id}
                            })
        return [payload]

    def get_obj_det_payload(self,observation_name,datastream_id,victims):
        """
        Returns payload for "Object detected" ObservedProperty
        """
        objects = self.observed_properties[observation_name].normal_values[0]
        prob = self.observed_properties[observation_name].normal_values[1]
        num_obj_detected = 1
        detected_obj = np.random.choice(objects,p=prob,size=num_obj_detected)
        _result_time = datetime.now().isoformat()
        location = self.location_finder()
        latitude = location[0]
        longitude = location[1]
        relative_altitude = 1.0
        payloads = []
        for vi in victims:
            result = {"relative_altitude": relative_altitude,
                        "confidence":np.random.uniform(0.7,1.0),
                        "latitude": vi.latitude,
                        "longitude":vi.longitude,
                        "label":"person"}
            payload = json.dumps({"result":result,
                                "parameters":{},
                                "Datastream": {"@iot.id": datastream_id},
                                # "resultTime": result_time
                                })
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
                                #"resultTime": result_time
                                })
            payloads.append(payload)
        return payloads

    def get_safe_exit_payload(self,datastream_id):
        """
        Returns payload for "Safe exit" ObservedProperty
        """
        _result_time = datetime.now().isoformat()
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
                                # "resultTime": result_time
                                })
            payloads.append(payload)
        return payloads
class ContIndoOutLocSubsystem(GeneralSensor):
    """
    Class representation of Continuous indoor ourtoor localization system
    """
    def __init__(self,env,thing,sensor,observed_properties,datastreams,
                 send_observation,location_finder):
        super().__init__(env,thing,sensor,observed_properties,
                         datastreams,send_observation,location_finder)
        self.observation_identifiers = self.get_observ_ideantfiers()
        self.env.process(self.start_subsystem())

    def start_subsystem(self):
        """
        Triggers the operation of the sensor
        """
        while True:
            yield self.env.timeout(self.get_delay())
            #! figure out how to prepare the observation for message sending
            for observation in self.observation_identifiers:
                # prepare observation based on name of the observation

                # prepare payload so that its None if no message is supposed to be transmitted
                payload = self.prepare_payload(observation.name)
                if payload:
                    _response = self.send_observation(payload)

    def prepare_payload(self,observation_name):
        """
        Prepare sensor payload as per OGC standard and sensor definition
        """
        _result_time = datetime.now().isoformat()
        location = self.location_finder()
        lt = location[0]
        lg = location[1]
        _at = location[2]
        try:
            datastream_id = self.datastreams[observation_name].iot_id
        except KeyError:
            print("error appeared")
        payload = json.dumps({"parameters": {"StepCounter": np.random.randint(1,1000),
                                            "DeviceId": np.random.randint(1,10),
                                            "BatteryStatus": np.random.uniform(0,100),
                                            "ExtraInfo": "#60059C025900090002FFFFEFFFFFC00027FC"+
                                                            "D1FECB000000000000000000CDDDFF0F7E37",
                                            "Flag": np.random.randint(1,100)},
                            "result": {"Lat": lt, "Long":lg, "MagBy": np.random.uniform(1,100), 
                                       "MagBz": np.random.uniform(1,100),
                                       "EstAltiZ": np.random.uniform(1,100),
                                       "MagBx": np.random.uniform(1,100),
                                       "EstInertZ":np.random.uniform(1,100),
                                       "EstInertY": np.random.uniform(1,100),
                                       "EstInertX": np.random.uniform(1,100),
                                       "Matrix1x1": np.random.uniform(1,100),
                                       "Matrix1x3": np.random.uniform(1,100),
                                       "Matrix2x2": np.random.uniform(1,100),
                                       "Matrix3x1": np.random.uniform(1,100),
                                       "Matrix1x2": np.random.uniform(1,100),
                                       "Matrix2x1": np.random.uniform(1,100),
                                       "Matrix3x3": np.random.uniform(1,100),
                                       "Matrix2x3": np.random.uniform(1,100),
                                       "Matrix3x2": np.random.uniform(1,100)},
                            # "resultTime": result_time,
                            "Datastream": {"@iot.id": datastream_id}})
        return payload

    def get_delay(self):
        """
        Return delay time to send the next message to the OGC server
        """
        return random.randint(1, 3)

class VisualSceneAnalysisSubsystemUav(GeneralSensor):
    """
    Class representation of Visual scene analysis system (UAV)
    """
    def __init__(self,env,thing,sensor,observed_properties,datastreams,
                 send_observation,victims,location_finder):
        super().__init__(env,thing,sensor,observed_properties,
                         datastreams,send_observation,location_finder)
        self.observation_identifiers = self.get_observ_ideantfiers()
        self.events = victims
        self.env.process(self.start_subsystem())

    def start_subsystem(self):
        """
        Triggers the operation of the sensor
        """
        payload = self.get_video_url_payload(self.datastreams["Videostream"].iot_id)
        _response = self.send_observation(payload)
        while True:
            yield self.env.timeout(self.get_delay())
            event_observations = self.check_victims()
            #! figure out how to prepare the observation for message sending
            for observation in self.observation_identifiers:
                # prepare observation based on name of the observation

                # prepare payload so that its None if no message is supposed to be transmitted
                # here the payload is prepared as a list to handle multiple observations at once
                payloads = self.prepare_payload(observation.name,event_observations)
                if payloads:
                    for payload in payloads:
                        _response = self.send_observation(payload)

    def check_victims(self):
        """
        Check if victims in proximity of the thing are observed.
        Returns all the victims in proximity of the associated thing at a given time
        """
        event_observations = []
        for event in self.events:
            if event.event.triggered:
                if self.in_range(event.latitude, event.longitude):
                    event_observations.append(event)
        return event_observations

    def in_range(self,event_lat, event_long, detection_range = 1000):
        """
        Check if the victim is in detection range of thing
        Return: Bool
        """
        event_loc = Feature(geometry=Point((event_lat, event_long)))
        latitude, longitude, _altitude = self.location_finder()
        current_loc = Feature(geometry=Point((latitude, longitude)))
        if measurement.distance(event_loc,current_loc,units="m") <= detection_range:
            return True
        return False

    def prepare_payload(self,observation_name,victims):
        """
        Prepare sensor payload as per OGC standard and sensor definition
        """
        if observation_name == "Location":
            payload = self.get_location_payload(self.datastreams[observation_name].iot_id)
        elif observation_name == "Object_Detection":
            payload = self.get_obj_det_payload(observation_name,
                                            self.datastreams[observation_name].iot_id,
                                            victims)
        else:
            payload = None
        return payload

    def get_delay(self):
        """
        Return delay time to send the next message to the OGC server
        """
        return random.randint(1, 3)

    def get_video_url_payload(self,datastream_id):
        """
        Returns payload for "Videostream" ObservedProperty
        """
        _result_time = datetime.now().isoformat()
        payload = json.dumps({"result": {"visible_stream": "rtsp://127.0.0.1:6000/visible",
                                        "infrared_stream": "rtsp://127.0.0.1:6000/infrared"},
                                "parameters": {},
                                # "resultTime": result_time,
                                "Datastream": {"@iot.id": datastream_id}
                                })
        return payload

    def get_location_payload(self,datastream_id):
        """
        Returns payload for "Location" ObservedProperty
        """
        _result_time = datetime.now().isoformat()
        location = self.location_finder()
        latitude = location[0]
        longitude = location[1]
        payload = json.dumps({"parameters": {},
                            "result": {"latitude": latitude, "longitude": longitude},
                            # "resultTime": result_time,
                            "Datastream": {"@iot.id": datastream_id}
                            })
        return [payload]

    def get_obj_det_payload(self,observation_name,datastream_id,victims):
        """
        Returns payload for "Object_Detection" ObservedProperty
        """
        objects = self.observed_properties[observation_name].normal_values[0]
        prob = self.observed_properties[observation_name].normal_values[1]
        num_obj_detected = 1
        detected_obj = np.random.choice(objects,p=prob,size=num_obj_detected)
        _result_time = datetime.now().isoformat()
        location = self.location_finder()
        latitude = location[0]
        longitude = location[1]
        relative_altitude = 1.0
        payloads = []
        for vi in victims:
            result = {"relative_altitude": relative_altitude,
                        "confidence":np.random.uniform(0.7,1.0),
                        "latitude": vi.latitude,
                        "longitude":vi.longitude,
                        "label":"person"}
            payload = json.dumps({"result":result,
                                "parameters":{},
                                "Datastream": {"@iot.id": datastream_id},
                                # "resultTime": result_time
                                })
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
                                # "resultTime": result_time
                                })
            payloads.append(payload)
        return payloads
class AcousticsDetectionSubsystem(GeneralSensor):
    """
    Class representation of Acoustics detection system
    """
    def __init__(self,env,thing,sensor,observed_properties,
                 datastreams,send_observation,audio_events,location_finder):
        super().__init__(env,thing,sensor,observed_properties,
                         datastreams,send_observation,location_finder)
        self.observation_identifiers = self.get_observ_ideantfiers()
        self.events = audio_events
        self.msgid = 1
        self.detection_map = {1:"primarydetection",
                              2:"secondarydetection"}
        self.env.process(self.start_subsystem())

    def start_subsystem(self):
        """
        Triggers the operation of the sensor
        """
        while True:
            yield self.env.timeout(self.get_delay())
            event_observations = self.check_acoustic_events()
            #! figure out how to prepare the observation for message sending
            for observation in self.observation_identifiers:
                # prepare observation based on name of the observation

                # prepare payload so that its None if no message is supposed to be transmitted
                payload = self.prepare_payload(observation.name, event_observations)
                if payload:
                    _response = self.send_observation(payload)

    def check_acoustic_events(self):
        """
        Check if acoustic events are observed.
        Returns all the acoustic events at a given time
        """
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
        """
        Return delay time to send the next message to the OGC server
        """
        return random.randint(1, 3)

    def prepare_payload(self,observation_name, event_observations):
        """
        Prepare sensor payload as per OGC standard and sensor definition
        """
        num_audio_detected = 2
        tag_counter = 0
        parameters = {}
        for ev in event_observations:
            tag = ev.label
            confidence = ev.confidence
            azimuth = ev.azimuth
            elevation = ev.elevation
            parameters["elevation"+str(tag_counter+1)] = elevation
            parameters["azimuth"+str(tag_counter+1)] = azimuth
            parameters["confidence"+str(tag_counter+1)] = confidence
            parameters[self.detection_map[tag_counter+1]] = tag
            tag_counter += 1

        for _i in range(num_audio_detected-tag_counter):
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
        _result_time = datetime.now().isoformat()
        datastream_id = self.datastreams[observation_name].iot_id
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
                            # "resultTime": result_time
                            })
        self.msgid += 1
        return payload

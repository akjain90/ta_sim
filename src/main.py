import os
import time
import simpy as sp
# from authantication import CloudAccess
from authantication import FrostApi
from event_based_triggering import setup_events
from things_new import FirstResponder, UAV
from ogc_server_new import setup_ogc_server


# c: classification; R: regression
NORMAL_VALUES = {"AMS":{"Activity":["C",["Walking","Tpose","Standing","Sitting","Kneeling",
                                         "Running","Lying"],[0.5,0.05,0.2,0.1,0.05,0.0,0.1]],
                        "Heartrate":["R",80,5],
                        "Spo2":["R",96,1],
                        "Skin temperature":["R",35,1],
                        "Fall detection":["C",[0,1],[0.9,0.1]]},
                "CDS":{"Ammonia":["R",30,2],
                       "Carbon monoxide":["R",8,1],
                       "Oxygen":["R",20,0.5],
                       "Hydrogen":["R",0.6,0.1],
                       "Chlorine":["R",0.4,0.1],
                       "Florine":["R",0.05,0.02],
                       "Hydrogen cyanide":["R",4,0.5],
                       "Sulfur dioxide":["R",3.5,0.5],
                       "Phosphine":["R",0.65,0.2]},
                "COILS":{},
                "VSAS_FR":{"Object detected":["C",["bicycle", "car", "motorbike", "bus", 
                                                   "train","truck", "animal", "backpack", 
                                                   "doors", "stairs", "windows", "suitcase", 
                                                   "cellphone", "rails"],
                                               [0.05,0.05,0.05,0.05,0.05,0.05,0.05,
                                                0.1,0.1,0.05,0.1,0.1,0.1,0.1]]},
                "VSAS_UAV":{"Object_Detection":["C",["bicycle", "car", "motorbike", "bus", 
                                                   "train","truck", "animal", "backpack", 
                                                   "doors", "stairs", "windows", "suitcase", 
                                                   "cellphone", "rails"],
                                               [0.05,0.05,0.05,0.05,0.05,0.05,0.05,
                                                0.1,0.1,0.05,0.1,0.1,0.1,0.1]]},
                "ADS":{"ADS":["C",["Silence", "Siren","Glass breaking", "Wind Noise"],
                                             [0.25,0.25,0.25,0.25]]}}
SCENARIO_ROOT = "./scenario/original_scenario_tested"
CONFIGURATION_ROOT = "./configuration_files/original_configurations/config_1"
CHEM_EVENT_DIR=os.path.join(SCENARIO_ROOT,"chem_events.csv")
MESSAGE_EVENT_DIR = os.path.join(SCENARIO_ROOT,"cicis_events.csv")
VICTIMS_DIR = os.path.join(SCENARIO_ROOT,"victims.csv")
AUDIO_EVENTS_DIR = os.path.join(SCENARIO_ROOT,"audio_events.csv")
FR_HLTH_EVENT_DIR = os.path.join(SCENARIO_ROOT,"fr_abnormal_health_event.csv")
FR_CONFIG = os.path.join(CONFIGURATION_ROOT,"first_responder_config.csv")
UAV_CONFIG = os.path.join(CONFIGURATION_ROOT,"uav_config.csv")
MOVEMENT_CONFIG = os.path.join(SCENARIO_ROOT,"movement_specifications.json")

class StartTeamAware():
    """Start simulation for the TeamAware scenario"""
    def __init__(self,env,api,events,sensors,
                 observed_properties,datastreams,fr_things,uav_things):
        self.i = 1
        self.env = env
        self.api = api
        self.events = events
        self.fr_things = fr_things
        self.uav_things = uav_things
        self.datastreams = datastreams
        self.sensors = sensors
        self.observed_properties = observed_properties
        self.env.process(self.start_first_responders())
        self.env.process(self.start_uavs())

    def start_first_responders(self):
        """Initiates all the firstresponders as individual resources in Simpy environment"""
        yield self.env.timeout(0)
        for name,thing in self.fr_things.items():
            FirstResponder(self.env,thing,self.sensors,self.observed_properties,
                           self.datastreams[name],self.events)
    # def fr_thread(self,env,thing,sensors,observed_properties,datastreams,cloud_access,events):
    #     FirstResponder(env,thing,sensors,observed_properties,datastreams,cloud_access,events)
    def start_uavs(self):
        """Initiates all the UAVs as individual resources in Simpy environment"""
        yield self.env.timeout(0)
        for name,thing in self.uav_things.items():
            UAV(self.env,thing,self.sensors,self.observed_properties,
                self.datastreams[name],self.events)
    def delete_things(self,delete):
        """Selectively deletes Things and Sensors to free up space on OGC server"""
        if delete:
            print("Deleting things")
            for _fr_name,ogc_thing in self.fr_things.items():
                ogc_thing.delete_ogc_thing()
            for _uav_name,ogc_thing in self.uav_things.items():
                ogc_thing.delete_ogc_thing()
            print("Deleting Sensors")
            for _sen_name,sensor in self.sensors.items():
                sensor.delete_ogc_sensor()
            print("Deleting observation properties")
            for _sys_name,ops in self.observed_properties.items():
                for _op_name,op in ops.items():
                    op.delete_ogc_observed_property()

def main():
    """Main: Create setup for simulation using input files, and run the simulation"""
    env = sp.rt.RealtimeEnvironment(strict=False,factor = 1.0)
    # env = sp.Environment()
    critical_events = setup_events(env,CHEM_EVENT_DIR,VICTIMS_DIR,
                                   AUDIO_EVENTS_DIR,FR_HLTH_EVENT_DIR)
    api = FrostApi("http://localhost:8080/FROST-Server/v1.1")
    fr_things,uav_things,sensors,\
        observed_properties,datastreams = setup_ogc_server(api,NORMAL_VALUES,
                                                        fr_config = FR_CONFIG,
                                                        uav_config=UAV_CONFIG,
                                                        movement_config = MOVEMENT_CONFIG)
    start = time.perf_counter()
    _teamaware_for_bursa = StartTeamAware(env,api,critical_events,sensors,
                                         observed_properties,datastreams,fr_things = fr_things,
                                         uav_things=uav_things)
    # ###### increase this int to run the sim longer #######
    env.run(10)
    end = time.perf_counter()
    print("Run time: ",end-start)
    # teamaware_for_bursa.delete_things(True)


if __name__ == "__main__":
    main()

from authantication import CloudAccess
from event_based_triggering import get_all_events, Events
from things_new import FirstResponder, UAV
import simpy as sp
from ogc_server_new import setup_ogc_server
import os
import time

# c: classification; R: regression
NORMAL_VALUES = {"AMS":{"Activity":["C",["Walking","Tpose","Standing","Sitting","Kneeling","Running","Lying"],[0.5,0.05,0.2,0.1,0.05,0.0,0.1]],
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
                                    # Explosion, 

class StartTeamAware():
    def __init__(self,env,cloud_access,events,sensors,observed_properties,datastreams,fr_things,uav_things):
        self.i = 1
        self.env = env
        self.cloud_access = cloud_access
        self.events = events
        self.env.process(self.start_first_responders(fr_things,sensors,observed_properties,datastreams))
        self.env.process(self.start_uavs(uav_things,sensors,observed_properties,datastreams))

    def start_first_responders(self,fr_things,sensors,observed_properties,datastreams):
        yield self.env.timeout(0)
        for thing in fr_things:
            FirstResponder(self.env,fr_things[thing],sensors,observed_properties,datastreams[thing],self.cloud_access,self.events)
        
        
    # def fr_thread(self,env,thing,sensors,observed_properties,datastreams,cloud_access,events):
    #     FirstResponder(env,thing,sensors,observed_properties,datastreams,cloud_access,events)
            
    def start_uavs(self,uav_things,sensors,observed_properties,datastreams):
        yield self.env.timeout(0)
        for thing in uav_things:
            UAV(self.env,uav_things[thing],sensors,observed_properties,datastreams[thing],self.cloud_access,self.events)
    
    def delete_things(self,delete, fr, uav, sensors):
        if delete:
            delete_thing_headers = {"Authorization":self.cloud_access.general_api.fetch_headers()["Authorization"]}
            for th in fr:
                thing_id = fr[th].thing_id
                delete_url = self.cloud_access.general_api.url_delete_thing(int(thing_id))
                fr[th].delete_thing(delete_url,delete_thing_headers)

            for th in uav:
                thing_id = uav[th].thing_id
                delete_url = self.cloud_access.general_api.url_delete_thing(int(thing_id))
                uav[th].delete_thing(delete_url,delete_thing_headers)
                # print()
                
            for sen in sensors:
                #       # IMS
                name = sensors[sen].name
                sensor_id = sensors[sen].id
                if name == "VSAS_FR" or name == "VSAS_UAV":
                    delete_url = self.cloud_access.vsas_api.url_delete_sensor(sensor_id)
                    delete_headers = {"Authorization":self.cloud_access.vsas_api.fetch_headers()["Authorization"]}
                elif name == "AMS":
                    delete_url = self.cloud_access.ams_api.url_delete_sensor(sensor_id)
                    delete_headers = {"Authorization":self.cloud_access.ams_api.fetch_headers()["Authorization"]}
                elif name == "CDS":
                    delete_url = self.cloud_access.cds_api.url_delete_sensor(sensor_id)
                    delete_headers = {"Authorization":self.cloud_access.cds_api.fetch_headers()["Authorization"]}
                elif name == "COILS":
                    delete_url = self.cloud_access.coils_api.url_delete_sensor(sensor_id)
                    delete_headers = {"Authorization":self.cloud_access.coils_api.fetch_headers()["Authorization"]}
                elif name == "ADS":
                    delete_url = self.cloud_access.ads_api.url_delete_sensor(sensor_id)
                    delete_headers = {"Authorization":self.cloud_access.ads_api.fetch_headers()["Authorization"]}
                else:
                    delete_url = self.cloud_access.ims_api.url_delete_sensor(sensor_id)
                    delete_headers = {"Authorization":self.cloud_access.ims_api.fetch_headers()["Authorization"]}
                sensors[sen].delete_sensor(delete_headers,delete_url)

            
    
    

def main():
    env = sp.rt.RealtimeEnvironment(strict=False,factor = 1.0)
    # # env = sp.Environment()
    scenario_root = "./scenario/firestation_sce"
    configurations_root = "./configuration_files/firestation/config1"
    chem_events, cicis_events,victims, audio_events, fr_abnormal_health_events = get_all_events(chem_events_dir=os.path.join(scenario_root,"chem_events.csv"),
                                                                     message_events_dir = os.path.join(scenario_root,"cicis_events.csv"),
                                                                     victims_dir = os.path.join(scenario_root,"victims.csv"),
                                                                     audio_events_dir = os.path.join(scenario_root,"audio_events.csv"),
                                                                     fr_abnormal_health_event_dir = os.path.join(scenario_root,"fr_abnormal_health_event.csv"))
    bursa_events = Events(env,chem_events,cicis_events,audio_events,victims,fr_abnormal_health_events)
    cloud_access = CloudAccess(env)
    fr_things,uav_things,sensors,observed_properties,datastreams = setup_ogc_server(cloud_access,NORMAL_VALUES,
                                                        fr_config = os.path.join(configurations_root,"first_responder_config.csv"),
                                                        uav_config=os.path.join(configurations_root,"uav_config.csv"),
                                                        movement_config = os.path.join(scenario_root,"movement_specifications.json"))
    start = time.perf_counter()
    teamaware_for_bursa = StartTeamAware(env,cloud_access,bursa_events,sensors,observed_properties,datastreams,fr_things = fr_things,
                                         uav_things=uav_things)
   
    ###### increase this int to run the sim longer #######
    env.run(10)
    end = time.perf_counter()
    print("Run time: ",end-start)
    teamaware_for_bursa.delete_things(True, fr_things, uav_things, sensors)


if __name__ == "__main__":
    main()
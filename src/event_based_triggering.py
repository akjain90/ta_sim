# -*- coding: utf-8 -*-
"""
Created on Mon Aug 15 13:18:03 2022

@author: jain
"""

# import simpy as sp
import pandas as pd

def setup_events(env,chem_events_dir,victims_dir,
                 audio_events_dir, fr_abnormal_health_event_dir):
    """
    Read all the events from the csv scripts.
    Create simpy events based as per the requirement from each event type
    """
    chem_events,victims,\
    audio_events, fr_abnormal_health_events = get_all_events(chem_events_dir,
                                                             victims_dir,audio_events_dir,
                                                             fr_abnormal_health_event_dir)
    events = Events(env,chem_events,audio_events,victims,fr_abnormal_health_events)
    return events

def get_all_events(chem_events_dir,victims_dir, audio_events_dir, fr_abnormal_health_event_dir):
    """
    Read and return all the events details from the CSV files
    """
    chem_events = get_chem_events(chem_events_dir)
    # cicis_events = get_message_events(message_events_dir)
    victims = get_victims(victims_dir)
    audio_events = get_audio_events(audio_events_dir)
    health_events = get_health_events(fr_abnormal_health_event_dir)
    return chem_events, victims, audio_events, health_events


def get_chem_events(chem_events_dir:str) -> dict:
    """
    Read chemical events from a csv file to a dictionary
    """
    df = pd.read_csv(chem_events_dir)
    event_dict = df.to_dict("records")
    return event_dict

def get_victims(victims_dir:str) -> dict:
    """
    Read victims as events from a csv file to a dictionary
    """
    df = pd.read_csv(victims_dir)
    victim_dict = df.to_dict("records")
    return victim_dict

def get_audio_events(audio_event_dir:str) -> dict:
    """
    Read audiol events from a csv file to a dictionary
    """
    df = pd.read_csv(audio_event_dir)
    event_dict = df.to_dict("records")
    return event_dict

def get_health_events(fr_abnormal_health_event_dir:str) -> dict:
    """
    Read FRs health events from a csv file to a dictionary
    """
    df = pd.read_csv(fr_abnormal_health_event_dir)
    health_event_dict = df.to_dict("records")
    return health_event_dict

class ChemEvent():
    """
    Object representation of each chemical event.
    """
    def __init__(self,env,name,latitude,longitude,time,spread_range,ppm,reset_time):
        self.env = env
        self.name = name
        self.latitude = latitude
        self.longitude = longitude
        self.time = time
        self.spread_range = spread_range
        self.ppm = ppm
        self.reset_time = reset_time
        self.event_triggered = False
        self.event = self.env.event()
        self.event_process = self.env.process(self.start_event())
        self.event_reset = self.env.process(self.reset_event())

    def start_event(self):
        """
        Triggers event after a given time as an input in configuration file 
        """
        yield self.env.timeout(self.time)
        self.event_triggered = True
        self.event.succeed()

    def reset_event(self):
        """
        Reset event after a given time delay as an input in configuration file
        """
        yield self.env.timeout(self.reset_time)
        self.event_triggered = False
        self.event = self.env.event()

class Victim():
    """
    Object representation of each Victim.
    """
    def __init__(self,env,number,latitude,longitude,time,reset_time):
        self.env = env
        self.number = number
        self.latitude = latitude
        self.longitude = longitude
        self.time = time
        self.reset_time = reset_time
        self.event = self.env.event()
        self.event_process = self.env.process(self.start_event())
        self.event_reset = self.env.process(self.reset_event())

    def start_event(self):
        """
        Triggers event after a given time as an input in configuration file 
        """
        yield self.env.timeout(self.time)
        self.event_triggered = True
        self.event.succeed()

    def reset_event(self):
        """
        Reset event after a given time delay as an input in configuration file
        """
        yield self.env.timeout(self.reset_time)
        self.event_triggered = False
        self.event = self.env.event()

class AudioEvent():
    """
    Object representation of each Audio event.
    """
    def __init__(self,env,label,azimuth,elevation,confidence,time):
        self.env = env
        self.label = label
        self.azimuth = azimuth
        self.elevation = elevation
        self.confidence = confidence
        self.time = time
        self.event = self.env.event()
        self.event_triggered = False
        self.event_process = self.env.process(self.start_event())

    def start_event(self):
        """
        Triggers event after a given time as an input in configuration file 
        """
        yield self.env.timeout(self.time)
        self.event_triggered = True
        self.event.succeed()

    def reset_event(self):
        """
        Reset event and is accessed directly by the sensor
        """
        self.event_triggered = False
        self.event = self.env.event()

    # def if_recorded(self):
    #     if self.event_recorded:
    #         return True
    #     else:
    #         return False


class HealthEvent():
    """
    Object representation of each health event.
    """
    def __init__(self,env,name,signal,value,time,reset_time):
        self.env = env
        self.name = name
        self.signal = signal
        self.value = value
        self.reset_time = reset_time
        self.time = time
        self.event_triggered = False
        self.event = self.env.event()
        self.event_process = self.env.process(self.start_event())
        self.event_reset = self.env.process(self.reset_event())

    def start_event(self):
        """
        Triggers event after a given time as an input in configuration file 
        """
        yield self.env.timeout(self.time)
        self.event_triggered = True
        self.event.succeed()

    def reset_event(self):
        """
        Reset event after a given time delay as an input in configuration file
        """
        yield self.env.timeout(self.reset_time)
        self.event_triggered = False
        self.event = self.env.event()

class Events():
    """
    Encapsulates all the events of the scenario.
    """
    def __init__(self,env,chem_events,audio_events,victims,fr_abnormal_health_events):
        self.env = env
        self.chem_events = self.trigger_chem_events(chem_events)
        # self.cicis_events = self.trigger_message_events(cicis_events)
        self.audio_events = self.trigger_audio_events(audio_events)
        self.victims = self.trigger_victims(victims)
        self.fr_health_events = self.trigger_fr_abnormal_health_events(fr_abnormal_health_events)

    def trigger_chem_events(self,chem_events):
        """
        Setup all the chemical events
        """
        all_events = []
        for event in chem_events:
            temp = ChemEvent(self.env,
                              event["name"],event["latitude"],event["longitude"],
                              event["time"],event["range"],event["ppm"],event["reset_time"])
            all_events.append(temp)
        return all_events

    # def trigger_message_events(self,cicis_events):
    #     all_events = []
    #     for event in cicis_events:
    #         temp = MessagingEvent(self.env,
    #                               event["tags"],
    #                               event["values"],
    #                               event["time"])
    #         all_events.append(temp)
    #     return all_events

    def trigger_victims(self,victims):
        """
        Setup all the Victims
        """
        all_victims = []
        for victim in victims:
            temp = Victim(self.env,victim["victim_num"],victim["latitude"],
                          victim["longitude"],victim["time"],victim["reset_time"])
            all_victims.append(temp)
        return all_victims

    def trigger_audio_events(self,audio_events):
        """
        Setup all the Audio events
        """
        all_events = []
        for event in audio_events:
            temp = AudioEvent(self.env,
                              event["label"],event["azimuth"],
                              event["elevation"],event["confidence"],event["time"])
            all_events.append(temp)
        return all_events

    def trigger_fr_abnormal_health_events(self,abnormal_health_events):
        """
        Setup all the abnormal health events
        """
        all_events = []
        for event in abnormal_health_events:
            temp = HealthEvent(self.env,
                              event["name"],event["signal"],
                              event["value"],event["time"],event["reset_time"])
            all_events.append(temp)
        return all_events
# def print_events(env,events):
#     while True:
        # print(env.now)
        # for chem_event in events.chem_events:
        #     if chem_event.event.triggered:
        #         print("name: {}; lat: {}; long: {}; area: {}; ppm: {}".format(chem_event.name,
        #                                                             chem_event.latitude,
        #                                                             chem_event.longitude,
        #                                                             chem_event.area,
        #                                                             chem_event.ppm))
        # for event in events.cicis_events:
        #     if event.event.triggered:
        #         print("message: {}; lat: {}; long: {}".format(event.message,
        #                                                                    event.latitude,
        #                                                                    event.longitude))
        #         event.event = event.env.event()

        # for victim in events.victims:
        #     if victim.event.triggered:
        #         print("victim num: {}; latitude: {}; longitude: {}".format(victim.number,
        #                                                                    victim.latitude,
        #                                                                    victim.longitude))

        # for event in events.audio_events:
        #     if event.event.triggered:
        #         print("Tag: {}; lat: {}; long: {}".format(event.tag,
        #                                                   event.latitude,
        #                                                   event.longitude))
        # yield env.timeout(1)


# def main():
#     chem_events = get_chem_events("./scenario/chem_events.csv")
#     cicis_events = get_message_events("./scenario/cicis_events.csv")
#     victims = get_victims("./scenario/victims.csv")
#     audio_events = get_audio_events("./scenario/audio_events.csv")
#     env = sp.rt.RealtimeEnvironment()
#     # env = sp.Environment()
#     events = Events(env,chem_events,cicis_events,audio_events,victims)
#     env.process(print_events(env,events))
#     env.run(until=25)

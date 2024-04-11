import requests

class FrostApi():
    """
    Variables and access API of the local Frost server
    """
    def __init__(self,gateway):
        self.gateway = gateway
    #URLs for creation
    def url_create_thing(self):
        """
        Return URL to create OGC thing
        """
        t = f"{self.gateway}/Things"
        return t

    def url_create_sensor(self):
        """
        Return URL to create OGC sensor
        """
        return f"{self.gateway}/Sensors"

    def url_create_observed_property(self):
        """
        Return URL to create OGC observed property
        """
        return f"{self.gateway}/ObservedProperties"

    def url_create_datastream(self):
        """
        Return URL to create OGC datastream
        """
        return f"{self.gateway}/Datastreams"

    # URLs for sending
    def url_send_location_for_thing(self):
        """
        Return URL to publish thing location on OGC server
        """
        return f"{self.gateway}/Locations"

    def url_send_observation(self):
        """
        Return URL to publish sensor observation on OGC server
        """
        return f"{self.gateway}/Observations"

    # URLs for deletion
    def url_delete_thing(self,thing_id):
        """
        Return URL to delete OGC thing
        """
        return f"{self.url_create_thing()}({thing_id})"

    def url_delete_sensor(self,sensor_id):
        """
        Return URL to delete OGC sensor
        """
        return f"{self.url_create_sensor()}({sensor_id})"

    def url_delete_observed_property(self,op_id):
        """
        Return URL to delete OGC observed property
        """
        return f"{self.url_create_observed_property()}({op_id})"

    # functions for creation
    def create_thing(self,payload):
        """
        Create OGC thing
        Return response
        """
        response = requests.request("POST",url=self.url_create_thing(),data=payload)
        return response

    def create_sensor(self,payload):
        """
        Create OGC sensor
        Return response
        """
        response = requests.request("POST",url=self.url_create_sensor(),data=payload)
        return response

    def create_observed_property(self,payload):
        """
        Create OGC observered property
        Return response
        """
        response = requests.request("POST",url=self.url_create_observed_property(),data=payload)
        return response

    def create_datastream(self,payload):
        """
        Create OGC datastream
        Return response
        """
        response = requests.request("POST", self.url_create_datastream(), data=payload)
        return response

    # functions for data sending
    def send_thing_location(self,payload):
        """
        Publish thing location on OGC server
        Return response
        """
        response = requests.request("POST", self.url_send_location_for_thing(),data=payload)
        return response

    def send_observation(self,payload):
        """
        Publish sensor observation on OGC server
        Return response
        """
        response = requests.request("POST", self.url_send_observation(),data=payload)
        return response

    # functions for deletion
    def delete_thing(self,thing_id):
        """
        Delete OGC thing
        Return response
        """
        response = requests.request("DELETE", self.url_delete_thing(thing_id))
        return response

    def delete_sensor(self,sensor_id):
        """
        Delete OGC sensor
        Return response
        """
        response = requests.request("DELETE", self.url_delete_sensor(sensor_id))
        return response

    def delete_observed_property(self,op_id):
        """
        Delete OGC observered property
        Return response
        """
        response = requests.request("DELETE", self.url_delete_observed_property(op_id))
        return response

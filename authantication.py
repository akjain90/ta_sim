import requests

class TeamAwareApi():
    def __init__(self,gateway,fetch_headers):
        self.gateway = gateway
        self.fetch_headers = fetch_headers

    def url_teamaware(self):
        return ("https://keycloak.teamaware.eu:7443/realms/teamaware/protocol/openid-connect/token")
    
    def url_create_thing(self):
        return("{}/Things".format(self.gateway))
    
    def url_create_location_for_thing(self,thing_id):
        return ("{}({})/Locations".format(self.url_create_thing(),thing_id))
    
    def url_delete_thing(self,thing_id):
        return ("{}({})".format(self.url_create_thing(),thing_id))
    
    def url_create_observed_property(self):
        return("{}/ObservedProperties".format(self.gateway))
    
    def url_create_sensor(self):
        return("{}/Sensors".format(self.gateway))
    
    def url_create_datastream(self):
        return("{}/Datastreams".format(self.gateway))
    
    def url_send_observation(self):
        return("{}/Observations".format(self.gateway))
    
    def url_delete_sensor(self,sensor_id):
        return ("{}({})".format(self.url_create_sensor(),sensor_id))
        
class CloudAccess():
    def __init__(self,env):
        self.teamaware_payload = 'grant_type=client_credentials&audience=TeamAware%20Platform'

        self.ads_headers = {'Content-Type': 'application/x-www-form-urlencoded',
                            'Authorization': 'Basic QURTOnN2N0ZtdDR4SXV2NUhRVHYwMEw2Y2JvNFJjWDAyRHBT'}
        
        self.ams_headers = {'Content-Type': 'application/x-www-form-urlencoded',
                            'Authorization': 'Basic QU1TOjRXN3BtSndpR0Vsb1JQYnFMSTJmOW9kMWxRcGk0emNi'}
        
        self.cds_headers = {'Content-Type': 'application/x-www-form-urlencoded',
                            'Authorization': 'Basic Q0RTOmZjbGoxclRIOWh3eU5LSmF5dlRhZ2dsdDh4QVlicVdO'}
        
        self.coils_headers = {'Content-Type': 'application/x-www-form-urlencoded',
                              'Authorization': 'Basic Q09JTFM6TWlUME1CTXRJNlZ4bFZzUVRzcWQwZlZ5UUIxV0hFR3M='}
        
        self.vsas_headers = {'Content-Type': 'application/x-www-form-urlencoded',
                             'Authorization': 'Basic VlNBUzpJVGFxNlcxTU12WnNTNXlpZ2JkOFRSSXNVd1JWUHh4aw=='}
        
        self.teamaware_gateway = "https://keycloak.teamaware.eu:7443/realms/teamaware/protocol/openid-connect/token"        
        self.ads_gateway = "https://gateway.teamaware.eu:7443/ogc/ADSData"
        self.ams_gateway= "https://gateway.teamaware.eu:7443/ogc/AMSData"
        self.cds_gateway = "https://gateway.teamaware.eu:7443/ogc/CDSData"
        self.coils_gateway = "https://gateway.teamaware.eu:7443/ogc/COILSData"
        self.vsas_gateway = "https://gateway.teamaware.eu:7443/ogc/VSASData"
        self.ims_gateway = None
        
        self.ads_token =  AccessToken(env,self.teamaware_gateway,
                                      self.teamaware_payload,
                                      self.ads_headers)
        
        self.ams_token =  AccessToken(env,self.teamaware_gateway,
                                      self.teamaware_payload,
                                      self.ams_headers)
        
        self.cds_token =  AccessToken(env,self.teamaware_gateway,
                                      self.teamaware_payload,
                                      self.cds_headers)
        
        self.coils_token =  AccessToken(env,self.teamaware_gateway,
                                      self.teamaware_payload,
                                      self.coils_headers)
        
        self.vsas_token =  AccessToken(env,self.teamaware_gateway,
                                      self.teamaware_payload,
                                      self.vsas_headers)
        
        self.general_api = TeamAwareApi(self.coils_gateway,self.coils_token.get_headers)
        self.ads_api = TeamAwareApi(self.ads_gateway,self.ads_token.get_headers)
        self.cds_api = TeamAwareApi(self.cds_gateway,self.cds_token.get_headers)
        self.vsas_api = TeamAwareApi(self.vsas_gateway,self.vsas_token.get_headers)
        self.ams_api = TeamAwareApi(self.ams_gateway,self.ams_token.get_headers)
        self.coils_api = TeamAwareApi(self.coils_gateway,self.coils_token.get_headers)


class AccessToken():
    def __init__(self,env,url,payload,headers):
        self.env = env
        self.url = url

        self.payload=payload
        self.headers = headers
        self.access_token = None
        self.access_prefatch()
        self.env.process(self.get_access_token())
        
    def get_access_token(self):
        while True:
            self.session = requests.Session()
            self.response = requests.request("POST", self.url, headers=self.headers, data=self.payload,verify=False)
            self.response_dict = eval(self.response.text)
            self.access_token = self.response_dict["access_token"]
            valid_for = self.response_dict["expires_in"]
            
            yield self.env.timeout(valid_for)

    def access_prefatch(self):
        self.session = requests.Session()
        self.response = requests.request("POST", self.url, headers=self.headers, data=self.payload,verify=False)
        self.response_dict = eval(self.response.text)
        self.access_token = self.response_dict["access_token"]

    def get_headers(self):
        authorization = self.response_dict["token_type"] + " " + self.access_token
        headers = {'Content-Type': 'application/json',
                   'Authorization': authorization
                   }
        return headers


# def main():
#     teamaware_api = CloudApi()
#     print(teamaware_api.url_ads_create_location_for_uav(1))
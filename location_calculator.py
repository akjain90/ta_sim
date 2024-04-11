# import simpy as sp
# import geopy as geo
# from geopy.distance import great_circle
# from turfpy import measurement
# from geojson import Point, Feature
# import numpy as np


# class locationUpdater():
#     def __init__(self, env):
#         self.env = env
#         self.start_lat = 39.89987928648268
#         self.start_lon = 32.86444565692524
#         self.waypoints_delay=[[39.900200, 32.864875,5],[39.900402, 32.864451,3]]
#         self.speed = 3
#         self.current_lat = self.start_lat
#         self.current_lon = self.start_lon
#         self.env.process(self.update_location())

#     def update_current_loc(self,destination):
#         self.current_lat = destination["geometry"]["coordinates"][0]
#         self.current_lon = destination["geometry"]["coordinates"][1]

#     def update_location(self):
#         # delay = 1
#         # for waypoint in self.waypoints_delay:
#         #     end = Feature(geometry=Point((waypoint[0],waypoint[1])))
#         #     wait = waypoint[2]
#         #     while True:
#         #         yield self.env.timeout(delay)
#         #         # print("Great earth distance: {}".format(great_circle((self.start_lat,self.start_lon),(self.end_lat,self.end_lon)).meters))
#         #         start = Feature(geometry=Point((self.start_lat,self.start_lon)))
#         #         end = Feature(geometry=Point((39.900200,32.864875)))
#         #         bearing = measurement.bearing(start,end) + np.random.uniform(-10,10)
#         #         destination = measurement.destination(start, 3, bearing, {"units" : "m"})
#         #         print("Trufy distance: {}".format(measurement.distance(start,end,units="m")))
#         #         print("Bearing: {}".format(bearing))
#         #         print("Destination: {}".format(destination))
#         #         print("Destination distance: {}".format(measurement.distance(start,destination["geometry"],units="m")))

#         delta_t = 0.1
#         i = 0
#         while True:
#             current_loc = Feature(geometry=Point((self.current_lat,self.current_lon)))
#             w_t = Feature(geometry=Point((self.waypoints_delay[i][0],self.waypoints_delay[i][1])))
#             dist_w_t = measurement.distance(current_loc,w_t,units="m")
#             bearing = measurement.bearing(current_loc,w_t) + 0 if dist_w_t > 4 else np.random.uniform(-0.1,0.1)
#             # delta_b = 0
#             # if dist_w_t > 3:
#             #     delta_b = np.random.uniform(-0.1,0.1)
#             # bearing = bearing + delta_b
#             travel_dist = self.speed * delta_t
#             destination = measurement.destination(current_loc, travel_dist, bearing, {"units" : "m"})
#             self.update_current_loc(destination)
#             current_loc = destination["geometry"]
#             if measurement.distance(current_loc,w_t,units="m") < 6:
#                 print("waiting at {} for {}".format(current_loc,self.waypoints_delay[i][2] ))
#                 print()
#                 yield self.env.timeout(self.waypoints_delay[i][2])
#                 i += 1
#                 if i >= len(self.waypoints_delay):
#                     print("Breaking out and waiting untill the end")
#                     break
#             else:
#                 # print("Moved to {}".format(current_loc))
#                 # print("Distance to destination is {}".format(measurement.distance(current_loc,w_t,units="m")))
#                 # print()
#                 yield self.env.timeout(delta_t)
#         while True:
#             yield self.env.timeout(1)



# def main():
#     env = sp.rt.RealtimeEnvironment(strict=False,factor = 1)
#     locationUpdater(env)
#     env.run(200)


# if __name__ == "__main__":
#     main()



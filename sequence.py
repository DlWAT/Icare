import json 

dict={"headers":{"structure":["intro","Couplet1","Refrain1","Couplet2","Refrain2","Solo"]},
      "data":{"intro":[],"Couplet1":[],"Refrain1":[],"Couplet2":[],"Refrain2":[],"Solo":[]} }

dict["data"]["intro"]=[[2,125,20,35],
                       [2,20,53,128]]

dict["data"]["Refrain1"]=[[0.5,125,20,35],
                          [0.5,20,53,128]]

with open("esquence_example.json", "w") as outfile:
    json.dump(dict, outfile)
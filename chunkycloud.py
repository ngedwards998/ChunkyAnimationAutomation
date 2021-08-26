import json, requests, time, sys, os
try:
    os.mkdir('snapshots/')
except:
    print('failed setting up the snapshots folder.\n This error is a general failure if you\'ve already run this script with no errors ignore the above')

class ChunkyCloud:
    def __init__(self, api_key: str):
        self._api_key = api_key
        self._id_queue: Dict[str, str] = {} # This stores the ids and their corresponding output filepaths
    
    def submit_json(self, key, octree: str, emitter_grid: str, scene_file: str, samples: int, output_path: str) -> str:
        print("sending file: " + scene_file)
        """
        This will submit a job to CC and return the ID number.
        :param octree:       Path to the octree file
        :param emitter_grid: Path to the emitter grid file
        :param scene_file:   Path to the scene file
        """
        payload={'X-Api-Key': str(key),
        'chunkyVersion': '2.x',
        'transient': 'True',
        'targetSpp': samples}
        files=[
            ('scene',(scene_file,open(scene_file,'rb'),'application/json')),
            ('octree',(octree + '.octree2',open(octree,'rb'),'application/octet-stream')),
            ('emittergrid',(emitter_grid,open(emitter_grid,'rb'),'application/octet-stream'))
        ]
        headers = {}

        response = requests.request("POST", "https://api.chunkycloud.lemaik.de/jobs", headers=headers, data=payload, files=files)
        new_id = response.json()['_id']
        self._id_queue[new_id] = output_path
        return new_id

    # Cancels job with provided jobid variable and api-key
    def cancel(self, jobid, api_key):
        url = ("https://api.chunkycloud.lemaik.de/jobs/" + str(jobid))
        
        payload={'X-Api-Key': str(api_key),
        'cancel': 'true'}
        files=[

        ]

        headers = {}
        response = requests.request("PUT", url, headers=headers, data=payload, files=files)
        print(response.text)

    # Cancel all jobs function, !!!WARNING USE WITH EXTREME CAUTION DELETES ALL JOBS!!!
    def cancel_all(self, idqueue):
        while len(idqueue) > 0:
            for id_name, output_path in list(idqueue.items()):
                del idqueue[id_name]
                url =("https://api.chunkycloud.lemaik.de/jobs/" + output_path)
                payload={'X-Api-Key': str(api_key),
                'cancel': 'true'}
                files=[

                ]

                headers = {}
                response = requests.request("PUT", url, headers=headers, data=payload, files=files)
                print(response.text)
    
    def is_complete(self, id_number: str) -> bool:
        """ Check if a job with an id is complete """
        response = requests.request("GET", "https://api.chunkycloud.lemaik.de/jobs/" + id_number)
        contents = response.json()
        return contents['spp'] >= contents['targetSpp']

    def download_img(self, id_number: str, output_file: str):
        # Download the result of the job with id to an output file
        # Download logic
        
        r = requests.get('https://api.chunkycloud.lemaik.de/jobs/' + id_number + '/latest.png?')
        with open('snapshots/' + output_file + '.png','wb') as f:
            f.write(r.content)
    
    def wait_and_download_all(self):
        while len(self._id_queue) > 0:
            time.sleep(10) # insert some reasonable poll time here
            for id_name, output_path in list(self._id_queue.items()):
                if self.is_complete(id_name):
                    print("downloading: " + id_name)
                    self.download_img(id_name, output_path)
                    #time.sleep(1)
                    del self._id_queue[id_name] # Remove this item from the queue
                else:
                    print('id - ' + id_name + ' not yet at targetSpp yet, waiting 5 seconds')
                    time.sleep(5)

import os

class Guard:
    _preserved_uid: int
    _preserved_gid: int
    _uid: int
    _gid: int


    def __init__(self, uid: int, gid: int):
        # safety measure
        if uid == 0 or gid == 0:
            print("Tried to su Guard to root :(")
            os.exit(-1)
        
        self._uid = uid
        self._gid = gid

    def _preserve_ids(self):
        self._preserved_uid = os.geteuid()
        self._preserved_gid = os.getegid()

    def __enter__(self):
        self._preserve_ids()
        os.setegid(self._gid)
        os.seteuid(self._uid)

    def __exit__(self ,type, value, traceback):
        os.seteuid(self._preserved_uid)
        os.setegid(self._preserved_gid)
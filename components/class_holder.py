# resources_holder.py
from components.station import Station, StationType
from components.agv import  AGV
from components.path import  PathNode
from components.id_manager import IDManager

class ClassHolder:
    """Backend data holder for managing non-UI components"""
    def __init__(self):
        # ID managers
        self.station_id_manager = IDManager()
        self.agv_id_manager = IDManager()
        self.path_id_manager = IDManager()
        self.path_node_id_manager = IDManager()
        
        # Backend objects storage
        self.stations = {}  # id -> Station
        self.agvs = {}  # id -> AGV
        self.paths = {}  # id -> Path
        self.path_nodes = {}  # id -> PathNode
        
        # Name-based lookups
        self.stations_by_name = {}  # name -> Station
        self.agvs_by_name = {}  # name -> AGV
        
        # Station types
        self.station_types = {}  # name -> StationType
    
    # -----------
    # Station
    # -----------
    def add_station(self, station: Station) -> Station:
        """Add a station to backend storage"""
        if station.id is None:
            station.id = self.station_id_manager.get_new_id()
        
        # Store backend object
        self.stations[station.id] = station
        if station.name:
            self.stations_by_name[station.name] = station
            
        return station

    def get_station_by_id(self, station_id: int) -> Station:
        """Get backend station object"""
        return self.stations.get(station_id)

    def get_station_by_name(self, name: str) -> Station:
        """Get backend station object by name"""
        return self.stations_by_name.get(name)

    def delete_station(self, station_id: int):
        """Delete backend station object"""
        station = self.stations.pop(station_id, None)
        if station and station.name in self.stations_by_name:
            self.stations_by_name.pop(station.name)

    def get_all_stations(self) -> list[Station]:
        """Get all backend station objects"""
        return list(self.stations.values())

    # -----------
    # AGV
    # -----------
    def add_agv(self, agv: AGV) -> AGV:
        """Add an AGV to backend storage"""
        if agv.id is None:
            agv.id = self.agv_id_manager.get_new_id()
        
        # Store backend object
        self.agvs[agv.id] = agv
        if agv.name:
            self.agvs_by_name[agv.name] = agv
            
        return agv

    def get_agv_by_id(self, agv_id: int) -> AGV:
        """Get backend AGV object"""
        return self.agvs.get(agv_id)

    def get_agv_by_name(self, name: str) -> AGV:
        """Get backend AGV object by name"""
        return self.agvs_by_name.get(name)

    def delete_agv(self, agv_id: int):
        """Delete backend AGV object"""
        agv = self.agvs.pop(agv_id, None)
        if agv and agv.name in self.agvs_by_name:
            self.agvs_by_name.pop(agv.name)

    def get_all_agvs(self) -> list[AGV]:
        """Get all backend AGV objects"""
        return list(self.agvs.values())

    # -----------
    # PathNode
    # -----------
    def add_path_node(self, node: PathNode) -> PathNode:
        """Add a path node to backend storage"""
        if node.id is None:
            node.id = self.path_node_id_manager.get_new_id()
            
        # Store backend object
        self.path_nodes[node.id] = node
        
        return node

    def get_path_node_by_id(self, node_id: int) -> PathNode:
        """Get backend path node object"""
        return self.path_nodes.get(node_id)

    def delete_path_node(self, node_id: int):
        """Delete backend path node object"""
        self.path_nodes.pop(node_id, None)
    
    def get_all_path_nodes(self) -> list[PathNode]:
        """Get all backend path node objects"""
        return list(self.path_nodes.values())

    # -----------
    # StationType
    # -----------
    def add_station_type(self, station_type: StationType):
        """Add a station type"""
        self.station_types[station_type.name] = station_type

    def get_station_type(self, name: str) -> StationType:
        """Get a station type by name"""
        return self.station_types.get(name)

    def delete_station_type(self, name: str):
        """Delete a station type"""
        self.station_types.pop(name, None)

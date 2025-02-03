# resources_holder.py
from components.station import QStation, Station
from components.agv import QAGV, AGV
from components.path import QPathNode, PathNode
from components.class_holder import ClassHolder

class QClassHolder:
    """Frontend data holder for managing UI components"""
    def __init__(self, class_holder: ClassHolder):
        self.class_holder = class_holder
        
        # UI objects storage
        self.qstations = {}  # id -> QStation
        self.qagvs = {}  # id -> QAGV
        self.qpaths = {}  # id -> QPath
        self.qpath_nodes = {}  # id -> QPathNode
    
    # -----------
    # Station
    # -----------
    def add_qstation(self, station: Station) -> QStation:
        """Add a station and create its UI representation"""
        # Create and store UI object
        qstation = QStation(station)
        self.qstations[station.id] = qstation
        
        return qstation

    def get_qstation_by_id(self, station_id: int) -> QStation:
        """Get UI station object"""
        return self.qstations.get(station_id)

    def get_qstation_by_name(self, name: str) -> QStation:
        """Get UI station object by name"""
        station = self.class_holder.get_station_by_name(name)
        if station:
            return self.qstations.get(station.id)
        return None

    def delete_qstation(self, station_id: int):
        """Delete UI station object"""
        self.qstations.pop(station_id, None)

    def get_all_qstations(self) -> list[QStation]:
        """Get all UI station objects"""
        return list(self.qstations.values())

    # -----------
    # AGV
    # -----------
    def add_qagv(self, agv: AGV) -> QAGV:
        """Add an AGV and create its UI representation"""
        # Create and store UI object
        qagv = QAGV(agv)
        self.qagvs[agv.id] = qagv
        
        return qagv

    def get_qagv_by_id(self, agv_id: int) -> QAGV:
        """Get UI AGV object"""
        return self.qagvs.get(agv_id)

    def get_qagv_by_name(self, name: str) -> QAGV:
        """Get UI AGV object by name"""
        agv = self.class_holder.get_agv_by_name(name)
        if agv:
            return self.qagvs.get(agv.id)
        return None

    def delete_qagv(self, agv_id: int):
        """Delete UI AGV object"""
        self.qagvs.pop(agv_id, None)

    def get_all_qagvs(self) -> list[QAGV]:
        """Get all UI AGV objects"""
        return list(self.qagvs.values())

    # -----------
    # PathNode
    # -----------
    def add_qpath_node(self, node: PathNode) -> QPathNode:
        """Add a path node and create its UI representation"""
        # Create and store UI object
        qnode = QPathNode(node)
        self.qpath_nodes[node.id] = qnode
        
        return qnode

    def get_qpath_node_by_id(self, node_id: int) -> QPathNode:
        """Get UI path node object"""
        return self.qpath_nodes.get(node_id)

    def delete_qpath_node(self, node_id: int):
        """Delete UI path node object"""
        self.qpath_nodes.pop(node_id, None)
    
    def get_all_qpath_nodes(self) -> list[QPathNode]:
        """Get all UI path node objects"""
        return list(self.qpath_nodes.values())


from xml.etree import ElementTree as ET
from xml.dom import minidom
from components.station import Station, StationType
from components.path import PathNode
from components.agv import AGV

class MapExporter:
    """Exports map elements to XML file"""
    def __init__(self, map_editor):
        self.map_editor = map_editor
        self.qclass_holder = map_editor.qclass_holder
        self.class_holder = map_editor.class_holder

    def save_map(self, file_path):
        """Save map elements to XML file"""
        # Create root element
        root = ET.Element("map")
        
        # Add map size
        map_size = ET.SubElement(root, "map_size")
        map_size.text = str(self.map_editor.map_size)
        
        # Add station types
        station_types = ET.SubElement(root, "station_types")
        for station_type in self.map_editor.station_manager.get_all_types().values():
            type_elem = ET.SubElement(station_types, "station_type")
            ET.SubElement(type_elem, "name").text = station_type.name
            ET.SubElement(type_elem, "color").text = station_type.color
            ET.SubElement(type_elem, "description").text = station_type.description
        
        # Add stations
        stations = ET.SubElement(root, "stations")
        for station in self.class_holder.get_all_stations():
            station_elem = ET.SubElement(stations, "station")
            ET.SubElement(station_elem, "id").text = str(station.id)
            ET.SubElement(station_elem, "name").text = station.name
            ET.SubElement(station_elem, "x").text = str(station.position[0])
            ET.SubElement(station_elem, "y").text = str(station.position[1])
            ET.SubElement(station_elem, "type").text = station.station_type.name
            ET.SubElement(station_elem, "direction").text = str(station.direction)
            # Add 3D size
            size_elem = ET.SubElement(station_elem, "size")
            ET.SubElement(size_elem, "width").text = str(station.size.width)
            ET.SubElement(size_elem, "length").text = str(station.size.length)
            ET.SubElement(size_elem, "height").text = str(station.size.height)
            ET.SubElement(size_elem, "mesh_path").text = station.size.mesh_path
        
        # Add path nodes
        nodes = ET.SubElement(root, "path_nodes")
        for node in self.class_holder.get_all_path_nodes():
            node_elem = ET.SubElement(nodes, "node")
            ET.SubElement(node_elem, "id").text = str(node.id)
            ET.SubElement(node_elem, "x").text = str(node.position[0])
            ET.SubElement(node_elem, "y").text = str(node.position[1])
            ET.SubElement(node_elem, "direction").text = str(node.direction)
        
        # Add AGVs
        agvs = ET.SubElement(root, "agvs")
        for agv in self.class_holder.get_all_agvs():
            agv_elem = ET.SubElement(agvs, "agv")
            ET.SubElement(agv_elem, "id").text = str(agv.id)
            ET.SubElement(agv_elem, "name").text = agv.name
            ET.SubElement(agv_elem, "x").text = str(agv.position[0])
            ET.SubElement(agv_elem, "y").text = str(agv.position[1])
            ET.SubElement(agv_elem, "direction").text = str(agv.direction)
            ET.SubElement(agv_elem, "status").text = agv.status
            # Add size
            size_elem = ET.SubElement(agv_elem, "size")
            ET.SubElement(size_elem, "width").text = str(agv.size[0])
            ET.SubElement(size_elem, "length").text = str(agv.size[1])
            ET.SubElement(size_elem, "height").text = str(agv.size[2])
            # Add latest node if exists
            if agv.latest_node:
                ET.SubElement(agv_elem, "latest_node_id").text = str(agv.latest_node.id)
        
        # Create pretty XML string
        xml_str = ET.tostring(root, encoding='utf-8')
        dom = minidom.parseString(xml_str)
        pretty_xml = dom.toprettyxml(indent="  ")
        
        # Save to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(pretty_xml)



class MapLoader:
    """Loads map elements from XML file"""
    def __init__(self, map_editor):
        self.map_editor = map_editor
        self.qclass_holder = map_editor.qclass_holder
        self.class_holder = map_editor.class_holder

    def load_map(self, file_path):
        """Load map elements from XML file"""
        # Parse XML file
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        # Clear existing data
        self.clear_existing_data()
        
        # Load map size
        map_size = int(root.find('map_size').text)
        self.map_editor.map_size = map_size
        self.map_editor.map_size_spin.setValue(map_size)
        
        # Load station types
        station_types = root.find('station_types')
        for type_elem in station_types.findall('station_type'):
            station_type = StationType(
                name=type_elem.find('name').text,
                color=type_elem.find('color').text,
                description=type_elem.find('description').text
            )
            self.map_editor.station_manager.add_type(station_type)
        
        # Update station types list in UI
        self.map_editor.update_station_types_list()
        
        # Load path nodes first (needed for AGV references)
        nodes = root.find('path_nodes')
        node_dict = {}  # Store nodes for AGV reference
        for node_elem in nodes.findall('node'):
            node_id = int(node_elem.find('id').text)
            x = float(node_elem.find('x').text)
            y = float(node_elem.find('y').text)
            direction = float(node_elem.find('direction').text)
            
            # Create backend node
            node = PathNode(x, y, node_id)
            node = self.class_holder.add_path_node(node)
            
            # Create UI node and add to scene
            qnode = self.qclass_holder.add_path_node(node)
            qnode.set_direction(direction)
            self.map_editor.scene.addItem(qnode)
            
            # Store for AGV reference
            node_dict[node_id] = node
        
        # Load stations
        stations = root.find('stations')
        for station_elem in stations.findall('station'):
            station_id = int(station_elem.find('id').text)
            name = station_elem.find('name').text
            x = float(station_elem.find('x').text)
            y = float(station_elem.find('y').text)
            type_name = station_elem.find('type').text
            direction = float(station_elem.find('direction').text)
            
            # Get station type
            station_type = self.map_editor.station_manager.get_type(type_name)
            if not station_type:
                continue
            
            # Create backend station
            station = Station(x, y, station_type, name, station_id)
            station.direction = direction
            
            # Set 3D size
            size_elem = station_elem.find('size')
            station.set_3d_size(
                float(size_elem.find('width').text),
                float(size_elem.find('length').text),
                float(size_elem.find('height').text)
            )
            station.size.mesh_path = size_elem.find('mesh_path').text
            
            # Create UI station and add to scene
            qstation = self.qclass_holder.add_station(station)
            self.map_editor.scene.addItem(qstation)
        
        # Load AGVs
        agvs = root.find('agvs')
        for agv_elem in agvs.findall('agv'):
            agv_id = int(agv_elem.find('id').text)
            name = agv_elem.find('name').text
            x = float(agv_elem.find('x').text)
            y = float(agv_elem.find('y').text)
            direction = float(agv_elem.find('direction').text)
            status = agv_elem.find('status').text
            
            # Get size
            size_elem = agv_elem.find('size')
            size = [
                float(size_elem.find('width').text),
                float(size_elem.find('length').text),
                float(size_elem.find('height').text)
            ]
            
            # Create backend AGV
            agv = AGV(name, [x, y], size)
            agv.id = agv_id
            agv.direction = direction
            agv.status = status
            
            # Set latest node if exists
            latest_node_elem = agv_elem.find('latest_node_id')
            if latest_node_elem is not None:
                node_id = int(latest_node_elem.text)
                if node_id in node_dict:
                    agv.set_latest_node(node_dict[node_id])
            
            # Create UI AGV and add to scene
            qagv = self.qclass_holder.add_agv(agv)
            self.map_editor.scene.addItem(qagv)
        
        # Redraw grid
        self.map_editor.update_scene_rect()
        self.map_editor._draw_grid()
        
        # Emit map changed signal
        self.map_editor.map_changed.emit()
    
    def clear_existing_data(self):
        """Clear all existing data from scene and holders"""
        # Clear scene
        self.map_editor.scene.clear()
        
        # Clear backend holders
        self.class_holder.stations.clear()
        self.class_holder.stations_by_name.clear()
        self.class_holder.agvs.clear()
        self.class_holder.agvs_by_name.clear()
        self.class_holder.path_nodes.clear()
        
        # Clear UI holders
        self.qclass_holder.qstations.clear()
        self.qclass_holder.qagvs.clear()
        self.qclass_holder.qpath_nodes.clear()
        
        # Reset ID managers
        self.class_holder.station_id_manager.reset()
        self.class_holder.agv_id_manager.reset()
        self.class_holder.path_node_id_manager.reset()
from dataclasses import dataclass
from typing import Dict
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QGraphicsItem, QGraphicsRectItem
)
from PySide6.QtGui import (
    QPen, QBrush, QColor, QPainter, QPolygonF
)
from PySide6.QtCore import Qt, QPointF
from dataclasses import dataclass
from .path import PathNode, QPathNode
import math

@dataclass
class StationType:
    """Represents a type of station with its properties"""
    name: str
    color: str
    description: str = ""
    port_x: float = 1.5
    port_y: float = 0.0
    port_direction: float = 0.0

class StationTypeManager:
    """Manages different types of stations"""
    def __init__(self):
        self._types: Dict[str, StationType] = {}
        self._initialize_default_types()
    
    def _initialize_default_types(self):
        """Initialize default station types"""
        self.add_type(StationType("Loading", "#4CAF50", "Loading station for materials"))
        self.add_type(StationType("Unloading", "#f44336", "Unloading station for materials"))
        self.add_type(StationType("Charging", "#FFC107", "QAGV charging station"))
        self.add_type(StationType("Storage", "#2196F3", "Storage location"))
    
    def add_type(self, station_type: StationType) -> bool:
        """Add a new station type"""
        if station_type.name in self._types:
            return False
        self._types[station_type.name] = station_type
        return True
    
    def get_type(self, name: str) -> StationType:
        """Get a station type by name"""
        return self._types.get(name)
    
    def get_all_types(self) -> Dict[str, StationType]:
        """Get all station types"""
        return self._types.copy()
    
    def remove_type(self, name: str) -> bool:
        """Remove a station type"""
        if name in self._types:
            del self._types[name]
            return True
        return False 
    

class Station:
    """Backend data model for stations"""
    
    def __init__(self, x: float, y: float, station_type: StationType, name: str, id: int = None):
        # Store basic properties
        self.position = [x, y]
        self.station_type = station_type
        self.name = name
        self.id = id
        self.station_type = station_type
        # Store 3D properties
        self.size = [1.0, 1.0, 1.0]
        # Store direction in degrees (0 is facing right/east)
        self.direction = 0.0
        self.port: PathNode = None
        self.mesh_path: str = None
    
    def set_3d_size(self, width: float, length: float, height: float):
        """Set the 3D size of the station"""
        self.size[0] = width
        self.size[1] = length
        self.size[2] = height
    


class QStation(QGraphicsRectItem):
    """Custom graphics item for stations"""

    def __init__(self, station: Station):
        # Create backend station
        self.station = station
        # Create a 40x40 rectangle centered at the scaled position (100 units = 1 meter)
        super().__init__(self.station.position[0] * 100 - station.size[1]/2 * 100, -(self.station.position[1] * 100) - station.size[0]/2 * 100, station.size[1] * 100, station.size[0] * 100)
        
        # Set up graphics
        self.setFlag(QGraphicsItem.ItemIsSelectable)  # Only selectable, not movable
        self.setBrush(QBrush(QColor(self.station_type.color)))
        self.setPen(QPen(Qt.black, 2))
        
        # Initialize port as None
        self.qport = None
        # Create port if station type has port configuration
        self._update_port()
        self._update_tooltip()

    def _update_port(self):
        """Update the port position and create/update QPathNode"""
        if hasattr(self.station_type, 'port_x') and hasattr(self.station_type, 'port_y'):
            # calculate the port position from relative position
            angle = self.station.direction * math.pi / 180
            port_x = self.station.position[0] + self.station.station_type.port_x * math.cos(angle) - self.station.station_type.port_y * math.sin(angle)
            port_y = self.station.position[1] + self.station.station_type.port_x * math.sin(angle) + self.station.station_type.port_y * math.cos(angle)
            
            # Create or update port node
            port_direction = (self.station.direction + self.station.station_type.port_direction) % 360
            if self.qport is None:
                path_node = PathNode(port_x, port_y, port_direction, id=None, name=f"{self.station.name} Port")
                self.qport = QPathNode(path_node)
                # Add port to scene if station is in a scene
                if self.scene():
                    self.scene().addItem(self.qport)
            else:
                # Update existing port position and direction
                self.qport.node.position = [port_x, port_y]
                self.qport.node.direction = port_direction
                self.qport.setPos(port_x * 100, -port_y * 100)
                self.qport.direction_arrow.update_arrow(port_direction)

    def pos(self):
        """Override pos to return stored position"""
        return self.station.position
    
    def _update_tooltip(self):
        """Update tooltip with current position and information"""
        pos = self.pos()
        self.setToolTip(
            f"Type: {self.station.station_type.name}\n"
            f"Name: {self.station.name}\n"
            f"Position: ({pos[0]:.3f}, {pos[1]:.3f})\n"
            f"Direction: {self.station.direction:.1f}°\n"
            f"Size: {self.station.size.width:.3f}x{self.station.size.length:.3f}x{self.station.size.height:.3f}\n"
            f"{self.station.station_type.description}"
        )
    
    def set_3d_size(self, width: float, length: float, height: float):
        """Set the 3D size of the station"""
        self.station.set_3d_size(width, length, height)
        self._update_tooltip()
    
    def set_mesh_path(self, path: str):
        """Set the path to the STL mesh file"""
        self.station.set_mesh_path(path)
        self._update_tooltip()
    
    def itemChange(self, change, value):
        """Handle item changes, particularly position changes"""
        if change == QGraphicsItem.ItemPositionChange:
            self._update_tooltip()
        elif change == QGraphicsItem.ItemSceneChange:
            # Remove port from old scene
            if self.qport and self.qport.scene():
                self.qport.scene().removeItem(self.qport)
        elif change == QGraphicsItem.ItemSceneHasChanged:
            # Add port to new scene
            if self.qport and self.scene():
                self.scene().addItem(self.qport)
        return super().itemChange(change, value)
    
    def paint(self, painter: QPainter, option, widget):
        """Paint the station with its name, type indicator and direction"""
        # Save painter state
        painter.save()
        
        # Translate to center for rotation
        rect = self.boundingRect()
        center = rect.center()
        painter.translate(center)
        painter.rotate(-self.station.direction)
        painter.translate(-center)
        
        # Draw the rectangle
        painter.setBrush(QBrush(QColor(self.station_type.color)))
        painter.setPen(QPen(Qt.black, 2))
        painter.drawRect(rect)
        
        # Draw direction indicator (arrow)
        arrow_length = 30  # pixels
        arrow_width = 10  # pixels
        
        # Calculate arrow points
        center_x = rect.center().x()
        center_y = rect.center().y()
        
        # Draw arrow
        painter.setBrush(QBrush(Qt.black))
        painter.setPen(QPen(Qt.black, 2))
        points = [
            QPointF(center_x, center_y - arrow_width/2),  # Base left
            QPointF(center_x + arrow_length, center_y),   # Tip
            QPointF(center_x, center_y + arrow_width/2)   # Base right
        ]
        painter.drawPolygon(QPolygonF(points))
        
        # Draw station name and type
        painter.resetTransform()  # Reset transform for text to be readable
        
        # Set up text properties
        painter.setPen(Qt.black)
        font = painter.font()
        font.setBold(True)
        painter.setFont(font)

        painter.restore()

    def set_direction(self, angle: float):
        """Set the direction of the station in degrees"""
        self.station.direction = angle
        self._update_port()  # Update port position when direction changes
        self._update_tooltip()
        self.update()
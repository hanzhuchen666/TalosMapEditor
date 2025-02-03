from PySide6.QtWidgets import (
    QGraphicsItem, QGraphicsEllipseItem, QGraphicsPathItem,
    QGraphicsPolygonItem
)
from PySide6.QtGui import (
    QPen, QBrush, QColor, QPolygonF
)
from PySide6.QtCore import Qt, QPointF
import math


class PathNode:
    """Backend data model for path nodes"""
    
    def __init__(self, x: float, y: float, direction: float = 0.0, id: int = None, name: str = None):
        # Store position in meters
        self.position = [x, y]
        # Store connected paths
        self.connected_paths = []
        # Store ID
        self.id = id
        # Store direction in degrees (0 is east, 90 is north)
        self.direction = direction
        # Store the name
        self.name = name
    
    def get_position(self):
        """Get node position"""
        return self.position
    
    def set_direction(self, direction: float):
        """Set node direction in degrees"""
        self.direction = direction


class QPathNode(QGraphicsEllipseItem):
    """Node for path creation and connection"""
    
    def __init__(self, node: PathNode):
        # Create a 10x10 circle centered at the given position
        self.node = node
        x = self.node.position[0]
        y = self.node.position[1]
        # Node size
        self.node_size = 10
        # Arrow properties
        self.arrow_size = 8  # pixels
        self.arrow_angle = 30  # degrees
        
        
        super().__init__(x*100 - self.node_size/2, -(y*100) - self.node_size/2, self.node_size, self.node_size)
        self.setFlag(QGraphicsItem.ItemIsSelectable)  # Only selectable, not movable
        
        # Set appearance
        self.setBrush(QBrush(QColor("#666666")))
        self.setPen(QPen(Qt.black, 1))
        
        # Ensure node is always on top
        self.setZValue(1000)  # High Z value to stay on top
        
        # Create direction arrow as a polygon item
        self.direction_arrow = QGraphicsPolygonItem(self)
        self.direction_arrow.setBrush(QBrush(Qt.red))
        self.direction_arrow.setPen(QPen(Qt.red, 2))
        self.direction_arrow.setZValue(1001)  # Above the node
        self._update_arrow(self.node.direction)
        
        # Set tooltip
        self._update_tooltip()
    
    def _update_arrow(self, direction=0):
        """Update arrow shape and direction"""
        # Calculate arrow points
        angle = math.radians(direction)
        
        # Arrow endpoint
        end_x = self.arrow_size * math.cos(angle)
        end_y = -self.arrow_size * math.sin(angle)  # Subtract because y-axis is inverted
        
        # Calculate arrow head points
        arrow_angle_rad = math.radians(self.arrow_angle)
        arrow_p1 = QPointF(
            -self.arrow_size/2 * math.cos(angle + arrow_angle_rad),
            self.arrow_size/2 * math.sin(angle + arrow_angle_rad)
        )
        arrow_p2 = QPointF(
            -self.arrow_size/2 * math.cos(angle - arrow_angle_rad),
            self.arrow_size/2 * math.sin(angle - arrow_angle_rad)
        )
        
        # Create arrow polygon
        arrow_points = [QPointF(0, 0), QPointF(end_x, end_y), arrow_p1, QPointF(end_x, end_y), arrow_p2]
        self.direction_arrow.setPolygon(QPolygonF(arrow_points))
    
    def _update_tooltip(self):
        """Update tooltip with current position and direction"""
        self.setToolTip(f"Node Position: ({self.node.position[0]:.3f}, {self.node.position[1]:.3f})\n"
                         f"Direction: {self.node.direction:.1f}°\n"
                         f"Name: {self.node.name}")
    
    def pos(self):
        """Override pos to return stored position"""
        return self.node.position
    
    def get_center(self) -> QPointF:
        """Get the center position of the node"""
        return self._pos
    
    @property
    def id(self):
        """Get node ID"""
        return self.node.id
    
    @id.setter
    def id(self, value):
        """Set node ID"""
        self.node.id = value

    def set_direction(self, angle: float):
        """Set the direction of the node"""
        self.node.direction = angle
        self._update_arrow(angle)
        self._update_tooltip()

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtWidgets import QGraphicsItem
from PySide6.QtGui import QPen, QBrush, QColor, QPainter, QPolygonF
from typing import List
from components.path import PathNode

class AGVStatus:
    IDLE = "idle"
    MOVING = "moving"
    LOADING = "loading"
    UNLOADING = "unloading"
    CHARGING = "charging"
    ERROR = "error"
    UNKNOWN = "unknown"

class AGV:
    def __init__(self, name: str, position: List[float], size: List[float]):
        # Basic properties
        self.name = name
        self.position = position  # Store position in meters
        self.size = size  # [width, length, height] in meters
        self.id = None
        # Status properties
        self.max_speed = 1.0  # m/s
        self.max_acc = 0.5   # m/s^2
        self.max_dec = 0.5   # m/s^2
        self.direction = 0.0  # in degrees
        self.status = AGVStatus.UNKNOWN
        # agv interactions
        self.agv_interactions = []
        # agv port 
        self.port = None

    
    
class QAGV(QGraphicsItem):
    """QAGV class for visualization"""
    def __init__(self, agv: AGV):
        super().__init__()
        self.agv = agv
        self.id = self.agv.id
        self.position = [self.agv.position[0], self.agv.position[1]]
        self.direction = self.agv.direction
        self.name = self.agv.name

        # Visual properties
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setPos(self.agv.position[0] * 100, - self.agv.position[1] * 100)  # Convert to scene units (pixels)

        # Set default color based on status
        self.color = QColor("#4287f5")  # Default blue color
        
        # Update tooltip with QAGV info
        self._update_tooltip()

    
    def _update_tooltip(self):
        """Update tooltip with QAGV information"""
        self.setToolTip(
            f"QAGV: {self.agv.name}\n"
            f"Status: {self.agv.status}\n"
            f"Speed: {self.agv.max_speed:.3f} m/s\n"
            f"Direction: {self.agv.direction:.2f}°\n"
            f"Position: ({self.agv.position[0]:.3f}, {self.agv.position[1]:.3f})"
        )
    
    def boundingRect(self) -> QRectF:
        """Return the bounding rectangle of the QAGV"""
        # Convert size from meters to scene units (pixels)
        width = self.agv.size[0] * 100
        length = self.agv.size[1] * 100
        return QRectF(-length/2, -width/2, length, width)
    
    def paint(self, painter: QPainter, option, widget):
        """Paint the QAGV"""
        # Save painter state
        painter.save()
        
        # Get bounding rectangle
        rect = self.boundingRect()
        center = rect.center()
        
        # Translate to center, rotate, and translate back
        painter.translate(center)
        painter.rotate(-self.agv.direction)
        painter.translate(-center)
        
        # Draw AGV body
        painter.setBrush(QBrush(self.color))
        painter.setPen(QPen(QColor("#000000"), 2))
        painter.drawRect(rect)
        
        # Draw direction indicator (arrow)
        arrow_length = rect.width() * 0.8  # 80% of AGV width
        arrow_width = arrow_length * 0.3   # 30% of arrow length
        
        # Calculate arrow points
        center_x = rect.center().x()
        center_y = rect.center().y()
        
        # Draw arrow
        painter.setBrush(QBrush(Qt.red))
        painter.setPen(QPen(Qt.red, 2))
        points = [
            QPointF(center_x, center_y - arrow_width/2),  # Base left
            QPointF(center_x + arrow_length/2, center_y),  # Tip
            QPointF(center_x, center_y + arrow_width/2)   # Base right
        ]
        painter.drawPolygon(QPolygonF(points))
        
        # Restore painter state
        painter.restore()
        
        # Update tooltip
        self._update_tooltip()

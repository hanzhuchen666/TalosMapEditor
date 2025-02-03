from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QGraphicsView, QGraphicsScene, QColorDialog,
    QInputDialog, QMessageBox, QListWidget, QLabel,
    QDialog, QLineEdit, QFormLayout, QDialogButtonBox,
    QSpinBox, QListWidgetItem, QFrame, QFileDialog,
    QStackedWidget, QButtonGroup, QDoubleSpinBox,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt, Signal,  QPointF
from PySide6.QtGui import QPen, QColor, QPainter, QBrush, QPolygonF
from components.station import QStation, Station
from components.path import QPathNode, PathNode
from components.station import StationType, StationTypeManager
from ui.file_management import MapExporter, MapLoader
from ui.agv_editor import AGVEditor
from components.qclass_holder import QClassHolder

class NewStationTypeDialog(QDialog):
    """Dialog for creating a new station type"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New QStation Type")
        self.setup_ui()
    
    def setup_ui(self):
        layout = QFormLayout(self)
        
        # Add input fields
        self.name_edit = QLineEdit()
        self.color_btn = QPushButton("Select Color")
        self.color_btn.clicked.connect(self.select_color)
        self.description_edit = QLineEdit()
        self.selected_color = "#000000"
        self.port_x_input = QDoubleSpinBox()
        self.port_x_input.setRange(-50.0, 50.0)
        self.port_x_input.setDecimals(2)
        self.port_x_input.setSingleStep(0.1)
        self.port_y_input = QDoubleSpinBox()
        self.port_y_input.setRange(-50.0, 50.0)
        self.port_y_input.setDecimals(2)
        self.port_y_input.setSingleStep(0.1)
        self.port_direction_input = QDoubleSpinBox()
        self.port_direction_input.setRange(0, 359.99)
        self.port_direction_input.setDecimals(2)
        self.port_direction_input.setSingleStep(15.0)
        self.port_direction_input.setSuffix("°")
        
        layout.addRow("Name:", self.name_edit)
        layout.addRow("Color:", self.color_btn)
        layout.addRow("Description:", self.description_edit)
        layout.addRow("Port X:", self.port_x_input)
        layout.addRow("Port Y:", self.port_y_input)
        layout.addRow("Port Direction:", self.port_direction_input)
        
        # Add buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
    
    def select_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.selected_color = color.name()
            self.color_btn.setStyleSheet(f"background-color: {self.selected_color}")
    
    def get_station_type(self) -> StationType:
        return StationType(
            self.name_edit.text(),
            self.selected_color,
            self.description_edit.text(),
            self.port_x_input.value(),
            self.port_y_input.value(),
            self.port_direction_input.value()
        )

class StationTypeItem(QListWidgetItem):
    """List widget item representing a station type"""
    def __init__(self, station_type: StationType, parent=None):
        super().__init__(parent)
        self.station_type = station_type
        # self.setText(station_type.name)
        self.setToolTip(station_type.description)
        
        # Create the custom widget for display
        self.custom_widget = StationTypeWidget(station_type)
        self.setSizeHint(self.custom_widget.sizeHint())

class StationTypeWidget(QWidget):
    """Widget for displaying station type in list"""
    def __init__(self, station_type: StationType, parent=None):
        super().__init__(parent)
        self.station_type = station_type
        self.setup_ui()
    
    def setup_ui(self):
        layout = QHBoxLayout(self)
        
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(20)  # Add spacing between elements
        
        # Color indicator
        color_frame = QFrame()
        color_frame.setFixedSize(20, 20)
        color_frame.setStyleSheet(
            f"background-color: {self.station_type.color}; "
            f"border: 1px solid black; border-radius: 2px;"
        )
        layout.addWidget(color_frame)
        
        # Type name and description
        info_layout = QVBoxLayout()
        info_layout.setSpacing(1)  # Reduce spacing between name and description
        
        name_label = QLabel(f"<b>{self.station_type.name}</b>")
        name_label.setStyleSheet("color: black;")  # Ensure text is visible
        
        desc_label = QLabel(self.station_type.description)
        desc_label.setStyleSheet("color: #666666;")  # Gray color for description
        desc_label.setWordWrap(False)
        
        info_layout.addWidget(name_label)
        info_layout.addWidget(desc_label)
        layout.addLayout(info_layout)
        layout.addStretch()
        
        # Set fixed height to prevent overlap
        self.setMinimumHeight(50)

class ZoomableGraphicsView(QGraphicsView):
    """Custom QGraphicsView with zoom and pan support"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRenderHint(QPainter.Antialiasing)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        
        # Set dark background color
        self.setBackgroundBrush(QBrush(QColor("#1e1e1e")))  # Dark gray background
        
        self.zoom_factor = 1.15
        self.panning = False
        self.last_mouse_pos = None
    
    def wheelEvent(self, event):
        """Handle mouse wheel events for zooming"""
        if event.angleDelta().y() > 0:
            self.scale(self.zoom_factor, self.zoom_factor)
        else:
            self.scale(1 / self.zoom_factor, 1 / self.zoom_factor)
    
    def mousePressEvent(self, event):
        """Handle mouse press events"""
        if event.button() == Qt.MiddleButton:
            # Enable panning mode
            self.panning = True
            self.last_mouse_pos = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
        else:
            super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release events"""
        if event.button() == Qt.MiddleButton:
            # Disable panning mode
            self.panning = False
            self.setCursor(Qt.ArrowCursor)
            event.accept()
        else:
            super().mouseReleaseEvent(event)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move events"""
        if self.panning and self.last_mouse_pos is not None:
            # Calculate the difference between current and last position
            delta = event.pos() - self.last_mouse_pos
            self.last_mouse_pos = event.pos()
            
            # Pan the view
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - delta.x()
            )
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - delta.y()
            )
            event.accept()
        else:
            super().mouseMoveEvent(event)

class MapEditor(QWidget):
    """Map editor widget for creating and editing QAGV stations and paths"""
    
    map_changed = Signal()  # Signal emitted when map is modified
    station_added = Signal(object)  # Signal emitted when a station is added
    station_modified = Signal(object)  # Signal emitted when a station is modified
    station_removed = Signal(object)  # Signal emitted when a station is removed
    map_size_changed = Signal(int)  # Signal emitted when map size changes
    
    def __init__(self, qclass_holder: QClassHolder):
        super().__init__()
        self.qclass_holder = qclass_holder
        self.class_holder = qclass_holder.class_holder
        self.station_manager = StationTypeManager()
        self.current_mode = "station"  # or "path" or "agv"
        self.path_tool = "add"  # or "delete" or "connect"
        self.current_path = None
        self.first_node = None  # For path connection
        self.map_size = 10  # Map size in meters (half-width/height)
        self.setup_ui()
        
        # Set up custom event handling
        self.view.original_mouse_press = self.view.mousePressEvent
        self.view.original_mouse_release = self.view.mouseReleaseEvent
        self.view.original_mouse_move = self.view.mouseMoveEvent
        
        self.view.mousePressEvent = self.handle_mouse_press
        self.view.mouseReleaseEvent = self.handle_mouse_release
        self.view.mouseMoveEvent = self.handle_mouse_move
    
    def setup_ui(self):
        """Set up the user interface"""
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(10)
        
        # Left side: Map view
        map_layout = QVBoxLayout()
        map_layout.setSpacing(5)
        
        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(5)
        map_layout.addLayout(toolbar)
        
        # Mode buttons styling
        button_style = """
            QPushButton {
                background-color: #2196F3;
                color: black;
                border: none;
                padding: 5px 15px;
                border-radius: 4px;
            }
            QPushButton:checked {
                background-color: #1976D2;
            }
            QPushButton:hover {
                background-color: #42A5F5;
            }
        """
        
        # Add mode buttons
        self.station_btn = QPushButton("QStation Mode")
        self.station_btn.setCheckable(True)
        self.station_btn.setChecked(True)
        self.station_btn.clicked.connect(lambda: self.set_mode("station"))
        self.station_btn.setStyleSheet(button_style)
        toolbar.addWidget(self.station_btn)
        
        self.path_btn = QPushButton("QPath Mode")
        self.path_btn.setCheckable(True)
        self.path_btn.clicked.connect(lambda: self.set_mode("path"))
        self.path_btn.setStyleSheet(button_style)
        toolbar.addWidget(self.path_btn)
        
        self.agv_btn = QPushButton("QAGV Mode")
        self.agv_btn.setCheckable(True)
        self.agv_btn.clicked.connect(lambda: self.set_mode("agv"))
        self.agv_btn.setStyleSheet(button_style)
        toolbar.addWidget(self.agv_btn)
        
        # Add map size control
        toolbar.addStretch()
        toolbar.addWidget(QLabel("Map Size (meters):"))
        self.map_size_spin = QSpinBox()
        self.map_size_spin.setRange(5, 100)  # Allow maps from 5m to 100m
        self.map_size_spin.setValue(self.map_size)
        self.map_size_spin.valueChanged.connect(self.update_map_size)
        toolbar.addWidget(self.map_size_spin)
        
        # Create graphics view
        self.scene = QGraphicsScene(self)
        self.view = ZoomableGraphicsView()
        self.view.setScene(self.scene)
        map_layout.addWidget(self.view)
        
        # Set up the scene with initial size
        self.update_scene_rect()
        self._draw_grid()
        
        main_layout.addLayout(map_layout, stretch=2)
        
        # Right side panel
        panel_layout = QVBoxLayout()
        panel_layout.setSpacing(10)
        
        # Create stacked widget for different mode tools
        self.tools_stack = QStackedWidget()
        panel_layout.addWidget(self.tools_stack)
        
        # QStation tools
        station_tools = QWidget()
        station_layout = QVBoxLayout(station_tools)
        
        # QStation types
        types_label = QLabel("<h3>Station Types</h3>")
        station_layout.addWidget(types_label)
        
        new_type_btn = QPushButton("New Station Type")
        new_type_btn.clicked.connect(self.add_station_type)
        station_layout.addWidget(new_type_btn)
        
        self.type_list = QListWidget()
        self.update_station_types_list()
        station_layout.addWidget(self.type_list)
        
        # Position input
        pos_label = QLabel("<h3>Add Station (meters)</h3>")
        station_layout.addWidget(pos_label)
        
        pos_form = QFormLayout()
        self.pos_x = QDoubleSpinBox()
        self.pos_x.setRange(-50.0, 50.0)
        self.pos_x.setDecimals(2)
        self.pos_x.setSingleStep(0.1)
        
        self.pos_y = QDoubleSpinBox()
        self.pos_y.setRange(-50.0, 50.0)
        self.pos_y.setDecimals(2)
        self.pos_y.setSingleStep(0.1)
        
        # Add direction input
        self.direction_spin = QDoubleSpinBox()
        self.direction_spin.setRange(0, 359.99)  # 0-360 degrees
        self.direction_spin.setDecimals(2)
        self.direction_spin.setValue(0.0)
        self.direction_spin.setSingleStep(15.0)  # 15 degree steps for convenience
        self.direction_spin.setSuffix("°")  # Add degree symbol
        
        pos_form.addRow("X (m):", self.pos_x)
        pos_form.addRow("Y (m):", self.pos_y)
        pos_form.addRow("Direction:", self.direction_spin)
        station_layout.addLayout(pos_form)
        
        # 3D properties
        size_label = QLabel("<h3>Station Size (meters)</h3>")
        station_layout.addWidget(size_label)
        
        size_form = QFormLayout()
        self.width_spin = QDoubleSpinBox()
        self.width_spin.setRange(0.1, 10.0)
        self.width_spin.setDecimals(2)
        self.width_spin.setValue(1.0)
        self.width_spin.setSingleStep(0.1)
        
        self.length_spin = QDoubleSpinBox()
        self.length_spin.setRange(0.1, 10.0)
        self.length_spin.setDecimals(2)
        self.length_spin.setValue(1.0)
        self.length_spin.setSingleStep(0.1)
        
        self.height_spin = QDoubleSpinBox()
        self.height_spin.setRange(0.1, 10.0)
        self.height_spin.setDecimals(2)
        self.height_spin.setValue(1.0)
        self.height_spin.setSingleStep(0.1)
        
        size_form.addRow("Width (m):", self.width_spin)
        size_form.addRow("Length (m):", self.length_spin)
        size_form.addRow("Height (m):", self.height_spin)
        station_layout.addLayout(size_form)
        
        mesh_btn = QPushButton("Load STL Mesh")
        mesh_btn.clicked.connect(self.load_station_mesh)
        station_layout.addWidget(mesh_btn)
        
        add_btn = QPushButton("Add Station")
        add_btn.clicked.connect(self.add_station_at_position)
        station_layout.addWidget(add_btn)
        
        # Add station table button and table dialog
        show_stations_btn = QPushButton("Show Stations Table")
        show_stations_btn.clicked.connect(self.show_stations_table)
        station_layout.addWidget(show_stations_btn)
        
        # QPath tools
        path_tools = QWidget()
        path_layout = QVBoxLayout(path_tools)
        
        path_label = QLabel("<h3>Path Tools</h3>")
        path_layout.addWidget(path_label)
        
        # Path tool buttons
        path_tools_group = QButtonGroup(self)
        path_tools_group.buttonClicked.connect(self.set_path_tool)
        
        add_node_btn = QPushButton("Add Node")
        add_node_btn.setCheckable(True)
        add_node_btn.setChecked(True)
        path_tools_group.addButton(add_node_btn, 0)
        path_layout.addWidget(add_node_btn)
        
        delete_node_btn = QPushButton("Delete Node")
        delete_node_btn.setCheckable(True)
        path_tools_group.addButton(delete_node_btn, 1)
        path_layout.addWidget(delete_node_btn)
        
        # Add path node by position button
        add_node_pos_btn = QPushButton("Add Node by Position")
        add_node_pos_btn.clicked.connect(self.add_path_node_by_position)
        path_layout.addWidget(add_node_pos_btn)
        
        # Add tools to stack
        self.tools_stack.addWidget(station_tools)
        self.tools_stack.addWidget(path_tools)
        
        # Add QAGV tools
        self.agv_editor = AGVEditor(self.qclass_holder, self)  # Pass self (MapEditor) as parent
        self.tools_stack.addWidget(self.agv_editor)
        
        main_layout.addLayout(panel_layout, stretch=1)
        
        # Apply styling
        self.setStyleSheet(self.get_style_sheet())
    
    def get_style_sheet(self):
        """Get the style sheet for the widget"""
        return """
            QLabel {
                color: #333333;
                margin-top: 10px;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 5px 15px;
                border-radius: 4px;
                margin: 5px 0;
            }
            QPushButton:hover {
                background-color: #66BB6A;
            }
            QPushButton:checked {
                background-color: #388E3C;
            }
            QListWidget {
                border: 1px solid #CCCCCC;
                border-radius: 4px;
            }
        """
    
    def set_mode(self, mode):
        """Set the current editing mode"""
        # Reset path connection if changing modes
        if self.current_mode == "path" and self.first_node:
            self.first_node.setBrush(QBrush(QColor("#666666")))
            self.first_node = None
        
        self.current_mode = mode
        self.station_btn.setChecked(mode == "station")
        self.path_btn.setChecked(mode == "path")
        self.agv_btn.setChecked(mode == "agv")
        
        # Switch tool panel
        if mode == "station":
            self.tools_stack.setCurrentIndex(0)
            self.current_path = None
            self.view.setDragMode(QGraphicsView.RubberBandDrag)
        elif mode == "path":
            self.tools_stack.setCurrentIndex(1)
            self.view.setDragMode(QGraphicsView.NoDrag)
        else:  # QAGV mode
            self.tools_stack.setCurrentIndex(2)
            self.view.setDragMode(QGraphicsView.RubberBandDrag)
    
    def set_path_tool(self, button):
        """Set the current path tool"""
        tool_id = self.sender().id(button)
        if tool_id == 0:  # Add Node
            self.path_tool = "add"
        elif tool_id == 1:  # Delete Node
            self.path_tool = "delete"
    
    def handle_mouse_press(self, event):
        """Handle mouse press events"""
        if event.button() == Qt.MiddleButton:
            # Let the view handle panning
            self.view.original_mouse_press(event)
            return
        
        pos = self.view.mapToScene(event.pos())
        
        if self.current_mode == "path":
            if event.button() == Qt.LeftButton:
                if self.path_tool == "add":
                    # Show direction input dialog
                    dialog = QDialog(self)
                    dialog.setWindowTitle("Set Node Direction")
                    dialog.setModal(True)
                    
                    layout = QFormLayout(dialog)
                    direction_input = QDoubleSpinBox()
                    direction_input.setRange(0, 359.99)
                    direction_input.setDecimals(2)
                    direction_input.setSuffix("°")
                    direction_input.setSingleStep(15.0)
                    layout.addRow("Direction:", direction_input)
                    
                    buttons = QDialogButtonBox(
                        QDialogButtonBox.Ok | QDialogButtonBox.Cancel
                    )
                    buttons.accepted.connect(dialog.accept)
                    buttons.rejected.connect(dialog.reject)
                    layout.addRow(buttons)
                    
                    if dialog.exec_() == QDialog.Accepted:
                        # Create backend PathNode first
                        node = PathNode(pos.x()/100, -pos.y()/100, direction=direction_input.value(), id=self.class_holder.path_node_id_manager.get_new_id())
                        node = self.class_holder.add_path_node(node)
                        try:
                            # Add to resources holder and get UI object
                            qnode = self.qclass_holder.add_qpath_node(node)
                            # Set direction after creating UI object
                            qnode.set_direction(direction_input.value())
                            # Add to scene
                            self.scene.addItem(qnode)
                            self.map_changed.emit()
                        except ValueError as e:
                            QMessageBox.warning(self, "Error", str(e))
                
                elif self.path_tool == "delete":
                    # Find and delete clicked node or path
                    item = self.scene.itemAt(pos, self.view.transform())
                    if isinstance(item, QPathNode):
                        try:
                            # Remove node
                            self.qclass_holder.delete_qpath_node(item.node.id)
                            self.class_holder.delete_path_node(item.node.id)
                            self.scene.removeItem(item)
                            self.map_changed.emit()
                        except ValueError as e:
                            QMessageBox.warning(self, "Error", str(e))

        else:
            # Handle other modes
            self.view.original_mouse_press(event)
    
    def handle_mouse_release(self, event):
        """Handle mouse release events"""
        if event.button() == Qt.MiddleButton:
            self.view.original_mouse_release(event)
        else:
            self.view.original_mouse_release(event)
    
    def handle_mouse_move(self, event):
        """Handle mouse move events"""
        if self.view.panning:
            self.view.original_mouse_move(event)
        else:
            self.view.original_mouse_move(event)
    
    def update_station_types_list(self):
        """Update the station types list in the side panel"""
        self.type_list.clear()
        for station_type in self.station_manager.get_all_types().values():
            # Create list item with custom widget
            item = StationTypeItem(station_type)
            self.type_list.addItem(item)
            self.type_list.setItemWidget(item, item.custom_widget)
    
    def add_station_type(self):
        """Add a new station type"""
        dialog = NewStationTypeDialog(self)
        if dialog.exec_():
            station_type = dialog.get_station_type()
            if self.station_manager.add_type(station_type):
                self.update_station_types_list()
    
    def add_station_at_position(self):
        """Add a station at the specified position"""
        selected_items = self.type_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Error", "Please select a station type")
            return
        
        station_type = selected_items[0].station_type
        name, ok = QInputDialog.getText(
            self, "New Station", "Enter station name:"
        )
        if ok and name:
            # Create backend Station first
            station = Station(
                self.pos_x.value(),
                self.pos_y.value(),
                station_type,
                name
            )
            # Set 3D size
            station.set_3d_size(
                self.width_spin.value(),
                self.length_spin.value(),
                self.height_spin.value()
            )
            # Set direction
            station.direction = self.direction_spin.value()
            
            try:
                # Add to resources holder and get UI object
                station = self.class_holder.add_station(station)
                qstation = self.qclass_holder.add_qstation(station)
                # Add visual representation to scene
                self.scene.addItem(qstation)
                # Emit signals
                self.map_changed.emit()
                self.station_added.emit(qstation)
            except ValueError as e:
                QMessageBox.warning(self, "Error", str(e))
    
    def update_map_size(self, new_size:int):
        """Update the map size and redraw the grid"""
        self.map_size = new_size
        self.update_scene_rect()
        
        # Get all components from resources holder
        qstations = self.qclass_holder.get_all_qstations()
        qpath_nodes = self.qclass_holder.get_all_qpath_nodes()
        qagvs = self.qclass_holder.get_all_qagvs()
        
        # Clear scene and redraw grid
        self.scene.clear()
        self.qclass_holder.qpath_nodes.clear()
        self.qclass_holder.qstations.clear()
        self.qclass_holder.qagvs.clear()
        self._draw_grid()
        
        # Re-add all components to scene
        for qnode in qpath_nodes:
            qnode = self.qclass_holder.add_qpath_node(qnode)
            self.scene.addItem(qnode)

        for qstation in qstations:
            qstation = self.qclass_holder.add_qstation(qstation)
            self.scene.addItem(qstation)

        for qagv in qagvs:
            qagv = self.qclass_holder.add_qagv(qagv)
            self.scene.addItem(qagv)

        self.map_changed.emit()
        self.map_size_changed.emit(new_size)  # Emit signal with new size
    
    def update_scene_rect(self):
        """Update the scene rectangle based on map size"""
        # Convert map size from meters to scene units (100 units = 1 meter)
        scene_size = self.map_size * 100
        self.scene.setSceneRect(-scene_size, -scene_size, scene_size * 2, scene_size * 2)
    
    def _draw_grid(self):
        """Draw background grid and coordinate axes"""
        # Draw grid (1 meter spacing) with darker color for better visibility
        grid_pen = QPen(QColor("#333333"))  # Darker grid lines
        grid_pen.setWidth(1)
        
        # Draw vertical and horizontal grid lines every meter
        for i in range(-self.map_size, self.map_size + 1):
            # Convert meters to scene units (100 units = 1 meter)
            pos = i * 100
            self.scene.addLine(pos, -self.map_size * 100, pos, self.map_size * 100, grid_pen)
            self.scene.addLine(-self.map_size * 100, pos, self.map_size * 100, pos, grid_pen)
        
        # Draw coordinate axes with brighter colors
        axis_pen = QPen(Qt.white)  # White for better visibility
        axis_pen.setWidth(2)
        
        # X-axis (bright red)
        x_axis = self.scene.addLine(-self.map_size * 100, 0, self.map_size * 100, 0, QPen(QColor("#FF6B6B"), 2))
        # Add arrow for X-axis
        arrow_size = 20  # Arrow size in scene units
        x_arrow = self.scene.addPolygon(
            QPolygonF([
                QPointF(self.map_size * 100 - arrow_size, -arrow_size/2),
                QPointF(self.map_size * 100, 0),
                QPointF(self.map_size * 100 - arrow_size, arrow_size/2)
            ]),
            QPen(QColor("#FF6B6B")),
            QBrush(QColor("#FF6B6B"))
        )
        # X-axis label with brighter color
        x_label = self.scene.addText("X")
        x_label.setDefaultTextColor(QColor("#FF6B6B"))
        x_label.setPos(self.map_size * 100 + 10, 5)
        
        # Y-axis (bright green)
        y_axis = self.scene.addLine(0, -self.map_size * 100, 0, self.map_size * 100, QPen(QColor("#4ADE80"), 2))
        # Add arrow for Y-axis
        y_arrow = self.scene.addPolygon(
            QPolygonF([
                QPointF(-arrow_size/2, -self.map_size * 100 + arrow_size),
                QPointF(0, -self.map_size * 100),
                QPointF(arrow_size/2, -self.map_size * 100 + arrow_size)
            ]),
            QPen(QColor("#4ADE80")),
            QBrush(QColor("#4ADE80"))
        )
        # Y-axis label with brighter color
        y_label = self.scene.addText("Y")
        y_label.setDefaultTextColor(QColor("#4ADE80"))
        y_label.setPos(5, -self.map_size * 100 - 25)
        
        # Origin label with white color
        origin_label = self.scene.addText("O")
        origin_label.setDefaultTextColor(Qt.white)
        origin_label.setPos(5, 5)
    
    def save_map(self):
        """Save the current map to a file"""
        # Show file dialog to get save location
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Map",
            "",
            "XML Files (*.xml)"
        )
        
        if file_path:
            # Add .xml extension if not present
            if not file_path.endswith('.xml'):
                file_path += '.xml'
            
            # Create exporter and save map
            exporter = MapExporter(self)
            try:
                exporter.save_map(file_path)
                QMessageBox.information(self, "Success", "Map saved successfully!")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to save map: {str(e)}")
        
    
    def load_map(self):
        """Load a map from a file"""
        # Show file dialog to get load location
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Map",
            "",
            "XML Files (*.xml)"
        )
        
        if file_path:
            # Create loader and load map
            loader = MapLoader(self)
            try:
                # Load the map
                loader.load_map(file_path)
                
                # Update station types list
                self.update_station_types_list()
                
                # Emit map changed signal
                self.map_changed.emit()
                
                QMessageBox.information(self, "Success", "Map loaded successfully!")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to load map: {str(e)}")
    
    def load_station_mesh(self):
        """Load an STL mesh file for the selected station"""
        selected_items = self.scene.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Error", "Please select a station")
            return
        
        station = selected_items[0]
        if not isinstance(station, QStation):
            return
        
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Load STL Mesh",
            "",
            "STL Files (*.stl)"
        )
        
        if file_name:
            station.set_mesh_path(file_name)
            self.station_modified.emit(station)
    
    def show_stations_table(self):
        """Show a table of all stations with delete functionality"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Stations Table")
        dialog.setModal(True)
        
        layout = QVBoxLayout(dialog)
        
        # Create table
        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["Name", "Type", "X", "Y", "Delete"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        # Get all stations from resources holder
        qstations = self.qclass_holder.get_all_qstations()
        table.setRowCount(len(qstations))
        
        for i, qstation in enumerate(qstations):
            # Name
            name_item = QTableWidgetItem(qstation.name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            table.setItem(i, 0, name_item)
            
            # Type
            type_item = QTableWidgetItem(qstation.station_type.name)
            type_item.setFlags(type_item.flags() & ~Qt.ItemIsEditable)
            table.setItem(i, 1, type_item)
            
            # Position X
            x_item = QTableWidgetItem(f"{qstation.position[0]:.2f}")
            x_item.setFlags(x_item.flags() & ~Qt.ItemIsEditable)
            table.setItem(i, 2, x_item)
            
            # Position Y
            y_item = QTableWidgetItem(f"{qstation.position[1]:.2f}")
            y_item.setFlags(y_item.flags() & ~Qt.ItemIsEditable)
            table.setItem(i, 3, y_item)
            
            # Delete button
            delete_btn = QPushButton("Delete")
            delete_btn.clicked.connect(lambda checked, s=qstation: self.delete_station(s, dialog))
            table.setCellWidget(i, 4, delete_btn)
        
        layout.addWidget(table)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.exec_()
    
    def delete_station(self, station, dialog:QDialog):
        """Delete a station after confirmation"""
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete station '{station.name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # Get the UI object before deletion
                qstation = self.qclass_holder.get_qstation_by_id(station.id)
                # Remove from resources holder
                self.class_holder.delete_station(station.id)
                self.qclass_holder.delete_qstation(station.id)
                # Remove from scene
                if qstation:
                    self.scene.removeItem(qstation)
                    self.station_removed.emit(qstation)
                self.map_changed.emit()
                # Refresh the stations table
                dialog.close()
                self.show_stations_table()
            except ValueError as e:
                QMessageBox.warning(self, "Error", str(e))
    
    def add_path_node_by_position(self):
        """Add a path node by entering its position"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Path Node")
        dialog.setModal(True)
        
        layout = QFormLayout(dialog)
        
        # Position inputs
        x_input = QDoubleSpinBox()
        x_input.setRange(-500, 500)
        x_input.setDecimals(2)
        
        y_input = QDoubleSpinBox()
        y_input.setRange(-500, 500)
        y_input.setDecimals(2)
        
        # Add direction input
        direction_input = QDoubleSpinBox()
        direction_input.setRange(0, 359.99)
        direction_input.setDecimals(2)
        direction_input.setSuffix("°")
        direction_input.setSingleStep(15.0)

        # add name input
        name_input = QLineEdit()
        name_input.setPlaceholderText("Enter node name")
        
        layout.addRow("Name:", name_input)
        layout.addRow("X Position:", x_input)
        layout.addRow("Y Position:", y_input)
        layout.addRow("Direction:", direction_input)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)
        
        if dialog.exec_() == QDialog.Accepted:
            # Create backend PathNode first
            node = PathNode(x_input.value(), y_input.value(), direction=direction_input.value(), name=name_input.text())
            try:
                # Add to resources holder and get UI object
                node = self.class_holder.add_path_node(node)
                qnode = self.qclass_holder.add_qpath_node(node)
                # Add to scene
                self.scene.addItem(qnode)
                self.map_changed.emit()
            except ValueError as e:
                QMessageBox.warning(self, "Error", str(e))
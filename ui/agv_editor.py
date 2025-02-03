from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QFormLayout, QDoubleSpinBox, QLabel, QMessageBox,
    QDialog, QLineEdit, QDialogButtonBox
)
from components.agv import QAGV, AGV, AGVStatus
from components.qclass_holder import QClassHolder
from components.path import QPathNode
class NewAGVDialog(QDialog):
    """Dialog for creating a new AGV"""
    def __init__(self, qclass_holder: QClassHolder = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New AGV")
        self.setup_ui()
        self.qclass_holder = qclass_holder
        self.class_holder = qclass_holder.class_holder
    
    def setup_ui(self):
        # Create layout
        layout = QFormLayout(self)
        
        # Add input fields
        self.name_edit = QLineEdit()
        self.name_edit.setText(f"test")
        self.width_spin = QDoubleSpinBox()
        self.length_spin = QDoubleSpinBox()
        self.height_spin = QDoubleSpinBox()
        self.direction_spin = QDoubleSpinBox()  # Add direction spinbox
        
        # Configure size inputs
        for spin in [self.width_spin, self.length_spin, self.height_spin]:
            spin.setRange(0.1, 5.0)  # 0.1m to 5m
            spin.setDecimals(3)
            spin.setValue(1.0)
            spin.setSingleStep(0.1)
        self.width_spin.setValue(0.5)
        self.height_spin.setValue(0.5)
        
        # Configure direction input
        self.direction_spin.setRange(0, 359.99)  # 0-360 degrees
        self.direction_spin.setDecimals(2)
        self.direction_spin.setValue(0.0)
        self.direction_spin.setSingleStep(15.0)  # 15 degree steps for convenience
        self.direction_spin.setSuffix("°")  # Add degree symbol
        
        # Add fields to layout
        layout.addRow("Name:", self.name_edit)
        layout.addRow("Width (m):", self.width_spin)
        layout.addRow("Length (m):", self.length_spin)
        layout.addRow("Height (m):", self.height_spin)
        layout.addRow("Direction:", self.direction_spin)
        
        # Add buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
    
    def get_agv_data(self) -> dict:
        """Get the AGV data from the dialog"""
        return {
            'name': self.name_edit.text(),
            'size': [
                self.width_spin.value(),
                self.length_spin.value(),
                self.height_spin.value()
            ],
            'direction': self.direction_spin.value()  # Add direction to returned data
        }

class AGVEditor(QWidget):
    """Widget for AGV editing tools"""
    def __init__(self, qclass_holder: QClassHolder, map_editor):
        super().__init__()
        self.qclass_holder = qclass_holder
        self.class_holder = qclass_holder.class_holder
        self.map_editor = map_editor  # Store reference to map editor
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the AGV editor UI"""
        layout = QVBoxLayout(self)
        
        # Add AGV controls
        controls_layout = QHBoxLayout()
        
        # Add AGV button
        add_btn = QPushButton("Add AGV at Node")
        add_btn.clicked.connect(self.add_agv_at_node)
        controls_layout.addWidget(add_btn)
        
        # Delete AGV button
        delete_btn = QPushButton("Delete AGV")
        delete_btn.clicked.connect(self.delete_agv)
        controls_layout.addWidget(delete_btn)
        
        layout.addLayout(controls_layout)
        
        # Add position display
        pos_layout = QFormLayout()
        self.pos_x_label = QLabel("0.0")
        self.pos_y_label = QLabel("0.0")
        pos_layout.addRow("X Position (m):", self.pos_x_label)
        pos_layout.addRow("Y Position (m):", self.pos_y_label)
        layout.addLayout(pos_layout)
    
    def add_agv_at_node(self):
        """Add a new AGV at the selected node"""
        # Get selected node using map_editor reference
        selected_items = self.map_editor.scene.selectedItems()
        if not selected_items or not isinstance(selected_items[0], QPathNode):
            QMessageBox.warning(self, "Error", "Please select a path node")
            return
        
        # Show AGV creation dialog
        dialog = NewAGVDialog(self.qclass_holder, self)
        if dialog.exec_():
            agv_data = dialog.get_agv_data()
            qnode = selected_items[0]
            pos = qnode.node.position  # Get position from backend node
            
            # Create new backend AGV first
            agv = AGV(
                agv_data['name'],
                pos,
                agv_data['size']
            )
            # Set direction and other properties
            agv.direction = agv_data['direction']  # Set the direction
            agv.set_status(AGVStatus.IDLE)
            
            try:
                # Add to resources holder and get UI object
                agv = self.class_holder.add_agv(agv)
                qagv = self.qclass_holder.add_qagv(agv)
                # Add to scene
                self.map_editor.scene.addItem(qagv)
                # Update position display
                self.update_position_display(qnode.node.position)
                # Emit map changed signal
                self.map_editor.map_changed.emit()
            except ValueError as e:
                QMessageBox.warning(self, "Error", str(e))
    
    def delete_agv(self):
        """Delete the selected AGV"""
        selected_items = self.map_editor.scene.selectedItems()
        if not selected_items or not isinstance(selected_items[0], QAGV):
            QMessageBox.warning(self, "Error", "Please select an AGV")
            return
        
        qagv = selected_items[0]
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete AGV '{qagv.agv.name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # Remove from resources holder
                self.qclass_holder.delete_qagv(qagv.agv.id)
                self.class_holder.delete_agv(qagv.agv.id)
                # Remove from scene
                self.map_editor.scene.removeItem(qagv)
                # Clear position display
                self.update_position_display([0, 0])
                # Emit map changed signal
                self.map_editor.map_changed.emit()
            except ValueError as e:
                QMessageBox.warning(self, "Error", str(e))
    
    def update_position_display(self, pos):
        """Update the position display labels"""
        if isinstance(pos, (list, tuple)):
            self.pos_x_label.setText(f"{pos[0]:.3f}")
            self.pos_y_label.setText(f"{pos[1]:.3f}")
        else:
            self.pos_x_label.setText(f"{pos.x():.3f}")
            self.pos_y_label.setText(f"{pos.y():.3f}") 
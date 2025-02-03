from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QPushButton, QToolBar, QStatusBar
)
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QAction, QIcon

from ui.map_editor import MapEditor
from ui.realtime_view import RealtimeView
from components.qclass_holder import QClassHolder
from components.class_holder import ClassHolder


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Talos AGV System")
        self.setMinimumSize(1200, 800)
        
        # Create resources holders
        self.class_holder = ClassHolder()
        self.qclass_holder = QClassHolder(self.class_holder)
        
        # Initialize UI components
        self._create_central_widget()
        self._create_toolbar()
        self._create_statusbar()
        
        # Set window properties
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QTabWidget::pane {
                border: 1px solid #cccccc;
                background: white;
                border-radius: 5px;
            }
            QTabBar::tab {
                background: #e1e1e1;
                padding: 8px 12px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background: white;
            }
        """)
        
        # Connect signals
        self.map_editor.map_changed.connect(self._update_paths_and_nodes)
        self.map_editor.station_added.connect(self.realtime_view.update_station)
        self.map_editor.station_modified.connect(self.realtime_view.update_station)
        self.map_editor.station_removed.connect(self.realtime_view.remove_station)
        self.map_editor.map_size_changed.connect(self.realtime_view.update_map_size)
    
    def _create_central_widget(self):
        """Create and set up the central widget with tabs"""
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Add Map Editor tab with resources holder
        self.map_editor = MapEditor(self.qclass_holder)
        self.tab_widget.addTab(self.map_editor, "Map Editor")
        
        # Add Real-time View tab with resources holder
        self.realtime_view = RealtimeView(self.qclass_holder)
        self.tab_widget.addTab(self.realtime_view, "Real-time View")
    
    def _create_toolbar(self):
        """Create and set up the toolbar"""
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        
        # Add save action
        save_action = QAction("Save", self)
        save_action.setStatusTip("Save current map")
        save_action.triggered.connect(self._on_save)
        toolbar.addAction(save_action)
        
        # Add load action
        load_action = QAction("Load", self)
        load_action.setStatusTip("Load map from file")
        load_action.triggered.connect(self._on_load)
        toolbar.addAction(load_action)
    
    def _create_statusbar(self):
        """Create and set up the status bar"""
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Ready")
    
    @Slot()
    def _on_save(self):
        """Handle save action"""
        if self.tab_widget.currentWidget() == self.map_editor:
            self.map_editor.save_map()
            self.statusBar.showMessage("Map saved successfully", 3000)
    
    @Slot()
    def _on_load(self):
        """Handle load action"""
        if self.tab_widget.currentWidget() == self.map_editor:
            self.map_editor.load_map()
            self.statusBar.showMessage("Map loaded successfully", 3000)

    @Slot()
    def _update_paths_and_nodes(self):
        """Update paths and nodes in the 3D view"""
        # Force realtime view to update from resources holder
        self.realtime_view.gl_widget.update()
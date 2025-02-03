from PySide6.QtWidgets import QWidget, QVBoxLayout, QProgressDialog
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np
from math import cos, sin, pi
import trimesh
from components.station import QStation
from components.qclass_holder import QClassHolder
from components.agv import AGV

class RealtimeView(QWidget):
    def __init__(self, qclass_holder: QClassHolder):
        super().__init__()
        # Store resources holder reference
        self.qclass_holder = qclass_holder
        self.setup_ui()
        
        # Dictionary to store loaded meshes
        self.station_meshes = {}
        
        # Set up animation timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_positions)
        self.timer.start(50)  # Update every 50ms
    
    def setup_ui(self):
        """Set up the user interface"""
        layout = QVBoxLayout(self)
        self.gl_widget = GLWidget(self.qclass_holder)
        layout.addWidget(self.gl_widget)
    
    def update_positions(self):
        """Update AGV positions from resources holder"""
        # Update the GL widget
        self.gl_widget.update()
    
    def update_station(self, qstation: QStation):
        """Update a station in the 3D view"""
        # Load mesh if available
        if qstation.station.size.mesh_path:
            try:
                progress = QProgressDialog("Loading mesh...", None, 0, 100, self)
                progress.setWindowModality(Qt.WindowModal)
                progress.show()
                
                # Load the mesh using trimesh
                mesh = trimesh.load(qstation.station.size.mesh_path)
                vertices = mesh.vertices
                faces = mesh.faces
                
                # Store the mesh data
                self.station_meshes[qstation.station.name] = {
                    'vertices': vertices,
                    'faces': faces
                }
                
                progress.close()
            except Exception as e:
                print(f"Error loading mesh: {e}")
        
        # Force update
        self.gl_widget.update()

    def remove_station(self, qstation: QStation):
        """Remove a station's mesh data"""
        station_name = qstation.station.name
        # Remove station mesh if it exists
        if station_name in self.station_meshes:
            del self.station_meshes[station_name]
        
        # Force update
        self.gl_widget.update()

    def update_map_size(self, new_size):
        """Update the map size in the 3D view"""
        self.gl_widget.update_map_size(new_size)

class GLWidget(QOpenGLWidget):
    def __init__(self, qclass_holder: QClassHolder):
        super().__init__()
        self.qclass_holder = qclass_holder
        self.last_pos = None
        
        # Set initial camera position for better view
        self.camera_rotation = [45, 45, 0]  # 45-degree tilt and 45-degree orbit
        self.camera_distance = 15  # Start a bit further back
        self.camera_position = [-5, -5, 5]  # Offset camera position for better initial view
        
        # Initialize transformation matrices
        self.model_matrix = np.identity(4, dtype=np.float32)
        self.view_matrix = np.identity(4, dtype=np.float32)
        self.projection_matrix = np.identity(4, dtype=np.float32)
        
        # Set zoom limits and speed
        self.min_zoom = 2.0  # Minimum zoom distance
        self.max_zoom = 50.0  # Maximum zoom distance
        self.zoom_speed = 1.1  # Zoom speed factor
        self.pan_speed = 0.02  # Pan speed factor
        self.rotation_speed = 0.5  # Rotation speed factor
        
        # Set initial map size
        self.map_size = 10  # Default 10m x 10m grid
    
    def initializeGL(self):
        """Initialize OpenGL settings"""
        glClearColor(0.95, 0.95, 0.95, 1.0)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_COLOR_MATERIAL)
        glEnable(GL_NORMALIZE)
        
        # Set up light
        glLight(GL_LIGHT0, GL_POSITION, (5.0, 5.0, 5.0, 1.0))
        glLightfv(GL_LIGHT0, GL_AMBIENT, (0.2, 0.2, 0.2, 1.0))
        glLightfv(GL_LIGHT0, GL_DIFFUSE, (0.8, 0.8, 0.8, 1.0))
    
    def resizeGL(self, width, height):
        """Handle window resize events"""
        glViewport(0, 0, width, height)
        aspect = width / height
        
        # Update projection matrix using perspective projection
        self.projection_matrix = self._perspective_matrix(45.0, aspect, 0.1, 100.0)
        
    def paintGL(self):
        """Render the scene"""
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        # Update view matrix
        self.view_matrix = self._create_view_matrix()
        
        # Apply view and projection matrices
        glMatrixMode(GL_PROJECTION)
        glLoadMatrixf(self.projection_matrix.T)
        glMatrixMode(GL_MODELVIEW)
        glLoadMatrixf(self.view_matrix.T)
        
        # Draw floor grid
        self._draw_grid()
        
        # Draw stations from resources holder
        qstations = self.qclass_holder.get_all_qstations()
        for qstation in qstations:
            self._draw_station(qstation)
        
        # Draw path nodes from resources holder
        qpath_nodes = self.qclass_holder.get_all_qpath_nodes()
        for qnode in qpath_nodes:
            self._draw_path_node(qnode)
        
        # Draw AGVs from resources holder
        agvs = self.qclass_holder.get_all_qagvs()
        for agv in agvs:
            # Create model matrix for this AGV
            model = np.identity(4, dtype=np.float32)
            pos = agv.position
            
            # Translation matrix
            trans = np.identity(4, dtype=np.float32)
            trans[0:3, 3] = [float(pos[0]), float(pos[1]), 0.1]  # Slightly above ground
            model = np.dot(model, trans)
            
            # Rotation matrix around Z axis
            rot = np.identity(4, dtype=np.float32)
            angle = np.radians(agv.direction)
            rot[0:2, 0:2] = [[np.cos(angle), -np.sin(angle)],
                            [np.sin(angle), np.cos(angle)]]
            model = np.dot(model, rot)
            
            # Apply model-view matrix
            modelview = np.dot(self.view_matrix, model)
            glLoadMatrixf(modelview.T)
            
            # Draw AGV
            self._draw_agv(agv)
    
    def _perspective_matrix(self, fovy, aspect, near, far):
        """Create perspective projection matrix"""
        f = 1.0 / np.tan(np.radians(fovy) / 2.0)
        matrix = np.zeros((4, 4), dtype=np.float32)
        matrix[0, 0] = f / aspect
        matrix[1, 1] = f
        matrix[2, 2] = (far + near) / (near - far)
        matrix[2, 3] = 2.0 * far * near / (near - far)
        matrix[3, 2] = -1.0
        return matrix
    
    def _create_view_matrix(self):
        """Create the view matrix from camera parameters"""
        # Start with identity matrix
        view = np.identity(4, dtype=np.float32)
        
        # Apply transformations in reverse order
        # 1. Translate for camera position (pan)
        trans_matrix = np.identity(4, dtype=np.float32)
        trans_matrix[0:3, 3] = [-self.camera_position[0], 
                               -self.camera_position[1], 
                               -self.camera_position[2]]
        view = np.dot(view, trans_matrix)
        
        # 2. Rotate around X and Y axes
        # X rotation (tilt)
        rot_x = np.identity(4, dtype=np.float32)
        angle_x = np.radians(self.camera_rotation[0])
        rot_x[1:3, 1:3] = [[np.cos(angle_x), -np.sin(angle_x)],
                          [np.sin(angle_x), np.cos(angle_x)]]
        view = np.dot(view, rot_x)
        
        # Y rotation (orbit)
        rot_y = np.identity(4, dtype=np.float32)
        angle_y = np.radians(self.camera_rotation[1])
        rot_y[0::2, 0::2] = [[np.cos(angle_y), np.sin(angle_y)],
                            [-np.sin(angle_y), np.cos(angle_y)]]
        view = np.dot(view, rot_y)
        
        # 3. Translate for zoom (camera distance)
        zoom_matrix = np.identity(4, dtype=np.float32)
        zoom_matrix[2, 3] = -self.camera_distance
        view = np.dot(view, zoom_matrix)
        
        return view
    
    def _draw_station(self, qstation: QStation):
        """Draw a station with its custom size or mesh"""
        # Create model matrix for this station
        model = np.identity(4, dtype=np.float32)
        pos = qstation.station.position
        # Convert scene coordinates to meters
        x = float(pos[0])
        y = float(pos[1])
        
        # Translation matrix for station position
        trans = np.identity(4, dtype=np.float32)
        trans[0:3, 3] = [x, y, 0]  # Map coordinates to x-y plane
        model = np.dot(model, trans)  # Apply translation
        
        # Rotation matrix for direction
        # Add initial -90 degree rotation to align with correct orientation
        initial_angle = np.radians(-90)
        rot_initial = np.identity(4, dtype=np.float32)
        rot_initial[0:2, 0:2] = [[np.cos(initial_angle), -np.sin(initial_angle)],
                                [np.sin(initial_angle), np.cos(initial_angle)]]
        model = np.dot(model, rot_initial)  # Apply initial rotation
        
        # Apply station's direction rotation
        rot = np.identity(4, dtype=np.float32)
        angle = np.radians(qstation.station.direction)
        rot[0:2, 0:2] = [[np.cos(angle), -np.sin(angle)],
                         [np.sin(angle), np.cos(angle)]]
        model = np.dot(model, rot)  # Apply direction rotation
        
        # Apply model-view matrix
        modelview = np.dot(self.view_matrix, model)
        glLoadMatrixf(modelview.T)
        
        # Set station color
        color = QColor(qstation.station.station_type.color)
        glColor3f(color.redF(), color.greenF(), color.blueF())
        
        if qstation.station.name in self.parent().station_meshes:
            # Draw custom mesh if available
            mesh_data = self.parent().station_meshes[qstation.station.name]
            self._draw_mesh(mesh_data['vertices'], mesh_data['faces'])
        else:
            # Draw box with custom size (convert to meters)
            w = qstation.station.size.width
            l = qstation.station.size.length
            h = qstation.station.size.height
            
            # Draw box with proper orientation
            # Note: width along x, length along y, height along z
            self._draw_box(w, h, l)
            
            # Draw direction indicator
            glColor3f(1.0, 0.0, 0.0)  # Red color for direction indicator
            
            # Draw arrow on top of box
            glPushMatrix()  # Save current matrix
            glTranslatef(0, 0, h/2 + 0.001)  # Move to top of box
            
            # Draw arrow
            arrow_length = l * 0.5  # Arrow length proportional to station length
            arrow_width = w * 0.2   # Arrow width proportional to station width
            
            glBegin(GL_TRIANGLES)
            glNormal3f(0, 0, 1)  # Normal pointing up
            # Arrow pointing in positive Y direction (forward)
            glVertex3f(0, 0, 0)          # Base center
            glVertex3f(0, arrow_length, 0)  # Tip
            glVertex3f(arrow_width/2, 0, 0)  # Right point
            
            glVertex3f(0, 0, 0)          # Base center
            glVertex3f(0, arrow_length, 0)  # Tip
            glVertex3f(-arrow_width/2, 0, 0)  # Left point
            glEnd()
            
            glPopMatrix()  # Restore matrix

        # Draw port if it exists
        if qstation.qport:
            # Save current matrix
            glPushMatrix()
            
            # Reset to view matrix for port position
            glLoadMatrixf(self.view_matrix.T)
            
            # Get port position
            port_pos = qstation.qport.node.position
            port_direction = qstation.qport.node.direction
            
            # Create port model matrix
            port_model = np.identity(4, dtype=np.float32)
            
            # Translate to port position
            port_trans = np.identity(4, dtype=np.float32)
            port_trans[0:3, 3] = [float(port_pos[0]), float(port_pos[1]), 0.1]  # Slightly above ground
            port_model = np.dot(port_model, port_trans)
            
            # Rotate for port direction
            port_rot = np.identity(4, dtype=np.float32)
            port_angle = np.radians(port_direction)
            port_rot[0:2, 0:2] = [[np.cos(port_angle), -np.sin(port_angle)],
                                [np.sin(port_angle), np.cos(port_angle)]]
            port_model = np.dot(port_model, port_rot)
            
            # Apply port model-view matrix
            port_modelview = np.dot(self.view_matrix, port_model)
            glLoadMatrixf(port_modelview.T)
            
            # Draw port as a cylinder with arrow
            glColor3f(0.7, 0.7, 0.7)  # Light gray color for port
            self._draw_cylinder(0.1, 0.1)  # radius=0.1m, height=0.1m
            
            # Draw direction arrow on top of cylinder
            glColor3f(0.0, 0.7, 0.0)  # Green color for port arrow
            glTranslatef(0, 0, 0.1+0.01)  # Move to top of cylinder
            
            # Draw arrow
            arrow_length = 0.15  # 15cm
            arrow_width = 0.05   # 5cm
            
            glBegin(GL_TRIANGLES)
            glNormal3f(0, 0, 1)  # Normal pointing up
            # Arrow pointing in positive X direction
            glVertex3f(0, 0, 0)  # Base center
            glVertex3f(arrow_length, 0, 0)  # Tip
            glVertex3f(0, arrow_width/2, 0)  # Right point
            
            glVertex3f(0, 0, 0)  # Base center
            glVertex3f(arrow_length, 0, 0)  # Tip
            glVertex3f(0, -arrow_width/2, 0)  # Left point
            glEnd()
            
            # Restore matrix
            glPopMatrix()
    
    def _draw_box(self, width, height, length):
        """Draw a box with given dimensions in meters
        width: along x-axis
        height: along z-axis
        length: along y-axis
        """
        # Convert dimensions to half-sizes for easier vertex calculations
        w, h, l = width/2, height/2, length/2
        
        # Define vertices in proper orientation
        # Front face is in the direction of positive Y (length)
        vertices = [
            # Front face (y = l)
            [-w, l, -h], [w, l, -h], [w, l, h], [-w, l, h],
            # Back face (y = -l)
            [-w, -l, -h], [w, -l, -h], [w, -l, h], [-w, -l, h],
        ]
        
        # Define faces as quads with proper winding order for correct normals
        faces = [
            # Front and back faces (along Y axis)
            [0, 1, 2, 3], [5, 4, 7, 6],  # Front (y = l), Back (y = -l)
            # Left and right faces (along X axis)
            [4, 0, 3, 7], [1, 5, 6, 2],  # Left (x = -w), Right (x = w)
            # Top and bottom faces (along Z axis)
            [3, 2, 6, 7], [0, 4, 5, 1]   # Top (z = h), Bottom (z = -h)
        ]
        
        # Define normals for each face
        normals = [
            [0, 1, 0], [0, -1, 0],   # Front, Back
            [-1, 0, 0], [1, 0, 0],   # Left, Right
            [0, 0, 1], [0, 0, -1]    # Top, Bottom
        ]
        
        glBegin(GL_QUADS)
        for face_idx, face in enumerate(faces):
            glNormal3fv(normals[face_idx])
            for vertex_idx in face:
                glVertex3fv(vertices[vertex_idx])
        glEnd()
    
    def _draw_mesh(self, vertices, faces):
        """Draw a mesh from vertices and faces"""
        glBegin(GL_TRIANGLES)
        for face in faces:
            # Calculate face normal for proper lighting
            v1, v2, v3 = [vertices[i] for i in face]
            normal = np.cross(v2 - v1, v3 - v1)
            normal = normal / np.linalg.norm(normal)
            glNormal3fv(normal)
            
            # Draw face vertices
            for vertex_idx in face:
                glVertex3fv(vertices[vertex_idx])
        glEnd()
    
    def _draw_grid(self):
        """Draw the floor grid with consistent units"""
        glDisable(GL_LIGHTING)  # Disable lighting for grid
        
        # Draw main grid with current map size
        glColor3f(0.8, 0.8, 0.8)
        glBegin(GL_LINES)
        for i in range(-self.map_size, self.map_size + 1):
            glVertex3f(i, -self.map_size, 0)
            glVertex3f(i, self.map_size, 0)
            glVertex3f(-self.map_size, i, 0)
            glVertex3f(self.map_size, i, 0)
        glEnd()
        
        # Draw coordinate axes
        glBegin(GL_LINES)
        # X axis (red)
        glColor3f(1, 0, 0)
        glVertex3f(0, 0, 0)
        glVertex3f(self.map_size, 0, 0)  # Extend to map size
        # Y axis (green)
        glColor3f(0, 1, 0)
        glVertex3f(0, 0, 0)
        glVertex3f(0, self.map_size, 0)  # Extend to map size
        # Z axis (blue)
        glColor3f(0, 0, 1)
        glVertex3f(0, 0, 1)
        glVertex3f(0, 0, 0)
        glEnd()
        
        glEnable(GL_LIGHTING)  # Re-enable lighting
    
    def _draw_path_node(self, qnode):
        """Draw a path node with consistent units"""
        # Create model matrix for this node
        model = np.identity(4, dtype=np.float32)
        pos = qnode.node.position
        
        # Translation matrix
        trans = np.identity(4, dtype=np.float32)
        trans[0:3, 3] = [float(pos[0]), float(pos[1]), 0.1]  # Slightly above ground
        model = np.dot(model, trans)
        
        # Rotation matrix for direction
        rot = np.identity(4, dtype=np.float32)
        angle = np.radians(qnode.node.direction)
        rot[0:2, 0:2] = [[np.cos(angle), -np.sin(angle)],
                         [np.sin(angle), np.cos(angle)]]
        model = np.dot(model, rot)
        
        # Apply model-view matrix
        modelview = np.dot(self.view_matrix, model)
        glLoadMatrixf(modelview.T)
        
        # Draw cylinder
        glColor3f(0.4, 0.4, 0.4)  # Gray color for cylinder
        self._draw_cylinder(0.1, 0.1)  # radius=0.1m, height=0.1m
        
        # Draw direction arrow on top of cylinder
        glColor3f(1.0, 0.0, 0.0)  # Red color for arrow
        glTranslatef(0, 0, 0.1+0.01)  # Move to top of cylinder
        
        # Draw arrow
        arrow_length = 0.15  # 15cm
        arrow_width = 0.05   # 5cm
        
        glBegin(GL_TRIANGLES)
        # Arrow pointing in positive X direction (will be rotated by node direction)
        glVertex3f(0, 0, 0)  # Base center
        glVertex3f(arrow_length, 0, 0)  # Tip
        glVertex3f(0, arrow_width/2, 0)  # Right point
        
        glVertex3f(0, 0, 0)  # Base center
        glVertex3f(arrow_length, 0, 0)  # Tip
        glVertex3f(0, -arrow_width/2, 0)  # Left point
        glEnd()
    
    def _draw_cylinder(self, radius, height):
        """Draw a cylinder with the specified dimensions in meters"""
        sides = 32
        step = 2 * pi / sides
        
        # Draw sides
        glBegin(GL_QUAD_STRIP)
        for i in range(sides + 1):
            angle = i * step
            x = radius * cos(angle)
            y = radius * sin(angle)
            # Changed normal and vertex coordinates to be in x-y plane
            glNormal3f(x/radius, y/radius, 0)
            glVertex3f(x, y, 0)
            glVertex3f(x, y, height)
        glEnd()
        
        # Draw caps
        for z in (0, height):
            glBegin(GL_TRIANGLE_FAN)
            glNormal3f(0, 0, 1 if z == height else -1)
            glVertex3f(0, 0, z)
            for i in range(sides + 1):
                angle = i * step
                x = radius * cos(angle)
                y = radius * sin(angle)
                glVertex3f(x, y, z)
            glEnd()
    
    def _draw_agv(self, agv: AGV):
        """Draw an AGV with its dimensions and color"""
        # Get AGV dimensions in meters
        width = agv.size[0]
        length = agv.size[1]
        height = agv.size[2]
        
        # Set AGV color based on status
        color = QColor("#4287f5")
        glColor3f(color.redF(), color.greenF(), color.blueF())
        
        # Create model matrix for this AGV
        model = np.identity(4, dtype=np.float32)
        pos = agv.position
        
        # Translation matrix
        trans = np.identity(4, dtype=np.float32)
        trans[0:3, 3] = [float(pos[0]), float(pos[1]), 0.1]  # Slightly above ground
        model = np.dot(model, trans)
        
        # Add initial -90 degree rotation to align with correct orientation
        initial_angle = np.radians(-90)
        rot_initial = np.identity(4, dtype=np.float32)
        rot_initial[0:2, 0:2] = [[np.cos(initial_angle), -np.sin(initial_angle)],
                                [np.sin(initial_angle), np.cos(initial_angle)]]
        model = np.dot(model, rot_initial)  # Apply initial rotation
        
        # Rotation matrix for AGV direction
        rot = np.identity(4, dtype=np.float32)
        angle = np.radians(agv.direction)
        rot[0:2, 0:2] = [[np.cos(angle), -np.sin(angle)],
                         [np.sin(angle), np.cos(angle)]]
        model = np.dot(model, rot)  # Apply direction rotation
        
        # Apply model-view matrix
        modelview = np.dot(self.view_matrix, model)
        glLoadMatrixf(modelview.T)
        
        # Draw AGV body - width along x, length along y, height along z
        self._draw_box(width, height, length)
        
        # Draw direction indicator (arrow)
        glColor3f(1.0, 0.0, 0.0)  # Red color for arrow
        
        glPushMatrix()  # Save current matrix
        glTranslatef(0, 0, height/2+0.001)  # Move to top of AGV
        
        # Draw arrow proportional to AGV size
        arrow_length = length * 0.5  # Arrow length proportional to AGV length
        arrow_width = width * 0.2   # Arrow width proportional to AGV width
        
        glBegin(GL_TRIANGLES)
        glNormal3f(0, 0, 1)  # Normal pointing up
        # Arrow pointing in positive Y direction (forward)
        glVertex3f(0, 0, 0)          # Base center
        glVertex3f(0, arrow_length, 0)  # Tip
        glVertex3f(arrow_width/2, 0, 0)  # Right point
        
        glVertex3f(0, 0, 0)          # Base center
        glVertex3f(0, arrow_length, 0)  # Tip
        glVertex3f(-arrow_width/2, 0, 0)  # Left point
        glEnd()
        
        glPopMatrix()  # Restore matrix
    
    def _screen_to_world(self, screen_x, screen_y):
        """Convert screen coordinates to world coordinates"""
        # Normalized device coordinates
        x = (2.0 * screen_x / self.width()) - 1.0
        y = 1.0 - (2.0 * screen_y / self.height())
            
        # Create combined view-projection matrix
        vp_matrix = np.dot(self.projection_matrix, self.view_matrix)
        vp_inverse = np.linalg.inv(vp_matrix)
            
        # Create ray in homogeneous coordinates
        ray_clip = np.array([x, y, -1.0, 1.0], dtype=np.float32)
        ray_world = np.dot(vp_inverse, ray_clip)
            
        # Convert to 3D point
        if ray_world[3] != 0:
            ray_world = ray_world / ray_world[3]
            
        # Project point onto the plane (z=0)
        if ray_world[2] != 0:
            t = -ray_world[2]  # Intersection parameter with z=0 plane
            ray_world = ray_world + t * ray_world  # Project to plane
            
        return ray_world[:3]

    def mousePressEvent(self, event):
        """Handle mouse press events"""
        self.last_pos = event.pos()
        if event.button() == Qt.MiddleButton:
            # Store initial pan position
            self.pan_start_pos = self._screen_to_world(event.pos().x(), event.pos().y())

    def wheelEvent(self, event):
        """Handle mouse wheel events for zooming while keeping the screen center point unchanged on the plane."""
        # Determine the zoom direction based on wheel movement
        zoom_in = event.angleDelta().y() > 0
        zoom_factor = self.zoom_speed if zoom_in else 1.0 / self.zoom_speed

        # Calculate the new camera distance with limits
        new_distance = self.camera_distance / zoom_factor
        if self.min_zoom <= new_distance <= self.max_zoom:
            # Get world position of screen center before zoom
            world_pos_before = self._screen_to_world(self.width() / 2, self.height() / 2)
            
            # Apply zoom by updating camera distance
            self.camera_distance = new_distance
            
            # Get world position of screen center after zoom
            world_pos_after = self._screen_to_world(self.width() / 2, self.height() / 2)
            
            # Adjust camera position to keep the screen center point unchanged
            self.camera_position[0] += (world_pos_before[0] - world_pos_after[0])
            self.camera_position[1] += (world_pos_before[1] - world_pos_after[1])
            self.camera_position[2] += (world_pos_before[2] - world_pos_after[2])
            
            # Update the view to reflect changes
            self.update()

    def mousePressEvent(self, event):
        """Handle mouse press events for initiating rotation or panning."""
        self.last_pos = event.pos()
        if event.button() == Qt.MiddleButton:
            # Store the initial pan position when middle button is pressed
            self.pan_start_pos = self._screen_to_world(event.pos().x(), event.pos().y())

    def mouseMoveEvent(self, event):
        """Handle mouse move events for rotating the view or translating the plane."""
        if self.last_pos is None:
            return

        # Calculate the difference in mouse movement
        dx = event.x() - self.last_pos.x()
        dy = event.y() - self.last_pos.y()

        if event.buttons() & Qt.LeftButton:
            # Handle rotation while keeping the central point unchanged

            # Get world position before rotation
            center_before = self._screen_to_world(self.width() / 2, self.height() / 2)
            
            # Update camera rotation based on mouse movement
            self.camera_rotation[0] += dy * self.rotation_speed  # Tilt around X axis
            self.camera_rotation[1] += dx * self.rotation_speed  # Orbit around Y axis

            # Clamp the tilt angle to prevent flipping
            self.camera_rotation[0] = max(-89, min(89, self.camera_rotation[0]))

            # Get world position after rotation
            center_after = self._screen_to_world(self.width() / 2, self.height() / 2)

            # Adjust camera position to keep the central point unchanged
            self.camera_position[0] += (center_before[0] - center_after[0])
            self.camera_position[1] += (center_before[1] - center_after[1])
            self.camera_position[2] += (center_before[2] - center_after[2])

            # Update the view to reflect changes
            self.update()

        elif event.buttons() & Qt.MiddleButton:
            # Handle panning by translating the camera position

            # Get world positions for the previous and current mouse positions
            pos_before = self._screen_to_world(self.last_pos.x(), self.last_pos.y())
            pos_after = self._screen_to_world(event.pos().x(), event.pos().y())

            # Calculate the translation delta in world space
            delta_x = pos_after[0] - pos_before[0]
            delta_y = pos_after[1] - pos_before[1]

            # Apply the translation to the camera position
            self.camera_position[0] -= delta_x
            self.camera_position[1] -= delta_y

            # Update the view to reflect changes
            self.update()

        # Update the last known mouse position
        self.last_pos = event.pos()

    def mouseReleaseEvent(self, event):
        """Handle mouse release events to reset the last mouse position."""
        self.last_pos = None
        if event.button() == Qt.MiddleButton:
            # Reset the pan start position when middle button is released
            self.pan_start_pos = None

        def update_map_size(self, new_size):
            """Update the map size and redraw"""
            self.map_size = new_size
            self.update()  # Force redraw
 #!/usr/bin/env python3
# Main entry point for the QAGV dispatching system

import sys
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow


def main():
    # Create the Qt Application
    app = QApplication(sys.argv)
    
    # Create and show the main window
    window = MainWindow()
    window.show()
    
    # Start the event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
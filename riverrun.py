import sys
import os
import sqlite3
import json
import shutil
import webbrowser
import platform
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTabWidget, QTableWidget, QTableWidgetItem, QFormLayout, QLineEdit, 
    QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox, QPushButton, QLabel,
    QFileDialog, QMessageBox, QDialog, QDialogButtonBox, QGroupBox,
    QListWidget, QListWidgetItem, QSplitter, QScrollArea, QFrame,
    QGridLayout, QDateEdit, QCheckBox, QProgressBar, QMenuBar, QMenu,
    QStatusBar, QToolBar, QHeaderView, QTreeWidget, QTreeWidgetItem,
    QInputDialog
)
from PyQt6.QtCore import Qt, QDate, QTimer, pyqtSignal, QThread, QSize, QSettings
from PyQt6.QtGui import QPixmap, QIcon, QAction, QFont, QPalette, QColor

def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

def get_icon_path():
    """Get the path to the icon file, works for both development and PyInstaller"""
    # Try different possible locations for the icon
    possible_paths = [
        get_resource_path("rr_icon.ico"),  # Bundled with PyInstaller
        "rr_icon.ico",  # Current directory (development)
        os.path.join(os.path.dirname(__file__), "rr_icon.ico"),  # Same directory as script
        os.path.join(os.path.dirname(sys.executable), "rr_icon.ico"),  # Same directory as executable
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    return None

def get_app_data_dir():
    """Get the OS-specific application data directory"""
    app_name = "RiverRunner"
    
    system = platform.system()
    
    if system == "Windows":
        # Windows: %APPDATA%\RiverRunner
        base_dir = os.environ.get('APPDATA', '')
        if not base_dir:
            # Fallback to user profile
            base_dir = os.path.expanduser('~\\AppData\\Roaming')
    elif system == "Darwin":  # macOS
        # macOS: ~/Library/Application Support/RiverRunner
        base_dir = os.path.expanduser('~/Library/Application Support')
    else:  # Linux and other Unix-like systems
        # Linux: ~/.local/share/RiverRunner
        base_dir = os.environ.get('XDG_DATA_HOME', os.path.expanduser('~/.local/share'))
    
    app_dir = os.path.join(base_dir, app_name)
    
    # Create the directory if it doesn't exist
    os.makedirs(app_dir, exist_ok=True)
    
    return app_dir

def migrate_old_data():
    """Migrate data from current directory to app data directory if needed"""
    app_dir = get_app_data_dir()
    current_dir = os.getcwd()
    
    old_db_path = os.path.join(current_dir, "river_data.db")
    new_db_path = os.path.join(app_dir, "river_data.db")
    
    old_attachments_dir = os.path.join(current_dir, "attachments")
    new_attachments_dir = os.path.join(app_dir, "attachments")
    
    migrated = False
    
    # Migrate database file
    if os.path.exists(old_db_path) and not os.path.exists(new_db_path):
        try:
            shutil.copy2(old_db_path, new_db_path)
            print(f"Migrated database from {old_db_path} to {new_db_path}")
            migrated = True
        except Exception as e:
            print(f"Failed to migrate database: {e}")
    
    # Migrate attachments directory
    if os.path.exists(old_attachments_dir) and not os.path.exists(new_attachments_dir):
        try:
            shutil.copytree(old_attachments_dir, new_attachments_dir)
            print(f"Migrated attachments from {old_attachments_dir} to {new_attachments_dir}")
            migrated = True
        except Exception as e:
            print(f"Failed to migrate attachments: {e}")
    
    return migrated

def get_difficulty_color(difficulty):
    """Get the color for a difficulty class"""
    if difficulty in ['Class I', 'Class II']:
        return QColor('green')
    elif difficulty == 'Class III':
        return QColor('orange')
    elif difficulty in ['Class IV', 'Class V']:
        return QColor('red')
    elif difficulty == 'Class VI':
        return QColor('#C71585')  # Pinkish purple
    else:
        return None  # Use default color

class DatabaseManager:
    """Handles all database operations for the River Runner application"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            # Use app data directory for database
            app_dir = get_app_data_dir()
            db_path = os.path.join(app_dir, "river_data.db")
        
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with all required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Rivers table - main table for river information
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rivers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                location TEXT NOT NULL,
                region TEXT,
                latitude REAL,
                longitude REAL,
                difficulty_class TEXT,
                length_miles REAL,
                typical_flow_min INTEGER,
                typical_flow_max INTEGER,
                put_in_location TEXT,
                take_out_location TEXT,
                shuttle_info TEXT,
                parking_details TEXT,
                best_seasons TEXT,
                water_level_source TEXT,
                hazards TEXT,
                portages TEXT,
                emergency_contacts TEXT,
                description TEXT,
                personal_rating INTEGER,
                date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT,
                tags TEXT
            )
        ''')
        
        # Documents/Files table for attachments
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS river_documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                river_id INTEGER,
                file_name TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_type TEXT NOT NULL,
                file_size INTEGER,
                description TEXT,
                upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (river_id) REFERENCES rivers (id) ON DELETE CASCADE
            )
        ''')
        
        # Trip logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trip_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                river_id INTEGER,
                trip_date DATE NOT NULL,
                companions TEXT,
                water_level TEXT,
                weather_conditions TEXT,
                flow_rate INTEGER,
                duration_hours REAL,
                difficulty_experienced TEXT,
                highlights TEXT,
                challenges TEXT,
                gear_used TEXT,
                trip_rating INTEGER,
                notes TEXT,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (river_id) REFERENCES rivers (id) ON DELETE CASCADE
            )
        ''')
        
        # Tags/Categories table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS river_tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                river_id INTEGER,
                tag TEXT NOT NULL,
                FOREIGN KEY (river_id) REFERENCES rivers (id) ON DELETE CASCADE
            )
        ''')
        
        # Handle database migration - add tags column if it doesn't exist
        try:
            cursor.execute("ALTER TABLE rivers ADD COLUMN tags TEXT")
            conn.commit()
        except sqlite3.OperationalError:
            # Column already exists, ignore the error
            pass
        
        conn.commit()
        conn.close()
    
    def add_river(self, river_data: Dict) -> int:
        """Add a new river to the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO rivers (
                name, location, region, latitude, longitude, difficulty_class,
                length_miles, typical_flow_min, typical_flow_max, put_in_location,
                take_out_location, shuttle_info, parking_details, best_seasons,
                water_level_source, hazards, portages, emergency_contacts,
                description, personal_rating, notes, tags
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            river_data.get('name', ''),
            river_data.get('location', ''),
            river_data.get('region', ''),
            river_data.get('latitude'),
            river_data.get('longitude'),
            river_data.get('difficulty_class', ''),
            river_data.get('length_miles'),
            river_data.get('typical_flow_min'),
            river_data.get('typical_flow_max'),
            river_data.get('put_in_location', ''),
            river_data.get('take_out_location', ''),
            river_data.get('shuttle_info', ''),
            river_data.get('parking_details', ''),
            river_data.get('best_seasons', ''),
            river_data.get('water_level_source', ''),
            river_data.get('hazards', ''),
            river_data.get('portages', ''),
            river_data.get('emergency_contacts', ''),
            river_data.get('description', ''),
            river_data.get('personal_rating'),
            river_data.get('notes', ''),
            river_data.get('tags', '')
        ))
        
        river_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return river_id
    
    def get_all_rivers(self) -> List[Dict]:
        """Get all rivers from the database"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM rivers ORDER BY name')
        rivers = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        return rivers
    
    def get_river_by_id(self, river_id: int) -> Optional[Dict]:
        """Get a specific river by ID"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM rivers WHERE id = ?', (river_id,))
        row = cursor.fetchone()
        
        conn.close()
        return dict(row) if row else None
    
    def update_river(self, river_id: int, river_data: Dict):
        """Update an existing river"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE rivers SET
                name=?, location=?, region=?, latitude=?, longitude=?, difficulty_class=?,
                length_miles=?, typical_flow_min=?, typical_flow_max=?, put_in_location=?,
                take_out_location=?, shuttle_info=?, parking_details=?, best_seasons=?,
                water_level_source=?, hazards=?, portages=?, emergency_contacts=?,
                description=?, personal_rating=?, notes=?, tags=?, last_updated=CURRENT_TIMESTAMP
            WHERE id=?
        ''', (
            river_data.get('name', ''),
            river_data.get('location', ''),
            river_data.get('region', ''),
            river_data.get('latitude'),
            river_data.get('longitude'),
            river_data.get('difficulty_class', ''),
            river_data.get('length_miles'),
            river_data.get('typical_flow_min'),
            river_data.get('typical_flow_max'),
            river_data.get('put_in_location', ''),
            river_data.get('take_out_location', ''),
            river_data.get('shuttle_info', ''),
            river_data.get('parking_details', ''),
            river_data.get('best_seasons', ''),
            river_data.get('water_level_source', ''),
            river_data.get('hazards', ''),
            river_data.get('portages', ''),
            river_data.get('emergency_contacts', ''),
            river_data.get('description', ''),
            river_data.get('personal_rating'),
            river_data.get('notes', ''),
            river_data.get('tags', ''),
            river_id
        ))
        
        conn.commit()
        conn.close()
    
    def delete_river(self, river_id: int):
        """Delete a river and all associated data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM rivers WHERE id = ?', (river_id,))
        
        conn.commit()
        conn.close()
    
    def add_document(self, river_id: int, file_path: str, description: str = ""):
        """Add a document attachment to a river"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        file_name = os.path.basename(file_path)
        file_type = os.path.splitext(file_name)[1].lower()
        file_size = os.path.getsize(file_path)
        
        cursor.execute('''
            INSERT INTO river_documents (river_id, file_name, file_path, file_type, file_size, description)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (river_id, file_name, file_path, file_type, file_size, description))
        
        conn.commit()
        conn.close()
    
    def get_river_documents(self, river_id: int) -> List[Dict]:
        """Get all documents for a specific river"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM river_documents WHERE river_id = ?', (river_id,))
        documents = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        return documents
    
    def add_trip_log(self, trip_data: Dict) -> int:
        """Add a new trip log"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO trip_logs (
                river_id, trip_date, companions, water_level, weather_conditions,
                flow_rate, duration_hours, difficulty_experienced, highlights,
                challenges, gear_used, trip_rating, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            trip_data.get('river_id'),
            trip_data.get('trip_date'),
            trip_data.get('companions', ''),
            trip_data.get('water_level', ''),
            trip_data.get('weather_conditions', ''),
            trip_data.get('flow_rate'),
            trip_data.get('duration_hours'),
            trip_data.get('difficulty_experienced', ''),
            trip_data.get('highlights', ''),
            trip_data.get('challenges', ''),
            trip_data.get('gear_used', ''),
            trip_data.get('trip_rating'),
            trip_data.get('notes', '')
        ))
        
        trip_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return trip_id
    
    def get_trip_log_by_id(self, trip_id: int) -> Optional[Dict]:
        """Get a specific trip log by ID"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT t.*, r.name as river_name 
            FROM trip_logs t 
            JOIN rivers r ON t.river_id = r.id 
            WHERE t.id = ?
        ''', (trip_id,))
        row = cursor.fetchone()
        
        conn.close()
        return dict(row) if row else None
    
    def update_trip_log(self, trip_id: int, trip_data: Dict):
        """Update an existing trip log"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE trip_logs SET
                river_id=?, trip_date=?, companions=?, water_level=?, weather_conditions=?,
                flow_rate=?, duration_hours=?, difficulty_experienced=?, highlights=?,
                challenges=?, gear_used=?, trip_rating=?, notes=?
            WHERE id=?
        ''', (
            trip_data.get('river_id'),
            trip_data.get('trip_date'),
            trip_data.get('companions', ''),
            trip_data.get('water_level', ''),
            trip_data.get('weather_conditions', ''),
            trip_data.get('flow_rate'),
            trip_data.get('duration_hours'),
            trip_data.get('difficulty_experienced', ''),
            trip_data.get('highlights', ''),
            trip_data.get('challenges', ''),
            trip_data.get('gear_used', ''),
            trip_data.get('trip_rating'),
            trip_data.get('notes', ''),
            trip_id
        ))
        
        conn.commit()
        conn.close()
    
    def delete_trip_log(self, trip_id: int):
        """Delete a trip log"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM trip_logs WHERE id = ?', (trip_id,))
        
        conn.commit()
        conn.close()

    def get_trip_logs(self, river_id: int = None) -> List[Dict]:
        """Get trip logs, optionally filtered by river"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if river_id:
            cursor.execute('''
                SELECT t.*, r.name as river_name 
                FROM trip_logs t 
                JOIN rivers r ON t.river_id = r.id 
                WHERE t.river_id = ? 
                ORDER BY t.trip_date DESC
            ''', (river_id,))
        else:
            cursor.execute('''
                SELECT t.*, r.name as river_name 
                FROM trip_logs t 
                JOIN rivers r ON t.river_id = r.id 
                ORDER BY t.trip_date DESC
            ''')
        
        trips = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return trips


class RiverFormDialog(QDialog):
    """Dialog for adding/editing river information"""
    
    def __init__(self, parent=None, river_data=None):
        super().__init__(parent)
        self.river_data = river_data
        self.setup_ui()
        if river_data:
            self.populate_form(river_data)
        
        # Set icon for dialog
        self.set_dialog_icon()
    
    def set_dialog_icon(self):
        """Set the icon for this dialog"""
        icon_path = get_icon_path()
        if icon_path and os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
    
    def setup_ui(self):
        self.setWindowTitle("Add River" if not self.river_data else "Edit River")
        self.setModal(True)
        self.resize(1000, 750)  # Reduced height to eliminate dead space in Additional Information section
        
        layout = QVBoxLayout(self)
        
        # Create main content widget and layout
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        
        # Create a grid layout for the top groups (2 columns)
        top_layout = QGridLayout()
        
        # River Information Group (Column 1, Row 1)
        basic_group = QGroupBox("River Information")
        basic_layout = QFormLayout(basic_group)
        
        self.name_edit = QLineEdit()
        self.location_edit = QLineEdit()
        self.region_edit = QLineEdit()
        self.latitude_edit = QDoubleSpinBox()
        self.latitude_edit.setRange(-90, 90)
        self.latitude_edit.setDecimals(6)
        self.longitude_edit = QDoubleSpinBox()
        self.longitude_edit.setRange(-180, 180)
        self.longitude_edit.setDecimals(6)
        
        basic_layout.addRow(QLabel("Name<span style='color: red;'>*</span>:"), self.name_edit)
        basic_layout.addRow(QLabel("Location<span style='color: red;'>*</span>:"), self.location_edit)
        basic_layout.addRow("Region:", self.region_edit)
        basic_layout.addRow("Latitude:", self.latitude_edit)
        basic_layout.addRow("Longitude:", self.longitude_edit)
        
        # Whitewater Details Group (Column 2, Row 1)
        whitewater_group = QGroupBox("Whitewater Details")
        whitewater_layout = QFormLayout(whitewater_group)
        
        self.difficulty_combo = QComboBox()
        self.difficulty_combo.addItems(["", "Class I", "Class II", "Class III", "Class IV", "Class V", "Class VI"])
        self.length_edit = QDoubleSpinBox()
        self.length_edit.setRange(0, 999)
        self.length_edit.setDecimals(1)
        self.length_edit.setSuffix(" miles")
        
        self.flow_min_edit = QSpinBox()
        self.flow_min_edit.setRange(0, 50000)
        self.flow_min_edit.setSuffix(" cfs")
        self.flow_max_edit = QSpinBox()
        self.flow_max_edit.setRange(0, 50000)
        self.flow_max_edit.setSuffix(" cfs")
        
        self.rating_combo = QComboBox()
        self.rating_combo.addItems(["", "1 - Poor", "2 - Fair", "3 - Good", "4 - Very Good", "5 - Excellent"])
        
        whitewater_layout.addRow("Difficulty Class:", self.difficulty_combo)
        whitewater_layout.addRow("Length:", self.length_edit)
        whitewater_layout.addRow("Min Flow Rate:", self.flow_min_edit)
        whitewater_layout.addRow("Max Flow Rate:", self.flow_max_edit)
        whitewater_layout.addRow("Personal Rating:", self.rating_combo)
        
        # Access Information Group (Column 1, Row 2)
        access_group = QGroupBox("Access Information")
        access_layout = QFormLayout(access_group)
        
        self.put_in_edit = QLineEdit()
        self.take_out_edit = QLineEdit()
        self.shuttle_edit = QTextEdit()
        self.shuttle_edit.setMaximumHeight(50)
        self.parking_edit = QTextEdit()
        self.parking_edit.setMaximumHeight(50)
        
        access_layout.addRow("Put-in Location:", self.put_in_edit)
        access_layout.addRow("Take-out Location:", self.take_out_edit)
        access_layout.addRow("Shuttle Info:", self.shuttle_edit)
        access_layout.addRow("Parking Details:", self.parking_edit)
        
        # Conditions & Safety Group (Column 2, Row 2)
        conditions_group = QGroupBox("Conditions & Safety")
        conditions_layout = QFormLayout(conditions_group)
        
        self.seasons_edit = QLineEdit()
        self.water_source_edit = QLineEdit()
        self.hazards_edit = QTextEdit()
        self.hazards_edit.setMaximumHeight(50)
        self.portages_edit = QTextEdit()
        self.portages_edit.setMaximumHeight(50)
        self.emergency_edit = QTextEdit()
        self.emergency_edit.setMaximumHeight(50)
        
        conditions_layout.addRow("Best Seasons:", self.seasons_edit)
        conditions_layout.addRow("Water Level Source:", self.water_source_edit)
        conditions_layout.addRow("Hazards:", self.hazards_edit)
        conditions_layout.addRow("Portages:", self.portages_edit)
        conditions_layout.addRow("Emergency Contacts:", self.emergency_edit)
        
        # Add groups to grid layout (2 columns)
        top_layout.addWidget(basic_group, 0, 0)
        top_layout.addWidget(whitewater_group, 0, 1)
        top_layout.addWidget(access_group, 1, 0)
        top_layout.addWidget(conditions_group, 1, 1)
        
        # Set column stretch to make columns equal width
        top_layout.setColumnStretch(0, 1)
        top_layout.setColumnStretch(1, 1)
        
        # Add the grid layout to the content layout
        content_layout.addLayout(top_layout)
        
        # Additional Information Group (spans both columns at bottom)
        desc_group = QGroupBox("Additional Information")
        desc_layout = QVBoxLayout(desc_group)
        
        # Create a horizontal layout for the text areas
        text_areas_layout = QHBoxLayout()
        
        # Left side - Description
        desc_left_layout = QVBoxLayout()
        desc_left_layout.setSpacing(2)  # Reduce spacing between label and text area
        desc_label = QLabel("River Description:")
        desc_label.setMaximumHeight(20)  # Limit label height
        desc_left_layout.addWidget(desc_label)
        self.description_edit = QTextEdit()
        self.description_edit.setMinimumHeight(100)
        self.description_edit.setMaximumHeight(100)
        self.description_edit.setPlaceholderText("Describe the river's character, notable rapids, scenery, and overall experience...")
        desc_left_layout.addWidget(self.description_edit)
        
        # Right side - Personal Notes
        notes_right_layout = QVBoxLayout()
        notes_right_layout.setSpacing(2)  # Reduce spacing between label and text area
        notes_label = QLabel("Personal Notes & Tips:")
        notes_label.setMaximumHeight(20)  # Limit label height
        notes_right_layout.addWidget(notes_label)
        self.notes_edit = QTextEdit()
        self.notes_edit.setMinimumHeight(100)
        self.notes_edit.setMaximumHeight(100)
        self.notes_edit.setPlaceholderText("Your personal observations, tips for future trips, gear recommendations, local contacts...")
        notes_right_layout.addWidget(self.notes_edit)
        
        # Add both sides to horizontal layout
        text_areas_layout.addLayout(desc_left_layout)
        text_areas_layout.addLayout(notes_right_layout)
        
        desc_layout.addLayout(text_areas_layout)
        
        # Add tags/keywords field at bottom
        tags_layout = QHBoxLayout()
        tags_layout.addWidget(QLabel("Tags/Keywords:"))
        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText("e.g., scenic, technical, family-friendly, wilderness, day-trip...")
        tags_layout.addWidget(self.tags_edit)
        
        desc_layout.addLayout(tags_layout)
        
        # Add Additional Information group at bottom spanning both columns
        content_layout.addWidget(desc_group)
        
        layout.addWidget(content_widget)
        
        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel)
        
        # Add custom Save button
        save_button = button_box.addButton("Save", QDialogButtonBox.ButtonRole.AcceptRole)
        save_button.setDefault(True)  # Make Save the default button
        
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def populate_form(self, river_data):
        """Populate form with existing river data"""
        self.name_edit.setText(river_data.get('name', ''))
        self.location_edit.setText(river_data.get('location', ''))
        self.region_edit.setText(river_data.get('region', ''))
        
        if river_data.get('latitude'):
            self.latitude_edit.setValue(river_data['latitude'])
        if river_data.get('longitude'):
            self.longitude_edit.setValue(river_data['longitude'])
        
        self.difficulty_combo.setCurrentText(river_data.get('difficulty_class', ''))
        
        if river_data.get('length_miles'):
            self.length_edit.setValue(river_data['length_miles'])
        if river_data.get('typical_flow_min'):
            self.flow_min_edit.setValue(river_data['typical_flow_min'])
        if river_data.get('typical_flow_max'):
            self.flow_max_edit.setValue(river_data['typical_flow_max'])
        
        if river_data.get('personal_rating'):
            rating_text = f"{river_data['personal_rating']} - "
            for i in range(self.rating_combo.count()):
                if self.rating_combo.itemText(i).startswith(rating_text):
                    self.rating_combo.setCurrentIndex(i)
                    break
        
        self.put_in_edit.setText(river_data.get('put_in_location', ''))
        self.take_out_edit.setText(river_data.get('take_out_location', ''))
        self.shuttle_edit.setPlainText(river_data.get('shuttle_info', ''))
        self.parking_edit.setPlainText(river_data.get('parking_details', ''))
        
        self.seasons_edit.setText(river_data.get('best_seasons', ''))
        self.water_source_edit.setText(river_data.get('water_level_source', ''))
        self.hazards_edit.setPlainText(river_data.get('hazards', ''))
        self.portages_edit.setPlainText(river_data.get('portages', ''))
        self.emergency_edit.setPlainText(river_data.get('emergency_contacts', ''))
        
        self.description_edit.setPlainText(river_data.get('description', ''))
        self.notes_edit.setPlainText(river_data.get('notes', ''))
        
        # Handle tags - for now we'll store them as a simple comma-separated string
        # In the future, this could be enhanced to use the river_tags table
        self.tags_edit.setText(river_data.get('tags', ''))
    
    def get_river_data(self) -> Dict:
        """Get the river data from the form"""
        rating_text = self.rating_combo.currentText()
        rating = int(rating_text[0]) if rating_text and rating_text[0].isdigit() else None
        
        return {
            'name': self.name_edit.text().strip(),
            'location': self.location_edit.text().strip(),
            'region': self.region_edit.text().strip(),
            'latitude': self.latitude_edit.value() if self.latitude_edit.value() != 0 else None,
            'longitude': self.longitude_edit.value() if self.longitude_edit.value() != 0 else None,
            'difficulty_class': self.difficulty_combo.currentText(),
            'length_miles': self.length_edit.value() if self.length_edit.value() != 0 else None,
            'typical_flow_min': self.flow_min_edit.value() if self.flow_min_edit.value() != 0 else None,
            'typical_flow_max': self.flow_max_edit.value() if self.flow_max_edit.value() != 0 else None,
            'personal_rating': rating,
            'put_in_location': self.put_in_edit.text().strip(),
            'take_out_location': self.take_out_edit.text().strip(),
            'shuttle_info': self.shuttle_edit.toPlainText().strip(),
            'parking_details': self.parking_edit.toPlainText().strip(),
            'best_seasons': self.seasons_edit.text().strip(),
            'water_level_source': self.water_source_edit.text().strip(),
            'hazards': self.hazards_edit.toPlainText().strip(),
            'portages': self.portages_edit.toPlainText().strip(),
            'emergency_contacts': self.emergency_edit.toPlainText().strip(),
            'description': self.description_edit.toPlainText().strip(),
            'notes': self.notes_edit.toPlainText().strip(),
            'tags': self.tags_edit.text().strip()
        }


class TripLogDialog(QDialog):
    """Dialog for adding/editing trip logs"""
    
    def __init__(self, parent=None, rivers=None, selected_river_id=None, trip_data=None):
        super().__init__(parent)
        self.rivers = rivers or []
        self.selected_river_id = selected_river_id
        self.trip_data = trip_data
        self.setup_ui()
        if trip_data:
            self.populate_form(trip_data)
        
        # Set icon for dialog
        self.set_dialog_icon()
    
    def set_dialog_icon(self):
        """Set the icon for this dialog"""
        icon_path = get_icon_path()
        if icon_path and os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
    
    def setup_ui(self):
        self.setWindowTitle("Add Trip Log" if not self.trip_data else "Edit Trip Log")
        self.setModal(True)
        self.resize(500, 600)
        
        layout = QVBoxLayout(self)
        
        # Create form
        form_layout = QFormLayout()
        
        # River selection
        self.river_combo = QComboBox()
        for river in self.rivers:
            self.river_combo.addItem(river['name'], river['id'])
        
        if self.selected_river_id:
            for i in range(self.river_combo.count()):
                if self.river_combo.itemData(i) == self.selected_river_id:
                    self.river_combo.setCurrentIndex(i)
                    break
        
        # Trip details
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        
        self.companions_edit = QLineEdit()
        self.water_level_edit = QLineEdit()
        self.weather_edit = QLineEdit()
        
        self.flow_rate_edit = QSpinBox()
        self.flow_rate_edit.setRange(0, 50000)
        self.flow_rate_edit.setSuffix(" cfs")
        
        self.duration_edit = QDoubleSpinBox()
        self.duration_edit.setRange(0, 24)
        self.duration_edit.setDecimals(1)
        self.duration_edit.setSuffix(" hours")
        
        self.difficulty_edit = QLineEdit()
        
        self.rating_combo = QComboBox()
        self.rating_combo.addItems(["", "1 - Poor", "2 - Fair", "3 - Good", "4 - Very Good", "5 - Excellent"])
        
        # Text areas
        self.highlights_edit = QTextEdit()
        self.highlights_edit.setMaximumHeight(80)
        self.challenges_edit = QTextEdit()
        self.challenges_edit.setMaximumHeight(80)
        self.gear_edit = QTextEdit()
        self.gear_edit.setMaximumHeight(60)
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(80)
        
        # Add fields to form
        form_layout.addRow(QLabel("River<span style='color: red;'>*</span>:"), self.river_combo)
        form_layout.addRow(QLabel("Date<span style='color: red;'>*</span>:"), self.date_edit)
        form_layout.addRow("Companions:", self.companions_edit)
        form_layout.addRow("Water Level:", self.water_level_edit)
        form_layout.addRow("Weather:", self.weather_edit)
        form_layout.addRow("Flow Rate:", self.flow_rate_edit)
        form_layout.addRow("Duration:", self.duration_edit)
        form_layout.addRow("Difficulty Experienced:", self.difficulty_edit)
        form_layout.addRow("Trip Rating:", self.rating_combo)
        form_layout.addRow("Highlights:", self.highlights_edit)
        form_layout.addRow("Challenges:", self.challenges_edit)
        form_layout.addRow("Gear Used:", self.gear_edit)
        form_layout.addRow("Notes:", self.notes_edit)
        
        layout.addLayout(form_layout)
        
        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel)
        
        # Add custom Save button
        save_button = button_box.addButton("Save", QDialogButtonBox.ButtonRole.AcceptRole)
        save_button.setDefault(True)  # Make Save the default button
        
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def populate_form(self, trip_data):
        """Populate form with existing trip data"""
        # Set the river selection
        for i in range(self.river_combo.count()):
            if self.river_combo.itemData(i) == trip_data.get('river_id'):
                self.river_combo.setCurrentIndex(i)
                break
        
        # Set the date
        if trip_data.get('trip_date'):
            date_parts = trip_data['trip_date'].split('-')
            if len(date_parts) == 3:
                year, month, day = map(int, date_parts)
                self.date_edit.setDate(QDate(year, month, day))
        
        # Set text fields
        self.companions_edit.setText(trip_data.get('companions', ''))
        self.water_level_edit.setText(trip_data.get('water_level', ''))
        self.weather_edit.setText(trip_data.get('weather_conditions', ''))
        
        # Set numeric fields
        if trip_data.get('flow_rate'):
            self.flow_rate_edit.setValue(trip_data['flow_rate'])
        if trip_data.get('duration_hours'):
            self.duration_edit.setValue(trip_data['duration_hours'])
        
        self.difficulty_edit.setText(trip_data.get('difficulty_experienced', ''))
        
        # Set rating
        if trip_data.get('trip_rating'):
            rating_text = f"{trip_data['trip_rating']} - "
            for i in range(self.rating_combo.count()):
                if self.rating_combo.itemText(i).startswith(rating_text):
                    self.rating_combo.setCurrentIndex(i)
                    break
        
        # Set text areas
        self.highlights_edit.setPlainText(trip_data.get('highlights', ''))
        self.challenges_edit.setPlainText(trip_data.get('challenges', ''))
        self.gear_edit.setPlainText(trip_data.get('gear_used', ''))
        self.notes_edit.setPlainText(trip_data.get('notes', ''))
    
    def get_trip_data(self) -> Dict:
        """Get the trip data from the form"""
        rating_text = self.rating_combo.currentText()
        rating = int(rating_text[0]) if rating_text and rating_text[0].isdigit() else None
        
        return {
            'river_id': self.river_combo.currentData(),
            'trip_date': self.date_edit.date().toString('yyyy-MM-dd'),
            'companions': self.companions_edit.text().strip(),
            'water_level': self.water_level_edit.text().strip(),
            'weather_conditions': self.weather_edit.text().strip(),
            'flow_rate': self.flow_rate_edit.value() if self.flow_rate_edit.value() != 0 else None,
            'duration_hours': self.duration_edit.value() if self.duration_edit.value() != 0 else None,
            'difficulty_experienced': self.difficulty_edit.text().strip(),
            'trip_rating': rating,
            'highlights': self.highlights_edit.toPlainText().strip(),
            'challenges': self.challenges_edit.toPlainText().strip(),
            'gear_used': self.gear_edit.toPlainText().strip(),
            'notes': self.notes_edit.toPlainText().strip()
        }


class FileAttachmentWidget(QWidget):
    """Widget for managing file attachments"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.river_id = None
        self.db_manager = None
        # Use app data directory for attachments
        app_dir = get_app_data_dir()
        self.attachments_dir = os.path.join(app_dir, "attachments")
        os.makedirs(self.attachments_dir, exist_ok=True)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header with add button
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("Attachments"))
        header_layout.addStretch()
        
        self.add_file_btn = QPushButton("Add File")
        self.add_file_btn.clicked.connect(self.add_file)
        header_layout.addWidget(self.add_file_btn)
        
        layout.addLayout(header_layout)
        
        # File list
        self.file_list = QListWidget()
        self.file_list.itemDoubleClicked.connect(self.open_file)
        layout.addWidget(self.file_list)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.open_btn = QPushButton("Open")
        self.open_btn.clicked.connect(self.open_selected_file)
        btn_layout.addWidget(self.open_btn)
        
        self.remove_btn = QPushButton("Remove")
        self.remove_btn.clicked.connect(self.remove_file)
        btn_layout.addWidget(self.remove_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
    
    def set_river(self, river_id, db_manager):
        """Set the river and database manager"""
        self.river_id = river_id
        self.db_manager = db_manager
        self.refresh_file_list()
    
    def add_file(self):
        """Add a new file attachment"""
        if not self.river_id:
            return
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select File to Attach",
            "",
            "All Files (*);;Images (*.png *.jpg *.jpeg *.gif *.bmp);;Documents (*.pdf *.doc *.docx);;Spreadsheets (*.xls *.xlsx *.csv)"
        )
        
        if file_path:
            try:
                # Copy file to attachments directory
                file_name = os.path.basename(file_path)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                new_file_name = f"{timestamp}_{file_name}"
                new_file_path = os.path.join(self.attachments_dir, new_file_name)
                
                shutil.copy2(file_path, new_file_path)
                
                # Add to database
                file_name = os.path.basename(file_path)
                base_name = os.path.splitext(file_name)[0]  # Remove extension for cleaner default description
                
                description, ok = QInputDialog.getText(
                    self, 
                    "File Description", 
                    f"Description for {file_name}:",
                    text=base_name  # Use base name without extension as default
                )
                
                if ok:
                    self.db_manager.add_document(self.river_id, new_file_path, description)
                    self.refresh_file_list()
                    QMessageBox.information(self, "Success", f"File '{file_name}' added successfully!")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to add file: {str(e)}")
    
    def refresh_file_list(self):
        """Refresh the file list"""
        if not self.river_id or not self.db_manager:
            return
        
        self.file_list.clear()
        documents = self.db_manager.get_river_documents(self.river_id)
        
        for doc in documents:
            # Just show the description, not the timestamped filename
            item_text = doc['description']
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, doc)
            
            # Add tooltip showing the actual filename and file info
            tooltip = f"File: {doc['file_name']}\nSize: {doc['file_size']} bytes\nUploaded: {doc['upload_date'][:16]}"
            item.setToolTip(tooltip)
            
            self.file_list.addItem(item)
    
    def open_selected_file(self):
        """Open the selected file"""
        current_item = self.file_list.currentItem()
        if current_item:
            self.open_file(current_item)
    
    def open_file(self, item):
        """Open a file"""
        doc_data = item.data(Qt.ItemDataRole.UserRole)
        file_path = doc_data['file_path']
        
        if os.path.exists(file_path):
            import subprocess
            import platform
            
            try:
                if platform.system() == 'Darwin':  # macOS
                    subprocess.call(('open', file_path))
                elif platform.system() == 'Windows':  # Windows
                    os.startfile(file_path)
                else:  # Linux
                    subprocess.call(('xdg-open', file_path))
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to open file: {str(e)}")
        else:
            QMessageBox.warning(self, "File Not Found", f"File not found: {file_path}")
    
    def remove_file(self):
        """Remove the selected file"""
        current_item = self.file_list.currentItem()
        if not current_item:
            return
        
        doc_data = current_item.data(Qt.ItemDataRole.UserRole)
        
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to remove '{doc_data['description']}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Remove from database
                conn = sqlite3.connect(self.db_manager.db_path)
                cursor = conn.cursor()
                cursor.execute('DELETE FROM river_documents WHERE id = ?', (doc_data['id'],))
                conn.commit()
                conn.close()
                
                # Remove physical file
                if os.path.exists(doc_data['file_path']):
                    os.remove(doc_data['file_path'])
                
                self.refresh_file_list()
                QMessageBox.information(self, "Success", "File removed successfully!")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to remove file: {str(e)}")


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        
        # Migrate old data if it exists
        migrated = migrate_old_data()
        
        self.db_manager = DatabaseManager()
        self.settings = QSettings("RiverRunner", "RiverRunner")
        self.dark_mode = self.settings.value("dark_mode", False, type=bool)
        self.include_trip_logs = self.settings.value("include_trip_logs", True, type=bool)
        self.setup_ui()
        self.apply_theme()
        self.refresh_rivers_table()
        self.refresh_trips_table()
        
        # Set the application icon
        self.set_application_icon()
        
        # Show migration message if data was migrated
        if migrated:
            app_dir = get_app_data_dir()
            QMessageBox.information(
                self,
                "Data Migrated",
                f"Your River Runner data has been moved to the standard application data folder:\n\n{app_dir}\n\n"
                "This follows operating system conventions and keeps your data safe and organized."
            )
    
    def set_application_icon(self):
        """Set the application icon for the main window and application"""
        icon_path = get_icon_path()
        if icon_path and os.path.exists(icon_path):
            icon = QIcon(icon_path)
            self.setWindowIcon(icon)
            # Also set it as the application icon for taskbar
            QApplication.instance().setWindowIcon(icon)
    
    def setup_ui(self):
        self.setWindowTitle("River Runner")
        self.setGeometry(100, 100, 1275, 800)  # Updated width to 1275
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        layout = QVBoxLayout(central_widget)
        layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.create_rivers_tab()
        self.create_trip_logs_tab()
        self.create_stats_tab()
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
    
    def apply_theme(self):
        """Apply the current theme"""
        if self.dark_mode:
            self.apply_dark_theme()
        else:
            self.apply_nature_theme()
    
    def apply_dark_theme(self):
        """Apply the dark theme"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QWidget {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QTabWidget::pane {
                border: 1px solid #555555;
                background-color: #2b2b2b;
            }
            QTabBar::tab {
                background-color: #404040;
                color: #ffffff;
                border: 1px solid #555555;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #4CAF50;
                color: #ffffff;
                border-bottom: 1px solid #4CAF50;
            }
            QTabBar::tab:hover {
                background-color: #505050;
                color: #ffffff;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555555;
                border-radius: 5px;
                margin-top: 1ex;
                padding-top: 10px;
                background-color: #333333;
                color: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #ffffff;
            }
            QPushButton {
                background-color: #4CAF50;
                border: none;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QLineEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit {
                background-color: #404040;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 5px;
                color: #ffffff;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
                border: 2px solid #4CAF50;
            }
            QTableWidget {
                background-color: #333333;
                alternate-background-color: #404040;
                gridline-color: #555555;
                color: #ffffff;
                selection-background-color: #4CAF50;
            }
            QTableWidget::item {
                padding: 5px;
                border-bottom: 1px solid #555555;
            }
            QTableWidget::item:selected {
                background-color: #4CAF50;
                color: #ffffff;
            }
            QHeaderView::section {
                background-color: #404040;
                color: #ffffff;
                padding: 5px;
                border: 1px solid #555555;
                font-weight: bold;
            }
            QListWidget {
                background-color: #333333;
                border: 1px solid #555555;
                color: #ffffff;
            }
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #555555;
            }
            QListWidget::item:selected {
                background-color: #4CAF50;
                color: #ffffff;
            }
            QListWidget::item:hover {
                background-color: #505050;
            }
            QLabel {
                color: #ffffff;
            }
            QScrollBar:vertical {
                background-color: #404040;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #555555;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #666666;
            }
            QScrollBar:horizontal {
                background-color: #404040;
                height: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:horizontal {
                background-color: #555555;
                border-radius: 6px;
                min-width: 20px;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: #666666;
            }
            QMenuBar {
                background-color: #333333;
                color: #ffffff;
                border-bottom: 1px solid #555555;
            }
            QMenuBar::item {
                background-color: transparent;
                padding: 5px 10px;
            }
            QMenuBar::item:selected {
                background-color: #4CAF50;
            }
            QMenu {
                background-color: #333333;
                color: #ffffff;
                border: 1px solid #555555;
            }
            QMenu::item {
                padding: 5px 10px;
            }
            QMenu::item:selected {
                background-color: #4CAF50;
            }
            QStatusBar {
                background-color: #333333;
                color: #ffffff;
                border-top: 1px solid #555555;
            }
        """)
    
    def apply_nature_theme(self):
        """Apply the nature-inspired theme"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #e8f4f8;
                color: #2c5530;
            }
            QWidget {
                background-color: #e8f4f8;
                color: #2c5530;
            }
            QTabWidget::pane {
                border: 1px solid #7fb069;
                background-color: #e8f4f8;
            }
            QTabBar::tab {
                background-color: #a8d5ba;
                color: #2c5530;
                border: 1px solid #7fb069;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background-color: #4682b4;
                color: #ffffff;
                border-bottom: 1px solid #4682b4;
            }
            QTabBar::tab:hover {
                background-color: #7fb069;
                color: #ffffff;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #7fb069;
                border-radius: 5px;
                margin-top: 1ex;
                padding-top: 10px;
                background-color: #f8fffe;
                color: #2c5530;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #2c5530;
            }
            QPushButton {
                background-color: #4682b4;
                border: none;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5a9bd4;
            }
            QPushButton:pressed {
                background-color: #2e6da4;
            }
            QLineEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit {
                background-color: #ffffff;
                border: 1px solid #a8d5ba;
                border-radius: 3px;
                padding: 5px;
                color: #2c5530;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
                border: 2px solid #4682b4;
            }
            QTableWidget {
                background-color: #ffffff;
                alternate-background-color: #f0f8ff;
                gridline-color: #a8d5ba;
                color: #2c5530;
                selection-background-color: #4682b4;
            }
            QTableWidget::item {
                padding: 5px;
                border-bottom: 1px solid #a8d5ba;
            }
            QTableWidget::item:selected {
                background-color: #4682b4;
                color: #ffffff;
            }
            QHeaderView::section {
                background-color: #a8d5ba;
                color: #2c5530;
                padding: 5px;
                border: 1px solid #7fb069;
                font-weight: bold;
            }
            QListWidget {
                background-color: #ffffff;
                border: 1px solid #a8d5ba;
                color: #2c5530;
            }
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #a8d5ba;
            }
            QListWidget::item:selected {
                background-color: #4682b4;
                color: #ffffff;
            }
            QListWidget::item:hover {
                background-color: #f0f8ff;
                color: #2c5530;
            }
            QListWidget::item:selected:hover {
                background-color: #5a9bd4;
                color: #ffffff;
            }
            QLabel {
                color: #2c5530;
            }
            QScrollBar:vertical {
                background-color: #d4e9f1;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #7fb069;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #88c999;
            }
            QScrollBar:horizontal {
                background-color: #d4e9f1;
                height: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:horizontal {
                background-color: #7fb069;
                border-radius: 6px;
                min-width: 20px;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: #88c999;
            }
            QMenuBar {
                background-color: #a8d5ba;
                color: #2c5530;
                border-bottom: 1px solid #7fb069;
            }
            QMenuBar::item {
                background-color: transparent;
                padding: 5px 10px;
            }
            QMenuBar::item:selected {
                background-color: #4682b4;
                color: #ffffff;
            }
            QMenu {
                background-color: #f8fffe;
                color: #2c5530;
                border: 1px solid #7fb069;
            }
            QMenu::item {
                padding: 5px 10px;
            }
            QMenu::item:selected {
                background-color: #4682b4;
                color: #ffffff;
            }
            QStatusBar {
                background-color: #a8d5ba;
                color: #2c5530;
                border-top: 1px solid #7fb069;
            }
        """)
    
    def create_menu_bar(self):
        """Create the menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        add_river_action = QAction('Add River', self)
        add_river_action.setShortcut('Ctrl+R')
        add_river_action.triggered.connect(self.add_river)
        file_menu.addAction(add_river_action)
        
        add_trip_action = QAction('Add Trip Log', self)
        add_trip_action.setShortcut('Ctrl+T')
        add_trip_action.triggered.connect(self.add_trip_log)
        file_menu.addAction(add_trip_action)
        
        file_menu.addSeparator()
        
        import_action = QAction('Import Data', self)
        import_action.triggered.connect(self.import_data)
        file_menu.addAction(import_action)
        
        export_action = QAction('Export Data', self)
        export_action.triggered.connect(self.export_data)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('Exit', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        
        # Settings menu
        settings_menu = menubar.addMenu('Settings')
        
        self.dark_mode_action = QAction('Dark Mode', self)
        self.dark_mode_action.setCheckable(True)
        self.dark_mode_action.setChecked(self.dark_mode)
        self.dark_mode_action.triggered.connect(self.toggle_dark_mode)
        settings_menu.addAction(self.dark_mode_action)
        
        settings_menu.addSeparator()
        
        self.trip_logs_action = QAction('Include Trip Logs (Import/Export)', self)
        self.trip_logs_action.setCheckable(True)
        self.trip_logs_action.setChecked(self.include_trip_logs)
        self.trip_logs_action.triggered.connect(self.toggle_trip_logs_setting)
        settings_menu.addAction(self.trip_logs_action)
        
        # Help menu
        help_menu = menubar.addMenu('Help')
        
        data_location_action = QAction('Show Data Location', self)
        data_location_action.triggered.connect(self.show_data_location)
        help_menu.addAction(data_location_action)
        
        documentation_action = QAction('Documentation', self)
        documentation_action.triggered.connect(self.open_documentation)
        help_menu.addAction(documentation_action)
        
        help_menu.addSeparator()
        
        about_action = QAction('About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def toggle_dark_mode(self):
        """Toggle between dark mode and nature theme"""
        self.dark_mode = self.dark_mode_action.isChecked()
        self.settings.setValue("dark_mode", self.dark_mode)
        self.apply_theme()
        
        # Refresh river details if one is currently selected to update the river name color
        current_row = self.rivers_table.currentRow()
        if current_row >= 0:
            river_id_item = self.rivers_table.item(current_row, 0)
            if river_id_item:
                river_id = int(river_id_item.text())
                river_data = self.db_manager.get_river_by_id(river_id)
                self.display_river_details(river_data)
        
        theme_name = "Dark Mode" if self.dark_mode else "Nature Theme"
        self.status_bar.showMessage(f"Switched to {theme_name}")
    
    def toggle_trip_logs_setting(self):
        """Toggle the trip logs import/export setting"""
        self.include_trip_logs = self.trip_logs_action.isChecked()
        self.settings.setValue("include_trip_logs", self.include_trip_logs)
        
        status_text = "enabled" if self.include_trip_logs else "disabled"
        self.status_bar.showMessage(f"Trip logs import/export {status_text}")
    
    def create_rivers_tab(self):
        """Create the rivers management tab"""
        rivers_widget = QWidget()
        self.tab_widget.addTab(rivers_widget, "Rivers")
        
        layout = QVBoxLayout(rivers_widget)
        
        # Search and filter section
        search_layout = QHBoxLayout()
        
        search_layout.addWidget(QLabel("Search:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search rivers by name, location, or difficulty...")
        self.search_edit.textChanged.connect(self.filter_rivers)
        search_layout.addWidget(self.search_edit)
        
        search_layout.addWidget(QLabel("Difficulty:"))
        self.difficulty_filter = QComboBox()
        self.difficulty_filter.addItems(["All", "Class I", "Class II", "Class III", "Class IV", "Class V", "Class VI"])
        self.difficulty_filter.currentTextChanged.connect(self.filter_rivers)
        search_layout.addWidget(self.difficulty_filter)
        
        layout.addLayout(search_layout)
        
        # Create splitter for table and details
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)
        
        # Rivers table
        table_widget = QWidget()
        table_layout = QVBoxLayout(table_widget)
        
        # Table buttons
        table_btn_layout = QHBoxLayout()
        
        self.add_river_btn = QPushButton("Add River")
        self.add_river_btn.clicked.connect(self.add_river)
        table_btn_layout.addWidget(self.add_river_btn)
        
        self.edit_river_btn = QPushButton("Edit River")
        self.edit_river_btn.clicked.connect(self.edit_river)
        table_btn_layout.addWidget(self.edit_river_btn)
        
        self.delete_river_btn = QPushButton("Delete River")
        self.delete_river_btn.clicked.connect(self.delete_river)
        self.delete_river_btn.setStyleSheet("QPushButton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #f44336, stop:1 #c62828); border: 2px solid #c62828; } QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #e57373, stop:1 #f44336); }")
        table_btn_layout.addWidget(self.delete_river_btn)
        
        table_btn_layout.addStretch()
        table_layout.addLayout(table_btn_layout)
        
        # Rivers table
        self.rivers_table = QTableWidget()
        self.rivers_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.rivers_table.itemSelectionChanged.connect(self.river_selection_changed)
        table_layout.addWidget(self.rivers_table)
        
        splitter.addWidget(table_widget)
        
        # River details panel
        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)
        
        details_layout.addWidget(QLabel("River Details"))
        
        self.river_details = QTextEdit()
        self.river_details.setReadOnly(True)
        details_layout.addWidget(self.river_details, 3)  # River details get 3 parts of the space
        
        # File attachments
        self.file_attachment_widget = FileAttachmentWidget()
        details_layout.addWidget(self.file_attachment_widget, 2)  # Attachments get 2 parts of the space
        
        splitter.addWidget(details_widget)
        
        # Set splitter proportions
        splitter.setSizes([700, 500])
    
    def create_trip_logs_tab(self):
        """Create the trip logs tab"""
        trips_widget = QWidget()
        self.tab_widget.addTab(trips_widget, "Trip Logs")
        
        layout = QVBoxLayout(trips_widget)
        
        # Trip log buttons
        btn_layout = QHBoxLayout()
        
        self.add_trip_btn = QPushButton("Add Trip Log")
        self.add_trip_btn.clicked.connect(self.add_trip_log)
        btn_layout.addWidget(self.add_trip_btn)
        
        self.edit_trip_btn = QPushButton("Edit Trip Log")
        self.edit_trip_btn.clicked.connect(self.edit_trip_log)
        btn_layout.addWidget(self.edit_trip_btn)
        
        self.delete_trip_btn = QPushButton("Delete Trip Log")
        self.delete_trip_btn.clicked.connect(self.delete_trip_log)
        self.delete_trip_btn.setStyleSheet("QPushButton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #f44336, stop:1 #c62828); border: 2px solid #c62828; } QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #e57373, stop:1 #f44336); }")
        btn_layout.addWidget(self.delete_trip_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # Trip logs table
        self.trips_table = QTableWidget()
        self.trips_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.trips_table.itemSelectionChanged.connect(self.trip_selection_changed)
        layout.addWidget(self.trips_table)
    
    def create_stats_tab(self):
        """Create the statistics tab"""
        stats_widget = QWidget()
        self.tab_widget.addTab(stats_widget, "Statistics")
        
        layout = QVBoxLayout(stats_widget)
        
        # Stats display
        self.stats_display = QTextEdit()
        self.stats_display.setReadOnly(True)
        layout.addWidget(self.stats_display)
        
        # Update stats
        self.update_statistics()
    
    def refresh_rivers_table(self):
        """Refresh the rivers table"""
        rivers = self.db_manager.get_all_rivers()
        
        self.rivers_table.setRowCount(len(rivers))
        self.rivers_table.setColumnCount(7)
        
        headers = ["ID", "Name", "Location", "Difficulty", "Length (mi)", "Rating", "Last Updated"]
        self.rivers_table.setHorizontalHeaderLabels(headers)
        
        for row, river in enumerate(rivers):
            self.rivers_table.setItem(row, 0, QTableWidgetItem(str(river['id'])))
            self.rivers_table.setItem(row, 1, QTableWidgetItem(river['name']))
            self.rivers_table.setItem(row, 2, QTableWidgetItem(river['location']))
            
            self.rivers_table.setItem(row, 3, QTableWidgetItem(river['difficulty_class'] or ''))
            
            length_text = f"{river['length_miles']:.1f}" if river['length_miles'] else ''
            self.rivers_table.setItem(row, 4, QTableWidgetItem(length_text))
            
            rating_text = str(river['personal_rating']) if river['personal_rating'] else ''
            self.rivers_table.setItem(row, 5, QTableWidgetItem(rating_text))
            
            self.rivers_table.setItem(row, 6, QTableWidgetItem(river['last_updated'][:10]))
        
        # Hide ID column and resize
        self.rivers_table.hideColumn(0)
        self.rivers_table.resizeColumnsToContents()
        
        # Store original data for filtering
        self.original_rivers_data = rivers
    
    def filter_rivers(self):
        """Filter rivers based on search criteria"""
        search_text = self.search_edit.text().lower()
        difficulty_filter = self.difficulty_filter.currentText()
        
        filtered_rivers = []
        for river in self.original_rivers_data:
            # Text search
            if search_text:
                searchable_text = f"{river['name']} {river['location']} {river['difficulty_class']}".lower()
                if search_text not in searchable_text:
                    continue
            
            # Difficulty filter
            if difficulty_filter != "All" and river['difficulty_class'] != difficulty_filter:
                continue
            
            filtered_rivers.append(river)
        
        # Update table with filtered results
        self.rivers_table.setRowCount(len(filtered_rivers))
        
        for row, river in enumerate(filtered_rivers):
            self.rivers_table.setItem(row, 0, QTableWidgetItem(str(river['id'])))
            self.rivers_table.setItem(row, 1, QTableWidgetItem(river['name']))
            self.rivers_table.setItem(row, 2, QTableWidgetItem(river['location']))
            
            self.rivers_table.setItem(row, 3, QTableWidgetItem(river['difficulty_class'] or ''))
            
            length_text = f"{river['length_miles']:.1f}" if river['length_miles'] else ''
            self.rivers_table.setItem(row, 4, QTableWidgetItem(length_text))
            
            rating_text = str(river['personal_rating']) if river['personal_rating'] else ''
            self.rivers_table.setItem(row, 5, QTableWidgetItem(rating_text))
            
            self.rivers_table.setItem(row, 6, QTableWidgetItem(river['last_updated'][:10]))
    
    def river_selection_changed(self):
        """Handle river selection change"""
        current_row = self.rivers_table.currentRow()
        if current_row >= 0:
            river_id_item = self.rivers_table.item(current_row, 0)
            if river_id_item:
                river_id = int(river_id_item.text())
                river_data = self.db_manager.get_river_by_id(river_id)
                self.display_river_details(river_data)
                self.file_attachment_widget.set_river(river_id, self.db_manager)
    
    def display_river_details(self, river_data):
        """Display detailed river information"""
        if not river_data:
            self.river_details.clear()
            return
        
        # Set river name color based on current theme
        river_name_color = "#ffffff" if self.dark_mode else "#4682b4"
        
        # Get difficulty and apply color coding
        difficulty = river_data.get('difficulty_class', '')
        difficulty_styled = difficulty
        
        if difficulty in ['Class I', 'Class II']:
            difficulty_styled = f'<span style="color: green; font-weight: bold;">{difficulty}</span>'
        elif difficulty == 'Class III':
            difficulty_styled = f'<span style="color: orange; font-weight: bold;">{difficulty}</span>'
        elif difficulty in ['Class IV', 'Class V']:
            difficulty_styled = f'<span style="color: red; font-weight: bold;">{difficulty}</span>'
        elif difficulty == 'Class VI':
            difficulty_styled = f'<span style="color: #C71585; font-weight: bold;">{difficulty}</span>'  # Changed to pinkish purple without underline
        
        # Helper function to check if a field has meaningful data
        def has_data(value):
            if value is None:
                return False
            if isinstance(value, (int, float)):
                return True  # All numeric values are valid (including 0)
            return value and str(value).strip() and str(value).strip().lower() != 'n/a'
        
        # Start building the HTML
        details_html = f'<h2 style="color: {river_name_color};">{river_data["name"]}</h2>'
        
        # Always show location (required field)
        details_html += f'<p><strong>Location:</strong> {river_data["location"]}</p>'
        
        # Show coordinates if available
        lat = river_data.get('latitude')
        lon = river_data.get('longitude')
        if has_data(lat) or has_data(lon):
            lat_text = f"{lat:.6f}" if has_data(lat) else "?"
            lon_text = f"{lon:.6f}" if has_data(lon) else "?"
            details_html += f'<p><strong>Coordinates:</strong> {lat_text}, {lon_text}</p>'
        
        # Conditionally show other basic info
        if has_data(river_data.get('region')):
            details_html += f'<p><strong>Region:</strong> {river_data["region"]}</p>'
        
        if has_data(difficulty):
            details_html += f'<p><strong>Difficulty:</strong> {difficulty_styled}</p>'
        
        if has_data(river_data.get('length_miles')):
            details_html += f'<p><strong>Length:</strong> {river_data["length_miles"]} miles</p>'
        
        # Flow range - only show if we have at least one value
        flow_min = river_data.get('typical_flow_min')
        flow_max = river_data.get('typical_flow_max')
        if has_data(flow_min) or has_data(flow_max):
            flow_min_text = str(flow_min) if has_data(flow_min) else '?'
            flow_max_text = str(flow_max) if has_data(flow_max) else '?'
            details_html += f'<p><strong>Flow Range:</strong> {flow_min_text} - {flow_max_text} cfs</p>'
        
        if has_data(river_data.get('personal_rating')):
            details_html += f'<p><strong>Personal Rating:</strong> {river_data["personal_rating"]}/5</p>'
        
        # Access Information section - only show if we have at least one field
        access_fields = []
        if has_data(river_data.get('put_in_location')):
            access_fields.append(f'<p><strong>Put-in:</strong> {river_data["put_in_location"]}</p>')
        if has_data(river_data.get('take_out_location')):
            access_fields.append(f'<p><strong>Take-out:</strong> {river_data["take_out_location"]}</p>')
        if has_data(river_data.get('shuttle_info')):
            access_fields.append(f'<p><strong>Shuttle Info:</strong> {river_data["shuttle_info"]}</p>')
        if has_data(river_data.get('parking_details')):
            access_fields.append(f'<p><strong>Parking:</strong> {river_data["parking_details"]}</p>')
        
        if access_fields:
            details_html += '<h3 style="color: #4682b4;">Access Information</h3>'
            details_html += ''.join(access_fields)
        
        # Conditions & Safety section - only show if we have at least one field
        safety_fields = []
        if has_data(river_data.get('best_seasons')):
            safety_fields.append(f'<p><strong>Best Seasons:</strong> {river_data["best_seasons"]}</p>')
        if has_data(river_data.get('water_level_source')):
            safety_fields.append(f'<p><strong>Water Level Source:</strong> {river_data["water_level_source"]}</p>')
        if has_data(river_data.get('hazards')):
            safety_fields.append(f'<p><strong>Hazards:</strong> {river_data["hazards"]}</p>')
        if has_data(river_data.get('portages')):
            safety_fields.append(f'<p><strong>Portages:</strong> {river_data["portages"]}</p>')
        if has_data(river_data.get('emergency_contacts')):
            safety_fields.append(f'<p><strong>Emergency Contacts:</strong> {river_data["emergency_contacts"]}</p>')
        
        if safety_fields:
            details_html += '<h3 style="color: #4682b4;">Conditions & Safety</h3>'
            details_html += ''.join(safety_fields)
        
        # Description section
        if has_data(river_data.get('description')):
            details_html += '<h3 style="color: #4682b4;">Description</h3>'
            details_html += f'<p>{river_data["description"]}</p>'
        
        # Personal Notes section
        if has_data(river_data.get('notes')):
            details_html += '<h3 style="color: #4682b4;">Personal Notes</h3>'
            details_html += f'<p>{river_data["notes"]}</p>'
        
        # Tags section
        if has_data(river_data.get('tags')):
            details_html += '<h3 style="color: #4682b4;">Tags</h3>'
            details_html += f'<p>{river_data["tags"]}</p>'
        
        self.river_details.setHtml(details_html)
    
    def add_river(self):
        """Add a new river"""
        dialog = RiverFormDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            river_data = dialog.get_river_data()
            
            if not river_data['name'] or not river_data['location']:
                QMessageBox.warning(self, "Validation Error", "Name and Location are required!")
                return
            
            try:
                self.db_manager.add_river(river_data)
                self.refresh_rivers_table()
                self.update_statistics()
                self.status_bar.showMessage(f"River '{river_data['name']}' added successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to add river: {str(e)}")
    
    def edit_river(self):
        """Edit the selected river"""
        current_row = self.rivers_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a river to edit.")
            return
        
        river_id_item = self.rivers_table.item(current_row, 0)
        river_id = int(river_id_item.text())
        river_data = self.db_manager.get_river_by_id(river_id)
        
        dialog = RiverFormDialog(self, river_data)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated_data = dialog.get_river_data()
            
            if not updated_data['name'] or not updated_data['location']:
                QMessageBox.warning(self, "Validation Error", "Name and Location are required!")
                return
            
            try:
                self.db_manager.update_river(river_id, updated_data)
                self.refresh_rivers_table()
                self.display_river_details(self.db_manager.get_river_by_id(river_id))
                self.update_statistics()  # Refresh statistics to reflect changes
                self.status_bar.showMessage(f"River '{updated_data['name']}' updated successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to update river: {str(e)}")
    
    def delete_river(self):
        """Delete the selected river"""
        current_row = self.rivers_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a river to delete.")
            return
        
        river_name = self.rivers_table.item(current_row, 1).text()
        river_id = int(self.rivers_table.item(current_row, 0).text())
        
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete '{river_name}' and all associated data?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.db_manager.delete_river(river_id)
                self.refresh_rivers_table()
                self.river_details.clear()
                self.file_attachment_widget.set_river(None, None)
                self.update_statistics()
                self.status_bar.showMessage(f"River '{river_name}' deleted successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete river: {str(e)}")
    
    def trip_selection_changed(self):
        """Handle trip selection change"""
        current_row = self.trips_table.currentRow()
        if current_row >= 0:
            # Enable edit and delete buttons when a trip is selected
            self.edit_trip_btn.setEnabled(True)
            self.delete_trip_btn.setEnabled(True)
        else:
            # Disable edit and delete buttons when no trip is selected
            self.edit_trip_btn.setEnabled(False)
            self.delete_trip_btn.setEnabled(False)
    
    def edit_trip_log(self):
        """Edit the selected trip log"""
        current_row = self.trips_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a trip to edit.")
            return
        
        trip_id_item = self.trips_table.item(current_row, 0)
        trip_id = int(trip_id_item.text())
        trip_data = self.db_manager.get_trip_log_by_id(trip_id)
        
        if not trip_data:
            QMessageBox.warning(self, "Error", "Could not load trip data.")
            return
        
        rivers = self.db_manager.get_all_rivers()
        dialog = TripLogDialog(self, rivers, trip_data.get('river_id'), trip_data)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated_data = dialog.get_trip_data()
            
            try:
                self.db_manager.update_trip_log(trip_id, updated_data)
                self.refresh_trips_table()
                self.update_statistics()
                self.status_bar.showMessage("Trip log updated successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to update trip log: {str(e)}")
    
    def delete_trip_log(self):
        """Delete the selected trip log"""
        current_row = self.trips_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a trip to delete.")
            return
        
        trip_id = int(self.trips_table.item(current_row, 0).text())
        river_name = self.trips_table.item(current_row, 1).text()
        trip_date = self.trips_table.item(current_row, 2).text()
        
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete the trip to '{river_name}' on {trip_date}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.db_manager.delete_trip_log(trip_id)
                self.refresh_trips_table()
                self.update_statistics()
                self.status_bar.showMessage("Trip log deleted successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete trip log: {str(e)}")

    def add_trip_log(self):
        """Add a new trip log"""
        rivers = self.db_manager.get_all_rivers()
        if not rivers:
            QMessageBox.warning(self, "No Rivers", "Please add some rivers first before logging trips.")
            return
        
        # Check if a river is selected in the rivers tab
        selected_river_id = None
        if self.tab_widget.currentIndex() == 0:  # Rivers tab
            current_row = self.rivers_table.currentRow()
            if current_row >= 0:
                selected_river_id = int(self.rivers_table.item(current_row, 0).text())
        
        dialog = TripLogDialog(self, rivers, selected_river_id)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            trip_data = dialog.get_trip_data()
            
            try:
                self.db_manager.add_trip_log(trip_data)
                self.refresh_trips_table()
                self.update_statistics()
                self.status_bar.showMessage("Trip log added successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to add trip log: {str(e)}")
    
    def refresh_trips_table(self):
        """Refresh the trip logs table"""
        trips = self.db_manager.get_trip_logs()
        
        self.trips_table.setRowCount(len(trips))
        self.trips_table.setColumnCount(8)
        
        headers = ["ID", "River", "Date", "Companions", "Duration", "Rating", "Water Level", "Weather"]
        self.trips_table.setHorizontalHeaderLabels(headers)
        
        for row, trip in enumerate(trips):
            self.trips_table.setItem(row, 0, QTableWidgetItem(str(trip['id'])))
            self.trips_table.setItem(row, 1, QTableWidgetItem(trip['river_name']))
            self.trips_table.setItem(row, 2, QTableWidgetItem(trip['trip_date']))
            self.trips_table.setItem(row, 3, QTableWidgetItem(trip['companions'] or ''))
            
            duration_text = f"{trip['duration_hours']:.1f}h" if trip['duration_hours'] else ''
            self.trips_table.setItem(row, 4, QTableWidgetItem(duration_text))
            
            rating_text = str(trip['trip_rating']) if trip['trip_rating'] else ''
            self.trips_table.setItem(row, 5, QTableWidgetItem(rating_text))
            
            self.trips_table.setItem(row, 6, QTableWidgetItem(trip['water_level'] or ''))
            self.trips_table.setItem(row, 7, QTableWidgetItem(trip['weather_conditions'] or ''))
        
        # Hide ID column and resize
        self.trips_table.hideColumn(0)
        self.trips_table.resizeColumnsToContents()
        
        # Disable edit and delete buttons by default (no selection)
        if hasattr(self, 'edit_trip_btn'):
            self.edit_trip_btn.setEnabled(False)
        if hasattr(self, 'delete_trip_btn'):
            self.delete_trip_btn.setEnabled(False)
    
    def update_statistics(self):
        """Update the statistics display"""
        rivers = self.db_manager.get_all_rivers()
        trips = self.db_manager.get_trip_logs()
        
        # Basic counts
        total_rivers = len(rivers)
        total_trips = len(trips)
        
        # Difficulty breakdown
        difficulty_counts = {}
        for river in rivers:
            diff = river['difficulty_class'] or 'Unknown'
            difficulty_counts[diff] = difficulty_counts.get(diff, 0) + 1
        
        # Rating statistics
        ratings = [r['personal_rating'] for r in rivers if r['personal_rating']]
        avg_rating = sum(ratings) / len(ratings) if ratings else 0
        
        # Trip statistics
        total_trip_hours = sum(t['duration_hours'] for t in trips if t['duration_hours'])
        
        # Generate statistics HTML
        stats_html = f"""
        <h2 style="color: #2c5530;">River Runner Statistics</h2>
        
        <h3 style="color: #4682b4;">Rivers</h3>
        <ul>
            <li><strong>Total Rivers:</strong> {total_rivers}</li>
            <li><strong>Average Rating:</strong> {avg_rating:.1f}/5</li>
        </ul>
        
        <h3 style="color: #4682b4;">Difficulty Breakdown</h3>
        <ul>
        """
        
        for difficulty, count in sorted(difficulty_counts.items()):
            stats_html += f"<li><strong>{difficulty}:</strong> {count}</li>"
        
        stats_html += f"""
        </ul>
        
        <h3 style="color: #4682b4;">Trip Logs</h3>
        <ul>
            <li><strong>Total Trips:</strong> {total_trips}</li>
            <li><strong>Total Hours Paddled:</strong> {total_trip_hours:.1f}</li>
        </ul>
        
        <h3 style="color: #4682b4;">Most Recent Trips</h3>
        <ul>
        """
        
        recent_trips = sorted(trips, key=lambda x: x['trip_date'], reverse=True)[:5]
        for trip in recent_trips:
            stats_html += f"<li>{trip['trip_date']} - {trip['river_name']}</li>"
        
        stats_html += "</ul>"
        
        self.stats_display.setHtml(stats_html)
    
    def export_data(self):
        """Export data to JSON"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Data",
            f"whitewater_data_{datetime.now().strftime('%Y%m%d')}.json",
            "JSON Files (*.json)"
        )
        
        if file_path:
            try:
                export_data = {
                    'rivers': self.db_manager.get_all_rivers(),
                    'export_date': datetime.now().isoformat(),
                    'includes_trip_logs': self.include_trip_logs
                }
                
                # Only include trip logs if the setting is enabled
                if self.include_trip_logs:
                    export_data['trips'] = self.db_manager.get_trip_logs()
                
                with open(file_path, 'w') as f:
                    json.dump(export_data, f, indent=2, default=str)
                
                # Show what was exported
                rivers_count = len(export_data['rivers'])
                trips_count = len(export_data.get('trips', []))
                
                if self.include_trip_logs:
                    message = f"Data exported successfully!\n\nRivers: {rivers_count}\nTrip Logs: {trips_count}\n\nFile: {file_path}"
                else:
                    message = f"Rivers exported successfully!\n\nRivers: {rivers_count}\nTrip Logs: Not included (disabled in settings)\n\nFile: {file_path}"
                
                QMessageBox.information(self, "Export Complete", message)
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export data: {str(e)}")
    
    def import_data(self):
        """Import data from JSON"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Data",
            "",
            "JSON Files (*.json)"
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'r') as f:
                import_data = json.load(f)
            
            # Validate the JSON structure
            if not isinstance(import_data, dict) or 'rivers' not in import_data:
                QMessageBox.critical(self, "Invalid File", "The selected file does not contain valid River Runner data.")
                return
            
            rivers_data = import_data.get('rivers', [])
            trips_data = import_data.get('trips', [])
            
            # Import rivers first
            rivers_imported, rivers_skipped = self.import_rivers(rivers_data)
            
            # Only import trips if the setting is enabled AND trip data exists in the file
            trips_imported, trips_skipped = 0, 0
            if self.include_trip_logs and trips_data:
                trips_imported, trips_skipped = self.import_trips(trips_data)
            elif not self.include_trip_logs and trips_data:
                trips_skipped = len(trips_data)  # Count as skipped since setting is disabled
            
            # Show summary
            summary_msg = f"Import completed successfully!\n\n"
            summary_msg += f"{'='*50}\n"
            summary_msg += f"RIVERS:\n"
            summary_msg += f"  • Imported:              {rivers_imported}\n"
            summary_msg += f"  • Skipped (duplicates):  {rivers_skipped}\n\n"
            summary_msg += f"TRIP LOGS:\n"
            if self.include_trip_logs:
                summary_msg += f"  • Imported:              {trips_imported}\n"
                summary_msg += f"  • Skipped (duplicates):  {trips_skipped}\n"
            else:
                summary_msg += f"  • Skipped (setting disabled): {len(trips_data) if trips_data else 0}\n"
            summary_msg += f"{'='*50}"
            
            if not self.include_trip_logs and trips_data:
                summary_msg += f"\n\nNote: Trip log import is disabled in Settings.\nTo import trip logs, enable 'Import/Export Trip Logs' in the Settings menu."
            
            # Create a custom message box with wider dimensions
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Import Complete")
            msg_box.setText(summary_msg)
            msg_box.setIcon(QMessageBox.Icon.Information)
            msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
            
            # Make the message box wider
            msg_box.setStyleSheet("QMessageBox { min-width: 400px; }")
            msg_box.exec()
            
            # Refresh the UI
            self.refresh_rivers_table()
            self.refresh_trips_table()
            self.update_statistics()
            
            self.status_bar.showMessage(f"Imported {rivers_imported} rivers and {trips_imported} trips")
            
        except json.JSONDecodeError:
            QMessageBox.critical(self, "Invalid File", "The selected file is not a valid JSON file.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to import data: {str(e)}")
    
    def import_rivers(self, rivers_data):
        """Import rivers and return counts of imported and skipped"""
        imported_count = 0
        skipped_count = 0
        
        existing_rivers = self.db_manager.get_all_rivers()
        
        # Create a set of existing river identifiers (name + location)
        existing_identifiers = set()
        for river in existing_rivers:
            identifier = f"{river['name'].lower().strip()}|{river['location'].lower().strip()}"
            existing_identifiers.add(identifier)
        
        for river_data in rivers_data:
            # Create identifier for this river
            river_name = river_data.get('name', '').lower().strip()
            river_location = river_data.get('location', '').lower().strip()
            identifier = f"{river_name}|{river_location}"
            
            # Skip if this river already exists
            if identifier in existing_identifiers:
                skipped_count += 1
                continue
            
            # Remove the ID field if it exists (we want new IDs)
            import_river = dict(river_data)
            if 'id' in import_river:
                del import_river['id']
            if 'date_added' in import_river:
                del import_river['date_added']
            if 'last_updated' in import_river:
                del import_river['last_updated']
            
            try:
                self.db_manager.add_river(import_river)
                existing_identifiers.add(identifier)  # Add to set to prevent duplicates within import
                imported_count += 1
            except Exception as e:
                print(f"Error importing river {river_data.get('name', 'Unknown')}: {e}")
                skipped_count += 1
        
        return imported_count, skipped_count
    
    def import_trips(self, trips_data):
        """Import trip logs and return counts of imported and skipped"""
        imported_count = 0
        skipped_count = 0
        
        # Get current rivers to map names to IDs
        current_rivers = self.db_manager.get_all_rivers()
        river_name_to_id = {river['name'].lower().strip(): river['id'] for river in current_rivers}
        
        # Get existing trips to check for duplicates
        existing_trips = self.db_manager.get_trip_logs()
        existing_trip_identifiers = set()
        for trip in existing_trips:
            identifier = f"{trip['river_id']}|{trip['trip_date']}"
            existing_trip_identifiers.add(identifier)
        
        for trip_data in trips_data:
            # Map river name to current river ID
            river_name = trip_data.get('river_name', '').lower().strip()
            if river_name not in river_name_to_id:
                skipped_count += 1  # Skip if river doesn't exist
                continue
            
            new_river_id = river_name_to_id[river_name]
            trip_date = trip_data.get('trip_date', '')
            
            # Check for duplicate (same river and date)
            identifier = f"{new_river_id}|{trip_date}"
            if identifier in existing_trip_identifiers:
                skipped_count += 1
                continue
            
            # Prepare trip data for import
            import_trip = dict(trip_data)
            import_trip['river_id'] = new_river_id
            
            # Remove fields that shouldn't be imported
            fields_to_remove = ['id', 'river_name', 'created_date']
            for field in fields_to_remove:
                if field in import_trip:
                    del import_trip[field]
            
            try:
                self.db_manager.add_trip_log(import_trip)
                existing_trip_identifiers.add(identifier)  # Add to set to prevent duplicates within import
                imported_count += 1
            except Exception as e:
                print(f"Error importing trip for {trip_data.get('river_name', 'Unknown')}: {e}")
                skipped_count += 1
        
        return imported_count, skipped_count
    
    def show_data_location(self):
        """Show the user where their data is stored"""
        app_dir = get_app_data_dir()
        db_path = self.db_manager.db_path
        
        msg = f"Your River Runner data is stored in:\n\n"
        msg += f"Data Folder: {app_dir}\n"
        msg += f"Database: {db_path}\n"
        msg += f"Attachments: {os.path.join(app_dir, 'attachments')}\n\n"
        msg += "You can backup this entire folder to preserve all your river data and attachments."
        
        # Create message box with option to open folder
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Data Location")
        msg_box.setText(msg)
        msg_box.setIcon(QMessageBox.Icon.Information)
        
        # Add custom button to open folder
        open_folder_button = msg_box.addButton("Open Folder", QMessageBox.ButtonRole.ActionRole)
        ok_button = msg_box.addButton(QMessageBox.StandardButton.Ok)
        msg_box.setDefaultButton(ok_button)
        
        result = msg_box.exec()
        
        # If user clicked "Open Folder", open the data directory
        if msg_box.clickedButton() == open_folder_button:
            try:
                if platform.system() == "Windows":
                    os.startfile(app_dir)
                elif platform.system() == "Darwin":  # macOS
                    os.system(f'open "{app_dir}"')
                else:  # Linux
                    os.system(f'xdg-open "{app_dir}"')
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not open folder: {str(e)}")
    
    def open_documentation(self):
        """Open documentation in default browser"""
        try:
            webbrowser.open("https://github.com/jackworthen/river-run")
            self.status_bar.showMessage("Documentation opened in browser")
        except Exception as e:
            QMessageBox.warning(
                self, 
                "Browser Error", 
                f"Could not open documentation in browser. Please visit:\nhttps://github.com/jackworthen/river-run\n\nError: {str(e)}"
            )
    
    def show_about(self):
        """Show about dialog"""
        app_dir = get_app_data_dir()
        QMessageBox.about(
            self,
            "About River Runner",
            "River Runner v1.1\n\n"
            "A comprehensive application for logging and organizing rivers for whitewater sports.\n\n"
            "Features:\n"
            "• River information management\n"
            "• File attachments\n"
            "• Trip logging\n"
            "• Statistics and reporting\n"
            "• Data export capabilities\n"
            "• Beautiful nature-inspired themes\n"
            "• Dark mode support\n"
            "• Cross-platform data storage\n\n"
            f"Data stored in: {app_dir}"
        )

def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("River Runner")
    app.setApplicationVersion("1.1")
    app.setOrganizationName("River Runner")
    
    # Set application icon early for taskbar display
    icon_path = get_icon_path()
    if icon_path and os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Start the application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
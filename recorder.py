import os
import json
import zlib
import sqlite3
import math
from datetime import datetime
from controller import Robot, Keyboard, Motor

class ChampionController:
    """A championship-level robot controller module for Webots with path recording and playback."""
    
    def __init__(self, robot_instance, config=None):
        """
        Initialize the champion controller.
        
        Args:
            robot_instance: The Webots Robot instance
            config (dict, optional): Configuration dictionary with:
                - timestep: Simulation timestep (default: 32)
                - paths_dir: Directory for saving paths (default: 'champion_paths')
                - db_name: Database filename (default: 'champion_movements.db')
                - wheel_radius: Wheel radius in meters (default: 0.033)
                - axle_length: Distance between wheels (default: 0.1)
        """
        self.robot = robot_instance
        self.config = config or {}
        
        # Configuration defaults
        self.timestep = self.config.get('timestep', 32)
        self.paths_dir = self.config.get('paths_dir', 'champion_paths')
        self.db_name = self.config.get('db_name', 'champion_movements.db')
        self.wheel_radius = self.config.get('wheel_radius', 0.033)
        self.axle_length = self.config.get('axle_length', 0.1)
        
        # Initialize components
        self._setup_filesystem()
        self._setup_motors()
        self._setup_keyboard()
        self._init_database()
        
        # State variables
        self.recording = False
        self.playing = False
        self.movement_buffer = []
        self.true_position = {'x': 0, 'y': 0, 'theta': 0}
        self.odometry = {'x': 0, 'y': 0, 'theta': 0}
        
        # Movement parameters (can be customized)
        self.move_params = {
            'forward': (4.0, 4.0),
            'backward': (-3.0, -3.0),
            'left': (-2.5, 2.5),
            'right': (2.5, -2.5),
            'stop': (0, 0)
        }

    def _setup_filesystem(self):
        """Ensure required directories exist."""
        os.makedirs(self.paths_dir, exist_ok=True)

    def _setup_motors(self):
        """Configure motors for championship performance."""
        self.left_motor = self.robot.getDevice('left wheel motor')
        self.right_motor = self.robot.getDevice('right wheel motor')
        
        self.left_motor.setPosition(float('inf'))
        self.right_motor.setPosition(float('inf'))
        self.left_motor.setVelocity(0)
        self.right_motor.setVelocity(0)
        self.left_motor.setAcceleration(10)
        self.right_motor.setAcceleration(10)

    def _setup_keyboard(self):
        """Enable keyboard input for manual control."""
        self.keyboard = self.robot.getKeyboard()
        self.keyboard.enable(self.timestep)

    def _init_database(self):
        """Initialize the movement database."""
        self.db_conn = sqlite3.connect(self.db_name)
        cursor = self.db_conn.cursor()
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS champion_paths (
                        id INTEGER PRIMARY KEY,
                        name TEXT UNIQUE,
                        path_data BLOB,
                        metrics REAL,
                        timestamp DATETIME)''')
        
        cursor.execute('''CREATE INDEX IF NOT EXISTS idx_metrics 
                        ON champion_paths(metrics)''')
        self.db_conn.commit()

    def update_odometry(self):
        """Update position tracking using wheel encoders."""
        left_vel = self.left_motor.getVelocity()
        right_vel = self.right_motor.getVelocity()
        
        dt = self.timestep / 1000.0
        
        # Calculate linear and angular velocity
        v = (left_vel + right_vel) / 2 * self.wheel_radius
        w = (right_vel - left_vel) / self.axle_length
        
        # Update position and orientation
        self.odometry['theta'] += w * dt
        self.odometry['x'] += v * math.cos(self.odometry['theta']) * dt
        self.odometry['y'] += v * math.sin(self.odometry['theta']) * dt
        
        # Update true position (with potential for sensor fusion later)
        self.true_position = self.odometry.copy()

    def execute_move(self, action, duration=1.0):
        """
        Execute a movement command.
        
        Args:
            action (str): Movement type ('forward', 'backward', 'left', 'right', 'stop')
            duration (float): Duration in seconds (default: 1.0)
        """
        if action in self.move_params:
            left, right = self.move_params[action]
            self.left_motor.setVelocity(left)
            self.right_motor.setVelocity(right)
            
            if self.recording and not self.playing:
                self.movement_buffer.append({
                    'action': action,
                    'duration': duration,
                    'position': self.true_position.copy(),
                    'timestamp': datetime.now().isoformat()
                })

    def save_path(self, path_name):
        """
        Save the recorded path to file and database.
        
        Args:
            path_name (str): Name for the path
            
        Returns:
            bool: True if save was successful
        """
        if not self.movement_buffer:
            return False
        
        # Calculate path efficiency metric
        efficiency = len(self.movement_buffer) / max(1, len({
            (m['position']['x'], m['position']['y']) 
            for m in self.movement_buffer
        }))
        
        # Save to database
        path_data = json.dumps({
            'movements': self.movement_buffer,
            'config': self.config,
            'metrics': efficiency
        }).encode('utf-8')
        
        cursor = self.db_conn.cursor()
        cursor.execute('''INSERT OR REPLACE INTO champion_paths 
                        (name, path_data, metrics, timestamp)
                        VALUES (?, ?, ?, ?)''',
                      (path_name, zlib.compress(path_data), efficiency, 
                       datetime.now().isoformat()))
        self.db_conn.commit()
        
        # Save to JSON file
        file_path = os.path.join(self.paths_dir, f"{path_name}.json")
        with open(file_path, 'w') as f:
            json.dump({
                'movements': self.movement_buffer,
                'config': self.config,
                'metrics': efficiency,
                'timestamp': datetime.now().isoformat()
            }, f, indent=2)
        
        self.movement_buffer = []
        return True

    def load_path(self, path_name):
        """
        Load a path from storage.
        
        Args:
            path_name (str): Name of the path to load
            
        Returns:
            dict: The loaded path data or None if not found
        """

        file_path = os.path.join(self.paths_dir, f"{path_name}.json")
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                return json.load(f)
        
        # Fall back to database
        cursor = self.db_conn.cursor()
        cursor.execute('''SELECT path_data FROM champion_paths 
                        WHERE name=? ORDER BY metrics DESC LIMIT 1''', (path_name,))
        result = cursor.fetchone()
        
        if result:
            return json.loads(zlib.decompress(result[0]).decode('utf-8'))
        return None

    def play_path(self, path_name):
        """
        Execute a recorded path.
        
        Args:
            path_name (str): Name of the path to execute
            
        Returns:
            bool: True if playback was successful
        """
        path_data = self.load_path(path_name)
        if not path_data:
            return False
        
        self.playing = True
        for movement in path_data['movements']:
            self.execute_move(movement['action'], movement['duration'])
            start_time = self.robot.getTime()
            
            while self.robot.step(self.timestep) != -1:
                if self.robot.getTime() - start_time >= movement['duration']:
                    break
                self.update_odometry()
        
        self.playing = False
        self.execute_move('stop')
        return True

    def list_paths(self):
        """List all available saved paths."""
        file_paths = [
            f.replace('.json', '') for f in os.listdir(self.paths_dir) 
            if f.endswith('.json')
        ]
        

        cursor = self.db_conn.cursor()
        cursor.execute('''SELECT name FROM champion_paths''')
        db_paths = [row[0] for row in cursor.fetchall()]
        
        return sorted(set(file_paths + db_paths))

    def get_help(self):
        """Return help information for the controller."""
        return {
            'controls': {
                '↑': 'Forward (Optimal Speed)',
                '↓': 'Backward (Safe Speed)',
                '←': 'Left Turn (Competition Tight)',
                '→': 'Right Turn (Competition Tight)',
                'SPACE': 'Immediate Stop',
                'R': 'Start/Stop Recording',
                'S': 'Save Champion Path',
                'P': 'Play Champion Path',
                'L': 'List Saved Paths'
            },
            'status': {
                'recording': self.recording,
                'playing': self.playing,
                'position': self.true_position,
                'buffer_length': len(self.movement_buffer)
            }
        }
    

    
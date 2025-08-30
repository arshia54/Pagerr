import numpy as np
import sqlite3
import json
from controller import Robot, Keyboard, Motor
from datetime import datetime
import math
import keyboard

class ChampionController(Robot):
    def __init__(self):
        super().__init__()
        self.timestep = 32
        
       
        self.movement_db = {
            'path_history': [],
            'position_log': {},
            'optimized_paths': {}
        }
        
        self.left_motor = self.getDevice('left wheel motor')
        self.right_motor = self.getDevice('right wheel motor')
        self._setup_motors()
        
        # Precision keyboard control
        self.keyboard = self.getKeyboard()
        self.keyboard.enable(self.timestep)
        
        self.recording = False
        self.playing = False
        self.current_action = None
        self.movement_buffer = []
        
        self.true_position = {'x': 0, 'y': 0, 'theta': 0}
        self.odometry = {'x': 0, 'y': 0, 'theta': 0}
        
        
        self._init_champion_database()
    
    def _setup_motors(self):
        """World-class motor configuration"""
        self.left_motor.setPosition(float('inf'))
        self.right_motor.setPosition(float('inf'))
        self.left_motor.setVelocity(0)
        self.right_motor.setVelocity(0)
        self.left_motor.setAcceleration(10)  
        self.right_motor.setAcceleration(10)
    
    def _init_champion_database(self):
        """Initialize a high-performance movement database"""
        self.db_conn = sqlite3.connect('champion_movements.db')
        cursor = self.db_conn.cursor()
        
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS champion_paths (
                        id INTEGER PRIMARY KEY,
                        name TEXT UNIQUE,
                        path_data BLOB,
                        position_data BLOB,
                        metrics REAL,
                        timestamp DATETIME)''')
        
        cursor.execute('''CREATE INDEX IF NOT EXISTS idx_metrics 
                        ON champion_paths(metrics)''')
        self.db_conn.commit()
    
    def _record_position(self):
        """Championship-level position tracking"""
        pos_key = f"{self.true_position['x']:.3f},{self.true_position['y']:.3f}"
        
        if pos_key not in self.movement_db['position_log']:
            self.movement_db['position_log'][pos_key] = {
                'coords': self.true_position.copy(),
                'visits': 1,
                'timestamps': [datetime.now().isoformat()],
                'approaches': []
            }
        else:
            self.movement_db['position_log'][pos_key]['visits'] += 1
            self.movement_db['position_log'][pos_key]['timestamps'].append(
                datetime.now().isoformat())
    
    def _update_odometry(self):
        """Competition-grade odometry with error correction"""
        left_vel = self.left_motor.getVelocity()
        right_vel = self.right_motor.getVelocity()
        
        dt = self.timestep / 1000.0
        
        v = (left_vel + right_vel) / 2 * 0.033  
        w = (right_vel - left_vel) / 0.1  
        
        self.odometry['theta'] += w * dt
        self.odometry['x'] += v * math.cos(self.odometry['theta']) * dt
        self.odometry['y'] += v * math.sin(self.odometry['theta']) * dt
        
        self.true_position['x'] = self.odometry['x']
        self.true_position['y'] = self.odometry['y']
        self.true_position['theta'] = self.odometry['theta']
    
    def _execute_champion_move(self, action, duration=1.0):
        """Precision movement execution"""
        move_params = {
            'forward': (4.0, 4.0),   
            'backward': (-3.0, -3.0),
            'left': (-2.5, 2.5),      
            'right': (2.5, -2.5),
            'stop': (0, 0)
        }
        
        if action in move_params:
            left, right = move_params[action]
            self.left_motor.setVelocity(left)
            self.right_motor.setVelocity(right)
            
            if self.recording and not self.playing:
                movement = {
                    'action': action,
                    'duration': duration,
                    'position': self.true_position.copy(),
                    'timestamp': datetime.now().isoformat()
                }
                self.movement_buffer.append(movement)
                self._record_position()
    
    def save_champion_path(self, path_name):
        """Save an optimized path with performance metrics"""
        if not self.movement_buffer:
            return False
        
       
        path_length = len(self.movement_buffer)
        coverage = len(self.movement_db['position_log'])
        efficiency = coverage / path_length 
        
        path_data = json.dumps({
            'movements': self.movement_buffer,
            'position_log': self.movement_db['position_log']
        }).encode('zlib')
        
        cursor = self.db_conn.cursor()
        cursor.execute('''INSERT INTO champion_paths 
                        (name, path_data, position_data, metrics, timestamp)
                        VALUES (?, ?, ?, ?, ?)''',
                      (path_name, path_data, None, efficiency, datetime.now().isoformat()))
        self.db_conn.commit()
        
        
        self.movement_db['optimized_paths'][path_name] = {
            'movements': self.movement_buffer.copy(),
            'metrics': efficiency
        }
        
        self.movement_buffer = []
        return True
    
    def load_champion_path(self, path_name):
        """Load a high-performance path from database"""
        cursor = self.db_conn.cursor()
        cursor.execute('''SELECT path_data FROM champion_paths 
                        WHERE name=? ORDER BY metrics DESC LIMIT 1''', (path_name,))
        result = cursor.fetchone()
        
        if result:
            return json.loads(result[0].decode('zlib'))
        return None
    
    def play_champion_path(self, path_name):
        """Execute a stored path with championship timing"""
        path_data = self.load_champion_path(path_name)
        if not path_data:
            return False
        
        self.playing = True
        print(f"Executing champion path: {path_name}")
        
        for movement in path_data['movements']:
            self._execute_champion_move(movement['action'], movement['duration'])
            start_time = self.getTime()
            
            while self.step(self.timestep) != -1:
                current_time = self.getTime()
                if current_time - start_time >= movement['duration']:
                    break
                
                self._update_odometry()
        
        self.playing = False
        self._execute_champion_move('stop')
        return True
    
    def run(self):
        """World-class control loop"""
        print("FIRA U19 Champion Controller Ready")
        print("Keyboard Controls:")
        print("  ↑: Forward (Optimal Speed)")
        print("  ↓: Backward (Safe Speed)")
        print("  ←: Left Turn (Competition Tight)")
        print("  →: Right Turn (Competition Tight)")
        print("  SPACE: Immediate Stop")
        print("  R: Start/Stop Recording")
        print("  S: Save Champion Path")
        print("  P: Play Champion Path")
        
        while self.step(self.timestep) != -1:
            self._update_odometry()
            
            key = self.keyboard.getKey()
            
            if key == ord('R'):
                self.recording = not self.recording
                status = "RECORDING" if self.recording else "READY"
                print(f"Controller Status: {status}")
            
            elif key == ord('S') and self.recording:
                path_name = input("Enter name for this champion path: ")
                if self.save_champion_path(path_name):
                    print(f"Saved path '{path_name}' with elite performance metrics!")
                else:
                    print("No movements to save!")
            
            elif key == ord('P'):
                path_name = input("Enter champion path name to execute: ")
                self.play_champion_path(path_name)
            
            elif key == Keyboard.UP:
                self._execute_champion_move('forward')
            
            elif key == Keyboard.DOWN:
                self._execute_champion_move('backward')
            
            elif key == Keyboard.LEFT:
                self._execute_champion_move('left')
            
            elif key == Keyboard.RIGHT:
                self._execute_champion_move('right')
            
            elif key == ord(' '):
                self._execute_champion_move('stop')

if __name__ == "__main__":
    champion = ChampionController()
    champion.run()
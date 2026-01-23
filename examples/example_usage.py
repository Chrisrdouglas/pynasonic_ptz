"""
Example usage of the improved PTZ Camera library.

This script demonstrates various features and best practices.
"""

import logging
import time
from ptz_camera import PTZCamera
from ptz_camera_exceptions import (
    InvalidParameter, CommandFailed, NetworkError, 
    TimeoutError, InvalidCamera
)


def setup_logging():
    """Configure logging for the example."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def basic_usage_example():
    """Demonstrate basic camera control."""
    print("\n=== Basic Usage Example ===")
    
    try:
        # Create camera instance
        camera = PTZCamera(
            camera="AW-HN40",
            address="192.168.0.10",
            timeout=5.0
        )
        
        # Check power state
        power = camera.get_power_state()
        print(f"Current power state: {power}")
        
        # Turn on camera if it's off
        if power != "On":
            print("Turning camera on...")
            result = camera.set_power_state(True)
            print(f"New power state: {result}")
            time.sleep(2)  # Wait for camera to power on
        
        # Move to preset
        print("Moving to preset 5...")
        camera.move_to_preset(5)
        time.sleep(camera.delay)
        
        # Get current position
        position = camera.get_pan_tilt_position()
        if position:
            pan, tilt = position
            print(f"Current position: pan={pan}, tilt={tilt}")
        
        # Set zoom
        print("Setting zoom to 2500...")
        camera.set_zoom(2500)
        
        # Get zoom
        zoom = camera.get_zoom()
        print(f"Current zoom: {zoom}")
        
        # Enable auto focus
        print("Enabling auto focus...")
        camera.set_auto_focus(True)
        
        # Check auto focus state
        af_state = camera.get_auto_focus()
        print(f"Auto focus: {af_state}")
        
        camera.close()
        
    except NetworkError as e:
        print(f"Network error: {e}")
    except TimeoutError as e:
        print(f"Timeout error: {e}")
    except CommandFailed as e:
        print(f"Command failed: {e}")


def context_manager_example():
    """Demonstrate using context manager for automatic cleanup."""
    print("\n=== Context Manager Example ===")
    
    try:
        with PTZCamera("AW-HN40", "192.168.0.10", timeout=3.0) as camera:
            print(f"Camera: {camera}")
            print(f"Pan bounds: {camera.pan_bounds}")
            print(f"Tilt bounds: {camera.tilt_bounds}")
            print(f"Zoom bounds: {camera.zoom_bounds}")
            
            # Camera operations here
            camera.set_power_state(True)
            camera.move_to_preset(1)
            
        # Session automatically closed after exiting context
        print("Camera session closed")
        
    except Exception as e:
        print(f"Error: {e}")


def error_handling_example():
    """Demonstrate comprehensive error handling."""
    print("\n=== Error Handling Example ===")
    
    camera = None
    try:
        camera = PTZCamera("AW-UE150", "192.168.0.10")
        
        # Try to set an invalid zoom value
        print("Attempting to set invalid zoom value...")
        camera.set_zoom(10000)  # This will raise InvalidParameter
        
    except InvalidParameter as e:
        print(f"Invalid parameter error:")
        print(f"  Command: {e.command}")
        print(f"  Parameter: {e.param_name}")
        print(f"  Invalid value: {e.value}")
        print(f"  Valid range: {e.valid_range}")
        
    except TimeoutError as e:
        print(f"Timeout error:")
        print(f"  Command: {e.command}")
        print(f"  Address: {e.address}")
        print(f"  Timeout: {e.timeout}s")
        
    except NetworkError as e:
        print(f"Network error:")
        print(f"  Address: {e.address}")
        print(f"  Details: {e.details}")
        
    except CommandFailed as e:
        print(f"Command failed:")
        print(f"  Command: {e.command}")
        print(f"  Address: {e.address}")
        if e.status_code:
            print(f"  HTTP Status: {e.status_code}")
        if e.details:
            print(f"  Details: {e.details}")
            
    finally:
        if camera:
            camera.close()


def advanced_positioning_example():
    """Demonstrate advanced pan/tilt positioning."""
    print("\n=== Advanced Positioning Example ===")
    
    try:
        with PTZCamera("AW-UE150", "192.168.0.10") as camera:
            # Get the valid ranges
            pan_min, pan_max = camera.pan_bounds
            tilt_min, tilt_max = camera.tilt_bounds
            
            print(f"Pan range: {pan_min} to {pan_max}")
            print(f"Tilt range: {tilt_min} to {tilt_max}")
            
            # Move to center position
            center_pan = (pan_min + pan_max) // 2
            center_tilt = (tilt_min + tilt_max) // 2
            
            print(f"Moving to center: pan={center_pan}, tilt={center_tilt}")
            camera.set_pan_tilt_position(
                pan=center_pan,
                tilt=center_tilt,
                speed=15,
                select=0
            )
            time.sleep(camera.delay)
            
            # Verify position
            current_pos = camera.get_pan_tilt_position()
            if current_pos:
                print(f"Current position: {current_pos}")
                
    except Exception as e:
        print(f"Error: {e}")


def speed_control_example():
    """Demonstrate pan/tilt speed control."""
    print("\n=== Speed Control Example ===")
    
    try:
        with PTZCamera("AW-UE150", "192.168.0.10") as camera:
            # Get speed bounds
            pan_speed_min, pan_speed_max = camera.pan_speed_bounds
            tilt_speed_min, tilt_speed_max = camera.tilt_speed_bounds
            
            print(f"Pan speed range: {pan_speed_min} to {pan_speed_max}")
            print(f"Tilt speed range: {tilt_speed_min} to {tilt_speed_max}")
            
            # Set moderate speed
            print("Setting pan/tilt speed to 50...")
            camera.set_pan_tilt_speed(pan_speed=50, tilt_speed=50)
            
            # Set slow speed
            print("Setting pan/tilt speed to 10...")
            camera.set_pan_tilt_speed(pan_speed=10, tilt_speed=10)
            
    except Exception as e:
        print(f"Error: {e}")


def unknown_camera_example():
    """Demonstrate handling unknown camera models."""
    print("\n=== Unknown Camera Example ===")
    
    try:
        # This will raise InvalidCamera
        camera = PTZCamera("UNKNOWN-MODEL", "192.168.0.10")
        
    except InvalidCamera as e:
        print(f"Invalid camera error:")
        print(f"  Model: {e.camera_model}")
        print(f"  Available models: {e.available_models}")
        
    try:
        # Use default configuration for unknown model
        print("\nUsing default configuration...")
        camera = PTZCamera(
            "UNKNOWN-MODEL",
            "192.168.0.10",
            use_default_on_unknown=True
        )
        print(f"Camera created with default config: {camera}")
        print(f"Pan bounds: {camera.pan_bounds}")
        camera.close()
        
    except Exception as e:
        print(f"Error: {e}")


def batch_operations_example():
    """Demonstrate batch camera operations."""
    print("\n=== Batch Operations Example ===")
    
    try:
        with PTZCamera("AW-UE150", "192.168.0.10") as camera:
            # Define a sequence of positions (pan, tilt, zoom)
            positions = [
                (30000, 28000, 2000, "Position 1"),
                (35000, 30000, 2500, "Position 2"),
                (25000, 26000, 1800, "Position 3"),
            ]
            
            for pan, tilt, zoom, name in positions:
                print(f"\nMoving to {name}...")
                
                # Set position
                camera.set_pan_tilt_position(pan, tilt, speed=20, select=0)
                time.sleep(camera.delay)
                
                # Set zoom
                camera.set_zoom(zoom)
                time.sleep(camera.delay)
                
                # Verify
                current_pos = camera.get_pan_tilt_position()
                current_zoom = camera.get_zoom()
                print(f"  Position: {current_pos}")
                print(f"  Zoom: {current_zoom}")
                
                # Wait before next movement
                time.sleep(1.0)
                
    except Exception as e:
        print(f"Error: {e}")


def main():
    """Run all examples."""
    setup_logging()
    
    print("PTZ Camera Library - Example Usage")
    print("=" * 50)
    
    # Run examples
    # Note: Comment out examples that you don't want to run
    
    basic_usage_example()
    context_manager_example()
    error_handling_example()
    advanced_positioning_example()
    speed_control_example()
    unknown_camera_example()
    batch_operations_example()
    
    print("\n" + "=" * 50)
    print("Examples complete!")


if __name__ == "__main__":
    main()